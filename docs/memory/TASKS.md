# Consolith Tasks & Build Tracker

- [x] **Module 1: Foundation**
  - [x] Docker Compose multi-service architecture
  - [x] PostgreSQL 16 container with healthcheck
  - [x] Qdrant container with healthcheck
  - [x] FastAPI backend with `/health` validation
  - [x] Next.js frontend with live system status
  - [x] Automated test harness `scripts/verify_module1.py`

- [x] **Module 2: Database Schema & Row-Level Security (RLS)**
  - [x] Migration runner and SQL schemas (`users`, `documents`, `conflicts`, `cases`, `audit_log`, `digital_signatures`)
  - [x] Dedicated non-superuser role `consolith_app`
  - [x] RLS policies for Citizen, Officer, and Admin
  - [x] FORCE ROW LEVEL SECURITY on all user-data tables
  - [x] Privilege escalation prevention trigger on `users`
  - [x] Append-only trigger on `audit_log`
  - [x] Safe session variable handling (`NULLIF(..., '')::uuid`)
  - [x] Independent test harness `scripts/test_rls_isolation.py` (9/9 tests pass)
  - [x] Backend database connection configuration update to `consolith_app`

- [x] **Module 3: Authentication & Role Scoping**
  - [x] Firebase Admin SDK integration with graceful unconfigured fallback
  - [x] Server-side ID token verification (signature, exp, aud, iss validation)
  - [x] Secure citizen auto-provisioning function (`provision_citizen_user`) with concurrency upsert
  - [x] Non-superuser role context mapping via transaction-local `SET LOCAL`
  - [x] Connection-pooling safe context cleanup
  - [x] RBAC FastAPI dependencies (`require_citizen`, `require_officer`, `require_admin`)
  - [x] Protected API endpoints (`/auth/me`, `/auth/provision`, `/auth/health`, role-scoped test endpoints)
  - [x] Frontend Firebase client integration (`AuthContext`, interactive test dashboard)
  - [x] Unit test suite (`backend/tests/test_auth.py`, 10/10 passing)
  - [x] HTTP integration test suite (`scripts/test_auth_api.py`, 8/8 passing)
  - [x] RLS regression verification (`scripts/test_rls_isolation.py`, 9/9 passing)

- [x] **Module 4: Document Upload & OCR Pipeline**
  - [x] Container stack update with Tesseract OCR 5.5.0 (Eng+Hin) and Poppler
  - [x] Content inspection: magic bytes (PDF, JPEG, PNG), file size limit, empty/corrupt file rejection
  - [x] Path traversal prevention in filename sanitization
  - [x] Temporary storage manager with SHA-256 deduplication and unpredictable UUID filenames
  - [x] Pluggable OCR abstraction (`BaseOCREngine`, `TesseractOCREngine`) with image preprocessing
  - [x] Document parsers for Tier 1 documents: Aadhaar, PAN, Passport, Class 10, Class 12, EPF records
  - [x] Aadhaar Act privacy compliance: strict masking (`XXXX-XXXX-1234`) and Fernet at-rest payload encryption
  - [x] Secure ephemeral retention policy: temporary files safely unlinked after OCR extraction
  - [x] FastAPI document endpoints: `/upload`, `/documents` (list), `/documents/{id}` (get), `/documents/{id}` (delete)
  - [x] PostgreSQL RLS enforced across all document operations using non-superuser role
  - [x] Next.js frontend upload and library UI with document type selection, status indicators, and delete actions
  - [x] Unit test suite (`backend/tests/test_upload_ocr.py`, 14/14 passing; total pytest: 24/24 passing)
  - [x] HTTP integration test suite (`scripts/test_upload_ocr_api.py`, 8/8 passing)

- [ ] **Module 5: Conflict Detection Engine**
- [ ] **Module 6: RAG Knowledge Base & AI Assistant**
- [ ] **Module 7: Correction Document Generator**
- [ ] **Module 8: Officer Verification Workflow**
- [ ] **Module 9: Document Authenticity & Ed25519 PKI/CA**
- [ ] **Module 10: Security Hardening Pass**
