# CONVELINA — Security Remediation Phase P0.1 Report

**Phase:** P0.1 — Dependency Vulnerabilities, Regression Stabilization & Security Tooling  
**Branch / Base Commit:** `main` @ `e22d16b` (`test(p3h13): complete paired OCR benchmark validation`)  
**Migration Baseline:** `022_security_hardening.sql` verified applied (`2026-11-12 09:35:38+00`)  
**Status:** Verified against live `convelina-postgres` (PostgreSQL 16), `convelina-qdrant`, `convelina-backend` Linux container, and Next.js production build (no commits or pushes executed).

---

## 1. Git & Environment Baseline

- **Current Branch:** `main`
- **Latest Commit:** `e22d16b test(p3h13): complete paired OCR benchmark validation`
- **Database Migrations:** `001` through `022_security_hardening.sql` applied; `email_otps` schema verified with `otp_hash`, `otp_salt`, `attempt_count`, `locked_until`, `verification_token_hash`, `request_ip`, forced RLS enabled (`p_email_otps_scoped`), and `consolith_app` confirmed `rolsuper = f`, `rolbypassrls = f`.

---

## 2. Dependency Vulnerability Remediation (Frontend & Backend)

### 2.1 Next.js & Transitive Frontend Upgrade Analysis
1. **Baseline Audit (`next@14.2.13`, `firebase@10.13.2`):** `15` advisories (`1 critical`, `7 high`, `7 moderate`) spanning `next`, `postcss`, `postcss-selector-parser`, `source-map-js`, `firebase`, `@firebase/*`, `undici`, and `@grpc/grpc-js`.
2. **Next.js 14.2.x vs 15.x vs 16.x Evaluation:**
   - Upgrading to `next@14.2.35` left post-14.2.35 vulnerabilities (`<=15.5.27` Server Actions DoS, Image Optimizer SVG RCE, Windows RCE) and nested `postcss` advisories unresolved.
   - Upgrading to `next@15.5.29` cleared Next.js direct CVEs (`critical: 0`), but bundled `postcss <= 8.5.22` kept `next` flagged via `postcss` and left `firebase@10.13.2` (`undici`/`@grpc/grpc-js`) flagged.
   - Selecting **`next@^16.4.6`** + **`firebase@^13.3.0`** (with `react@18.3.1` supported per `next@16.4.6` `peerDependencies`) cleared all Next.js, `postcss`, `postcss-selector-parser`, `source-map-js`, and `undici` advisories without `--force`.
   - The remaining transitive chain (`firebase -> @firebase/firestore-compat -> @firebase/firestore -> @grpc/grpc-js <= 1.13.5`) was checked: `frontend/src` contains **zero** `firestore` imports, and adding `"overrides": { "@grpc/grpc-js": "^1.14.7" }` in [package.json](file:///c:/Users/ajaya/Desktop/consolin/frontend/package.json) bumped `@grpc/grpc-js` cleanly to a patched `1.x` release.

#### Exact Before & After `npm audit` Results
- **Before:** `15 vulnerabilities (7 moderate, 7 high, 1 critical)`
- **After (`npm --prefix frontend audit` verbatim):**
```text
found 0 vulnerabilities
```

#### Frontend Build, Middleware & Compatibility Verification
- `npx tsc --noEmit`: Exited `0`
- `npm run build` (`Next.js 16.4.6 Turbopack`): Exited `0` (all 16 app routes + middleware proxy built cleanly)
- **Playwright Auth/RBAC E2E** (`e2e/authentication.spec.ts` + `e2e/authorization.spec.ts`): **7 passed (`37.6s`)**
- **Playwright Citizen Repository E2E** (`e2e/citizen_repository.spec.ts`): **1 passed (`25.3s`)**
- **Live Next.js Security Headers & Middleware Probe:** `HTTP 200` on `/login`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy` containing `frame-ancestors 'none'`, `X-Powered-By: None`, and `Host: admin.localhost:3000` `/signup` -> `307 Location: /admin/login`.

### 2.2 Backend Dependency Remediation (`backend/requirements.txt`)
- Upgraded stale parser/crypto/web packages cleanly in both `backend/.venv` and [requirements.txt](file:///c:/Users/ajaya/Desktop/consolin/backend/requirements.txt):
  - `Pillow`: `10.4.0` -> `13.0.0` (4 Critical, 33 High, 15 Medium CVEs resolved)
  - `pypdf`: `5.0.1` -> `7.0.1` (20 High, 43 Medium, 4 Low CVEs resolved)
  - `cryptography`: `43.0.1` -> `50.0.2` (3 High, 2 Low CVEs resolved)
  - `python-multipart`: `0.0.12` -> `0.0.33` (4 High, 1 Medium, 3 Low CVEs resolved)
  - `fastapi`: `0.115.0` -> `0.162.5` (and `.venv` `starlette==1.10.0`, `urllib3==2.8.0`, `anyio==4.16.0`, `fonttools==4.68.0`, `python-dotenv==1.2.4`)
  - `langchain`: `0.3.30` -> `1.5.0`, `langchain-core`: `0.3.86` -> `1.8.0`, `langchain-community`: `0.3.27` -> `0.4.2`

---

## 3. Complete Backend Regression & Root-Cause Resolution

The earlier host regression (`393 passed, 23 failed`) was fully investigated and every category resolved cleanly without skipping tests or weakening security assertions:

| Root-Cause Category | Specific Cause Found | Resolution Applied |
| :--- | :--- | :--- |
| **Genuine App Bug Found via Ruff `F821`** | [engine.py](file:///c:/Users/ajaya/Desktop/consolin/backend/app/ocr/engine.py) used `settings.MAX_UPLOAD_PDF_PAGES` without importing `settings` (`NameError` during PDF OCR extraction) | Imported `from app.config import settings` in [engine.py](file:///c:/Users/ajaya/Desktop/consolin/backend/app/ocr/engine.py) |
| **Genuine RAG Eligibility Gap** | [bm25_engine.py](file:///c:/Users/ajaya/Desktop/consolin/backend/app/rag/retrieval/bm25_engine.py) & [retriever.py](file:///c:/Users/ajaya/Desktop/consolin/backend/app/rag/retrieval/retriever.py) did not filter `is_active == False`, `verification_status in ("unverified", "outdated", "retired", "rejected")`, `retrieval_eligibility == "INELIGIBLE"`, or non-`DOC_043` `needs_review` chunks | Enforced strict source-status and eligibility filtering while preserving `DOC_043` (`SOURCE_METADATA_CONFLICT` + mandatory statutory disclaimer) |
| **Mandatory Production MFA Gap** | [auth.py](file:///c:/Users/ajaya/Desktop/consolin/backend/app/dependencies/auth.py) only checked `ADMIN_REQUIRE_MFA`; `production` with default `False` could bypass MFA | Enforced `require_mfa = bool(settings.ADMIN_REQUIRE_MFA) or settings.ENVIRONMENT.lower() == "production"` |
| **ClamAV Unavailability Transparency** | `/health` in [main.py](file:///c:/Users/ajaya/Desktop/consolin/backend/app/main.py) did not surface AV status | Added `services["malware_scanner"]` reporting `"unavailable"` when `CLAMAV_HOST` is unset |
| **Stale Legacy Test Expectations** | `test_p2c_llm_grounding.py` (`test_07`, `test_08`), `test_sprint8b_packaging.py` (`test_in_process_qdrant_seeding_and_retrieval`), and `test_upload_ocr.py` (`test_token_{uid}` missing colon) asserted pre-P3H5 keys or old token prefixes | Updated those tests cleanly to match canonical `HybridRetriever` fields and `test_token_:uid:email` contract |
| **Persistent DB Collisions & Unset RLS Context in Test Setup** | `test_auth.py` and `test_firebase_auth_security.py` reused static emails across runs with random UIDs or queried `users`/`audit_log` directly without `set_rls_context` | Scoped test fixture emails per test run and added `set_rls_context` only for direct SQLAlchemy test-fixture setup/verification, plus fixed `Document` column names in `test_scenario_16` |
| **Windows Environment Dependencies** | Windows host lacks Linux `tesseract 5.5.0` binary and `Lohit-Tamil`/`FreeSans`/`DejaVuSans` fonts needed by `test_field_level_ocr_and_user_confirmation.py`, `test_p3e_multimodal_attachments.py`, and `test_p3g4_multilingual_export.py` | Executed full backend suite inside `convelina-backend` Linux container against live `convelina-postgres` |

### Final Observed Test Counts (Post-Final Edit)
- **Full Backend Regression (`pytest backend/tests` inside `convelina-backend` Linux container):** **416 collected, 416 passed, 0 failed, 0 skipped, 0 errors** (`117.08s`)
- **Host `.venv` 20-Case Security Hardening Suite ([test_security_hardening_suite.py](file:///c:/Users/ajaya/Desktop/consolin/backend/tests/test_security_hardening_suite.py)):** **20 collected, 20 passed, 0 failed** (`22.61s`)
- **Live PostgreSQL 16 Forced-RLS Suite ([test_rls_isolation.py](file:///c:/Users/ajaya/Desktop/consolin/scripts/test_rls_isolation.py)):** **10/10 passed**

---

## 4. Security Scanner Tooling & Findings Triage

Installed and configured both local automation ([run_security_scans.ps1](file:///c:/Users/ajaya/Desktop/consolin/scripts/run_security_scans.ps1)) and CI workflow ([security.yml](file:///c:/Users/ajaya/Desktop/consolin/.github/workflows/security.yml)).

| Tool | Target | Observed Output Summary | Finding Triage |
| :--- | :--- | :--- | :--- |
| **Ruff (`F821,S105,S108,S110,S112,S310,S324`)** | `backend/app` | Caught `2` real `F821` (`settings` undefined in `ocr/engine.py`), `1` `S310` (`urllib` in `email_service.py` -> replaced with `httpx.post` + `mask_email`), `1` `S324` (`md5` -> `usedforsecurity=False`). Post-fix: `11` remaining (`S105`, `S108`, `S110`, `S112`) | `F821` fixed; `S310` & `S324` resolved; remaining `11` triaged as false positives (`"test_token_*"`, `"TOKEN_ORDER_VARIATION"`, container `/tmp/consolith/*` defaults, non-fatal logging fallbacks) |
| **Bandit (`-ll`)** | `backend/app` (`21,340` LOC) | **0 High, 3 Medium, 10 Low** | `3` Medium are all `B108` (`/tmp/consolith/temp_*` default Docker paths for containerized scratch dirs); `10` Low are test-token/enum strings & fail-safe exception guards |
| **Semgrep (`p/python`, `p/security-audit`)** | `backend/app` | Initially `4` findings (`use-defused-xml` in `prompt_templates.py`, `md5` in `embeddings.py`, `logger-credential-disclosure` in `draft_translation_service.py` & `email_service.py`). Fixed first 3; final scan: **1 finding** (`email_service.py:31`) | Final finding (`"RESEND_API_KEY unconfigured..."` literal string) confirmed **false positive** (no credential logged) |
| **Trivy (`0.76.2`)** | `backend/requirements.txt`, `frontend/package-lock.json`, Dockerfiles | `requirements.txt` dropped **127 -> 0** MEDIUM/HIGH/CRITICAL CVEs; `package-lock.json`: **0** CVEs; `backend/Dockerfile`: **0** misconfigs; `frontend/Dockerfile`: **0** misconfigs | Clean across all scanned targets |
| **Gitleaks (`8.30.1`)** | Git repository (`36` commits, `9.18 MB`) | **`no leaks found`** | Confirmed zero committed secrets |
| **`npm audit`** | `frontend/` | **`15 -> 0 vulnerabilities`** | Zero critical/high/moderate/low advisories |
| **`pip-audit` (Clean Linux `python:3.11-slim`)** | `backend/requirements.txt` | With base `setuptools 79.0.1`: `3` base-tool vulns (`PYSEC-2026-3447`, `GHSA-xmj3-9gf7-h52w`); **0 CVEs across all CONVELINA application packages** | Updated `backend/Dockerfile` to upgrade `pip` and `setuptools>=84.1.0`; verifies none of the `120` host-env CVEs affect deployed app dependencies |
| **`pip-audit` (Host Windows `.venv`)** | Shared host `.venv` | Reduced **268 -> 120 CVEs in 18 shared/non-app Windows packages** | `bokeh`, `dnspython`, `filelock`, `flask`, `fsspec`, `gitpython`, `lxml`, `pdfminer-six`, `pip`, `pyarrow`, `pygments`, `pymongo`, `pypdf2`, `setuptools`, `streamlit`, `torch`, `tornado`, `werkzeug` — non-deployed host packages, not part of `requirements.txt` |

---

## 5. Security Control Verification Matrix (Sections 5–10)

- **IAM & MFA (Section 5):** Firebase JWT verification (`check_revoked=True`), unsigned `eyJ...` rejection (`test_01`), staging/prod test-token lockout (`test_02`), RBAC `403` (`test_03`), role-injection defense (`test_04`), dev MFA optionality vs strict production MFA enforcement (`test_05`), and HMAC-SHA256 OTP hashing with 5-attempt lockout & IP rate limiting (`test_06`, `test_07`) all verified.
- **Database Isolation (Section 6):** All **21** public tables verified via `pg_class`/`pg_policies` with `relrowsecurity = true` and `relforcerowsecurity = true`, `consolith_app` confirmed `rolsuper = f`, `rolbypassrls = f`, `email_otps` uses `p_email_otps_scoped`, `test_rls_isolation.py` passed `10/10`, and router-level IDOR filters (`test_08`) + immutable `audit_log` triggers (`test_09`) passed.
- **Cryptography & Key Management (Section 7):** Direct 32B Fernet keys, HKDF-SHA256 context separation, `v1:`/`v2:` MultiFernet rotation, **legacy unversioned SHA-256 Fernet backward-compatibility decrypt** (`test_10`), and production Ed25519 deterministic-seed refusal (`test_11`) all verified.
- **File Upload Security (Section 8):** Magic bytes + MIME header matching, EICAR & polyglot rejection (`test_12`), PDF `25`-page limit + `/JavaScript`/`/OpenAction` rejection + image dimension/pixel bomb caps (`test_13`), filename traversal defense, and explicit `/health` reporting of `"malware_scanner": {"status": "unavailable"}` when `CLAMAV_HOST` is unconfigured (`test_20`) verified.
- **AI & Privacy Security (Section 9):** XML escaping & injection flagging (`test_15`), citation allowlist validation (`test_16`), RAG source eligibility/outdated rejection + `DOC_043` preservation (`test_07`, `test_08`, `test_doc043_statutory_restrictions`), PII & log scrubbing (`test_14`), admin user masking (`test_19`), and synthetic dataset tests all passed.
- **Production Infrastructure Prerequisites (Section 10 — Not Deployed):** Production Firebase service account credentials, Cloud KMS / Vault key wrapping for Fernet KEKs & Ed25519 keys, TLS termination (reverse proxy/ALB with HTTPS + HSTS), live ClamAV daemon (`CLAMAV_HOST`), private-network PostgreSQL 16 & Qdrant (no public ports), Secret Manager injection (`ENVIRONMENT=production`, `DEBUG=False`, `TEST_MODE_ALLOW_SIMULATED_TOKENS=False`), automated encrypted backups via [backup_and_restore.py](file:///c:/Users/ajaya/Desktop/consolin/scripts/backup_and_restore.py), and enrolled hardware/TOTP 2FA factors on all production `admin` Firebase accounts.

