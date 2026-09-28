import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False)
    ocr_status = Column(String(20), nullable=False, default="pending")
    extracted_fields = Column(JSONB, nullable=False, default=dict)
    masked_id = Column(String(50), nullable=True)
    encrypted_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="documents")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "document_type": self.document_type,
            "file_hash": self.file_hash,
            "ocr_status": self.ocr_status,
            "extracted_fields": self.extracted_fields or {},
            "masked_id": self.masked_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
