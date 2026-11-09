# CONVELINA — Knowledge Base Implementation & Architecture (P3H.5)

## 1. Executive Summary

This document describes the production implementation of the knowledge base retrieval infrastructure for CONVELINA, built on the 47-document reconciled and benchmarked official circular corpus.

The implementation strictly adheres to statutory evidence standards, fail-safe abstention, procedure-aware hierarchical chunking, dual Qdrant collection isolation, and BM25-first lexical retrieval with optional experimental dense embedding fusion.

---

## 2. Corpus Taxonomy & Classification

The knowledge corpus consists of 47 verified government circulars, forms, and procedural guidelines, strictly segregated into three architectural tiers:

```
                                  47-DOCUMENT OFFICIAL CORPUS
                                                │
         ┌──────────────────────────────────────┼──────────────────────────────────────┐
         ▼                                      ▼                                      ▼
8 Core Operational Documents           12 Reference Documents                 27 Quarantined Documents
  • convelina_core_operational           • convelina_reference_secondary        • Excluded from Vector Store
  • Primary procedural guidance          • Secondary authority / circulars      • Historical supersessions
  • 167 Chunks (Strategy 6)              • 28 Chunks (Strategy 6)               • Unverified third-party forms
  • DOC_001, DOC_004, DOC_013,           • DOC_005, DOC_006, DOC_021,           • Hard-blocked from citizen retrieval
    DOC_022, DOC_023, DOC_034,             DOC_024, DOC_025, DOC_026,           • Stored for administrative audit
    DOC_036, DOC_043                       DOC_027, DOC_028, DOC_029,
                                           DOC_031, DOC_033, DOC_047
```

### 2.1 Core Operational Collection (`convelina_core_operational`)
- **Document Count**: 8 official documents (`DOC_001`, `DOC_004`, `DOC_013`, `DOC_022`, `DOC_023`, `DOC_034`, `DOC_036`, `DOC_043`).
- **Total Chunks**: Exactly **167 chunks**, generated deterministically using Candidate Strategy 6 (Procedure-Aware Hierarchical Chunking).
- **Table Preservation**: Special segmentation for `DOC_034` (Aadhaar proof matrix), preserving tabular integrity across 6 semantic sub-tables rather than slicing across arbitrary byte offsets.
- **DOC_043 Invariant**: Exactly **21 chunks**, all strictly tagged with `source_status = "SOURCE_METADATA_CONFLICT"` and `human_review_required = True`.

### 2.2 Reference Secondary Collection (`convelina_reference_secondary`)
- **Document Count**: 12 secondary circulars (`DOC_005`, `DOC_006`, `DOC_021`, `DOC_024`, `DOC_025`, `DOC_026`, `DOC_027`, `DOC_028`, `DOC_029`, `DOC_031`, `DOC_033`, `DOC_047`).
- **Total Chunks**: Exactly **28 chunks**.
- **Scope**: Serves as secondary validation and historical context for administrative and specialist review.

### 2.3 Quarantined Documents (Hard-Blocked)
- **Document Count**: 27 documents.
- **Status**: Quarantined due to superseded authority, unofficial provenance, or unverified claims.
- **Enforcement**: Strictly excluded from Qdrant ingestion and BM25 index; retrieval queries matching these circulars trigger immediate statutory abstention.

---

## 3. Candidate Strategy 6: Procedure-Aware Hierarchical Chunking

### 3.1 Design Principles
1. **Preserve Procedural Wholeness**: Administrative rules, eligibility criteria, and step-by-step procedures are preserved within cohesive units.
2. **Table Integrity**: Tables are recognized and split along row/item boundaries, maintaining column headers in every generated chunk.
3. **Structured Context Prefix**: Every chunk is anchored with a deterministic metadata header:
   ```text
   [DOC: DOC_034 | TITLE: List of Acceptable Documents... | COHORT: ADULT | FUNC: POI_POA | STATUS: OFFICIALLY_PUBLISHED | ELIG: ELIGIBLE | SEC: Annexure A | PAGE: 15]
   ```
4. **Deterministic Point Identifiers**: Chunk IDs (e.g., `PROC_DOC_034_P15_UNIT01`) are transformed into reproducible UUIDv5 points using the DNS namespace:
   ```python
   point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))
   ```

### 3.2 Metadata Allowlist Contract
To guarantee compliance with the Aadhaar Act and zero PII leakage into vector databases, every chunk payload is strictly constrained to the following allowlist:

| Metadata Field | Type | Description |
| :--- | :--- | :--- |
| `chunk_id` | String | Unique deterministic identifier |
| `document_id` | String | Official document catalog ID (e.g., `DOC_034`) |
| `document_title` | String | Full title of the official circular |
| `document_category` | String | `aadhaar`, `pan`, `passport`, `epfo` |
| `corpus_classification` | String | `CORE_OPERATIONAL` or `REFERENCE_SECONDARY` |
| `source_sha256` | String | SHA-256 hash of the authoritative source document |
| `source_version` | String | Source circular version |
| `chunk_index` | Integer | Global chunk index |
| `page_number` | Integer | Authoritative page number in source PDF |
| `section_title` | String | Heading or section reference |
| `content_type` | String | `PROCEDURAL_GUIDANCE`, `DOCUMENT_TABLE`, or `PROCEDURAL_SCENARIO` |
| `source_status` | String | `OFFICIALLY_PUBLISHED` or `SOURCE_METADATA_CONFLICT` |
| `verification_status` | String | `VERIFIED` or `NEEDS_REVIEW` |
| `source_date` | String | Official date of circular issuance |
| `effective_date` | String | Date circular entered legal force |
| `ingestion_timestamp` | String | ISO 8601 UTC timestamp of ingestion run |
| `human_review_required` | Boolean | `True` for DOC_043 and exceptional procedures |
| `retrieval_eligibility` | String | `ELIGIBLE` or `CONDITIONAL` |
| `chunk_text` | String | Text content of the retrieval unit |

> [!CAUTION]
> **Citizen PII Absolute Prohibition**: The ingestion pipeline explicitly blocks and asserts the absence of any citizen-identifying keys (`aadhaar`, `pan`, `ocr_result`, `phone`, `citizen_id`, `user_id`, `address`).

---

## 4. Strict DOC_043 Statutory Restrictions

`DOC_043` (*UIDAI Exception Handling Process Guidelines*) contains an unresolved source metadata conflict regarding third-time exceptions and Regional Office escalation packets.

To prevent misrepresenting provisional administrative drafts as definitive law:
1. **Source Status**: Hard-coded to `SOURCE_METADATA_CONFLICT`.
2. **Review Flag**: `human_review_required` is permanently set to `True` for all 21 chunks.
3. **Statutory Limitation Notice**: All retrievals returning `DOC_043` automatically attach the mandatory disclaimer:
   > *"STATUTORY LIMITATION NOTICE: DOC_043 retains an unverified source metadata conflict. Claims regarding third-time exceptions and Regional Office escalation packets cannot be represented as definitive law."*
4. **Mandatory Abstention on Unverified Claims**: Queries requesting unverified third-time name updates, RO packet replays, or lifetime counter resets are intercepted by `check_statutory_abstention()` and return empty results with explicit logging.

---

## 5. Retrieval Architecture: BM25-First Lexical Search

The retrieval engine defaults to Okapi BM25 (`lexical_only` mode), with optional dense vector similarity (`hybrid_experimental` mode):

```
                                      CITIZEN QUERY
                                            │
                                            ▼
                          ┌───────────────────────────────────┐
                          │    check_statutory_abstention     │
                          │ (Intercepts illicit/superseded q) │
                          └─────────────────┬─────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
             Statutory Match                              Legitimate Procedural
          [ABSTAIN: Return []]                                     │
                                                                   ▼
                                                       ┌───────────────────────┐
                                                       │    BM25 Lexical       │
                                                       │   Search (k1=1.5,     │
                                                       │       b=0.75)         │
                                                       └───────────┬───────────┘
                                                                   │
                                             ┌─────────────────────┴─────────────────────┐
                                             ▼                                           ▼
                                    Score < Threshold (4.5)                     Score >= Threshold
                                    or Coverage < 0.34                          [Return Scored Hits]
                                    [ABSTAIN: Return []]                                 │
                                                                                         ▼
                                                                             Attach DOC_043 Disclaimer
                                                                             and Citations
```

### 5.1 Retrieval Parameters
- **Okapi BM25 Parameters**: $k_1 = 1.5$, $b = 0.75$.
- **Term Coverage Floor**: Requires candidate chunks to contain at least 34% (`min_coverage = 0.34`) of informative query terms, preventing large document tables from matching on single stray keywords.
- **Calibrated Score Floor**: `DEFAULT_BM25_SCORE_FLOOR = 4.5`. Queries failing to reach this relevance score trigger honest statutory abstention.

---

## 6. Staged Ingestion & Safe Rollback Architecture

To ensure zero downtime and prevent corrupt indices:
1. **Ingestion Mutex**: `_INGESTION_LOCK` prevents concurrent ingestion runs.
2. **Staging Collections**: New indices are written to isolated staging collections (`convelina_core_operational_<version>`).
3. **Automated Smoke Test**: A test query (`"Aadhaar name update procedure"`) is executed against staging collections before promotion.
4. **Atomic Activation**: On smoke test success, the global BM25 engine and active collection pointers are updated atomically.
5. **Instant Rollback**: `mgr.rollback(target_version)` restores previous collections with zero downtime.

---

## 7. Administrative APIs & Role-Based Access Control

| Endpoint | Method | Role | Purpose |
| :--- | :--- | :--- | :--- |
| `/api/v1/knowledge/corpus/status` | `GET` | Authenticated | View corpus counts, active version, health |
| `/api/v1/knowledge/corpus/manifest` | `GET` | Authenticated | View 47-document reconciled manifest |
| `/api/v1/knowledge/admin/ingest` | `POST` | **ADMIN** | Trigger staged ingestion pipeline |
| `/api/v1/knowledge/admin/ingest/status/{job_id}` | `GET` | **ADMIN** | Poll asynchronous ingestion status |
| `/api/v1/knowledge/admin/collections/health` | `GET` | **ADMIN** | Detailed Qdrant collection point counts and vector config |
| `/api/v1/knowledge/admin/collections/rollback` | `POST` | **ADMIN** | Revert active collections to previous version |
| `/api/v1/knowledge/retrieval/diagnostics` | `POST` | **ADMIN** | Test query scoring, normalized tokens, and abstention reasons |

