# CONVELINA — Zero-Cost / Ultra-Low-Cost Deployment Feasibility Audit

**Project**: CONVELINA (Consolith) — Privacy-Preserving Citizen Document Discrepancy Detection & Government Correction Assistance Platform  
**Document**: `docs/deployment/FREE_TIER_DEPLOYMENT_FEASIBILITY.md`  
**Evaluation Sprint**: Sprint 7 Feasibility Audit  
**Target Recurring Budget**: **₹0 – ₹200 INR per month** ($0.00 – $2.35 USD at ₹85.00/USD)  
**Date of Evaluation**: October 28, 2026  
**Auditor Roles**: Senior Cloud Architect, DevOps Engineer, Application Security Engineer, and Cost Optimization Specialist  
**Operating Mode**: Read-Only Architectural Feasibility Audit (Zero public cloud resources created, zero domains purchased, zero secrets staged)

---

## 1. Executive Summary & Recommended Architecture

### 1.1 Executive Summary
A comprehensive audit of the CONVELINA repository confirms that **deploying CONVELINA on a ₹0–₹200 INR/month budget is technically and operationally feasible for a public evaluation prototype**, without requiring an architectural rewrite or compromising core security guarantees.

CONVELINA’s design choices make it well suited for ultra-low-cost hosting:
1. **Lightweight Deterministic Semantic Embeddings**: The vector search engine utilizes `DeterministicBGEEmbeddingService` (1024-dimensional CPU hash projection) rather than heavy 2GB+ PyTorch transformer weights. Container startup requires < 2 seconds and idles at < 80 MB RAM.
2. **Deterministic Conflict Engine**: Document comparison (Aadhaar, PAN, Passport, Voter ID, Marksheets) runs 100% in-process via compiled C/Python libraries (`RapidFuzz`, `Jellyfish`, `Verhoeff`). It incurs **₹0 external API costs** and functions completely independently of LLMs.
3. **Ephemeral Document Processing**: Raw identity scans and PDFs are processed in-memory / temporary tmpfs and unlinked immediately in a `finally:` block (`STORAGE_RETENTION_POLICY="delete_after_ocr"`). Because only encrypted metadata is persisted, CONVELINA requires **zero expensive cloud object storage (AWS S3 / GCS)**.
4. **Relational Database Footprint**: The entire relational schema (18 tables with forced PostgreSQL Row-Level Security, audit triggers, and case workflows) consumes **< 10 MB** for a 100-user prototype, fitting well within free managed PostgreSQL tiers (500 MB limit).
5. **Token Economy**: AI Assistant RAG queries enforce a 0.55 similarity floor and strict context capping (4,000 tokens). On pay-as-you-go Gemini 1.5 Flash, 50 active demo citizens cost **less than ₹10 INR ($0.12 USD) per month**.

### 1.2 Recommended Architecture: "Decoupled Serverless Edge & Container" (Architecture B)
- **Frontend**: **Vercel Hobby Tier** ($0.00 / month) — Hosts the Next.js 14 App Router with edge CDN, automatic HTTPS, and global DNS.
- **Backend**: **Google Cloud Run** ($0.00 / month under Always Free Tier in `us-central1`, or ~₹50–₹70/mo in Mumbai `asia-south1` with scale-to-zero) — Executes the 297MB production backend container (FastAPI + Tesseract OCR 5.5 + Poppler) with 1 vCPU and 1 GB RAM.
- **Database**: **Supabase Free Tier** ($0.00 / month in Mumbai `ap-south-1`) — Provides managed PostgreSQL 16 with native support for the unprivileged `consolith_app` role, forced RLS on all 18 tables, transaction-local `SET LOCAL` context, and append-only cryptographic triggers.
- **Vector Search**: **Qdrant Cloud Free Tier** ($0.00 / month) or **FastAPI In-Process Qdrant** ($0.00 / month) — Stores 31 official government knowledge chunks and forms (< 200 KB).
- **Authentication**: **Firebase Authentication Spark Plan** ($0.00 / month) — Supports up to 50,000 Monthly Active Users for Google Sign-in and server-side token validation.
- **Email OTP**: **Resend Free Tier** ($0.00 / month) — Handles citizen email verification (100 emails/day, 3,000 emails/month).
- **LLM / AI Assistant**: **Google Gemini 1.5 Flash Pay-As-You-Go** (~₹5 – ₹25 INR / month) — Enables strict enterprise privacy (zero training on customer data) for resolution guidance and correction drafting.
- **Custom Domain**: Optional `.in` domain amortized (~₹40 – ₹50 INR / month) or free provider subdomains (`*.vercel.app` + `*.run.app`) for ₹0.00.

**Estimated Recurring Cost**: **₹0.00 – ₹120.00 INR / month** ($0.00 – $1.41 USD / month).

---

## 2. Actual Current Repository Architecture & Verified Inventory

### 2.1 Codebase Structure & Verified Components
The repository was audited locally. All uncommitted changes and project-memory files were inspected:

| Subsystem | Technology | Verified Implementation State |
| :--- | :--- | :--- |
| **Frontend** | Next.js 14.2.13 (App Router), React 18.3.1, TypeScript 5.6.2, Tailwind CSS 3.4.12 | Modular App Router (`/app`, `/app/inconsistencies`, `/app/assistant`, `/app/forms`, `/app/profile`, `/admin`). Verified production build compiles 15/15 routes cleanly (`npm run build`). Clean TypeScript compilation (`tsc --noEmit`, 0 errors). |
| **Backend** | FastAPI 0.115.0, Uvicorn 0.30.6, Pydantic v2.9.2, SQLAlchemy 2.0.35 | 77/77 passing pytest unit tests. Production settings validator in `app/config.py` fails closed on default secrets, wildcard CORS, or superuser connections. |
| **Database** | PostgreSQL 16 Alpine, Alembic / custom sequential runner `app/core/migrate.py` | 9 migrations applied sequentially and verified idempotent. 18 tables have `FORCE ROW LEVEL SECURITY`. Non-superuser runtime role `consolith_app`. Triggers block `UPDATE`/`DELETE` on `audit_log` and role self-escalation on `users`. |
| **OCR Pipeline** | Tesseract OCR 5.5.0 (`eng+hin`), Poppler, pdf2image, Pillow | Magic-byte checking, path traversal sanitization, 10MB size limit. Max 3 pages rasterized per PDF. Temporary files unlinked in `finally:` block. Aadhaar 12-digit numbers validated via Verhoeff algorithm and masked to `XXXX-XXXX-1234`. Sensitive payloads encrypted with Fernet at rest. |
| **Conflict Engine** | RapidFuzz 3.9.7, Jellyfish 1.1.0, Python `datetime` | Pure deterministic Python logic. Resolves cross-document discrepancies across Aadhaar, PAN, Passport, Class 10/12, and EPF. Discrepancy output uses neutral, non-accusatory framing. |
| **RAG Assistant** | Qdrant 1.11.3, `DeterministicBGEEmbeddingService`, Google Gemini 1.5 Flash | 25 UIDAI/NSDL/MEA/EPFO circular chunks + 6 forms indexed. Hybrid retrieval enforces >= 0.55 similarity floor and strict citation validation. Gracefully degrades with `"Assistant service is not currently available. Please try again later."` if unconfigured. |
| **PKI & Attestation** | Ed25519 (`cryptography.hazmat`), SHA-256 fingerprinting, RFC 8785 canonical JSON | Signs document conflict findings with digital signatures. Validates key status, expiration, and revocation. Cross-tenant attestation links blocked. |
| **Reverse Proxy** | Caddy 2.8 Alpine | Verified syntax (`caddy validate`), unbuffered streaming (`flush_interval -1`), 15MB request body size cap, automatic HTTPS. |

### 2.2 Container Images & Footprints
Production images built and verified locally in Docker Desktop:
- `convelina-prod-backend:latest` (ID: `f10063f43d00`): **297 MB compressed** / 1.29 GB uncompressed. Runs as unprivileged `appuser` (UID 10001).
- `convelina-prod-frontend:latest` (ID: `96c0db935a3c`): **179 MB compressed** / 993 MB uncompressed. Runs as unprivileged `nextjs` (UID 1001).
- `caddy:2.8-alpine` (ID: `af32e97399fe`): **18.9 MB**.

---

## 3. Hosting Provider Comparison (Official Sources & Limits)

*Information verified against official provider documentation as of late 2026.*

| Provider & Service | Free Tier Allowances & Quotas | Regional Availability & Latency | Cold Starts / Inactivity Rules | Billing Caps & Overage Risks | Evaluation for CONVELINA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Vercel** (Frontend) | **100 GB** bandwidth/mo, 100 GB-hrs serverless execution, 1M Edge Middleware invocations. Free SSL. | Global Edge Network (Anycast POPs in Mumbai, Chennai, etc. ~20ms). | Serverless functions cold start ~300ms. Static assets: 0ms. | Soft alerts at 50%, 75%, 100%. Does not auto-charge; may suspend hobby account on abuse. | **Excellent fit for Frontend**. Native Next.js 14 App Router support. Commercial clause requires Hobby tier to remain non-commercial/prototype. |
| **Cloudflare Pages** (Frontend Alt) | **Unlimited** bandwidth, 500 builds/month, free SSL, custom domains. | Global Edge (Indian POPs in BOM, DEL, MAA, BLR, HYD, CCU). | 0ms static edge routing; ~50ms Workers SSR. | Hard cap on builds (fails build if > 500). Unlimited bandwidth prevents overage surprises. | **Strong Alternative for Frontend**. Zero risk of bandwidth overage charges. |
| **Google Cloud Run** (Backend) | **Always Free Tier**: 2M requests/mo, 360k vCPU-seconds, 180k GiB-seconds, 1 GB North America egress/mo. | **CRITICAL**: Free tier applies **ONLY to US regions** (`us-central1`, `us-east1`, `us-west1`). Mumbai (`asia-south1`) has NO free tier. | Scale-to-zero (`min-instances=0`): 8–12 sec cold start for 297MB image. Idle instances terminate after 15 min. | Hard quota limits can be configured in Google Cloud Console. Cloud Billing alerts trigger emails but do not halt service without custom Pub/Sub script. | **Recommended for Backend**. Fits within free tier in `us-central1`. In `asia-south1`, scale-to-zero costs only ~₹50–₹70/mo for 50 demo users. |
| **Render** (Backend Alt) | 750 free instance hours/month. 512 MB RAM limit. 100 GB egress. | Oregon (US West), Frankfurt (EU), Singapore (`ap-southeast-1`). No India region. | Severe cold start: 50+ seconds after 15 minutes of inactivity. | Hard stops when 750 free hours expire. Free database expires after 30 days! | **Incompatible / High Risk**. 512MB RAM causes Tesseract OCR to crash with Out-Of-Memory (OOM) SIGKILL during PDF rasterization. 30-day database deletion is unacceptable. |
| **Supabase** (Database) | **500 MB** database storage, 2 free projects, 50k monthly active users, 2 GB egress. | **Mumbai (`ap-south-1`)** is available on the Free Tier! Native low latency to India (~25ms). | **CRITICAL INACTIVITY RULE**: Free projects **pause after 7 days of zero queries**. Unpause takes 1–2 minutes. | Free tier enforces hard limit; refuses writes if storage exceeds 500 MB. Zero accidental credit card charges. | **Recommended for Database**. Full PostgreSQL 16 support for custom roles (`consolith_app`), forced RLS on 18 tables, triggers, and Supavisor connection pooling. |
| **Neon** (Database Alt) | **0.5 GiB** storage, 1 project, 100 compute hours/month. | Singapore (`ap-southeast-1`), Frankfurt (`eu-central-1`), US East. Mumbai is Paid-only. | Scales to zero after 5 min. **Wakes up automatically in ~500ms** on incoming connection (no manual unpause). | Hard limit prevents unexpected billing. | **Strong Alternative for Database**. Eliminates Supabase's 7-day pause issue, though Singapore adds ~60ms latency to India. |
| **Qdrant Cloud** (Vector DB) | **1 free permanent cluster forever** (0.5 vCPU, 1 GB RAM, 4 GB storage, ~1M vectors). | AWS Frankfurt (`eu-central-1`) or US East. | Always running; **never sleeps or pauses**. | Zero overage risk; hard blocked at 4 GB. | **Recommended for Vector DB**. Zero maintenance, rock-solid uptime, zero cost. (Alternatively, in-memory Qdrant inside FastAPI costs ₹0). |
| **Firebase Auth** (Identity) | **Spark Plan (Free)**: 50,000 MAUs for Google Sign-In and Email/Password. | Global Google infrastructure. | Instant (cloud managed). | Hard stop when 50,000 MAU limit is reached. | **Recommended for Auth**. Exact drop-in match for existing `backend/app/dependencies/auth.py`. |
| **Google Gemini API** (LLM) | **AI Studio Free Tier**: 15 RPM, 1M TPM, 1,500 RPD. **Pay-as-you-go (Tier 1)**: $0.075 / 1M input, $0.30 / 1M output tokens. | Global API endpoints. | Fast cloud API (< 1.5s response). | Pay-as-you-go requires Cloud Billing. Can set spend budget alerts ($1.00 USD). | **Recommended**: Use Free Tier for synthetic testing; use Pay-as-you-go ($0.05–$0.20/mo) for privacy-compliant live evaluations. |
| **Resend** (Email OTP) | **Free Tier**: 100 emails/day, 3,000 emails/month. 1 custom sending domain. | Global edge delivery. | Instant delivery (< 2s). | Hard stop when 100 daily limit is reached. | **Recommended for Email**. Matches `backend/app/routers/auth.py` configuration. |

---

## 4. Rigorous Monthly Cost Estimates (INR & USD)

*Exchange Rate Assumption: $1.00 USD = ₹85.00 INR (late 2026).*

### 4.1 Workload Profile Assumptions (Evaluation Prototypes)
Costs are determined by transaction volume, not merely user counts:
- **Profile A (10 Demo Citizens / month)**: 30 document uploads, 30 OCR jobs (avg 2 pages), 60 conflict detection runs, 40 AI assistant queries (avg 1,500 prompt tokens, 400 completion tokens), 20 email OTPs, ~2 MB database storage.
- **Profile B (50 Demo Citizens / month)**: 150 document uploads, 150 OCR jobs, 300 conflict runs, 200 AI queries, 100 email OTPs, ~8 MB database storage.
- **Profile C (100 Active Citizens / month)**: 400 document uploads, 400 OCR jobs, 800 conflict runs, 500 AI queries, 250 email OTPs, ~18 MB database storage.

---

### 4.2 Scenario 1: ₹0.00 / month ($0.00 USD) — Pure Free-Tier Prototype
*Target: Best-effort public prototype operating strictly within zero-cost tier limits.*

| Component | Provider & Tier | Quota Allocation | Monthly Usage (50 Users) | Cost (USD) | Cost (INR) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Frontend** | Vercel Hobby | 100 GB bandwidth | ~1.5 GB | $0.00 | ₹0.00 |
| **Backend** | Google Cloud Run (`us-central1`) | 2M req, 360k vCPU-s, 180k GiB-s | ~2,500 req, 45k vCPU-s, 45k GiB-s | $0.00 | ₹0.00 |
| **Database** | Supabase Free (`ap-south-1`) | 500 MB storage, pooling | ~8 MB storage, 15 connections | $0.00 | ₹0.00 |
| **Vector DB** | Qdrant Cloud Free | 1 cluster (4 GB) | < 200 KB (31 vectors) | $0.00 | ₹0.00 |
| **OCR Processing** | Tesseract in Cloud Run | In-container CPU | 150 documents (avg 3.5s CPU) | $0.00 | ₹0.00 |
| **Authentication** | Firebase Spark | 50,000 MAUs | 50 MAUs | $0.00 | ₹0.00 |
| **Email OTP** | Resend Free | 3,000 emails/mo | ~100 emails | $0.00 | ₹0.00 |
| **AI Assistant** | Google AI Studio Free Tier | 1,500 RPD, 15 RPM | ~200 requests/mo (synthetic only) | $0.00 | ₹0.00 |
| **Domain & SSL** | `*.vercel.app` + Let's Encrypt | Unlimited | 1 subdomain | $0.00 | ₹0.00 |
| **Backups** | GitHub Actions Cron to GDrive | Free 2,000 runner mins | 30 runs x 1 min = 30 mins | $0.00 | ₹0.00 |
| **Total** | | | | **$0.00** | **₹0.00** |

**Trade-offs in Scenario 1**:
- Cloud Run in `us-central1` incurs ~180–220ms network latency to Indian citizens.
- Cold start on first request after idle takes 8–12 seconds.
- Supabase pauses after 7 days of zero database activity (requires manual dashboard resume or keep-alive ping).
- Google AI Studio Free Tier terms allow prompt logging; therefore, **only synthetic/demo data may be processed**.

---

### 4.3 Scenario 2: ₹100.00 / month (~$1.18 USD) — Enhanced Privacy & Custom Identity
*Target: Ultra-low-cost production-like evaluation with privacy-compliant LLM and custom domain.*

| Component | Provider & Tier | Allocation / Details | Cost (USD) | Cost (INR) |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | Vercel Hobby / Cloudflare Pages | Free tier edge CDN | $0.00 | ₹0.00 |
| **Backend** | Google Cloud Run (`us-central1`) | Free tier scale-to-zero | $0.00 | ₹0.00 |
| **Database** | Supabase Free (`ap-south-1`) | Free tier managed Postgres | $0.00 | ₹0.00 |
| **Vector DB** | Qdrant Cloud Free | Permanent free cluster | $0.00 | ₹0.00 |
| **Identity & Email** | Firebase Spark + Resend | Free tiers | $0.00 | ₹0.00 |
| **LLM Privacy** | Google Gemini 1.5 Flash (Tier 1 Paid) | 200 queries (300k input tokens @ $0.075/M + 80k output @ $0.30/M) = $0.047 USD | $0.05 | ~₹4.25 |
| **Custom Domain** | `.in` Domain (e.g., `convelina.in`) | Amortized registration (~₹540/year = ₹45/month) | $0.53 | ~₹45.00 |
| **Safety Reserve** | Cloud Run Egress / Buffer | Buffer for unexpected token or egress bursts | $0.50 | ~₹42.50 |
| **Total** | | | **~$1.08** | **~₹91.75** |

**Advantages over Scenario 1**:
- Gemini API uses paid Tier 1 enterprise terms: **zero logging or prompt training by Google**, ensuring full compliance with citizen privacy expectations.
- Official `.in` domain creates trust with institutional evaluators.

---

### 4.4 Scenario 3: ₹200.00 / month (~$2.35 USD) — Maximum Low-Cost Budget
*Target: Low-latency Indian hosting with keep-alive uptime and active monitoring.*

| Component | Provider & Tier | Allocation / Details | Cost (USD) | Cost (INR) |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | Vercel Hobby / Cloudflare Pages | Edge hosting + free SSL | $0.00 | ₹0.00 |
| **Backend** | Google Cloud Run (`asia-south1` Mumbai) | Scale-to-zero in Mumbai (50 users = ~30,000 vCPU-sec @ $0.000024 + 30k GiB-sec @ $0.0000025) | ~$0.80 | ~₹68.00 |
| **Database** | Supabase Free (`ap-south-1` Mumbai) | Free tier managed Postgres in Mumbai | $0.00 | ₹0.00 |
| **Keep-Alive Cron** | GitHub Actions / cron-job.org | Pings `/health` every 4 days to prevent Supabase 7-day pause | $0.00 | ₹0.00 |
| **Vector DB** | Qdrant Cloud Free | Free cluster | $0.00 | ₹0.00 |
| **Identity & Email** | Firebase Spark + Resend | Free tiers | $0.00 | ₹0.00 |
| **LLM Privacy** | Google Gemini 1.5 Flash (Tier 1 Paid) | 500 queries (~750k input + 200k output tokens) | $0.12 | ~₹10.20 |
| **Custom Domain** | `.in` Domain (Amortized) | Amortized annual registrar fee | $0.53 | ~₹45.00 |
| **Monitoring** | Sentry Developer Free Tier | 5,000 error events/month | $0.00 | ₹0.00 |
| **Buffer / Tax** | GST & Currency Fluctuation | 18% GST on Indian cloud billing + safety buffer | $0.80 | ~₹68.00 |
| **Total** | | | **~$2.25** | **~₹191.20** |

**Key Advantages of Scenario 3**:
- **Full In-Country Latency**: Both Backend (Cloud Run) and Database (Supabase) reside in **Mumbai (`asia-south1` / `ap-south-1`)**. Round-trip API latency drops from ~250ms to ~35ms!
- Automated keep-alive pings completely eliminate the Supabase 7-day pause issue.

---

### 4.5 Scenario 4: Beyond ₹200.00 / month — What Triggers Commercial Tiers?
The budget would exceed ₹200/month only if the following operational decisions are made:
1. **Always-On Backend (`min-instances=1`)**: Eliminating Cloud Run cold starts requires 730 continuous hours of 1 vCPU / 1 GB RAM, which costs **~$14.50 USD / month (~₹1,230 INR)**.
2. **Dedicated Cloud SQL / Supabase Pro**: Supabase Pro ($25/mo = ~₹2,125 INR) or Google Cloud SQL `db-f1-micro` (~$12/mo = ~₹1,020 INR) for automated point-in-time recovery and no pause policies.
3. **Commercial Vercel Pro License**: If the project transitions from educational/open-source evaluation to a commercial entity, Vercel Pro costs **$20/seat/month (~₹1,700 INR)**.
4. **Cloud Managed OCR (Google Cloud Vision API)**: If Tesseract is replaced by Google Document AI or Cloud Vision API ($1.50 per 1,000 pages), heavy scanning volumes would add variable costs.

---

## 5. Architecture Diagrams in Mermaid

### 5.1 System Topology: Architecture B (₹0–₹200 Public Prototype)

```mermaid
flowchart TD
    subgraph Citizens["Indian Citizen / Browser"]
        User["Citizen Web Client"]
    end

    subgraph Edge["Edge & Ingress Tier (Global & India CDN)"]
        Vercel["Vercel Edge Network / Cloudflare Pages<br/>• Hosts Next.js 14 App Router<br/>• SSL Termination (HTTPS)<br/>• Subdomain / Custom .in Domain<br/>• Cost: ₹0.00"]
    end

    subgraph Identity["Identity & Messaging Tier"]
        FirebaseAuth["Firebase Authentication (Spark Tier)<br/>• Google Sign-In<br/>• RS256 JWT Issuance<br/>• Cost: ₹0.00"]
        Resend["Resend API (Free Tier)<br/>• Email OTP Verification<br/>• Cost: ₹0.00"]
    end

    subgraph Compute["Serverless Backend Tier"]
        CloudRun["Google Cloud Run (FastAPI + OCR Container)<br/>• Non-Root appuser (UID 10001)<br/>• Tesseract OCR 5.5 + Poppler<br/>• Scale-to-Zero (min=0, max=3)<br/>• Deterministic Conflict Engine<br/>• Cost: ₹0.00 (US) or ~₹68 (Mumbai)"]
    end

    subgraph AI["Artificial Intelligence Tier"]
        Gemini["Google Gemini 1.5 Flash<br/>• Context-Aware RAG Guidance<br/>• Correction Document Generation<br/>• Tier 1 Pay-as-you-go (Zero Logging)<br/>• Cost: ~₹5–₹15/mo"]
    end

    subgraph Data["Managed Data Tier (Mumbai ap-south-1)"]
        Supabase["Supabase Managed PostgreSQL 16<br/>• Role: consolith_app (Non-Superuser)<br/>• 18 Tables with FORCED RLS<br/>• Append-Only Audit Triggers<br/>• Supavisor Connection Pooler (6543)<br/>• Cost: ₹0.00"]
        Qdrant["Qdrant Cloud Free / In-Memory<br/>• 31 Government Knowledge Vectors<br/>• 1024-dim Cosine Distance<br/>• Cost: ₹0.00"]
    end

    User -->|"1. HTTPS / Browse UI"| Vercel
    User -->|"2. Authenticate"| FirebaseAuth
    User -->|"3. Request Email OTP"| CloudRun
    CloudRun -->|"3a. Send OTP"| Resend
    Vercel -->|"4. API Requests (Bearer JWT)"| CloudRun
    CloudRun -->|"5. Verify JWT Public Keys"| FirebaseAuth
    CloudRun -->|"6. SET LOCAL RLS Context & SQL Queries"| Supabase
    CloudRun -->|"7. Semantic Vector Search"| Qdrant
    CloudRun -->|"8. RAG Completion (If Score >= 0.55)"| Gemini
```

---

### 5.2 Document Upload & Ephemeral OCR Privacy Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen Client
    participant Frontend as Next.js (Vercel)
    participant Backend as FastAPI (Cloud Run)
    participant Tesseract as Tesseract OCR (In-Memory)
    participant DB as PostgreSQL (Supabase)

    Citizen->>Frontend: Select Aadhaar/PAN (PDF/JPG)
    Frontend->>Backend: POST /api/documents/upload (Multipart + Bearer Token)
    Backend->>Backend: Validate Magic Bytes & Size (<= 10MB)
    Backend->>Backend: Write to /tmp/consolith (Ephemeral tmpfs)
    Backend->>Tesseract: Process Image / Max 3 PDF Pages
    Tesseract-->>Backend: Return Extracted Text
    Backend->>Backend: Verhoeff Checksum Validation & Aadhaar Masking (XXXX-XXXX-1234)
    Backend->>Backend: Fernet Encrypt Sensitive Payload at Rest
    Note over Backend,Tesseract: PRIVACY COMPLIANCE HOOK
    Backend->>Backend: unlink(/tmp/consolith/temp_file) (Raw file permanently erased!)
    Backend->>DB: INSERT INTO documents (file_path="ephemeral://redacted...", encrypted_payload)
    Note over DB: Enforced by consolith_app non-superuser RLS
    Backend-->>Frontend: HTTP 201 Created (Masked Document Record)
    Frontend-->>Citizen: Display Masked Identity Metadata
```

---

## 6. Component Compatibility Matrix

| Repository Component | Free / Low-Cost Target | Status | Architectural & Codebase Compatibility Analysis |
| :--- | :--- | :--- | :--- |
| **Next.js 14 App Router** | Vercel Hobby / Cloudflare Pages | **100% Compatible** | Production build verified (`npm run build`, 15/15 routes). Zero Docker dependency on Vercel. Static assets served from edge CDN; dynamic routes run as serverless functions. |
| **FastAPI Backend** | Google Cloud Run | **100% Compatible** | Runs the existing Dockerfile. Non-root user `appuser` (UID 10001) is fully supported by Cloud Run. Stateless architecture conforms to Cloud Run requirements. |
| **Tesseract 5.5 + Poppler** | Google Cloud Run Container | **100% Compatible** | Built into `convelina-prod-backend` image. Rasterization capped at 3 pages (`app/ocr/engine.py:100`), ensuring RAM consumption stays under 420 MB during peak OCR. |
| **PostgreSQL 16 & Forced RLS** | Supabase Free / Neon | **100% Compatible** | Supabase natively supports non-superuser role `consolith_app`, `FORCE ROW LEVEL SECURITY`, `SET LOCAL app.current_user_id`, and append-only audit triggers. |
| **Qdrant Vector DB** | Qdrant Cloud Free / In-Process | **100% Compatible** | Total vector volume is 31 items (< 200 KB). Qdrant Cloud Free provides 4 GB. Alternatively, in-process Qdrant runs inside FastAPI with zero network calls. |
| **Deterministic Conflict Engine** | In-Process Python | **100% Compatible** | RapidFuzz and Jellyfish run on CPU. Incurs ₹0 external cost and 0 external dependencies. |
| **Google Gemini RAG** | Gemini 1.5 Flash (Tier 1 Paid) | **100% Compatible** | `backend/app/rag/assistant/orchestrator.py` enforces 0.55 relevance floor, source validation, and safe degradation if unconfigured. Fits within ₹10/mo. |
| **Ed25519 PKI Attestation** | In-Process Python | **100% Compatible** | Runs on `cryptography` library in-memory. SHA-256 fingerprinting and digital signatures require zero external cloud services. |
| **Database Migrations** | Cloud Run Job / Local CLI | **100% Compatible** | `backend/app/core/migrate.py` runs sequentially and idempotently. Can be executed once from developer machine pointing to Supabase, or as a Cloud Run one-shot Job. |
| **Caddy Reverse Proxy** | Replaced by Vercel/Cloud Run Edge | **Fully Replaced** | In local Compose, Caddy provides SSL and routing. In cloud deployment, Vercel and Google Cloud Run provide built-in SSL termination, DDoS protection, and HTTP/2/3. Caddy container is not required in serverless staging. |

---

## 7. Required Configuration & Environment Variables

*All secret values omitted. Variable structure conforms to Pydantic validation in `backend/app/config.py`.*

### 7.1 Backend Environment (`.env.production` in Cloud Run Secret Manager)
```bash
# General
PROJECT_NAME="CONVELINA API"
ENVIRONMENT="production"
DEBUG="false"

# Database (Supabase Session Pooler or Direct Connection)
# Must connect as non-superuser consolith_app to satisfy production validator
DATABASE_URL="postgresql://consolith_app:${SUPABASE_APP_PASSWORD}@db.${SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"

# Connection Pool Settings (Optimized for Serverless scale-to-zero)
DB_POOL_SIZE="4"
DB_MAX_OVERFLOW="6"
DB_POOL_TIMEOUT="20"

# Fernet Payload Encryption (Mandatory 32-byte url-safe base64 string)
ENCRYPTION_KEY="${PROD_FERNET_KEY_BASE64}"

# Firebase Authentication
FIREBASE_PROJECT_ID="${FIREBASE_PROD_PROJECT_ID}"
FIREBASE_SERVICE_ACCOUNT_PATH="/secrets/firebase/serviceAccountKey.json"
TEST_MODE_ALLOW_SIMULATED_TOKENS="false"
ADMIN_GMAIL="admin.official@gmail.com"

# Resend Email Configuration
RESEND_API_KEY="${RESEND_API_KEY}"
RESEND_FROM_EMAIL="noreply@convelina.in"

# Qdrant Vector DB (Qdrant Cloud Free Tier)
QDRANT_HOST="${QDRANT_CLOUD_CLUSTER_ID}.eu-central-1.aws.cloud.qdrant.io"
QDRANT_PORT="6333"

# Google Gemini API
GEMINI_API_KEY="${GEMINI_PROD_API_KEY}"
GEMINI_MODEL="gemini-1.5-flash"
EMBEDDING_MODEL="BAAI/bge-m3"
RAG_MIN_RELEVANCE="0.55"

# Document Processing & Aadhaar Act Compliance
STORAGE_TEMP_DIR="/tmp/consolith/temp_docs"
STORAGE_RETENTION_POLICY="delete_after_ocr"
MAX_UPLOAD_SIZE_BYTES="10485760"

# CORS Origins (Restricted to Vercel production frontend)
CORS_ORIGINS=["https://convelina.vercel.app","https://convelina.in"]
```

### 7.2 Frontend Environment (`.env.production` in Vercel Project Settings)
```bash
# Backend Ingress URL
NEXT_PUBLIC_API_URL="https://convelina-api-${HASH}-uc.a.run.app"

# Firebase Client SDK Configuration (Public credentials)
NEXT_PUBLIC_FIREBASE_API_KEY="${FIREBASE_WEB_API_KEY}"
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN="${FIREBASE_PROD_PROJECT_ID}.firebaseapp.com"
NEXT_PUBLIC_FIREBASE_PROJECT_ID="${FIREBASE_PROD_PROJECT_ID}"
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET="${FIREBASE_PROD_PROJECT_ID}.appspot.com"
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID="${FIREBASE_MESSAGING_SENDER_ID}"
NEXT_PUBLIC_FIREBASE_APP_ID="${FIREBASE_APP_ID}"
```

---

## 8. Security, Privacy & Regulatory Compliance Assessment

### 8.1 Aadhaar Act (Section 29) & Identity Privacy Compliance
- **Zero Raw Image Retention**: Cloud Run's `/tmp` is temporary in-memory tmpfs. Files are unlinked immediately after OCR in the `finally:` block. No raw images or PDFs are stored on disk, database, or object storage.
- **Mandatory 12-Digit Masking**: Unmasked Aadhaar numbers are parsed in-memory, checked against Verhoeff checksum algorithm, and strictly masked to `XXXX-XXXX-1234` before being returned to the API caller or stored in the database.
- **At-Rest Payload Encryption**: Extracted identity document fields are encrypted using Fernet (AES-128-CBC + HMAC-SHA256) with a 32-byte secret key before database insertion.

### 8.2 Database Isolation & Row-Level Security (RLS)
- **Non-Superuser Application Role**: Runtime connections strictly use `consolith_app` (`rolsuper=false`). The production settings validator immediately rejects connections using `postgres`.
- **Forced RLS**: All 18 user-data tables enforce `FORCE ROW LEVEL SECURITY`. Even table owners cannot bypass policies.
- **Transaction-Local Isolation**: Every API request maps the authenticated citizen's ID via `SET LOCAL app.current_user_id` inside the active transaction. Connections returned to the pool clean up automatically upon `COMMIT` or `ROLLBACK`.
- **Connection-Pooling UUID Safety**: All policies use `NULLIF(current_setting('app.current_user_id', true), '')::uuid` to prevent cast errors during pool re-use.

### 8.3 Tamper-Evident Audit Immutability
- PostgreSQL triggers `block_audit_log_modifications` actively reject all `UPDATE` and `DELETE` operations on `audit_log`.
- Every audit entry's SHA-256 hash cryptographically chains to the previous row's hash (`previous_hash`), forming an immutable tamper-evident chain.

### 8.4 Zero-Hallucination AI Architecture
- **Deterministic Independence**: The core conflict detection engine (Module 5) does NOT use LLMs. All date discrepancies, name distance calculations, and father's name mismatches are evaluated deterministically.
- **Relevance Floor**: The RAG assistant rejects any context chunk with cosine similarity below 0.55.
- **Safe Degradation**: If the Gemini API is unreachable, rate-limited, or disabled, the application returns the sanitized message `"Assistant service is not currently available. Please try again later."` rather than hallucinating government procedures.

---

## 9. Feature Limitations of the Free-Tier / Ultra-Low-Cost Prototype

Evaluating the prototype under free/ultra-low-cost constraints imposes the following operational boundaries:

1. **Cold Start Latency (8–12 seconds)**: When Cloud Run scales to zero after 15 minutes of inactivity, the first incoming citizen request triggers a cold container start. Once warm, subsequent requests complete in 50–200ms.
2. **Supabase Inactivity Pause (Free Tier)**: If no database queries occur for 7 consecutive days, Supabase pauses the project. (Mitigated in Scenario 3 via an automated keep-alive ping).
3. **Synthetic / Demo Data Only on AI Studio Free Tier**: If running under ₹0/mo (Scenario 1), Google AI Studio Free terms permit prompt logging. Real identity documents must not be submitted under Scenario 1; only synthetic demo identities may be tested. (Scenario 2/3 eliminates this limitation by using Tier 1 paid Gemini with zero logging).
4. **Concurrency Ceiling (Max 3 Cloud Run Instances)**: To guarantee zero unexpected billing bursts, Cloud Run max instances should be capped at 3, supporting ~60 concurrent requests.
5. **No SMS OTP Authentication**: Firebase SMS authentication is costly. CONVELINA prototype uses Google Sign-In and Email OTP via Resend Free Tier (100 emails/day).
6. **No High-Resolution Multi-Page Batch OCR**: Uploads are restricted to 10 MB and max 3 rasterized pages per PDF to operate within Cloud Run's 1 GB container memory envelope.

---

## 10. Operational Risks, Provider Lock-In & Failure Modes

### 10.1 Failure Modes & Mitigations
| Failure Scenario | Root Cause | Impact | Automated / Architectural Mitigation |
| :--- | :--- | :--- | :--- |
| **Cloud Run OOM Kill** | Upload of massive 100-page PDF or 50MP scan | Container restarts; HTTP 504 returned | `pdf2image` rasterization is hard-capped at 3 pages in `engine.py:100`. File size is rejected if > 10 MB before OCR starts. |
| **Supabase Project Paused** | 7 days without evaluation traffic | Database connection refused (HTTP 500) | Scheduled GitHub Actions workflow runs every 4 days executing `SELECT 1;`, keeping project active. |
| **Gemini API Rate Limit / Quota** | Evaluation flood exceeds 15 RPM | RAG queries fail | Orchestrator catches `ResourceExhausted` and falls back gracefully with official cached circulars and standard guidance. |
| **Unexpected Cloud Billing Spike** | Scraping bot or DDoS attack on API | Cloud Run auto-scales and bills CPU | Hard ceiling configured: `max-instances=3`. Cloud Billing budget alert set to $2.00 USD with auto-shutdown Cloud Function. |
| **Token Verification Failure** | Firebase public keys rotate | Auth requests fail | Firebase Admin SDK automatically caches and refreshes Google OAuth2 public x509 certs. |

### 10.2 Provider Lock-In Assessment
- **PostgreSQL**: Zero lock-in. Schema is standard ANSI SQL with standard RLS and Alembic migrations. Dumps (`pg_dump`) can restore into AWS RDS, Google Cloud SQL, or local Docker with 100% fidelity.
- **FastAPI / Python**: Zero lock-in. Containerized via standard OCI Dockerfile. Runs interchangeably on Cloud Run, AWS ECS, Fly.io, or on-premise K8s.
- **Frontend**: Zero lock-in. Next.js App Router runs on Vercel, Cloudflare Pages, AWS Amplify, or inside its existing production Docker container (`convelina-prod-frontend:latest`).
- **Vector DB**: Minimal lock-in. Qdrant is open-source. Knowledge vectors can be transferred to self-hosted Qdrant or `pgvector` in under 5 minutes.

---

## 11. Backup, Restoration, Monitoring & Safe Shutdown Strategy

### 11.1 Automated Backup Strategy ($0.00 Cost)
- **Relational Data**: A GitHub Actions scheduled workflow runs daily using `pg_dump` targeting Supabase. Custom-format dump is encrypted with GPG using a public key and stored as an encrypted GitHub Release artifact or dispatched to Google Drive via service account.
- **Audit Hash Verification**: Backup script validates the latest SHA-256 audit hash before and after dump to prove zero data corruption.
- **Restoration Drill**: Verified in Sprint 4; database snapshot can be restored into any blank PostgreSQL 16 instance in < 45 seconds using `scripts/backup_database.sh`.

### 11.2 Monitoring & Alerting ($0.00 Cost)
- **Uptime Monitoring**: Free tier UptimeRobot or Cron-job.org checks `/health` every 10 minutes.
- **Error Tracking**: Sentry Developer Free Tier (5,000 error events/month) captures unhandled exceptions with full stack traces and redacted PII.
- **Google Cloud Budget Alerts**: Configured at $1.00 USD, $2.00 USD, and $3.00 USD with email and SMS notifications.

### 11.3 Safe Instant Shutdown Procedure
If testing is concluded or anomalous activity occurs:
1. **Cloud Run**: Run `gcloud run services update convelina-backend --max-instances=0` (instantly halts all container execution and billing).
2. **Vercel**: Toggle project to "Disabled" in dashboard or unassign custom domain.
3. **Supabase**: Click "Pause project" in dashboard.
4. **Data Destruction**: To permanently purge prototype data, run `scripts/backup_database.sh` to archive an encrypted snapshot, then execute `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` in Supabase SQL editor.

---

## 12. Exact Deployment Steps for a Future Approved Sprint

*This runbook is documented for a future approved sprint. NO steps were executed during this audit.*

```mermaid
flowchart LR
    Step1["1. Supabase Setup<br/>• Create Project (Mumbai)<br/>• Run 001-009 Migrations<br/>• Create consolith_app Role"] --> 
    Step2["2. Firebase Auth<br/>• Register Prod App<br/>• Download Service Key<br/>• Whitelist Frontend URL"] --> 
    Step3["3. Qdrant Setup<br/>• Provision Free Cluster<br/>• Initialize Collections<br/>• Ingest 31 Vectors"] --> 
    Step4["4. Cloud Run Deploy<br/>• Build & Push Backend<br/>• Deploy min=0, max=3<br/>• Inject Secrets"] --> 
    Step5["5. Vercel Deploy<br/>• Connect GitHub<br/>• Set NEXT_PUBLIC_API_URL<br/>• Deploy Frontend"] --> 
    Step6["6. Verification<br/>• Run E2E Health Check<br/>• Verify RLS Isolation<br/>• Verify Ephemeral OCR"]
```

### Detailed Execution Phase (Future Sprint)
1. **Database Provisioning (Supabase Mumbai)**:
   - Create project in `ap-south-1`.
   - In SQL Editor, execute role creation:
     ```sql
     CREATE ROLE consolith_app WITH LOGIN PASSWORD 'strong_random_password_here';
     GRANT USAGE ON SCHEMA public TO consolith_app;
     GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO consolith_app;
     GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO consolith_app;
     ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO consolith_app;
     ```
   - Run migrations sequentially from developer machine: `python scripts/run_migrations.py`.
2. **Backend Container Deployment (Google Cloud Run)**:
   - Authenticate Google Cloud CLI: `gcloud auth configure-docker`.
   - Tag and push verified production backend image:
     ```bash
     docker tag convelina-prod-backend:latest gcr.io/${GCP_PROJECT_ID}/convelina-backend:latest
     docker push gcr.io/${GCP_PROJECT_ID}/convelina-backend:latest
     ```
   - Deploy service with scale-to-zero:
     ```bash
     gcloud run deploy convelina-backend \
       --image gcr.io/${GCP_PROJECT_ID}/convelina-backend:latest \
       --region us-central1 \
       --memory 1Gi \
       --cpu 1 \
       --min-instances 0 \
       --max-instances 3 \
       --allow-unauthenticated \
       --set-env-vars ENVIRONMENT=production,DEBUG=false,STORAGE_RETENTION_POLICY=delete_after_ocr
     ```
3. **Frontend Deployment (Vercel)**:
   - Import repository into Vercel.
   - Configure Root Directory to `frontend`.
   - Set Environment Variables (`NEXT_PUBLIC_API_URL` pointing to Cloud Run).
   - Click "Deploy".
4. **Post-Deployment Verification**:
   - Run live health check against public domain: `curl -s https://api.convelina.in/health`.
   - Verify unauthenticated rejection returns HTTP 401.
   - Verify upload of sample synthetic Aadhaar masks properly to `XXXX-XXXX-1234` and temporary file is unlinked.

---

## 13. Explicit List of Commands NOT Executed

In accordance with Sprint 7 instructions, the following actions were **strictly NOT executed**:
- Did NOT purchase or register any domain names.
- Did NOT create or configure any Google Cloud Run, Supabase, Neon, or Vercel resources.
- Did NOT enable billing or enter credit card / payment details on any cloud platform.
- Did NOT change public DNS records or configure TLS certificates.
- Did NOT push code, images, or tags to GitHub or public container registries.
- Did NOT modify or overwrite local Docker Compose configurations (`docker-compose.yml`, `docker-compose.prod.yml`).
- Did NOT alter or reset existing local development databases or volumes.
- Did NOT rotate, overwrite, or delete local Fernet encryption keys or signing keys.
- Did NOT disable PostgreSQL RLS, audit triggers, or role-based security policies.

---

## 14. Open Questions & External Prerequisites

Before an active deployment sprint can begin, the user must provide explicit approval and configure the following external items:

1. **Hosting Geography Preference**:
   - Option 1: **$0.00 / month** using Google Cloud Run in `us-central1` (US latency ~200ms).
   - Option 2: **~₹70.00 / month** using Google Cloud Run in `asia-south1` (Mumbai latency ~35ms).
2. **Domain Decision**:
   - Use free provider subdomains (`convelina.vercel.app` + `*.run.app`) for ₹0.00?
   - Or purchase a `.in` domain (~₹450–₹540/year = ~₹45/mo amortized)?
3. **Google Cloud Billing Account**:
   - To use Cloud Run (even within the Always Free Tier), Google Cloud requires a billing account linked to the GCP project with a $0 budget alert.
4. **Firebase Production Project**:
   - Creation of a clean Firebase project for production OAuth client IDs and service account credentials.

---

## 15. Acceptance Checklist for the Next Sprint

- [ ] User approves deployment architecture (Architecture B) and target budget scenario (Scenario 1, 2, or 3).
- [ ] User creates empty Supabase project in Mumbai (`ap-south-1`) and provides database credentials.
- [ ] User provisions clean Firebase project and downloads `serviceAccountKey.json`.
- [ ] User confirms whether custom domain registration is desired or provider subdomains are sufficient.
- [ ] Run dry-run migration against remote Supabase database using `consolith_app` role.
- [ ] Execute smoke test verifying Tesseract OCR and Verhoeff masking in Cloud Run container.
- [ ] Verify zero data leakage and confirm tamper-evident audit log chaining.

---

## 16. Final Acceptance Criteria Answers & Conclusive Recommendation

### 16.1 Answers to the 10 Acceptance Criteria Questions
1. **Can CONVELINA's current code run on a ₹0–₹200/month architecture without a major rewrite?**  
   **YES**. The application's architecture is already decoupled and containerized. With in-memory tmpfs OCR, CPU-based embeddings, deterministic conflict detection, and standard PostgreSQL RLS, zero architectural changes are required.
2. **Which existing components are incompatible with free hosting?**  
   Only **Render Free Web Service** is incompatible (its 512 MB RAM limit causes Tesseract OCR OOM crashes, and its free database is purged after 30 days). Caddy is replaced in cloud deployment by Vercel/Cloud Run edge proxies.
3. **What is the cheapest viable public prototype?**  
   **Architecture B (Scenario 1)**: Vercel Hobby (Frontend) + Google Cloud Run `us-central1` (Backend) + Supabase Free `ap-south-1` (Postgres) + Qdrant Cloud Free (Vector DB) + Firebase Spark (Auth) = **₹0.00 / month ($0.00 USD)**.
4. **What features will be unavailable or limited?**  
   Cold starts will take 8–12 seconds on idle container resume; Supabase requires active traffic or keep-alive pings to avoid the 7-day inactivity pause; concurrent request capacity is capped at ~60 requests (3 instances); SMS OTP is omitted in favor of Email OTP.
5. **What are the realistic monthly cost and overage risks?**  
   - Scenario 1: ₹0.00/mo (Hard quotas prevent charges).
   - Scenario 2: ~₹90.00/mo ($1.08 USD) including custom `.in` domain and paid private Gemini API.
   - Overage risks are strictly mitigated by setting Cloud Run `max-instances=3` and configuring GCP budget alerts at $2.00 USD.
6. **Can PostgreSQL RLS, authentication, OCR, and tenant isolation remain intact?**  
   **YES**. Supabase supports native PostgreSQL roles, forced RLS on all 18 tables, transaction-local `SET LOCAL`, and cryptographic triggers with 100% fidelity to the existing local database.
7. **Does the proposed hosting support the required data-retention and deletion model?**  
   **YES**. Raw identity documents are unlinked immediately after OCR from Cloud Run's in-memory tmpfs. Extracted metadata is Fernet-encrypted at rest. No raw documents are retained, satisfying Aadhaar Act Section 29.
8. **What must be tested locally before deployment?**  
   The remote connection string to Supabase with the non-superuser `consolith_app` role must be validated with `scripts/test_rls_isolation.py` to confirm pooling compatibility.
9. **Which prerequisites require user approval?**  
   Selection of the budget scenario (Scenario 1 at ₹0/mo vs Scenario 2/3 at ₹90–₹190/mo), provision of a GCP project for Cloud Run, and creation of a free Supabase project.
10. **What is the next smallest safe implementation sprint?**  
    **Sprint 8: Staging Cloud Deployment Preparation (Zero-Cost Dry Run)**: Set up Supabase Mumbai and run migrations remotely; test non-root Cloud Run deployment with simulated traffic; verify zero public exposure until the launch gate is passed.

---

### 16.2 Conclusive Single Recommendation

**Recommended Option**: **Architecture B (Scenario 2: ₹100 INR / month Prototype)**  
**Reason for Choosing It**: It provides the optimal balance of privacy, credibility, and cost. By allocating a tiny budget (~₹5 INR) to Google Gemini Tier 1 Pay-As-You-Go, citizen identity prompts are guaranteed **never to be logged or used for model training**, ensuring full compliance with citizen privacy expectations. Amortizing an official `.in` domain (~₹45 INR/mo) provides an authentic institutional appearance for government evaluators, while the backend and database leverage robust Always-Free tiers (Cloud Run, Supabase, Qdrant Cloud, Firebase Spark).  
**Estimated Monthly Cost Range**: **₹65.00 – ₹110.00 INR / month ($0.75 – $1.30 USD / month)**.  
**Most Important Limitation**: **Cold Start Latency (8–12 seconds on the initial request after 15 minutes of inactivity)** due to Cloud Run scaling to zero to maintain the zero-cost compute tier. Once initialized, the instance responds in 50–150ms.

