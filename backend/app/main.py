import logging
import time
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from qdrant_client import QdrantClient

logger = logging.getLogger("convelina.api")

from app.core.database import engine as db_engine
from app.config import settings
from app.core.firebase import initialize_firebase, is_firebase_configured
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.conflicts import router as conflicts_router
from app.routers.assistant import router as assistant_router
from app.routers.knowledge import router as knowledge_router
from app.routers.correction_drafts import router as correction_drafts_router
from app.routers.admin import router as admin_router
from app.routers.pki import router as pki_router
from app.routers.repository import router as repository_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Firebase Admin SDK
    initialize_firebase()
    # Startup: Ensure Qdrant knowledge base and collections are indexed
    try:
        from app.rag.qdrant import ensure_knowledge_indexed
        ensure_knowledge_indexed()
    except Exception as e:
        logger.error("Failed to initialize Qdrant knowledge index on startup: %s", e)
    yield

is_prod = settings.ENVIRONMENT.lower() == "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for CONVELINA: Modular AI-Powered Business Management & Verification Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if is_prod and not settings.DEBUG else "/docs",
    redoc_url=None if is_prod and not settings.DEBUG else "/redoc",
    openapi_url=None if is_prod and not settings.DEBUG else "/openapi.json",
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    if is_prod:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Global Exception Handler (prevents leaking internal stack traces or environment variables)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    detail = str(exc) if settings.DEBUG else "Internal server error. Please try again."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail}
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(conflicts_router)
app.include_router(assistant_router)
app.include_router(knowledge_router)
app.include_router(correction_drafts_router)
app.include_router(admin_router)
app.include_router(pki_router)
app.include_router(repository_router)

# Development Explorer router (available only in non-production environments)
if not is_prod:
    from app.routers.dev import router as dev_router
    app.include_router(dev_router)


@app.get("/")
def read_root():
    return {
        "service": "CONVELINA Backend API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "firebase_auth_configured": is_firebase_configured(),
    }

@app.get("/health")
def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "fastapi": {"status": "up", "version": "1.0.0"},
            "postgres": {"status": "unknown"},
            "database_migrations": {"status": "unknown"},
            "qdrant": {"status": "unknown"},
            "ocr_engine": {"status": "unknown"},
            "storage": {"status": "unknown"},
            "firebase_auth": {
                "status": "configured" if is_firebase_configured() else "unconfigured"
            },
            "gemini": {
                "status": "enabled" if settings.GEMINI_ENABLED else "disabled",
                "model": settings.GEMINI_MODEL if settings.GEMINI_ENABLED else None,
            },
        },
    }

    # 1. Check PostgreSQL & Migration State (via dedicated non-superuser consolith_app pool)
    try:
        with db_engine.connect() as connection:
            user_row = connection.execute(text("SELECT current_user, session_user, current_database();")).fetchone()
            current_user = user_row[0] if user_row else "unknown"
            health_status["services"]["postgres"] = {
                "status": "up",
                "role": current_user,
                "database": user_row[2] if user_row else "unknown",
            }

            try:
                mig_rows = connection.execute(text("SELECT version FROM schema_migrations ORDER BY version;")).fetchall()
                applied_versions = [r[0] for r in mig_rows]
                health_status["services"]["database_migrations"] = {
                    "status": "up",
                    "applied_count": len(applied_versions),
                    "latest_applied": applied_versions[-1] if applied_versions else None,
                }
            except Exception as mig_err:
                health_status["services"]["database_migrations"] = {
                    "status": "down",
                    "error": "schema_migrations table unavailable or uninitialized",
                }
                health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Healthcheck failed to connect to PostgreSQL: {e}")
        error_msg = str(e) if settings.DEBUG else "Database connection failed or unreachable."
        health_status["services"]["postgres"] = {"status": "down", "error": error_msg}
        health_status["services"]["database_migrations"] = {"status": "down", "error": "Database unreachable"}
        health_status["status"] = "degraded"

    # 2. Check Qdrant
    try:
        if settings.QDRANT_IN_PROCESS or settings.QDRANT_LOCATION:
            from app.rag.qdrant import get_qdrant_client
            client = get_qdrant_client()
            cols = [c.name for c in client.get_collections().collections]
            health_status["services"]["qdrant"] = {
                "status": "up",
                "mode": "in_process",
                "collections": cols,
            }
        else:
            qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
            with httpx.Client(timeout=2.0) as http_client:
                resp = http_client.get(f"{qdrant_url}/healthz")
                if resp.status_code == 200:
                    health_status["services"]["qdrant"] = {"status": "up", "mode": "external"}
                else:
                    health_status["services"]["qdrant"] = {"status": "down", "code": resp.status_code}
                    health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Healthcheck failed to connect to Qdrant: {e}")
        error_msg = str(e) if settings.DEBUG else "Vector database connection failed or unreachable."
        health_status["services"]["qdrant"] = {"status": "down", "error": error_msg}
        health_status["status"] = "degraded"

    # 3. Check OCR Engine
    try:
        from app.ocr.engine import default_ocr_engine
        health_status["services"]["ocr_engine"] = {
            "status": "up",
            "engine": "tesseract",
            "available": True,
        }
    except Exception as e:
        health_status["services"]["ocr_engine"] = {
            "status": "down",
            "error": str(e) if settings.DEBUG else "OCR engine uninitialized",
        }
        health_status["status"] = "degraded"

    # 4. Check Storage
    try:
        import os
        temp_dir = settings.STORAGE_TEMP_DIR
        os.makedirs(temp_dir, exist_ok=True)
        health_status["services"]["storage"] = {
            "status": "up",
            "retention_policy": settings.STORAGE_RETENTION_POLICY,
            "temp_dir_available": os.path.isdir(temp_dir),
        }
    except Exception as e:
        health_status["services"]["storage"] = {
            "status": "down",
            "error": str(e) if settings.DEBUG else "Storage directory unwritable",
        }
        health_status["status"] = "degraded"

    http_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=http_code, content=health_status)
