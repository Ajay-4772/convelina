from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CorrectionDraftCreate(BaseModel):
    conflict_id: UUID
    document_type: str = Field(
        default="correction_request_letter",
        description="Type of document: correction_request_letter, supporting_document_checklist, declaration_draft, general_correction_application"
    )
    document_category: str = Field(
        default="pan",
        description="Category: aadhaar, pan, passport, certificate, epfo"
    )
    confirmed_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="User-verified/confirmed fields (e.g. {'applicant_name': 'RAJESH KUMAR SHARMA'})"
    )
    user_explanation: Optional[str] = Field(
        default=None,
        description="Citizen's plain-language context or reason for the requested correction"
    )


class CorrectionDraftUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None  # generated, user_edited, approved
    confirmed_fields: Optional[Dict[str, Any]] = None


class CorrectionDraftRegenerateRequest(BaseModel):
    confirmed_fields: Optional[Dict[str, Any]] = None


class CorrectionDraftResponse(BaseModel):
    id: UUID
    user_id: UUID
    conflict_id: Optional[UUID] = None
    document_type: str
    document_category: str
    status: str
    title: str
    content: str
    confirmed_fields: Dict[str, Any] = Field(default_factory=dict)
    source_references: List[Dict[str, Any]] = Field(default_factory=list)
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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentValidationResult(BaseModel):
    is_valid: bool
    unresolved_placeholders: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    has_disclaimer: bool = True
