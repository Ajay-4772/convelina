"""
CONVELINA - Resolution Mapping Service (Phase P2B)
Deterministic mapping of document discrepancies to official Indian government
correction procedures, statutory authorities, verified forms, and submission rules.

Zero hallucination: Never invents authorities, forms, or legal requirements.
Fail-safe: Flags low OCR confidence and non-Latin scripts for mandatory manual review.
"""

import logging
from typing import List, Dict, Any, Optional
from app.rag.schemas import ResolutionProcedureMapping, MappedFormRef

logger = logging.getLogger("convelina.resolution_mapping")

# Canonical official form definitions for fast deterministic lookup
KNOWN_OFFICIAL_FORMS: Dict[str, MappedFormRef] = {
    "form_aadhaar_update_adult": MappedFormRef(
        form_id="form_aadhaar_update_adult",
        form_name="Aadhaar Enrolment and Update Form (Adult 18+ Years)",
        issuing_authority="Unique Identification Authority of India (UIDAI)",
        official_download_url="https://uidai.gov.in/images/aadhaar_enrolment_update_form_adult.pdf",
        purpose="Correction or updating of Name, Date of Birth, Gender, or Address in Aadhaar database.",
    ),
    "form_pan_csf_correction": MappedFormRef(
        form_id="form_pan_csf_correction",
        form_name="Request for New PAN Card Or/And Changes or Correction in PAN Data (CSF Form)",
        issuing_authority="Income Tax Department / Protean (NSDL)",
        official_download_url="https://www.tin-nsdl.com/downloads/pan/download/Request-for-New-PAN-Card-or-and-Changes-or-Correction-in-PAN-Data-Form.pdf",
        purpose="Official application to rectify discrepancies in Name, Date of Birth, or Father's Name on an existing PAN card.",
    ),
    "form_passport_reissue": MappedFormRef(
        form_id="form_passport_reissue",
        form_name="Application for Re-issue of Indian Passport (Passport Seva)",
        issuing_authority="Ministry of External Affairs (CPV Division)",
        official_download_url="https://www.passportindia.gov.in/AppOnlineProject/online/printForm",
        purpose="Application for re-issuance of passport due to change in Personal Particulars (Name, DOB, Parentage).",
    ),
    "form_passport_annexure_e": MappedFormRef(
        form_id="form_passport_annexure_e",
        form_name="Annexure 'E' — Deed Poll / Sworn Affidavit for Change in Name",
        issuing_authority="Ministry of External Affairs",
        official_download_url="https://www.passportindia.gov.in/AppOnlineProject/pdf/AnnexureE.pdf",
        purpose="Mandatory affidavit format for Indian passport re-issue involving major name change or significant spelling changes.",
    ),
    "form_epf_joint_declaration": MappedFormRef(
        form_id="form_epf_joint_declaration",
        form_name="EPFO Joint Declaration Form (Member & Employer)",
        issuing_authority="Employees' Provident Fund Organisation (EPFO)",
        official_download_url="https://www.epfindia.gov.in/site_docs/PDFs/Downloads_PDFs/Joint_Declaration_Form.pdf",
        purpose="Correction or updating of Member Name, Father's Name, Date of Birth, and Gender in EPF/UAN records.",
    ),
    "form_epfo_digital_jd": MappedFormRef(
        form_id="form_epfo_digital_jd",
        form_name="EPFO Member Profile Update / Online Joint Declaration Proforma",
        issuing_authority="Employees' Provident Fund Organisation (EPFO)",
        official_download_url="https://unifiedportal-mem.epfindia.gov.in",
        purpose="Online Joint Declaration submitted through employer digital signature on Member Portal for demographic alignment.",
    ),
    "form_cbse_name_correction": MappedFormRef(
        form_id="form_cbse_name_correction",
        form_name="CBSE Application Form for Correction in Candidate / Parents' Name or DOB",
        issuing_authority="Central Board of Secondary Education (CBSE)",
        official_download_url="https://www.cbse.gov.in/newsite/forms.html",
        purpose="Application to correct clerical/typographical discrepancies in Class 10 or 12 Certificates.",
    ),
    "form_gazette_name_change": MappedFormRef(
        form_id="form_gazette_name_change",
        form_name="Proforma for Change of Name Advertisement in The Gazette of India (Part IV)",
        issuing_authority="Department of Publication, Ministry of Housing and Urban Affairs",
        official_download_url="https://egazette.gov.in",
        purpose="Official statutory proforma required to publish change of name in the weekly Gazette of India.",
    ),
}


class ResolutionMappingService:
    """
    Deterministic resolution mapper.
    Maps discrepancy classifications and document pairings directly into verified
    statutory correction workflows, required forms, document checklists, and authorities.
    """

    @classmethod
    def map_conflict(
        cls,
        field_name: str,
        deterministic_classification: str,
        document_types: List[str],
        ocr_quality_warning: Optional[str] = None,
        non_latin_warning: Optional[str] = None,
        requires_manual_review: bool = False,
    ) -> ResolutionProcedureMapping:
        """
        Deterministically produces a ResolutionProcedureMapping.
        Prioritizes fail-safes (low OCR confidence, non-Latin script) before document pairing logic.
        """
        field = (field_name or "").lower().strip()
        det_cls = (deterministic_classification or "").upper().strip()
        norm_types = [cls._normalize_doc_type(t) for t in (document_types or [])]

        # 1. Fail-Safe: OCR Quality Below Confidence Floor
        if ocr_quality_warning or det_cls == "LOW_CONFIDENCE_NEEDS_REVIEW":
            return ResolutionProcedureMapping(
                target_document_category="scan_quality_review",
                authority_name="CONVELINA Document Verification System",
                authority_portal="https://convelina.internal/quality",
                procedure_name="High-Resolution Document Re-Scan and Manual Inspection",
                procedure_type="manual_review",
                prescribed_forms=[],
                document_checklist=[
                    "Original physical identity document (no photocopies of photocopies)",
                    "Color scan at 300+ DPI with uniform lighting and no flash glare",
                    "All 4 edges and corners of the document fully visible",
                ],
                submission_channel="internal_review",
                statutory_rules=[
                    "Automatic statutory filing must NOT be initiated when OCR confidence is below 60%.",
                    "Values must be visually confirmed by the citizen prior to official authority submission.",
                ],
                official_fee_guidance="None (Internal data verification)",
                sla_guidance="Immediate upon clean re-scan",
                action_priority="high",
            )

        # 2. Fail-Safe: Non-Latin / Regional Indic Script Detected
        if non_latin_warning or det_cls == "UNRESOLVABLE_NON_LATIN_SCRIPT":
            return ResolutionProcedureMapping(
                target_document_category="certified_translation",
                authority_name="Authorized Notary Public / Certified Translator",
                authority_portal="https://egazette.gov.in",
                procedure_name="Certified Script Translation and Notarized Verification",
                procedure_type="manual_review",
                prescribed_forms=[],
                document_checklist=[
                    "Original document in regional/Indic script",
                    "Certified English or Hindi translation and transliteration certificate by a licensed notary/translator",
                    "Self-attested affidavit confirming phonetic identity across scripts",
                ],
                submission_channel="physical_notary",
                statutory_rules=[
                    "Non-Latin script transliteration cannot be deterministically verified by automated character analysis.",
                    "Official statutory authorities (Passport Seva, ITD, EPFO) require certified English/Hindi documentation.",
                ],
                official_fee_guidance="Standard notary attestation fee (Rs 100 - Rs 500 depending on state)",
                sla_guidance="1-2 working days for notary verification",
                action_priority="high",
            )

        # 3. Document Category Pairings
        has_aadhaar = "aadhaar" in norm_types
        has_pan = "pan" in norm_types
        has_passport = "passport" in norm_types
        has_edu10 = "education_10th" in norm_types or "education" in norm_types
        has_edu12 = "education_12th" in norm_types
        has_epf = "epf" in norm_types

        # SCENARIO A: EPF / UAN Profile Discrepancy (Aadhaar <-> EPF or PAN <-> EPF)
        if has_epf:
            return cls._map_epf_resolution(field, det_cls, has_aadhaar)

        # SCENARIO B: Aadhaar <-> Education Certificate (Class 10 Matriculation Root)
        if has_edu10 and has_aadhaar:
            return cls._map_aadhaar_education_resolution(field, det_cls)

        # SCENARIO C: Class 12 <-> Class 10 Marksheet Alignment
        if has_edu12 and has_edu10:
            return cls._map_cbse_12th_alignment_resolution(field, det_cls)

        # SCENARIO D: Aadhaar <-> PAN Discrepancy (Demographic linking alignment)
        if has_aadhaar and has_pan:
            return cls._map_aadhaar_pan_resolution(field, det_cls)

        # SCENARIO E: Passport <-> Other Public ID (Aadhaar, PAN, Education)
        if has_passport:
            return cls._map_passport_resolution(field, det_cls)

        # SCENARIO F: Standalone Education Certificate
        if has_edu10 or has_edu12:
            return cls._map_education_standalone_resolution(field, det_cls)

        # SCENARIO G: Generic Aadhaar Update
        if has_aadhaar:
            return cls._map_aadhaar_generic_resolution(field, det_cls)

        # SCENARIO H: Generic PAN Update
        if has_pan:
            return cls._map_pan_generic_resolution(field, det_cls)

        # Default Fallback for Unclassified Document Pairings
        return cls._map_default_unclassified(field, det_cls, document_types)

    # -------------------------------------------------------------------------
    # Scenario Mappers
    # -------------------------------------------------------------------------

    @classmethod
    def _map_aadhaar_pan_resolution(cls, field: str, det_cls: str) -> ResolutionProcedureMapping:
        """Aadhaar <-> PAN demographic conflict resolution."""
        is_major = det_cls in ("MISMATCH", "HIGH_RISK_GENUINE_MISMATCH", "UNRESOLVABLE_CONFLICT")
        csf_form = KNOWN_OFFICIAL_FORMS["form_pan_csf_correction"]
        gz_form = KNOWN_OFFICIAL_FORMS["form_gazette_name_change"]

        if is_major and field in ("name", "full_name"):
            return ResolutionProcedureMapping(
                target_document_category="pan",
                authority_name="Income Tax Department / Protean (NSDL) & Department of Publication",
                authority_portal="https://www.tin-nsdl.com/services/pan/pan-change-correction.html",
                procedure_name="Major PAN Name Change with Gazette Notification",
                procedure_type="major_name_change",
                prescribed_forms=[csf_form, gz_form],
                document_checklist=[
                    "Official Gazette of India notification copy publishing change of name",
                    "Two original newspaper advertisements (one English, one regional)",
                    "Copy of existing PAN card",
                    "Aadhaar card copy reflecting the correct legal name",
                ],
                submission_channel="physical_center",
                statutory_rules=[
                    "Possessing more than one PAN card is a punishable offense under Section 272B (penalty Rs 10,000).",
                    "Demographic match between PAN and Aadhaar is mandatory for statutory tax filing under Section 139AA.",
                    "Major name change requires prior publication in The Gazette of India Part IV.",
                ],
                official_fee_guidance="Rs 107 for physical PAN dispatch within India",
                sla_guidance="15 to 20 working days post physical dossier receipt",
                action_priority="high",
            )

        # Minor variation / initial expansion / order reversal / DOB / Father name
        forms = [csf_form]
        procedure_title = "PAN Data Correction via Form CSF (Aadhaar Demographic Alignment)"
        checklist = [
            "Self-attested copy of existing PAN card",
            "Self-attested copy of Aadhaar card (reflecting the exact target spelling/DOB)",
            "Two recent passport-size color photographs (for physical form submission)",
        ]

        if field in ("date_of_birth", "dob"):
            checklist.append("Proof of Date of Birth (Aadhaar or Municipal Birth Certificate)")

        return ResolutionProcedureMapping(
            target_document_category="pan",
            authority_name="Income Tax Department / Protean (NSDL e-Gov)",
            authority_portal="https://www.tin-nsdl.com/services/pan/pan-change-correction.html",
            procedure_name=procedure_title,
            procedure_type="minor_correction",
            prescribed_forms=forms,
            document_checklist=checklist,
            submission_channel="online_portal",
            statutory_rules=[
                "Online e-Sign / e-KYC route is available if mobile number is linked to Aadhaar.",
                "Never apply for a new PAN card; possessing multiple PANs is an offense under Section 272B (penalty Rs 10,000).",
                "Tick only the specific checkboxes corresponding to the fields requiring change.",
            ],
            official_fee_guidance="Rs 101 to Rs 107 for Indian address delivery",
            sla_guidance="7 to 10 working days via paperless e-KYC mode",
            action_priority="high" if field in ("name", "full_name", "date_of_birth") else "medium",
        )

    @classmethod
    def _map_aadhaar_education_resolution(cls, field: str, det_cls: str) -> ResolutionProcedureMapping:
        """Aadhaar <-> Class 10 Matriculation conflict (Matriculation is root proof)."""
        adult_form = KNOWN_OFFICIAL_FORMS["form_aadhaar_update_adult"]
        gz_form = KNOWN_OFFICIAL_FORMS["form_gazette_name_change"]

        if field in ("date_of_birth", "dob"):
            return ResolutionProcedureMapping(
                target_document_category="aadhaar",
                authority_name="Unique Identification Authority of India (UIDAI)",
                authority_portal="https://myaadhaar.uidai.gov.in",
                procedure_name="Aadhaar Date of Birth Update using Class 10 Matriculation Certificate",
                procedure_type="statutory_linkage",
                prescribed_forms=[adult_form],
                document_checklist=[
                    "Original Class 10 Secondary Examination Marksheet/Certificate showing DOB",
                    "Aadhaar Enrolment / Update Form (Adult 18+)",
                    "Current original Aadhaar card or letter",
                ],
                submission_channel="physical_center",
                statutory_rules=[
                    "UIDAI permits Date of Birth correction ONLY ONCE in a resident's lifetime.",
                    "Class 10 Matriculation Certificate issued by recognized Boards (CBSE/ICSE/State) is accepted as primary Proof of Date of Birth (PDB).",
                    "If difference exceeds +/- 3 years from originally recorded date, approval from UIDAI Regional Office is required.",
                ],
                official_fee_guidance="Rs 50 statutory demographic update fee at Aadhaar Seva Kendra",
                sla_guidance="7 to 15 working days post biometric verification",
                action_priority="high",
            )

        # Name variation (Initials / Transliteration / Surname)
        is_major = det_cls in ("MISMATCH", "HIGH_RISK_GENUINE_MISMATCH", "UNRESOLVABLE_CONFLICT")
        forms = [adult_form, gz_form] if is_major else [adult_form]

        return ResolutionProcedureMapping(
            target_document_category="aadhaar",
            authority_name="Unique Identification Authority of India (UIDAI)",
            authority_portal="https://myaadhaar.uidai.gov.in",
            procedure_name="Aadhaar Name Correction to Align with Class 10 Matriculation Record",
            procedure_type="major_name_change" if is_major else "minor_correction",
            prescribed_forms=forms,
            document_checklist=[
                "Original Class 10 Board Marksheet / Passing Certificate with candidate photograph",
                "Aadhaar Enrolment / Update Form (Adult 18+)",
            ] + (["Official Gazette of India notification copy"] if is_major else []),
            submission_channel="physical_center",
            statutory_rules=[
                "A resident can update their name in Aadhaar a maximum of TWO (2) times in their lifetime.",
                "Original education certificate must be presented for physical scanning; no photocopies without originals.",
                "Class 10 education certificate is the primary root proof in India; changing school records after 5 years is legally restrictive.",
            ],
            official_fee_guidance="Rs 50 statutory update fee",
            sla_guidance="7 to 14 working days",
            action_priority="medium" if not is_major else "high",
        )

    @classmethod
    def _map_epf_resolution(cls, field: str, det_cls: str, has_aadhaar: bool) -> ResolutionProcedureMapping:
        """EPFO Member / UAN profile discrepancy resolution."""
        jd_form = KNOWN_OFFICIAL_FORMS["form_epf_joint_declaration"]
        digital_jd = KNOWN_OFFICIAL_FORMS["form_epfo_digital_jd"]

        checklist = [
            "Joint Declaration Form signed by employee and authorized employer signatory",
            "Self-attested copy of Aadhaar card (mandatory under Section 142)",
            "Self-attested copy of PAN card",
        ]
        if field in ("date_of_birth", "dob"):
            checklist.append("Class 10 Certificate or Municipal Birth Certificate (mandatory if DOB difference > 3 years)")

        return ResolutionProcedureMapping(
            target_document_category="epf",
            authority_name="Employees' Provident Fund Organisation (EPFO)",
            authority_portal="https://unifiedportal-mem.epfindia.gov.in",
            procedure_name="EPFO Joint Declaration for Member Profile Correction",
            procedure_type="statutory_linkage",
            prescribed_forms=[jd_form, digital_jd],
            document_checklist=checklist,
            submission_channel="joint_employer_physical",
            statutory_rules=[
                "Section 142 of the Code on Social Security mandates exact Aadhaar demographic matching for PF claims.",
                "Correction request requires mandatory verification and digital signature (DSC) of the employer.",
                "If establishment is closed, the Joint Declaration must be attested by a designated authority (Bank Manager / Gazetted Officer).",
            ],
            official_fee_guidance="Free of cost (Official statutory service)",
            sla_guidance="15 to 30 working days post employer digital approval",
            action_priority="high",
        )

    @classmethod
    def _map_passport_resolution(cls, field: str, det_cls: str) -> ResolutionProcedureMapping:
        """Ministry of External Affairs Passport Seva Re-issue."""
        reissue_form = KNOWN_OFFICIAL_FORMS["form_passport_reissue"]
        annexure_e = KNOWN_OFFICIAL_FORMS["form_passport_annexure_e"]
        gazette_form = KNOWN_OFFICIAL_FORMS["form_gazette_name_change"]

        is_major = det_cls in ("MISMATCH", "HIGH_RISK_GENUINE_MISMATCH", "UNRESOLVABLE_CONFLICT")

        if is_major and field in ("name", "full_name"):
            return ResolutionProcedureMapping(
                target_document_category="passport",
                authority_name="Ministry of External Affairs (CPV Division / Passport Seva)",
                authority_portal="https://www.passportindia.gov.in",
                procedure_name="Passport Re-Issue for Major Name Change (Gazette & Annexure E Route)",
                procedure_type="major_name_change",
                prescribed_forms=[reissue_form, annexure_e, gazette_form],
                document_checklist=[
                    "Current original Indian passport alongside self-attested photocopies of first and last pages",
                    "Annexure 'E' Deed Poll Affidavit executed on non-judicial stamp paper attested by First Class Magistrate/Notary",
                    "Two original daily newspaper advertisements (one English, one vernacular circulating in permanent residence)",
                    "Original copy of the Official Gazette of India notification publishing change of name",
                ],
                submission_channel="physical_center",
                statutory_rules=[
                    "Major change of first name or addition of unrelated surname requires mandatory Gazette Notification.",
                    "Physical biometric verification at Passport Seva Kendra (PSK/POPSK) is compulsory.",
                    "Police Verification (Pre or Post) will be initiated by the Passport Issuing Authority.",
                ],
                official_fee_guidance="Rs 1,500 (Normal 36-page booklet) or Rs 2,000 (60-page jumbo booklet)",
                sla_guidance="20 to 30 working days post police verification",
                action_priority="high",
            )

        # Minor spelling / Initial expansion in passport
        return ResolutionProcedureMapping(
            target_document_category="passport",
            authority_name="Ministry of External Affairs (CPV Division)",
            authority_portal="https://www.passportindia.gov.in",
            procedure_name="Passport Re-Issue for Minor Correction in Personal Particulars",
            procedure_type="minor_correction",
            prescribed_forms=[reissue_form],
            document_checklist=[
                "Original existing passport with copy of first and last two pages",
                "At least two public identity documents in the correct name (e.g. Aadhaar, PAN, or Matriculation Certificate)",
                "Self-attested address proof if residential address has changed",
            ],
            submission_channel="physical_center",
            statutory_rules=[
                "Minor spelling correction not altering phonetic sound does not require newspaper publication or Gazette notification.",
                "Applicant must book an appointment and visit PSK/POPSK for physical biometrics and document verification.",
            ],
            official_fee_guidance="Rs 1,500 for standard 36-page booklet",
            sla_guidance="10 to 15 working days",
            action_priority="medium",
        )

    @classmethod
    def _map_cbse_12th_alignment_resolution(cls, field: str, det_cls: str) -> ResolutionProcedureMapping:
        """Class 12 Senior School Certificate alignment with Class 10 Matriculation."""
        cbse_form = KNOWN_OFFICIAL_FORMS["form_cbse_name_correction"]

        return ResolutionProcedureMapping(
            target_document_category="education_12th",
            authority_name="Central Board of Secondary Education (CBSE)",
            authority_portal="https://www.cbse.gov.in/cbsenew/duplicate.html",
            procedure_name="CBSE Class 12 Certificate Alignment with Class 10 Record (Rule 69.1)",
            procedure_type="minor_correction",
            prescribed_forms=[cbse_form],
            document_checklist=[
                "Certified copy of Class 10 Secondary Examination Passing Certificate",
                "School Admission Register extract certified by the Principal of Senior Secondary School",
                "Original Class 12 marksheet / certificate requiring correction",
                "Prescribed CBSE regional fee challan",
            ],
            submission_channel="physical_school",
            statutory_rules=[
                "Class 10 Matriculation certificate is the root foundational record in Indian education.",
                "Candidate name, parents' names, and DOB in Class 12 must strictly match Class 10 records.",
                "Application must be forwarded through the Head of the School within 5 years of examination result declaration.",
            ],
            official_fee_guidance="Rs 1,000 correction fee + Rs 500 for duplicate corrected certificate",
            sla_guidance="30 to 45 working days post school forwarding to Regional Office",
            action_priority="medium",
        )

    @classmethod
    def _map_education_standalone_resolution(cls, field: str, det_cls: str) -> ResolutionProcedureMapping:
        """Standalone education board certificate discrepancy."""
        cbse_form = KNOWN_OFFICIAL_FORMS["form_cbse_name_correction"]
        gz_form = KNOWN_OFFICIAL_FORMS["form_gazette_name_change"]

        return ResolutionProcedureMapping(
            target_document_category="education",
            authority_name="Secondary / Senior Secondary Education Board (CBSE / State Board)",
            authority_portal="https://www.cbse.gov.in/newsite/examination-bye-laws.html",
            procedure_name="School Board Examination Certificate Correction (Rule 69)",
            procedure_type="minor_correction",
            prescribed_forms=[cbse_form, gz_form],
            document_checklist=[
                "School Admission Form and Withdrawal Register extract certified by School Principal",
                "Affidavit executed before First Class Magistrate (if beyond 5 years of examination)",
                "Official Gazette Notification copy (if major name change post-examination)",
            ],
            submission_channel="physical_school",
            statutory_rules=[
                "Clerical corrections must strictly conform to original school admission register entries.",
                "Under Supreme Court ruling (Jigya Yadav vs CBSE), post-schooling legal name changes require Gazette Notification.",
            ],
            official_fee_guidance="Rs 1,000 per certificate",
            sla_guidance="30 to 60 working days",
            action_priority="medium",
        )

    @classmethod
    def _map_aadhaar_generic_resolution(cls, field: str, det_cls: str) -> ResolutionProcedureMapping:
        """Generic Aadhaar demographic update."""
        adult_form = KNOWN_OFFICIAL_FORMS["form_aadhaar_update_adult"]
        return ResolutionProcedureMapping(
            target_document_category="aadhaar",
            authority_name="Unique Identification Authority of India (UIDAI)",
            authority_portal="https://myaadhaar.uidai.gov.in",
            procedure_name="Aadhaar Demographic Update (Aadhaar Seva Kendra)",
            procedure_type="minor_correction",
            prescribed_forms=[adult_form],
            document_checklist=[
                "Valid Proof of Identity (Passport, PAN Card, Voter ID, or Board Certificate)",
                "Aadhaar Enrolment / Update Form (Adult 18+)",
            ],
            submission_channel="physical_center",
            statutory_rules=[
                "Maximum 2 name updates and 1 date of birth update allowed in a lifetime.",
                "Original documents must be presented at the Seva Kendra for scanning.",
            ],
            official_fee_guidance="Rs 50 demographic update fee",
            sla_guidance="7 to 15 working days",
            action_priority="medium",
        )

    @classmethod
    def _map_pan_generic_resolution(cls, field: str, det_cls: str) -> ResolutionProcedureMapping:
        """Generic PAN data correction."""
        csf_form = KNOWN_OFFICIAL_FORMS["form_pan_csf_correction"]
        return ResolutionProcedureMapping(
            target_document_category="pan",
            authority_name="Income Tax Department / Protean (NSDL)",
            authority_portal="https://www.tin-nsdl.com/services/pan/pan-change-correction.html",
            procedure_name="PAN Data Correction (Form CSF)",
            procedure_type="minor_correction",
            prescribed_forms=[csf_form],
            document_checklist=[
                "Copy of existing PAN card",
                "Proof of Identity in the corrected name (Aadhaar / Passport / Voter ID)",
            ],
            submission_channel="online_portal",
            statutory_rules=[
                "Never apply for a new PAN card if you already possess one (Section 272B penalty).",
            ],
            official_fee_guidance="Rs 101 - Rs 107",
            sla_guidance="7 to 12 working days",
            action_priority="medium",
        )

    @classmethod
    def _map_default_unclassified(
        cls, field: str, det_cls: str, doc_types: List[str]
    ) -> ResolutionProcedureMapping:
        """Fallback for unclassified or custom identity document pairings."""
        return ResolutionProcedureMapping(
            target_document_category=doc_types[0] if doc_types else "identity_document",
            authority_name="Jurisdictional Issuing Authority",
            authority_portal="https://india.gov.in",
            procedure_name="Administrative Demographic Correction and Record Verification",
            procedure_type="manual_review",
            prescribed_forms=[],
            document_checklist=[
                "Original primary identity document",
                "Supporting documentary proof reflecting the correct legal particulars",
                "Self-attested resident declaration / affidavit where applicable",
            ],
            submission_channel="physical_center",
            statutory_rules=[
                "Review document scans manually before submitting statutory change requests.",
                "Consult the official issuing authority guidelines for document-specific evidentiary requirements.",
            ],
            official_fee_guidance="Varies by authority",
            sla_guidance="Standard administrative processing window",
            action_priority="medium",
        )

    @staticmethod
    def _normalize_doc_type(doc_type: str) -> str:
        """Normalizes document types to canonical taxonomy keys."""
        t = (doc_type or "").lower().strip()
        if "aadhaar" in t:
            return "aadhaar"
        if "pan" in t:
            return "pan"
        if "passport" in t:
            return "passport"
        if "12" in t or "senior" in t or "hsc" in t:
            return "education_12th"
        if "10" in t or "matric" in t or "ssc" in t:
            return "education_10th"
        if "education" in t or "marksheet" in t or "certificate" in t:
            return "education_10th"
        if "epf" in t or "uan" in t or "pf" in t:
            return "epf"
        if "gazette" in t:
            return "gazette"
        return t
