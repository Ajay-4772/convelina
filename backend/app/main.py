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
            "backend": {"status": "up"},
            "postgres": {"status": "unknown"},
            "qdrant": {"status": "unknown"},
            "firebase_auth": {
                "status": "configured" if is_firebase_configured() else "unconfigured"
            }
        }
    }
    
    # 1. Check PostgreSQL (via shared application connection pool)
    try:
        with db_engine.connect() as connection:
            result = connection.execute(text("SELECT 1;")).scalar()
            if result == 1:
                health_status["services"]["postgres"] = {"status": "up"}
            else:
                health_status["services"]["postgres"] = {"status": "down", "error": "Query returned unexpected result"}
                health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Healthcheck failed to connect to PostgreSQL: {e}")
        error_msg = str(e) if settings.DEBUG else "Database connection failed or unreachable."
        health_status["services"]["postgres"] = {"status": "down", "error": error_msg}
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
                "collections": cols
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

    http_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=http_code, content=health_status)
