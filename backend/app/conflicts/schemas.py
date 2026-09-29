from typing import List, Optional
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
