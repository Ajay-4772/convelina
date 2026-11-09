"""
CONVELINA — Field-Level Extraction Schema & Processor (Phase P3 & P3E.1)
Implements category-specific field extraction with field-level confidence,
page numbers, bounding coordinates, validation status, and review_required triggers.
Never fabricates missing values (returns None).
"""

import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from app.ocr.parsers.factory import get_document_parser
from app.services.identity_matching.normalization import (
    normalize_person_name,
    normalize_date_of_birth,
    normalize_gender_value,
    normalize_address_string,
)


class FieldExtractionResult(BaseModel):
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence: float = 1.0  # Combined calibrated confidence: 0.0 to 1.0 scale
    ocr_engine_confidence: float = 1.0  # Evidence from OCR engine word/page confidence
    parser_confidence: float = 1.0      # Pattern anchor precision (e.g. 1.0 for exact label, 0.75 for heuristic)
    format_validated: bool = True       # Syntactic validation against statutory regex/checksum
    user_confirmed: bool = False        # Explicit citizen verification status
    page_number: int = 1
    bounding_box: Optional[Dict[str, float]] = None
    validation_status: str = "valid"    # valid, invalid_format, unverified, missing
    review_required: bool = False
    source_document_id: Optional[str] = None


class CategoryExtractionResult(BaseModel):
    document_type: str
    overall_confidence: float = 1.0
    field_extractions: Dict[str, FieldExtractionResult] = Field(default_factory=dict)
    fields_flat: Dict[str, Any] = Field(default_factory=dict)
    masked_id: Optional[str] = None
    requires_manual_review: bool = False


# Expected fields per document category
CATEGORY_SCHEMAS = {
    "aadhaar": [
        "full_name",
        "date_of_birth",
        "gender",
        "aadhaar_number",
        "address",
        "pincode",
    ],
    "pan": [
        "full_name",
        "father_name",
        "date_of_birth",
        "pan_number",
    ],
    "passport": [
        "full_name",
        "passport_number",
        "date_of_birth",
        "place_of_birth",
        "date_of_issue",
        "expiry_date",
        "father_name",
        "mother_name",
        "address",
    ],
    "education_10th": [
        "full_name",
        "father_name",
        "mother_name",
        "date_of_birth",
        "roll_number",
        "registration_number",
        "board",
        "passing_year",
    ],
    "education_12th": [
        "full_name",
        "father_name",
        "mother_name",
        "date_of_birth",
        "roll_number",
        "registration_number",
        "board",
        "passing_year",
    ],
    "epf": [
        "full_name",
        "uan",
        "member_id",
        "employer_name",
        "establishment_id",
        "date_of_joining",
        "date_of_exit",
    ]
}

OPTIONAL_FIELDS = {
    "epf": ["date_of_exit", "establishment_id"],
    "passport": ["place_of_birth", "father_name", "mother_name", "address", "date_of_issue", "expiry_date"],
    "aadhaar": ["address", "pincode", "year_of_birth"],
    "education_10th": ["registration_number", "mother_name"],
    "education_12th": ["registration_number", "mother_name", "date_of_birth"],
}


class FieldExtractor:
    """
    Standardized Field Extractor implementing 14-step OCR processing rules.
    Derives field-level confidence, formats, normalization, and review triggers.
    """

    @classmethod
    def extract_category_fields(
        cls,
        document_type: str,
        raw_text: str,
        overall_confidence: float = 1.0,
        source_document_id: Optional[str] = None,
        page_number: int = 1,
    ) -> CategoryExtractionResult:
        doc_type = document_type.lower()
        parser = get_document_parser(doc_type)
        parsed = parser.parse(raw_text)

        parsed_fields = parsed.get("fields", {})
        masked_id = parsed.get("masked_id")

        schema_fields = CATEGORY_SCHEMAS.get(doc_type, list(parsed_fields.keys()))
        extractions: Dict[str, FieldExtractionResult] = {}
        flat_fields: Dict[str, Any] = {}
        any_review_required = False

        for f_name in schema_fields:
            raw_val = parsed_fields.get(f_name)
            # Check aliases
            if raw_val is None:
                if f_name == "full_name":
                    raw_val = (
                        parsed_fields.get("candidate_name")
                        or parsed_fields.get("student_name")
                        or parsed_fields.get("member_name")
                        or parsed_fields.get("name")
                    )
                elif f_name == "passing_year":
                    raw_val = parsed_fields.get("examination_year") or parsed_fields.get("year")
                elif f_name == "employer_name":
                    raw_val = parsed_fields.get("establishment_name") or parsed_fields.get("establishment")
                elif f_name == "aadhaar_number":
                    raw_val = parsed_fields.get("aadhaar_last_4")

            norm_val = None
            ocr_conf = float(overall_confidence)
            parser_conf = 0.95  # Standard anchored extraction confidence
            format_validated = True
            user_confirmed = False
            val_status = "valid"
            rev_req = False
            is_optional = f_name in OPTIONAL_FIELDS.get(doc_type, [])

            if raw_val is None or str(raw_val).strip() == "" or str(raw_val).strip().upper() in ("NONE", "NULL", "NA", "N/A"):
                raw_val = None
                if is_optional:
                    val_status = "optional_omitted"
                    format_validated = True
                    f_conf = 0.0
                    parser_conf = 0.0
                    rev_req = False
                else:
                    val_status = "missing"
                    format_validated = False
                    f_conf = 0.0
                    parser_conf = 0.0
                    rev_req = True
                    any_review_required = True
            else:
                raw_str = str(raw_val).strip()
                raw_val = raw_str

                # Field-specific normalization & format validation
                if f_name in ("full_name", "father_name", "mother_name", "student_name"):
                    norm_val, _, _ = normalize_person_name(raw_str)
                    if len(raw_str) < 3 or re.search(r"\d", raw_str):
                        val_status = "invalid_format"
                        format_validated = False
                elif f_name in ("date_of_birth", "date_of_issue", "expiry_date", "date_of_joining", "date_of_exit"):
                    norm_val, _, _, _ = normalize_date_of_birth(raw_str)
                    if not norm_val:
                        val_status = "invalid_format"
                        format_validated = False
                elif f_name == "gender":
                    norm_val = normalize_gender_value(raw_str)
                    if not norm_val:
                        val_status = "invalid_format"
                        format_validated = False
                elif f_name == "address":
                    norm_val, _ = normalize_address_string(raw_str)
                elif f_name == "pincode":
                    p_match = re.search(r"\b([1-9][0-9]{5})\b", raw_str)
                    if p_match:
                        norm_val = p_match.group(1)
                    else:
                        val_status = "invalid_format"
                        format_validated = False
                elif f_name == "pan_number":
                    if re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", raw_str.upper()):
                        norm_val = raw_str.upper()
                    else:
                        val_status = "invalid_format"
                        format_validated = False
                elif f_name == "uan":
                    if re.match(r"^\d{12}$", raw_str):
                        norm_val = raw_str
                    else:
                        val_status = "invalid_format"
                        format_validated = False
                elif f_name == "board":
                    raw_upper = raw_str.upper()
                    if "CENTRAL BOARD" in raw_upper or raw_upper == "CBSE":
                        norm_val = "CBSE"
                    elif "COUNCIL FOR THE INDIAN SCHOOL" in raw_upper or raw_upper in ("ICSE", "CISCE"):
                        norm_val = "ICSE"
                    else:
                        norm_val = raw_str
                else:
                    norm_val = raw_str

                # Calibrated confidence calculation:
                # Decoupled: format validity cannot inflate low OCR confidence;
                # invalid format strictly caps confidence to <= 0.45.
                base_combined = ocr_conf * parser_conf
                if format_validated:
                    f_conf = round(min(0.95, base_combined), 3)
                else:
                    f_conf = round(min(0.45, base_combined * 0.5), 3)

                # Calibrated review threshold (0.75):
                # Review is required if confidence is below threshold, format failed,
                # or regional script is present requiring citizen confirmation.
                has_regional = any('\u0B80' <= c <= '\u0BFF' for c in raw_str)
                if f_conf < 0.75 or val_status != "valid" or has_regional:
                    rev_req = True
                    any_review_required = True

            result_item = FieldExtractionResult(
                field_name=f_name,
                raw_value=raw_val,
                normalized_value=norm_val,
                confidence=round(f_conf, 3),
                ocr_engine_confidence=round(ocr_conf, 3),
                parser_confidence=round(parser_conf, 3),
                format_validated=format_validated,
                user_confirmed=user_confirmed,
                page_number=page_number,
                bounding_box=None,
                validation_status=val_status,
                review_required=rev_req,
                source_document_id=source_document_id,
            )
            extractions[f_name] = result_item
            if raw_val is not None:
                flat_fields[f_name] = norm_val if norm_val is not None else raw_val

        # Also carry over any additional parsed fields not in the standard schema
        for extra_k, extra_v in parsed_fields.items():
            if extra_k not in extractions and extra_v is not None:
                flat_fields[extra_k] = extra_v
                has_regional = any('\u0B80' <= c <= '\u0BFF' for c in str(extra_v))
                extra_conf = round(min(0.92, overall_confidence * 0.95), 3)
                extra_rev = extra_conf < 0.75 or has_regional
                if extra_rev:
                    any_review_required = True
                extractions[extra_k] = FieldExtractionResult(
                    field_name=extra_k,
                    raw_value=str(extra_v),
                    normalized_value=str(extra_v),
                    confidence=extra_conf,
                    ocr_engine_confidence=round(overall_confidence, 3),
                    parser_confidence=0.95,
                    format_validated=True,
                    user_confirmed=False,
                    page_number=page_number,
                    bounding_box=None,
                    validation_status="valid",
                    review_required=extra_rev,
                    source_document_id=source_document_id,
                )

        if overall_confidence < 0.75:
            any_review_required = True

        return CategoryExtractionResult(
            document_type=doc_type,
            overall_confidence=round(overall_confidence, 3),
            field_extractions=extractions,
            fields_flat=flat_fields,
            masked_id=masked_id,
            requires_manual_review=any_review_required,
        )
