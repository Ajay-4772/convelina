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
