from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class UserProvisionRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255, description="Full legal name of citizen")
    # Client cannot submit or alter 'role'

class UserResponse(BaseModel):
    id: UUID
    firebase_uid: str
    email: str
    full_name: str
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AuthHealthResponse(BaseModel):
    status: str
    firebase_configured: bool
    details: Optional[str] = None
