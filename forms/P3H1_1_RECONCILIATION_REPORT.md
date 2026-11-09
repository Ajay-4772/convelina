# CONVELINA — Phase P3H.1.1: Independent Audit Reconciliation & Provenance Evidence Correction Report

**Audit Phase:** P3H.1.1 (Audit Reconciliation & Provenance Evidence Correction)  
**Corpus Audited:** 47 Files (41 Audited Aadhaar & PAN Documents + 6 Repository Files)  
**Audit Status:** **RECONCILED & VERIFIED**  
**Integrity Guarantee:** 100% SHA-256 Immutability Preserved; Zero External LLM/Gemini Calls; Zero Database/App Source Modifications.

---

## 1. Executive Summary & Audit Purpose

Phase P3H.1.1 was authorized to correct and reconcile the Phase P3H.1 Aadhaar and PAN source verification findings, eliminate provenance ambiguities, resolve misclassifications, and ground all high-impact legal claims in exact page-level statutory citations before any corpus pre-processing or RAG ingestion is considered.

### Key Audit Outcomes
1. **Canonical 1:1 Identity Resolution:** Resolved all 41 audited document identities across 47 repository files. Every document ID (`DOC_001` through `DOC_047`) maps to exactly one physical original file with verified SHA-256 cryptographic integrity.
2. **Rectification of Misclassifications:**
   - **`DOC_014`:** Corrected false claim of supersession by Form 1. Verified as an Authentication Division circular (`K-11020/45/2012-UIDAI(Auth)`) regarding airline/airport requesting entities. Correctly classified as **`OUT_OF_SCOPE`**.
   - **`DOC_035` & `DOC_040`:** Corrected conflation of physical file duplicates with statutory supersession. Correctly classified as **`EXACT_DUPLICATE`** of `DOC_034` and `DOC_041` respectively.
   - **`DOC_011`:** Verified as authentic historical circular (`4(4)/57/315/2016-E&U-I`) amending Schedule II in 2016, subsumed by the comprehensive 22-page Proof Matrix `DOC_034`. Correctly classified as **`HISTORICAL_VERSION`**.
3. **Master SOP Authenticity & Extraction:** Corrected hallucinated 2022 citations for `DOC_043`. Verified authentic circular `F.no. HQ-16024/4/2020-EU-I-HQ` (e-Office `1/58751/2026`) dated `18-09-2026` signed by `Nikhil Sinha, Director`. Completed 100% extraction across all 11 pages, transcribing the complete Minor Name Change scenarios, Major Name Change Gazette rules, and statutory Affidavits B through F.
4. **Statutory Grounding of High-Impact Claims:** Mapped 16 high-impact claims to exact PDF page numbers, clauses, and quotations across `DOC_043`, `DOC_039`, `DOC_034`, and `DOC_013`.
5. **PAN Purpose Separation:** Partitioned PAN documents into **New PAN Allotment** (Forms 93–96 under Rule 158), **PAN Correction** (`DOC_036` CSF Form), and **PAN-Aadhaar Linking** (`DOC_004` Seeding Form).
6. **Multi-Dimensional Taxonomy:** Replaced single-label tags with separate dimensions for Authenticity, Currency, and Relevance.

---

## 2. Targeted In-Depth Document Investigations

### A. Investigation of `DOC_014`
- **Original Filename:** `Circular_(Legal)_Regarding Aadhaar (Authentication) Regulations, 2016, First Amendment in Schedule A.pdf`
- **SHA-256:** `81c835e7e82be5bd039309cc031f44a8e62c01e55603653ec0aa1894de15a399`
- **Issuing Authority:** UIDAI (Authentication Division)
- **Official Reference:** `File No: K-11020/45/2012-UIDAI(Auth)` dated `03-04-2017`
- **Audit Findings:** The previous P3H.1 audit erroneously claimed that `DOC_014` was "SUPERSEDED: replaced by Form 1". Full OCR extraction of `DOC_014` established that it is an administrative circular approving an amendment to Schedule A of the Aadhaar (Authentication) Regulations, 2016, to appoint airport operators and scheduled airlines as requesting entities under DGCA/AAI. It has **no relation whatsoever to Form 1 or citizen demographic updates**.
- **Reconciliation Verdict:** **`OUT_OF_SCOPE`** (Authentic official circular, but outside the functional scope of CONVELINA's citizen identity correction platform).

### B. Investigation of `DOC_034` vs `DOC_035`
- **`DOC_034`:** `List of Acceptable Document for Aadhaar Enrolment and Update  English.pdf` (organized under `forms/01_AADHAAR/Checklists/`)
- **`DOC_035`:** `List_of_Supporting_Document_for_Aadhaar_Enrolment_and_Update.pdf` (quarantined under `forms/10_DUPLICATES_REVIEW/`)
- **SHA-256 (Both):** `07e1d5ff18a56ac8e5654573cafa6cec351793bfe754be2939c39fa971d3afd8`
- **Audit Findings:** Both files are 100% byte-for-byte identical (2,183,015 bytes). The previous audit mislabeled `DOC_035` as "SUPERSEDED". A duplicate file in a storage repository is not legally superseded; it is an identical artifact.
- **Reconciliation Verdict:**
  - `DOC_034` is retained as the **`CURRENT_VERSION`** canonical master proof matrix.
  - `DOC_035` is classified as **`EXACT_DUPLICATE`** of `DOC_034`.

### C. Investigation of `DOC_040` vs `DOC_041`
- **`DOC_040`:** `SOP for Training, Testing and Certification of Authentication Operators (1).pdf` (quarantined under `forms/10_DUPLICATES_REVIEW/`)
- **`DOC_041`:** `SOP for Training, Testing and Certification of Authentication Operators.pdf` (organized under `forms/01_AADHAAR/SOPs/`)
- **SHA-256 (Both):** `961f7b55761c3b9bfb53e43177cab5fde787c1c5e0744aa41918a602108c8b15`
- **Audit Findings:** Both files are 100% byte-for-byte identical (2,135,718 bytes). Both documents govern the training and testing of authentication operators (minimum 10th/12th pass qualifications for NSEIT testing).
- **Reconciliation Verdict:**
  - `DOC_041` is classified as **`OUT_OF_SCOPE`** (operator accreditation).
  - `DOC_040` is classified as **`EXACT_DUPLICATE`** of `DOC_041`.

### D. Investigation of `DOC_011`
- **Original Filename:** `Circular_(E&U-I)_Regarding Expansion Modification in the list of supporting documents accepted as Proof of Address (PoA) and Date of Birth (DoB).pdf`
- **SHA-256:** `f0b0115e57fdc904f468fe1bcd44f28621c244d1b08bd42d934d637ea8d55d02`
- **Issuing Authority:** UIDAI (Enrolment & Update-I Division)
- **Official Reference:** `No. 4(4)/57/315/2016-E&U-I` dated `09-11-2016`
- **Audit Findings:** Issued under Regulation 10(2) of Aadhaar Regulations 2016, modifying Schedule II by adding PAN card (#5 for DOB) and Marriage Certificate containing address (#35 for POA). While historically authentic and statutory, its provisions have been subsumed by the comprehensive 22-page master proof matrix (`DOC_034`).
- **Reconciliation Verdict:** **`HISTORICAL_VERSION`** (Authentic official circular; retained for legal evolution and precedent).

### E. Investigation of `DOC_043` vs `DOC_039`
- **`DOC_043`:** `Standard operating Procedure (SOP) to be followed for updating name in Aadhaar.pdf` (11 pages)
  - Reference: `F.no. HQ-16024/4/2020-EU-I-HQ`, e-Office `1/58751/2026`, dated `18-09-2026`, signed by `Nikhil Sinha, Director`.
  - Scope: Master Name Update SOP. Defines Minor Name Changes (initials, sequence, spelling), Major Name Changes (Gazette required), post-marriage surname changes, data entry error corrections, and alias removals. Contains official Affidavits B, C, D, E, F.
  - Page 1 Clause 1 explicitly states: *"In supersession of the Name update process as described in the Standard Operating Procedure (SOP) of Name & Gender Update Request under Exception Handling Process issued vide F.no. HQ 16022/2/2020-EU-I-HQ-Part(1) on 28.10.2021 [DOC_039]..."*
- **`DOC_039`:** `SOP dated 28-10-2021 - Name & Gender update request under exception handling process` (7 pages)
  - Reference: `F.No. HQ-16022/2/2020-EU-I-HQ-Part(1)` dated `28-10-2021` / Circular dated `03-11-2021`, signed by `Prabhakaran C R, Deputy Director (E&U-I)`.
  - Scope: Governs update requests exceeding the 2-update lifetime limit (3rd or greater update), Regional Office (RO) exception handling escalation via 1947/email, Tech Centre packet replay, and Gender update medical certification rules.
- **Reconciliation Verdict:**
  - `DOC_043` is **`CURRENT_VERSION`** (The active operational authority for standard name corrections).
  - `DOC_039` is **`HISTORICAL_VERSION`** (Partially superseded regarding standard name scenarios by `DOC_043`, but retaining active procedural validity for 3rd+ update RO exception handling and Gender updates).

---

## 3. Canonical Document Identity & Classification Table

The table below reconciles all 47 repository files. Every document ID maps to exactly one original file:

| Document ID | Original Filename | Current Organized Path | Issuing Authority | Document Type | Authenticity | Currency | Relevance | Canonical Classification | PAN Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DOC_001** | Aadhaar Enrolment And Update Forms English.pdf | `forms/01_AADHAAR/Forms/` | UIDAI | Form 1 (Adults 18+) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_002** | Aadhaar Forms, Usage, and Benefits.pdf | `forms/08_UNCLASSIFIED/` | Private (Azam Khan) | Slide Deck | AUTHENTICITY_UNCONFIRMED | HISTORICAL | OUT_OF_SCOPE | **AUTHENTICITY_UNCONFIRMED** | NOT_APPLICABLE |
| **DOC_003** | Aadhaar Handbook For Residents Tamil.pdf | `forms/01_AADHAAR/Guidelines/` | UIDAI | Resident Handbook (Tamil) | AUTHENTIC_OFFICIAL | HISTORICAL | IN_SCOPE | **HISTORICAL_VERSION** | NOT_APPLICABLE |
| **DOC_004** | Aadhaar_Seeding_Request_Form.pdf | `forms/07_CROSS_CATEGORY/Forms/` | Income Tax Dept / Protean | Seeding Request Form | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | PAN_AADHAAR_LINKING |
| **DOC_005** | Charges waived off for email update...pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (E&U-I) | Fee Waiver Circular | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_006** | Circular 30.04.2026 - Verifiable Credential.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (AU) | Policy Circular | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_007** | Circular dated 12.03.2025 - Operator Actions.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (E&U) | Disincentives Policy | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_008** | Circular dated 3.10.2023 - Version 4.1.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (Enforcement) | Disincentives Policy 4.1 | AUTHENTIC_OFFICIAL | HISTORICAL | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_009** | Circular_(DBT)_NRIPIOsOCIs.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI / DBT Mission | Advisory Circular | AUTHENTIC_OFFICIAL | HISTORICAL | IN_SCOPE | **HISTORICAL_VERSION** | NOT_APPLICABLE |
| **DOC_010** | Circular_(DBT)_Section 7 State Govts.pdf | `forms/01_AADHAAR/Circulars/` | Cabinet Sect / UIDAI | Section 7 Guidelines | AUTHENTIC_OFFICIAL | HISTORICAL | IN_SCOPE | **HISTORICAL_VERSION** | NOT_APPLICABLE |
| **DOC_011** | Circular_(E&U-I)_Expansion Modification.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (E&U-I) | Circular (Sched II) | AUTHENTIC_OFFICIAL | HISTORICAL | IN_SCOPE | **HISTORICAL_VERSION** | NOT_APPLICABLE |
| **DOC_012** | Circular_(E&U-I)_School Admissions.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (E&U) | Circular | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_013** | Circular_(E&U-II)_Certificate Enrolment Update.pdf | `forms/01_AADHAAR/Forms/` | UIDAI (E&U-II) | Certifier Proforma | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_014** | Circular_(Legal)_Authentication Regs Sched A.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (Auth) | Regulatory Amendment | AUTHENTIC_OFFICIAL | HISTORICAL | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_015** | Circular_(Legal)_Continuation AEPS.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (Legal) | Advisory Circular | AUTHENTIC_OFFICIAL | HISTORICAL | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_016** | Circular_(Legal)_Exception handling PDS.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (Legal) | Policy Directive | AUTHENTIC_OFFICIAL | HISTORICAL | IN_SCOPE | **HISTORICAL_VERSION** | NOT_APPLICABLE |
| **DOC_017** | Circular_(Legal)_Regulation 12A Gazette.pdf | `forms/01_AADHAAR/Notifications/` | UIDAI / MeitY | Gazette Notification | AUTHENTIC_OFFICIAL | HISTORICAL | IN_SCOPE | **HISTORICAL_VERSION** | NOT_APPLICABLE |
| **DOC_018** | Circular_(Legal)_Bank Accounts AePS.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (Legal) | Circular | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_019** | Circular_(Legal)_Section 7 Targeted Delivery.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (Legal) | Legal Directive | AUTHENTIC_OFFICIAL | HISTORICAL | IN_SCOPE | **HISTORICAL_VERSION** | NOT_APPLICABLE |
| **DOC_020** | Exploring New Horizons FINTECH.pdf | `forms/09_IRRELEVANT_QUARANTINE/` | UIDAI | Marketing Brochure | AUTHENTIC_OFFICIAL | HISTORICAL | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_021** | Extension of relaxation in fee charges SSUP.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (E&U-I) | Fee Waiver Circular | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_022** | For Resident Indian child (5-18) English.pdf | `forms/01_AADHAAR/Forms/` | UIDAI | Form 3 (Children 5-18) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_023** | For Resident Indian child (<5) English.pdf | `forms/01_AADHAAR/Forms/` | UIDAI | Form 5 (Children <5) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_024** | For Resident Indian Adult (18+) English.pdf | `forms/01_AADHAAR/Forms/` | UIDAI | Form 1 (Adults 18+) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_025** | For NRI child (5-18) outside India English.pdf | `forms/01_AADHAAR/Forms/` | UIDAI | Form 4 (NRI Child 5-18) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_026** | For NRI child (<5) outside India English.pdf | `forms/01_AADHAAR/Forms/` | UIDAI | Form 6 (NRI Child <5) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_027** | For Resident Foreign National (18+) English.pdf | `forms/01_AADHAAR/Forms/` | UIDAI | Form 7 (Foreign Adult) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_028** | For Resident Foreign National (<18) English.pdf | `forms/01_AADHAAR/Forms/` | UIDAI | Form 8 (Foreign Minor) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_029** | Form 93.pdf | `forms/02_PAN/Forms/` | Income Tax Dept (CBDT) | Form 93 (Rule 158) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NEW_PAN_ALLOTMENT |
| **DOC_030** | Form 94.pdf | `forms/02_PAN/Forms/` | Income Tax Dept (CBDT) | Form 94 (Rule 158) | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NEW_PAN_ALLOTMENT |
| **DOC_031** | Form 95_Updated_03Nov.pdf | `forms/02_PAN/Forms/` | Income Tax Dept (CBDT) | Form 95 (Rule 158) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NEW_PAN_ALLOTMENT |
| **DOC_032** | Form 96_Updated_03Nov.pdf | `forms/02_PAN/Forms/` | Income Tax Dept (CBDT) | Form 96 (Rule 158) | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NEW_PAN_ALLOTMENT |
| **DOC_033** | Introduction of Aadhaar Card PVC.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (Logistics) | Policy Circular | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_034** | List of Acceptable Document English.pdf | `forms/01_AADHAAR/Checklists/` | UIDAI (E&U) | Master Proof Matrix | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_035** | List_of_Supporting_Document.pdf | `forms/10_DUPLICATES_REVIEW/` | UIDAI (E&U) | Duplicate Proof Matrix | AUTHENTIC_OFFICIAL | DUPLICATE | IN_SCOPE | **EXACT_DUPLICATE** | NOT_APPLICABLE |
| **DOC_036** | PAN CR individual_03Nov.pdf | `forms/02_PAN/Forms/` | Income Tax Dept / Protean | PAN Correction (CSF) | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | PAN_CORRECTION |
| **DOC_037** | PAN CR non-Individual_03Nov.pdf | `forms/02_PAN/Forms/` | Income Tax Dept / Protean | Corporate PAN CSF | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | PAN_CORRECTION |
| **DOC_038** | Resident Handbook English 2021.pdf | `forms/01_AADHAAR/Guidelines/` | UIDAI | Resident Handbook (Eng) | AUTHENTIC_OFFICIAL | HISTORICAL | IN_SCOPE | **HISTORICAL_VERSION** | NOT_APPLICABLE |
| **DOC_039** | SOP dated 28-10-2021 - Exception SOP.pdf | `forms/01_AADHAAR/SOPs/` | UIDAI (E&U-I) | Exception SOP | AUTHENTIC_OFFICIAL | HISTORICAL | IN_SCOPE | **HISTORICAL_VERSION** | NOT_APPLICABLE |
| **DOC_040** | SOP for Training Authentication (1).pdf | `forms/10_DUPLICATES_REVIEW/` | UIDAI (Training) | Duplicate Operator SOP | AUTHENTIC_OFFICIAL | DUPLICATE | OUT_OF_SCOPE | **EXACT_DUPLICATE** | NOT_APPLICABLE |
| **DOC_041** | SOP for Training Authentication Operators.pdf | `forms/01_AADHAAR/SOPs/` | UIDAI (Training) | Operator SOP | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_042** | SOP for training E&U Operators.pdf | `forms/01_AADHAAR/SOPs/` | UIDAI (Training) | Operator SOP | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_043** | Standard operating Procedure (SOP) Name.pdf | `forms/01_AADHAAR/SOPs/` | UIDAI (E&U-I) | Master Name Update SOP | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |
| **DOC_044** | Swachhata Pakhwada implementation.pdf | `forms/09_IRRELEVANT_QUARANTINE/` | UIDAI | Office Action Plan | AUTHENTIC_OFFICIAL | HISTORICAL | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_045** | Three-month Preventive Vigilance Campaign.pdf | `forms/09_IRRELEVANT_QUARANTINE/` | UIDAI (Vigilance) | Vigilance Circular | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_046** | Training, Testing and Certification Policy.pdf | `forms/01_AADHAAR/SOPs/` | UIDAI (Training) | Training Policy 2023 | AUTHENTIC_OFFICIAL | CURRENT | OUT_OF_SCOPE | **OUT_OF_SCOPE** | NOT_APPLICABLE |
| **DOC_047** | Waiving off charges for MBU-1.pdf | `forms/01_AADHAAR/Circulars/` | UIDAI (E&U) | Fee Waiver Circular | AUTHENTIC_OFFICIAL | CURRENT | IN_SCOPE | **CURRENT_VERSION** | NOT_APPLICABLE |

---

## 4. High-Impact Legal Claims Matrix with Page-Level Evidence

All 8 high-impact claim categories have been reviewed against authentic physical documents. The supporting passages, clauses, and page numbers are detailed below (also exported to [`forms/LEGAL_CLAIM_SOURCE_MATRIX.csv`](file:///c:/Users/ajaya/Desktop/consolin/forms/LEGAL_CLAIM_SOURCE_MATRIX.csv)):

| Claim ID | Category | Statutory Claim Statement | Source ID | Page | Clause / Section | Supporting Quotation / Statutory Passage | Verification Status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **CLM_001** | Name update limits | Maximum 2 lifetime name updates permitted for Aadhaar number holders. | `DOC_039` | 2 | Para 1(b) | *"As per the existing guidelines, an Aadhaar number holder can update his/her name up to maximum of two times in life time."* | **VERIFIED_STATUTORY** |
| **CLM_002** | Name update limits | Operator typographical/data-entry errors do not consume the 2-update quota (count remains 0). | `DOC_039` | 5 | Annexure I, Case 2 | *"Request Due to 1. Typo Error by Enrolment operator 2. Transliteration error -> The request shall be accepted and correction made as per existing guidelines. Count of Update remains 0."* | **VERIFIED_STATUTORY** |
| **CLM_003** | Minor spelling corrections | Phonetically similar spelling changes (Ram to Rama, Sitaram to Seetaram) require only standard PoI. | `DOC_043` | 3 | Annexure A, Scenario 1(d) | *"There is a minor correction in English spelling, however names are phonetically similar. Illustrations: Ram to Rama, Sitaram to Seetaram, Savita to Sawita. Prescribed Document: PoI."* | **VERIFIED_STATUTORY** |
| **CLM_004** | Minor spelling corrections | Expanding abbreviations to full name or vice versa (V. S. Prasad to Vaddi Venkata Rama Siva Prasad) requires standard PoI. | `DOC_043` | 3 | Annexure A, Scenario 1(a) | *"Expanding the abbreviation or abbreviating the name to initials. Illustrations: V S Prasad to Vaddi Venkata Rama Siva Prasad... Prescribed Document: PoI."* | **VERIFIED_STATUTORY** |
| **CLM_005** | Minor spelling corrections | Adding or deleting middle or last names (Himanshu Gupta to Himanshu Chandra Gupta) requires standard PoI. | `DOC_043` | 3 | Annexure A, Scenario 1(b) | *"Addition or deletion of middle name(s) or last name. Illustrations: Himanshu Gupta to Himanshu Chandra Gupta... Prescribed Document: PoI."* | **VERIFIED_STATUTORY** |
| **CLM_006** | Minor spelling corrections | Sequential word order changes (Anand Breakar to Breakar Anand) require standard PoI. | `DOC_043` | 3 | Annexure A, Scenario 1(c) | *"Change in sequential order. Illustrations: Anand Breakar to Breakar Anand; Kishan Ravi to Ravi Kishan. Prescribed Document: PoI."* | **VERIFIED_STATUTORY** |
| **CLM_007** | Major name changes | Complete change of name / identity (Ram Kumar to Shyam Gupta) strictly requires Gazette Notification + PoI. | `DOC_043` | 2, 6 | Para 5 & Annexure A, Scenario 5(o) | *"In case such matching results in complete change in name / change of identity (categorized as a Major Name Change), the update request is liable to be rejected, if not accompanied by a Gazette Notification. Prescribed Document: PoI + Gazette for Name Change (Gazette Only)."* | **VERIFIED_STATUTORY** |
| **CLM_008** | Marriage surname changes | Female surname change post-marriage/divorce permitted via sworn Affidavit (Annexure D) + PoI / Marriage Certificate. | `DOC_043` | 5, 9 | Annexure A, Scenario 4(b) & Annexure D | *"Page 5: Change of surname of women, post marriage or divorce. Prescribed Document: PoI + Annexure D (Affidavit). Page 9: 'That consequent upon my marriage solemnized on... I have adopted/am entitled to use the surname... while my identity as the individual remains same.'"* | **VERIFIED_STATUTORY** |
| **CLM_009** | Marriage surname changes | Government marriage certificate containing address valid for PoA and PoR. | `DOC_034` | 16–18 | PoA List (#35) & PoR Section | *"Marriage Certificate issued by the Government, containing address. Permissible for PoA and PoR."* | **VERIFIED_STATUTORY** |
| **CLM_010** | Exception handling | 3rd or subsequent name update after exhausting 2-update quota routed to Regional Office (RO) Exception Handling. | `DOC_039` | 2–3 | Section B, Sub-paras (i) & (ii) | *"Resident to enrol for Aadhaar update at the nearest enrolment centre with concerned document and intimate UIDAI through mail... request to be verified with due diligence and packet to be processed as per process available for re-processing."* | **VERIFIED_STATUTORY** |
| **CLM_011** | Regional Office approvals | UIDAI Regional Offices hold exclusive jurisdiction to verify exception cases and recommend packet replay to Tech Centre. | `DOC_039` | 3, 6 | Section B & Annexure II | *"Page 3: 'the concerned Regional Offices to reprocess the packet'... Annexure II: 'The reviewing official may recommend for Replay... Packet reprocessed at Tech Centre.'"* | **VERIFIED_STATUTORY** |
| **CLM_012** | Gazette requirements | Gazette notification must be published in The Gazette of India or State Gazette, supported by prior photographic identity proof. | `DOC_034` | 1 | Notes, Point 5 | *"Gazette Notification along with any supporting PoI document of previous name with photograph (for Name change of resident)."* | **VERIFIED_STATUTORY** |
| **CLM_013** | Supporting documents | Original documents mandatory at enrolment centres; expired documents strictly rejected. | `DOC_034` | 1 | Important Instructions 1–4 | *"Original documents must be produced by the resident at the enrolment centre. The document must be in the name of the resident. Expired documents will not be accepted."* | **VERIFIED_STATUTORY** |
| **CLM_014** | Supporting documents | Standard Certifier Certificate (Gazetted Officer, MP/MLA, Panchayat Head) valid for 3 months from issuance. | `DOC_013` | 1–2 | Certifier Instructions 1–7 | *"The Certificate is valid for 3 months from date of issue. To be filled in BLOCK LETTERS. Certifier must sign and stamp across the resident photograph..."* | **VERIFIED_STATUTORY** |
| **CLM_015** | Data entry error correction | Aadhaar name data entry error corrected via sworn Affidavit on Rs. 10 stamp paper (Annexure B adults / Annexure C minors) + PoI. | `DOC_043` | 4, 7, 8 | Annexure A, Scenario (f) & Annexures B, C | *"Page 7: 'That due to an inadvertent data entry error at the time of enrolment/update, my name had been recorded in Aadhaar as whereas my correct name is... does not amount to a change of identity.'"* | **VERIFIED_STATUTORY** |
| **CLM_016** | Alias / Urf removal | Removal of 'urf' or 'alias' requires sworn Affidavit (Annexure E adults / Annexure F minors) declaring retention of single name. | `DOC_043` | 6, 10, 11 | Annexure A, Scenario (n) & Annexures E, F | *"Page 10: 'That I am presently recorded as ... urf or alias ... That I intend to retain the name of ... and discontinue the use as an alias/urf.'"* | **VERIFIED_STATUTORY** |

---

## 5. Separation of PAN Document Purposes

The 6 PAN documents in `forms/02_PAN/` plus cross-category `DOC_004` have been partitioned into distinct operational functional categories:

```
PAN Corpus Architecture:
├── NEW_PAN_ALLOTMENT (Rule 158 of Income Tax Rules, 1962)
│   ├── DOC_029: Form No. 93 — Indian Citizen Individuals (Replaces Form 49A) [IN_SCOPE Reference]
│   ├── DOC_030: Form No. 94 — Indian Companies & Entities [OUT_OF_SCOPE]
│   ├── DOC_031: Form No. 95 — Non-Citizen Individuals (Replaces Form 49AA) [IN_SCOPE Edge Case]
│   └── DOC_032: Form No. 96 — Foreign Corporate Entities [OUT_OF_SCOPE]
├── PAN_CORRECTION (Changes or Correction in PAN Data)
│   ├── DOC_036: PAN CR Individual (CSF Form) — [CORE OPERATIONAL ASSET FOR CONVELINA]
│   └── DOC_037: PAN CR Non-Individual — [OUT_OF_SCOPE Corporate]
└── PAN_AADHAAR_LINKING (Section 139AA of Income Tax Act)
    └── DOC_004: Aadhaar Seeding Request Form — [CORE CROSS-CATEGORY ASSET]
```

### Statutory Findings:
1. **Allotment vs Correction Separation:** Forms 93, 94, 95, and 96 are **allotment forms** used exclusively when applying for a new Permanent Account Number. They establish baseline identity fields and formatting requirements (e.g. mandatory quotation of Aadhaar, expanding initials). **They cannot be submitted to request a change or correction in existing PAN data.**
2. **Individual Correction Authority (`DOC_036`):** The *Request for Changes or Correction in PAN Data [For an Individual]* (CSF Form) is the sole authorized instrument for resolving name, parent name, date of birth, photo/signature, and address discrepancies on an existing PAN card.
3. **Cross-Category Linking Authority (`DOC_004`):** The *Seeding Request Form* provides the statutory mechanism under Section 139AA to reconcile minor demographic differences and link Aadhaar with PAN.

---

## 6. Preserved Evidence Gaps for Missing Categories

As established in Phase P3H.1, the `forms/` directory contains **zero documents** for four of CONVELINA's six statutory Tier 1 categories:

| Category | Available Files | Statutory Gap Status | Priority for Next User Ingestion |
| :--- | :---: | :---: | :--- |
| **01_AADHAAR** | **35 Files** (34 + 1 dup) | **CORPUS COMPREHENSIVE** | Ready for Pre-Processing Approval |
| **02_PAN** | **6 Files** | **CORPUS COMPREHENSIVE** | Ready for Pre-Processing Approval (Forms 93, 95, 36) |
| **03_PASSPORT** | **0 Files** | **CRITICAL EVIDENCE GAP** | PSP Application Form, Annexure E (Deed Poll), Annexure D, MEA Split-Name Advisory |
| **04_CLASS_10** | **0 Files** | **CRITICAL EVIDENCE GAP** | CBSE Rule 69 Examination Bye-Laws, State Board Correction Proforma |
| **05_CLASS_12** | **0 Files** | **CRITICAL EVIDENCE GAP** | CBSE Senior School Certificate Correction Guidelines, Gazette Notification Proforma |
| **06_EPFO_UAN** | **0 Files** | **CRITICAL EVIDENCE GAP** | EPFO Joint Declaration Form (3-column format), Member Profile SOP 2024 |

The detailed statutory gap ledger remains documented in [`forms/SOURCE_VERIFICATION_GAPS.md`](file:///c:/Users/ajaya/Desktop/consolin/forms/SOURCE_VERIFICATION_GAPS.md).

---

## 7. Corpus Pre-Processing Eligibility Roster

The following 19 authoritative documents are hereby certified as **reconciled, verified, and eligible for future human approval** before corpus pre-processing or RAG ingestion:

### A. Aadhaar In-Scope Corpus (15 Documents)
1. **`DOC_001`**: Aadhaar Enrolment/Update Form 1 (Adults 18+) — `CURRENT_VERSION`
2. **`DOC_024`**: Aadhaar Enrolment/Update Form 1 (Adults 18+ Variant) — `CURRENT_VERSION`
3. **`DOC_022`**: Aadhaar Enrolment/Update Form 3 (Children 5–18) — `CURRENT_VERSION`
4. **`DOC_023`**: Aadhaar Enrolment/Update Form 5 (Children <5) — `CURRENT_VERSION`
5. **`DOC_025`**: Aadhaar Enrolment/Update Form 4 (NRI Child 5–18) — `CURRENT_VERSION`
6. **`DOC_026`**: Aadhaar Enrolment/Update Form 6 (NRI Child <5) — `CURRENT_VERSION`
7. **`DOC_027`**: Aadhaar Enrolment/Update Form 7 (Foreign Adult 18+) — `CURRENT_VERSION`
8. **`DOC_028`**: Aadhaar Enrolment/Update Form 8 (Foreign Minor <18) — `CURRENT_VERSION`
9. **`DOC_043`**: Master Name Update SOP (`HQ-16024/4/2020-EU-I-HQ`) — `CURRENT_VERSION`
10. **`DOC_034`**: Master Proof Matrix (22 Pages, `HQ-16042/4/2021-EU-I-HQ`) — `CURRENT_VERSION`
11. **`DOC_013`**: Standard Certifier Certificate Format (`4(4)/57/405/AM/2019-E&U-II`) — `CURRENT_VERSION`
12. **`DOC_005`**: Email Address Update Fee Waiver Circular — `CURRENT_VERSION`
13. **`DOC_006`**: Digital Verifiable Credential Validity Circular — `CURRENT_VERSION`
14. **`DOC_021`**: myAadhaar Free Document Update Extension Circular — `CURRENT_VERSION`
15. **`DOC_047`**: MBU-1 Child Biometric Update Fee Waiver Circular — `CURRENT_VERSION`

### B. PAN In-Scope Corpus (3 Documents)
16. **`DOC_036`**: Request for Changes or Correction in PAN Data (Individual CSF Form) — `CURRENT_VERSION`
17. **`DOC_029`**: Form No. 93 [Rule 158] (Indian Individual Allotment Reference) — `CURRENT_VERSION`
18. **`DOC_031`**: Form No. 95 [Rule 158] (Foreign Individual Allotment Reference) — `CURRENT_VERSION`

### C. Cross-Category Corpus (1 Document)
19. **`DOC_004`**: Form for Aadhaar Seeding into PAN Database (Section 139AA) — `CURRENT_VERSION`

### D. Historical & Tamil Reference Corpus (Eligible as Reference Context)
20. **`DOC_039`**: Exception Handling SOP 2021 (RO 3rd+ Update & Gender Rules) — `HISTORICAL_VERSION`
21. **`DOC_003`**: Aadhaar Resident Handbook (Tamil Translation Glossary) — `HISTORICAL_VERSION`
22. **`DOC_038`**: Aadhaar Resident Handbook (English Edition 2021) — `HISTORICAL_VERSION`
23. **`DOC_011`**: Schedule II Expansion Circular 2016 — `HISTORICAL_VERSION`
24. **`DOC_016`**: Welfare Scheme Exception Handling Circular 2017 — `HISTORICAL_VERSION`
25. **`DOC_017`**: Regulation 12A Extraordinary Gazette Notification 2017 — `HISTORICAL_VERSION`

---

## 8. Final Acceptance Verification

- [x] All 41 audited document IDs reconciled across all 47 repository files.
- [x] Zero duplicate document identities; every DOC ID maps 1:1 to one original file.
- [x] All original file SHA-256 hashes unchanged and verified against physical disk files.
- [x] Zero unsupported `VERIFIED_CURRENT` claims; misclassifications (`DOC_014`, `DOC_035`, `DOC_040`, `DOC_041`, `DOC_043`) fully resolved.
- [x] High-impact legal claims backed by exact PDF page numbers, clauses, and quotations.
- [x] PAN allotment and correction instruments strictly separated.
- [x] Missing categories (`Passport`, `Class 10`, `Class 12`, `EPFO`) preserved as documented evidence gaps.
- [x] Zero Qdrant ingestion, zero embedding generation, zero Gemini API calls, zero source code changes.

**Audit Status:** P3H.1.1 is fully executed. Awaiting human approval before proceeding to Phase P3H.2.

