# CONVELINA — Deployment, Hosting & Cloud Infrastructure Specification

```
+---------------------------------------------------------------------------------------------------------+
| DEPLOYMENT TIER: Docker Multi-Stage | Compose Network Isolation | Caddy 2.8 Reverse Proxy | Cloud Ready |
+---------------------------------------------------------------------------------------------------------+
```

**Classification:** Technical Architecture Specification  
**Component:** `Caddyfile`, `docker-compose.yml`, `docker-compose.prod.yml`  
**Status:** Production Verified | Zero Exposed Database Ports  

---

## 1. Executive Overview

CONVELINA uses a **containerized network-isolated deployment model**. All incoming traffic enters through an unprivileged Caddy 2.8 edge reverse proxy handling automated TLS 1.3 termination, rate-limiting, and request body size enforcement. Database and vector persistence engines run inside an internal network inaccessible from the host or internet.

---

## 2. Docker Network Segregation

Production architecture defines two distinct bridge networks in [`docker-compose.prod.yml`](file:///c:/Users/ajaya/Desktop/consolin/docker-compose.prod.yml):

```
+---------------------------------------------------------------------------------------------------------+
|                                        INTERNET / INGRESS                                               |
|                                                │                                                        |
|                                       Port 80 / 443 (TLS 1.3)                                           |
|                                                ▼                                                        |
|                                     [Caddy 2.8 Reverse Proxy]                                           |
|                                                │                                                        |
|                       ┌────────────────────────┴────────────────────────┐                               |
|                       │ (Proxy /)                                       │ (Proxy /api/*)                |
|                       ▼                                                 ▼                               |
|       [public-net: Next.js Frontend]                    [public-net: FastAPI Backend]                   |
+─────────────────────────────────────────────────────────────────────────┼───────────────────────────────+
|                                                                         │                               |
|                                                                 TCP     ▼     TCP                       |
|                                                      ┌──────────────────┴──────────────────┐            |
|                                                      ▼                                     ▼            |
|                                          [PostgreSQL 16 Alpine]                  [Qdrant Vector DB]     |
|                                        (Forced RLS / Non-Superuser)             (HNSW Vector Graph)     |
|                                                                                                         |
|                                 INTERNAL-NET (internal: true | ZERO Host Ports)                         |
+---------------------------------------------------------------------------------------------------------+
```

### Network Security Properties:
- `public-net`: Shared strictly by Caddy, Next.js, and FastAPI.
- `internal-net`: Configured with `internal: true`. Accessible **only** by the FastAPI backend. PostgreSQL (port 5432) and Qdrant (port 6333) have **zero exposed host ports**.

---

## 3. Local Execution vs. Production Cloud Deployment

### 3.1 Local Development Stack
```bash
# Start all local containers (Frontend, Backend, Postgres, Qdrant)
docker compose up -d

# Verify service health
docker compose ps

# View unified application logs
docker compose logs -f
```

### 3.2 Production Cloud Deployment
```bash
# 1. Run database migrations first via one-shot isolated container
docker compose -f docker-compose.prod.yml run --rm migrate

# 2. Launch production stack in background
docker compose -f docker-compose.prod.yml up -d

# 3. Verify health probes
curl -f http://localhost/health
```

---

## 4. Cloud Hosting Blueprints

| Provider / Model | Recommended Architecture | Advantages | Estimated Monthly Cost |
| :--- | :--- | :--- | :--- |
| **Single-Host VPS** *(Hetzner / DigitalOcean / Linode)* | Ubuntu 24.04 LTS + Docker Compose + Caddy Auto-TLS. Place behind Cloudflare DNS/WAF. | Simplest ops, lowest cost, sub-5ms internal database latency. | \$20 – \$40 / month |
| **AWS Cloud** | ECS Fargate (Frontend & Backend containers) + Amazon RDS PostgreSQL 16 + Amazon ALB + Route 53. | High availability, auto-scaling, managed database backups. | \$120 – \$250 / month |
| **Google Cloud (GCP)** | Cloud Run (Frontend & Backend services) + Cloud SQL for PostgreSQL + Serverless VPC Access. | Pay-per-use, scale-to-zero when idle, seamless Gemini API IAM bindings. | \$60 – \$150 / month |

---

## 5. Environment Variables & Secret Configuration

Production secrets are defined via `.env` (never committed to git):
- `DATABASE_URL`: PostgreSQL connection string using `consolith_app` user.
- `ENCRYPTION_KEY`: 32-byte Fernet AES-256 base64-encoded key.
- `FIREBASE_PROJECT_ID`: Google Firebase project ID.
- `GEMINI_API_KEY`: API key for Google Gemini 1.5 Flash legal RAG.
- `RESEND_API_KEY`: Transactional email API key for OTP delivery.
- `CORS_ORIGINS`: JSON array of allowed origins (e.g. `["https://convelina.gov.in"]`).

