from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class FieldExtractionSchema(BaseModel):
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence: float = 1.0
    page_number: int = 1
    bounding_box: Optional[Dict[str, float]] = None
    validation_status: str = "valid"
    review_required: bool = False
    source_document_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentUploadResponse(BaseModel):
    id: str
    document_type: str
    file_hash: str
    ocr_status: str
    masked_id: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    field_extractions: Dict[str, Any] = Field(default_factory=dict)
    confirmed_fields: Dict[str, Any] = Field(default_factory=dict)
    is_user_confirmed: bool = False
    confirmed_at: Optional[str] = None
    message: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: str
    user_id: str
    document_type: str
    file_hash: str
    ocr_status: str
    masked_id: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    field_extractions: Dict[str, Any] = Field(default_factory=dict)
    confirmed_fields: Dict[str, Any] = Field(default_factory=dict)
    is_user_confirmed: bool = False
    confirmed_at: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]

class DocumentFieldsUpdate(BaseModel):
    extracted_fields: Dict[str, Any]

class DocumentConfirmRequest(BaseModel):
    confirmed_fields: Dict[str, Any]

