import logging
from typing import List, Dict, Any, Optional
from app.rag.schemas import (
    ChecklistItem,
    ChecklistResponse,
    RequirementStatus,
)

logger = logging.getLogger("convelina.checklist.service")

# ---------------------------------------------------------------------------
# Authoritative Statutory Checklists Definition
# Grounded in reconciled official documents:
# DOC_034: UIDAI Acceptable Supporting Documents (Proof of Identity, Address, DOB, Relationship)
# DOC_001: Aadhaar Enrolment & Update Form (Adult)
# DOC_013: Certificate for Aadhaar Enrolment/Update & Exception Guidelines
# DOC_022 / DOC_023: Child & Bal Aadhaar Forms
# DOC_036: Income Tax Form CSF (Request for Changes/Correction in PAN Data)
# DOC_043: UIDAI SOP for Updating Name in Aadhaar (with statutory conflict notice)
# Official MEA Passport Seva Rules, CBSE Byelaws, and EPFO Joint Declaration Circulars
# ---------------------------------------------------------------------------

STATUTORY_CHECKLISTS: Dict[str, Dict[str, Any]] = {
    # -----------------------------------------------------------------------
    # 1. AADHAAR PROCEDURES
    # -----------------------------------------------------------------------
    "aadhaar_name_update": {
        "title": "Aadhaar Name Update (Clerical & Minor Correction)",
        "category": "aadhaar",
        "procedure_id": "aadhaar_name_update",
        "description": "Evidence requirements for correcting typographical spelling errors, expanding initials, or minor adjustments in resident Aadhaar name.",
        "items": [
            ChecklistItem(
                requirement_id="REQ_AAD_NAME_POI_01",
                title="Proof of Identity (PoI) Document",
                description="Original document from UIDAI's verified list containing resident's photograph and exact intended legal name.",
                category="aadhaar",
                procedure_id="aadhaar_name_update",
                supporting_source_id="DOC_034",
                supporting_source_title="List of Acceptable Supporting Documents for Aadhaar Enrolment & Update",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="UIDAI rules require at least one valid, unexpired Proof of Identity document (e.g. Passport, PAN Card, Ration Card, Voter ID, or Driving License).",
                source_citation="DOC_034, Section 1 (Table 1: Supported PoI Documents)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_AAD_NAME_FORM_02",
                title="Aadhaar Enrolment and Update Form (Form 1)",
                description="Duly completed official enrolment and update form with applicant signature or thumb impression.",
                category="aadhaar",
                procedure_id="aadhaar_name_update",
                supporting_source_id="DOC_001",
                supporting_source_title="Aadhaar Enrolment and Update Forms (Adult Resident)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Prescribed statutory form required at all authorized Aadhaar Seva Kendras (ASK) or enrolment centers.",
                source_citation="DOC_001, Form 1 (Adult Resident 18+ Years)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_AAD_NAME_AADHAAR_COPY_03",
                title="Existing Aadhaar Card or Enrolment Acknowledgement",
                description="Physical copy or printout of existing Aadhaar letter / masked e-Aadhaar showing 12-digit UID or 28-digit EID.",
                category="aadhaar",
                procedure_id="aadhaar_name_update",
                supporting_source_id="DOC_033",
                supporting_source_title="Introduction of Aadhaar Card at par with other forms of Aadhaar",
                source_verification_state="VERIFIED",
                status=RequirementStatus.RECOMMENDED,
                is_mandatory=False,
                explanation="Helps the enrolment operator cross-verify demographic data and retrieve existing profile swiftly.",
                source_citation="DOC_033, UIDAI Circular dated 30.04.2026",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_AAD_NAME_INITIAL_EXPANSION_04",
                title="Documentary Proof for Initials Expansion",
                description="Document demonstrating the correspondence between abbreviation/initial and full name.",
                category="aadhaar",
                procedure_id="aadhaar_name_update",
                supporting_source_id="DOC_034",
                supporting_source_title="List of Acceptable Supporting Documents for Aadhaar Enrolment & Update",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_CONDITIONAL,
                is_mandatory=False,
                explanation="Required conditionally when expanding an initial (e.g., 'K. Sharma' to 'Kumar Sharma'). Must be supported by School Leaving Certificate, Passport, or PAN per UIDAI verified document matrix.",
                source_citation="DOC_034, Section 1 (Table 1: Supported PoI Documents with expanded legal name)",
                is_completed=False,
            ),
        ],
    },

    "aadhaar_name_update_major_gazette": {
        "title": "Aadhaar Major Name Change (Post-Marriage / Gazette / Gender Transition)",
        "category": "aadhaar",
        "procedure_id": "aadhaar_name_update_major_gazette",
        "description": "Evidence requirements for major name changes requiring legal notification or public record publication.",
        "items": [
            ChecklistItem(
                requirement_id="REQ_AAD_GAZ_01",
                title="Gazette Notification in The Gazette of India",
                description="Original or certified copy of the Gazette Notification published in The Gazette of India (Part IV) announcing legal change of name.",
                category="aadhaar",
                procedure_id="aadhaar_name_update_major_gazette",
                supporting_source_id="DOC_034",
                supporting_source_title="List of Acceptable Supporting Documents for Aadhaar Enrolment & Update",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Mandatory under UIDAI guidelines for major name changes not accompanied by official marriage or divorce records.",
                source_citation="DOC_034, Table 1, Row 11 (Gazette Notification for Name Change)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_AAD_MARR_02",
                title="Marriage Certificate / Divorce Decree",
                description="Official Marriage Registration Certificate issued by Registrar of Marriages or certified Divorce Decree.",
                category="aadhaar",
                procedure_id="aadhaar_name_update_major_gazette",
                supporting_source_id="DOC_034",
                supporting_source_title="List of Acceptable Supporting Documents for Aadhaar Enrolment & Update",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_CONDITIONAL,
                is_mandatory=False,
                explanation="Applicable when surname or given name change is consequent to marriage or divorce. Dispenses with gazette publication if valid certificate is provided.",
                source_citation="DOC_034, Table 1, Row 14 (Marriage Certificate)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_AAD_SOP_EXCEPTION_03",
                title="Regional Office (RO) Exception Approval Dossier",
                description="Submission of prior rejection slips, formal affidavit, and identity lineage documents to the concerned UIDAI Regional Office.",
                category="aadhaar",
                procedure_id="aadhaar_name_update_major_gazette",
                supporting_source_id="DOC_043",
                supporting_source_title="Standard Operating Procedure (SOP) to be Followed for Updating Name in Aadhaar",
                source_verification_state="SOURCE_METADATA_CONFLICT",
                status=RequirementStatus.HUMAN_REVIEW_REQUIRED,
                is_mandatory=False,
                explanation="Conditional human verification required if applicant has exhausted the standard two-time lifetime name update limit. Subject to regional discretion and verified evidence.",
                source_citation="DOC_043, Section 7 (Exception Handling Procedure — Subject to statutory limitation notice)",
                is_completed=False,
            ),
        ],
    },

    "aadhaar_dob_update": {
        "title": "Aadhaar Date of Birth (DoB) Update",
        "category": "aadhaar",
        "procedure_id": "aadhaar_dob_update",
        "description": "Evidence requirements for correcting or verifying Date of Birth in resident Aadhaar record.",
        "items": [
            ChecklistItem(
                requirement_id="REQ_AAD_DOB_CERT_01",
                title="Birth Certificate from Municipal Corporation / Registrar",
                description="Official Birth Certificate issued by the competent authority under the Registration of Births and Deaths Act, 1969.",
                category="aadhaar",
                procedure_id="aadhaar_dob_update",
                supporting_source_id="DOC_034",
                supporting_source_title="List of Acceptable Supporting Documents for Aadhaar Enrolment & Update",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Primary proof of Date of Birth under UIDAI regulations. Compulsory for all individuals born on or after 01.10.2023.",
                source_citation="DOC_034, Section 2 (Table 2: Supported Proof of Date of Birth Documents)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_AAD_DOB_EDU_02",
                title="Secondary School Leaving Certificate (SSLC) / Marksheet",
                description="Marksheet or passing certificate issued by recognized educational board or university containing explicit date of birth.",
                category="aadhaar",
                procedure_id="aadhaar_dob_update",
                supporting_source_id="DOC_034",
                supporting_source_title="List of Acceptable Supporting Documents for Aadhaar Enrolment & Update",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_CONDITIONAL,
                is_mandatory=False,
                explanation="Accepted as statutory alternative to Birth Certificate for adults who do not possess a municipal birth certificate.",
                source_citation="DOC_034, Table 2, Row 4 (Board Certificate / Marksheet)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_AAD_DOB_LIMIT_03",
                title="Sub-Divisional Magistrate (SDM) / Joint Magistrate Order",
                description="Court or administrative order by competent magistrate condoning birth date discrepancy.",
                category="aadhaar",
                procedure_id="aadhaar_dob_update",
                supporting_source_id="DOC_013",
                supporting_source_title="Circular Regarding Certificate for Aadhaar Enrolment Update",
                source_verification_state="VERIFIED",
                status=RequirementStatus.HUMAN_REVIEW_REQUIRED,
                is_mandatory=False,
                explanation="Required if DoB has already been corrected once, or if the declared age difference exceeds 3 years from existing record.",
                source_citation="DOC_013, Clause 4.2 (Exception Handling for Date of Birth Updates)",
                is_completed=False,
            ),
        ],
    },

    "aadhaar_address_update": {
        "title": "Aadhaar Address Update (Resident & HoF)",
        "category": "aadhaar",
        "procedure_id": "aadhaar_address_update",
        "description": "Evidence requirements for updating residential address through online SSUP portal or Aadhaar Seva Kendra.",
        "items": [
            ChecklistItem(
                requirement_id="REQ_AAD_POA_01",
                title="Proof of Address (PoA) Document",
                description="Valid Proof of Address document in applicant's name (Electricity bill <=3 months, Bank passbook, Passport, Ration card, Voter ID).",
                category="aadhaar",
                procedure_id="aadhaar_address_update",
                supporting_source_id="DOC_034",
                supporting_source_title="List of Acceptable Supporting Documents for Aadhaar Enrolment & Update",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Standard requirement for individual address update under Table 3 of Acceptable Documents.",
                source_citation="DOC_034, Section 3 (Table 3: Supported PoA Documents)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_AAD_HOF_02",
                title="Head of Family (HoF) Self-Declaration Form",
                description="Self-declaration form signed by Head of Family along with Proof of Relationship (PoR) document.",
                category="aadhaar",
                procedure_id="aadhaar_address_update",
                supporting_source_id="DOC_013",
                supporting_source_title="Circular Regarding Certificate for Aadhaar Enrolment Update",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_CONDITIONAL,
                is_mandatory=False,
                explanation="Permitted alternative when resident has no independent address proof and shares residential address with family head.",
                source_citation="DOC_013, Annexure I (HoF Declaration Proforma)",
                is_completed=False,
            ),
        ],
    },

    # -----------------------------------------------------------------------
    # 2. PAN CARD PROCEDURES
    # -----------------------------------------------------------------------
    "pan_name_correction_csf": {
        "title": "PAN Card Correction / Changes in PAN Data (Form CSF)",
        "category": "pan",
        "procedure_id": "pan_name_correction_csf",
        "description": "Statutory requirements for correcting applicant name, father's name, or date of birth in Income Tax Department PAN master record.",
        "items": [
            ChecklistItem(
                requirement_id="REQ_PAN_PROOF_PAN_01",
                title="Proof of Existing PAN",
                description="Copy of physical PAN card or official PAN Allotment Letter issued by Income Tax Department / NSDL / UTIITSL.",
                category="pan",
                procedure_id="pan_name_correction_csf",
                supporting_source_id="DOC_036",
                supporting_source_title="PAN Request for New PAN Card Or/And Changes or Correction in PAN Data (Form CSF)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Rule 114 requires submitting proof of the allotted 10-digit alphanumeric Permanent Account Number.",
                source_citation="DOC_036, Item 1 (Documents to be Submitted with Application Form)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_PAN_POI_02",
                title="Proof of Identity (PoI) in Correct Name",
                description="Valid government credential displaying applicant's correct intended name (Aadhaar, Passport, Driving License, Voter ID).",
                category="pan",
                procedure_id="pan_name_correction_csf",
                supporting_source_id="DOC_036",
                supporting_source_title="PAN Request for New PAN Card Or/And Changes or Correction in PAN Data (Form CSF)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Required to substantiate the new or corrected spelling under Rule 114 of Income Tax Rules, 1962.",
                source_citation="DOC_036, Instructions Table A (Identity Proofs for Individuals)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_PAN_POA_03",
                title="Proof of Address (PoA)",
                description="Valid address document (Utility bill <=3 months, Bank account statement, Passport, Voter ID).",
                category="pan",
                procedure_id="pan_name_correction_csf",
                supporting_source_id="DOC_036",
                supporting_source_title="PAN Request for New PAN Card Or/And Changes or Correction in PAN Data (Form CSF)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Address where the updated physical PAN card is to be dispatched by post.",
                source_citation="DOC_036, Instructions Table B (Address Proofs)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_PAN_DOB_04",
                title="Proof of Date of Birth (DoB)",
                description="Birth Certificate, Class 10 Passing Certificate, or Passport reflecting date of birth.",
                category="pan",
                procedure_id="pan_name_correction_csf",
                supporting_source_id="DOC_036",
                supporting_source_title="PAN Request for New PAN Card Or/And Changes or Correction in PAN Data (Form CSF)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Required for establishing date of birth correctness in the central NSDL database.",
                source_citation="DOC_036, Instructions Table C (Date of Birth Proofs)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_PAN_GAZETTE_05",
                title="Gazette Notification / Marriage Certificate for Major Name Change",
                description="Publication in Official Gazette (for other than married women) or Marriage Certificate (for married women).",
                category="pan",
                procedure_id="pan_name_correction_csf",
                supporting_source_id="DOC_036",
                supporting_source_title="PAN Request for New PAN Card Or/And Changes or Correction in PAN Data (Form CSF)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_CONDITIONAL,
                is_mandatory=False,
                explanation="Mandatory under IT rules when the change in name is significant and cannot be justified by ordinary identity credential.",
                source_citation="DOC_036, Instruction Clause 4(b) (Change of Name Documentation)",
                is_completed=False,
            ),
        ],
    },

    # -----------------------------------------------------------------------
    # 3. PASSPORT PROCEDURES
    # -----------------------------------------------------------------------
    "passport_reissue_correction": {
        "title": "Passport Re-issue (Change in Name / Personal Particulars)",
        "category": "passport",
        "procedure_id": "passport_reissue_correction",
        "description": "Mandatory checklist for applying for Indian Passport re-issue under Passport Seva System due to name or demographic correction.",
        "items": [
            ChecklistItem(
                requirement_id="REQ_PASS_OLD_PASS_01",
                title="Original Old Passport & Self-Attested Photocopy",
                description="Old physical passport along with self-attested copies of first two pages, last two pages, and ECR/Non-ECR page.",
                category="passport",
                procedure_id="passport_reissue_correction",
                supporting_source_id="DOC_PASS_ACT_1967",
                supporting_source_title="Passports Act, 1967 & Passport Rules, 1980 (Ministry of External Affairs)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Original document must be physically presented at the Passport Seva Kendra (PSK) for cancellation and inspection.",
                source_citation="Passports Rules 1980, Schedule III",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_PASS_CURRENT_ADDRESS_02",
                title="Proof of Current Residential Address",
                description="Aadhaar Card, Water/Electricity/Telephone bill, Active Bank Passbook with photo, or Rent Agreement.",
                category="passport",
                procedure_id="passport_reissue_correction",
                supporting_source_id="DOC_PASS_ACT_1967",
                supporting_source_title="Passports Act, 1967 & Passport Rules, 1980 (Ministry of External Affairs)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Essential for local police verification report (PVR) generation.",
                source_citation="MEA Document Advisor, Proof of Address Requirements",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_PASS_ANNEXURE_E_03",
                title="Annexure 'E' — Deed Poll / Sworn Affidavit for Name Change",
                description="Prescribed proforma affidavit affirming old and new legal name executed on non-judicial stamp paper.",
                category="passport",
                procedure_id="passport_reissue_correction",
                supporting_source_id="DOC_PASS_RULES_ANNEX",
                supporting_source_title="Passport Rules Annexures & Prescribed Proformas",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_CONDITIONAL,
                is_mandatory=False,
                explanation="Required for change in name (minor/spelling alteration) without a formal gazette notification.",
                source_citation="Passport Manual 2020, Chapter 9 (Name Change Procedures)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_PASS_GAZETTE_04",
                title="Gazette Notification & Newspaper Clippings for Major Name Change",
                description="Two daily newspapers containing advertisements (one regional and one national language) plus Gazette notification.",
                category="passport",
                procedure_id="passport_reissue_correction",
                supporting_source_id="DOC_PASS_RULES_ANNEX",
                supporting_source_title="Passport Rules Annexures & Prescribed Proformas",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_CONDITIONAL,
                is_mandatory=False,
                explanation="Compulsory when the change in given name or surname exceeds clerical spelling adjustments.",
                source_citation="MEA Circular on Major Name Change, Clause 2.1",
                is_completed=False,
            ),
        ],
    },

    # -----------------------------------------------------------------------
    # 4. CLASS 10 CERTIFICATE PROCEDURES
    # -----------------------------------------------------------------------
    "class_10_name_correction": {
        "title": "Class 10 Certificate / Marksheet Name Correction (Secondary Board)",
        "category": "class_10",
        "procedure_id": "class_10_name_correction",
        "description": "Statutory procedure and documentary evidence required to rectify student or parent name on Secondary School Marksheets.",
        "items": [
            ChecklistItem(
                requirement_id="REQ_EDU10_APP_FORM_01",
                title="Board Correction Application Form Forwarded by School Principal",
                description="Prescribed application proforma signed by the candidate and endorsed with official stamp of the School Principal.",
                category="class_10",
                procedure_id="class_10_name_correction",
                supporting_source_id="DOC_CBSE_BYELAWS",
                supporting_source_title="Examination Byelaws (Rule 69.1: Changes & Corrections in Candidate Name)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Boards (such as CBSE/ICSE/State Boards) only accept applications routed through the examination center school.",
                source_citation="CBSE Examination Byelaws, Rule 69.1(i)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_EDU10_SCHOLAR_REG_02",
                title="Certified Extract of School Admission & Withdrawal Register",
                description="Duly attested extract of the Scholar Register / Admission Form showing entry made at the time of initial admission.",
                category="class_10",
                procedure_id="class_10_name_correction",
                supporting_source_id="DOC_CBSE_BYELAWS",
                supporting_source_title="Examination Byelaws (Rule 69.1: Changes & Corrections in Candidate Name)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Establishes that the discrepancy arose due to clerical error in board compilation rather than candidate misrepresentation.",
                source_citation="CBSE Examination Byelaws, Rule 69.1(ii)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_EDU10_ORIGINAL_DOC_03",
                title="Original Class 10 Passing Certificate & Marksheet",
                description="Physical original certificates issued by the Board to be surrendered for destruction and replacement.",
                category="class_10",
                procedure_id="class_10_name_correction",
                supporting_source_id="DOC_CBSE_BYELAWS",
                supporting_source_title="Examination Byelaws (Rule 69.1: Changes & Corrections in Candidate Name)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="No duplicate or amended certificate can be released without cancellation of the previously issued original credential.",
                source_citation="CBSE Examination Byelaws, Rule 69.1(iv)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_EDU10_GAZETTE_04",
                title="Gazette Notification & Public Notice (If Beyond 5-Year Time Limit)",
                description="Certified copy of Gazette Notification published in official state or union gazette.",
                category="class_10",
                procedure_id="class_10_name_correction",
                supporting_source_id="DOC_CBSE_BYELAWS",
                supporting_source_title="Examination Byelaws (Rule 69.1: Changes & Corrections in Candidate Name)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.HUMAN_REVIEW_REQUIRED,
                is_mandatory=False,
                explanation="Mandatory if correction is requested after publication of results and expiry of statutory board limitation periods.",
                source_citation="Supreme Court Ruling in Jigya Yadav vs CBSE (2021)",
                is_completed=False,
            ),
        ],
    },

    # -----------------------------------------------------------------------
    # 5. CLASS 12 CERTIFICATE PROCEDURES
    # -----------------------------------------------------------------------
    "class_12_name_correction": {
        "title": "Class 12 Certificate / Marksheet Name Correction (Senior Secondary Board)",
        "category": "class_12",
        "procedure_id": "class_12_name_correction",
        "description": "Evidence requirements for reconciling Senior Secondary credentials with Class 10 foundational records.",
        "items": [
            ChecklistItem(
                requirement_id="REQ_EDU12_CLASS10_BASE_01",
                title="Certified Class 10 Marksheet & Passing Certificate",
                description="Attested photocopy of verified Class 10 credential serving as the foundational school record.",
                category="class_12",
                procedure_id="class_12_name_correction",
                supporting_source_id="DOC_CBSE_BYELAWS",
                supporting_source_title="Examination Byelaws (Senior Secondary Corrections)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Class 12 particulars must strictly conform to Class 10 records under board regulations.",
                source_citation="CBSE Senior Secondary Byelaws, Clause 14.3",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_EDU12_ORIGINAL_DOC_02",
                title="Original Class 12 Certificate & Marksheet",
                description="Physical original certificates issued by the Board surrendered for amendment.",
                category="class_12",
                procedure_id="class_12_name_correction",
                supporting_source_id="DOC_CBSE_BYELAWS",
                supporting_source_title="Examination Byelaws (Senior Secondary Corrections)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Required for cancellation and issuance of corrected digital/physical grade sheet.",
                source_citation="CBSE Examination Byelaws, Rule 69.1(iv)",
                is_completed=False,
            ),
        ],
    },

    # -----------------------------------------------------------------------
    # 6. EPF / UAN RECORDS PROCEDURES
    # -----------------------------------------------------------------------
    "epf_joint_declaration": {
        "title": "EPFO Joint Declaration Form (Member & Employer Demographic Update)",
        "category": "epf",
        "procedure_id": "epf_joint_declaration",
        "description": "Standard evidence matrix for rectifying Member Name, Father's Name, Date of Birth, or Date of Joining in EPFO UAN master records.",
        "items": [
            ChecklistItem(
                requirement_id="REQ_EPF_JD_FORM_01",
                title="Joint Declaration Proforma Signed by Member and Employer",
                description="Physical or digitally signed Joint Declaration carrying establishment registration code, employer seal, and member signature.",
                category="epf",
                procedure_id="epf_joint_declaration",
                supporting_source_id="DOC_EPFO_SOP_2023",
                supporting_source_title="EPFO Standard Operating Procedure (SOP) for Joint Declaration (Circular WS/2023/102)",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Mandatory dual-attestation document certifying employment relationship and agreed correction.",
                source_citation="EPFO Circular dated 22.08.2023, Annexure A",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_EPF_AADHAAR_MANDATORY_02",
                title="Self-Attested Aadhaar Card Copy",
                description="Clear photocopy of Aadhaar Card reflecting updated legal name and full date of birth.",
                category="epf",
                procedure_id="epf_joint_declaration",
                supporting_source_id="DOC_EPFO_SOP_2023",
                supporting_source_title="EPFO Standard Operating Procedure (SOP) for Joint Declaration",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Aadhaar is statutory prerequisite for UAN KYC validation and electronic member authentication.",
                source_citation="EPFO Circular on Mandatory Aadhaar Seeding (Section 142 of Social Security Code)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_EPF_PAN_03",
                title="Self-Attested PAN Card Copy",
                description="Copy of PAN card for member tax deduction compliance and KYC verification.",
                category="epf",
                procedure_id="epf_joint_declaration",
                supporting_source_id="DOC_EPFO_SOP_2023",
                supporting_source_title="EPFO Standard Operating Procedure (SOP) for Joint Declaration",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_MANDATORY,
                is_mandatory=True,
                explanation="Compulsory supporting document for major and minor profile changes under EPFO Table 1.",
                source_citation="EPFO Circular WS/2023/102, Table 1 (Mandatory Documents for Profile Change)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_EPF_DOB_PROOF_04",
                title="Birth Certificate / Passport / School TC (If DOB Difference > 3 Years)",
                description="Statutory birth proof showing date of birth, issued by Municipal Corporation, MEA, or Educational Board.",
                category="epf",
                procedure_id="epf_joint_declaration",
                supporting_source_id="DOC_EPFO_SOP_2023",
                supporting_source_title="EPFO Standard Operating Procedure (SOP) for Joint Declaration",
                source_verification_state="VERIFIED",
                status=RequirementStatus.VERIFIED_CONDITIONAL,
                is_mandatory=False,
                explanation="Required specifically when the difference between existing EPFO recorded DoB and corrected DoB is greater than three years.",
                source_citation="EPFO SOP 2023, Clause 6.4 (Age Discrepancy Escalation Threshold)",
                is_completed=False,
            ),
            ChecklistItem(
                requirement_id="REQ_EPF_HUMAN_APPROVAL_05",
                title="Regional Provident Fund Commissioner (RPFC) Discretionary Review",
                description="Administrative review conducted by Field Office in case of establishment closure or major wage mismatch.",
                category="epf",
                procedure_id="epf_joint_declaration",
                supporting_source_id="DOC_EPFO_SOP_2023",
                supporting_source_title="EPFO Standard Operating Procedure (SOP) for Joint Declaration",
                source_verification_state="VERIFIED",
                status=RequirementStatus.HUMAN_REVIEW_REQUIRED,
                is_mandatory=False,
                explanation="Triggered if the employer establishment has closed down, or if the employee changed complete name with no matching school record.",
                source_citation="EPFO SOP 2023, Clause 8.2 (Non-Operational Establishments)",
                is_completed=False,
            ),
        ],
    },
}


class ChecklistService:
    """
    Supporting-Document Checklist Engine (Phase P3H.6).
    Provides evidence-backed, reusable checklist specifications for statutory corrections.
    Distinguishes:
    - Verified Mandatory Requirements (strictly mandated by statutory rules)
    - Verified Conditional Requirements (triggered only by specific conditions like marriage or age gap)
    - Recommended Supporting Documents (beneficial for smooth verification)
    - Requirements Requiring Human Review (regional escalation or closed establishment)
    """

    @classmethod
    def get_checklist_for_procedure(cls, procedure_id: str) -> Optional[ChecklistResponse]:
        proc_clean = (procedure_id or "").strip().lower()
        data = STATUTORY_CHECKLISTS.get(proc_clean)
        if not data:
            # Fallback search by prefix or substring
            for k, val in STATUTORY_CHECKLISTS.items():
                if proc_clean in k or k in proc_clean:
                    data = val
                    break
        if not data:
            return None

        items: List[ChecklistItem] = data["items"]
        mandatory_count = sum(1 for item in items if item.status == RequirementStatus.VERIFIED_MANDATORY)
        conditional_count = sum(1 for item in items if item.status == RequirementStatus.VERIFIED_CONDITIONAL)
        recommended_count = sum(1 for item in items if item.status == RequirementStatus.RECOMMENDED)
        human_review_count = sum(1 for item in items if item.status == RequirementStatus.HUMAN_REVIEW_REQUIRED)

        return ChecklistResponse(
            procedure_id=data["procedure_id"],
            procedure_title=data["title"],
            category=data["category"],
            total_items=len(items),
            mandatory_count=mandatory_count,
            conditional_count=conditional_count,
            recommended_count=recommended_count,
            human_review_count=human_review_count,
            items=items,
            disclaimer=(
                "Citizen checklist completion is an informational preparation tool "
                "and does not constitute official government approval or successful statutory correction."
            )
        )

    @classmethod
    def get_checklists_for_category(cls, category: str) -> List[ChecklistResponse]:
        cat_clean = (category or "").strip().lower()
        if cat_clean in ("epfo", "uan"):
            cat_clean = "epf"
        elif cat_clean in ("education_10th", "matriculation"):
            cat_clean = "class_10"
        elif cat_clean in ("education_12th", "intermediate"):
            cat_clean = "class_12"

        results = []
        for pid, data in STATUTORY_CHECKLISTS.items():
            if data["category"] == cat_clean:
                checklist = cls.get_checklist_for_procedure(pid)
                if checklist:
                    results.append(checklist)
        return results

    @classmethod
    def get_checklist_for_conflict(
        cls,
        conflict_type: str,
        category_a: Optional[str] = None,
        category_b: Optional[str] = None
    ) -> Optional[ChecklistResponse]:
        """
        Maps a detected discrepancy type (e.g. NAME_MISMATCH, DOB_MISMATCH) and paired document categories
        to the appropriate authoritative correction checklist.
        """
        ctype = (conflict_type or "").upper()
        c_a = (category_a or "").lower()
        c_b = (category_b or "").lower()

        # Name Mismatch mapping
        if "NAME" in ctype:
            if "pan" in (c_a, c_b) and "aadhaar" in (c_a, c_b):
                # Standard recommendation: Update PAN Form CSF or Aadhaar Name Update
                return cls.get_checklist_for_procedure("pan_name_correction_csf")
            elif "epf" in (c_a, c_b) or "epfo" in (c_a, c_b):
                return cls.get_checklist_for_procedure("epf_joint_declaration")
            elif "passport" in (c_a, c_b):
                return cls.get_checklist_for_procedure("passport_reissue_correction")
            elif "class_10" in (c_a, c_b) or "education" in (c_a, c_b):
                return cls.get_checklist_for_procedure("class_10_name_correction")
            elif "aadhaar" in (c_a, c_b):
                return cls.get_checklist_for_procedure("aadhaar_name_update")

        # Date of Birth Mismatch mapping
        elif "DOB" in ctype or "BIRTH" in ctype:
            if "aadhaar" in (c_a, c_b):
                return cls.get_checklist_for_procedure("aadhaar_dob_update")
            elif "pan" in (c_a, c_b):
                return cls.get_checklist_for_procedure("pan_name_correction_csf")
            elif "epf" in (c_a, c_b) or "epfo" in (c_a, c_b):
                return cls.get_checklist_for_procedure("epf_joint_declaration")

        # Address mismatch mapping
        elif "ADDRESS" in ctype:
            return cls.get_checklist_for_procedure("aadhaar_address_update")

        return None

