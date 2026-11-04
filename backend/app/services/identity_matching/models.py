"""
CONVELINA - Canonical Document Identity Profile & Comparison Result Models
Represents structured identity data extracted from statutory documents and multi-field comparison outputs.
Guarantees strict separation between raw OCR values, normalized representations, and confidence metrics.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class DocumentIdentityProfile(BaseModel):
    """
    Canonical representation of a citizen's extracted document identity.
    Preserves raw OCR extractions untouched alongside derived normalized representations.
    """
    document_id: Optional[str] = None
    document_type: str = "generic"

    # Raw extracted values (Never overwritten)
    full_name_raw: Optional[str] = None
    father_name_raw: Optional[str] = None
    mother_name_raw: Optional[str] = None
    date_of_birth_raw: Optional[str] = None
    gender_raw: Optional[str] = None
    address_raw: Optional[str] = None
    raw_extracted_text: Optional[str] = None

    # Normalized derived values (For deterministic matching)
    full_name_normalized: Optional[str] = None
    name_tokens: List[str] = Field(default_factory=list)
    initials: List[str] = Field(default_factory=list)

    father_name_normalized: Optional[str] = None
    father_name_tokens: List[str] = Field(default_factory=list)
    father_initials: List[str] = Field(default_factory=list)

    mother_name_normalized: Optional[str] = None
    mother_name_tokens: List[str] = Field(default_factory=list)

    date_of_birth_normalized: Optional[str] = None  # YYYY-MM-DD or YYYY
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None

    gender_normalized: Optional[str] = None
    address_normalized: Optional[str] = None
    pincode: Optional[str] = None

    # Quality, Confidence, and Security Metadata
    field_confidence: Dict[str, float] = Field(default_factory=dict)
    overall_ocr_confidence: float = 1.0  # 0.0 to 1.0 scale
    language_detected: Optional[str] = "en"
    is_non_latin: bool = False
    extraction_status: str = "completed"
    source_document_reference: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_extracted_fields(
        cls,
        document_id: Optional[str],
        document_type: str,
        extracted_fields: Dict[str, Any],
        overall_ocr_confidence: float = 1.0,
        raw_text: Optional[str] = None,
        source_ref: Optional[str] = None,
    ) -> "DocumentIdentityProfile":
        """
        Constructs a canonical DocumentIdentityProfile from OCR parser output,
        deriving normalized fields deterministically without modifying raw values.
        """
        from app.services.identity_matching.normalization import (
            normalize_person_name,
            normalize_date_of_birth,
            normalize_gender_value,
            normalize_address_string,
            contains_unsupported_non_latin,
        )

        name_raw = extracted_fields.get("full_name") or extracted_fields.get("name")
        father_raw = extracted_fields.get("father_name")
        mother_raw = extracted_fields.get("mother_name")
        dob_raw = extracted_fields.get("date_of_birth") or extracted_fields.get("year_of_birth")
        gender_raw = extracted_fields.get("gender")
        address_raw = extracted_fields.get("address")

        # Name normalization
        norm_name, name_tokens, initials = normalize_person_name(name_raw)
        norm_father, father_tokens, father_inits = normalize_person_name(father_raw)
        norm_mother, mother_tokens, _ = normalize_person_name(mother_raw)

        # Date normalization
        std_dob, y, m, d = normalize_date_of_birth(dob_raw)

        # Gender normalization
        norm_gender = normalize_gender_value(gender_raw)

        # Address normalization
        norm_addr, pin = normalize_address_string(address_raw)

        # Non-Latin script detection
        has_non_latin = contains_unsupported_non_latin(name_raw or "") or contains_unsupported_non_latin(raw_text or "")

        return cls(
            document_id=str(document_id) if document_id else None,
            document_type=document_type,
            full_name_raw=name_raw,
            full_name_normalized=norm_name,
            name_tokens=name_tokens,
            initials=initials,
            father_name_raw=father_raw,
            father_name_normalized=norm_father,
            father_name_tokens=father_tokens,
            father_initials=father_inits,
            mother_name_raw=mother_raw,
            mother_name_normalized=norm_mother,
            mother_name_tokens=mother_tokens,
            date_of_birth_raw=str(dob_raw) if dob_raw else None,
            date_of_birth_normalized=std_dob,
            birth_year=y,
            birth_month=m,
            birth_day=d,
            gender_raw=gender_raw,
            gender_normalized=norm_gender,
            address_raw=address_raw,
            address_normalized=norm_addr,
            pincode=pin,
            raw_extracted_text=raw_text,
            field_confidence=extracted_fields.get("field_confidence", {}),
            overall_ocr_confidence=overall_ocr_confidence,
            is_non_latin=has_non_latin,
            source_document_reference=source_ref,
        )


class FieldMatchResult(BaseModel):
    """Evaluation result for a single demographic attribute across two documents."""
    field_name: str
    value_a_raw: Optional[str] = None
    value_b_raw: Optional[str] = None
    value_a_normalized: Optional[str] = None
    value_b_normalized: Optional[str] = None
    classification: str
    similarity_score: float = 0.0
    confidence_score: float = 1.0
    is_conflict: bool = False
    severity: str = "low"
    requires_manual_review: bool = False
    explanation: str = ""
    possible_causes: List[str] = Field(default_factory=list)
    recommended_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "value_a_raw": self.value_a_raw,
            "value_b_raw": self.value_b_raw,
            "value_a_normalized": self.value_a_normalized,
            "value_b_normalized": self.value_b_normalized,
            "classification": self.classification,
            "similarity_score": round(self.similarity_score, 2),
            "confidence_score": round(self.confidence_score, 2),
            "is_conflict": self.is_conflict,
            "severity": self.severity,
            "requires_manual_review": self.requires_manual_review,
            "explanation": self.explanation,
            "possible_causes": self.possible_causes,
            "recommended_action": self.recommended_action,
        }


class IdentityComparisonResult(BaseModel):
    """Holistic cross-document reconciliation result combining multi-field evidence."""
    overall_classification: str
    confidence_score: float = 1.0
    requires_manual_review: bool = False
    matched_fields: List[str] = Field(default_factory=list)
    conflicting_fields: List[str] = Field(default_factory=list)
    ambiguous_fields: List[str] = Field(default_factory=list)
    field_results: Dict[str, FieldMatchResult] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    explanation: str = ""
    warnings: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_classification": self.overall_classification,
            "confidence_score": round(self.confidence_score, 2),
            "requires_manual_review": self.requires_manual_review,
            "matched_fields": self.matched_fields,
            "conflicting_fields": self.conflicting_fields,
            "ambiguous_fields": self.ambiguous_fields,
            "field_results": {k: v.to_dict() for k, v in self.field_results.items()},
            "evidence": self.evidence,
            "explanation": self.explanation,
            "warnings": self.warnings,
        }

