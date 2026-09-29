from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CaseCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    conflict_id: Optional[UUID] = None
    correction_draft_id: Optional[UUID] = None
    evidence_notes: Optional[str] = None


class CaseAssignRequest(BaseModel):
    officer_id: UUID


class CaseRequestInformationRequest(BaseModel):
    request_details: str = Field(..., min_length=5, description="Clear description of the requested information or clarification")
    request_reason: str = Field(..., min_length=3, description="Official justification for the request")


class CaseRespondInformationRequest(BaseModel):
    response_text: str = Field(..., min_length=3, description="Citizen's response to the clarification request")


class CaseDecisionRequest(BaseModel):
    decision_reason: str = Field(..., min_length=5, description="Official review reasoning or justification for decision")
    officer_notes: Optional[str] = None


class CaseReviewRequestResponse(BaseModel):
    id: UUID
    case_id: UUID
    officer_id: UUID
    citizen_id: UUID
    request_details: str
    request_reason: str
    status: str
    response_text: Optional[str] = None
    response_timestamp: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseResponse(BaseModel):
    id: UUID
    citizen_id: UUID
    assigned_officer_id: Optional[UUID] = None
    conflict_id: Optional[UUID] = None
    correction_draft_id: Optional[UUID] = None
    status: str
    title: str
    evidence_notes: Optional[str] = None
    officer_notes: Optional[str] = None
    resolution_notes: Optional[str] = None
    review_started_at: Optional[datetime] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    decision_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    total: int
    items: List[CaseResponse]


class CaseDossierResponse(BaseModel):
    case: CaseResponse
    conflict_details: Optional[Dict[str, Any]] = None
    correction_draft: Optional[Dict[str, Any]] = None
    review_requests: List[CaseReviewRequestResponse] = Field(default_factory=list)
    audit_history: List[Dict[str, Any]] = Field(default_factory=list)


class OfficerWorkloadItem(BaseModel):
    officer_id: UUID
    officer_name: str
    officer_email: str
    assigned_active_cases: int
    completed_reviews: int
