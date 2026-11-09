# CONVELINA — Document Duplicate & Version Lineage Report (Phase P3H.0)

**Date of Audit:** November 8, 2026  
**Auditor:** Antigravity Autonomous Pair Programmer  
**Policy:** Never delete duplicate files automatically. Preserve original files, calculate SHA-256 hashes, and document lineage relationships.

---

## 1. Exact Byte-Identical Duplicates Identified

Two pairs of byte-identical duplicate files were detected via SHA-256 collision analysis:

### Group 1: Master Acceptable Documents Matrix
- **SHA-256 Hash:** `07e1d5ff787474495c65a04fe2e9bb7874ea595d734e0aebaa022fffc18610eb`
- **File Size:** 2,183,015 bytes (22 pages)
- **Primary Canonical File:** `DOC_034`: `01_AADHAAR/Checklists/List of Acceptable Document for Aadhaar Enrolment and Update  English.pdf`
- **Duplicate File:** `DOC_035`: `10_DUPLICATES_REVIEW/List_of_Supporting_Document_for_Aadhaar_Enrolment_and_Update.pdf`
- **Relationship:** Exact byte-for-byte duplicate. Both represent the official 22-page UIDAI document proof matrix.
- **Action Taken:** `DOC_035` moved to `10_DUPLICATES_REVIEW/` and preserved. `DOC_034` retained as the canonical reference checklist.

### Group 2: Authentication Operator Training SOP
- **SHA-256 Hash:** `961f7b55f524317f2fa8ef153ce11516e9196fe6cf4ff8281358c27a20c571ad`
- **File Size:** 2,135,718 bytes (3 pages)
- **Primary Canonical File:** `DOC_041`: `01_AADHAAR/SOPs/SOP for Training, Testing and Certification of Authentication Operators.pdf`
- **Duplicate File:** `DOC_040`: `10_DUPLICATES_REVIEW/SOP for Training, Testing and Certification of Authentication Operators (1).pdf`
- **Relationship:** Exact byte-for-byte duplicate caused by a duplicate browser download `(1)`.
- **Action Taken:** `DOC_040` moved to `10_DUPLICATES_REVIEW/` and preserved. `DOC_041` retained in `01_AADHAAR/SOPs/`.

---

## 2. Probable Semantic Duplicates & Form Variants

In addition to byte-identical duplicates, content analysis revealed several semantic variants and form packages:

1. **Aadhaar Adult Enrolment Form Package vs Standalone:**
   - `DOC_001`: `Aadhaar Enrolment And Update Forms  English.pdf` (Multi-page package containing Form 1)
   - `DOC_024`: `For (a) Resident Indian, or (b) Non-Resident Indian having Proof of Address in India (aged 18 years and above)  English.pdf` (Standalone 2-page Form 1)
   - *Lineage:* Both contain identical Form 1 fields for adult residents. `DOC_001` was distributed as a combined package, while `DOC_024` was distributed as a standalone printable proforma.

2. **UIDAI Name Update SOPs:**
   - `DOC_039`: `SOP dated 28-10-2021 - Name & Gender update request under exception handling process (Circular dated 03-11-2021).pdf`
   - `DOC_043`: `Standard operating Procedure (SOP) to be followed for updating name in Aadhaar.pdf`
   - *Lineage:* `DOC_043` is the baseline operational SOP for clerical and major name updates (spelling, sequence change, proof matrix). `DOC_039` is the specialized escalation SOP when a resident has exhausted their lifetime limit of 2 updates and requires Gazette notification exception processing. Both are distinct, valid, and essential!

3. **Income Tax PAN Application Series (Rule 158):**
   - `DOC_029` (Form 93): Indian Individual Allotment
   - `DOC_030` (Form 94): Indian Entity Allotment
   - `DOC_031` (Form 95): Foreign Individual Allotment
   - `DOC_032` (Form 96): Foreign Entity Allotment
   - `DOC_036` (PAN CR Individual): Individual Correction / Changes
   - `DOC_037` (PAN CR Non-Individual): Entity Correction / Changes
   - *Lineage:* These constitute the complete formal suite of Income Tax Department PAN forms under updated Rule 158. They are not duplicates; each serves a mutually exclusive taxpayer classification.

---

## 3. Preservation & Retention Recommendation
- **Zero Deletion Policy:** Maintain all files in `10_DUPLICATES_REVIEW` to preserve historical chain of custody.
- **RAG Routing Recommendation:** When knowledge ingestion is approved in a future phase, only canonical files (`DOC_034` and `DOC_041`) should be vectorized, avoiding duplicated chunk embeddings in Qdrant.
