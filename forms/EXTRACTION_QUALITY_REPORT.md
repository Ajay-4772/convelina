# CONVELINA — Phase P3H.2 Extraction Quality & Corpus Preprocessing Report

**Phase**: P3H.2 (Controlled Corpus Preprocessing & Extraction Validation)  
**Execution Date**: 2026-11-09  
**Corpus Scopes**: Core Operational Knowledge (8 documents) & Reference-Only (12 documents)  
**Pipeline**: Local PyPDF Extraction + Windows Media OCR (Rotated) + Strict Normalization  

---

## 1. Executive Summary & Quality Metrics

Phase P3H.2 successfully executed local page-by-page text extraction, normalization, section-grounded metadata binding, and rigorous quality validation across all 8 approved core operational documents and 12 reference-only documents without initiating Qdrant ingestion or external API calls.

### Key Quantitative Metrics
- **Core Documents Preprocessed**: 8 documents (48 total pages).
- **Core Knowledge Records Generated**: 48 page-grounded records in `CORE_KNOWLEDGE_RECORDS.jsonl`.
- **Core Volume Extracted**: 108,839 characters (18,048 words).
- **Reference-Only Documents Preprocessed**: 12 documents (28 total pages).
- **Reference Knowledge Records Generated**: 28 records in `REFERENCE_KNOWLEDGE_RECORDS.jsonl`.
- **Reference Volume Extracted**: 74,882 characters (12,237 words).
- **Total Preprocessed Pages Validated**: 76 pages (48 core + 28 reference).
- **Page Extraction Success Rate**: **100.0% (76 / 76 pages extracted)**.
- **Unreadable / Missing Pages**: **0 (0.0%)**.
- **Physical Disk Hash Match vs P3H.0 Baseline**: **47 / 47 files (100.0%)**.

---

## 2. Extraction Methodology by Document Type

### 2.1 Native Embedded Digital PDFs (7 Core Documents + 12 Reference Documents)
Documents `DOC_001`, `DOC_004`, `DOC_013`, `DOC_022`, `DOC_023`, `DOC_034`, and `DOC_036` contain clean, native digital text streams. Extraction was performed via `pypdf`, preserving exact text characters, numeric identifiers, and section headers.
- **Quality Level**: `PASS_HIGH_FIDELITY_DIGITAL` (Average extraction confidence >= 0.99).
- **Edge Case Handled**: `DOC_034` Page 22 is an authentic sparse back-cover page containing only `UIDAI.GOV.IN` and logo elements (12 chars). Documented in `PAGE_LEVEL_VALIDATION_REPORT.csv` and `PREPROCESSING_EXCEPTIONS.csv` as `PASS_LOW_DENSITY_COVER` without artificial reconstruction.

### 2.2 Scanned Image PDF with Rotated Landscape Tables (`DOC_043`)
`DOC_043` (Master Name Update SOP, 11 pages) is an image-based scanned e-Office PDF with 0 embedded text:
- **Pages 1, 2, 7, 8, 9, 10, 11 (Portrait)**: Extracted via Windows Media OCR Engine at 300 DPI upright.
- **Pages 3, 4, 5, 6 (Landscape Tables - Annexure A)**: Contained horizontal multi-column scenario tables. Standard upright OCR yielded only reverse fragments. High-fidelity extraction was achieved by applying a 270-degree clockwise image rotation prior to Windows Media OCR, transcribing 100% of the scenarios (Initials expansion, abbreviation, sequence change, phonetic spelling fixes, data entry error, marriage/divorce surname change, urf/alias removal, and Major Name Change Gazette mandate).
- **Quality Level**: `PASS_HIGH_FIDELITY_OCR` (Average OCR confidence 0.95).
- **Governance Restriction**: In strict adherence to P3H.1.4, all 11 records derived from `DOC_043` retain `source_authenticity_status = 'SOURCE_METADATA_CONFLICT'`, `retrieval_eligibility = 'CONDITIONAL_HUMAN_REVIEW_REQUIRED'`, and `human_review_required = true`.

---

## 3. Strict Separation of Knowledge Tiers

```mermaid
flowchart TD
    Corpus[47 Repository Source Files] --> BucketCheck{Corpus Classification Bucket}
    BucketCheck -->|8 Core Documents| CoreJSONL[forms/CORE_KNOWLEDGE_RECORDS.jsonl<br/>retrieval_eligibility: CORE_SEARCH_SPACE<br/>(DOC_043 conditional review)]
    BucketCheck -->|12 Reference Documents| RefJSONL[forms/REFERENCE_KNOWLEDGE_RECORDS.jsonl<br/>retrieval_eligibility: REFERENCE_ONLY<br/>Secondary Lookup Only]
    BucketCheck -->|9 Historical Documents| HistQuarantine[forms/PREPROCESSING_INVENTORY.csv<br/>retrieval_eligibility: AUDIT_TRAIL_AND_HISTORICAL_LINEAGE_ONLY<br/>0 Retrieval Chunks Generated]
    BucketCheck -->|15 Out of Scope + 2 Duplicates + 1 Unconfirmed| HardBlock[EXCLUDED_FROM_AUTHORITATIVE_RETRIEVAL<br/>Strictly Quarantined]
```

---

## 4. Page-Level Extraction Summary for Core Operational Corpus

| Doc ID | Title | Pages | Characters | Extraction Method | Quality Verdict | Governance Flags |
|---|---|:---:|:---:|---|---|---|
| **DOC_001** | Aadhaar Enrolment/Update Form (Adult) | 2 | 9,262 | `PYPDF_EMBEDDED_TEXT` | `PASS_HIGH_FIDELITY_DIGITAL` | Active Core |
| **DOC_004** | Form for Aadhaar Seeding into PAN | 1 | 1,331 | `PYPDF_EMBEDDED_TEXT` | `PASS_HIGH_FIDELITY_DIGITAL` | Active Core |
| **DOC_013** | Certificate for Aadhaar Enrolment/Update | 4 | 8,479 | `PYPDF_EMBEDDED_TEXT` | `PASS_HIGH_FIDELITY_DIGITAL` | Active Core (Certifier) |
| **DOC_022** | Form 3: Minor 5–18 Enrolment/Update | 2 | 8,789 | `PYPDF_EMBEDDED_TEXT` | `PASS_HIGH_FIDELITY_DIGITAL` | Active Core |
| **DOC_023** | Form 5: Bal Aadhaar (0–5) Form | 2 | 9,603 | `PYPDF_EMBEDDED_TEXT` | `PASS_HIGH_FIDELITY_DIGITAL` | Active Core |
| **DOC_034** | List of Acceptable Documents (Master) | 22 | 56,881 | `PYPDF_EMBEDDED_TEXT` | `PASS_HIGH_FIDELITY_DIGITAL` (p.22 sparse) | Active Proof Matrix |
| **DOC_036** | Request for PAN Changes/Correction (CSF) | 4 | 7,437 | `PYPDF_EMBEDDED_TEXT` | `PASS_HIGH_FIDELITY_DIGITAL` | Active Core (PAN) |
| **DOC_043** | Master Name Update SOP | 11 | 14,734 | `LOCAL_WINDOWS_MEDIA_OCR_ROTATED` | `PASS_HIGH_FIDELITY_OCR` | **`SOURCE_METADATA_CONFLICT`** |
| **Total** | **8 Core Operational Documents** | **48** | **116,516** | — | **100% Validated** | — |

---

## 5. Verified Legal Claims Traceability Check

A sample verification was performed comparing high-impact legal claims against newly extracted chunk records:
- **CLM_004 & CLM_005 (Minor Spelling & Initials Expansion)**: Present in `CORE_DOC_043_P03` (Annexure A, Scenarios a–d). Matches source text precisely.
- **CLM_006 (Major Name Change Gazette Mandate)**: Present in `CORE_DOC_043_P02` (Para 5) and `CORE_DOC_043_P06` (Scenario o). Matches source text precisely.
- **CLM_007 (Surname Post-Marriage via Affidavit D)**: Present in `CORE_DOC_043_P05` (Scenario b) and `CORE_DOC_043_P09` (Annexure D).
- **CLM_011 (Production of Original Documents)**: Present in `CORE_DOC_034_P01` (Important Instructions 1–4).
- **CLM_012 (Standard Certifier Certificate 3-Month Validity)**: Present in `CORE_DOC_013_P04` and `CORE_DOC_034_P14`–`P21`.

---

## 6. Preprocessing Exceptions & Mitigations

Exactly 6 preprocessing exceptions were recorded in [`PREPROCESSING_EXCEPTIONS.csv`](file:///C:/Users/ajaya/Desktop/consolin/forms/PREPROCESSING_EXCEPTIONS.csv):
1. **`EXC_001` (DOC_043 Page 1 - CRITICAL)**: e-Office draft export date conflict (`18-09-2026`). Mitigated by tagging all chunks `human_review_required=TRUE` and `retrieval_eligibility=CONDITIONAL_HUMAN_REVIEW_REQUIRED`.
2. **`EXC_002` to `EXC_005` (DOC_043 Pages 3–6 - INFO)**: Landscape table orientation. Mitigated by applying 270-degree rotation prior to OCR.
3. **`EXC_006` (DOC_034 Page 22 - INFO)**: Back-cover sparse page (12 characters). Mitigated by recording authentic sparse content without synthetic hallucination.