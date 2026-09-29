import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base

class OfficialForm(Base):
    __tablename__ = "official_forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id = Column(String(100), unique=True, nullable=False, index=True)
    form_name = Column(String(255), nullable=False)
    document_category = Column(String(50), nullable=False, index=True)
    purpose = Column(Text, nullable=False)
    issuing_authority = Column(String(150), nullable=False)
    official_download_url = Column(String(512), nullable=False)
    instructions_source_id = Column(String(100), nullable=True)
    applicable_issue_types = Column(JSONB, nullable=False, default=list)
    applicable_conditions = Column(JSONB, nullable=False, default=list)
    language = Column(String(10), nullable=False, default="en")
    version = Column(String(30), nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    last_verified_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    verification_status = Column(String(20), nullable=False, default="verified")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "form_id": self.form_id,
            "form_name": self.form_name,
            "document_category": self.document_category,
            "purpose": self.purpose,
            "issuing_authority": self.issuing_authority,
            "official_download_url": self.official_download_url,
            "instructions_source_id": self.instructions_source_id,
            "applicable_issue_types": self.applicable_issue_types or [],
            "applicable_conditions": self.applicable_conditions or [],
            "language": self.language,
            "version": self.version,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "verification_status": self.verification_status,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
