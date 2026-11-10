# P3H.9 — Feature, API & Storage Mapping

## Executive Overview

This document defines the architectural mapping between CONVELINA's **8 core system features**, their underlying **FastAPI endpoints**, their **database models and tables**, their **storage mechanisms**, and their **PostgreSQL Row-Level Security (RLS) enforcement rules**.

---

## 1. Architectural Mapping Matrix

| Feature | Primary API Endpoints | PostgreSQL Tables & Models | Storage Type | Security & RLS Policy |
|---------|-----------------------|----------------------------|--------------|-----------------------|
| **1. Citizen Profile & Consent** | `GET /api/v1/auth/me`<br>`POST /api/v1/auth/provision`<br>`PUT /api/v1/auth/profile`<br>`POST /api/v1/auth/consent/revoke` | `users` (`User`)<br>`cases` (`Case`) | Relational PostgreSQL | `users_rls_policy`: Citizens can only query/update their own profile (`id = current_setting('app.current_user_id')::uuid`). Role escalation strictly prevented by database trigger. |
| **2. Ephemeral Ingestion & PII Masking** | `POST /api/v1/documents/upload`<br>`GET /api/v1/documents`<br>`DELETE /api/v1/documents/{id}` | `documents` (`Document`)<br>`audit_log` (`AuditLog`) | Local temp dir (`/tmp/consolin_uploads`) + PostgreSQL JSONB | `documents_rls_policy`: Forced RLS on `documents`. Sensitive fields (Aadhaar numbers, PAN) are masked before persistence. Raw image files purged after ephemeral OCR extraction. |
| **3. OCR Extraction & Field Review** | `PATCH /api/v1/documents/{id}/fields`<br>`POST /api/v1/documents/{id}/confirm`<br>`GET /api/v1/documents/{id}/profile` | `documents` (`Document`) | PostgreSQL JSONB (`extracted_fields`, `confirmed_fields`) | `is_citizen_confirmed` boolean flag and `citizen_confirmed_at` timestamp locked upon Stage 5 review. Edits allowed only by document owner before confirmation lock. |
| **4. Deterministic Conflict Detection** | `POST /api/v1/conflicts/compare`<br>`POST /api/v1/conflicts/detect`<br>`GET /api/v1/conflicts` | `conflicts` (`Conflict`)<br>`audit_log` (`AuditLog`) | Relational PostgreSQL | `conflicts_rls_policy`: Citizens see only conflicts derived from documents they own. Deterministic pairwise matching prevents initial expansion false-positives and gender mismatch errors. |
| **5. AI Assistant & Procedural RAG** | `POST /api/v1/assistant/conversations`<br>`POST /api/v1/assistant/conversations/{id}/messages`<br>`GET /api/v1/assistant/resolution-context/{id}` | `conversations` (`Conversation`)<br>`messages` (`Message`)<br>`message_attachments` | PostgreSQL + Qdrant `statutory_documents` | `conversations_rls_policy`: Multi-tenant isolation enforced on all chat threads. RAG pipeline uses BM25-first keyword retrieval backed by Qdrant vector index. Strict relevance floor (>= 0.55) enforces zero hallucination. |
| **6. Correction Draft Generator** | `POST /api/v1/correction-drafts`<br>`PUT /api/v1/correction-drafts/{id}`<br>`POST /api/v1/correction-drafts/{id}/confirm`<br>`GET /api/v1/correction-drafts/{id}/download` | `correction_drafts` (`CorrectionDraft`)<br>`correction_draft_versions` | Relational PostgreSQL + ephemeral PDF export | `correction_drafts_rls_policy`: Citizen can only read/edit their own representations. Every citizen edit archives prior version and invalidates prior confirmation. Binds confirmation to SHA-256 hash. |
| **7. Forms Repository & Checklists** | `GET /api/v1/repository/resources`<br>`GET /api/v1/repository/checklists/{id}/progress`<br>`PUT /api/v1/repository/checklists/{id}/progress` | `official_forms` (`OfficialForm`)<br>`citizen_checklist_progress` | Static disk catalog + PostgreSQL | `citizen_checklist_progress_rls`: Checklists are publicly browseable, but individual citizen progress is strictly isolated and persisted under forced RLS. Survives browser reloads. |
| **8. Admin Telemetry & Security Gate** | `GET /api/v1/admin/overview-stats`<br>`GET /api/v1/admin/system-activity`<br>`POST /api/v1/knowledge/admin/forms/{id}/replace`<br>`GET /api/v1/pki/keys` | `audit_log` (`AuditLog`)<br>`official_forms`<br>`pki_signing_keys` | Relational PostgreSQL + Ed25519 PKI | `admin_role_enforcement`: Only callers with verified `role == 'admin'` can access administrative endpoints. Database triggers strictly block `UPDATE` and `DELETE` on `audit_log`. Hash chaining verifies integrity. |

---

## 2. In-Depth Feature Architecture

### Feature 1: Citizen Profile & Ephemeral Verification
- **Purpose**: Establishes verified citizen context for identity dispute resolution without permanently storing high-risk identity numbers.
- **Data Read**: `users` record matching `app.current_user_id`.
- **Data Modified**: `full_name`, `phone_number`, `date_of_birth`, `address`, `consent_records`.
- **Code**:
  - Router: `backend/app/routers/auth.py`
  - Service: `backend/app/services/user_service.py`
  - Frontend: `frontend/src/app/setup-profile/page.tsx`, `frontend/src/app/app/profile/page.tsx`

### Feature 2: Ephemeral Ingestion & PII Masking
- **Purpose**: Accepts citizen-uploaded PDFs and PNGs, runs OCR in-memory, extracts demographic tokens, masks Aadhaar (all but last 4 digits) and PAN (middle alphanumeric), and stores masked metadata.
- **Data Read**: Multipart form data with file binary.
- **Data Modified**: `documents` table record created with `file_hash`, `masked_number`, and `ocr_status`.
- **Code**:
  - Router: `backend/app/routers/documents.py`
  - OCR Pipeline: `backend/app/ocr/pipeline.py`
  - Frontend: `frontend/src/app/app/inconsistencies/page.tsx`

### Feature 3: OCR Extraction & Stage 5 Field Review
- **Purpose**: Displays extracted names, dates of birth, parent names, and gender to the citizen for explicit confirmation before conflict detection or drafting can occur.
- **Data Read**: `documents.extracted_fields`.
- **Data Modified**: `documents.confirmed_fields`, `documents.is_citizen_confirmed = true`.
- **Code**:
  - Router: `backend/app/routers/documents.py`
  - Frontend: `frontend/src/components/documents/DocumentConfirmationModal.tsx`

### Feature 4: Deterministic Conflict Detection Engine
- **Purpose**: Pairwise, rule-based cross-document discrepancy detection across verified credentials.
- **Specialized Rules**:
  - Initial ambiguity handling (e.g. `A. Sharma` vs `Aarav Sharma` marked as initial expansion, not total name conflict).
  - Date of birth formats (`DD/MM/YYYY` vs `YYYY-MM-DD`).
  - Gender mismatch detection with high severity.
- **Data Read**: Two confirmed `documents` belonging to the citizen.
- **Data Modified**: `conflicts` table records created with severity, type, and evidence.
- **Code**:
  - Router: `backend/app/routers/conflicts.py`
  - Engine: `backend/app/conflicts/engine.py`
  - Service: `backend/app/services/identity_matching.py`

### Feature 5: Conversational AI Workspace & Procedural RAG
- **Purpose**: Provides interactive legal and procedural guidance tailored to the citizen's specific detected discrepancy.
- **Grounding Protocol**:
  - BM25 lexical search over statutory regulations.
  - Hybrid search with Qdrant dense vector embeddings.
  - Relevance score floor (0.55) to prevent hallucinated government procedures.
  - Automatic injection of official forms (e.g. Form 49A, Annexure E).
- **Data Read**: `conversations`, `messages`, `conflicts`, Qdrant collection `statutory_documents`.
- **Data Modified**: `conversations`, `messages`, `message_attachments`.
- **Code**:
  - Router: `backend/app/routers/assistant.py`
  - RAG Core: `backend/app/rag/engine.py`, `backend/app/rag/hybrid_retriever.py`
  - Frontend: `frontend/src/app/app/assistant/page.tsx`

### Feature 6: Administrative Correction Draft Generator
- **Purpose**: Automatically populates formal representations and petitions to government authorities (e.g., UIDAI, Income Tax Department, Regional Passport Office).
- **Security Invariant**: Any citizen edit generates a new version and invalidates prior confirmation.
- **Data Read**: `conflicts`, `documents.confirmed_fields`.
- **Data Modified**: `correction_drafts`, `correction_draft_versions`.
- **Code**:
  - Router: `backend/app/routers/correction_drafts.py`
  - Service: `backend/app/services/correction_draft_service.py`
  - Frontend: `frontend/src/components/drafting/AdministrativeDraftingModal.tsx`

### Feature 7: Statutory Forms Repository & Checklist Preparation
- **Purpose**: Centralized statutory repository of verified official forms and interactive preparation checklists.
- **Persistence**: Citizen preparation checklist progress is saved to PostgreSQL (`citizen_checklist_progress`), ensuring items remain completed across page refreshes.
- **Data Read**: `official_forms`, `citizen_checklist_progress`.
- **Data Modified**: `citizen_checklist_progress`.
- **Code**:
  - Router: `backend/app/routers/repository.py`, `backend/app/routers/checklists.py`
  - Frontend: `frontend/src/app/app/forms/page.tsx`, `frontend/src/app/app/forms/[formId]/page.tsx`

### Feature 8: Administrator Audit Ledger & Document Security Gate
- **Purpose**: Platform health monitoring, user inspection, immutable audit log verification, form replacement with version archiving, and Ed25519 signing key inspection.
- **Security Invariant**: Strictly restricted to `role == 'admin'`. Non-admin users are rejected at the API level (403 Forbidden) and UI level (Access Denied).
- **Data Read**: `audit_log`, `users`, `official_forms`, `pki_signing_keys`.
- **Data Modified**: `official_forms` (replace binary, update status), `users` (administrative role management).
- **Code**:
  - Router: `backend/app/routers/admin.py`
  - Service: `backend/app/services/audit_service.py`
  - Frontend: `frontend/src/app/admin/page.tsx`
