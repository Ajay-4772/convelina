# CONVELINA — P3H.9.1 PostgreSQL Schema & Persistence Inspector Audit

**Document Version**: 1.0.0  
**Phase**: P3H.9.1 Acceptance & Remediation  
**Status**: AUDITED & ACCEPTED  
**Auditor**: Principal Database Architect & Security Auditor  
**Inspection Target**: PostgreSQL 16 Database (`consolith`), `backend/app/routers/dev.py`, `scripts/test_rls_isolation.py`  

---

## 1. Executive Summary

This audit evaluates the database schema integrity, Row-Level Security (RLS) enforcement, and privacy controls of the CONVELINA PostgreSQL database and the Development Application Explorer's Persistence Inspector (`/api/v1/dev/persistence-inspect`).

### Key Audit Findings
1. **100% Forced RLS on Application Tables**: The database contains 22 tables in the `public` schema. Exactly 21 tables hold application/user data, and **all 21 enforce `FORCE ROW LEVEL SECURITY`** (`relrowsecurity = true` AND `relforcerowsecurity = true`). The 22nd table is `schema_migrations`, an infrastructure metadata table holding migration version strings without user data.
2. **Dedicated Runtime Non-Superuser Role**: The application connects using the dedicated non-superuser role `consolith_app`, preventing superuser RLS bypass.
3. **Strict Read-Only Inspector**: `/api/v1/dev/persistence-inspect` accepts exclusively HTTP `GET` requests. Write operations (`POST`, `PUT`, `DELETE`) are rejected with HTTP 405 Method Not Allowed.
4. **Session-Bound Identity**: The inspector derives user identity exclusively from the verified token claims (`current_user: User = Depends(get_current_user)`), making tenant spoofing impossible.
5. **Aadhaar Act & DPDP Act Privacy Compliance**: Sensitive identity numbers and personal details are strictly masked before serialization (`XXXX-XXXX-last4` for Aadhaar, `XXXXXlast4` for PAN, `A***a` for personal names). Zero raw Aadhaar numbers or plaintext OCR payloads are returned.

---

## 2. PostgreSQL 16 Schema & RLS Audit Matrix

Every table in the `public` schema was queried directly via `pg_class` and `pg_policies`:

| # | Table Name | Primary Key | Owner Column | RLS Enabled | FORCE RLS | Policy Count | PII Classification | Retention Policy |
|---|---|---|---|:---:|:---:|:---:|---|---|
| 1 | `assistant_conversations` | `id` (UUID) | `user_id` | **TRUE** | **TRUE** | 2 | Low (Conversation Title) | User Retained |
| 2 | `assistant_messages` | `id` (UUID) | `user_id` | **TRUE** | **TRUE** | 2 | Medium (Consultation text) | User Retained |
| 3 | `attestation_verifications` | `id` (UUID) | None (System) | **TRUE** | **TRUE** | 3 | None (Verification status) | Permanent Audit |
| 4 | `audit_log` | `id` (UUID) | `user_id` | **TRUE** | **TRUE** | 3 | Medium (Action, Entity, IP) | Permanent Append-Only |
| 5 | `case_evidence` | `id` (UUID) | None (System) | **TRUE** | **TRUE** | 2 | Low (Scaffolding metadata) | System Scaffolding |
| 6 | `case_review_requests` | `id` (UUID) | None (System) | **TRUE** | **TRUE** | 2 | Low (Review flags) | System Scaffolding |
| 7 | `cases` | `id` (UUID) | None (System) | **TRUE** | **TRUE** | 2 | Low (System case record) | System Scaffolding |
| 8 | `citizen_checklist_items` | `id` (UUID) | `user_id` | **TRUE** | **TRUE** | 4 | Low (Item ID, completed flag)| User Retained |
| 9 | `conflicts` | `id` (UUID) | `user_id` | **TRUE** | **TRUE** | 2 | High (Masked name/DOB values)| Active Resolution |
| 10 | `correction_draft_versions` | `id` (UUID) | `user_id` | **TRUE** | **TRUE** | 2 | High (Encrypted petition text)| Versioned History |
| 11 | `correction_drafts` | `id` (UUID) | `user_id` | **TRUE** | **TRUE** | 2 | High (Encrypted petition text)| User Retained |
| 12 | `digital_signatures` | `id` (UUID) | None (System) | **TRUE** | **TRUE** | 2 | None (Ed25519 signature bytes)| Permanent Attestation |
| 13 | `document_attestations` | `id` (UUID) | None (System) | **TRUE** | **TRUE** | 2 | None (Canonical SHA-256 hash) | Permanent Attestation |
| 14 | `documents` | `id` (UUID) | `user_id` | **TRUE** | **TRUE** | 2 | Critical (Fernet encrypted) | Ephemeral / User |
| 15 | `email_otps` | `id` (UUID) | None (System) | **TRUE** | **TRUE** | 1 | Medium (Hashed OTP token) | 300s TTL |
| 16 | `knowledge_sources` | `id` (UUID) | None (Public) | **TRUE** | **TRUE** | 2 | None (Public Statutory Texts)| Permanent Reference |
| 17 | `message_attachments` | `id` (UUID) | `user_id` | **TRUE** | **TRUE** | 2 | High (Encrypted attachment) | 24 Hours TTL |
| 18 | `official_form_versions` | `id` (UUID) | None (Public) | **TRUE** | **TRUE** | 2 | None (Form version metadata) | Permanent Reference |
| 19 | `official_forms` | `id` (UUID) | None (Public) | **TRUE** | **TRUE** | 2 | None (Government Form Specs) | Permanent Reference |
| 20 | `signing_keys` | `id` (UUID) | None (System) | **TRUE** | **TRUE** | 2 | Critical (Encrypted Private Key)| KMS Managed |
| 21 | `users` | `id` (UUID) | `id` | **TRUE** | **TRUE** | 2 | High (Email, Full Name) | Permanent Account |
| 22 | `schema_migrations` | `version` (VARCHAR) | None (Metadata) | FALSE | FALSE | 0 | None (Migration versions) | Migration Ledger |

---

## 3. Persistence Inspector Security Architecture

```
[Authenticated Client Request]
       │
       ▼
[GET /api/v1/dev/persistence-inspect]
       │
       ├── 1. verify_dev_mode(): Must be development mode (403 if production)
       │
       ├── 2. get_current_user(): Resolve caller identity via verified token claims
       │
       ├── 3. set_rls_context(db, user_id, role):
       │      SET LOCAL app.current_user_id = '<user_uuid>';
       │      SET LOCAL app.current_user_role = 'user';
       │
       ├── 4. Query Scoped Entities (Filtered strictly by user_id):
       │      - Documents (Fernet decrypted only for metadata; numbers masked)
       │      - Conflicts (Values masked)
       │      - Conversations & Message Counts
       │      - Procedural Checklists
       │      - Correction Drafts (SHA-256 digest short-hash)
       │      - User Audit Events (Last 15 records)
       │
       ▼
[JSON Response with Masked Identifiers & Tenancy Verification]
```

### 3.1 Field-Level Masking Algorithms
In `backend/app/routers/dev.py`:
- **Document Numbers** (`_mask_doc_number`):
  - Aadhaar: `123456789012` -> `XXXX-XXXX-9012`
  - PAN: `ABCDE1234F` -> `XXXXX234F`
  - Other IDs: `12345678` -> `****-****-5678`
- **Personal Text** (`_mask_text`):
  - `Aarav Sharma` -> `A**********a` (length preserved with asterisks, revealing only first and last characters)
  - Short strings ($\le 2$ chars) -> `**`
- **Cryptographic Hashes**:
  - SHA-256 hashes truncated to first 10-12 hex characters followed by ellipsis (`a1b2c3d4e5...`).

---

## 4. Multi-Tenant Isolation Verification

Multi-tenant isolation within the persistence inspector was empirically verified through automated test suites:
1. **Disjoint Inventories**: In `test_p3h9_1_explorer_security.py` (`test_tenant_isolation_in_persistence_inspector`), Citizen A (`citizen_a@example.com`) and Citizen B (`citizen_b@example.com`) simultaneously queried the persistence inspector.
2. **Zero Cross-Leakage**:
   - `docs_a_ids.isdisjoint(docs_b_ids) == True`
   - Citizen A's documents, conflicts, conversations, and drafts never appeared in Citizen B's payload.
3. **Database RLS Enforcement**: If Citizen A attempts to query Citizen B's rows directly in SQL, PostgreSQL's forced RLS policies return 0 rows.

**Audit Conclusion**: The PostgreSQL database enforces 100% forced RLS across all application tables, and the Persistence Inspector is secure, read-only, and fully compliant with privacy regulations.
