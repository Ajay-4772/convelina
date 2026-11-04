# CONVELINA — Target Architecture State

**Document Classification:** Strategic Engineering Architecture  
**Target Horizon:** Production Hardening (Phase 1 through Phase 10)  
**Architectural Style:** Secure Modular Monolith  

---

## 1. Architectural Philosophy & Invariants

CONVELINA targets an enterprise-grade, privacy-first identity discrepancy resolution platform for Indian citizens. To maintain high reliability and operational simplicity without unwarranted infrastructure sprawl, the following architectural invariants are locked:

1. **Modular Monolith Integrity**: No microservices, Kafka, RabbitMQ, or Kubernetes clusters. A single decoupled FastAPI backend and Next.js frontend running alongside PostgreSQL and Qdrant fulfill all product requirements with minimal operational surface.
2. **Defensive Database Kernel**: Security is enforced at the PostgreSQL kernel level using forced Row-Level Security (`FORCE ROW LEVEL SECURITY`), executed via an unprivileged role (`consolith_app`), and guarded by pooling-safe session variables.
3. **Statutory Aadhaar Compliance**: Absolute prohibition on persistent storage of raw Aadhaar documents or unmasked 12-digit identity numbers. Ingestion must follow ephemeral streaming, in-memory OCR extraction, immediate file shredding, and `XXXX-XXXX-1234` masking.
4. **Deterministic Precedence over LLMs**: Document discrepancy detection is 100% deterministic (Levenshtein, token-sort, Soundex, Double Metaphone, calendar normalization). LLMs are restricted strictly to explaining legal circulars, advising on statutory forms, and drafting correction petitions—never making identity matching decisions.
5. **Cryptographic Tamper-Evidence**: Document attestations use Ed25519 digital signatures (RFC 8032) with RFC 8785 canonical JSON payloads. Audit logs maintain an unbroken SHA-256 cryptographic chain where database triggers reject any `UPDATE` or `DELETE`.

---

## 2. Target Component Architecture

```
                                  PUBLIC INTERNET
                                         │
                                         ▼ [TLS 1.3 / Strict-Transport-Security]
                            ┌────────────────────────┐
                            │ Reverse Proxy (Caddy)  │
                            └────┬──────────────┬────┘
                                 │              │
                   Host: convelina.in           │ Host: admin.convelina.in
                                 │              │
                                 ▼              ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS 14 APP ROUTER                           │
│  Public Routes: / (Landing), /login, /signup, /verify-email            │
│  Citizen Workspace (/app):                                             │
│    • /app (Overview with personalized welcome & real activity)         │
│    • /app/inconsistencies (Upload, OCR, deterministic conflict list)   │
│    • /app/assistant & /[conversationId] (RAG discourse stream)         │
│    • /app/forms & /[formId] (Statutory forms catalog & downloads)      │
│    • /app/profile (Account settings, security, account deletion)       │
│  Admin Console (/admin): Scoped strictly to admin subdomain            │
│  Design System: Google Stitch (#FAF9F6, Inter, Merriweather, 1px rules)│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (JWT Bearer Token)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    FASTAPI 0.115 BACKEND SERVICE                       │
│  Non-root Execution (`USER appuser`) • Strict Pydantic v2 Validation   │
│  Security Headers • 1MB Chunk Streaming Upload • Magic Byte Inspection │
│  Modules:                                                              │
│    • Auth & Session Scoping (/api/v1/auth)                             │
│    • Document Pipeline & OCR (/api/v1/documents)                       │
│    • Conflict Engine (/api/v1/conflicts)                               │
│    • Assistant & RAG (/api/v1/assistant)                               │
│    • Knowledge & Official Forms (/api/v1/knowledge)                    │
│    • Correction Draft Generator (/api/v1/correction-drafts)            │
│    • Case & Verification Workflow (/api/v1/cases, /api/v1/officer)     │
│    • PKI Attestation & QR (/api/v1/pki)                                │
│    • Admin Operations & Telemetry (/api/v1/admin)                      │
└───────┬───────────────────────────┼───────────────────────────┬────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐            ┌──────────────┐            ┌──────────────┐
│  OCR ENGINE  │            │ CONFLICT DET │            │  RAG ENGINE  │
│  Tesseract   │            │  RapidFuzz   │            │ Qdrant v1.11 │
│ Poppler PDF  │            │  Metaphone   │            │ Google Gemini│
│Ephemeral /tmp│            │ Deterministic│            │ BGE-M3 1024d │
│0600 POSIX    │            │ 0% LLM logic │            │ Floor >= 0.55│
└───────┬──────┘            └───────┬──────┘            └───────┬──────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  POSTGRESQL 16 DATABASE (FORCED RLS)                   │
│        Dedicated Least-Privilege App Role: `consolith_app`             │
│  • Forced Row-Level Security on all tenant tables                      │
│  • Session variables cast via `NULLIF(current_setting(...), '')::uuid`  │
│  • Append-Only Audit Log: Database trigger blocks UPDATE / DELETE      │
│  • SHA-256 Hash Chaining: Previous-hash verification                   │
│  • Encrypted Sensitive Payloads at rest via Fernet                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Target State Evolution by Layer

### 3.1 Frontend Evolution
* **Browser-Side Previews**: Implement client-side PDF first-page canvas rasterization (`pdfjs-dist` or browser object URLs) and image thumbnails so raw files never need server round-trips for viewing.
* **Direct Form Autofill**: Allow citizens with detected conflicts to auto-populate official form drafts (e.g. Form 49A, Annexure E) directly into the Correction Document Generator.
* **Accessibility & Fluid Typography**: Standardize WCAG 2.1 AA compliance across all Stitch components, keyboard navigation, and high-contrast focus rings.

### 3.2 Backend & API Evolution
* **Controlled Router Reconnection**: Mount `cases.py` and `officer.py` under explicit RBAC role guards (`require_officer`, `require_admin`) so the verification lifecycle is available without leaking into citizen views.
* **Worker Process Isolation**: Offload heavy OCR processing and ReportLab PDF compilation to background tasks with status polling, keeping HTTP worker event loops unblocked.
* **Non-Root Container Hardening**: Configure Dockerfiles to execute under non-privileged service accounts (`USER appuser`, UID 10001).

### 3.3 Database & Cryptographic Evolution
* **Automated Hash-Chain Verification**: Provide an automated daily cron verification of the entire `audit_log` cryptographic chain to guarantee tamper detection.
* **Cloud KMS / Hardware Keystore Integration**: Transition dev-keystore Ed25519 signing keys to production Google Cloud KMS / AWS KMS envelope signing.

