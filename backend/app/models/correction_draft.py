import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

MANDATORY_DRAFT_DISCLAIMER = (
    "AI-GENERATED ADMINISTRATIVE DRAFT — REVIEW ALL DETAILS AND VERIFY THE APPLICABLE OFFICIAL PROCEDURE BEFORE SUBMISSION."
)

class CorrectionDraft(Base):
    __tablename__ = "correction_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conflict_id = Column(UUID(as_uuid=True), ForeignKey("conflicts.id", ondelete="SET NULL"), nullable=True, index=True)
    document_type = Column(String(50), nullable=False, index=True)
    document_category = Column(String(50), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="ai_generated")  # ai_generated, citizen_edited, citizen_confirmed, generated, user_edited, approved
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    recipient_authority = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=True)
    user_explanation = Column(Text, nullable=True)
    requested_action = Column(Text, nullable=True)
    confirmed_fields = Column(JSONB, nullable=False, default=dict)
    supporting_documents = Column(JSONB, nullable=False, default=list)
    source_references = Column(JSONB, nullable=False, default=list)
    disclaimer = Column(Text, nullable=False, default=MANDATORY_DRAFT_DISCLAIMER)
    is_citizen_confirmed = Column(Boolean, nullable=False, default=False, index=True)
    citizen_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_version_number = Column(Integer, nullable=True)
    sha256_hash = Column(String(64), nullable=True)
    file_path = Column(String(512), nullable=True)
    language = Column(String(32), nullable=False, default="en")
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="correction_drafts")
    conflict = relationship("Conflict", backref="correction_drafts")
    versions = relationship(
        "CorrectionDraftVersion",
        back_populates="draft",
        cascade="all, delete-orphan",
        order_by="CorrectionDraftVersion.version_number.desc()"
    )

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
            "recipient_authority": self.recipient_authority,
            "subject": self.subject,
            "user_explanation": self.user_explanation,
            "requested_action": self.requested_action,
            "confirmed_fields": self.confirmed_fields or {},
            "supporting_documents": self.supporting_documents or [],
            "source_references": self.source_references or [],
            "disclaimer": self.disclaimer or MANDATORY_DRAFT_DISCLAIMER,
            "is_citizen_confirmed": bool(self.is_citizen_confirmed),
            "citizen_confirmed_at": self.citizen_confirmed_at.isoformat() if self.citizen_confirmed_at else None,
            "confirmed_version_number": self.confirmed_version_number,
            "sha256_hash": self.sha256_hash,
            "file_path": self.file_path,
            "language": self.language or "en",
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
    change_type = Column(String(50), nullable=False, default="initial_generation")  # initial_generation, manual_edit, regenerated, translation, citizen_confirmed
    recipient_authority = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=True)
    confirmed_fields = Column(JSONB, nullable=False, default=dict)
    supporting_documents = Column(JSONB, nullable=False, default=list)
    source_references = Column(JSONB, nullable=False, default=list)
    is_citizen_confirmed = Column(Boolean, nullable=False, default=False)
    citizen_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    sha256_hash = Column(String(64), nullable=True)
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
            "recipient_authority": self.recipient_authority,
            "subject": self.subject,
            "confirmed_fields": self.confirmed_fields or {},
            "supporting_documents": self.supporting_documents or [],
            "source_references": self.source_references or [],
            "is_citizen_confirmed": bool(self.is_citizen_confirmed),
            "citizen_confirmed_at": self.citizen_confirmed_at.isoformat() if self.citizen_confirmed_at else None,
            "sha256_hash": self.sha256_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
