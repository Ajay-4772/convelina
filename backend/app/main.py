import time
import httpx
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient

from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Consolith: AI-Powered Identity Conflict Detection & Assistance",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "service": "Consolith Backend API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
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
        }
    }
    
    # 1. Check PostgreSQL
    try:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1;")).scalar()
            if result == 1:
                health_status["services"]["postgres"] = {"status": "up"}
            else:
                health_status["services"]["postgres"] = {"status": "down", "error": "Query returned unexpected result"}
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["postgres"] = {"status": "down", "error": str(e)}
        health_status["status"] = "degraded"

    # 2. Check Qdrant
    try:
        qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
        # Using REST healthz check
        with httpx.Client(timeout=2.0) as http_client:
            resp = http_client.get(f"{qdrant_url}/healthz")
            if resp.status_code == 200:
                health_status["services"]["qdrant"] = {"status": "up"}
            else:
                health_status["services"]["qdrant"] = {"status": "down", "code": resp.status_code}
                health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["qdrant"] = {"status": "down", "error": str(e)}
        health_status["status"] = "degraded"

    http_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=http_code, content=health_status)
