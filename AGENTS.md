# Consolith Agent Operating Rules

This file defines the mandatory operating guidelines for all AI agents working on Consolith.

## Core Rules

1. **Inspect Before Coding**: Always read `PROJECT.md`, `docs/memory/CURRENT_STATE.md`, and relevant module files before planning or writing code.
2. **Follow Approved Architecture & Locked Build Order**:
   - Module 1: Foundation (Completed & Verified)
   - Module 2: Database Schema & Row-Level Security (RLS) (In Progress)
   - Module 3: Authentication & Role Scoping
   - Module 4: Document Upload & OCR Pipeline
   - Module 5: Conflict Detection Engine
   - Module 6: RAG Knowledge Base & AI Assistant
   - Module 7: Correction Document Generator
   - Module 8: Officer Verification Workflow
   - Module 9: Document Authenticity & Ed25519 PKI/CA
   - Module 10: Security Hardening & Penetration Testing
3. **Fail-Safe, Never Silently Wrong**:
   - Ambiguous names, low OCR confidence, or unverified native scripts must be flagged as "unresolvable — needs manual review".
   - Never report false "no conflict" matches.
4. **Row-Level Security Enforcement**:
   - RLS must be enabled and **forced** on every table holding user data.
   - Runtime connections must use the dedicated non-superuser role (`consolith_app`).
   - All session settings must use `NULLIF(current_setting(...), '')::uuid` to prevent connection-pooling UUID cast failures.
5. **Aadhaar Act Compliance**:
   - No long-term storage of Aadhaar numbers or raw identity images.
   - Mask all but last 4 digits in UI and logs.
   - Sensitive fields encrypted at rest using Fernet.
6. **Append-Only Tamper-Evident Audit Log**:
   - Database triggers must block any `UPDATE` or `DELETE` on `audit_log`.
   - Each audit entry's hash must cryptographically link to the previous entry's hash.
7. **RAG Grounding & Zero Hallucination**:
   - Enforce relevance score floor (>= 0.55). If below floor, decline to answer.
   - Validate every generated citation against retrieved context.
   - Never invent government procedures, URLs, or requirements.
8. **Credential & Secret Protection**:
   - Never commit `.env`, private keys, or Firebase service account JSON files to version control.
   - Verify `.gitignore` and scan staged files before every commit.
9. **Test Rigor**:
   - Tests must have real failure modes. Never write tests that pass regardless of logic.
   - Always run tests against live containers before declaring a module complete.
