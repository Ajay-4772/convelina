# CONVELINA — Knowledge Ingestion & Corpus Operations Runbook (P3H.5)

## 1. Overview & Operational Principles

This runbook defines the operational procedures for managing, ingesting, promoting, and rolling back knowledge base collections for CONVELINA.

The ingestion pipeline follows a strict staged architecture:
```
[Pre-Flight Hash Validation]
             │
             ▼
[Candidate Strategy 6 Chunking]
             │
             ▼
[Deterministic Point ID Generation (UUIDv5)]
             │
             ▼
[Isolated Staging Upload]
             │
             ▼
[Point Count & Smoke Test Verification]
             │
             ▼
[Atomic Activation & BM25 Cache Switch]
```

---

## 2. Invariants & Pre-Flight Checklist

Before triggering an ingestion run, operators must verify:
- [x] Authoritative source documents are present in `forms/` directory.
- [x] Manifest files exist:
  - `forms/CORE_OPERATIONAL_KNOWLEDGE_CORPUS_MANIFEST.csv` (8 Core docs)
  - `forms/REFERENCE_ONLY_CORPUS_MANIFEST.csv` (12 Reference docs)
  - `forms/P3H4_1_CORPUS_RECONCILIATION.csv` (47 reconciled docs)
- [x] Preprocessed JSONL files exist:
  - `forms/CORE_KNOWLEDGE_RECORDS.jsonl`
  - `forms/REFERENCE_KNOWLEDGE_RECORDS.jsonl`
- [x] Expected deterministic chunk outputs:
  - **Core Operational Chunks**: Exactly **167**
  - **Reference Secondary Chunks**: Exactly **28**
  - **Total Chunks**: Exactly **195**
  - **DOC_043 Chunks**: Exactly **21**

---

## 3. CLI Ingestion Execution

To run knowledge ingestion from the terminal:

### 3.1 Standard Execution (Automatic Version Tagging)
```powershell
backend\.venv\Scripts\python.exe scripts/run_corpus_ingestion.py
```

### 3.2 Custom Version Tagging
```powershell
backend\.venv\Scripts\python.exe scripts/run_corpus_ingestion.py --version-tag v20261109_prod
```

### 3.3 Safe Dry Run (Validation & Chunking Only, No Vector Writes)
```powershell
backend\.venv\Scripts\python.exe scripts/run_corpus_ingestion.py --dry-run
```

---

## 4. Administrative API Operations

Knowledge base operations can also be managed via authenticated administrative endpoints.

### 4.1 Triggering Ingestion
```http
POST /api/v1/knowledge/admin/ingest HTTP/1.1
Host: localhost:8000
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json

{
  "version_tag": "v20261109_release",
  "dry_run": false
}
```

**Expected Response**:
```json
{
  "job_id": "4b6c3d9a-...",
  "status": "activated",
  "version_tag": "v20261109_release",
  "core_chunks_indexed": 167,
  "reference_chunks_indexed": 28,
  "staging_collections": [
    "convelina_core_operational_v20261109_release",
    "convelina_reference_secondary_v20261109_release"
  ],
  "active_collections": [
    "convelina_core_operational_v20261109_release",
    "convelina_reference_secondary_v20261109_release"
  ],
  "created_at": "2026-11-09T10:45:00Z",
  "completed_at": "2026-11-09T10:45:15Z"
}
```

### 4.2 Checking Collection Health & Point Counts
```http
GET /api/v1/knowledge/admin/collections/health HTTP/1.1
Host: localhost:8000
Authorization: Bearer <ADMIN_TOKEN>
```

**Response Format**:
```json
{
  "backend_mode": "in_process_memory",
  "active_version": "v20261109_release",
  "collections": {
    "convelina_core_operational": {
      "name": "convelina_core_operational",
      "exists": true,
      "points_count": 167,
      "vector_size": 1024,
      "distance": "Cosine",
      "status": "green"
    },
    "convelina_reference_secondary": {
      "name": "convelina_reference_secondary",
      "exists": true,
      "points_count": 28,
      "vector_size": 1024,
      "distance": "Cosine",
      "status": "green"
    }
  }
}
```

### 4.3 Rollback to Previous Version
In the event of an indexing error, discrepancy, or corrupted release, an immediate rollback can be triggered:
```http
POST /api/v1/knowledge/admin/collections/rollback HTTP/1.1
Host: localhost:8000
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json

{
  "target_version": "v1.0.0-initial"
}
```

---

## 5. Retrieval Diagnostics & Inspection

Administrators can evaluate query retrieval quality, score breakdown, and abstention reasons:

```http
POST /api/v1/knowledge/retrieval/diagnostics HTTP/1.1
Host: localhost:8000
Authorization: Bearer <ADMIN_TOKEN>
Content-Type: application/json

{
  "query": "supporting documents for date of birth update in aadhaar",
  "top_k": 3,
  "mode": "lexical_only"
}
```

**Response**:
```json
{
  "query": "supporting documents for date of birth update in aadhaar",
  "normalized_query": "supporting birth date documents in update of aadhaar",
  "mode": "lexical_only",
  "retrieved_count": 3,
  "abstention_triggered": false,
  "chunks": [
    {
      "chunk_id": "PROC_DOC_013_P01_UNIT01",
      "document_id": "DOC_013",
      "document_title": "UIDAI Circular on Date of Birth Update",
      "page_number": 1,
      "section_title": "Page 1",
      "score": 5.3757,
      "bm25_score": 5.3757,
      "source_status": "OFFICIALLY_PUBLISHED",
      "human_review_required": false,
      "is_doc043": false
    }
  ]
}
```

---

## 6. Troubleshooting Common Issues

### 6.1 `RuntimeError: An ingestion job is currently running`
- **Cause**: Mutex `_INGESTION_LOCK` is active due to a concurrent or uncompleted run.
- **Resolution**: Wait for the background job to finish. If process crashed, restart backend service to release in-memory lock.

### 6.2 `ValueError: Staging point count error for core: expected 167, got ...`
- **Cause**: Document missing from `forms/` or record corrupted in `forms/CORE_KNOWLEDGE_RECORDS.jsonl`.
- **Resolution**: Validate file integrity via `python -c "from app.rag.ingestion.corpus_ingestion import CorpusValidator; print(CorpusValidator.validate_manifests_and_files())"`.

### 6.3 HTTP 503 on Administrative Endpoints
- **Cause**: Firebase Admin SDK uncredentialed and `settings.TEST_MODE_ALLOW_SIMULATED_TOKENS` is False.
- **Resolution**: Provide valid Firebase Admin credentials in `.env` or run in test mode.
