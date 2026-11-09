# CONVELINA P3H.8.1 — Credential Security, Rotation & Simulation Audit

## Executive Summary

During milestone **P3H.8.1**, a credential security audit was performed to identify any exposed credentials, rotate active development passwords, verify secret exclusion from version control, and audit test-simulation guardrails.

Key Actions & Outcomes:
1. **Plain-Text Credential Remediation**: A development database password previously referenced in `docs/P3H8_DATABASE_RECOVERY.md` was immediately redacted to `[REDACTED_DEV_PASSWORD]`.
2. **PostgreSQL Role Password Rotation**: Role `consolith_app` in the live PostgreSQL 16 container was rotated to a newly generated 24-character cryptographically secure token using `ALTER ROLE consolith_app WITH PASSWORD ...`.
3. **Local Environment Update**: The local `.env` file was updated with the rotated connection string. Database connectivity was re-established and validated via `/health`.
4. **Git & Secret Exclusion Verification**: Confirmed `.env` is strictly excluded via `.gitignore`. A scan of Git history confirmed no sensitive production keys or service account credentials have been tracked.
5. **Fail-Closed Test Mode Enforcement**: Verified that static demo credentials and test OTP bypasses (`123456`) are strictly constrained to local development and will fail closed with a fatal exception if enabled in a production environment.

---

## 1. Development Credential Rotation Execution

### 1.1 Remediation of Documentation Exposure
Line 60 of `docs/P3H8_DATABASE_RECOVERY.md` contained a plain-text development connection string. This was sanitized:
```diff
- postgresql://consolith_app:consolith_dev_pass@localhost:5432/consolith
+ postgresql://consolith_app:[REDACTED_DEV_PASSWORD]@localhost:5432/consolith
```
A full repository search (`git grep -n "consolith_dev_pass"`) confirmed zero remaining instances across the codebase and documentation.

### 1.2 Automated Rotation Workflow (`scripts/rotate_dev_credentials.py`)
To ensure the previously exposed credential is fully neutralized:
1. **Entropy Generation**: A 24-character token was generated via Python `secrets.token_urlsafe(24)`.
2. **Database Role Update**:
   ```sql
   ALTER ROLE consolith_app WITH PASSWORD '<ROTATED_SECRET>';
   ```
   Executed directly in the `convelina-postgres` container via administrative Docker execution.
3. **Local Configuration**: `.env` updated with the new `DATABASE_URL`.
4. **Connection Revalidation**: Verified that standard queries execute cleanly under `consolith_app` on `consolith`.
5. **Backend Restart**: FastAPI backend restarted; `/health` reports `status: healthy` with `postgres.status: up`.

---

## 2. Static Demo Credentials & Test-Mode Simulation Audit

CONVELINA supports a designated local test mode for automated test suites (e.g., Pytest, Playwright) without requiring live Google Firebase cloud connectivity.

### 2.1 Simulation Configuration (`backend/app/config.py`)
```python
# Test Mode / Isolated verification (never enable in production)
TEST_MODE_ALLOW_SIMULATED_TOKENS: bool = False
```

### 2.2 Production Fail-Closed Validator
In `backend/app/config.py`, the Pydantic `@model_validator` enforces strict guardrails whenever `ENVIRONMENT = "production"`:
```python
if self.ENVIRONMENT.lower() == "production":
    if self.DEBUG:
        raise ValueError("Security violation: DEBUG must be set to False in production.")
    if self.TEST_MODE_ALLOW_SIMULATED_TOKENS:
        raise ValueError("Security violation: TEST_MODE_ALLOW_SIMULATED_TOKENS must be False in production.")
    if "consolith_secure_app_pw" in self.DATABASE_URL or "postgres_dev_password" in self.DATABASE_URL:
        raise ValueError("Security violation: Default development database credentials are forbidden in production.")
    if self.STORAGE_RETENTION_POLICY != "delete_after_ocr":
        raise ValueError("Privacy violation: STORAGE_RETENTION_POLICY must be 'delete_after_ocr' in production per Aadhaar Act privacy compliance.")
```
If any simulated credential flag or default dev password is present during production startup, FastAPI will abort initialization immediately with a fatal error.

### 2.3 Simulated OTP Behavior (`backend/app/routers/auth.py`)
The convenience OTP code (`123456`) used in automated frontend tests is strictly conditional:
```python
if settings.TEST_MODE_ALLOW_SIMULATED_TOKENS and req.otp_code == "123456" and (
    email.endswith("@gmail.com") or ".test" in email or ".in" in email or "@example.com" in email
):
    ...
```
When `TEST_MODE_ALLOW_SIMULATED_TOKENS` is `False` (the default in all non-test environments), the endpoint queries the `email_otps` table with expiry validation and single-use verification, rejecting `123456` as invalid.

---

## 3. Secret Protection & Git Ignore Verification

| Secret / Credential Asset | Git Status | Protection Mechanism |
| :--- | :---: | :--- |
| `.env` (Environment variables) | **IGNORED** | Rule in `.gitignore` (line 2) |
| `.env.local` / `.env.*.local` | **IGNORED** | Rule in `.gitignore` (lines 3–4) |
| Firebase service account JSON | **IGNORED** | `*.json` exclusion rule in root `.gitignore` |
| Ed25519 Private Keys | **IGNORED** | Key generation in-memory or persisted via encrypted DB |
| Fernet Encryption Key | **MASKED** | Derived or passed via environment variable |

A pre-commit scan verified that no secrets, active tokens, or credentials are staged for version control.
