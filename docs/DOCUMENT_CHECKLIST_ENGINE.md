# CONVELINA — Supporting-Document Checklist Engine Specification

## 1. Architectural Mission & Philosophy

When citizens attempt to rectify cross-document identity conflicts, a primary cause of rejection at government enrollment counters (UIDAI, ITD, Passport Seva Kendras, EPFO, CBSE) is incomplete or non-statutory supporting documentation.

The **Supporting-Document Checklist Engine** (`backend/app/services/checklist_service.py`) provides citizens with verified, evidence-backed documentary checklists tailored to each specific correction procedure.

### The Non-Equivalence Principle
> **Statutory Rule**: A recommended supporting document must never be transformed into a mandatory requirement, and an optional evidence route must never be falsely presented as obligatory. Furthermore, checklist completion by a citizen is an informational preparation mechanism and **never constitutes official government approval or successful statutory correction**.

---

## 2. Requirement Status Differentiation

The engine enforces four distinct requirement statuses derived directly from authoritative gazette notifications:

| Requirement Status | Operational Definition | Citizen Guidance Meaning |
| :--- | :--- | :--- |
| `VERIFIED_MANDATORY` | Explicitly mandated by statute, regulation, or departmental rule (e.g., existing PAN copy for CSF correction, Gazette Notification for major Aadhaar name change). | Without this document, the government portal or processing officer will reject the application immediately. |
| `VERIFIED_CONDITIONAL` | Required only if specific factual conditions are met (e.g., Marriage Certificate in case of female surname change upon marriage, Court Decree for legal adoption). | Citizen must inspect whether their specific factual scenario triggers this condition. |
| `RECOMMENDED` | Helpful secondary evidence recognized by departmental guidelines to accelerate verification or resolve edge cases (e.g., Class 10 mark sheet as secondary age proof). | Helpful to produce, but application cannot be lawfully rejected solely for lack of this document if an alternative primary document is furnished. |
| `HUMAN_REVIEW_REQUIRED` | Involves discretionary administrative scrutiny, regional office exception approvals, or special magistrate attestations (e.g., UIDAI RO escalation, affidavit under notary). | Citizen is explicitly alerted that human counter/officer verification is compulsory. |

---

## 3. Statutory Checklist Specifications Across 6 Categories

### 3.1. Aadhaar Card (`aadhaar`)

#### A. Standard Name Update (`aadhaar_name_update`)
- **Authority**: UIDAI Demographic Update SOP
- **Mandatory**: Standard Proof of Identity (PoI) bearing applicant's photograph and exact corrected name (Passport, PAN Card, Voter ID, Driving Licence).
- **Conditional**: Marriage Certificate (for post-marriage surname change).
- **Recommended**: Previous Aadhaar acknowledgement slip.
- **Human Review**: Mandatory biometric verification at UIDAI Aadhaar Seva Kendra (ASK).

#### B. Major Name Change via Gazette (`aadhaar_name_update_major_gazette`)
- **Authority**: UIDAI Notification on Extraordinary Name Changes
- **Mandatory**: Original copy of the Central Government Gazette Notification certifying legal name change.
- **Mandatory**: Newspaper advertisements (one English daily and one vernacular daily) announcing name change.
- **Conditional**: Marriage certificate or deed poll affidavit executed before a Judicial Magistrate.
- **Human Review**: Regional Office exception review.

#### C. Date of Birth Update (`aadhaar_dob_update`)
- **Authority**: UIDAI Regulation 10 on Date of Birth Rectification
- **Mandatory**: Birth Certificate issued by Municipal Corporation / Registrar of Births OR Class 10 Pass Certificate / Mark Sheet with DoB.
- **Limitation Warning**: Strictly limited to a single update in an individual's lifetime.

#### D. Address Update (`aadhaar_address_update`)
- **Authority**: UIDAI Proof of Address Matrix
- **Mandatory**: Valid Proof of Address (PoA) in applicant's name (Passport, Electricity Bill under 3 months, Bank Passbook with photo, Rent Agreement registered).

---

### 3.2. PAN Card (`pan`)

#### PAN Name & Data Correction (`pan_name_correction_csf`)
- **Authority**: Income Tax Rules 1962, Rule 114 / Form 49A CSF Guidelines
- **Mandatory**: Copy of Existing PAN Card or PAN Allotment Letter.
- **Mandatory**: Proof of Identity reflecting corrected name (Aadhaar Card, Passport, or Elector's Photo ID).
- **Mandatory**: Proof of Address reflecting current residence.
- **Conditional**: Gazette publication copy if full name is altered substantially.
- **Online Channel**: Available digitally via Protean (NSDL) / UTIITSL paperless e-Sign.

---

### 3.3. Passport (`passport`)

#### Passport Reissue under Name Change / Correction (`passport_reissue_correction`)
- **Authority**: Ministry of External Affairs Passport Rules 1980 & Passport Manual
- **Mandatory**: Original Old / Existing Passport with self-attested photocopies of first two and last two pages.
- **Mandatory**: Annexure E Deed Poll Affidavit on non-judicial stamp paper affirming name change.
- **Mandatory**: Clippings of two leading daily newspaper advertisements announcing name change.
- **Conditional**: Gazette publication if change of name is major/unrelated to marriage.
- **Human Review**: Compulsory appointment at Passport Seva Kendra (PSK) for biometric capture and document scrutiny.

---

### 3.4. Class 10 Certificate (`class_10`)

#### High School Credential Name / DoB Rectification (`class_10_name_correction`)
- **Authority**: CBSE Examination Byelaws, Rule 69.1 / State Secondary Board Rules
- **Mandatory**: Formal application endorsed by the Head of the School last attended.
- **Mandatory**: Certified extract of the School Admission and Withdrawal Register showing original enrollment details.
- **Mandatory**: Central Gazette Notification copy published prior to or following board examination.
- **Conditional**: Court Decree from a court of competent jurisdiction if timeline exceeds statutory petition limit.
- **Human Review**: Scrutiny by CBSE Regional Examination Committee.

---

### 3.5. Class 12 Certificate (`class_12`)

#### Senior Secondary Credential Rectification (`class_12_name_correction`)
- **Authority**: CBSE Examination Byelaws, Rule 69.1(ii)
- **Mandatory**: Class 10 Original Certificate and Mark Sheet reflecting baseline verified name and parentage.
- **Mandatory**: Principal's forwarding letter and school record concordance certificate.
- **Mandatory**: Gazette publication establishing public notification of corrected identity.

---

### 3.6. EPF/UAN Records (`epf`)

#### EPFO Member Profile Alignment (`epf_joint_declaration`)
- **Authority**: EPFO Circular on Standard Operating Procedure for Joint Declaration
- **Mandatory**: Joint Declaration Form duly filled and signed by both the employee and the authorized signatory of the employer.
- **Mandatory**: Self-attested copy of Aadhaar Card seeded with active mobile number.
- **Mandatory**: Copy of PAN Card (mandatory for claims exceeding statutory thresholds).
- **Mandatory**: Cancelled cheque or bank passbook copy showing bank account seeded with UAN.
- **Conditional**: Letter of resignation / appointment letter if father's name or date of joining requires revision.

---

## 4. Reusable API Contract

The checklist engine is accessible through standardized REST endpoints:

- `GET /api/v1/repository/checklists/{procedure_id}`: Retrieves evidence-backed checklist for a specific procedure.
- `GET /api/v1/repository/checklists/category/{category}`: Aggregates all checklists applicable to a specific identity category.
- `RepositoryResourceDetail.supporting_document_checklist`: Embedded directly into document detail responses.

