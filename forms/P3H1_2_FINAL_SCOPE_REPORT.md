# CONVELINA — Phase P3H.1.2: Final Corpus Scope, Applicability & Approval Manifest Report

**Phase:** P3H.1.2 (Corpus Scope Partition, Applicability Mapping & Final Approval Manifest)  
**Total Repository Documents Audited:** 47 Files  
**Mathematical Reconciliation:** 100% Reconciled (8 Core + 12 Reference + 9 Historical + 15 Out-of-Scope + 2 Duplicates + 1 Unverified = 47)  
**Corpus Approval Status:** All Candidate Documents Flagged as **`PENDING_USER_APPROVAL`**  
**Restrictions Enforced:** Zero Embeddings Generated; Zero Qdrant Ingestion; Zero External LLM Calls; Zero Code Changes.

---

## 1. Executive Summary & Purpose

Phase P3H.1.2 formally resolves the remaining corpus-scope questions from P3H.1.1, establishes explicit applicability metadata across all statutory documents, disambiguates core correction procedures from reference/allotment sources, and creates four definitive manifests to govern future corpus pre-processing.

No documents are automatically approved for ingestion. Every document proposed for future pre-processing is marked **`PENDING_USER_APPROVAL`**, while non-qualifying files are tagged **`EXCLUDED_FROM_PREPROCESSING`**.

---

## 2. Mathematical Reconciliation of the 47-File Inventory

The previous P3H.1.1 report grouped 19 documents as an "eligible roster" without cleanly distinguishing between active correction workflows and static reference/allotment material. In P3H.1.2, this grouping has been mathematically reconciled into mutually exclusive, transparent categories:

```
Master Inventory Breakdown (Total: 47 Physical PDFs)
├── 1. Current Core Correction Corpus:       8 documents (Active operational correction forms & rules)
├── 2. Reference-Only Corpus:               12 documents (Allotment references, NRI/foreign forms, fee circulars)
├── 3. Historical Reference Corpus:          9 documents (Historical precedents, Tamil glossary, exception SOP)
├── 4. Out-of-Scope Documents:              15 documents (Operator testing/penalties, AePS banking, corporate PAN)
├── 5. Exact Duplicates:                     2 documents (DOC_035 duplicate of DOC_034; DOC_040 of DOC_041)
└── 6. Unverified Material:                  1 document  (DOC_002: Private Azam Khan slide deck)
─────────────────────────────────────────────────────────────────────────────────────────────
SUM TOTAL:                                  47 documents (Exact 100% Mathematical Reconciliation)
```

### Reconciliation of the Preliminary 19-Document Roster:
The preliminary 19-document roster in P3H.1.1 combined:
- **8 Core Correction Documents:** `DOC_001`, `DOC_004`, `DOC_013`, `DOC_022`, `DOC_023`, `DOC_034`, `DOC_036`, `DOC_043`.
- **11 Reference-Only Documents:** `DOC_005`, `DOC_006`, `DOC_021`, `DOC_024`, `DOC_025`, `DOC_026`, `DOC_027`, `DOC_028`, `DOC_029`, `DOC_031`, `DOC_047`.
- *(Plus `DOC_033` PVC Card Equivalence Circular, bringing Reference-Only to exactly 12 documents).*

By separating the **8 Core Correction** instruments from the **12 Reference-Only** instruments, CONVELINA ensures that an allotment proforma or fee waiver circular is never mistaken for a citizen correction procedure.

---

## 3. Aadhaar Applicability Metadata

Every Aadhaar document proposed for pre-processing has been evaluated against explicit demographic, cohort, and procedural parameters:

| Document ID | Official Title | Applicant Age Group | Demographic Cohort | Lifecycle Stage | Data Type | Target Field Coverage | Workflow Type | Key Statutory Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DOC_043** | Master Name Update SOP (`HQ-16024/4/2020-EU-I-HQ`) | All age cohorts | All Aadhaar Holders | Correction / Update | Demographic | Name, Initials, Sequence, Surnames, Alias | Standard (Minor) / Gazette (Major) | Gazette mandatory for major name change; Affidavits B–F mandatory on Rs. 10 stamp paper; supersedes name update process of DOC_039. |
| **DOC_034** | Master Proof Matrix (22 Pages) | All age cohorts | Residents, NRIs, Foreign Nationals | Enrolment & Update | Supporting Proofs | All demographic fields (PoI, PoA, PDB, PoR) | Statutory Verification | Original documents mandatory at centre; expired documents rejected; certifier certificates limited to 3-month validity. |
| **DOC_013** | Standard Certifier Certificate Form | All age cohorts lacking primary proofs | Resident Indian | Enrolment & Update | Alternative PoI & PoA | Name, Date of Birth, Address | Standard Alternative Proof | Strictly valid for 3 months from issuance; certifier stamp must overlap photograph; any overwriting renders void. |
| **DOC_001** | Form 1: Adult Enrolment/Update Form | Adults (18 years and above) | Resident Indian & NRI (Indian Address) | Enrolment & Update | Demographic & Biometric | Name, DOB, Gender, Address, Mobile, Email | Standard Adult Update | Requires standard PoI/PoA/PDB proofs; dual-purpose proforma (new enrolment vs demographic update). |
| **DOC_022** | Form 3: Enrolment/Update Form | Minors / Students (5 to 18 years) | Resident Indian & NRI (Indian Address) | Enrolment & Update | Demographic & MBU | Name, DOB, Gender, Address, Parent Linking | Standard Minor Update / MBU | Parent/guardian authentication mandatory; MBU-1 tracked at age 5, MBU-2 at age 15; school marksheet/certificate valid. |
| **DOC_023** | Form 5: Enrolment/Update Form | Infants / Children (Below 5 years) | Resident Indian & NRI (Indian Address) | Enrolment & Update | Demographic only | Child Name, DOB, Gender, Address, Parent Linking | Standard Infant Update | Biometrics not captured; linked to parent Aadhaar via PoR (Birth Certificate); photo only. |
| **DOC_024** | Form 1: Adult Enrolment/Update Variant | Adults (18 years and above) | Resident Indian & NRI (Indian Address) | Enrolment & Update | Demographic & Biometric | Name, DOB, Gender, Address, Mobile, Email | Standard Adult Update | Form 1 variant upload; identical statutory fields to DOC_001. Reference copy. |
| **DOC_025** | Form 4: NRI Child Enrolment/Update | NRI Minors (5 to 18 years) | Non-Resident Indian (Overseas Address) | Enrolment & Update | Demographic & Biometric | Name, DOB, Overseas Address, Passport | NRI Minor Update | Indian passport mandatory; valid overseas address proof required. |
| **DOC_026** | Form 6: NRI Child Enrolment/Update | NRI Infants (Below 5 years) | Non-Resident Indian (Overseas Address) | Enrolment & Update | Demographic only | Child Name, DOB, Overseas Address, Parent Passport | NRI Infant Update | Child Indian passport mandatory; parent passport authentication required. |
| **DOC_027** | Form 7: Resident Foreign National | Adults (18 years and above) | Resident Foreign National | Enrolment & Update | Demographic & Biometric | Name, DOB, Indian Address, Visa, Passport, FRRO | Foreign National Adult Update | Valid foreign passport, Indian visa, and FRRO/FRO permit mandatory; validity tied to visa duration. |
| **DOC_028** | Form 8: Resident Foreign National | Minors (Below 18 years) | Resident Foreign National | Enrolment & Update | Demographic & Biometric | Minor Name, DOB, Indian Address, Parent Visa | Foreign National Minor Update | Valid foreign passport and parent visa/FRRO permit mandatory. |
| **DOC_005** | Email Update Fee Waiver Circular | All mobile app users | All Aadhaar Holders | Mobile App Update | Demographic (Email) | Email Address | Digital Self-Service | Applies exclusively to email updates executed via mAadhaar mobile app till 31.12.2026. |
| **DOC_006** | Digital Verifiable Credential Circular | All verifying entities | All Aadhaar Holders | Electronic Verification | Digital Credential | All demographic fields | Digital Verification | Governs offline verifiable electronic credentials presented via mAadhaar; equal legal standing to physical letters. |
| **DOC_021** | myAadhaar Free Document Update Circular | Citizens with Aadhaar >10 yrs | Resident Indian | Portal Revalidation | PoI & PoA Revalidation | Identity and Address | Online Self-Service | Extends fee waiver for re-validating PoI/PoA on myAadhaar portal through 14.06.2027. |
| **DOC_033** | Aadhaar PVC Card Equivalence Circular | All service providers | All Aadhaar Holders | Physical Presentation | Physical Card | Identity & QR Code | Physical Verification | Establishes full legal equivalence among PVC card, paper letter, e-Aadhaar, and mAadhaar. |
| **DOC_047** | MBU-1 Fee Waiver Circular | Children aged 7 to 15 years | Resident Indian Minors | Mandatory Biometric Update | Biometric (Fingerprints, Iris, Photo) | Biometrics | Enrolment Centre MBU | Fee waiver for children who missed mandatory age-5 biometric update; valid for 1 year w.e.f. 01.10.2025. |

---

## 4. PAN Applicability Metadata & Statutory Separation

The PAN corpus has been strictly partitioned into distinct statutory functions to prevent treating allotment forms as correction procedures:

```
PAN Functional Taxonomy:
├── 1. NEW PAN ALLOTMENT (Rule 158 of Income Tax Rules, 1962)
│   ├── DOC_029: Form No. 93 — Indian Citizen Individuals [REFERENCE ONLY]
│   ├── DOC_030: Form No. 94 — Indian Companies, LLPs, Firms, Trusts [OUT OF SCOPE]
│   ├── DOC_031: Form No. 95 — Non-Citizen Individuals [REFERENCE ONLY]
│   └── DOC_032: Form No. 96 — Foreign Corporate Entities [OUT OF SCOPE]
├── 2. PAN DATA CORRECTION (Section 139A of Income Tax Act, 1961)
│   ├── DOC_036: PAN CR Individual (CSF Form) — [CORE CORRECTION INSTRUMENT]
│   └── DOC_037: PAN CR Non-Individual — [OUT OF SCOPE]
└── 3. PAN-AADHAAR LINKING (Section 139AA of Income Tax Act, 1961)
    └── DOC_004: Aadhaar Seeding Request Form — [CORE CROSS-CATEGORY LINKAGE]
```

### Statutory Scope & Operational Distinctions:
1. **Core Individual Correction (`DOC_036`):**
   - Title: *Request for Changes or Correction in PAN Data [For an Individual]* (CSF Form).
   - Operational Role: **The sole statutory form for individuals seeking to correct errors or update fields on an existing PAN card.**
   - Field Scope: Corrects Name, Father's Name, Date of Birth, Gender, Address, Photo, and Signature. Enforces mandatory quoting of existing PAN and Aadhaar number.
2. **Allotment Proforma as Structural Reference Only (`DOC_029` & `DOC_031`):**
   - Title: *Form No. 93 [Rule 158]* (for Indian citizens) and *Form No. 95 [Rule 158]* (for non-citizens).
   - Operational Role: Application for **initial allotment** of a new PAN.
   - Statutory Restriction: **Must never be used to correct an existing PAN.** Submitting an allotment form when already possessing a PAN violates Section 272B of the Income Tax Act (possessing duplicate PANs carries a statutory Rs. 10,000 penalty).
   - Intended Retrieval Use: Reference-only for statutory personal data definitions (`First Name`, `Middle Name`, `Last Name`, `Name as per Aadhaar`, and Father's/Mother's name conventions).
3. **Aadhaar-PAN Linking Proforma (`DOC_004`):**
   - Title: *Form for Aadhaar seeding into PAN database*.
   - Operational Role: Sworn declaration submitted to manual facilitation counters when online automated seeding fails due to minor demographic discrepancies between Aadhaar and PAN databases under Section 139AA.

---

## 5. Historical Applicability & Statutory Supersession Analysis

The relationship between the Master Name Update SOP (`DOC_043`) and the Exception Handling SOP (`DOC_039`) has been analyzed with exact statutory precision:

### A. Explicit Supersession Language in `DOC_043`
Circular No. `HQ-16024/4/2020-EU-I-HQ` (e-Office `1/58751/2026`) dated `18-09-2026`, signed by `Nikhil Sinha, Director`, states on Page 1, Paragraph 1:
> *"In supersession of the Name update process as described in the Standard Operating Procedure (SOP) of Name & Gender Update Request under Exception Handling Process issued vide F.no. HQ 16022/2/2020-EU-I-HQ-Part(1) on 28.10.2021 [DOC_039], a revised SOP (along with Annexures) is being issued to be followed for carrying out update of name in Aadhaar by an Aadhaar number holder."*

### B. What is Explicitly Superseded in `DOC_039`
1. **Standard Name Update Scenarios & Categories:** The categorization in `DOC_039` Annexure I (Cases 1, 2, 3) is entirely superseded by `DOC_043` Annexure A (Minor Name Change scenarios 1(a)–1(d), Special Cases 4(a)–4(e), and Major Name Change 5(o)).
2. **Proof Requirements for Name Corrections:** Replaced by `DOC_043` Annexure A and `DOC_034`.
3. **Affidavit Formats:** Replaced by `DOC_043` Annexures B, C, D, E, and F.

### C. What Remains Active and Authoritative in `DOC_039`
1. **Lifetime 2-Update Cap:** Established in `DOC_039` Page 2, Para 1(b) (*"up to maximum of two times in life time"*). `DOC_043` references matching against previous names, but `DOC_039` provides the statutory definition of the 2-update cap.
2. **Regional Office (RO) Exception Handling Escalation:** The operational protocol in `DOC_039` Section B (Pages 2–3) and Annexure II for escalating 3rd or subsequent update requests via CRM (calling 1947 or emailing `help@uidai.gov.in`) and submitting the Enrolment ID (EID) to Regional Offices for verification.
3. **Technology Centre Bengaluru Packet Replay:** The backend replay protocol authorized by Regional Offices.
4. **Gender Update Rules:** Section C (Pages 3–4) and Annexure III governing medical certification by a surgeon or government transgender certificate.

### D. Flagged Unresolved Legal Interpretation
* **Quota Consumption for Minor Corrections:** Does a Minor Name Change under `DOC_043` (e.g. expanding initials from `V.S. Prasad` to `Vaddi Venkata Rama Siva Prasad`) consume one of the citizen's two lifetime updates?
  * *Statutory Reality:* Under `DOC_039` Annexure I (Case 2), only typographical/data-entry errors by operators have an explicit provision: *"Count of Update remains 0"*. All other resident-initiated changes consume the lifetime quota unless proven as operator error via sworn Affidavit (Annexure B/C).
  * *CONVELINA Guardrail:* The platform assistant must transparently inform citizens that executing even minor initial/spelling corrections consumes one of their two lifetime updates unless they prove and declare prior operator error.

---

## 6. Manifest Rosters & Approval Boundaries

Four standalone CSV manifests have been generated and deposited into `forms/`:

### A. Manifest 1: [`CORE_CORRECTION_CORPUS_MANIFEST.csv`](file:///c:/Users/ajaya/Desktop/consolin/forms/CORE_CORRECTION_CORPUS_MANIFEST.csv) (8 Documents)
*Active operational instruments defining correction workflows, proof matrix, and application proformas.*

| Document ID | Filename | Authority | Intended Retrieval Use | Approval Status |
| :--- | :--- | :--- | :--- | :---: |
| **DOC_043** | Standard operating Procedure (SOP) to be followed for updating name in Aadhaar.pdf | UIDAI (E&U-I) | Supreme operational rulebook for resolving name discrepancies, spelling mismatches, and statutory affidavits. | `PENDING_USER_APPROVAL` |
| **DOC_034** | List of Acceptable Document for Aadhaar Enrolment and Update English.pdf | UIDAI (E&U) | Supreme proof matrix defining acceptable supporting documents (PoI, PoA, PDB, PoR) across all categories. | `PENDING_USER_APPROVAL` |
| **DOC_013** | Circular_(E&U-II)_Regarding Certificate for Aadhaar Enrolment Update..pdf | UIDAI (E&U-II) | Alternative certifier identity/address verification format for citizens lacking primary documents. | `PENDING_USER_APPROVAL` |
| **DOC_001** | Aadhaar Enrolment And Update Forms English.pdf | UIDAI | Primary application proforma for citizen adult Aadhaar demographic correction (Form 1). | `PENDING_USER_APPROVAL` |
| **DOC_022** | For (a) Resident Indian child, or (b) Non-Resident Indian child (5-18)...pdf | UIDAI | Primary application proforma for student/minor Class 10/12 identity discrepancy resolution (Form 3). | `PENDING_USER_APPROVAL` |
| **DOC_023** | For (a) Resident Indian child, or (b) Non-Resident Indian child (<5)...pdf | UIDAI | Primary application proforma for Bal Aadhaar infant demographic corrections (Form 5). | `PENDING_USER_APPROVAL` |
| **DOC_036** | PAN CR individual_03Nov.pdf | Income Tax Dept / Protean | Primary statutory correction proforma for resolving individual PAN discrepancies against Aadhaar/Passport. | `PENDING_USER_APPROVAL` |
| **DOC_004** | Aadhaar_Seeding_Request_Form.pdf | Income Tax Dept / Protean | Statutory declaration format for resolving demographic mismatches preventing electronic Aadhaar-PAN linking. | `PENDING_USER_APPROVAL` |

---

### B. Manifest 2: [`REFERENCE_ONLY_CORPUS_MANIFEST.csv`](file:///c:/Users/ajaya/Desktop/consolin/forms/REFERENCE_ONLY_CORPUS_MANIFEST.csv) (12 Documents)
*Allotment personal data structures, specialized overseas/foreign forms, and regulatory fee waiver policies.*

| Document ID | Filename | Authority | Scope / Purpose | Intended Retrieval Use | Approval Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **DOC_029** | Form 93.pdf | Income Tax Dept (CBDT) | NEW_PAN_ALLOTMENT | Baseline personal data structure and naming convention reference for Indian individuals. | `PENDING_USER_APPROVAL` |
| **DOC_031** | Form 95_Updated_03Nov.pdf | Income Tax Dept (CBDT) | NEW_PAN_ALLOTMENT | Baseline personal data structure reference for foreign individual taxpayers. | `PENDING_USER_APPROVAL` |
| **DOC_024** | For Resident Indian Adult (18+) English.pdf | UIDAI | Form 1 Adult Variant | Redundant upload of Form 1; reference copy. | `PENDING_USER_APPROVAL` |
| **DOC_025** | For NRI child (5-18) outside India English.pdf | UIDAI | Form 4 NRI Child (5-18) | Reference proforma for overseas minor passport-linked updates. | `PENDING_USER_APPROVAL` |
| **DOC_026** | For NRI child (<5) outside India English.pdf | UIDAI | Form 6 NRI Child (<5) | Reference proforma for overseas infant passport-linked updates. | `PENDING_USER_APPROVAL` |
| **DOC_027** | For Resident Foreign National (18+) English.pdf | UIDAI | Form 7 Foreign Adult | Reference proforma for foreign adult visa/FRRO-linked updates. | `PENDING_USER_APPROVAL` |
| **DOC_028** | For Resident Foreign National (<18) English.pdf | UIDAI | Form 8 Foreign Minor | Reference proforma for foreign minor visa/FRRO-linked updates. | `PENDING_USER_APPROVAL` |
| **DOC_005** | Charges waived off for email update...pdf | UIDAI (E&U-I) | Fee Waiver Circular | Fee exemption rules for email update via mAadhaar mobile app. | `PENDING_USER_APPROVAL` |
| **DOC_006** | Circular 30.04.2026 - Verifiable Credential.pdf | UIDAI (AU) | Credential Policy | Electronic verifiable credential legal standing and presentation rules. | `PENDING_USER_APPROVAL` |
| **DOC_021** | Extension of relaxation in fee charges SSUP.pdf | UIDAI (E&U-I) | Fee Waiver Circular | Free 10-year document update revalidation window on myAadhaar portal. | `PENDING_USER_APPROVAL` |
| **DOC_033** | Introduction of Aadhaar Card PVC.pdf | UIDAI (Logistics) | Format Equivalence | Legal equivalence of PVC card to paper letter, e-Aadhaar, and mAadhaar. | `PENDING_USER_APPROVAL` |
| **DOC_047** | Waiving off charges for MBU-1.pdf | UIDAI (E&U) | Fee Waiver Circular | Fee waiver rules for delayed child biometric update (MBU-1, ages 7-15). | `PENDING_USER_APPROVAL` |

---

### C. Manifest 3: [`HISTORICAL_REFERENCE_MANIFEST.csv`](file:///c:/Users/ajaya/Desktop/consolin/forms/HISTORICAL_REFERENCE_MANIFEST.csv) (9 Documents)
*Historical precedents, Indic translation glossaries, and exception handling protocols.*

| Document ID | Filename | Authority | Historical / Supersession Status | Intended Retrieval Use | Approval Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **DOC_039** | SOP dated 28-10-2021 - Exception SOP.pdf | UIDAI (E&U-I) | Partially superseded by DOC_043; active for RO 3rd+ update escalation and Gender rules. | Procedural authority for citizens who have exhausted their 2-update lifetime limit. | `PENDING_USER_APPROVAL` |
| **DOC_003** | Aadhaar Handbook For Residents Tamil.pdf | UIDAI | Official Tamil translation of Resident Handbook 2021. | Tamil linguistic grounding for citizen translation and explanation validation. | `PENDING_USER_APPROVAL` |
| **DOC_038** | Resident Handbook English 2021.pdf | UIDAI | Citizen guidance handbook from 2021; procedural details updated by DOC_043. | Resident guidance concepts, service definitions, and historical glossary. | `PENDING_USER_APPROVAL` |
| **DOC_011** | Circular_(E&U-I)_Expansion Modification.pdf | UIDAI (E&U-I) | 2016 circular amending Schedule II; subsumed by Proof Matrix DOC_034. | Historical precedent establishing statutory basis for accepting PAN for DOB. | `PENDING_USER_APPROVAL` |
| **DOC_010** | Circular_(DBT)_Section 7 State Govts.pdf | Cabinet Sect / UIDAI | 2017 OM on drafting state welfare scheme notifications under Section 7. | Statutory context for welfare scheme identity verification requirements. | `PENDING_USER_APPROVAL` |
| **DOC_016** | Circular_(Legal)_Exception handling PDS.pdf | UIDAI (Legal) | 2017 directive prohibiting denial of ration/subsidies due to biometric failure. | Precedent establishing citizen right to alternate manual verification. | `PENDING_USER_APPROVAL` |
| **DOC_017** | Circular_(Legal)_Regulation 12A Gazette.pdf | UIDAI / MeitY | Extraordinary Gazette No. 4353 GI/17; modified by Supreme Court Puttaswamy ruling. | Statutory milestone for mandatory identity linkage frameworks. | `PENDING_USER_APPROVAL` |
| **DOC_019** | Circular_(Legal)_Section 7 Targeted Delivery.pdf | UIDAI (Legal) | 2017 circular guiding ministries on Section 7 notification criteria. | Statutory reference on welfare eligibility and non-exclusion mandates. | `PENDING_USER_APPROVAL` |
| **DOC_009** | Circular_(DBT)_NRIPIOsOCIs.pdf | UIDAI / DBT Mission | 2017 advisory on NRI/PIO/OCI exemption from mandatory domestic Aadhaar. | Precedent clarifying non-resident exemption from mandatory Aadhaar linking. | `PENDING_USER_APPROVAL` |

---

### D. Complete Master Applicability Ledger: [`DOCUMENT_APPLICABILITY_MATRIX.csv`](file:///c:/Users/ajaya/Desktop/consolin/forms/DOCUMENT_APPLICABILITY_MATRIX.csv) (47 Documents)
*Defines exact demographic, cohort, procedural, and approval statuses for all 47 files in the repository.*

Summary of Excluded Documents:
- **Exact Duplicates (2 Documents):** `DOC_035` (duplicate of `DOC_034`), `DOC_040` (duplicate of `DOC_041`) -> **`EXCLUDED_FROM_PREPROCESSING`**.
- **Out of Scope (15 Documents):** Operator testing policies (`DOC_041`, `DOC_042`, `DOC_046`), operator disincentives/penalties (`DOC_007`, `DOC_008`), school admissions (`DOC_012`), aviation requesting entities (`DOC_014`), AePS banking/e-KYC (`DOC_015`, `DOC_018`), Fintech brochure (`DOC_020`), corporate PAN allotment/correction (`DOC_030`, `DOC_032`, `DOC_037`), and internal office drives (`DOC_044`, `DOC_045`) -> **`EXCLUDED_FROM_PREPROCESSING`**.
- **Unverified Material (1 Document):** Azam Khan slide deck (`DOC_002`) -> **`EXCLUDED_FROM_PREPROCESSING`**.

---

## 7. Deliverables & Brain Artifacts

All required manifests and reports have been generated and cross-copied to the conversation brain directory:

| Workspace File | Brain Artifact Link | Description |
| :--- | :--- | :--- |
| [`forms/CORE_CORRECTION_CORPUS_MANIFEST.csv`](file:///c:/Users/ajaya/Desktop/consolin/forms/CORE_CORRECTION_CORPUS_MANIFEST.csv) | [CORE_CORRECTION_CORPUS_MANIFEST](file:///C:/Users/ajaya/.gemini/antigravity/brain/3b1f54ae-b77b-431b-9705-cd8ba1713a42/CORE_CORRECTION_CORPUS_MANIFEST.csv) | 8 active core correction instruments with intended retrieval use. |
| [`forms/REFERENCE_ONLY_CORPUS_MANIFEST.csv`](file:///c:/Users/ajaya/Desktop/consolin/forms/REFERENCE_ONLY_CORPUS_MANIFEST.csv) | [REFERENCE_ONLY_CORPUS_MANIFEST](file:///C:/Users/ajaya/.gemini/antigravity/brain/3b1f54ae-b77b-431b-9705-cd8ba1713a42/REFERENCE_ONLY_CORPUS_MANIFEST.csv) | 12 reference-only documents (allotment proformas, specialized forms, fee waivers). |
| [`forms/HISTORICAL_REFERENCE_MANIFEST.csv`](file:///c:/Users/ajaya/Desktop/consolin/forms/HISTORICAL_REFERENCE_MANIFEST.csv) | [HISTORICAL_REFERENCE_MANIFEST](file:///C:/Users/ajaya/.gemini/antigravity/brain/3b1f54ae-b77b-431b-9705-cd8ba1713a42/HISTORICAL_REFERENCE_MANIFEST.csv) | 9 historical reference documents with supersession details and glossary scope. |
| [`forms/DOCUMENT_APPLICABILITY_MATRIX.csv`](file:///c:/Users/ajaya/Desktop/consolin/forms/DOCUMENT_APPLICABILITY_MATRIX.csv) | [DOCUMENT_APPLICABILITY_MATRIX](file:///C:/Users/ajaya/.gemini/antigravity/brain/3b1f54ae-b77b-431b-9705-cd8ba1713a42/DOCUMENT_APPLICABILITY_MATRIX.csv) | Exhaustive 47-row applicability matrix covering all demographic cohorts and limits. |
| [`forms/P3H1_2_FINAL_SCOPE_REPORT.md`](file:///c:/Users/ajaya/Desktop/consolin/forms/P3H1_2_FINAL_SCOPE_REPORT.md) | [P3H1_2_FINAL_SCOPE_REPORT](file:///C:/Users/ajaya/.gemini/antigravity/brain/3b1f54ae-b77b-431b-9705-cd8ba1713a42/P3H1_2_FINAL_SCOPE_REPORT.md) | Master Phase P3H.1.2 final scope, reconciliation, and applicability report. |

---

## 8. Explicit Approval Request

In strict compliance with Phase P3H.1.2 rules, **no documents have been approved automatically, no embeddings have been generated, and no Qdrant ingestion has taken place.**

The 29 candidate documents are divided into three clearly bounded manifests:
1. **Core Correction Manifest:** 8 documents (`DOC_001`, `DOC_004`, `DOC_013`, `DOC_022`, `DOC_023`, `DOC_034`, `DOC_036`, `DOC_043`)
2. **Reference-Only Manifest:** 12 documents (`DOC_005`, `DOC_006`, `DOC_021`, `DOC_024`, `DOC_025`, `DOC_026`, `DOC_027`, `DOC_028`, `DOC_029`, `DOC_031`, `DOC_033`, `DOC_047`)
3. **Historical Reference Manifest:** 9 documents (`DOC_003`, `DOC_009`, `DOC_010`, `DOC_011`, `DOC_016`, `DOC_017`, `DOC_019`, `DOC_038`, `DOC_039`)

**Next Action:** Awaiting your explicit approval of these manifests before proceeding to corpus pre-processing or RAG ingestion. Which manifests or document subsets would you like to approve for Phase P3H.2? Additionally, please advise on whether you wish to supply official files for the four missing categories (`Passport`, `Class 10`, `Class 12`, `EPFO/UAN`).

*(Note: You can view and interact with the live platform at any time at [http://localhost:3000](http://localhost:3000).)*

<hr />
<br />
<div align="center">
  <b>Suggested Developer Tool:</b> To inspect and manage background automations or recurring jobs, you can use the <code>/automation</code> slash command.
</div>
<br />

<div align="center">
  <b>Marketplace Recommendations:</b><br />
  If your upcoming phases require deep document scanning, verification, or collaborative documentation management:
  <br /><br />
  For syncing and managing official government circulars, forms, and project documentation across your team:
  <br />
  <plugin-card catalog-id="antigravity-plugins-official/plugin/gdocs"></plugin-card>
  <br />
  For automated PDF, spreadsheet, and statutory checklist auditing:
  <br />
  <plugin-card catalog-id="antigravity-plugins-official/plugin/gsheets"></plugin-card>
</div>
