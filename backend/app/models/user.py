import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Any = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid: Any = Column(String(128), unique=True, nullable=False, index=True)
    email: Any = Column(String(255), nullable=False)
    full_name: Any = Column(String(255), nullable=False)
    role: Any = Column(String(20), nullable=False, default="user")
    phone_number: Any = Column(String(30), nullable=True)
    date_of_birth: Any = Column(String(30), nullable=True)
    address: Any = Column(Text, nullable=True)
    father_name: Any = Column(String(255), nullable=True)
    mother_name: Any = Column(String(255), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "firebase_uid": self.firebase_uid,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "phone_number": self.phone_number,
            "date_of_birth": self.date_of_birth,
            "address": self.address,
            "father_name": self.father_name,
            "mother_name": self.mother_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EmailOTP(Base):
    __tablename__ = "email_otps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    otp_hash = Column(String(128), nullable=True)
    otp_salt = Column(String(64), nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    verification_token_hash = Column(String(128), nullable=True)
    request_ip = Column(String(64), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
