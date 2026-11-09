# CONVELINA — PAN Source Document Verification Report (Phase P3H.1.1 Reconciled)

**Audited Domain:** Income Tax Department (Central Board of Direct Taxes - CBDT) / Permanent Account Number (PAN)  
**Audit Date:** November 8, 2026 (Reconciled in Phase P3H.1.1)  
**Total Documents Audited:** 6 Documents in `forms/02_PAN/` (plus cross-category `DOC_004`)  
**Status:** **RECONCILED & PURPOSE-SEPARATED**

---

## 1. Executive Summary

This report provides the authoritative reconciliation of all Permanent Account Number (PAN) documents in CONVELINA. 

In Phase P3H.1.1, the PAN corpus was rigorously separated into its distinct statutory purposes:
1. **New PAN Allotment** under Rule 158 of Income Tax Rules, 1962 (Forms 93–96).
2. **PAN Data Correction & Changes** (CSF Form for Individuals).
3. **PAN-Aadhaar Linking / Seeding** under Section 139AA of Income Tax Act (`DOC_004`).

### Purpose Separation Matrix

| Document ID | Form Name | Governing Rule / Section | Purpose Classification | Target Audience | CONVELINA Applicability | Canonical Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DOC_029** | Form No. 93 | Rule 158, Income Tax Rules 1962 | **NEW_PAN_ALLOTMENT** | Indian Citizen Individuals | Baseline naming & formatting rules; NOT a correction form | **CURRENT_VERSION** |
| **DOC_030** | Form No. 94 | Rule 158, Income Tax Rules 1962 | **NEW_PAN_ALLOTMENT** | Indian Companies, LLPs, Trusts | Out of Scope (corporate entities) | **OUT_OF_SCOPE** |
| **DOC_031** | Form No. 95 | Rule 158, Income Tax Rules 1962 | **NEW_PAN_ALLOTMENT** | Non-Citizen Individuals | Foreign individual allotment rules | **CURRENT_VERSION** |
| **DOC_032** | Form No. 96 | Rule 158, Income Tax Rules 1962 | **NEW_PAN_ALLOTMENT** | Foreign Corporate Entities | Out of Scope (foreign corporate entities) | **OUT_OF_SCOPE** |
| **DOC_036** | PAN CR Individual | Section 139A, Income Tax Act 1961 | **PAN_CORRECTION** | Individual Taxpayers | **CORE OPERATIONAL ASSET** for PAN clerical corrections | **CURRENT_VERSION** |
| **DOC_037** | PAN CR Non-Individual | Section 139A, Income Tax Act 1961 | **PAN_CORRECTION** | Companies, LLPs, Trusts | Out of Scope (non-individual entities) | **OUT_OF_SCOPE** |
| **DOC_004** | Seeding Request Form | Section 139AA, Income Tax Act 1961 | **PAN_AADHAAR_LINKING** | Individual Taxpayers | **CORE CROSS-CATEGORY ASSET** for Aadhaar-PAN linkage | **CURRENT_VERSION** |

---

## 2. In-Depth Operational Analysis of PAN Correction Assets

### A. The Core PAN Correction Instrument: `DOC_036` (`PAN CR individual_03Nov.pdf`)
- **Authority:** Income Tax Department (CBDT) / NSDL Database Management Ltd (Protean) / UTIITSL.
- **Reference:** Request for Changes or Correction in PAN Data [For an Individual] (CSF Form).
- **Physical Details:** 4 pages. SHA-256: `e08c5d7c1f3962fb5291b93f1d8c114f6b216be02e9cf30c144577881b22e1d7`.
- **Statutory Workflow:**
  - Used when an individual already holds an allotted PAN and requires correction in Name, Father's Name, Date of Birth, Gender, Address, Photo, or Signature.
  - Page 1 Instructions: Requires quoting existing 10-digit alphanumeric PAN at the top. The tick boxes on the left margin must be selected specifically for fields requiring correction.
  - Page 3 Guidelines (Clause c): Aadhaar number is mandatory for all applicants except exempt categories; Aadhaar demographic matching is enforced.
  - Page 3 Guidelines (Clause b): Copy of existing PAN card must be enclosed; in case of loss, a copy of police FIR is mandatory.
  - Page 4 Guidelines: Specifies formatting for Date of Birth (`DDMMYYYY`), Father's Name (mandatory even for married female applicants), and Address for communication.

### B. PAN-Aadhaar Seeding Instrument: `DOC_004` (`Aadhaar_Seeding_Request_Form.pdf`)
- **Authority:** Income Tax Department / Protean / UTIITSL.
- **Reference:** Seeding Request Form under Section 139AA of Income Tax Act.
- **Physical Details:** 1 page. SHA-256: `39c6da3c7dbeec1c9b2751478bda5267b98f097edf909c0255981c4fd20f41cc`.
- **Statutory Workflow:**
  - Used when biometric or demographic linkage fails via the automated e-filing portal due to minor discrepancies between PAN card and Aadhaar card (e.g. initials vs expanded name, minor spelling difference).
  - Contains formal sworn declaration that the Aadhaar belongs to the PAN holder and has not been linked to any other PAN.

### C. The Allotment Forms: `DOC_029` (Form 93) & `DOC_031` (Form 95)
- **Authority:** CBDT under Rule 158 of Income Tax Rules, 1962.
- **Physical Details:** 5 pages each.
- **Audit Clarification:**
  - Form 93 replaced legacy Form 49A for Indian individuals. Form 95 replaced Form 49AA for foreign individuals.
  - **Critical Rule:** An allotment form cannot be used to execute a correction. Submitting Form 93 when already possessing a PAN constitutes a violation of Section 272B of the Income Tax Act (possessing more than one PAN incurs a statutory penalty of Rs. 10,000).
  - Its value for CONVELINA lies solely in establishing the statutory personal information structure: `First Name`, `Middle Name`, `Last Name`, `Name as per Aadhaar`, and Father's/Mother's name conventions.

---

## 3. Pre-Processing Eligibility Roster for PAN

The following PAN documents are certified as reconciled and eligible for future human approval:
1. **`DOC_036` (PAN CR Individual - CSF Form):** Canonical correction proforma.
2. **`DOC_029` (Form No. 93 [Rule 158]):** Allotment identity structure reference.
3. **`DOC_031` (Form No. 95 [Rule 158]):** Non-citizen allotment structure reference.
4. **`DOC_004` (Aadhaar Seeding Request Form):** Cross-category linkage instrument.
