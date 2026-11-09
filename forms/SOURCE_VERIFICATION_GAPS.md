# CONVELINA — Statutory Evidence Gaps & Missing Category Ledger (Phase P3H.1.1)

**Audit Date:** November 8, 2026 (Reconciled in Phase P3H.1.1)  
**Objective:** Transparent inventory of missing official statutory documents across CONVELINA's six Tier 1 categories prior to any RAG knowledge base construction.

---

## 1. Category Readiness & Evidence Gap Matrix

| Category | Available Files in `forms/` | Statutory Readiness | Minimum Required Documents Before RAG Ingestion | Priority for User Ingestion |
| :--- | :---: | :---: | :--- | :---: |
| **01_AADHAAR** | **35 Files** (34 primary + 1 dup) | **READY** | None. Comprehensive coverage across Forms 1–8, Master SOP `DOC_043`, Exception SOP `DOC_039`, and Proof Matrix `DOC_034`. | **COMPLETED** |
| **02_PAN** | **6 Files** (+ 1 cross-cat) | **READY** | None for core clerical workflows. CSF Form `DOC_036`, Seeding Form `DOC_004`, and Allotment Form `DOC_029` present. | **COMPLETED** |
| **03_PASSPORT** | **0 Files** | **CRITICAL GAP** | 1. Passport Seva Project (PSP) Form 1 (Re-issue/Correction proforma).<br>2. Annexure E (Deed Poll Sworn Affidavit for name change).<br>3. Annexure D (Specimen declaration for minor applicants).<br>4. MEA Advisory on Split Names (Given Name / Surname separation). | **URGENT** |
| **04_CLASS_10** | **0 Files** | **CRITICAL GAP** | 1. CBSE Examination Bye-Laws Rule 69 (Correction in Date of Birth and Candidate Name).<br>2. State Board (SSLC) Correction Proforma & School Principal Forwarding Format. | **URGENT** |
| **05_CLASS_12** | **0 Files** | **CRITICAL GAP** | 1. CBSE Senior School Certificate Examination Bye-Laws Rule 69.1 (Name/Father/Mother Name Changes).<br>2. Proforma for Gazette Notification attestation for educational certificates. | **URGENT** |
| **06_EPFO_UAN** | **0 Files** | **CRITICAL GAP** | 1. Official EPFO Joint Declaration Form (3-column proforma signed by Member & Employer).<br>2. EPFO Circular / SOP on Member Profile Rejection (dated 2024 / 2026) specifying acceptable supporting proofs for major vs minor corrections. | **URGENT** |

---

## 2. Detailed Evidence Gaps by Category

### Category 3: Passport (`03_PASSPORT`) — Critical Gap (0 Documents)
- **Problem Statement:** Citizens frequently face passport re-issue rejection due to discrepancies between Aadhaar and Passport (e.g. single name in passport vs two names in Aadhaar, or expansion of initials).
- **Statutory Artifacts Needed:**
  1. *Passport Seva Form 1 (Application for Passport / Re-issue):* To verify field requirements and declarations.
  2. *Annexure E (Deed Poll Affidavit):* Required for any major name change or change of surname post-marriage in passport records.
  3. *Annexure D (Minor Declaration):* Required for minor name/parentage discrepancy corrections.
  4. *MEA Order on Split Names:* Official circular governing citizens traveling abroad with a single name in their passport.

### Categories 4 & 5: Educational Certificates (`04_CLASS_10` & `05_CLASS_12`) — Critical Gap (0 Documents)
- **Problem Statement:** Educational certificates are often treated as immutable baseline documents, yet clerical errors in candidate name, parents' names, or date of birth create lifelong cascading conflicts.
- **Statutory Artifacts Needed:**
  1. *CBSE Examination Bye-Laws Rule 69 (Amended):* Defines strict 5-year limitation periods and mandatory school record concordance rules.
  2. *State Board Correction Guidelines:* For state secondary and higher secondary education boards (e.g. Tamil Nadu DGE, Maharashtra State Board, UP Board).
  3. *Principal Attestation Proforma:* Official school letter format certifying that an error occurred in the admission register.

### Category 6: EPF / UAN Records (`06_EPFO_UAN`) — Critical Gap (0 Documents)
- **Problem Statement:** Name, date of birth, and father's name mismatches between EPFO UAN records and Aadhaar prevent automated PF settlement and pension transfer.
- **Statutory Artifacts Needed:**
  1. *EPFO Joint Declaration Form (3-Column Proforma):* The statutory joint application submitted by employee and employer containing "Correct Particulars", "Incorrect Particulars", and "Supporting Documents Enclosed".
  2. *EPFO Standard Operating Procedure on Member Profile Corrections (2024):* UIDAI-EPFO joint circular categorizing minor vs major profile updates and defining mandatory supporting documents (Class 10 marksheet, passport, PAN).

---

## 3. Recommended Actions Prior to Knowledge Base Ingestion

1. **Approve Aadhaar and PAN Corpora:** Proceed to Phase P3H.2 (Pre-Processing & Metadata Extraction) exclusively for the 19 verified `CURRENT_VERSION` and in-scope Aadhaar and PAN documents.
2. **Ingest Missing Categories in Next Phase:** Request user to provide authentic PDF files for Passport, Class 10/12, and EPFO before attempting cross-category RAG embedding.
