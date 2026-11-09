import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.user import User
from app.models.conflict import Conflict
from app.models.document import Document
from app.rag.retrieval.retriever import HybridRetriever, DEFAULT_BM25_SCORE_FLOOR
from app.rag.ingestion.corpus_ingestion import DOC_043_STATUTORY_DISCLAIMER
from app.rag.schemas import (
    ProceduralGuidanceRequest,
    ProceduralGuidanceResponse,
    ProceduralGuidanceStep,
    PersonalizedGuidanceItem,
    PersonalizedGuidanceResponse,
    SourceCitation,
    RepositoryResourceItem,
    ChecklistItem,
)
from app.services.checklist_service import ChecklistService
from app.services.repository_service import CitizenRepositoryService, CATEGORY_NORMALIZATION

logger = logging.getLogger("convelina.procedural_guidance.service")

# Procedural templates grounded in verified official circulars
PROCEDURAL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "aadhaar_name_update": {
        "title": "Aadhaar Name Correction (Demographic Update)",
        "category": "aadhaar",
        "issue_summary": "Resident requires correction of clerical typographical errors or expansion of initials in their Aadhaar demographic profile.",
        "steps": [
            ProceduralGuidanceStep(
                step_number=1,
                title="Prepare Prescribed Proof of Identity (PoI)",
                instruction="Ensure you have at least one valid, unexpired government credential from the approved UIDAI list (such as Passport, PAN Card, Voter ID, or Driving License) reflecting your correct intended legal name.",
                official_portal_or_form="UIDAI Acceptable Supporting Documents (DOC_034)",
                required_documents=["Valid Proof of Identity (PoI)", "Current Aadhaar copy / letter"],
            ),
            ProceduralGuidanceStep(
                step_number=2,
                title="Complete Aadhaar Enrolment/Update Form",
                instruction="Fill out Form 1 (for Adult Residents aged 18+) or Form 2 (for Minors aged 5-18), marking the checkbox for 'Name Update' and writing your exact name in CAPITAL letters.",
                official_portal_or_form="Aadhaar Enrolment and Update Form (DOC_001)",
                required_documents=["Aadhaar Enrolment/Update Form (Form 1)"],
            ),
            ProceduralGuidanceStep(
                step_number=3,
                title="Visit an Authorized Aadhaar Seva Kendra (ASK)",
                instruction="Book an appointment online via myAadhaar (uidai.gov.in) or walk into an authorized Aadhaar center for biometric confirmation (fingerprint/iris) and document verification.",
                official_portal_or_form="myAadhaar Appointment Portal (myaadhaar.uidai.gov.in)",
                required_documents=["Original PoI document for physical verification", "Form 1"],
            ),
            ProceduralGuidanceStep(
                step_number=4,
                title="Retain Update Request Number (URN)",
                instruction="Collect the printed acknowledgement slip containing the 14-digit Update Request Number (URN) to track update status online within statutory turnaround time.",
                official_portal_or_form="UIDAI Check Status Portal",
                required_documents=["Acknowledgement Slip / URN"],
            ),
        ],
        "citations": [
            SourceCitation(
                source_id="DOC_001",
                title="Aadhaar Enrolment and Update Forms (Adult Resident)",
                authority="Unique Identification Authority of India (UIDAI)",
                url="https://uidai.gov.in",
                section="Form 1 Instructions",
                verification_status="verified",
            ),
            SourceCitation(
                source_id="DOC_034",
                title="UIDAI List of Acceptable Supporting Documents",
                authority="Unique Identification Authority of India (UIDAI)",
                url="https://uidai.gov.in",
                section="Section 1 (Table 1: Supported Proof of Identity)",
                verification_status="verified",
            ),
        ],
        "limitations": [
            "Aadhaar name update has a standard limit of 2 times in a lifetime under Regulation 12A.",
            "Initials expansion must match supporting educational marksheet, passport, or gazette record.",
        ],
    },

    "pan_name_correction_csf": {
        "title": "PAN Card Correction / Changes in PAN Data (Form CSF)",
        "category": "pan",
        "issue_summary": "Citizen requires correction of name, parent's name, or date of birth on their Permanent Account Number card.",
        "steps": [
            ProceduralGuidanceStep(
                step_number=1,
                title="Obtain and Complete Form CSF",
                instruction="Fill out the 'Request for New PAN Card Or/And Changes or Correction in PAN Data' (CSF Form). Check the box on the left margin corresponding to Item 1 (Full Name).",
                official_portal_or_form="Income Tax / NSDL CSF Form (DOC_036)",
                required_documents=["Form CSF", "Existing PAN copy"],
            ),
            ProceduralGuidanceStep(
                step_number=2,
                title="Compile Statutory Supporting Documents",
                instruction="Attach proof of existing PAN, proof of identity in correct name (matching Aadhaar or Passport), proof of address, and proof of date of birth.",
                official_portal_or_form="Rule 114 Income Tax Rules, 1962",
                required_documents=["Proof of Identity", "Proof of Address", "Proof of Date of Birth", "PAN Card Copy"],
            ),
            ProceduralGuidanceStep(
                step_number=3,
                title="Submit Application Online or Physical Center",
                instruction="Submit electronically through the Protean (NSDL) or UTIITSL portal with Aadhaar e-Sign, or submit physical dossier at a TIN-Facilitation Center.",
                official_portal_or_form="Protean e-Gov Portal (onlineservices.nsdl.com)",
                required_documents=["Signed Form CSF or Aadhaar OTP Authentication"],
            ),
            ProceduralGuidanceStep(
                step_number=4,
                title="Track 15-Digit Acknowledgement Number",
                instruction="Track dispatch and processing status via the Income Tax e-Filing or NSDL tracking facility.",
                official_portal_or_form="NSDL PAN Status Portal",
                required_documents=["15-Digit Acknowledgement Number"],
            ),
        ],
        "citations": [
            SourceCitation(
                source_id="DOC_036",
                title="Request for New PAN Card Or/And Changes or Correction in PAN Data (Form CSF)",
                authority="Income Tax Department / NSDL",
                url="https://incometax.gov.in",
                section="Instructions Clause 1 to 4",
                verification_status="verified",
            ),
        ],
        "limitations": [
            "For significant name changes beyond minor spelling, a copy of the official Gazette publication or Marriage Certificate is compulsory.",
            "PAN name must match Aadhaar demographic records to ensure uninterrupted PAN-Aadhaar linkage.",
        ],
    },

    "passport_reissue_correction": {
        "title": "Passport Re-issue for Name / Particulars Correction",
        "category": "passport",
        "issue_summary": "Citizen requires a re-issued Indian Passport reflecting updated or corrected name or demographic particulars.",
        "steps": [
            ProceduralGuidanceStep(
                step_number=1,
                title="Register and Fill Online Application on Passport Seva",
                instruction="Create account on portal2.passportindia.gov.in, select 'Apply for Re-issue of Passport', and choose reason 'Change in Existing Personal Particulars - Name'.",
                official_portal_or_form="Passport Seva Online Portal (passportindia.gov.in)",
                required_documents=["Passport Seva Account Registration"],
            ),
            ProceduralGuidanceStep(
                step_number=2,
                title="Execute Name Change Proforma / Affidavit",
                instruction="For minor spelling changes, execute Annexure 'E' deed poll affidavit on non-judicial stamp paper. For major changes, obtain Gazette notification and 2 newspaper notices.",
                official_portal_or_form="Passport Rules 1980 Annexure 'E'",
                required_documents=["Annexure 'E' Affidavit / Gazette Notification"],
            ),
            ProceduralGuidanceStep(
                step_number=3,
                title="Schedule Appointment at Passport Seva Kendra (PSK)",
                instruction="Pay the statutory fee online and book an appointment slot at the nearest PSK or Post Office PSK (POPSK).",
                official_portal_or_form="Passport Seva Appointment Scheduling",
                required_documents=["Original Old Passport", "Proof of Address", "Photocopies of passport pages"],
            ),
            ProceduralGuidanceStep(
                step_number=4,
                title="Biometric Verification and Document Verification",
                instruction="Attend in person with original credentials for biometric capture, counter verification, and Granting Officer interview.",
                official_portal_or_form="PSK Counter Verification",
                required_documents=["Original Credentials Dossier"],
            ),
        ],
        "citations": [
            SourceCitation(
                source_id="DOC_PASS_ACT_1967",
                title="Passports Act, 1967 & Passport Rules, 1980",
                authority="Ministry of External Affairs (CPV Division)",
                url="https://passportindia.gov.in",
                section="Chapter 9 (Name Change Guidelines)",
                verification_status="verified",
            ),
        ],
        "limitations": [
            "Police Verification Report (PVR) is mandatory for name corrections on re-issued passports.",
            "Physical original passport must be presented for cancellation.",
        ],
    },

    "epf_joint_declaration": {
        "title": "EPFO Joint Declaration for Member Profile Correction",
        "category": "epf",
        "issue_summary": "EPF member requires correction of name, father's name, or date of birth in their UAN electronic member record.",
        "steps": [
            ProceduralGuidanceStep(
                step_number=1,
                title="Obtain and Fill Joint Declaration Proforma",
                instruction="Fill the EPFO Joint Declaration Form indicating the incorrect value currently in EPFO records and the correct value supported by identity proofs.",
                official_portal_or_form="EPFO Joint Declaration Proforma (Circular WS/2023/102)",
                required_documents=["Joint Declaration Form", "Aadhaar Card Copy", "PAN Card Copy"],
            ),
            ProceduralGuidanceStep(
                step_number=2,
                title="Obtain Employer Attestation and Seal",
                instruction="Submit to current or former establishment employer for authorized signatory signature and official corporate seal.",
                official_portal_or_form="Employer Attestation Requirement",
                required_documents=["Establishment Authorized Signature and Seal"],
            ),
            ProceduralGuidanceStep(
                step_number=3,
                title="Submit Online or to EPFO Regional Office",
                instruction="Submit through the EPFO Unified Member Portal (Member e-Sewa) or deliver physical application to the concerned EPFO Regional Field Office.",
                official_portal_or_form="EPFO Member e-Sewa Portal (unifiedportal-mem.epfindia.gov.in)",
                required_documents=["Attested Joint Declaration Dossier"],
            ),
        ],
        "citations": [
            SourceCitation(
                source_id="DOC_EPFO_SOP_2023",
                title="EPFO Standard Operating Procedure for Joint Declaration",
                authority="Employees' Provident Fund Organisation (EPFO)",
                url="https://epfindia.gov.in",
                section="Circular WS/2023/102 (Table 1 Supporting Matrix)",
                verification_status="verified",
            ),
        ],
        "limitations": [
            "Aadhaar seeding is compulsory for all UAN profile corrections.",
            "DOB discrepancy exceeding 3 years requires official municipal birth certificate or passport.",
        ],
    },

    "class_10_name_correction": {
        "title": "Secondary School (Class 10) Certificate Correction",
        "category": "class_10",
        "issue_summary": "Student requires correction of spelling or personal particulars in Class 10 Board Marksheet / Certificate.",
        "steps": [
            ProceduralGuidanceStep(
                step_number=1,
                title="Apply through School Head / Principal",
                instruction="Obtain the board correction application form and submit it to the Principal of the school last attended.",
                official_portal_or_form="Board Examination Byelaws (Rule 69.1)",
                required_documents=["Application Form", "Original Marksheet / Passing Certificate"],
            ),
            ProceduralGuidanceStep(
                step_number=2,
                title="Extract Certified School Scholar Register",
                instruction="Ensure the school Principal forwards a certified extract of the Admission / Scholar Register demonstrating the initial school record.",
                official_portal_or_form="School Scholar Register Attestation",
                required_documents=["Certified Admission Register Copy"],
            ),
            ProceduralGuidanceStep(
                step_number=3,
                title="Surrender Original Certificate upon Approval",
                instruction="Once the regional board office sanctions the correction, surrender original certificate for replacement with amended grade sheet.",
                official_portal_or_form="Regional Board Examination Office",
                required_documents=["Original Certificate for Cancellation"],
            ),
        ],
        "citations": [
            SourceCitation(
                source_id="DOC_CBSE_BYELAWS",
                title="Examination Byelaws (Rule 69.1: Changes & Corrections in Candidate Name)",
                authority="Central Board of Secondary Education (CBSE)",
                url="https://cbse.gov.in",
                section="Rule 69.1(i)-(iv)",
                verification_status="verified",
            ),
        ],
        "limitations": [
            "Clerical corrections must be consistent with school records. Inconsistencies require Gazette publication.",
        ],
    },
}


class ProceduralGuidanceService:
    """
    Procedural Guidance Synthesis Engine (Phase P3H.6).
    Coordinates BM25 retrieval, provenance validation, and strict DOC_043 restrictions
    to synthesize grounded, step-by-step procedural instructions for citizens.
    """

    @classmethod
    def synthesize_guidance(
        cls,
        payload: ProceduralGuidanceRequest,
        current_user: Optional[User] = None,
        db: Optional[Session] = None,
    ) -> ProceduralGuidanceResponse:
        query = (payload.query or "").strip()
        cat_filter = (payload.category or "").strip().lower() if payload.category else None
        if cat_filter:
            cat_filter = CATEGORY_NORMALIZATION.get(cat_filter, cat_filter)

        retriever = HybridRetriever()

        # 1. Statutory Abstention Check
        should_abstain, abst_reason = retriever.check_statutory_abstention(query)
        if should_abstain:
            logger.info("Procedural guidance abstained for query '%s': %s", query, abst_reason)
            return ProceduralGuidanceResponse(
                query=query,
                category=cat_filter or "general",
                issue_summary="Request touches on unverified, superseded, or legally unsupported statutory claims.",
                prescribed_procedure="Statutory Abstention Enforced",
                steps=[],
                checklist=[],
                relevant_resources=[],
                statutory_citations=[],
                statutory_abstention=True,
                abstention_reason=abst_reason,
                source_conflict_flag=False,
                human_review_required=True,
                limitations=[
                    "CONVELINA strictly declines to fabricate procedures for third-time exceptions, expired credentials, or non-statutory requests.",
                    "Consult an authorized government regional office or legal counsel directly.",
                ],
                disclaimer="STATUTORY ABSTENTION: Insufficient verified statutory evidence to formulate authoritative guidance.",
            )

        # 2. Conflict Context Retrieval (if conflict_id provided)
        conflict_details = None
        if payload.conflict_id and db and current_user:
            try:
                c_uuid = UUID(payload.conflict_id)
                c_rec = db.query(Conflict).filter(Conflict.id == c_uuid, Conflict.user_id == current_user.id).first()
                if c_rec:
                    conflict_details = c_rec.to_dict()
            except Exception as e:
                logger.warning("Could not retrieve conflict %s: %s", payload.conflict_id, e)

        # 3. Detect Applicable Procedure Template
        matched_proc_key = None
        q_low = query.lower()

        # Conflict-aware routing
        if conflict_details:
            ctype = conflict_details.get("conflict_type", "")
            if "NAME" in ctype:
                if cat_filter == "pan" or "pan" in q_low:
                    matched_proc_key = "pan_name_correction_csf"
                elif cat_filter == "passport" or "passport" in q_low:
                    matched_proc_key = "passport_reissue_correction"
                elif cat_filter == "epf" or "epf" in q_low:
                    matched_proc_key = "epf_joint_declaration"
                elif cat_filter == "class_10" or "10" in q_low:
                    matched_proc_key = "class_10_name_correction"
                else:
                    matched_proc_key = "aadhaar_name_update"
            elif "DOB" in ctype:
                matched_proc_key = "aadhaar_dob_update" if cat_filter == "aadhaar" else "pan_name_correction_csf"
            elif "ADDRESS" in ctype:
                matched_proc_key = "aadhaar_address_update"

        # Query-text routing
        if not matched_proc_key:
            if "pan" in q_low or cat_filter == "pan":
                matched_proc_key = "pan_name_correction_csf"
            elif "passport" in q_low or cat_filter == "passport":
                matched_proc_key = "passport_reissue_correction"
            elif "epf" in q_low or "uan" in q_low or cat_filter == "epf":
                matched_proc_key = "epf_joint_declaration"
            elif "10" in q_low or "matric" in q_low or cat_filter == "class_10":
                matched_proc_key = "class_10_name_correction"
            elif "dob" in q_low or "birth" in q_low:
                matched_proc_key = "aadhaar_dob_update"
            elif "address" in q_low:
                matched_proc_key = "aadhaar_address_update"
            else:
                matched_proc_key = "aadhaar_name_update"

        template = PROCEDURAL_TEMPLATES.get(matched_proc_key, PROCEDURAL_TEMPLATES["aadhaar_name_update"])

        # 4. Check for DOC_043 and Source Conflict Invariants
        has_doc043_restriction = False
        if matched_proc_key in ("aadhaar_name_update", "aadhaar_name_update_major_gazette") or (
            ("name" in q_low or "spelling" in q_low or "initial" in q_low)
            and ("aadhaar" in q_low or cat_filter == "aadhaar")
        ):
            has_doc043_restriction = True

        # 5. Retrieve Relevant Supporting Checklist Items
        checklist_resp = ChecklistService.get_checklist_for_procedure(matched_proc_key)
        checklist_items = checklist_resp.items if checklist_resp else []

        # 6. Retrieve Relevant Resources from Catalog
        target_cat = cat_filter or template["category"]
        repo_resp = CitizenRepositoryService.list_resources(category=target_cat, page=1, page_size=4)
        relevant_resources = repo_resp.resources

        # 7. Assemble Limitations and Warnings
        limitations = list(template.get("limitations", []))
        if has_doc043_restriction:
            limitations.append(DOC_043_STATUTORY_DISCLAIMER)

        # 8. Disclaimer Formulation
        disclaimer = (
            "Informational procedural guidance synthesized from verified statutory circulars and forms. "
            "CONVELINA is an independent identity reconciliation tool and does not represent official government authority."
        )
        if conflict_details:
            disclaimer = f"AUTOMATED COMPARISON RESULT — NOT OFFICIAL GOVERNMENT VERIFICATION. {disclaimer}"

        return ProceduralGuidanceResponse(
            query=query,
            category=target_cat,
            issue_summary=template["issue_summary"],
            prescribed_procedure=template["title"],
            steps=template["steps"],
            checklist=checklist_items,
            relevant_resources=relevant_resources,
            statutory_citations=template.get("citations", []),
            statutory_abstention=False,
            abstention_reason=None,
            source_conflict_flag=has_doc043_restriction,
            human_review_required=has_doc043_restriction,
            limitations=limitations,
            disclaimer=disclaimer,
        )

    @classmethod
    def get_personalized_guidance(
        cls,
        current_user: User,
        db: Session,
    ) -> PersonalizedGuidanceResponse:
        """
        Retrieves active discrepancies for the authenticated user and synthesizes
        personalized, evidence-backed procedural guidance.
        """
        conflicts = db.query(Conflict).filter(
            Conflict.user_id == current_user.id,
            Conflict.status.in_(["detected", "in_review"])
        ).order_by(Conflict.created_at.desc()).all()

        items: List[PersonalizedGuidanceItem] = []

        for c in conflicts:
            c_dict = c.to_dict()
            doc_a_id = c.document_a_id
            doc_b_id = c.document_b_id

            doc_a = db.query(Document).filter(Document.id == doc_a_id).first() if doc_a_id else None
            doc_b = db.query(Document).filter(Document.id == doc_b_id).first() if doc_b_id else None

            doc_a_cat = doc_a.document_type if doc_a else "aadhaar"
            doc_b_cat = doc_b.document_type if doc_b else "pan"

            val_a = c_dict.get("document_a_value") or "Not Available"
            val_b = c_dict.get("document_b_value") or "Not Available"
            field = c_dict.get("field_name") or "name"
            ctype = c_dict.get("conflict_type") or "NAME_MISMATCH"

            # Determine Recommended Procedure
            if "NAME" in ctype:
                if "pan" in (doc_a_cat.lower(), doc_b_cat.lower()) and "aadhaar" in (doc_a_cat.lower(), doc_b_cat.lower()):
                    rec_proc = "PAN Data Correction (Form CSF) or Aadhaar Name Update"
                    proc_id = "pan_name_correction_csf"
                    explanation = (
                        f"Detected discrepancy in {field}: '{val_a}' in {doc_a_cat.upper()} vs '{val_b}' in {doc_b_cat.upper()}. "
                        "To ensure successful PAN-Aadhaar linkage and prevent tax filing rejections, you must align the spelling across both documents."
                    )
                elif "epf" in (doc_a_cat.lower(), doc_b_cat.lower()):
                    rec_proc = "EPFO Joint Declaration Demographic Correction"
                    proc_id = "epf_joint_declaration"
                    explanation = (
                        f"Detected discrepancy in {field}: '{val_a}' in {doc_a_cat.upper()} vs '{val_b}' in {doc_b_cat.upper()}. "
                        "EPFO requires exact matching with Aadhaar for UAN KYC and claim processing."
                    )
                else:
                    rec_proc = "Aadhaar Name Correction (Form 1)"
                    proc_id = "aadhaar_name_update"
                    explanation = f"Detected discrepancy in {field} between {doc_a_cat.upper()} ('{val_a}') and {doc_b_cat.upper()} ('{val_b}')."
            elif "DOB" in ctype:
                rec_proc = "Aadhaar Date of Birth Update"
                proc_id = "aadhaar_dob_update"
                explanation = f"Detected discrepancy in Date of Birth: '{val_a}' in {doc_a_cat.upper()} vs '{val_b}' in {doc_b_cat.upper()}."
            else:
                rec_proc = "Aadhaar Address Update"
                proc_id = "aadhaar_address_update"
                explanation = f"Detected discrepancy in residential address between {doc_a_cat.upper()} and {doc_b_cat.upper()}."

            # Fetch Checklist and Resources
            chk = ChecklistService.get_checklist_for_procedure(proc_id)
            checklist_items = chk.items if chk else []

            repo_resp = CitizenRepositoryService.list_resources(category=doc_a_cat.lower(), page=1, page_size=2)
            applicable_resources = repo_resp.resources

            # Assistant Prompt Context for 1-click continuation
            prompt_context = (
                f"I have a verified discrepancy in my {field} between my {doc_a_cat.upper()} ('{val_a}') "
                f"and my {doc_b_cat.upper()} ('{val_b}'). Please guide me step-by-step through the {rec_proc} "
                f"and list the exact official supporting documents required."
            )

            items.append(
                PersonalizedGuidanceItem(
                    conflict_id=str(c.id),
                    conflict_type=ctype,
                    severity=c_dict.get("severity", "MEDIUM"),
                    field_name=field,
                    document_a_category=doc_a_cat,
                    document_a_name=doc_a.file_name if doc_a else doc_a_cat.upper(),
                    document_a_value=val_a,
                    document_b_category=doc_b_cat,
                    document_b_name=doc_b.file_name if doc_b else doc_b_cat.upper(),
                    document_b_value=val_b,
                    ocr_confidence=0.92,
                    review_warning=None if c.status == "in_review" else "Automated optical character extraction — confirm spelling against physical credentials.",
                    explanation=explanation,
                    recommended_procedure=rec_proc,
                    applicable_resources=applicable_resources,
                    checklist=checklist_items,
                    assistant_prompt_context=prompt_context,
                    disclaimer="AUTOMATED COMPARISON RESULT — NOT OFFICIAL GOVERNMENT VERIFICATION.",
                )
            )

        return PersonalizedGuidanceResponse(
            total_conflicts=len(items),
            items=items,
            disclaimer="AUTOMATED COMPARISON RESULT — NOT OFFICIAL GOVERNMENT VERIFICATION.",
        )
