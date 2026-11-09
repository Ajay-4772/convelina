# CONVELINA — Phase P3H.4: Qdrant Retrieval Integration Design & Local Compatibility Audit
## Deliverable 6: Qdrant Security, Privacy & Integrity Test Plan

**Date of Audit:** 2026-11-09  
**Phase:** P3H.4 (Qdrant Retrieval Integration Design & Local Compatibility Audit)  
**Classification:** QUALITY ASSURANCE & SYSTEM SECURITY SPECIFICATION  
**Scope:** Security Test Suites, RBAC Enforcement, Zero-PII Verification, Dimension Integrity, Quarantine Interception, and Stale Vector Purge Verification  
**Enforcement Baseline:** CONVELINA Operating Rules 4, 5, 6, 7 & 8

---

## 1. Objective & Security Invariants

This test plan defines the mandatory security, privacy, and data-integrity test suites that must pass prior to approving vector ingestion in Phase P3H.5. 

### Core Security Invariants Tested:
1. **Administrative Access Control**: No citizen or unauthenticated caller can invoke vector indexing, collection deletion, or form mutation endpoints (HTTP 401/403).
2. **Zero PII in Vector Payloads**: Vector storage must contain strictly official statutory guidance; zero citizen names, phone numbers, email addresses, or Aadhaar numbers may exist in vector payloads.
3. **Quarantine Isolation**: Ingesting or searching for historical, duplicate, or unconfirmed statutory claims must result in 100% abstention or mandatory human review routing.
4. **Dimension & Payload Contract Integrity**: Qdrant rejects malformed payloads, missing cryptographic hashes, or dimension mismatches before point persistence.
5. **Stale Vector Elimination**: When a source document is updated, legacy points must be cryptographically purged.

---

## 2. Test Suite Specifications

### Test Suite 1: RBAC & Ingestion Endpoint Access Control

| Test ID | Test Scenario | Input / Action | Expected Result | Enforced Rule |
| :--- | :--- | :--- | :--- | :--- |
| `SEC-RBAC-01` | Unauthenticated Ingestion Call | `POST /api/v1/knowledge/admin/sources/ingest-file` without Authorization header | HTTP 401 Unauthorized | RBAC Boundary |
| `SEC-RBAC-02` | Citizen Role Ingestion Call | `POST /api/v1/knowledge/admin/sources/ingest-file` with valid Citizen JWT | HTTP 403 Forbidden (`require_admin` dependency rejects) | RBAC Boundary |
| `SEC-RBAC-03` | Admin Role Ingestion Call | `POST /api/v1/knowledge/admin/sources/ingest-file` with valid Admin JWT | HTTP 200 OK; returns ingestion report with chunk count | RBAC Boundary |
| `SEC-RBAC-04` | Citizen Form Upload Call | `POST /api/v1/knowledge/admin/forms/{form_id}/upload` with Citizen JWT | HTTP 403 Forbidden | RBAC Boundary |
| `SEC-RBAC-05` | Direct Port Access from WAN | TCP probe to Qdrant ports 6333/6334 from non-loopback IP | Connection Refused (bound strictly to `127.0.0.1` in Docker Compose) | Rule 8 (Secret & Network Isolation) |

### Test Suite 2: Privacy & Zero PII Leakage Verification

| Test ID | Test Scenario | Input / Action | Expected Result | Enforced Rule |
| :--- | :--- | :--- | :--- | :--- |
| `SEC-PII-01` | Payload Inspection for Aadhaar Numbers | Regex scan (`\b\d{4}\s\d{4}\s\d{4}\b`) across all 195 chunk payloads in `convelina_core_operational` | **Zero matches**; no 12-digit Aadhaar patterns | Rule 5 (Aadhaar Act Compliance) |
| `SEC-PII-02` | Payload Inspection for Citizen Emails | Regex scan (`[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+`) across all chunk payloads | **Zero personal matches** (only official portals like `@uidai.gov.in`) | Rule 5 (Aadhaar Act Compliance) |
| `SEC-PII-03` | Query Context Masking | Submitting citizen question with unmasked Aadhaar number: `"How to fix my name in Aadhaar 1234 5678 9012?"` | `sanitize_pii()` redacts to `[REDACTED_AADHAAR]`; audit event `pii_masked_in_chat` logged | Rule 5 (Aadhaar Act Compliance) |
| `SEC-PII-04` | Vector Ingestion of User Attachments | Uploading citizen identity proof via chat | Attachment stored in ephemeral `/tmp` with `STORAGE_RETENTION_POLICY="delete_after_ocr"`; **never indexed into Qdrant** | Rule 5 (Aadhaar Act Compliance) |

### Test Suite 3: Vector Dimension & Schema Contract Validation

| Test ID | Test Scenario | Input / Action | Expected Result | Enforced Rule |
| :--- | :--- | :--- | :--- | :--- |
| `SEC-SCH-01` | Dimension Mismatch Rejection | Attempting to upsert a 768-dim vector into 384-dim `convelina_core_operational` | Client raises `ValueError: Vector dimension mismatch (expected 384, got 768)`; transaction aborted | Integration Contract |
| `SEC-SCH-02` | Missing Mandatory Metadata Field | Attempting to upsert chunk without `source_file_sha256` or `retrieval_eligibility` | Pydantic schema validation error (HTTP 422); point rejected before Qdrant API call | Integration Contract |
| `SEC-SCH-03` | Invalid SHA-256 Format | Chunk with truncated hash (`"abc123"`) | Schema validation regex failure (`minLength=64, maxLength=64`) | Integration Contract |
| `SEC-SCH-04` | Malicious Code Injection in Heading | Chunk heading containing `<script>alert(1)</script>` or SQL injection | Output sanitized via `html.escape()` and XML boundary isolation in prompt | Rule 8 (Injection Defense) |

### Test Suite 4: Source Quarantine & Abstention Enforcement

| Test ID | Test Scenario | Input / Action | Expected Result | Enforced Rule |
| :--- | :--- | :--- | :--- | :--- |
| `SEC-QUR-01` | Historical Source Query | Querying: *"What was the UIDAI supporting document list in 2018 under DOC_009?"* | 100% Honest Abstention (`NO_VERIFIED_PROCEDURE_AVAILABLE`); 0 vectors retrieved | Rule 7 (RAG Grounding & Zero Hallucination) |
| `SEC-QUR-02` | DOC_043 Quarantine Intercept | Querying: *"Can an MP/MLA certificate be used for Aadhaar date of birth update under DOC_043?"* | Intercepted with `requires_human_review = True`; displays `SOURCE_METADATA_CONFLICT` warning | P3H.1.4 Acceptance Criteria |
| `SEC-QUR-03` | Out-of-Scope Distractor Query | Querying: *"How to register a commercial satellite under Indian Law?"* | Combined score < 0.55; returns `confidence="insufficient_evidence"`; 0 citations | Rule 7 (RAG Grounding & Zero Hallucination) |
| `SEC-QUR-04` | Unconfirmed Statutory Claim | Querying unverified claim: *"Can PAN card be updated using an online self-attestation without Aadhaar linkage?"* | Zero matching core chunks; returns `NO_VERIFIED_PROCEDURE_AVAILABLE` | Rule 7 (RAG Grounding & Zero Hallucination) |

### Test Suite 5: Stale Vector Purge Verification

| Test ID | Test Scenario | Input / Action | Expected Result | Enforced Rule |
| :--- | :--- | :--- | :--- | :--- |
| `SEC-PUR-01` | PDF Revision Re-Indexing | Admin updates `DOC_001` with modified circular; runs document replacement | Old chunk points deleted via `document_id="DOC_001"` filter selector before new points upserted; point count stays constant | Reindexing Protocol |
| `SEC-PUR-02` | Obsolete Phrase Search | Searching for unique phrase present *only* in superseded revision | Zero hits; old wording produces score < 0.05 in Qdrant | Zero Stale Vectors |
| `SEC-PUR-03` | Audit Event Lineage | Verifying database after replacement | `AuditLog` contains linked entries: `document_replacement_started` $\to$ `document_replacement_completed` | Rule 6 (Append-Only Audit Trail) |

---

## 3. Test Implementation Fixtures & Mock Runners

All test suites defined above are executable via `pytest backend/tests/test_qdrant_security.py` using CONVELINA's existing in-process Qdrant client fixture.

```python
# Conceptual Test Runner Snippet
@pytest.fixture
def isolated_qdrant():
    """Provides an isolated in-memory Qdrant client with dual collections."""
    client = QdrantClient(location=":memory:")
    client.create_collection(
        collection_name="convelina_core_operational",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    client.create_collection(
        collection_name="convelina_reference_secondary",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    return client
```
This guarantees that the complete test suite runs in < 2.0 seconds in local CI environments without external network dependencies.

