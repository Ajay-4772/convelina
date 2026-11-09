from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# 0. Statutory Disclaimers & Taxonomy Constants
# ---------------------------------------------------------------------------

MANDATORY_DRAFT_DISCLAIMER = (
    "AI-GENERATED ADMINISTRATIVE DRAFT — REVIEW ALL DETAILS AND VERIFY THE APPLICABLE OFFICIAL PROCEDURE BEFORE SUBMISSION."
)

class DraftTypeEnum(str, Enum):
    IDENTITY_CORRECTION_REQUEST = "identity_correction_request"
    NAME_CHANGE_REPRESENTATION = "name_change_representation"
    DOB_RECTIFICATION_REQUEST = "dob_rectification_request"
    ADDRESS_UPDATE_APPLICATION = "address_update_application"
    PARENT_NAME_RECTIFICATION = "parent_name_rectification"
    EDUCATIONAL_CERTIFICATE_REPRESENTATION = "educational_certificate_representation"
    EPF_MEMBER_CORRECTION_REQUEST = "epf_member_correction_request"
    GENERAL_ADMINISTRATIVE_REPRESENTATION = "general_administrative_representation"
    SUPPORTING_DOCUMENT_COVER_LETTER = "supporting_document_cover_letter"
    STATUTORY_PETITION_REPRESENTATION = "statutory_petition_representation"

    # Backwards compatibility legacy aliases
    CORRECTION_REQUEST_LETTER = "correction_request_letter"
    SUPPORTING_DOCUMENT_CHECKLIST = "supporting_document_checklist"
    DECLARATION_DRAFT = "declaration_draft"
    GENERAL_CORRECTION_APPLICATION = "general_correction_application"


class DocumentCategoryEnum(str, Enum):
    AADHAAR = "aadhaar"
    PAN = "pan"
    PASSPORT = "passport"
    EDUCATION_10TH = "education_10th"
    EDUCATION_12TH = "education_12th"
    EPF = "epf"

    # Compatibility aliases
    EDUCATION = "education"
    EPFO = "epfo"
    CERTIFICATE = "certificate"


class DraftStatusEnum(str, Enum):
    AI_GENERATED = "ai_generated"
    CITIZEN_EDITED = "citizen_edited"
    CITIZEN_CONFIRMED = "citizen_confirmed"

    # Compatibility aliases
    GENERATED = "generated"
    USER_EDITED = "user_edited"
    APPROVED = "approved"
    DRAFT = "draft"


# ---------------------------------------------------------------------------
# 1. Deterministic Compatibility Matrix
# ---------------------------------------------------------------------------

DRAFT_COMPATIBILITY_MATRIX: Dict[str, List[str]] = {
    "aadhaar": [
        DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value,
        DraftTypeEnum.NAME_CHANGE_REPRESENTATION.value,
        DraftTypeEnum.DOB_RECTIFICATION_REQUEST.value,
        DraftTypeEnum.ADDRESS_UPDATE_APPLICATION.value,
        DraftTypeEnum.GENERAL_ADMINISTRATIVE_REPRESENTATION.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_COVER_LETTER.value,
        DraftTypeEnum.STATUTORY_PETITION_REPRESENTATION.value,
        # Legacy
        DraftTypeEnum.CORRECTION_REQUEST_LETTER.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_CHECKLIST.value,
        DraftTypeEnum.DECLARATION_DRAFT.value,
        DraftTypeEnum.GENERAL_CORRECTION_APPLICATION.value,
    ],
    "pan": [
        DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value,
        DraftTypeEnum.NAME_CHANGE_REPRESENTATION.value,
        DraftTypeEnum.DOB_RECTIFICATION_REQUEST.value,
        DraftTypeEnum.PARENT_NAME_RECTIFICATION.value,
        DraftTypeEnum.GENERAL_ADMINISTRATIVE_REPRESENTATION.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_COVER_LETTER.value,
        DraftTypeEnum.STATUTORY_PETITION_REPRESENTATION.value,
        # Legacy
        DraftTypeEnum.CORRECTION_REQUEST_LETTER.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_CHECKLIST.value,
        DraftTypeEnum.DECLARATION_DRAFT.value,
        DraftTypeEnum.GENERAL_CORRECTION_APPLICATION.value,
    ],
    "passport": [
        DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value,
        DraftTypeEnum.NAME_CHANGE_REPRESENTATION.value,
        DraftTypeEnum.DOB_RECTIFICATION_REQUEST.value,
        DraftTypeEnum.PARENT_NAME_RECTIFICATION.value,
        DraftTypeEnum.ADDRESS_UPDATE_APPLICATION.value,
        DraftTypeEnum.GENERAL_ADMINISTRATIVE_REPRESENTATION.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_COVER_LETTER.value,
        DraftTypeEnum.STATUTORY_PETITION_REPRESENTATION.value,
        # Legacy
        DraftTypeEnum.CORRECTION_REQUEST_LETTER.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_CHECKLIST.value,
        DraftTypeEnum.DECLARATION_DRAFT.value,
        DraftTypeEnum.GENERAL_CORRECTION_APPLICATION.value,
    ],
    "education_10th": [
        DraftTypeEnum.EDUCATIONAL_CERTIFICATE_REPRESENTATION.value,
        DraftTypeEnum.NAME_CHANGE_REPRESENTATION.value,
        DraftTypeEnum.DOB_RECTIFICATION_REQUEST.value,
        DraftTypeEnum.PARENT_NAME_RECTIFICATION.value,
        DraftTypeEnum.GENERAL_ADMINISTRATIVE_REPRESENTATION.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_COVER_LETTER.value,
        DraftTypeEnum.STATUTORY_PETITION_REPRESENTATION.value,
        # Legacy
        DraftTypeEnum.CORRECTION_REQUEST_LETTER.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_CHECKLIST.value,
        DraftTypeEnum.DECLARATION_DRAFT.value,
        DraftTypeEnum.GENERAL_CORRECTION_APPLICATION.value,
    ],
    "education_12th": [
        DraftTypeEnum.EDUCATIONAL_CERTIFICATE_REPRESENTATION.value,
        DraftTypeEnum.NAME_CHANGE_REPRESENTATION.value,
        DraftTypeEnum.DOB_RECTIFICATION_REQUEST.value,
        DraftTypeEnum.PARENT_NAME_RECTIFICATION.value,
        DraftTypeEnum.GENERAL_ADMINISTRATIVE_REPRESENTATION.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_COVER_LETTER.value,
        DraftTypeEnum.STATUTORY_PETITION_REPRESENTATION.value,
        # Legacy
        DraftTypeEnum.CORRECTION_REQUEST_LETTER.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_CHECKLIST.value,
        DraftTypeEnum.DECLARATION_DRAFT.value,
        DraftTypeEnum.GENERAL_CORRECTION_APPLICATION.value,
    ],
    "epf": [
        DraftTypeEnum.EPF_MEMBER_CORRECTION_REQUEST.value,
        DraftTypeEnum.NAME_CHANGE_REPRESENTATION.value,
        DraftTypeEnum.DOB_RECTIFICATION_REQUEST.value,
        DraftTypeEnum.PARENT_NAME_RECTIFICATION.value,
        DraftTypeEnum.GENERAL_ADMINISTRATIVE_REPRESENTATION.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_COVER_LETTER.value,
        DraftTypeEnum.STATUTORY_PETITION_REPRESENTATION.value,
        # Legacy
        DraftTypeEnum.CORRECTION_REQUEST_LETTER.value,
        DraftTypeEnum.SUPPORTING_DOCUMENT_CHECKLIST.value,
        DraftTypeEnum.DECLARATION_DRAFT.value,
        DraftTypeEnum.GENERAL_CORRECTION_APPLICATION.value,
    ],
}

# Alias mappings
DRAFT_COMPATIBILITY_MATRIX["education"] = DRAFT_COMPATIBILITY_MATRIX["education_10th"]
DRAFT_COMPATIBILITY_MATRIX["certificate"] = DRAFT_COMPATIBILITY_MATRIX["education_10th"]
DRAFT_COMPATIBILITY_MATRIX["epfo"] = DRAFT_COMPATIBILITY_MATRIX["epf"]


def is_draft_type_applicable(draft_type: str, category: str) -> bool:
    """Checks whether the requested draft type is valid for the target category."""
    norm_cat = (category or "").lower().strip()
    norm_type = (draft_type or "").lower().strip()
    allowed_types = DRAFT_COMPATIBILITY_MATRIX.get(norm_cat, [])
    return norm_type in allowed_types


# ---------------------------------------------------------------------------
# 2. Request and Response Models
# ---------------------------------------------------------------------------

class CorrectionDraftCreate(BaseModel):
    conflict_id: UUID
    document_type: str = Field(
        default="identity_correction_request",
        description="Type of administrative document (e.g. identity_correction_request, name_change_representation, etc.)"
    )
    document_category: str = Field(
        default="pan",
        description="Statutory category: aadhaar, pan, passport, education_10th, education_12th, epf"
    )
    confirmed_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Citizen-confirmed identity fields (e.g. {'applicant_name': 'RAJESH KUMAR SHARMA'})"
    )
    user_explanation: Optional[str] = Field(
        default=None,
        description="Citizen's plain-language context or reason for the requested correction"
    )
    requested_action: Optional[str] = Field(
        default=None,
        description="Citizen's explicit desired administrative rectification or relief"
    )
    language: Optional[str] = Field(
        default="en",
        description="Language for the draft: 'en' (English), 'ta' (Tamil), or 'hi' (Hindi)"
    )


class CorrectionDraftUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    confirmed_fields: Optional[Dict[str, Any]] = None
    recipient_authority: Optional[str] = None
    subject: Optional[str] = None
    user_explanation: Optional[str] = None
    requested_action: Optional[str] = None


class CorrectionDraftRegenerateRequest(BaseModel):
    confirmed_fields: Optional[Dict[str, Any]] = None
    user_explanation: Optional[str] = None
    requested_action: Optional[str] = None
    tone: Optional[str] = Field(
        default="formal",
        description="Drafting style: 'formal', 'concise', or 'petition'"
    )


class CorrectionDraftConfirmRequest(BaseModel):
    confirmation_statement: str = Field(
        ...,
        description="Explicit citizen acknowledgement that details have been reviewed and approved for export"
    )
    version_number: Optional[int] = Field(
        default=None,
        description="Specific draft version being confirmed"
    )
    expected_sha256_hash: Optional[str] = Field(
        default=None,
        description="Client-side SHA-256 hash of the content reviewed by the citizen to prevent race-condition confirmations"
    )


class CorrectionDraftTranslateRequest(BaseModel):
    target_language: str = Field(
        default="ta",
        description="Target language code: 'ta' (Tamil), 'en' (English), 'hi' (Hindi), or 'bilingual_en_ta'"
    )
    bilingual: bool = Field(
        default=False,
        description="If True, synthesizes both English and target language parallel representations"
    )


class CorrectionDraftResponse(BaseModel):
    id: UUID
    user_id: UUID
    conflict_id: Optional[UUID] = None
    document_type: str
    document_category: str
    status: str
    title: str
    content: str
    recipient_authority: Optional[str] = None
    subject: Optional[str] = None
    user_explanation: Optional[str] = None
    requested_action: Optional[str] = None
    confirmed_fields: Dict[str, Any] = Field(default_factory=dict)
    supporting_documents: List[Dict[str, Any]] = Field(default_factory=list)
    source_references: List[Dict[str, Any]] = Field(default_factory=list)
    disclaimer: str = MANDATORY_DRAFT_DISCLAIMER
    is_citizen_confirmed: bool = False
    citizen_confirmed_at: Optional[datetime] = None
    confirmed_version_number: Optional[int] = None
    sha256_hash: Optional[str] = None
    language: str = "en"
    version: int
    created_at: datetime
    updated_at: datetime
    validation_status: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CorrectionDraftListResponse(BaseModel):
    total: int
    items: List[CorrectionDraftResponse]


class CorrectionDraftVersionResponse(BaseModel):
    id: UUID
    draft_id: UUID
    user_id: UUID
    version_number: int
    content: str
    change_type: str
    recipient_authority: Optional[str] = None
    subject: Optional[str] = None
    confirmed_fields: Dict[str, Any] = Field(default_factory=dict)
    supporting_documents: List[Dict[str, Any]] = Field(default_factory=list)
    source_references: List[Dict[str, Any]] = Field(default_factory=list)
    is_citizen_confirmed: bool = False
    citizen_confirmed_at: Optional[datetime] = None
    sha256_hash: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentValidationResult(BaseModel):
    is_valid: bool
    unresolved_placeholders: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    has_disclaimer: bool = True
    unconfirmed_fields_detected: List[str] = Field(default_factory=list)
