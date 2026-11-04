# CONVELINA — Operations & Deployment Guide

**Classification:** Infrastructure & DevOps Specification  
**Architecture:** Multi-Container Modular Monolith  
**Status:** VALIDATED CONTAINER STACK  

---

## 1. Container Infrastructure Topology

CONVELINA is deployed using Docker Compose across four orchestrated container services on a private internal bridge network (`convelina_network`):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL REVERSE PROXY                          │
│               TLS 1.3 Termination • Port 443/80 (Caddy)                │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │ convelina.in                   │ admin.convelina.in
                    ▼                                ▼
┌───────────────────────────────────────┐  ┌─────────────────────────────┐
│          CONVELINA FRONTEND           │  │      SUBDOMAIN REWRITE      │
│         Next.js 14 Production         │  │     Next.js Middleware      │
│      Port 3000 (Internal Bridge)      │  │      Rewrite to /admin      │
└───────────────────┬───────────────────┘  └──────────────┬──────────────┘
                    │                                     │
                    └──────────────────┬──────────────────┘
                                       │ HTTP / REST
                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          CONVELINA BACKEND                             │
│                     FastAPI 0.115 • Python 3.11                        │
│            Port 8000 • Healthcheck: curl -f /health                    │
└───────────────────────┬────────────────────────┬───────────────────────┘
                        │                        │
                        ▼                        ▼
┌───────────────────────────────┐        ┌───────────────────────────────┐
│      CONVELINA POSTGRES       │        │       CONVELINA QDRANT        │
│     PostgreSQL 16 Alpine      │        │        Qdrant v1.11.0         │
│  Port 5432 • Forced RLS       │        │  Port 6333 (HTTP) / 6334 (GRPC)│
│  Volume: consolin_postgres_data│       │   Volume: consolin_qdrant_data │
└───────────────────────────────┘        └───────────────────────────────┘
```

---

## 2. Container Service Specifications

| Service | Image | Internal Port | Published Port | Healthcheck Command | Restart Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`postgres`** | `postgres:16-alpine` | `5432` | `5432:5432` | `pg_isready -U postgres -d consolith` | `unless-stopped` |
| **`qdrant`** | `qdrant/qdrant:v1.11.0` | `6333`, `6334` | `6333:6333`, `6334:6334` | TCP / HTTP socket check on `/healthz` | `unless-stopped` |
| **`backend`** | Custom (`./backend/Dockerfile`) | `8000` | `8000:8000` | `curl -f http://localhost:8000/health \|\| exit 1` | `unless-stopped` |
| **`frontend`** | Custom (`./frontend/Dockerfile`) | `3000` | `3000:3000` | HTTP GET `/` returns 200 | `unless-stopped` |

---

## 3. Production Deployment Procedure

### 3.1 Environment Configuration
Create a production `.env` file from `.env.example`. Ensure production invariants are satisfied:

```bash
# Production Invariants Checklist
ENVIRONMENT=production
DEBUG=False
TEST_MODE_ALLOW_SIMULATED_TOKENS=False

# Database Configuration (dedicated non-superuser role consolith_app)
DATABASE_URL=postgresql://consolith_app:<strong-generated-password>@postgres:5432/consolith

# Sensitive Data Encryption at Rest (32-byte URL-safe base64 Fernet key)
ENCRYPTION_KEY=<strong-unique-fernet-key-32-bytes>

# AI & RAG Configuration
GEMINI_API_KEY=<valid-google-gemini-api-key>
GEMINI_MODEL=gemini-1.5-flash

# Firebase Admin SDK Configuration
FIREBASE_PROJECT_ID=convelina-prod
FIREBASE_SERVICE_ACCOUNT_PATH=/app/serviceAccountKey.json
```

### 3.2 Starting Container Stack

For production environments, launch the hardened stack using `docker-compose.prod.yml`, which isolates Postgres and Qdrant to an unexposed `internal-net`, drops root container privileges, scales Uvicorn workers to 4, and automatically deploys Caddy as the edge TLS reverse proxy:

```bash
# 1. Build and launch production services in background
docker compose -f docker-compose.prod.yml up -d --build

# 2. Verify all containers are healthy (postgres, qdrant, backend, frontend, caddy)
docker compose -f docker-compose.prod.yml ps

# 3. Apply SQL migrations 001-009 as superuser postgres
docker compose -f docker-compose.prod.yml exec -e PYTHONPATH=/app backend python /scripts/run_migrations.py

# 4. Provision initial administrator account
docker compose -f docker-compose.prod.yml exec -e PYTHONPATH=/app backend python /scripts/provision_admin.py --email admin@convelina.in

# 5. Execute system verification suite
docker compose -f docker-compose.prod.yml exec -e PYTHONPATH=/app backend python /scripts/verify_module1.py
```

---

## 4. Production Reverse Proxy Specification (Caddyfile)

```caddy
# Citizen Web Application
convelina.in {
    encode zstd gzip
    reverse_proxy frontend:3000

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
}

# Officer & Administrator Management Console
admin.convelina.in {
    encode zstd gzip
    reverse_proxy frontend:3000

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
}

# Backend API Gateway
api.convelina.in {
    encode zstd gzip
    reverse_proxy backend:8000

    # Limit client upload body to 10MB
    request_body {
        max_size 10MB
    }
}
```



---

## 5. Emergency Rollback Procedure

If a deployment encounters critical runtime errors, failed migrations, or unexpected service degradation, execute the following controlled rollback procedure:

```bash
# ==============================================================================
# CONVELINA PRODUCTION ROLLBACK PROTOCOL
# Target RTO: < 15 Minutes
# ==============================================================================

# 1. Gracefully stop user-facing ingress proxy and backend workers
docker compose -f docker-compose.prod.yml stop caddy frontend backend

# 2. If database schema rollback is required, restore from pre-deployment snapshot
# Pre-requisite: ensure consolith_app role exists
docker exec convelina-postgres-prod psql -U postgres -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'consolith_app') THEN
        CREATE ROLE consolith_app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
    END IF;
END
\$\$;
"

# Re-create clean database and restore pre-deployment dump
docker exec convelina-postgres-prod psql -U postgres -c "DROP DATABASE IF EXISTS consolith;"
docker exec convelina-postgres-prod psql -U postgres -c "CREATE DATABASE consolith;"
docker exec -i convelina-postgres-prod pg_restore -U postgres -d consolith /backups/consolith_pg_PRE_DEPLOYMENT.dump

# 3. Roll back application image tags in docker-compose.prod.yml (e.g. to previous release SHA)
# Restart the stack with the known stable release
docker compose -f docker-compose.prod.yml up -d --no-build

# 4. Execute post-rollback smoke tests
docker compose -f docker-compose.prod.yml exec backend curl -f http://localhost:8000/health
curl -f http://localhost/health
```
