# Security Notes & Hardening Guidelines

## 1. Row-Level Security (RLS)
- Every table containing user data must have:
  - `ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;`
  - `ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;`
- Connection to database must never use `postgres` (superuser); must use `consolith_app`.

## 2. Privilege Escalation Defense
- Citizens cannot change their own `role` column in `users`.
- A PostgreSQL `BEFORE UPDATE` trigger on `users` raises an exception if `NEW.role != OLD.role` and `app.current_user_role != 'admin'`.

## 3. Tamper-Evident Audit Logging
- `audit_log` is protected by a trigger blocking `UPDATE` and `DELETE`.
- Each entry cryptographically hashes the payload plus `prev_hash` to maintain an immutable hash chain.

## 4. Sensitive Data Protection
- Aadhaar numbers must be masked (showing only last 4 digits) everywhere in application responses and logs (`XXXX-XXXX-1234`).
- Full numbers and sensitive payloads must be encrypted at rest using Fernet before database insertion.

## 5. Authentication & Identity Token Security (Module 3)
- **Token Verification**: ID tokens must be cryptographically validated via official Firebase Admin SDK. Never trust client-supplied user IDs, roles, or claims in request bodies.
- **Client Role Sanitization**: Clients can NEVER specify their own role. Auto-provisioning strictly assigns role `'citizen'`. Role updates are strictly restricted to admin callers via DB trigger `trg_prevent_role_escalation`.
- **Transaction-Local Identity**: All authenticated DB sessions set `app.current_user_id` and `app.current_user_role` using `SET LOCAL`. When connections return to the pool, session context is automatically cleared, preventing identity leakage across requests.
- **Testing Isolation**: Test/simulated tokens are strictly disabled unless explicit `TEST_MODE_ALLOW_SIMULATED_TOKENS=true` is enabled in non-production environments.

## 6. Document Upload & OCR Privacy Hardening (Module 4)
- **File Validation & Magic Bytes**: Never trust client-supplied MIME types or filenames. Inspect magic bytes (`%PDF-`, `\xFF\xD8\xFF`, `\x89PNG\r\n\x1a\n`) and perform image/PDF integrity decoding before processing.
- **Path Traversal Defense**: All filenames are sanitized, directory separators stripped, and stored using server-generated UUID filenames in a dedicated temporary storage directory outside web roots.
- **Aadhaar Act Compliance**: Plaintext 12-digit Aadhaar numbers are NEVER stored or returned in API responses. The parser strictly masks all but the last 4 digits (`XXXX-XXXX-1234`).
- **At-Rest Payload Encryption**: Any retained sensitive payload or raw text is encrypted using Fernet symmetric cryptography (`encrypted_data`).
- **Ephemeral Storage Retention**: Raw temporary uploaded files are securely unlinked from disk upon OCR extraction completion (`STORAGE_RETENTION_POLICY="delete_after_ocr"`).
- **PostgreSQL RLS Storage Scoping**: All document operations execute under transaction-local `set_rls_context(db, user.id, user.role)` via `consolith_app`. Citizens can only access, view, or delete their own documents. Cross-user IDOR access attempts return HTTP 404.


