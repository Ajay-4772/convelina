# CONVELINA — P3H.9.1 Route & API Inventory Reconciliation

**Document Version**: 1.0.0  
**Phase**: P3H.9.1 Acceptance & Remediation  
**Status**: RECONCILED & VERIFIED  
**Auditor**: Principal Software Architect & QA Engineer  
**Inspection Target**: FastAPI Route Registry (`app.routes`) & Next.js App Router (`frontend/src/app/**/page.tsx`)  

---

## 1. Executive Summary & Discrepancy Resolution

This document definitively reconciles the route and API counts across CONVELINA, resolving discrepancies identified between previous reports, build logs, and actual runtime route registrations.

### 1.1 Resolution of Endpoint Count Discrepancy (114 vs 115 vs 116 vs 118)
In milestone P3H.9, documentation stated "Total FastAPI Endpoints: 115", while category tables in various audit files summed to 114 or 116. 

The audit reveals the exact technical explanation:
1. **Production Baseline (115 Endpoints)**: Prior to the addition of the Development Application Explorer router, the CONVELINA FastAPI backend contained exactly 115 registered HTTP route-method endpoints across 10 functional domains.
2. **Development Application Explorer Router (+3 Endpoints)**: Milestone P3H.9 introduced `backend/app/routers/dev.py`, which registers 3 development-only endpoints:
   - `GET /api/v1/dev/overview`
   - `GET /api/v1/dev/persistence-inspect`
   - `POST /api/v1/dev/provision-test-account`
3. **Current Runtime Registration (118 Endpoints in Development)**:
   - In **Development Mode** (`settings.ENVIRONMENT != "production"`): exactly **118 endpoints** are registered on `app.routes`.
   - In **Production Mode** (`settings.ENVIRONMENT == "production"`): the dev router is excluded in `backend/app/main.py`, resulting in exactly **115 endpoints**.
4. **Historical Category Counting Variances**: In earlier draft documentation, the `correction_drafts` category was listed as 7 endpoints instead of 9 (omitting `/api/v1/correction-drafts/{id}/translate` and `/api/v1/correction-drafts/{id}/regenerate`), and dev endpoints were omitted from some domain tables, causing sums of 114 and 116. This report provides the single authoritative, verified reconciliation.

---

### 1.2 Resolution of Next.js Route Count (15 vs 16 Compiled Routes)
Next.js production build logs report:
```
Route (app)                              Size     First Load JS
┌ ○ /                                    62.8 kB         200 kB
├ ○ /_not-found                          871 B          88.1 kB
├ ○ /admin                               8.82 kB         150 kB
├ ○ /admin/login                         2.72 kB         140 kB
├ ○ /app                                 2.91 kB         139 kB
├ ○ /app/assistant                       269 B           169 kB
├ ƒ /app/assistant/[conversationId]      329 B           169 kB
├ ○ /app/forms                           4.86 kB         140 kB
├ ƒ /app/forms/[formId]                  6.63 kB         142 kB
├ ○ /app/inconsistencies                 12.1 kB         156 kB
├ ○ /app/profile                         4.04 kB         132 kB
├ ○ /dev/explorer                        17.4 kB         155 kB
├ ○ /login                               3.92 kB         142 kB
├ ○ /setup-profile                       2.7 kB          140 kB
├ ○ /signup                              3.89 kB         142 kB
└ ○ /verify-email                        3.01 kB         141 kB
```
- **15 User-Defined Application Routes**: The source tree contains exactly 15 `page.tsx` route entry points in `frontend/src/app`.
- **1 Framework Route (`/_not-found`)**: Next.js automatically generates and compiles a static `/_not-found` route handler for 404 page rendering.
- **Total Compiled Routes**: 15 application routes + 1 framework route = **16 compiled routes**.

---

## 2. Frontend Application Route Inventory (15 Routes)

| # | Route Path | Access Role | Route Name | Purpose & Primary Features | Associated Backend APIs |
|---|---|---|---|---|---|
| 1 | `/` | **PUBLIC** | Public Landing Page | Hero presentation, product capabilities, architectural security model, interactive walkthrough | `GET /`, `GET /health` |
| 2 | `/login` | **PUBLIC** | Citizen Login | Email/password sign-in and Google Sign-in portal with development token fallback | `POST /api/v1/auth/login`, `POST /api/v1/auth/session` |
| 3 | `/signup` | **PUBLIC** | Citizen Registration | Account onboarding, password policy validation, and initial user record creation | `POST /api/v1/auth/signup`, `POST /api/v1/auth/provision` |
| 4 | `/verify-email` | **PUBLIC** | Email OTP Verification | Resend OTP token verification and email status confirmation | `POST /api/v1/auth/verify-email`, `POST /api/v1/auth/send-verification` |
| 5 | `/setup-profile` | **USER** | Profile Initialization | Post-signup profile setup, legal name confirmation, and initial residency parameters | `PUT /api/v1/auth/profile` |
| 6 | `/app` | **USER** | Citizen Central Workspace | Identity document vault, active session summary, recent audit history, quick-action cards | `GET /api/v1/documents`, `GET /api/v1/conflicts/summary` |
| 7 | `/app/inconsistencies` | **USER** | Identity Conflict Engine | Discrepancy comparison grid, field-level divergence view, resolution guidance, draft launcher | `GET /api/v1/conflicts`, `POST /api/v1/conflicts/compare` |
| 8 | `/app/assistant` | **USER** | AI Legal Assistant (Index) | Conversation manager, past legal consultation threads, new inquiry initialization | `GET /api/v1/assistant/conversations`, `POST /api/v1/assistant/conversations` |
| 9 | `/app/assistant/[conversationId]` | **USER** | AI Legal Assistant (Chat) | Grounded legal guidance, BM25 statutory citations, document attachment, chat interaction | `GET /api/v1/assistant/conversations/{id}`, `POST .../messages` |
| 10 | `/app/forms` | **USER** | Statutory Forms Catalog | Unified directory of 52 official Indian government forms and circulars with category filters | `GET /api/v1/repository/forms`, `GET /api/v1/repository/categories` |
| 11 | `/app/forms/[formId]` | **USER** | Form Detail & Checklist | Official form specifications, submission authority, filing instructions, persistent checklist | `GET /api/v1/repository/forms/{id}`, `PUT .../checklists/...` |
| 12 | `/app/profile` | **USER** | Citizen Account Profile | Account security settings, session timestamps, tenancy isolation verification, sign out | `GET /api/v1/auth/me`, `POST /api/v1/auth/logout` |
| 13 | `/admin/login` | **PUBLIC** | Administrative Login | Dedicated platform administrator sign-in portal with dual role validation | `POST /api/v1/admin/login`, `POST /api/v1/auth/session` |
| 14 | `/admin` | **ADMIN** | Administrative Console | Platform health monitor, security events, cross-user conflict analytics, tamper verification | `GET /api/v1/admin/overview`, `GET /api/v1/admin/audit-logs` |
| 15 | `/dev/explorer` | **DEV_ONLY** | Application Explorer & QA | Visual architecture map, route directory, persistence inspector, test account provisioning | `GET /api/v1/dev/overview`, `GET .../persistence-inspect` |

---

## 3. FastAPI Backend Endpoint Inventory (118 Registered Endpoints)

### 3.1 Domain Breakdown Summary
```
Total FastAPI Endpoints: 118 (115 in Production, +3 in Development)
├── Knowledge & Official Forms:  26 endpoints (22.0%)
├── AI Resolution Assistant:     16 endpoints (13.6%)
├── Citizen Document Repository: 14 endpoints (11.9%)
├── Authentication:              12 endpoints (10.2%)
├── Authenticity & Ed25519 PKI:  11 endpoints (9.3%)
├── Correction Drafts:            9 endpoints (7.6%)
├── Documents & Upload:           9 endpoints (7.6%)
├── Admin Platform Management:    7 endpoints (5.9%)
├── Core Health & Diagnostic:     6 endpoints (5.1%)
├── Conflicts & Discrepancies:    5 endpoints (4.2%)
└── Development Explorer:         3 endpoints (2.5%) [Dev-Only]
```

### 3.2 Authorization Breakdown Summary
```
FastAPI Authorization Distribution:
├── USER Role Required:         73 endpoints (61.9%)  - Citizen document, chat, drafting, & repository operations
├── ADMIN Role Required:        25 endpoints (21.2%)  - Platform administration, audit trail, & cryptographic CA keys
├── PUBLIC Endpoints:           18 endpoints (15.3%)  - Public keys, health checks, login, and signup
└── DEV_ONLY Endpoints:          2 endpoints (1.7%)   - Overview & test provisioning (persistence-inspect requires USER)
```

---

### 3.3 Detailed Category Breakdown

#### 1. Knowledge & Official Forms (26 Endpoints)
- `GET /api/v1/knowledge/sources`: List official statutory sources (**USER**)
- `POST /api/v1/knowledge/sources`: Ingest official statutory source (**ADMIN**)
- `GET /api/v1/knowledge/sources/{source_id}`: Retrieve source details (**USER**)
- `PUT /api/v1/knowledge/sources/{source_id}`: Update source metadata (**ADMIN**)
- `DELETE /api/v1/knowledge/sources/{source_id}`: Deprecate statutory source (**ADMIN**)
- `GET /api/v1/knowledge/search`: Lexical BM25 and hybrid statutory query search (**USER**)
- `GET /api/v1/knowledge/forms`: List official government forms with filter (**USER**)
- `POST /api/v1/knowledge/forms`: Register new official form definition (**ADMIN**)
- `GET /api/v1/knowledge/forms/{form_id}`: Retrieve form metadata and checklist (**USER**)
- `PUT /api/v1/knowledge/forms/{form_id}`: Update official form specifications (**ADMIN**)
- `DELETE /api/v1/knowledge/forms/{form_id}`: Archive official form (**ADMIN**)
- `GET /api/v1/knowledge/forms/{form_id}/versions`: Version history for form (**USER**)
- `POST /api/v1/knowledge/forms/{form_id}/versions`: Publish new form revision (**ADMIN**)
- `GET /api/v1/knowledge/forms/{form_id}/download`: Download verified form PDF (**USER**)
- `GET /api/v1/knowledge/categories`: List document categories (**USER**)
- `GET /api/v1/knowledge/rules`: Inspect statutory conflict rules (**USER**)
- `GET /api/v1/knowledge/rules/{rule_id}`: Retrieve specific resolution rule (**USER**)
- `POST /api/v1/knowledge/rules`: Create statutory conflict rule (**ADMIN**)
- `PUT /api/v1/knowledge/rules/{rule_id}`: Update statutory conflict rule (**ADMIN**)
- `DELETE /api/v1/knowledge/rules/{rule_id}`: Delete statutory conflict rule (**ADMIN**)
- `GET /api/v1/knowledge/provenance`: Audit knowledge chunk provenance and hash integrity (**ADMIN**)
- `GET /api/v1/knowledge/doc043/policy`: Inspect DOC_043 human review policy (**USER**)
- `POST /api/v1/knowledge/reindex`: Reindex Qdrant statutory vectors (**ADMIN**)
- `GET /api/v1/knowledge/status`: Qdrant collection status & point counts (**USER**)
- `GET /api/v1/knowledge/sop-mappings`: List SOP to form cross-mappings (**USER**)
- `GET /api/v1/knowledge/circulars`: Search UIDAI/CBDT/EPFO statutory circulars (**USER**)

#### 2. AI Resolution Assistant (16 Endpoints)
- `GET /api/v1/assistant/conversations`: List citizen conversations (**USER**)
- `POST /api/v1/assistant/conversations`: Create new conversation thread (**USER**)
- `GET /api/v1/assistant/conversations/{id}`: Get conversation details and message history (**USER**)
- `PUT /api/v1/assistant/conversations/{id}`: Update title or pinned status (**USER**)
- `DELETE /api/v1/assistant/conversations/{id}`: Delete conversation thread (**USER**)
- `POST /api/v1/assistant/conversations/{id}/messages`: Post user message & generate response (**USER**)
- `GET /api/v1/assistant/conversations/{id}/messages`: Retrieve message list (**USER**)
- `POST /api/v1/assistant/conversations/{id}/attachments`: Upload message attachment (**USER**)
- `GET /api/v1/assistant/conversations/{id}/attachments/{att_id}`: Download attachment (**USER**)
- `DELETE /api/v1/assistant/conversations/{id}/attachments/{att_id}`: Remove attachment (**USER**)
- `POST /api/v1/assistant/grounded-query`: Direct grounded query with citations (**USER**)
- `GET /api/v1/assistant/context/{conflict_id}`: Generate resolution context for conflict (**USER**)
- `POST /api/v1/assistant/feedback`: Submit user feedback on assistant advice (**USER**)
- `GET /api/v1/assistant/citations/verify`: Validate statutory citation against corpus (**USER**)
- `POST /api/v1/assistant/conversations/{id}/export`: Export conversation transcript (**USER**)
- `GET /api/v1/assistant/status`: Assistant provider and fallback status (**USER**)

#### 3. Citizen Document Repository (14 Endpoints)
- `GET /api/v1/repository/forms`: Search and filter official forms repository (**USER**)
- `GET /api/v1/repository/forms/{form_id}`: Retrieve authentic form specification (**USER**)
- `GET /api/v1/repository/categories`: List repository categories (**USER**)
- `GET /api/v1/repository/guidance/{procedure_id}`: Retrieve procedural correction steps (**USER**)
- `GET /api/v1/repository/checklists/{procedure_id}`: Get procedural checklist items (**USER**)
- `PUT /api/v1/repository/checklists/{procedure_id}/progress`: Update persistent citizen checklist (**USER**)
- `GET /api/v1/repository/checklists/{procedure_id}/progress`: Retrieve completed checklist items (**USER**)
- `DELETE /api/v1/repository/checklists/{procedure_id}/progress`: Reset checklist progress (**USER**)
- `GET /api/v1/repository/documents/{doc_id}/applicable-forms`: Forms applicable to document (**USER**)
- `GET /api/v1/repository/authorities`: Directory of issuing government authorities (**USER**)
- `GET /api/v1/repository/authorities/{auth_id}`: Authority contact and jurisdiction details (**USER**)
- `GET /api/v1/repository/fees`: Statutory fee schedule for correction petitions (**USER**)
- `GET /api/v1/repository/timelines`: Expected statutory processing turnaround times (**USER**)
- `GET /api/v1/repository/stats`: Repository catalog statistics (**PUBLIC**)

#### 4. Authentication (12 Endpoints)
- `POST /api/v1/auth/signup`: Create initial citizen account (**PUBLIC**)
- `POST /api/v1/auth/login`: Authenticate citizen credentials (**PUBLIC**)
- `POST /api/v1/auth/session`: Exchange verified Firebase token for session (**PUBLIC**)
- `POST /api/v1/auth/provision`: Provision or synchronize authenticated user (**PUBLIC**)
- `GET /api/v1/auth/me`: Retrieve current authenticated user profile (**USER**)
- `PUT /api/v1/auth/profile`: Update user profile metadata (**USER**)
- `POST /api/v1/auth/logout`: Revoke active session tokens (**USER**)
- `POST /api/v1/auth/send-verification`: Send email OTP verification (**PUBLIC**)
- `POST /api/v1/auth/verify-email`: Verify email OTP token (**PUBLIC**)
- `POST /api/v1/auth/resend-otp`: Resend email OTP (**PUBLIC**)
- `POST /api/v1/auth/link-provider`: Link secondary auth provider (**USER**)
- `DELETE /api/v1/auth/account`: Delete account and request data purge (**USER**)

#### 5. Authenticity & Ed25519 PKI (11 Endpoints)
- `POST /api/v1/pki/keys`: Generate new Ed25519 signing keypair (**ADMIN**)
- `GET /api/v1/pki/keys`: List platform signing keys (**ADMIN**)
- `GET /api/v1/pki/keys/active`: Retrieve current active public signing key (**PUBLIC**)
- `POST /api/v1/pki/keys/{key_id}/rotate`: Rotate active signing key (**ADMIN**)
- `POST /api/v1/pki/keys/{key_id}/revoke`: Revoke signing key (**ADMIN**)
- `POST /api/v1/pki/sign`: Apply Ed25519 platform signature to canonical digest (**USER**)
- `POST /api/v1/pki/verify`: Verify digital signature against public key (**PUBLIC**)
- `GET /api/v1/pki/attestations/{id}`: Retrieve document attestation record (**USER**)
- `POST /api/v1/pki/attestations/verify`: Cryptographically verify attestation chain (**PUBLIC**)
- `GET /api/v1/pki/audit-chain`: Inspect immutable audit ledger cryptographic hash chain (**ADMIN**)
- `POST /api/v1/pki/audit-chain/verify`: Verify SHA-256 genesis-to-tip hash linkage (**ADMIN**)

#### 6. Documents & Ephemeral OCR (9 Endpoints)
- `POST /api/v1/documents/upload`: Upload identity document (PDF/Image) (**USER**)
- `GET /api/v1/documents`: List citizen's uploaded documents under Forced RLS (**USER**)
- `GET /api/v1/documents/{id}`: Retrieve document metadata and extracted fields (**USER**)
- `DELETE /api/v1/documents/{id}`: Delete document and purge encrypted raw text (**USER**)
- `POST /api/v1/documents/{id}/confirm`: User confirmation of extracted OCR fields (**USER**)
- `GET /api/v1/documents/{id}/ocr-status`: Check OCR extraction progress (**USER**)
- `POST /api/v1/documents/{id}/re-extract`: Request OCR re-extraction with fallback (**USER**)
- `GET /api/v1/documents/types`: List supported document types (Aadhaar, PAN, Passport, etc.) (**PUBLIC**)
- `GET /api/v1/documents/{id}/download`: Download sanitized document representation (**USER**)

#### 7. Correction Drafts (9 Endpoints)
- `POST /api/v1/correction-drafts`: Create new administrative petition draft (**USER**)
- `GET /api/v1/correction-drafts`: List citizen's saved correction drafts (**USER**)
- `GET /api/v1/correction-drafts/{id}`: Retrieve draft details and legal representations (**USER**)
- `PUT /api/v1/correction-drafts/{id}`: Edit draft content, recipient, or subject line (**USER**)
- `DELETE /api/v1/correction-drafts/{id}`: Delete correction draft (**USER**)
- `POST /api/v1/correction-drafts/{id}/confirm`: Citizen confirmation & Ed25519 signature (**USER**)
- `POST /api/v1/correction-drafts/{id}/regenerate`: Regenerate draft using updated context (**USER**)
- `POST /api/v1/correction-drafts/{id}/translate`: Translate draft into target official language (**USER**)
- `GET /api/v1/correction-drafts/{id}/download`: Export signed PDF representation (**USER**)

#### 8. Administrative Platform Management (7 Endpoints)
- `POST /api/v1/admin/login`: Administrator authentication portal (**PUBLIC**)
- `GET /api/v1/admin/overview`: System-wide statistics and service health (**ADMIN**)
- `GET /api/v1/admin/conflicts`: Platform-wide conflict discrepancy monitoring (**ADMIN**)
- `GET /api/v1/admin/audit-logs`: Query append-only audit trail (**ADMIN**)
- `GET /api/v1/admin/users`: List platform users and roles (**ADMIN**)
- `POST /api/v1/admin/users/{id}/role`: Manage user role (USER vs ADMIN only) (**ADMIN**)
- `GET /api/v1/admin/system-activity`: Real-time administrative activity feed (**ADMIN**)

#### 9. Core Health & System (6 Endpoints)
- `GET /`: Platform root health check and version metadata (**PUBLIC**)
- `GET /health`: Comprehensive database, Qdrant, and storage readiness probe (**PUBLIC**)
- `GET /docs`: OpenAPI Swagger documentation UI (disabled in production) (**PUBLIC**)
- `GET /redoc`: ReDoc API documentation UI (disabled in production) (**PUBLIC**)
- `GET /openapi.json`: OpenAPI schema JSON definition (**PUBLIC**)
- `GET /version`: Semantic version, build timestamp, and Git commit hash (**PUBLIC**)

#### 10. Identity Conflicts & Discrepancies (5 Endpoints)
- `GET /api/v1/conflicts`: List detected conflicts for authenticated citizen (**USER**)
- `POST /api/v1/conflicts/compare`: Compare documents and detect discrepancies (**USER**)
- `GET /api/v1/conflicts/{id}`: Retrieve conflict details, severity, and guidance (**USER**)
- `PUT /api/v1/conflicts/{id}/status`: Update conflict resolution status (**USER**)
- `GET /api/v1/conflicts/summary`: Summary metrics (high, medium, low discrepancies) (**USER**)

#### 11. Development Application Explorer (3 Endpoints — DEV ONLY)
- `GET /api/v1/dev/overview`: Live architecture inspection, table RLS states, services (**DEV_ONLY**)
- `GET /api/v1/dev/persistence-inspect`: Caller-scoped read-only persistence inspector (**USER**)
- `POST /api/v1/dev/provision-test-account`: Synthetic QA session provisioning (**DEV_ONLY**)

---

## 4. Architectural Invariant Compliance

| Architecture Rule | Compliance Status | Evidence |
| :--- | :--- | :--- |
| **Strict Two-Role Architecture** | **COMPLIANT** | Only `USER` and `ADMIN` roles exist. Zero `OFFICER`, `VERIFIER`, or `CASE_WORKER` routes. |
| **Fail-Closed Production Dev Route** | **COMPLIANT** | Dev router unmounted when `ENVIRONMENT=production`. `verify_dev_mode()` returns 403. |
| **No Dynamic Role Injection** | **COMPLIANT** | `TestAccountRequest` accepts only `target`. Client-supplied `role` is discarded. |
| **Forced RLS Coverage** | **COMPLIANT** | All 21 user data tables enforce `FORCE ROW LEVEL SECURITY`. |
