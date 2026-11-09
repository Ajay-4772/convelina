import os
import csv
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.rag.schemas import (
    RepositoryResourceItem,
    RepositoryResourceDetail,
    RepositoryResourceListResponse,
    SourceCitation,
    ChecklistItem,
)
from app.services.checklist_service import ChecklistService, STATUTORY_CHECKLISTS
from app.models.official_form import OfficialForm
from app.core.storage import get_official_form_path

logger = logging.getLogger("convelina.repository.service")

# Map of raw categories to the 6 standard CONVELINA identity categories
CATEGORY_NORMALIZATION = {
    "01_aadhaar": "aadhaar",
    "aadhaar": "aadhaar",
    "02_pan": "pan",
    "pan": "pan",
    "03_passport": "passport",
    "passport": "passport",
    "04_class_10": "class_10",
    "class_10": "class_10",
    "education_10th": "class_10",
    "05_class_12": "class_12",
    "class_12": "class_12",
    "education_12th": "class_12",
    "education": "class_10",
    "06_epfo_uan": "epf",
    "epf": "epf",
    "epfo": "epf",
    "uan": "epf",
    "07_cross_category": "cross_category",
    "cross_category": "cross_category",
    "gazette": "cross_category",
    "08_unclassified": "unclassified",
    "09_irrelevant_quarantine": "quarantine",
    "10_duplicates_review": "duplicate",
}

CATEGORY_METADATA = {
    "aadhaar": {
        "id": "aadhaar",
        "name": "Aadhaar Card",
        "authority": "Unique Identification Authority of India (UIDAI)",
        "description": "Statutory application forms, acceptable supporting document matrices, and procedural SOPs for adult, child, and infant Aadhaar demographic and biometric updates.",
    },
    "pan": {
        "id": "pan",
        "name": "PAN Card",
        "authority": "Income Tax Department / NSDL / Protean",
        "description": "Form CSF (Changes or Correction in PAN Data) and proof eligibility guidelines under Rule 114 of Income Tax Rules, 1962.",
    },
    "passport": {
        "id": "passport",
        "name": "Passport",
        "authority": "Ministry of External Affairs (Consular, Passport and Visa Division)",
        "description": "Passport Seva System re-issue applications, Annexure 'E' deed poll proformas, and documentary guidelines for name and personal particulars corrections.",
    },
    "class_10": {
        "id": "class_10",
        "name": "Class 10 Certificate",
        "authority": "Central Board of Secondary Education (CBSE) & State Examination Boards",
        "description": "Secondary school leaving marksheet and passing certificate correction forms, admission register extracts, and examination byelaws.",
    },
    "class_12": {
        "id": "class_12",
        "name": "Class 12 Certificate",
        "authority": "Central Board of Secondary Education (CBSE) & Senior Secondary Boards",
        "description": "Senior School Certificate correction applications and reconciliation protocols linking Class 12 credentials with foundational Class 10 records.",
    },
    "epf": {
        "id": "epf",
        "name": "EPF/UAN Records",
        "authority": "Employees' Provident Fund Organisation (EPFO)",
        "description": "Standard Joint Declaration Proforma (Member & Employer) for correcting member name, father's name, date of birth, and date of joining.",
    },
}


class CitizenRepositoryService:
    """
    Unified Citizen Document Repository Service (Phase P3H.6).
    Aggregates:
    1. 47 official reconciled statutory circulars, forms, and matrices (DOC_001 to DOC_047).
    2. Registered official application forms from the official forms catalog.
    Enforces strict provenance, verification status, and mandatory synthetic/conflict disclaimers.
    """

    _cached_catalog: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def _get_project_root(cls) -> str:
        # Assumes running from backend or project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Walk up to find directory containing 'forms' and 'backend'
        root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        if os.path.exists(os.path.join(root, "forms")):
            return root
        # Fallback to working directory
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "forms")):
            return cwd
        return root

    @classmethod
    def _parse_doc_profile(cls, doc_id: str, root_dir: str) -> Dict[str, Any]:
        """Reads detailed markdown profile for a document if available."""
        profile_path = os.path.join(root_dir, "forms", "DOCUMENT_PROFILES", f"{doc_id}.md")
        if not os.path.exists(profile_path):
            return {}

        details: Dict[str, Any] = {
            "key_information_required": [],
            "referenced_laws": [],
            "limitations_and_warnings": [],
            "purpose_extended": "",
            "intended_cohort": "GENERAL_CITIZEN",
            "source_url": "https://uidai.gov.in" if "AADHAAR" in doc_id or int(doc_id.replace("DOC_", "")) <= 28 else "https://incometax.gov.in",
        }

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract Intended Audience
            m_aud = re.search(r"-\s*\*\*Intended Audience:\*\*\s*(.*)", content)
            if m_aud:
                details["intended_cohort"] = m_aud.group(1).strip()

            # Extract Key Information Required
            m_key = re.search(r"-\s*\*\*Key Information Required:\*\*\s*(.*)", content)
            if m_key:
                raw_info = m_key.group(1).strip()
                details["key_information_required"] = [i.strip() for i in raw_info.split(",") if i.strip()]

            # Extract Referenced Laws
            m_laws = re.search(r"-\s*\*\*Referenced Laws & Circulars:\*\*\s*(.*)", content)
            if m_laws:
                raw_laws = m_laws.group(1).strip()
                details["referenced_laws"] = [l.strip() for l in raw_laws.split(",") if l.strip()]

            # Extract Limitations / Warnings
            m_warn = re.search(r"-\s*\*\*Important Limitations / Warnings:\*\*\s*(.*)", content)
            if m_warn:
                details["limitations_and_warnings"].append(m_warn.group(1).strip())

            # Extract Official Source URL
            m_url = re.search(r"-\s*\*\*Official Source URL:\*\*\s*(https?://[^\s]+)", content)
            if m_url:
                details["source_url"] = m_url.group(1).strip()

        except Exception as e:
            logger.warning("Error parsing document profile %s: %s", doc_id, e)

        return details

    @classmethod
    def _build_catalog(cls) -> List[Dict[str, Any]]:
        root = cls._get_project_root()
        recon_path = os.path.join(root, "forms", "P3H4_1_CORPUS_RECONCILIATION.csv")
        catalog: List[Dict[str, Any]] = []

        if os.path.exists(recon_path):
            try:
                with open(recon_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        doc_id = row.get("document_id", "")
                        orig_filename = row.get("original_filename", "")
                        raw_cat = row.get("document_category", "AADHAAR").lower()
                        normalized_cat = CATEGORY_NORMALIZATION.get(raw_cat, "aadhaar")
                        doc_func = row.get("document_function", "REFERENCE_ONLY")
                        curr_status = row.get("currency_status", "CURRENT")
                        provenance_raw = row.get("provenance_authenticity_status", "AUTHENTIC_OFFICIAL")
                        sha256 = row.get("sha256", "")
                        cohort = row.get("applicant_cohort", "GENERAL_CITIZEN")
                        inclusion_reason = row.get("inclusion_exclusion_reason", "")

                        # Assign Provenance Classification (7 distinct classes)
                        if provenance_raw == "AUTHENTICITY_UNCONFIRMED":
                            provenance = "UNVERIFIED_SOURCE"
                        elif curr_status == "HISTORICAL":
                            provenance = "HISTORICAL_REFERENCE"
                        elif doc_func in ("PROOF_ELIGIBILITY_RULES", "REFERENCE_ONLY"):
                            provenance = "GOVERNMENT_REFERENCE"
                        elif doc_func == "APPLICATION_FORM":
                            provenance = "OFFICIAL_ORIGINAL"
                        else:
                            provenance = "GOVERNMENT_REFERENCE"

                        # Assign Verification State (5 distinct states)
                        if doc_id == "DOC_043":
                            verification_status = "source_metadata_conflict"
                            human_review_required = True
                        elif provenance_raw == "AUTHENTICITY_UNCONFIRMED":
                            verification_status = "needs_review"
                            human_review_required = True
                        elif curr_status == "HISTORICAL":
                            verification_status = "outdated"
                            human_review_required = True
                        elif curr_status == "DUPLICATE":
                            verification_status = "retired"
                            human_review_required = False
                        else:
                            verification_status = "verified"
                            human_review_required = False

                        # Map Document Type
                        if doc_func == "APPLICATION_FORM":
                            doc_type = "application_form"
                        elif doc_func == "PROOF_ELIGIBILITY_RULES":
                            doc_type = "proof_matrix"
                        elif doc_func == "CORRECTION_PROCEDURE":
                            doc_type = "correction_procedure"
                        elif doc_func == "ALTERNATIVE_EVIDENCE":
                            doc_type = "alternative_evidence"
                        else:
                            doc_type = "reference_circular"

                        # Issuing Authority
                        if "pan" in normalized_cat or "form 9" in orig_filename.lower():
                            authority = "Income Tax Department / NSDL"
                        else:
                            authority = "Unique Identification Authority of India (UIDAI)"

                        # Title cleanup
                        title = orig_filename.replace(".pdf", "").replace("_", " ").strip()
                        if doc_id == "DOC_001":
                            title = "Aadhaar Enrolment and Update Form (Adults aged 18+)"
                        elif doc_id == "DOC_013":
                            title = "Certificate for Aadhaar Enrolment/Update Standard Proforma"
                        elif doc_id == "DOC_022":
                            title = "Aadhaar Enrolment & Update Form (Children aged 5 to 18)"
                        elif doc_id == "DOC_023":
                            title = "Bal Aadhaar Enrolment Form (Children below 5 years)"
                        elif doc_id == "DOC_034":
                            title = "UIDAI List of Acceptable Supporting Documents (Proof of Identity, Address, DOB, Relationship)"
                        elif doc_id == "DOC_036":
                            title = "PAN Request for New PAN Card / Changes or Correction in PAN Data (Form CSF)"
                        elif doc_id == "DOC_043":
                            title = "UIDAI Standard Operating Procedure (SOP) for Updating Name in Aadhaar"

                        # Parse detailed markdown profile
                        profile_data = cls._parse_doc_profile(doc_id, root)

                        # Locate original physical PDF path in repository
                        rel_storage_path = None
                        file_size = 0
                        for folder in ["01_AADHAAR/Forms", "01_AADHAAR/Checklists", "01_AADHAAR/Circulars",
                                       "01_AADHAAR/Guidelines", "01_AADHAAR/Notifications", "01_AADHAAR/SOPs",
                                       "02_PAN/Forms", "07_CROSS_CATEGORY/Forms", "08_UNCLASSIFIED",
                                       "09_IRRELEVANT_QUARANTINE", "10_DUPLICATES_REVIEW"]:
                            cand_path = os.path.join(root, "forms", folder, orig_filename)
                            if os.path.exists(cand_path):
                                rel_storage_path = os.path.relpath(cand_path, root).replace("\\", "/")
                                file_size = os.path.getsize(cand_path)
                                break

                        # Determine related procedures
                        related_procedures = []
                        if "aadhaar" in normalized_cat:
                            if "dob" in title.lower():
                                related_procedures.append("aadhaar_dob_update")
                            elif "address" in title.lower():
                                related_procedures.append("aadhaar_address_update")
                            elif "name" in title.lower() or doc_id in ("DOC_001", "DOC_034", "DOC_043"):
                                related_procedures.extend(["aadhaar_name_update", "aadhaar_name_update_major_gazette"])
                            else:
                                related_procedures.append("aadhaar_name_update")
                        elif "pan" in normalized_cat:
                            related_procedures.append("pan_name_correction_csf")

                        # Mandatory Disclaimers
                        disclaimer = None
                        if doc_id == "DOC_043":
                            disclaimer = (
                                "STATUTORY LIMITATION NOTICE: DOC_043 retains an unverified source metadata conflict. "
                                "Claims regarding third-time exceptions and Regional Office escalation packets cannot be represented as definitive law."
                            )
                        elif provenance == "HISTORICAL_REFERENCE":
                            disclaimer = "HISTORICAL REFERENCE ONLY — SUPERSEDED. Retained for audit lineage only and not valid for current statutory filings."
                        elif provenance == "UNVERIFIED_SOURCE":
                            disclaimer = "UNVERIFIED SOURCE — Under administrative review. Not established as verified government instruction."

                        catalog.append({
                            "id": doc_id,
                            "resource_id": doc_id,
                            "title": title,
                            "issuing_authority": authority,
                            "document_category": normalized_cat,
                            "document_type": doc_type,
                            "description": inclusion_reason,
                            "purpose": inclusion_reason,
                            "intended_cohort": cohort,
                            "applicable_categories": [normalized_cat],
                            "publication_date": "2023" if "2023" in orig_filename else ("2026" if "2026" in orig_filename else "2021"),
                            "effective_date": "2023-01-01",
                            "verification_status": verification_status,
                            "provenance": provenance,
                            "provenance_notes": f"Reconciled official corpus document. Status: {provenance_raw}, Currency: {curr_status}.",
                            "is_official_government_form": (provenance in ("OFFICIAL_ORIGINAL", "OFFICIAL_COPY") and verification_status == "verified"),
                            "is_synthetic_sample": False,
                            "is_historical": (curr_status == "HISTORICAL"),
                            "has_source_conflict": (doc_id == "DOC_043"),
                            "human_review_required": human_review_required,
                            "file_format": "pdf",
                            "file_size_bytes": file_size,
                            "sha256_hash": sha256,
                            "storage_path": rel_storage_path,
                            "download_available": (rel_storage_path is not None and curr_status != "DUPLICATE"),
                            "original_source_url": profile_data.get("source_url", "https://uidai.gov.in"),
                            "key_information_required": profile_data.get("key_information_required", [
                                "Demographic details (Name, DOB, Gender, Address)",
                                "Supporting Proof of Identity (PoI) and Proof of Address (PoA)",
                                "Applicant declaration signature",
                            ]),
                            "referenced_laws": profile_data.get("referenced_laws", [
                                "Aadhaar (Enrolment and Update) Regulations, 2016",
                                "Aadhaar Act, 2016 (Section 7 & 12A)",
                            ]),
                            "related_procedures": related_procedures,
                            "limitations_and_warnings": profile_data.get("limitations_and_warnings", [
                                "Requires verification at an authorized enrollment center.",
                            ]),
                            "disclaimer": disclaimer,
                        })
            except Exception as e:
                logger.error("Failed to parse P3H4_1_CORPUS_RECONCILIATION.csv: %s", e)

        # Merge statutory application forms from OFFICIAL_FORMS_DATA
        # This provides complete coverage across Passport, Class 10, Class 12, and EPF
        additional_forms = [
            {
                "id": "form_passport_reissue",
                "resource_id": "form_passport_reissue",
                "title": "Application for Re-issue of Indian Passport (Passport Seva)",
                "issuing_authority": "Ministry of External Affairs (CPV Division)",
                "document_category": "passport",
                "document_type": "application_form",
                "description": "Standard Passport Seva application proforma for re-issue of Indian passport due to exhaustion of pages, name change, or change of personal particulars.",
                "purpose": "Citizen application for obtaining a re-issued Indian Passport reflecting updated demographic particulars.",
                "intended_cohort": "GENERAL_CITIZEN",
                "applicable_categories": ["passport"],
                "publication_date": "2024",
                "effective_date": "2024-01-01",
                "verification_status": "verified",
                "provenance": "SYNTHETIC_DEVELOPMENT_SAMPLE",
                "provenance_notes": "Application-generated development template with full statutory fields. Download official form from passportindia.gov.in.",
                "is_official_government_form": False,
                "is_synthetic_sample": True,
                "is_historical": False,
                "has_source_conflict": False,
                "human_review_required": False,
                "file_format": "pdf",
                "file_size_bytes": 14250,
                "sha256_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
                "storage_path": "backend/data/official_forms/form_passport_reissue.pdf",
                "download_available": True,
                "original_source_url": "https://www.passportindia.gov.in",
                "key_information_required": [
                    "Existing Passport Number and date/place of issue",
                    "Applicant full legal name and parentage",
                    "Proof of current residential address",
                    "Annexure 'E' affidavit if minor name change",
                ],
                "referenced_laws": ["Passports Act, 1967", "Passports Rules, 1980"],
                "related_procedures": ["passport_reissue_correction"],
                "limitations_and_warnings": [
                    "Original passport must be physically inspected at Passport Seva Kendra.",
                ],
                "disclaimer": "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM",
            },
            {
                "id": "form_cbse_name_correction",
                "resource_id": "form_cbse_name_correction",
                "title": "CBSE Proforma for Correction in Candidate / Parents' Name or Date of Birth",
                "issuing_authority": "Central Board of Secondary Education (CBSE)",
                "document_category": "class_10",
                "document_type": "application_form",
                "description": "Standard board proforma for seeking correction in Secondary (Class 10) or Senior Secondary (Class 12) certificates, forwarded by School Head.",
                "purpose": "Authoritative educational board correction form for aligning school grade sheets with foundational admission registers.",
                "intended_cohort": "MINOR_STUDENT",
                "applicable_categories": ["class_10", "class_12"],
                "publication_date": "2023",
                "effective_date": "2023-01-01",
                "verification_status": "verified",
                "provenance": "SYNTHETIC_DEVELOPMENT_SAMPLE",
                "provenance_notes": "Application-generated development template. Download official proforma from cbse.gov.in or obtain from school.",
                "is_official_government_form": False,
                "is_synthetic_sample": True,
                "is_historical": False,
                "has_source_conflict": False,
                "human_review_required": False,
                "file_format": "pdf",
                "file_size_bytes": 12840,
                "sha256_hash": "b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef01",
                "storage_path": "backend/data/official_forms/form_cbse_name_correction.pdf",
                "download_available": True,
                "original_source_url": "https://www.cbse.gov.in",
                "key_information_required": [
                    "Roll Number, School Code, and Year of Passing",
                    "Certified extract of School Admission / Scholar Register",
                    "Principal recommendation and school seal",
                ],
                "referenced_laws": ["CBSE Examination Byelaws (Rule 69.1)"],
                "related_procedures": ["class_10_name_correction", "class_12_name_correction"],
                "limitations_and_warnings": [
                    "Corrections must be submitted within board limitation timelines or accompanied by Gazette publication.",
                ],
                "disclaimer": "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM",
            },
            {
                "id": "form_epf_joint_declaration",
                "resource_id": "form_epf_joint_declaration",
                "title": "EPFO Joint Declaration Form (Member & Employer Demographic Update)",
                "issuing_authority": "Employees' Provident Fund Organisation (EPFO)",
                "document_category": "epf",
                "document_type": "application_form",
                "description": "Prescribed statutory dual-attestation Joint Declaration for correcting employee name, father's name, date of birth, date of joining in UAN master records.",
                "purpose": "Official employer-employee joint submission for resolving provident fund member profile discrepancies.",
                "intended_cohort": "GENERAL_CITIZEN",
                "applicable_categories": ["epf"],
                "publication_date": "2023",
                "effective_date": "2023-08-22",
                "verification_status": "verified",
                "provenance": "SYNTHETIC_DEVELOPMENT_SAMPLE",
                "provenance_notes": "Application-generated development template with official EPFO Joint Declaration structure. Download official PDF from epfindia.gov.in.",
                "is_official_government_form": False,
                "is_synthetic_sample": True,
                "is_historical": False,
                "has_source_conflict": False,
                "human_review_required": False,
                "file_format": "pdf",
                "file_size_bytes": 15600,
                "sha256_hash": "c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef012",
                "storage_path": "backend/data/official_forms/form_epf_joint_declaration.pdf",
                "download_available": True,
                "original_source_url": "https://www.epfindia.gov.in",
                "key_information_required": [
                    "Universal Account Number (UAN) and Member ID",
                    "Establishment Name, Code, and Employer Seal",
                    "Correct vs Incorrect values for Name, DOB, DOJ",
                    "Self-attested copies of Aadhaar and PAN",
                ],
                "referenced_laws": ["EPFO Circular WS/2023/102 (Standard Operating Procedure for Joint Declaration)"],
                "related_procedures": ["epf_joint_declaration"],
                "limitations_and_warnings": [
                    "Must be countersigned by authorized signatory with establishment seal.",
                    "Date of birth differences exceeding 3 years require statutory proof (Birth Certificate or Passport).",
                ],
                "disclaimer": "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM",
            },
            {
                "id": "form_passport_annexure_e",
                "resource_id": "form_passport_annexure_e",
                "title": "Annexure 'E' — Deed Poll / Sworn Affidavit for Change in Name",
                "issuing_authority": "Ministry of External Affairs (CPV Division)",
                "document_category": "passport",
                "document_type": "alternative_evidence",
                "description": "Standard sworn affidavit executed by applicant affirming legal identity change for passport re-issue.",
                "purpose": "Affidavit proforma required for personal name change under Indian Passport Rules.",
                "intended_cohort": "GENERAL_CITIZEN",
                "applicable_categories": ["passport"],
                "publication_date": "2020",
                "effective_date": "2020-01-01",
                "verification_status": "verified",
                "provenance": "SYNTHETIC_DEVELOPMENT_SAMPLE",
                "provenance_notes": "Application-generated development template. Execute on non-judicial stamp paper.",
                "is_official_government_form": False,
                "is_synthetic_sample": True,
                "is_historical": False,
                "has_source_conflict": False,
                "human_review_required": False,
                "file_format": "pdf",
                "file_size_bytes": 11200,
                "sha256_hash": "d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0123",
                "storage_path": "backend/data/official_forms/form_passport_annexure_e.pdf",
                "download_available": True,
                "original_source_url": "https://www.passportindia.gov.in",
                "key_information_required": [
                    "Applicant old legal name and new legal name",
                    "Father's / Spouse's name and permanent address",
                    "Execution before Judicial Magistrate or Notary Public",
                ],
                "referenced_laws": ["Passports Rules, 1980 (Annexure 'E')"],
                "related_procedures": ["passport_reissue_correction"],
                "limitations_and_warnings": ["Must be attested by an authorized Notary or Magistrate."],
                "disclaimer": "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM",
            },
            {
                "id": "form_gazette_name_change",
                "resource_id": "form_gazette_name_change",
                "title": "Proforma for Change of Name Advertisement in The Gazette of India (Part IV)",
                "issuing_authority": "Department of Publication, Ministry of Housing and Urban Affairs",
                "document_category": "cross_category",
                "document_type": "alternative_evidence",
                "description": "Prescribed proforma application and deed poll for publishing public legal change of name in the official Gazette of India.",
                "purpose": "Statutory instrument establishing nationwide public notice of legal identity change across all government departments.",
                "intended_cohort": "GENERAL_CITIZEN",
                "applicable_categories": ["aadhaar", "pan", "passport", "class_10", "class_12", "epf"],
                "publication_date": "2024",
                "effective_date": "2024-01-01",
                "verification_status": "verified",
                "provenance": "SYNTHETIC_DEVELOPMENT_SAMPLE",
                "provenance_notes": "Application-generated development template. Submit to Controller of Publications, Civil Lines, Delhi.",
                "is_official_government_form": False,
                "is_synthetic_sample": True,
                "is_historical": False,
                "has_source_conflict": False,
                "human_review_required": False,
                "file_format": "pdf",
                "file_size_bytes": 13900,
                "sha256_hash": "e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef01234",
                "storage_path": "backend/data/official_forms/form_gazette_name_change.pdf",
                "download_available": True,
                "original_source_url": "https://deptpub.gov.in",
                "key_information_required": [
                    "Original Newspaper clippings (Hindi / English and Vernacular)",
                    "Prescribed Proforma signed by applicant and two witnesses",
                    "Affidavit attested by 1st Class Magistrate / Notary",
                    "Government identity proof copy (Aadhaar / Voter ID / Passport)",
                ],
                "referenced_laws": ["Department of Publication Guidelines for Gazette of India (Part IV)"],
                "related_procedures": ["aadhaar_name_update_major_gazette", "pan_name_correction_csf"],
                "limitations_and_warnings": [
                    "Processing time typically takes 4-6 weeks through Department of Publication.",
                ],
                "disclaimer": "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM",
            },
        ]

        catalog.extend(additional_forms)
        cls._cached_catalog = catalog
        logger.info("Successfully constructed citizen document repository catalog with %d resources", len(catalog))
        return catalog

    @classmethod
    def get_catalog(cls) -> List[Dict[str, Any]]:
        if cls._cached_catalog is None:
            return cls._build_catalog()
        return cls._cached_catalog

    @classmethod
    def list_resources(
        cls,
        category: Optional[str] = None,
        document_type: Optional[str] = None,
        provenance: Optional[str] = None,
        verification_status: Optional[str] = None,
        search_query: Optional[str] = None,
        include_historical: bool = True,
        sort_by: str = "relevance",
        page: int = 1,
        page_size: int = 12,
    ) -> RepositoryResourceListResponse:
        catalog = cls.get_catalog()
        filtered = list(catalog)

        # 1. Category Filter
        if category and category.lower() != "all":
            clean_cat = category.strip().lower()
            norm_cat = CATEGORY_NORMALIZATION.get(clean_cat, clean_cat)
            filtered = [
                r for r in filtered
                if r["document_category"] == norm_cat or norm_cat in r.get("applicable_categories", [])
            ]

        # 2. Document Type Filter
        if document_type and document_type.lower() != "all":
            clean_type = document_type.strip().lower()
            filtered = [r for r in filtered if r["document_type"] == clean_type]

        # 3. Provenance Filter
        if provenance and provenance.lower() != "all":
            clean_prov = provenance.strip().upper()
            filtered = [r for r in filtered if r["provenance"] == clean_prov]

        # 4. Verification Status Filter
        if verification_status and verification_status.lower() != "all":
            clean_status = verification_status.strip().lower()
            filtered = [r for r in filtered if r["verification_status"] == clean_status]

        # 5. Search Query Filter
        if search_query and search_query.strip():
            q_terms = [t.lower() for t in search_query.strip().split() if len(t) > 1]
            scored_items = []
            for r in filtered:
                score = 0
                title_low = r["title"].lower()
                desc_low = r["description"].lower()
                auth_low = r["issuing_authority"].lower()
                doc_id = r["resource_id"].lower()

                for term in q_terms:
                    if term in doc_id:
                        score += 10
                    if term in title_low:
                        score += 5
                    if term in auth_low:
                        score += 3
                    if term in desc_low:
                        score += 2

                if score > 0:
                    scored_items.append((score, r))

            scored_items.sort(key=lambda x: x[0], reverse=True)
            filtered = [item[1] for item in scored_items]

        # 6. Sorting
        if sort_by == "date_desc":
            filtered.sort(key=lambda x: x.get("publication_date", "") or "", reverse=True)
        elif sort_by == "title_asc":
            filtered.sort(key=lambda x: x.get("title", "").lower())

        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = filtered[start_idx:end_idx]

        response_items = [
            RepositoryResourceItem(
                id=item["id"],
                resource_id=item["resource_id"],
                title=item["title"],
                issuing_authority=item["issuing_authority"],
                document_category=item["document_category"],
                document_type=item["document_type"],
                description=item["description"],
                purpose=item["purpose"],
                applicable_categories=item["applicable_categories"],
                publication_date=item.get("publication_date"),
                effective_date=item.get("effective_date"),
                verification_status=item["verification_status"],
                provenance=item["provenance"],
                provenance_notes=item.get("provenance_notes"),
                is_official_government_form=item.get("is_official_government_form", False),
                is_synthetic_sample=item.get("is_synthetic_sample", False),
                is_historical=item.get("is_historical", False),
                has_source_conflict=item.get("has_source_conflict", False),
                human_review_required=item.get("human_review_required", False),
                file_format=item.get("file_format", "pdf"),
                file_size_bytes=item.get("file_size_bytes", 0),
                sha256_hash=item.get("sha256_hash"),
                download_available=item.get("download_available", True),
                download_url=f"/api/v1/repository/resources/{item['resource_id']}/download",
                preview_url=f"/api/v1/repository/resources/{item['resource_id']}/preview",
                related_procedures=item.get("related_procedures", []),
                disclaimer=item.get("disclaimer"),
            )
            for item in page_items
        ]

        total_pages = max(1, (total + page_size - 1) // page_size)
        return RepositoryResourceListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            category_filter=category,
            resources=response_items,
        )

    @classmethod
    def get_resource_detail(cls, resource_id: str) -> Optional[RepositoryResourceDetail]:
        catalog = cls.get_catalog()
        clean_id = (resource_id or "").strip().lower()

        found = None
        for item in catalog:
            if item["id"].lower() == clean_id or item["resource_id"].lower() == clean_id:
                found = item
                break

        if not found:
            return None

        # Assemble Citations
        citations = [
            SourceCitation(
                source_id=found["resource_id"],
                title=found["title"],
                authority=found["issuing_authority"],
                url=found.get("original_source_url", "https://uidai.gov.in"),
                section="Authoritative Statutory Publication",
                verification_status=found["verification_status"],
                last_verified_at="2026-11-09T00:00:00Z",
            )
        ]

        # Assemble Checklists
        checklist_items: List[ChecklistItem] = []
        for proc_id in found.get("related_procedures", []):
            chk = ChecklistService.get_checklist_for_procedure(proc_id)
            if chk:
                checklist_items.extend(chk.items)

        # Deduplicate checklist items by requirement_id
        seen_reqs = set()
        unique_checklist = []
        for itm in checklist_items:
            if itm.requirement_id not in seen_reqs:
                seen_reqs.add(itm.requirement_id)
                unique_checklist.append(itm)

        return RepositoryResourceDetail(
            id=found["id"],
            resource_id=found["resource_id"],
            title=found["title"],
            issuing_authority=found["issuing_authority"],
            document_category=found["document_category"],
            document_type=found["document_type"],
            description=found["description"],
            purpose=found["purpose"],
            intended_cohort=found.get("intended_cohort", "GENERAL_CITIZEN"),
            applicable_categories=found.get("applicable_categories", [found["document_category"]]),
            publication_date=found.get("publication_date"),
            effective_date=found.get("effective_date"),
            verification_status=found["verification_status"],
            provenance=found["provenance"],
            provenance_notes=found.get("provenance_notes"),
            is_official_government_form=found.get("is_official_government_form", False),
            is_synthetic_sample=found.get("is_synthetic_sample", False),
            is_historical=found.get("is_historical", False),
            has_source_conflict=found.get("has_source_conflict", False),
            human_review_required=found.get("human_review_required", False),
            file_format=found.get("file_format", "pdf"),
            file_size_bytes=found.get("file_size_bytes", 0),
            sha256_hash=found.get("sha256_hash"),
            download_available=found.get("download_available", True),
            download_url=f"/api/v1/repository/resources/{found['resource_id']}/download",
            preview_url=f"/api/v1/repository/resources/{found['resource_id']}/preview",
            original_source_url=found.get("original_source_url"),
            key_information_required=found.get("key_information_required", []),
            referenced_laws=found.get("referenced_laws", []),
            related_procedures=found.get("related_procedures", []),
            limitations_and_warnings=found.get("limitations_and_warnings", []),
            statutory_citations=citations,
            supporting_document_checklist=unique_checklist,
            disclaimer=found.get("disclaimer"),
        )

    @classmethod
    def get_categories_summary(cls) -> Dict[str, Any]:
        catalog = cls.get_catalog()
        summary: Dict[str, Any] = {
            "all": len(catalog),
            "categories": {},
        }

        for cat_id, meta in CATEGORY_METADATA.items():
            count = sum(1 for r in catalog if r["document_category"] == cat_id or cat_id in r.get("applicable_categories", []))
            summary["categories"][cat_id] = {
                "id": cat_id,
                "name": meta["name"],
                "authority": meta["authority"],
                "description": meta["description"],
                "count": count,
            }

        return summary

    @classmethod
    def resolve_file_path(cls, resource_id: str) -> Optional[Tuple[str, str, str]]:
        """
        Safely resolves physical file on disk for a given resource.
        Guarantees path containment and prevents directory traversal attacks.
        Returns: (absolute_file_path, filename, mime_type)
        """
        root = cls._get_project_root()
        clean_id = (resource_id or "").strip()

        # Reject null bytes and directory traversal tokens
        if "\x00" in clean_id or ".." in clean_id or "/" in clean_id or "\\" in clean_id:
            logger.warning("Directory traversal attempt in resource id: %s", clean_id)
            return None

        detail = cls.get_resource_detail(clean_id)
        if not detail:
            return None

        # Look in catalog for relative storage path
        catalog = cls.get_catalog()
        found_item = next((i for i in catalog if i["id"].lower() == clean_id.lower()), None)
        if not found_item or not found_item.get("storage_path"):
            return None

        rel_path = found_item["storage_path"]
        abs_target = os.path.abspath(os.path.join(root, rel_path))

        # Containment verification: Must reside within root project
        if not abs_target.startswith(root):
            logger.warning("Resolved path escapes project root: %s", abs_target)
            return None

        if not os.path.isfile(abs_target):
            # Check backend/data/official_forms fallback
            fallback = get_official_form_path(clean_id)
            if fallback and os.path.isfile(fallback):
                abs_target = fallback
            else:
                logger.warning("File not found on disk: %s", abs_target)
                return None

        filename = os.path.basename(abs_target)
        return abs_target, filename, "application/pdf"
