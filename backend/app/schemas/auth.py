from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class UserProvisionRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255, description="Full legal name of citizen")
    phone_number: Optional[str] = Field(None, max_length=30)
    date_of_birth: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = None
    father_name: Optional[str] = Field(None, max_length=255)
    mother_name: Optional[str] = Field(None, max_length=255)

class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=30)
    date_of_birth: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = None
    father_name: Optional[str] = Field(None, max_length=255)
    mother_name: Optional[str] = Field(None, max_length=255)

class UserResponse(BaseModel):
    id: UUID
    firebase_uid: str
    email: str
    full_name: str
    role: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AuthHealthResponse(BaseModel):
    status: str
    firebase_configured: bool
    details: Optional[str] = None

class SendOTPRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)

class SendOTPResponse(BaseModel):
    success: bool
    message: str
    expires_in_seconds: int = 300

class VerifyOTPRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    otp_code: str = Field(..., min_length=6, max_length=6)

class VerifyOTPResponse(BaseModel):
    success: bool
    verified: bool
    message: str
    verification_token: Optional[str] = None

class UserActivityItem(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: Dict[str, Any]
    created_at: str

class UserActivityResponse(BaseModel):
    activities: List[UserActivityItem]
