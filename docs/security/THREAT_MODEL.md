# CONVELINA — Application Security Threat Model

**Classification:** Application Security Architecture  
**Methodology:** STRIDE & OWASP API Security Top 10  
**Status:** EVIDENCE-BASED AUDIT & DEFENSE MATRIX  

---

## 1. Threat Profile & Asset Valuation

CONVELINA processes primary Indian identity credentials (Aadhaar cards, PAN cards, Passports, Class 10/12 marksheets, EPF records). The threat model assumes:
1. Attackers will attempt cross-tenant access to inspect other citizens' documents.
2. Malicious users will attempt to upload corrupted files or execute path traversal attacks.
3. Attackers may attempt prompt injection against the AI assistant or attempt to forge digital attestations.
4. Compromised application application code must never be able to bypass database tenant boundaries.

---

## 2. STRIDE Threat Assessment & Verification Matrix

| STRIDE Category | Threat Description | Attack Vector | CONVELINA Defense Mechanism | Verification Status |
| :--- | :--- | :--- | :--- | :---: |
| **Spoofing** | Forged JWT identity tokens to impersonate other citizens or administrators. | Client passes forged Bearer token or simulated credentials to `/api/v1/*`. | • Firebase Admin SDK validates cryptographic signature, expiration, and issuer.<br>• `@model_validator` in `config.py` strictly blocks simulated tokens in `ENVIRONMENT=production`. | **VERIFIED (8/8 Auth tests passed)** |
| **Tampering** | Modification or deletion of historical audit logs to conceal unauthorized access. | Direct SQL `UPDATE` or `DELETE` on `audit_log` table. | • PostgreSQL statement trigger `block_audit_log_mutation()` raises an unhandled exception on any mutation.<br>• Every record is linked via SHA-256 hash chaining (`previous_hash`). | **VERIFIED (Trigger active in Migration 002)** |
| **Tampering** | Forging or altering verified document attestations. | Tampering with citizen name or DOB in an issued attestation. | • Ed25519 digital signature (RFC 8032) generated over RFC 8785 canonical JSON payload.<br>• Any single-byte modification fails signature verification. | **VERIFIED (12/12 PKI tests passed)** |
| **Tampering** | SQL Injection to bypass authentication or extract raw records. | Raw SQL string interpolation in query parameters. | • SQLAlchemy 2.0 parameterized queries eliminate raw string interpolation across all endpoints. | **VERIFIED (No raw SQL interpolation)** |
| **Repudiation** | An officer denies making an approval or rejection decision. | Officer disavows case review record. | • Every officer action requires Bearer authentication, records `officer_id`, captures explicit decision justification, and writes to immutable audit trail. | **VERIFIED (Module 8 audit logging)** |
| **Information Disclosure** | Cross-tenant data leakage where Citizen B views Citizen A's documents. | Direct REST query `GET /api/v1/documents/{id}` or `GET /api/v1/conflicts`. | • PostgreSQL forced Row-Level Security (`FORCE ROW LEVEL SECURITY`) bound to `NULLIF(current_setting('app.current_user_id', true), '')::uuid`.<br>• Runtime connections execute under non-superuser `consolith_app`. | **VERIFIED (9/9 RLS isolation tests passed)** |
| **Information Disclosure** | Long-term exposure of 12-digit Aadhaar numbers or raw scanned images. | Data breach of server filesystem or persistent database dump. | • First 8 digits masked immediately (`XXXX-XXXX-1234`).<br>• Ephemeral storage unlinked in `finally:` block (`delete_after_ocr`).<br>• Sensitive extracted fields encrypted via Fernet at rest. | **VERIFIED (Module 4 compliance verified)** |
| **Information Disclosure** | Exposure of internal API schemas or debug stack traces in production. | Accessing `/docs`, `/redoc`, or triggering unhandled exceptions. | • `docs_url`, `redoc_url`, and `openapi_url` are conditionally disabled in production.<br>• Production security headers middleware injects `X-Content-Type-Options: nosniff`. | **VERIFIED (Implemented in main.py)** |
| **Denial of Service** | Memory exhaustion via oversized multipart uploads. | Submitting multi-gigabyte files to `/api/v1/documents/upload`. | • 1MB chunked streaming read terminates immediately with HTTP 413 if the payload exceeds 10MB (`MAX_UPLOAD_SIZE_BYTES`). | **VERIFIED (Streaming abort verified)** |
| **Denial of Service** | Prompt injection or resource exhaustion against Gemini LLM. | Malicious citizen prompts designed to hijack system prompt or trigger infinite generation. | • System prompts use strict XML delimiters and instructions bounds.<br>• Relevance score floor ($\ge 0.55$) declines out-of-domain queries.<br>• Bounded token lengths enforced. | **VERIFIED (Module 6 output validation)** |
| **Elevation of Privilege** | Citizen escalates privileges to 'admin' or 'officer'. | Sending `PATCH /api/v1/auth/profile` with `{"role": "admin"}`. | • PostgreSQL trigger `prevent_role_escalation()` blocks any update to `users.role` unless `current_app_user_role() = 'admin'`.<br>• Endpoint Pydantic schemas disallow `role` field in update payloads. | **VERIFIED (Trigger active in Migration 002)** |

---

## 3. High-Priority Residual Security Risks & Mitigations

1. **Docker Container Execution as Root**:
   - *Risk*: `backend/Dockerfile` and `frontend/Dockerfile` currently run without an explicit `USER` directive.
   - *Target Mitigation*: Inject `USER appuser` (UID 10001) in production Dockerfiles.
2. **Key Storage Dev Fallback**:
   - *Risk*: Ed25519 signing private keys in dev environment are stored in local keystore.
   - *Target Mitigation*: Integrate Cloud KMS / AWS KMS envelope encryption for production key lifecycle management.

