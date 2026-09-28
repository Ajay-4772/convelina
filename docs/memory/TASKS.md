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

- [ ] **Module 3: Authentication & Role Scoping**
- [ ] **Module 4: Document Upload & OCR Pipeline**
- [ ] **Module 5: Conflict Detection Engine**
- [ ] **Module 6: RAG Knowledge Base & AI Assistant**
- [ ] **Module 7: Correction Document Generator**
- [ ] **Module 8: Officer Verification Workflow**
- [ ] **Module 9: Document Authenticity & Ed25519 PKI/CA**
- [ ] **Module 10: Security Hardening Pass**
