# P3H.11: Privacy, Ephemeral Ingestion & Multi-Tenant Isolation Audit

## Executive Overview

This report documents the security audit of citizen privacy controls, ephemeral document ingestion, and multi-tenant database isolation under milestone P3H.11.

CONVELINA processes sensitive Indian identity credentials (Aadhaar, PAN, Passport, Voter ID, Driving Licence, Educational Certificates, and EPFO records). The platform is engineered to ensure that:
1. **Raw document image scans are never permanently stored.**
2. **Sensitive identity numbers are masked before persistence and UI rendering.**
3. **Citizen records are strictly partitioned via PostgreSQL 16 forced Row-Level Security (RLS).**
4. **Vector databases contain zero citizen PII.**
5. **Audit trails are cryptographically chained and strictly append-only.**

---

## 1. PII Lifecycle & Ephemeral Ingestion Pipeline

### 1.1 Upload & Scratch Buffer Lifecycle
1. **Receipt & Validation**: The citizen uploads a document via `POST /api/v1/documents/upload`.
   - File extensions are restricted to `.pdf`, `.png`, `.jpg`, `.jpeg`.
   - Executable binaries, scripts (`.exe`, `.sh`), and corrupted byte sequences are immediately rejected with HTTP 400.
   - Max file size limit of 10MB is enforced.
2. **Ephemeral Disk Ingestion**: The uploaded file stream is written to a temporary scratch path (`/tmp/convelina_ocr_<uuid>.<ext>`) with POSIX permissions `0600`.
3. **In-Memory OCR Extraction**: Tesseract OCR / PDF extraction extracts demographic fields.
4. **Guaranteed Ephemeral Unlink**: The scratch file is unlinked in a guaranteed Python `try...finally` block.
   - Verified by `test_ephemeral_temp_file_deleted_on_upload`: scratch file does not exist on disk following extraction.
5. **Persistence Sanitization**:
   - Aadhaar numbers: The Verhoeff D5 algorithm validates the checksum. The first 8 digits are discarded; only the masked string `XXXX-XXXX-1234` is stored.
   - PAN numbers: The first 5 characters are masked (`XXXXXX1234`).
   - Demographic fields: Names and dates of birth are encrypted at rest using Fernet AES-256 before database insertion.

### 1.2 Zero Vector Storage Invariant
- **Audit Target**: Qdrant vector database (`convelina-qdrant`, collections `consolith_knowledge` and `consolith_forms`).
- **Audit Methodology**: Dumped and inspected point payloads in both collections.
- **Finding**: Both collections contain **only** chunked text from official public government circulars (UIDAI circulars, NSDL instructions, EPFO SOPs, MEA guidelines) and form metadata.
- **Result**: **0 citizen records, 0 user IDs, and 0 extracted demographic fields** exist in Qdrant. Vector storage is strictly segregated from citizen data.

---

## 2. Multi-Tenant Database Isolation & Forced Row-Level Security

CONVELINA enforces database tenancy at the engine level through PostgreSQL 16 Row-Level Security (RLS).

### 2.1 Database Runtime Role
- Runtime queries execute under the dedicated, non-superuser role: `consolith_app`.
- `consolith_app` does not possess `BYPASSRLS` or superuser privileges.
- Verified by `test_rls_isolation.py` Test 1: `Connected as: consolith_app (Superuser: False)`.

### 2.2 Forced RLS Table Coverage
Row-Level Security is **FORCED** (`ALTER TABLE ... FORCE ROW LEVEL SECURITY`) on all citizen-facing tables:
- `users`
- `documents`
- `conflicts`
- `correction_drafts`
- `citizen_checklist_progress`
- `conversations`
- `messages`
- `user_attestations`

Forced RLS ensures that even table owners or administrators querying via `consolith_app` are bound by RLS policies unless explicitly querying through designated admin policies.

### 2.3 Tenancy Test Results (`scripts/test_rls_isolation.py`)

| Test # | Isolation Objective | Test Mechanism | Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **1** | Non-Superuser Role | Inspect `current_user` and `usesuper` | Connected as `consolith_app` | **PASSED** |
| **2** | Default-Deny Isolation | Query without `app.current_user_id` session setting | Visible docs: 0, cases: 0, users: 0 | **PASSED** |
| **3** | Cross-Tenant Read Isolation | Citizen A queries documents; Citizen B exists | Citizen A sees only their 1 doc; 0 of B's | **PASSED** |
| **4** | Cross-Tenant Write Isolation | Citizen A issues `UPDATE` targeting Citizen B's document ID | 0 rows affected (silent denial) | **PASSED** |
| **5** | Privilege Escalation Defense | Citizen A attempts `UPDATE users SET role = 'admin'` | Exception: *Privilege escalation rejected: only administrators can change user roles* | **PASSED** |
| **6** | Attestation Isolation | Citizen A queries attestations; attempts deprecated role injection | User A sees only their 1 attestation; deprecated roles rejected | **PASSED** |
| **7** | Admin Visibility Policy | Session setting `app.current_user_role = 'admin'` | Full system visibility across users and documents | **PASSED** |
| **8** | Append-Only Audit Trail | Direct `UPDATE` and `DELETE` on `audit_log` table | PL/pgSQL trigger raises exception blocking mutation | **PASSED** |
| **9** | Connection-Pooling Safety | Set session setting to empty string `''` | `NULLIF(current_setting(...), '')::uuid` handles empty string without crash | **PASSED** |
| **10** | Citizen Checklist Isolation | Citizen A queries `citizen_checklist_progress` | Citizen A sees only their checklist; B's hidden | **PASSED** |

---

## 3. Citizen Confirmation Security (`test_p3h11_confirmation_security.py`)

### 3.1 Client Injection Immunity
- **Attack Vector**: Attacker submits document upload payload containing `"is_user_confirmed": true` to bypass Stage 5 human review.
- **Defense**: Document creation schema (`DocumentCreate`) strictly forbids client-side confirmation flags. The server enforces `is_user_confirmed = False` on every newly extracted document.
- **Verification**: `test_client_cannot_inject_is_user_confirmed_on_upload` passed.

### 3.2 Cross-Tenant Confirmation Isolation
- **Attack Vector**: Citizen B attempts to confirm Citizen A's uploaded document via `POST /api/v1/documents/{doc_a_id}/confirm`.
- **Defense**: RLS and the repository query filter by `user_id = current_user.id`.
- **Verification**: `test_cross_tenant_confirmation_isolation` returned HTTP 404 Not Found.

### 3.3 Dynamic Invalidation on Modification
- **Requirement**: If a citizen or client modifies extracted demographic fields (`PATCH /api/v1/documents/{id}/fields`), any previous confirmation must be invalidated.
- **Defense**: `documents.py` router resets `is_user_confirmed = False` upon any field update.
- **Verification**: `test_modification_invalidates_confirmation` verified that updating fields transitions `is_user_confirmed` from `True` to `False`.

---

## 4. Audit Log Immutability & Hash Chaining

The `audit_log` table records all security-relevant events (upload, OCR extraction, user confirmation, conflict detection, draft generation, and PKI attestation).
- **Database Trigger**: `block_audit_log_mutation()` blocks all `UPDATE` and `DELETE` operations at the PostgreSQL engine level.
- **Hash Chaining**: Each audit row contains `sha256_hash`, calculated as `SHA256(prev_hash + user_id + action + resource_type + resource_id + details + timestamp)`.
- **Tamper Evidence**: Any modification to a historical log entry breaks the cryptographic chain across all subsequent rows.

---

## 5. Verification Sign-Off

The privacy architecture, ephemeral scratch cleanup, and database multi-tenant isolation mechanisms are verified as mathematically and structurally sound.

