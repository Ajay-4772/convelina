"""
Authoritative Indian Government Procedures and Official Forms Catalog.
Verified guidelines and procedural requirements from:
- UIDAI (Aadhaar)
- Income Tax Department / NSDL (PAN)
- Ministry of External Affairs (Passport Seva)
- EPFO (Employees' Provident Fund Organisation)
- Central Board of Secondary Education (CBSE)
"""

from typing import List, Dict, Any

OFFICIAL_SOURCES_DATA: List[Dict[str, Any]] = [
    {
        "source_id": "src_uidai_update_policy_2024",
        "title": "UIDAI Aadhaar Enrolment and Update Standard Operating Procedure",
        "issuing_authority": "Unique Identification Authority of India (UIDAI)",
        "document_type": "standard_operating_procedure",
        "document_category": "aadhaar",
        "source_url": "https://uidai.gov.in/en/my-aadhaar/update-aadhaar.html",
        "jurisdiction": "India",
        "language": "en",
        "effective_date": "2024-01-01T00:00:00Z",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "version": "SOP-2024-V2",
        "verification_status": "verified",
        "is_active": True,
        "content": """
# UIDAI Aadhaar Correction and Update Guidelines

### 1. Name Correction in Aadhaar
- A resident can update/correct their name in Aadhaar up to a maximum of TWO (2) times in their entire lifetime.
- Minor spelling corrections or changes in format (e.g. expanding initials to full name or vice-versa) can be updated online or at an Aadhaar Seva Kendra with valid Proof of Identity (POI).
- Acceptable POI documents include: Passport, PAN Card, Voter ID, Driving License, or School/Board Certificate with photograph.
- Complete/Major Name Change requires: Prior publication of name change in the Official Gazette of India alongside newspaper advertisements and the original gazette copy.

### 2. Date of Birth (DOB) Correction in Aadhaar
- Date of birth can be updated ONLY ONCE in a lifetime.
- Permitted Range: Discrepancy up to +/- 3 years from the recorded date can be updated at any Aadhaar Seva Kendra by submitting an authentic birth certificate or matriculation certificate.
- Mandatory Proof of Date of Birth (PDB) documents: Birth Certificate issued by Municipal Corporation/Registrar of Births, Indian Passport, or Matriculation Marksheet/Certificate issued by a recognized Board/University.
- Year-Only Recorded DOB: If Aadhaar displays only the birth year (e.g. 1988) and full date (DD/MM/YYYY) is required, the full date can be recorded with an acceptable PDB document without consuming the lifetime DOB correction limit.
- DOB Exception Cases: Any correction exceeding 3 years difference or beyond the one-time limit requires exceptional approval from the UIDAI Regional Office with an affidavit.

### 3. Gender Correction in Aadhaar
- Gender update is permitted ONLY ONCE in a lifetime.
- Can be done at an Aadhaar Seva Kendra with standard resident declaration or medical certificate where applicable.

### 4. Supporting Document Requirements & Form
- The resident must fill the 'Aadhaar Enrolment / Update Form (Adults 18+)' and present original documents for physical scanning. No photocopies without originals are accepted.
- Application portal: https://myaadhaar.uidai.gov.in
"""
    },
    {
        "source_id": "src_pan_correction_nsdl_2024",
        "title": "Income Tax Department / NSDL Guidelines for Changes or Correction in PAN Data",
        "issuing_authority": "Income Tax Department / Protean (NSDL e-Gov)",
        "document_type": "guideline",
        "document_category": "pan",
        "source_url": "https://www.tin-nsdl.com/services/pan/pan-change-correction.html",
        "jurisdiction": "India",
        "language": "en",
        "effective_date": "2023-04-01T00:00:00Z",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "version": "PAN-CSF-2024",
        "verification_status": "verified",
        "is_active": True,
        "content": """
# PAN Card Data Correction and Update Guidelines (Form 49A / CSF)

### 1. PAN Data Correction Overview
- Any existing PAN holder requiring correction in Name, Father's Name, Date of Birth, or Signature must submit the 'Request For New PAN Card Or/ And Changes Or Correction in PAN Data' (commonly referred to as the CSF Form).
- A citizen must NEVER apply for a new PAN card if they already possess one; possessing more than one PAN is an offense under Section 272B of the Income Tax Act with a penalty of Rs 10,000.

### 2. Name Correction Procedure in PAN
- Minor Typographical/Spelling Correction: Submit copy of existing PAN card alongside Proof of Identity (POI) reflecting the correct name (e.g., Aadhaar Card, Passport, or Matriculation Certificate).
- Major Name Change (All citizens): Requires copy of Official Government Gazette Notification publishing the change in name.
- Name Change due to Marriage: Female applicants changing surname post-marriage can submit Marriage Certificate, Marriage Invitation card, or copy of Husband's passport along with self-declaration.

### 3. Date of Birth (DOB) Correction in PAN
- The date of birth on PAN must match official municipal records.
- Acceptable Proof of Date of Birth (PDB) documents:
  - Birth Certificate issued by Registrar of Births and Deaths
  - Matriculation Certificate of recognized Board
  - Passport of the applicant
  - Driving License or Aadhaar Card
- The date of birth entered in the CSF form must exactly match the supporting PDB document.

### 4. Father's Name Correction in PAN
- Father's name is an essential identifier on Indian PAN cards even for married women. Mother's name can be chosen optionally if single parent.
- Proof required: Birth certificate, passport, or school certificate showing correct parentage.

### 5. Application Modes
- Paperless Online Application: Using Aadhaar-based e-KYC and e-Sign on the Protean (NSDL) or UTIITSL portal.
- Physical Form Submission: Download CSF Form, affix two passport-size photographs, cross-sign, attach self-attested document copies, and submit to nearest TIN-FC center.
"""
    },
    {
        "source_id": "src_passport_reissue_mea_2024",
        "title": "Ministry of External Affairs Passport Seva Re-issue Manual for Change in Particulars",
        "issuing_authority": "Ministry of External Affairs, Government of India (CPV Division)",
        "document_type": "manual",
        "document_category": "passport",
        "source_url": "https://www.passportindia.gov.in/AppOnlineProject/online/faqServicesAvailable",
        "jurisdiction": "India",
        "language": "en",
        "effective_date": "2023-01-01T00:00:00Z",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "version": "PSP-SOP-V4",
        "verification_status": "verified",
        "is_active": True,
        "content": """
# Ministry of External Affairs — Passport Re-Issue for Correction in Personal Particulars

### 1. Categories of Name Change in Passport
- Minor Name Change / Spelling Correction: Where the spelling difference does not phonetically alter the name, or change involves minor surname addition consistent with parentage. Requires self-attested copies of at least two public identity documents in the correct name.
- Major Name Change: Substantial alteration of first name, addition of unrelated surname, or total change of name.
  - Requirement: Prior publication in two prominent daily newspapers (one local circulated at permanent address, one at present address) AND publication in the Official Gazette of India.
  - Applicant must submit Annexure 'E' (Deed Poll/Sworn Affidavit for Change of Name).

### 2. Date of Birth (DOB) Correction in Indian Passport
- As per MEA circulars, if an applicant applies for correction in DOB within 5 years of issuance of the first passport:
  - Applicant must produce a valid Municipal Birth Certificate or School Leaving Certificate issued prior to passport issuance.
- If correction is sought after more than 5 years from issuance:
  - The Passport Issuing Authority (PIA) conducts detailed inquiry. If substantial discrepancy exists, an order from the Judicial First Class Magistrate or competent civil court having jurisdiction may be required.

### 3. Parent's Name Correction
- Minor typographical errors can be rectified by providing parents' passport copies or applicant's Class 10 education certificate.
- Major change in parent's name requires court decree or parent's gazette notification.

### 4. Application Process
- Complete the online application for 'Re-issue of Passport' on https://www.passportindia.gov.in.
- Pay the requisite government fee and book an appointment at the nearest Passport Seva Kendra (PSK) or Post Office PSK (POPSK).
- Carry original old passport alongside all supporting documents for biometric verification.
"""
    },
    {
        "source_id": "src_epfo_joint_declaration_2024",
        "title": "EPFO Standard Operating Procedure for Profile Updates and Joint Declaration",
        "issuing_authority": "Employees' Provident Fund Organisation (EPFO)",
        "document_type": "standard_operating_procedure",
        "document_category": "epf",
        "source_url": "https://www.epfindia.gov.in/site_docs/PDFs/Circulars/Y2023-2024/Joint_Declaration_SOP_2023.pdf",
        "jurisdiction": "India",
        "language": "en",
        "effective_date": "2023-08-23T00:00:00Z",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "version": "EPFO-JD-SOP-2023",
        "verification_status": "verified",
        "is_active": True,
        "content": """
# EPFO Guidelines for Member Details Correction via Joint Declaration

### 1. Joint Declaration Overview
- Inconsistencies between EPF Member Records (UAN profile) and Aadhaar/PAN prevent PF balance withdrawals, transfer requests, and pension claims.
- The Joint Declaration Form is an official application submitted jointly by the employee (member) and employer to the jurisdictional EPF Field Office.

### 2. Name and Father's Name Correction in EPF
- Minor Correction (less than 2 characters or spelling variation): Can be submitted through the Employer's digital signature on the Member Portal with Aadhaar copy.
- Major Correction: When name in EPF is completely different from Aadhaar, member must submit:
  - Physical or digital Joint Declaration signed by employee and authorized employer signatory.
  - Three supporting documents: Aadhaar card (mandatory), PAN card, and any of (Passport / School Certificate / Driving License).

### 3. Date of Birth (DOB) Correction in EPF
- Difference up to 3 years: Member can update DOB directly on the EPFO Unified Member Portal by linking verified Aadhaar.
- Difference greater than 3 years: Requires supporting documentation uploaded on portal:
  - Municipal Birth Certificate
  - School / Education Board Certificate or Marksheet
  - Indian Passport or Government Medical Board Certificate.
  - Employer verification and approval is mandatory before EPFO Regional Office processes the change.

### 4. UAN and Aadhaar Seeding Rule
- Section 142 of Code on Social Security mandates Aadhaar seeding for EPF contributions and benefits.
- If Aadhaar details (Name, DOB, Gender) do not match EPF records exactly, electronic linking will fail with error 'Aadhaar demographic mismatch'.
"""
    },
    {
        "source_id": "src_cbse_name_correction_byelaws_2024",
        "title": "CBSE Examination Bye-Laws for Correction and Change in Name and Date of Birth",
        "issuing_authority": "Central Board of Secondary Education (CBSE)",
        "document_type": "regulation",
        "document_category": "education",
        "source_url": "https://www.cbse.gov.in/newsite/examination-bye-laws.html",
        "jurisdiction": "India",
        "language": "en",
        "effective_date": "2022-06-01T00:00:00Z",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "version": "CBSE-EBL-Rule-69",
        "verification_status": "verified",
        "is_active": True,
        "content": """
# CBSE Examination Bye-Laws — Correction in Candidate Name, Parents' Name, and Date of Birth

### 1. Correction in Spelling of Name (Rule 69.1(i))
- Applications for correction in surname or name spelling of candidate/father/mother are considered if the proposed correction conforms to the candidate's school admission records.
- Time Limit: Applications must be forwarded through the Head of School within FIVE (5) years of the declaration of examination results.
- Documents Required:
  - School admission form and school withdrawal/leaving register extracts duly certified by principal.
  - Prescribed fee and application form addressed to Regional Officer.

### 2. Change in Name (Rule 69.1(ii))
- Changes in name or surname from what was originally recorded in school records can only be considered if:
  - The change was admitted by a Court of Law or published in the Official Gazette of India prior to final examination, OR
  - Under specific Supreme Court of India guidelines (Jigya Yadav vs CBSE), where name change is permitted based on subsequent gazette notification and public identity document updates upon payment of penalty fees.

### 3. Date of Birth Correction in Class 10 Certificate (Rule 69.2)
- No change in the date of birth once recorded in Board certificates is permitted after examination, EXCEPT for rectifying clerical/typographical errors made by the Board/school that contradict the original school admission register.
- Request must be submitted through the School Principal within five years of result declaration accompanied by the original school admission register extract.
"""
    }
]

OFFICIAL_FORMS_DATA: List[Dict[str, Any]] = [
    {
        "form_id": "form_epf_joint_declaration",
        "form_name": "EPFO Joint Declaration Form (Member & Employer)",
        "document_category": "epf",
        "purpose": "Correction or updating of Member Name, Father's Name, Date of Birth, Date of Joining, and Gender in EPF/UAN records",
        "issuing_authority": "Employees' Provident Fund Organisation (EPFO)",
        "official_download_url": "https://www.epfindia.gov.in/site_docs/PDFs/Downloads_PDFs/Joint_Declaration_Form.pdf",
        "instructions_source_id": "src_epfo_joint_declaration_2024",
        "applicable_issue_types": ["full_name", "date_of_birth", "father_name", "gender"],
        "applicable_conditions": [
            "Must be signed jointly by both employee and authorized employer signatory",
            "Must be submitted to the jurisdictional EPF Field Office",
            "Must be accompanied by self-attested copy of Aadhaar and PAN"
        ],
        "language": "en",
        "version": "JD-2023",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "verification_status": "verified",
        "is_active": True
    },
    {
        "form_id": "form_pan_csf_correction",
        "form_name": "Request for New PAN Card Or/And Changes or Correction in PAN Data (CSF Form)",
        "document_category": "pan",
        "purpose": "Official application to rectify discrepancies in Name, Date of Birth, or Father's Name on an existing PAN card",
        "issuing_authority": "Income Tax Department / Protean (NSDL)",
        "official_download_url": "https://www.tin-nsdl.com/downloads/pan/download/Request-for-New-PAN-Card-or-and-Changes-or-Correction-in-PAN-Data-Form.pdf",
        "instructions_source_id": "src_pan_correction_nsdl_2024",
        "applicable_issue_types": ["full_name", "date_of_birth", "father_name"],
        "applicable_conditions": [
            "Applicant must specify existing 10-character PAN number",
            "Do not apply for a new PAN card if you already possess one",
            "Tick only the specific checkboxes corresponding to the fields requiring change"
        ],
        "language": "en",
        "version": "CSF-Rev-2023",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "verification_status": "verified",
        "is_active": True
    },
    {
        "form_id": "form_aadhaar_update_adult",
        "form_name": "Aadhaar Enrolment and Update Form (Adult 18+ Years)",
        "document_category": "aadhaar",
        "purpose": "Correction or updating of Name, Date of Birth, Gender, Address, or Biometrics in Aadhaar database",
        "issuing_authority": "Unique Identification Authority of India (UIDAI)",
        "official_download_url": "https://uidai.gov.in/images/aadhaar_enrolment_update_form_adult.pdf",
        "instructions_source_id": "src_uidai_update_policy_2024",
        "applicable_issue_types": ["full_name", "date_of_birth", "gender"],
        "applicable_conditions": [
            "Must be presented at an authorized Aadhaar Seva Kendra with original POI/PDB documents",
            "Name correction subject to 2-times lifetime limit",
            "DOB correction subject to 1-time lifetime limit"
        ],
        "language": "en",
        "version": "UIDAI-ENR-2024",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "verification_status": "verified",
        "is_active": True
    },
    {
        "form_id": "form_passport_reissue",
        "form_name": "Application for Re-issue of Indian Passport (Passport Seva)",
        "document_category": "passport",
        "purpose": "Application for re-issuance of passport due to change in Personal Particulars (Name, DOB, Parentage)",
        "issuing_authority": "Ministry of External Affairs (CPV Division)",
        "official_download_url": "https://www.passportindia.gov.in/AppOnlineProject/online/printForm",
        "instructions_source_id": "src_passport_reissue_mea_2024",
        "applicable_issue_types": ["full_name", "date_of_birth", "father_name", "gender"],
        "applicable_conditions": [
            "Applicant must apply online on the official Passport Seva portal",
            "Major name change requires Annexure 'E' and Gazette Notification copy",
            "Physical biometric verification at PSK is mandatory"
        ],
        "language": "en",
        "version": "PSP-REISSUE-2024",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "verification_status": "verified",
        "is_active": True
    },
    {
        "form_id": "form_passport_annexure_e",
        "form_name": "Annexure 'E' — Deed Poll / Sworn Affidavit for Change in Name",
        "document_category": "passport",
        "purpose": "Mandatory affidavit format for Indian passport re-issue involving major name change or significant spelling changes",
        "issuing_authority": "Ministry of External Affairs",
        "official_download_url": "https://www.passportindia.gov.in/AppOnlineProject/pdf/AnnexureE.pdf",
        "instructions_source_id": "src_passport_reissue_mea_2024",
        "applicable_issue_types": ["full_name"],
        "applicable_conditions": [
            "Must be executed on non-judicial stamp paper of prescribed value",
            "Must be attested by a First Class Judicial Magistrate or Notary Public",
            "Must accompany two original newspaper cuttings publishing the change of name"
        ],
        "language": "en",
        "version": "ANNEXURE-E-2023",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "verification_status": "verified",
        "is_active": True
    },
    {
        "form_id": "form_cbse_name_correction",
        "form_name": "CBSE Application Form for Correction in Candidate / Parents' Name or DOB",
        "document_category": "education",
        "purpose": "Application to correct clerical/typographical discrepancies in Class 10 or 12 Certificates",
        "issuing_authority": "Central Board of Secondary Education (CBSE)",
        "official_download_url": "https://www.cbse.gov.in/newsite/forms.html",
        "instructions_source_id": "src_cbse_name_correction_byelaws_2024",
        "applicable_issue_types": ["full_name", "date_of_birth", "father_name"],
        "applicable_conditions": [
            "Must be submitted through the Head of the School from which candidate appeared",
            "Must be within 5 years of examination result declaration",
            "Correction must strictly conform to school admission register records"
        ],
        "language": "en",
        "version": "CBSE-CORR-2023",
        "last_verified_at": "2026-09-01T00:00:00Z",
        "verification_status": "verified",
        "is_active": True
    }
]
