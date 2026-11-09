import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    issuing_authority = Column(String(150), nullable=False)
    document_type = Column(String(50), nullable=False, default="guideline")
    document_category = Column(String(50), nullable=False, index=True)
    source_url = Column(String(512), nullable=False)
    jurisdiction = Column(String(50), nullable=False, default="India")
    language = Column(String(10), nullable=False, default="en")
    retrieved_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    last_verified_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    version = Column(String(30), nullable=True)
    content_hash = Column(String(64), nullable=False)
    verification_status = Column(String(20), nullable=False, default="verified")
    is_active = Column(Boolean, nullable=False, default=True)
    ingestion_status = Column(String(30), nullable=False, default="completed")
    uploaded_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    correction_category = Column(String(50), nullable=True)
    raw_content = Column(Text, nullable=True)
    metadata_payload = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "source_id": self.source_id,
            "title": self.title,
            "issuing_authority": self.issuing_authority,
            "document_type": self.document_type,
            "document_category": self.document_category,
            "correction_category": self.correction_category,
            "source_url": self.source_url,
            "jurisdiction": self.jurisdiction,
            "language": self.language,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "version": self.version,
            "content_hash": self.content_hash,
            "verification_status": self.verification_status,
            "ingestion_status": self.ingestion_status,
            "uploaded_by_user_id": str(self.uploaded_by_user_id) if self.uploaded_by_user_id else None,
            "review_notes": self.review_notes,
            "is_active": self.is_active,
            "metadata": self.metadata_payload or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
