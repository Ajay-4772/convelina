import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

class CorrectionDraft(Base):
    __tablename__ = "correction_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conflict_id = Column(UUID(as_uuid=True), ForeignKey("conflicts.id", ondelete="SET NULL"), nullable=True, index=True)
    document_type = Column(String(50), nullable=False)
    document_category = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft, edited, approved
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    confirmed_fields = Column(JSONB, nullable=False, default=dict)
    source_references = Column(JSONB, nullable=False, default=list)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="correction_drafts")
    conflict = relationship("Conflict", backref="correction_drafts")
    versions = relationship("CorrectionDraftVersion", back_populates="draft", cascade="all, delete-orphan", order_by="CorrectionDraftVersion.version_number.desc()")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "conflict_id": str(self.conflict_id) if self.conflict_id else None,
            "document_type": self.document_type,
            "document_category": self.document_category,
            "status": self.status,
            "title": self.title,
            "content": self.content,
            "confirmed_fields": self.confirmed_fields or {},
            "source_references": self.source_references or [],
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CorrectionDraftVersion(Base):
    __tablename__ = "correction_draft_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("correction_drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    change_type = Column(String(50), nullable=False, default="initial_generation")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    draft = relationship("CorrectionDraft", back_populates="versions")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": str(self.id),
            "draft_id": str(self.draft_id),
            "user_id": str(self.user_id),
            "version_number": self.version_number,
            "content": self.content,
            "change_type": self.change_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
