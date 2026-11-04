from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# 0. Verification Status Taxonomy (Phase P2B)
# ---------------------------------------------------------------------------

class SourceVerificationStatus(str, Enum):
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"
    OUTDATED = "outdated"
    RETIRED = "retired"

class UpdateVerificationStatusRequest(BaseModel):
    verification_status: SourceVerificationStatus
    review_notes: Optional[str] = None

# ---------------------------------------------------------------------------
# 1. Knowledge Sources
# ---------------------------------------------------------------------------

class KnowledgeSourceResponse(BaseModel):
    id: str
    source_id: str
    title: str
    issuing_authority: str
    document_type: str
    document_category: str
    source_url: str
    jurisdiction: str
    language: str
    retrieved_at: str
    effective_date: Optional[str] = None
    last_verified_at: str
    version: Optional[str] = None
    content_hash: str
    verification_status: str
    is_active: bool
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

class KnowledgeSourceListResponse(BaseModel):
    total: int
    sources: List[KnowledgeSourceResponse]

class KnowledgeIngestionJobResponse(BaseModel):
    job_id: str
    status: str
    sources_indexed: int
    forms_indexed: int
    message: str

# ---------------------------------------------------------------------------
# 2. Official Forms
# ---------------------------------------------------------------------------

class OfficialFormResponse(BaseModel):
    id: Optional[str] = None
    form_id: str
    form_name: str
    document_category: str
    purpose: str
    issuing_authority: str
    official_download_url: str
    instructions_source_id: Optional[str] = None
    applicable_issue_types: List[str] = Field(default_factory=list)
    applicable_conditions: List[str] = Field(default_factory=list)
    language: str = "en"
    version: Optional[str] = None
    effective_date: Optional[str] = None
    last_verified_at: Optional[str] = None
    verification_status: str = "verified"
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)

class OfficialFormListResponse(BaseModel):
    total: int
    forms: List[OfficialFormResponse]

# ---------------------------------------------------------------------------
# 3. Traceable Citations
# ---------------------------------------------------------------------------

class SourceCitation(BaseModel):
    source_id: str
    title: str
    authority: str
    url: str
    section: Optional[str] = None
    verification_status: str = "verified"
    last_verified_at: Optional[str] = None

# ---------------------------------------------------------------------------
# 4. Structured RAG Grounded Answer
# ---------------------------------------------------------------------------

class ResolutionStep(BaseModel):
    step_number: int
    title: str
    description: str
    required_documents: List[str] = Field(default_factory=list)
    official_portal_or_form: Optional[str] = None

class FutureImplication(BaseModel):
    area: str
    risk_assessment: str = Field(..., description="conditional, documented_requirement, or uncertain")
    explanation: str
    suggested_action: str

class GroundedAnswer(BaseModel):
    answer: str
    issue_summary: Optional[str] = None
    resolution_steps: List[ResolutionStep] = Field(default_factory=list)
    relevant_forms: List[OfficialFormResponse] = Field(default_factory=list)
    potential_future_implications: List[FutureImplication] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    citations: List[SourceCitation] = Field(default_factory=list)
    requires_clarification: bool = False
    confidence: str = Field("supported", description="supported, partially_supported, or insufficient_evidence")
    is_fallback: bool = False
    provider_status: str = Field("operational", description="operational, fallback_offline, or insufficient_evidence")

# ---------------------------------------------------------------------------
# 5. Assistant Conversations & Messages
# ---------------------------------------------------------------------------

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"
    active_case_id: Optional[str] = None
    active_conflict_id: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    active_case_id: Optional[str] = None
    active_conflict_id: Optional[str] = None
    created_at: str
    updated_at: str
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class ConversationListResponse(BaseModel):
    total: int
    conversations: List[ConversationResponse]

class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    conflict_id: Optional[str] = None
    case_id: Optional[str] = None
    document_category: Optional[str] = None

class ChatMessageResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: str = "assistant"
    response: GroundedAnswer
    created_at: Optional[str] = None

class MessageHistoryItem(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    structured_response: Dict[str, Any] = Field(default_factory=dict)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str

    model_config = ConfigDict(from_attributes=True)

class MessageListResponse(BaseModel):
    total: int
    messages: List[MessageHistoryItem]

# ---------------------------------------------------------------------------
# 6. Resolution Context Grounding & Workflow Mapping (Phase P2A & P2B)
# ---------------------------------------------------------------------------

class MappedFormRef(BaseModel):
    form_id: str
    form_name: str
    issuing_authority: str
    official_download_url: str
    purpose: str

    model_config = ConfigDict(from_attributes=True)

class ResolutionProcedureMapping(BaseModel):
    target_document_category: str
    authority_name: str
    authority_portal: str
    procedure_name: str
    procedure_type: str  # "minor_correction", "major_name_change", "statutory_linkage", "manual_review"
    prescribed_forms: List[MappedFormRef] = Field(default_factory=list)
    document_checklist: List[str] = Field(default_factory=list)
    submission_channel: str  # "online_portal", "physical_center", "joint_employer_physical", "court_gazette"
    statutory_rules: List[str] = Field(default_factory=list)
    official_fee_guidance: Optional[str] = None
    sla_guidance: Optional[str] = None
    action_priority: str = "medium"  # "high", "medium", "low"

    model_config = ConfigDict(from_attributes=True)

class ResolutionContext(BaseModel):
    conflict_id: str
    user_id: str
    field_name: str
    conflict_type: str
    severity: str
    status: str
    document_types: List[str] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list)
    value_a: str = ""
    value_b: str = ""
    deterministic_classification: str
    overall_classification: str
    confidence_score: float = 1.0
    requires_manual_review: bool = False
    possible_causes: List[str] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    ocr_quality_warning: Optional[str] = None
    non_latin_warning: Optional[str] = None
    statutory_disclaimer: str = "AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION"
    resolution_mapping: Optional[ResolutionProcedureMapping] = None

    model_config = ConfigDict(from_attributes=True)

