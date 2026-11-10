# P3H.9 — Known Limitations, Current Status & Future Roadmap

## 1. Development Mode vs. Live Production Status

| Subsystem / Capability | Current Development State | Production Readiness & Requirements | Safe Fallback Behavior |
|------------------------|---------------------------|-------------------------------------|------------------------|
| **Firebase Authentication** | **SIMULATED (Local Tokens)** | `BLOCKED` until real Firebase credentials (`FIREBASE_SERVICE_ACCOUNT_PATH`) and frontend config (`NEXT_PUBLIC_FIREBASE_API_KEY`, etc.) are provisioned. | Uses deterministic `test_token_:<fuid>:<email>:<name>` format. All authorization, RBAC, and RLS policies remain 100% active and enforced. Non-admin users are rejected from admin endpoints. |
| **Gemini LLM Provider** | **BLOCKED / DISABLED** (`GEMINI_ENABLED=false`) | Disabled by default to ensure deterministic, zero-hallucination statutory legal assistance. Requires Google AI Studio API key (`GEMINI_API_KEY`). | Deterministic BM25 retrieval, rule-based citation engine, and static statutory mapping templates provide complete, trustworthy resolution steps and official forms. |
| **OCR Pipeline** | **READY (Dual-Mode)** | Production-ready with Tesseract OCR binary or host heuristic fallback. | In environments where Tesseract OCR binary is uninstalled on the host OS, the pipeline safely falls back to pdfplumber text extraction and deterministic regex parsing without crashing. |
| **PostgreSQL 16 Database** | **READY & PERSISTENT** | Production-grade schema with forced Row-Level Security (`FORCE ROW LEVEL SECURITY`) across all 21 application tables. Connected via non-superuser role `consolith_app`. | Durable named Docker volume `consolin_pgdata` persists across container restarts and page refreshes. Connection pooling empty-string trap defended by `NULLIF(current_setting(...), '')::uuid`. |
| **Qdrant Vector Database** | **READY & PERSISTENT** | 384-dimensional cosine vector collection `statutory_documents` initialized with named volume `consolin_qdrant_data`. | If Qdrant is temporarily offline, the RAG engine automatically degrades to pure BM25 keyword search without throwing 500 errors to the citizen. |
| **Ed25519 PKI Attestation** | **READY** | Active RFC 8032 digital signature generation and verification. | Generates cryptographic attestation signatures embedded into exported PDF petitions and representations. |
| **Application Explorer (`/dev/explorer`)** | **DEV ONLY** | Strictly disabled in production. Returns `404 Not Found` when `NEXT_PUBLIC_ENVIRONMENT === "production"` and API returns `403 Forbidden`. | Ensures internal telemetry, test account switchers, and route inventories are never exposed on public cloud deployments. |

---

## 2. In-Depth Subsystem Assessments

### A. Firebase Authentication & Identity Management
- **Current Mode**:
  - The developer has explicitly instructed not to invent or fabricate fake Firebase credentials.
  - In development mode, `TEST_MODE_ALLOW_SIMULATED_TOKENS=true` allows the application to construct and accept development tokens.
  - When a synthetic user logs in or switches accounts in `/dev/explorer`, `AuthContext` writes to `localStorage.convelina_test_token`.
  - The FastAPI backend validates the token structure, extracts the synthetic user claims, and provisions or retrieves the user from PostgreSQL.
- **Production Path**:
  - Provision a Google Firebase project.
  - Place the service account JSON file in a secure location specified by `FIREBASE_SERVICE_ACCOUNT_PATH`.
  - Populate `.env` with actual frontend credentials (`NEXT_PUBLIC_FIREBASE_PROJECT_ID`, `NEXT_PUBLIC_FIREBASE_API_KEY`, etc.).
  - Set `TEST_MODE_ALLOW_SIMULATED_TOKENS=false`.

### B. Gemini Large Language Model & Conversational RAG
- **Current Mode**:
  - `GEMINI_ENABLED=false` is enforced in backend settings.
  - Grounded legal advice is generated through deterministic statutory templates, BM25 retrieval over official government circulars, and structured resolution context.
  - Zero hallucination policy: the assistant will decline to answer or cite regulations if the relevance score falls below 0.55.
- **Production Path**:
  - Acquire Gemini API key and configure `GEMINI_API_KEY` in backend `.env`.
  - Enable `GEMINI_ENABLED=true`.
  - The existing hybrid retriever will pass retrieved statutory context to Gemini 1.5 Flash for conversational synthesis with mandatory citation validation.

### C. Host OCR & Multilingual Scripts
- **Current Mode**:
  - Tesseract OCR handles standard image and PDF text recognition.
  - Fallback regex handles synthetic PDF samples cleanly.
  - Non-Latin scripts (Devanagari, Tamil, Telugu) without verified OCR confidence are explicitly flagged as `"unresolvable — needs manual review"` per project rule #3 ("Fail-Safe, Never Silently Wrong").
- **Production Path**:
  - Ensure Google Cloud Vision API or full `tesseract-ocr` language packs (`tessdata/hin.traineddata`, etc.) are installed on the production worker container.

---

## 3. Platform Architecture Invariants Maintained

Throughout P3H.9 and all previous phases, CONVELINA strictly maintains these architectural invariants:
1. **Exactly Two Roles**: Only `USER` (citizen) and `ADMIN` (platform administrator) exist. Zero officer or verifier roles exist in the database, API, or frontend.
2. **PostgreSQL Forced RLS**: All 21 tables holding user data enforce `FORCE ROW LEVEL SECURITY`. Runtime connections use the dedicated non-superuser role `consolith_app`.
3. **Immutable Audit Ledger**: Database triggers block `UPDATE` and `DELETE` on `audit_log`. Each audit entry cryptographically links to the prior entry via SHA-256 hash chaining.
4. **Aadhaar Act Compliance**: Sensitive identity numbers (Aadhaar, PAN) are masked before persistence. Raw document images are purged after ephemeral OCR extraction.
