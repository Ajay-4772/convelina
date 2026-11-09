# CONVELINA — Aadhaar Source Document Verification Report (Phase P3H.1.1 Reconciled)

**Audited Domain:** Unique Identification Authority of India (UIDAI) / Aadhaar Card  
**Audit Date:** November 8, 2026 (Reconciled in Phase P3H.1.1)  
**Total Documents Audited:** 35 Documents (34 primary organized + 1 duplicate review)  
**Status:** **RECONCILED & GROUNDED IN STATUTORY TEXT**

---

## 1. Executive Summary

This report establishes the authentic provenance, legal authority, and operational validity of the 35 Aadhaar-related documents identified in CONVELINA's `forms/` directory.

### Reconciled Multi-Dimensional Breakdown
- **`CURRENT_VERSION` (16 Documents):** Form suite (Forms 1, 3, 4, 5, 6, 7, 8), Master Name Update SOP (`DOC_043`), Master Proof Matrix (`DOC_034`), Certifier Certificate (`DOC_013`), Fee Waiver Circulars (`DOC_005`, `DOC_021`, `DOC_047`), PVC Card Equivalence (`DOC_033`), and Verifiable Credential Validity (`DOC_006`).
- **`HISTORICAL_VERSION` (8 Documents):** Resident Handbooks (`DOC_003` Tamil, `DOC_038` English), Exception Handling SOP 2021 (`DOC_039`), Schedule II Expansion Circular 2016 (`DOC_011`), Section 7 Directives (`DOC_010`, `DOC_019`), Welfare Exception Circular (`DOC_016`), and Regulation 12A Extraordinary Gazette (`DOC_017`).
- **`EXACT_DUPLICATE` (1 Document):** `DOC_035` (quarantined copy of `DOC_034`, SHA-256: `07e1d5ff18a56ac8e5654573cafa6cec351793bfe754be2939c39fa971d3afd8`).
- **`OUT_OF_SCOPE` (9 Documents):** Operator testing/certification policies and SOPs (`DOC_041`, `DOC_042`, `DOC_046`), Operator fraud/penalty policies (`DOC_007`, `DOC_008`), School admission circular (`DOC_012`), Aviation requesting entities circular (`DOC_014`), and Banking payment/e-KYC advisories (`DOC_015`, `DOC_018`).
- **`AUTHENTICITY_UNCONFIRMED` (1 Document):** Azam Khan slide deck (`DOC_002`).

---

## 2. Key Operational Assets & Page-Level Statutory Evidence

### A. The Master Name Update SOP (`DOC_043`)
- **Authority:** Unique Identification Authority of India (UIDAI), Enrolment & Update-I Division.
- **Reference Number:** `F.no. HQ-16024/4/2020-EU-I-HQ` (e-Office: `1/58751/2026`) dated `18-09-2026`.
- **Issuing Official:** `Nikhil Sinha, Director`.
- **Key Provisions & Page Numbers:**
  - **Page 1, Paragraph 1:** Explicitly supersedes the Name update process described in the 2021 Exception SOP (`DOC_039`).
  - **Page 2, Paragraph 2:** Mandatory block letter recording; dots, prefixes, ranks, and special characters prohibited.
  - **Page 2, Paragraph 5:** Match with previously updated names; major name changes liable to be rejected without Gazette Notification.
  - **Page 3 (Annexure A, Minor Name Change):**
    - Scenario 1(a): Expanding abbreviation or abbreviating name to initials -> Requires standard PoI.
    - Scenario 1(b): Addition or deletion of middle name(s) or last name -> Requires standard PoI.
    - Scenario 1(c): Change in sequential order of words -> Requires standard PoI.
    - Scenario 1(d): Minor spelling correction with phonetic similarity -> Requires standard PoI.
  - **Page 4 (Annexure A, Data Entry Error):**
    - Scenario (f): Error by operator -> Verified against previously submitted documents; if matching CIDR, instant update accepted. If not matching, requires PoI/PoA + sworn Affidavit (**Annexure B** for adults, **Annexure C** for minors) on Rs. 10 stamp paper.
  - **Page 5 (Annexure A, Women's Post-Marriage/Divorce Surname Change):**
    - Scenario 4(b): Change of surname of women post marriage/divorce -> Requires PoI + sworn Affidavit (**Annexure D**) on Rs. 10 stamp paper.
  - **Page 6 (Annexure A, Major Name Change & Alias Removal):**
    - Scenario 5(o): Complete change of name / identity -> Strictly requires **PoI + Gazette Notification for Name Change (Gazette Only)**.
    - Scenario (n): Removal of "urf" or "alias" -> Requires PoI + sworn Affidavit (**Annexure E** for adults, **Annexure F** for minors) declaring retention of single name.
  - **Pages 7–11:** Full statutory text and formats for Affidavits B, C, D, E, and F.

### B. Standard Operating Procedure for Exception Handling (`DOC_039`)
- **Authority:** UIDAI Enrolment & Update-I Division.
- **Reference Number:** `F.No. HQ-16022/2/2020-EU-I-HQ-Part(1)` dated `28-10-2021` / Circular dated `03-11-2021`.
- **Issuing Official:** `Prabhakaran C R, Deputy Director (E&U-I)`.
- **Key Provisions & Page Numbers:**
  - **Page 2, Paragraph 1(b):** Lifetime update limit: *"As per the existing guidelines, an Aadhaar number holder can update his/her name up to maximum of two times in life time."*
  - **Page 2–3, Section B:** Procedure for 3rd or subsequent updates: Resident enrols at enrolment centre, sends Enrolment ID (EID) and documents to the concerned UIDAI Regional Office (RO) directly or via CRM (`help@uidai.gov.in` / toll-free `1947`).
  - **Page 3 & 6 (Annexure II):** Regional Office verifies due diligence and initiates packet replay via the UIDAI Technology Centre in Bengaluru.
  - **Page 4 & 7 (Annexure III):** Gender update exception handling (Medical Certificate issued by surgeon or Government Transgender Certificate required).

### C. Master Proof Matrix (`DOC_034`)
- **Authority:** UIDAI Enrolment & Update Division.
- **Reference Number:** Circular No. `HQ-16042/4/2021-EU-I-HQ` (22 pages).
- **Key Provisions:**
  - Defines the 4 statutory proof schedules: Proof of Identity (PoI), Proof of Address (PoA), Proof of Date of Birth (PDB), and Proof of Relationship (PoR).
  - Page 1 Instructions: Original documents mandatory at centres; document must be in the resident's name; expired documents strictly rejected.
  - Gazette Notification rule: Must be accompanied by previous photo PoI document.

### D. Standard Certifier Certificate Form (`DOC_013`)
- **Authority:** UIDAI E&U-II Division.
- **Reference Number:** `F. No. 4(4)/57/405/AM/2019-E&U-II` dated `23-10-2019`.
- **Key Provisions:**
  - Standard proforma for residents lacking primary documents.
  - Authorized certifiers: Gazetted Officers (Group A/B), Village Panchayat Head/Mukhiya, MP/MLA/MLC, Municipal Councilor, Tehsildar, Superintendent of Recognized Shelter Homes/Orphanages.
  - Validity: Strictly 3 months from date of issuance. Overwriting or correction invalidates the certificate.

---

## 3. Discrepancies Rectified from Previous Audit

1. **`DOC_014` Supersession Blunder:** Previous report claimed `DOC_014` was "replaced by Form 1". Rectified: `DOC_014` is an amendment to Schedule A of Authentication Regulations regarding airport/airline requesting entities under `K-11020/45/2012-UIDAI(Auth)`. Classified as **`OUT_OF_SCOPE`**.
2. **`DOC_035` Mislabeling:** Rectified from "SUPERSEDED" to **`EXACT_DUPLICATE`** of `DOC_034`.
3. **`DOC_043` Hallucinated Citations:** Rectified from non-existent 2022 circular to authentic `F.no. HQ-16024/4/2020-EU-I-HQ` dated `18-09-2026`.
4. **Complete Extraction of `DOC_043`:** 100% of all 11 pages extracted, transcribed, and analyzed.

---

## 4. Pre-Processing Eligibility Roster

The 15 in-scope `CURRENT_VERSION` Aadhaar documents (`DOC_001`, `DOC_005`, `DOC_006`, `DOC_013`, `DOC_021`, `DOC_022`, `DOC_023`, `DOC_024`, `DOC_025`, `DOC_026`, `DOC_027`, `DOC_028`, `DOC_033`, `DOC_034`, `DOC_043`, `DOC_047`) are certified as reconciled and eligible for future human approval before corpus pre-processing.
