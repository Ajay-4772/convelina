# CONVELINA — Phase P3H.4.1: Rapid Design Reconciliation
## Deliverable 6: Vector Security, Data Privacy & Boundary Protection Contract

**Date of Contract:** 2026-11-09  
**Phase:** P3H.4.1 (Rapid Design Reconciliation & Qdrant Integration Readiness)  
**Classification:** MANDATORY SECURITY & COMPLIANCE CONTRACT  
**Governing Standard:** CONVELINA Operating Rules 4, 5, 6, 7 & 8 • Aadhaar Act 2016 Privacy Invariants  
**Policy Status:** STRICT ZERO-PII VECTOR PAYLOAD MANDATE

---

## 1. Zero-PII Invariant & Strict Payload Allowlist

A foundational security principle of CONVELINA is that **Qdrant vector databases must NEVER contain citizen Personally Identifiable Information (PII)**. Vector storage is reserved strictly and exclusively for official government procedural guidance, form specifications, and legal rules.

### 1.1 Prohibited Data Categories (Blacklist)
The ingestion worker and API endpoints strictly reject and sanitize any vector payload containing:
1. **Citizen Names** (e.g. applicant full names, guardian names, spouse names).
2. **Aadhaar Numbers** (raw or unmasked 12-digit Aadhaar patterns `\b\d{4}\s\d{4}\s\d{4}\b`).
3. **PAN Numbers** (10-character alphanumeric tax identifiers `[A-Z]{5}[0-9]{4}[A-Z]{1}`).
4. **Phone Numbers & Personal Email Addresses**.
5. **Physical Citizen Addresses & Biometric Signatures**.
6. **Uploaded Identity Document OCR Text** (citizen identity scans are ephemeral and processed in `/tmp`, never indexed into vector storage).
7. **Citizen Conversation Messages or Chat History**.

### 1.2 Explicit Payload Allowlist (Permitted Fields Only)
Only the following 15 non-personal, statutory metadata fields may be written to Qdrant vector payloads:

| Payload Field Name | Allowed Data Type | Purpose | Sample Value |
| :--- | :--- | :--- | :--- |
| `chunk_id` | `string` | Deterministic chunk identifier | `"DOC_001_c001"` |
| `document_id` | `string` | Canonical document identifier | `"DOC_001"` |
| `document_title` | `string` | Official government title | `"Aadhaar Enrolment and Update Form"` |
| `issuing_authority` | `string` | Issuing government agency | `"Unique Identification Authority of India (UIDAI)"` |
| `document_category` | `string` | Identity category | `"aadhaar"` |
| `document_function` | `string` | Controlled procedural function | `"APPLICATION_FORM"` |
| `page_start` | `integer` | Physical start page | `1` |
| `page_end` | `integer` | Physical end page | `2` |
| `section_reference` | `string` | Heading or section ID | `"Section 2: Demographic Details"` |
| `applicant_cohort` | `string` | Target citizen demographic group | `"ADULT_RESIDENTS_18_PLUS"` |
| `lifecycle_stage` | `string` | Procedural stage | `"UPDATE_CORRECTION"` |
| `retrieval_eligibility` | `string` | Controlled retrieval access | `"CORE_SEARCH_SPACE"` |
| `current_applicability_status` | `string` | Current legal applicability | `"ACTIVE_CURRENT"` |
| `source_authenticity_status` | `string` | Provenance classification | `"OFFICIALLY_PUBLISHED"` |
| `source_file_sha256` | `string` | 64-char hex hash of physical PDF | `"68b2eac3...cec300d4"` |
| `human_review_required` | `boolean` | Safety & review flag | `false` |
| `chunk_text` | `string` | Official procedural prose | `"[Official Form 1] Residents may update..."` |

---

## 2. Authentication, Authorization & Role Boundaries

### 2.1 Role-Based Access Control (RBAC)
- **`CITIZEN` Role (Standard Authenticated User)**:
  - Has `READ-ONLY` access to vector search through the guarded RAG Orchestrator (`POST /api/v1/assistant/chat`).
  - Has zero access to vector write, delete, collection creation, or re-indexing endpoints.
  - Direct HTTP calls to `/api/v1/knowledge/admin/*` immediately return **`HTTP 403 Forbidden`**.
- **`ADMIN` Role (Authenticated System Administrator)**:
  - Authorized to invoke ingestion and replacement endpoints (`POST /api/v1/knowledge/admin/sources/ingest-file`).
  - Access enforced via FastAPI dependency `current_user: User = Depends(require_admin)`.

### 2.2 Row-Level Security (RLS) & Connection Scoping
- The backend application connects to PostgreSQL strictly as the dedicated non-superuser role `consolith_app`.
- Session settings are scoped via `set_rls_context(db, user_id, role)` using:
  `SET LOCAL app.current_user_id = NULLIF(:user_id, '')::uuid`
  `SET LOCAL app.current_user_role = NULLIF(:role, '')`
- RLS policies are **FORCED** (`ALTER TABLE ... FORCE ROW LEVEL SECURITY`), preventing accidental leakage of user cases or documents across tenant boundaries.

---

## 3. Network Isolation & Boundary Protections

1. **Loopback Port Binding**:
   - In `docker-compose.yml`, Qdrant ports `6333` and `6334` are strictly bound to `127.0.0.1`.
   - Qdrant is **never exposed to the public Internet or WAN**.
2. **Container Network Isolation**:
   - Qdrant communicates with the `backend` container across the internal Docker bridge network (`convelina_default`).
3. **Cross-Collection Leakage Prevention**:
   - Citizen retrieval queries against `convelina_core_operational` specify hard Qdrant collection routing.
   - Reference-only documents are physically stored in the separate collection `convelina_reference_secondary`.
   - Historical and out-of-scope documents reside solely in PostgreSQL relational tables with `retrieval_eligibility = 'EXCLUDED'`; they do not possess vectors in Qdrant.

---

## 4. Cryptographic Audit Trail (Rule 6 Compliance)

Every vector modification, ingestion run, document replacement, or collection purge generates an append-only audit event in the `AuditLog` table.

### 4.1 Immutability Triggers
- PostgreSQL database triggers block any `UPDATE` or `DELETE` on `audit_log`:
  ```sql
  CREATE OR REPLACE FUNCTION block_audit_log_mutation()
  RETURNS TRIGGER AS $$
  BEGIN
      RAISE EXCEPTION 'Security violation: audit_log is strictly append-only. UPDATE and DELETE are prohibited.';
  END;
  $$ LANGUAGE plpgsql;
  ```

### 4.2 Hash Chain Linkage
- Each audit log record computes a SHA-256 hash incorporating the previous entry's hash:
  $$\text{record\_hash} = \text{SHA256}(\text{previous\_hash} + \text{timestamp} + \text{action} + \text{user\_id} + \text{details\_json})$$
- This guarantees tamper-evident provenance across all vector database modifications.

---

## 5. Security & Privacy Acceptance Matrix

| Requirement | Implementation Mechanism | Verification Test |
| :--- | :--- | :--- |
| **No Citizen PII in Payloads** | Payload Allowlist + Regex Sanitizer | `SEC-PII-01`, `SEC-PII-02` |
| **Admin-Only Vector Writes** | `Depends(require_admin)` | `SEC-RBAC-01`, `SEC-RBAC-02` |
| **Quarantined Claim Safety** | Automated Intercept + Human Review Notice | `SEC-QUR-02` (`DOC_043`) |
| **Tamper-Evident Logging** | Append-only Hash Chain Trigger | `SEC-PUR-03` |
| **Network Ingress Defense** | Localhost binding (`127.0.0.1:6333`) | `SEC-RBAC-05` |

