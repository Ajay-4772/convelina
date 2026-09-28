from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    id: str
    document_type: str
    file_hash: str
    ocr_status: str
    masked_id: Optional[str] = None
    extracted_fields: Dict[str, Any]
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
    extracted_fields: Dict[str, Any]
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]
