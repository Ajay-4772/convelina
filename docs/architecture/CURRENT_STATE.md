# CONVELINA — Current Architecture State

**Document Classification:** Internal Architecture Baseline  
**Audit Date:** October 28, 2026  
**Status:** EVIDENCE-BASED AUDIT BASELINE  

---

## 1. System Topology Overview

CONVELINA is architected as a modular monolith orchestrated across four primary service tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CITIZEN & ADMIN FRONTEND                        │
│                   Next.js 14 App Router • React 18                     │
│         Google Stitch Minimalist Design (#FAF9F6, Inter, Merriweather) │
│       Routes: /app (Overview), /inconsistencies, /assistant, /forms,   │
│               /profile, /login, /signup, /admin (Isolated Subdomain)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (JWT Bearer Token)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND SERVICE                         │
│           Python 3.11 • Starlette Middleware • Pydantic v2            │
│         Auth Guards • Magic Byte Validator • Tesseract 5.5 OCR         │
│           Deterministic Conflict Matcher • Google Gemini RAG           │
└───────┬───────────────────────────┼───────────────────────────┬────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐            ┌──────────────┐            ┌──────────────┐
│  OCR ENGINE  │            │ CONFLICT DET │            │  RAG ENGINE  │
│  Tesseract   │            │  RapidFuzz   │            │ Qdrant v1.11 │
│ Poppler PDF  │            │  Metaphone   │            │ Google Gemini│
│Ephemeral /tmp│            │ Deterministic│            │ BGE-M3 1024d │
└───────┬──────┘            └───────┬──────┘            └───────┬──────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  POSTGRESQL 16 DATABASE (FORCED RLS)                   │
│        Dedicated Least-Privilege App Role: `consolith_app`             │
│    Tables: users, documents, conflicts, correction_drafts, cases,      │
│            signing_keys, document_attestations, audit_log (immutable) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Inventory & Operational Status

| Component | Technology | File / Path | Operational Status | Evidence & Notes |
| :--- | :--- | :--- | :---: | :--- |
| **Workspace Shell** | Next.js 14 / Tailwind | `frontend/src/app/app/layout.tsx` | **VERIFIED** | Google Stitch design system implemented; fixed desktop sidebar (`w-64`), mobile drawer, top header without sensitive search, persistent WORKSPACE badge. |
| **Overview Page** | Next.js 14 App Router | `frontend/src/app/app/page.tsx` | **VERIFIED** | Real profile welcome, 3 primary action cards, audit-backed recent activity stream with honest empty state. Route redirect for old `?tab=...` bookmarks. |
| **Inconsistencies Route** | Next.js 14 App Router | `frontend/src/app/app/inconsistencies/page.tsx` | **VERIFIED** | Document upload with magic byte check, OCR extraction feedback, file list with deletion, deterministic conflict detection trigger, side-by-side discrepancy cards. |
| **AI Assistant Routes** | Next.js 14 App Router | `frontend/src/app/app/assistant/` | **VERIFIED** | Root and dynamic `[conversationId]` routes; session history drawer; discourse stream; grounded citations display; exact error fallback contract. |
| **Forms Repository Routes**| Next.js 14 App Router | `frontend/src/app/app/forms/` | **VERIFIED** | Root and dynamic `[formId]` routes; real backend binding to `/api/v1/knowledge/forms`; search filter; category pills; prerequisites checklists; verified PDF downloads. |
| **Profile Settings** | Next.js 14 App Router | `frontend/src/app/app/profile/page.tsx` | **VERIFIED** | Authenticated personal coordinates (view/edit mode), security provider info, cascading account deletion modal. Zero mock data. |
| **Admin Console** | Next.js 14 App Router | `frontend/src/app/admin/page.tsx` | **VERIFIED** | Scoped to admin subdomain via `src/middleware.ts`; telemetry metrics, citizen account management, append-only audit trail viewer. |
| **API Client** | TypeScript / Fetch | `frontend/src/lib/api.ts` | **VERIFIED** | Strongly typed client with real JWT Bearer token propagation; handles empty responses, 404s, and structured errors. |
| **FastAPI Core** | FastAPI / Python 3.11 | `backend/app/main.py` | **VERIFIED** | Lifespan Firebase initialization, security response headers (`nosniff`, `DENY`), CORS origins, healthcheck endpoint. |
| **Document Upload & OCR** | Tesseract 5.5 / Poppler | `backend/app/routers/documents.py` | **VERIFIED** | Bounded 1MB chunked stream up to 10MB; magic byte header check; Aadhaar first-8-digit masking (`XXXX-XXXX-1234`); ephemeral file unlinking post-extraction. |
| **Deterministic Conflict Engine** | RapidFuzz / Metaphone | `backend/app/conflicts/` | **VERIFIED** | Token-sort ratio, Soundex/Metaphone phonetic analysis, calendar normalization with year-only compatibility; independent of LLM. |
| **RAG Knowledge Assistant**| Qdrant / Google Gemini | `backend/app/rag/` | **VERIFIED** | 1024-dim deterministic BGE semantic embeddings; relevance floor $\ge 0.55$; citation validation against retrieved chunks; single-provider Google Gemini. |
| **Case & Officer Workflow**| FastAPI Router | `backend/app/routers/cases.py`, `officer.py` | **PARTIAL** | Complete ORM models, state machine, and routers exist in code, but routes are currently **unmounted in `main.py`** due to citizen-only portal scoping. |
| **Database & RLS** | PostgreSQL 16 Alpine | `backend/migrations/001-009` | **VERIFIED** | Forced RLS across all user tables; dedicated non-superuser role `consolith_app`; connection-pooling-safe `NULLIF(..., '')::uuid`; append-only audit trigger. |
| **Ed25519 PKI Attestation**| PyNaCl / RFC 8032 | `backend/app/services/pki_service.py` | **VERIFIED** | RFC 8785 canonical JSON serialization, Ed25519 keypair generation, digital signature signing, verification status state machine. |
| **Container Orchestration**| Docker Compose | `docker-compose.yml` | **VERIFIED** | Multi-container stack (Postgres, Qdrant, Backend, Frontend) with healthchecks and volume persistence. (Note: host Docker daemon was offline during audit). |

---

## 3. Configuration & Environment Variables

| Variable | Current Default / Fallback | Production Constraint | Validation Status |
| :--- | :--- | :--- | :---: |
| `ENVIRONMENT` | `development` | Must be `production` | Enforced in `config.py` |
| `DEBUG` | `True` | **Forbidden** in production (`@model_validator` raises error) | Enforced in `config.py` |
| `DATABASE_URL` | `postgresql://consolith_app:...@postgres:5432/consolith` | Non-superuser role `consolith_app` mandatory | Enforced in migrations & config |
| `ENCRYPTION_KEY` | `consolith_dev_fernet_secret_key_32_bytes_len=` | Default key **forbidden** in production | Enforced in `config.py` |
| `TEST_MODE_ALLOW_SIMULATED_TOKENS` | `False` (`True` in compose dev) | **Forbidden** in production | Enforced in `config.py` |
| `GEMINI_API_KEY` | `None` (set via env) | Required for live RAG generation; fallback returns service unavailable | Handled safely in `GoogleGeminiProvider` |
| `MAX_UPLOAD_SIZE_BYTES` | `10485760` (10 MB) | Enforced via streaming chunk abort | Enforced in `documents.py` |
| `STORAGE_RETENTION_POLICY`| `delete_after_ocr` | Unlinks raw temporary files in `finally:` block | Enforced in `storage.py` |

