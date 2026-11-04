from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class ConflictResponse(BaseModel):
    id: str
    user_id: str
    doc_a_id: str
    doc_b_id: str
    conflict_type: str
    severity: str
    field_name: str
    value_a: str
    value_b: str
    description: str
    status: str
    comparison_method: Optional[str] = "exact"
    similarity_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

class ConflictListResponse(BaseModel):
    total: int
    conflicts: List[ConflictResponse]

class ConflictReviewUpdate(BaseModel):
    status: str = Field(..., description="Review status: detected, in_review, resolved, or ignored")

class ConflictDetectResponse(BaseModel):
    total_documents_analyzed: int
    total_conflicts_detected: int
    new_conflicts_created: int
    conflicts: List[ConflictResponse]
    message: str

class DocumentCompareRequest(BaseModel):
    document_ids: List[UUID] = Field(
        ...,
        min_length=2,
        max_length=10,
        description="List of document IDs belonging to the authenticated user to compare",
    )

class DocumentMetadataSummary(BaseModel):
    id: str
    document_type: str
    masked_id: Optional[str] = None
    ocr_status: str
    created_at: str

class DocumentCompareResponse(BaseModel):
    overall_classification: str
    confidence_score: float
    requires_manual_review: bool
    action_recommended: bool
    matched_fields: List[str]
    conflicting_fields: List[str]
    ambiguous_fields: List[str]
    field_results: Dict[str, Any]
    evidence: List[str]
    explanation: str
    warnings: List[str]
    documents_compared: List[DocumentMetadataSummary]
    discrepancies_count: int
    conflicts_created: int
    disclaimer: str = (
        "AUTOMATED COMPARISON RESULT: CONVELINA provides automated identity discrepancy "
        "detection and statutory guidance. It does not constitute official government verification or certification."
    )

