# CONVELINA — Citizen Document Repository Architecture & Specification

## 1. Executive Overview

The **Citizen Document Repository** in CONVELINA provides Indian citizens with a trusted, transparent, and structured interface to explore statutory documents, official government forms, standard operating procedures (SOPs), and proof matrices across six critical identity domains.

Rather than acting as an opaque, hallucinated chat interface, the repository grounds all guidance in **verified statutory artifacts**, preserving official provenance, providing exact citations, and maintaining strict distinction between official government forms and synthetic or application-generated materials.

---

## 2. Six Supported Identity Categories

The repository organizes and indexes official resources across six standardized identity categories:

| Identity Category ID | Citizen Display Name | Primary Statutory Authority | Typical Use Cases |
| :--- | :--- | :--- | :--- |
| `aadhaar` | Aadhaar Card | Unique Identification Authority of India (UIDAI) | Demographic update (name, DoB, gender, address), enrollment/update forms, exception handling |
| `pan` | PAN Card | Income Tax Department (ITD) / Protean (NSDL) / UTIITSL | Name correction, reprint, Form 49A, Change Request Form (CSF), father's name update |
| `passport` | Passport | Ministry of External Affairs (MEA) / CPV Division | Reissue due to name change, spelling correction, Annexure E, Tatkaal documentary proofs |
| `class_10` | Class 10 Certificate | Central Board of Secondary Education (CBSE) / State Boards | Birth date verification, name correction petition, gazette publication linkage, school record sync |
| `class_12` | Class 12 Certificate | Central Board of Secondary Education (CBSE) / State Boards | High school credential alignment, parentage correction, mark sheet correction procedure |
| `epf` | EPF/UAN Records | Employees' Provident Fund Organisation (EPFO) | Joint Declaration Form, member profile correction, Aadhaar-UAN seeding, establishment signoff |

---

## 3. Catalog Composition & Metadata Architecture

The catalog unifies resources from the reconciled official forms corpus (`forms/P3H4_1_CORPUS_RECONCILIATION.csv`, `forms/DOCUMENT_PROFILES/DOC_*.md`) and statutory application templates (`backend/app/rag/forms/catalog.py`).

### Total Resources Indexed: 52
- **Aadhaar**: 35 documents (UIDAI enrollment/update guidelines, gazette circulars, proof of identity lists)
- **PAN**: 7 documents (Form 49A guidelines, Change Request Form instructions, Rule 114 proof matrices)
- **Passport**: 3 documents (Passport reissue manual, Form 2 / Annexure E deed poll affidavit, document advisor)
- **Class 10**: 2 documents (CBSE examination byelaws Rule 69.1 on name/DoB changes, correction petition form)
- **Class 12**: 2 documents (CBSE secondary certificate correction form, notification on surname amendments)
- **EPF/UAN**: 2 documents (EPFO Joint Declaration standard form, Circular on member profile corrections)

### Metadata Schema (`RepositoryResourceItem` & `RepositoryResourceDetail`)

Each resource maintains a rigorous, typed schema validated via Pydantic v2:

```python
class RepositoryResourceDetail(BaseModel):
    id: str
    resource_id: str                          # e.g., "DOC_036" or "form_pan_csf"
    title: str                                # Exact official document title
    issuing_authority: str                    # e.g., "Income Tax Department"
    document_category: str                    # aadhaar | pan | passport | class_10 | class_12 | epf
    document_type: str                        # application_form | proof_matrix | correction_procedure | etc.
    provenance: str                           # OFFICIAL_ORIGINAL | OFFICIAL_COPY | GOVERNMENT_REFERENCE | etc.
    verification_status: str                  # VERIFIED | NEEDS_REVIEW | OUTDATED | RETIRED | SOURCE_METADATA_CONFLICT
    description: str                          # Plain-language overview
    purpose: str                              # Verified explanation of statutory use
    who_should_use: str                       # Targeted citizen cohort
    source_date: Optional[str]                # Publication / notification date
    source_verification_status: str           # Internal source validation state
    original_file_name: Optional[str]         # Source filename
    original_file_format: Optional[str]       # pdf | image | html
    original_file_sha256: Optional[str]       # SHA-256 cryptographic checksum
    is_official_government_form: bool         # Strictly False for ReportLab/synthetic samples
    is_synthetic_sample: bool                 # True for local dev mock forms
    synthetic_sample_disclaimer: Optional[str]# Prominent disclaimer text if synthetic
    human_review_required: bool               # Mandated for DOC_043 or conflicting sources
    source_conflict_flag: bool                # Indicates metadata inconsistency
    statutory_limitation_notice: Optional[str]# Legal warning attached to restricted items
    related_procedures: List[Dict[str, Any]]  # Linked correction procedures
    checklists: List[ChecklistItem]           # Reusable supporting document checklist
    citations: List[Dict[str, Any]]           # Verified page/section legal citations
```

---

## 4. Frontend UI Specification

### 4.1. Repository Catalog View (`/app/forms`)
- **Category Filter Tabs**: Horizontal responsive bar with all 6 categories + "All Documents", displaying resource counts per category.
- **Search Engine**: Instant text search supporting document IDs (`DOC_036`), keywords, issuing authorities, and procedures.
- **Secondary Filters**: Document Type dropdown (`application_form`, `proof_matrix`, `correction_procedure`, `reference_circular`) and Provenance dropdown (`Official Original`, `Government Reference`, `Historical Reference`, `Synthetic Sample`).
- **Personalized Discrepancy Banner**: If an authenticated citizen has confirmed discrepancies detected by Module 5 (`/api/v1/conflicts`), a prominent alert guides them directly to the relevant document with the required disclaimer:
  > `AUTOMATED COMPARISON RESULT — NOT OFFICIAL GOVERNMENT VERIFICATION.`
- **Resource Cards**:
  - Category tag and document type badge.
  - Provenance badge with distinct visual tokens (`OFFICIAL_ORIGINAL` = green, `GOVERNMENT_REFERENCE` = sky, `HISTORICAL_REFERENCE` = amber, `SYNTHETIC_DEVELOPMENT_SAMPLE` = violet/warning).
  - Verification state badge (`VERIFIED`, `NEEDS_REVIEW`, `SOURCE_METADATA_CONFLICT`).
  - Clear issuing authority and publication date.
  - Action buttons: "View Details & Checklist", "Preview", "Download PDF".

### 4.2. Dedicated Document Detail View (`/app/forms/[formId]`)
Divided into seven structured sections:
1. **Document Overview**: Complete metadata header, issuing authority, cryptographic SHA-256 hash, and provenance tags.
2. **What is this document used for?**: Plain-language statutory purpose directly synthesized from verified sources.
3. **Who should use it?**: Specific citizen cohorts eligible to file or reference the document.
4. **Related Correction Procedures**: Direct pathway to online/offline correction steps (e.g., Aadhaar Update Portal vs UIDAI Enrollment Center).
5. **Required Supporting Documents Checklist**: Interactive checklist with status indicators (`VERIFIED_MANDATORY`, `VERIFIED_CONDITIONAL`, `RECOMMENDED`, `HUMAN_REVIEW_REQUIRED`) and personal preparation checkboxes.
6. **Original Document Asset**: Safe preview modal and direct verified download link.
7. **Source Citations & Statutory Limitations**: Exact section references, legal quotes, and explicit statutory limitation notices (including `DOC_043` governance).

---

## 5. Security & Path Traversal Guardrails

The repository enforces strict security protocols:
- **No Path Traversal**: Endpoints `/api/v1/repository/resources/{id}/download` and `/preview` use `CitizenRepositoryService.resolve_file_path()` which strips null bytes (`\x00`), checks relative path escapes (`../`), resolves real absolute paths, and strictly validates that the target file resides within the approved white-listed directories (`forms/` or `forms_corpus/`).
- **No Private Citizen Data**: The repository catalog is strictly public domain knowledge. Private citizen identity records, OCR images, and user documents are never exposed through repository endpoints.
- **Two Application Roles**: Only `USER` and `ADMIN` exist in the system. Citizens cannot alter document verification states or edit statutory metadata.
