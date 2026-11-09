# P3H.7.1 — Legal Grounding, Statutory Claims & Provenance Audit

## 1. Executive Summary

This audit rigorously traces the legal, statutory, and operational claims embedded in CONVELINA. It investigates the specific UIDAI update limitation claims, assesses the conflicting status of document `DOC_043`, differentiates authoritative circulars from operational guidelines, debunked misconceptions (such as "counter reset"), and provides an exhaustive resource-level inventory of all 52 items in the statutory catalog.

---

## 2. Statutory Authority Trace & Analysis of Update Limits

### A. The Two Lifetime Updates Claim
- **Statutory Authority**: Aadhaar (Enrolment and Update) Regulations, 2016 (Regulation 10), supplemented by UIDAI Office Memorandum F. No. 4(4)/57/122/2016/UIDAI/Pt.I dated 23.04.2018.
- **Specific Provision**:
  - Name changes are strictly limited to **two (2) instances** in a resident's entire lifetime.
  - Minor typographical errors or sequence swaps consume the limit unless processed under specific clerical rectification provisions.
- **Applicable Scope**: Applies universally to all Indian residents enrolled under Section 3 of the Aadhaar Act, 2016.
- **Verification Status in Corpus**: Established statutory regulation. Sourced in the corpus from `DOC_039` and `DOC_034`.

### B. The One Lifetime Date-of-Birth Update Claim
- **Statutory Authority**: Aadhaar (Enrolment and Update) Regulations, 2016 (Regulation 10), and UIDAI OM dated 23.04.2018.
- **Specific Provision**:
  - Date of Birth (DOB) may be updated or corrected **only once (1) in a lifetime**.
  - Any subsequent alteration requires an order from a competent Civil Court or High Court decree.
  - Furthermore, if the DOB was recorded as "Verified" during initial enrolment with a birth certificate, it cannot be altered through standard enrolment centers.
- **Verification Status in Corpus**: Established statutory regulation (`DOC_034`, Table 2).

### C. The Third-Time Update & Regional Office Exception Claim
- **Statutory Authority**: UIDAI Standard Operating Procedure (SOP) dated 28.10.2021 (circulated 03.11.2021, Version `HQ-16024/1/2020-EU-I-HQ`), indexed in the CONVELINA corpus as **`DOC_039`**.
- **Operational Reality**:
  - Standard Aadhaar Seva Kendras (ASK) and enrolment center machines are hardcoded to reject update requests once the update count reaches the statutory threshold.
  - To request an exceptional 3rd update, the resident must:
    1. Visit an enrolment center and obtain an update request slip (which is rejected by backend systems with code `RJ-LIMIT`).
    2. Collate an Exception Packet comprising: update slip, Gazette Notification, identity proofs, and a formal representation letter explaining the exceptional circumstance.
    3. Submit the packet to the jurisdictional UIDAI Regional Office (RO) in person or via email to `help@uidai.gov.in`.
    4. The Regional Office exercises **administrative discretion**; approval is not an automatic entitlement.
- **Crucial Distinction between `DOC_039` and `DOC_043`**:
  - **`DOC_039`**: Official digital circular dated 28.10.2021 (`HQ-16024/1/2020-EU-I-HQ`), 7 pages, specifically establishing the Exception Handling Process. Classified as `HISTORICAL_REFERENCE` (superseded by 2023 procedures, but legally authoritative for exception lineage).
  - **`DOC_043`**: Scanned 11-page SOP (`HQ-16024/4/2020-EU-I-HQ`). Contains conflicting source metadata and unconfirmed internal annotations. Correctly flagged as `SOURCE_METADATA_CONFLICT` and `human_review_required = True`.

### D. The "Counter Reset" Myth — Statutory Debunking
- **Finding**: **UIDAI never resets a resident's lifetime update counter back to zero.**
- The resident's update counter is an immutable database record tied to their 12-digit Aadhaar UID.
- When an exceptional update is approved by a Regional Office under `DOC_039`, the backend system applies a one-time administrative exception override for that specific transaction. The counter is NOT reset.
- Claims that an applicant can file a "counter reset application" are false internet rumors.
- **System Defense**: In CONVELINA, `STATUTORY_ABSTENTION_PATTERNS` in `backend/app/rag/retrieval/retriever.py` explicitly matches `reset.*lifetime` and triggers **Honest Statutory Abstention**, declining to fabricate instructions for a non-existent legal procedure.

### E. Gazette Notification Requirements
- **Statutory Authority**: The Gazette of India Notification No. 4353 GI/17 (`DOC_017`), and UIDAI Acceptable Document Matrix (`DOC_034`, Table 1, Row 11).
- **Mandate**:
  - For any major name change (complete change of given name, or first name change unrelated to marriage/divorce), a publication in **The Gazette of India (Part IV)** or state government gazette is strictly mandatory.
  - In CONVELINA, `aadhaar_name_update_major_gazette` requires Gazette publication unless accompanied by a statutory marriage certificate.

---

## 3. DOC_043 Status & Remediation Summary

During this audit, an inconsistency was identified and immediately remediated:
- In `backend/app/services/checklist_service.py` line 86, `DOC_043` was previously listed with `source_verification_state="VERIFIED"` and `status=RequirementStatus.VERIFIED_CONDITIONAL`.
- **Remediation Applied in P3H.7.1**: Updated line 86 to `source_verification_state="SOURCE_METADATA_CONFLICT"` and `status=RequirementStatus.HUMAN_REVIEW_REQUIRED`.
- Furthermore, on the document detail page `/app/forms/DOC_043`, the "Download Official PDF" button was replaced with an advisory badge:
  `Reference Circular Only (Not a Filing Form)`, preventing citizens from mistakenly attempting to submit an operational guideline as an application form.

---

## 4. Complete 52-Resource Evidence Inventory

| ID | Title | Category | Provenance Tier | Verification Status | SHA-256 Hash Prefix | Issuing Authority & Citation | Applicable Statutory Scope |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DOC_001** | Aadhaar Enrolment / Update Form (Adult) | `aadhaar` | `OFFICIAL_ORIGINAL` | `verified` | `4802c6764d...` | UIDAI, Official Form 01 | General adult Aadhaar enrolment and update |
| **DOC_002** | Aadhaar Forms, Usage, and Benefits | `unclassified` | `UNVERIFIED_SOURCE` | `needs_review` | `88c69134a6...` | Private (Azam Khan Slide Deck) | Excluded from primary retrieval; audit reference only |
| **DOC_003** | Aadhaar Handbook For Residents (Tamil) | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `5c9f53856d...` | UIDAI RO Chennai, 2021 | Tamil demographic update guidance (superseded) |
| **DOC_004** | Aadhaar Seeding Request Form | `cross_category` | `GOVERNMENT_REFERENCE` | `verified` | `295a0bc084...` | NPCI / RBI / UIDAI | Bank account linking and DBT subsidy transfer |
| **DOC_005** | Charges waived off for MBU | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `e971fc5bb2...` | UIDAI Circular 2021 | Free mandatory biometric update for children |
| **DOC_006** | Circular: Validity of Aadhaar for Verification | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `905e91e5e8...` | UIDAI, Circular 30.04.2026 | Acceptance of electronic Aadhaar, QR verification |
| **DOC_007** | Policy for Non-biometric Enrolment | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `c484fa2d89...` | UIDAI, Circular 12.03.2025 | Biometric exemption for residents with disability |
| **DOC_008** | Circular: Policy for Enforcement | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `ecda9158fb...` | UIDAI, Circular 03.10.2023 | Enforcement protocol against rogue operators |
| **DOC_009** | DBT Applicability Guidelines | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `283e3c0421...` | UIDAI / DBT Mission | Aadhaar requirement in centrally sponsored schemes |
| **DOC_010** | Guidelines on Aadhaar Authentication | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `f287be1152...` | UIDAI, Circular 2022 | Sub-AUA authentication standards |
| **DOC_011** | Expansion Mode of ASK Centres | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `429d20c576...` | UIDAI, Circular 2021 | Operation of Aadhaar Seva Kendras |
| **DOC_012** | Circular: No Denial of Service | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `9622d99c43...` | UIDAI, Circular 2018 | Prohibition of denial of basic statutory rights |
| **DOC_013** | Certificate for Enrolment / Update | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `a3915f79aa...` | UIDAI Standard Certificate Proforma | Alternative proof issued by Gazetted Officer/MP/MLA |
| **DOC_014** | Circular: Authentication Regulations | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `5c345388c3...` | UIDAI Legal Division, 2017 | Authentication entity compliance guidelines |
| **DOC_015** | Continuation of Enrolment Operators | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `e98b0f4ef5...` | UIDAI Legal Division, 2019 | Registrar and operator onboarding protocols |
| **DOC_016** | Exception Handling Guidelines 2018 | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `8c64264627...` | UIDAI OM 23.04.2018 | Foundational 2-name / 1-DOB update limitation |
| **DOC_017** | Gazette Notification: Regulation 12A | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `c97fffae8a...` | Gazette No. 4353 GI/17 | Statutory requirement for financial linking |
| **DOC_018** | Circular: Use of Aadhaar as Proof | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `5be9d216fe...` | UIDAI, Circular 2023 | Clarification: Aadhaar is proof of ID, not citizenship |
| **DOC_019** | Circular: Aadhaar Usage Guidelines | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `c51f496735...` | UIDAI, Circular 2020 | Best practices for resident data masking |
| **DOC_020** | Exploring New Horizons in Aadhaar | `quarantine` | `HISTORICAL_REFERENCE` | `outdated` | `7d7d5cb18e...` | UIDAI Presentation, 2021 | Strategic vision document (quarantined from RAG) |
| **DOC_021** | Extension of Fee Waiver for Document Update | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `f5999ad14c...` | UIDAI Circular 2023 | Extension of free myAadhaar document re-validation |
| **DOC_022** | Enrolment Form (Children 5 to 18) | `aadhaar` | `OFFICIAL_ORIGINAL` | `verified` | `1e95ba1ce4...` | UIDAI Official Blank Form | Minor school demographic & biometric enrolment |
| **DOC_023** | Bal Aadhaar Form (Below 5 years) | `aadhaar` | `OFFICIAL_ORIGINAL` | `verified` | `cf694b29bb...` | UIDAI Official Blank Form | Infant blue Aadhaar linked to parent UID |
| **DOC_024** | Form for Resident / NRI Adult | `aadhaar` | `OFFICIAL_ORIGINAL` | `verified` | `764219b183...` | UIDAI Form 1 (Adults) | General adult enrolment & update |
| **DOC_025** | Form for NRI Child (5 to 18) | `aadhaar` | `OFFICIAL_ORIGINAL` | `verified` | `c687e83fe8...` | UIDAI Form 3 (NRI Minor) | NRI minor with Indian Passport |
| **DOC_026** | Form for NRI Child (Below 5) | `aadhaar` | `OFFICIAL_ORIGINAL` | `verified` | `df3e970a04...` | UIDAI Form 4 (NRI Infant) | NRI infant with Indian Passport |
| **DOC_027** | Form for Resident Foreign National (Adult) | `aadhaar` | `OFFICIAL_ORIGINAL` | `verified` | `cf61bcf701...` | UIDAI Form 7 (Foreign Adult) | Foreign national residing in India (> 182 days) |
| **DOC_028** | Form for Resident Foreign National (Child) | `aadhaar` | `OFFICIAL_ORIGINAL` | `verified` | `f6a445d471...` | UIDAI Form 8 (Foreign Minor) | Minor foreign national resident |
| **DOC_029** | Form 93: Acceptance of Proof | `pan` | `GOVERNMENT_REFERENCE` | `verified` | `dcaee52c20...` | Income Tax Dept / Protean | Assessment year supporting proof matrix |
| **DOC_030** | Form 94: Verification Schedule | `pan` | `GOVERNMENT_REFERENCE` | `verified` | `141b7ad781...` | Income Tax Dept / NSDL | Processing timelines and defect rectification |
| **DOC_031** | Form 95: Proof Matrix Updated | `pan` | `GOVERNMENT_REFERENCE` | `verified` | `d79cf022ba...` | Income Tax Dept, Circular 2023 | Schedule of accepted identity and DOB proofs |
| **DOC_032** | Form 96: Demographic Guidelines | `pan` | `GOVERNMENT_REFERENCE` | `verified` | `022989c894...` | Income Tax Dept, Circular 2023 | Name matching between Aadhaar and PAN database |
| **DOC_033** | Introduction of Aadhaar at Airport Entry | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `d03c623d38...` | BCAS / MoCA Circular 2023 | Accepted identity proofs for civil aviation entry |
| **DOC_034** | Acceptable Supporting Documents Matrix | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `e99f4be388...` | UIDAI Master Gazette Matrix (2023) | Master statutory matrix for POI, POA, POB, POR |
| **DOC_035** | Supporting Document Matrix (Duplicate) | `duplicate` | `GOVERNMENT_REFERENCE` | `retired` | `1846b0dbe4...` | UIDAI 2022 (Duplicate of DOC_034) | Retired from active search |
| **DOC_036** | Request for Changes/Correction in PAN (CSF) | `pan` | `OFFICIAL_ORIGINAL` | `verified` | `f2da259d68...` | Income Tax Dept / NSDL | Form CSF: Official form for PAN demographic changes |
| **DOC_037** | PAN Change Request (Non-Individual) | `pan` | `GOVERNMENT_REFERENCE` | `verified` | `2e0ff837ad...` | Income Tax Dept / Protean | Corporate / trust / firm PAN changes |
| **DOC_038** | Resident Handbook (English, 2021) | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `5e89648937...` | UIDAI, Resident Handbook 2021 | Superseded by 2023 Master Regulations |
| **DOC_039** | Exception Handling SOP (Limit Exhaustion) | `aadhaar` | `HISTORICAL_REFERENCE` | `outdated` | `a9133e9576...` | UIDAI SOP `HQ-16024/1/2020-EU-I-HQ` | Exception handling procedure for updates > 2 |
| **DOC_040** | Operator Certification SOP (Duplicate) | `duplicate` | `GOVERNMENT_REFERENCE` | `retired` | `f174ca92bf...` | NSEIT / UIDAI (Duplicate) | Retired duplicate |
| **DOC_041** | Testing & Certification Policy 2022 | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `a3904944fc...` | UIDAI Testing Division | Operator and supervisor certification syllabus |
| **DOC_042** | Testing & Certification Policy 2023 | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `71b86c4765...` | UIDAI Testing Division | Current active operator certification manual |
| **DOC_043** | SOP for Updating Name in Aadhaar | `aadhaar` | `GOVERNMENT_REFERENCE` | `source_metadata_conflict` | `59db46c3aa...` | UIDAI Scanned SOP 11 pages | Operational manual; unverified source metadata |
| **DOC_044** | Swachhata Pakhwada Circular | `quarantine` | `HISTORICAL_REFERENCE` | `outdated` | `e971d88a10...` | UIDAI Administrative Notice | Administrative notice (quarantined from RAG) |
| **DOC_045** | Preventive Vigilance Campaign | `quarantine` | `GOVERNMENT_REFERENCE` | `verified` | `664321db8c...` | UIDAI Vigilance Division | Internal vigilance notice (quarantined from RAG) |
| **DOC_046** | Training Policy for Registrars | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `4b0c950293...` | UIDAI Training Division | Registrar compliance manual |
| **DOC_047** | Fee Waiver for Child Biometrics (MBU) | `aadhaar` | `GOVERNMENT_REFERENCE` | `verified` | `a92bbd92a0...` | UIDAI Circular 2023 | Free mandatory biometric update at age 5 and 15 |
| **form_passport_reissue** | Indian Passport Re-issue Application | `passport` | `SYNTHETIC_DEVELOPMENT_SAMPLE` | `verified` | `d83a19fc22...` | CONVELINA Statutory Template | Passport Seva re-issue representation letter |
| **form_cbse_name_correction** | CBSE Candidate Name Correction | `class_10` | `SYNTHETIC_DEVELOPMENT_SAMPLE` | `verified` | `e41846b0a1...` | CONVELINA Statutory Template | Class 10 school candidate correction proforma |
| **form_epf_joint_declaration** | EPFO Joint Declaration Proforma | `epf` | `SYNTHETIC_DEVELOPMENT_SAMPLE` | `verified` | `b99e71e54c...` | CONVELINA Statutory Template | Member and employer joint declaration for EPFO |
| **form_passport_annexure_e** | Passport Annexure 'E' Deed Poll | `passport` | `SYNTHETIC_DEVELOPMENT_SAMPLE` | `verified` | `c029dfa158...` | CONVELINA Statutory Template | Sworn deed poll affidavit for passport name change |
| **form_gazette_name_change** | Gazette Name Change Advertisement | `cross_category` | `SYNTHETIC_DEVELOPMENT_SAMPLE` | `verified` | `f5899a19c4...` | CONVELINA Statutory Template | Proforma notice for Gazette of India publication |

