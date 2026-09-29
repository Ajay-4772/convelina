import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    citizen_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    conflict_id = Column(UUID(as_uuid=True), ForeignKey("conflicts.id", ondelete="SET NULL"), nullable=True, index=True)
    correction_draft_id = Column(UUID(as_uuid=True), ForeignKey("correction_drafts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    status = Column(String(50), nullable=False, default="pending_assignment", index=True)
    title = Column(String(255), nullable=False)
    evidence_notes = Column(Text, nullable=True)
    officer_notes = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolution_signature = Column(Text, nullable=True)
    resolution_timestamp = Column(DateTime(timezone=True), nullable=True)

    review_started_at = Column(DateTime(timezone=True), nullable=True)
    decision = Column(String(30), nullable=True)
    decision_reason = Column(Text, nullable=True)
    decision_timestamp = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    citizen = relationship("User", foreign_keys=[citizen_id], backref="citizen_cases")
    assigned_officer = relationship("User", foreign_keys=[assigned_officer_id], backref="assigned_cases")
    conflict = relationship("Conflict", foreign_keys=[conflict_id], backref="cases")
    correction_draft = relationship("CorrectionDraft", foreign_keys=[correction_draft_id], backref="cases")
    review_requests = relationship("CaseReviewRequest", back_populates="case", cascade="all, delete-orphan")


class CaseEvidence(Base):
    __tablename__ = "case_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    case = relationship("Case", backref="evidence_items")
    document = relationship("Document")


class CaseReviewRequest(Base):
    __tablename__ = "case_review_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    citizen_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    request_details = Column(Text, nullable=False)
    request_reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, responded, closed
    response_text = Column(Text, nullable=True)
    response_timestamp = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    case = relationship("Case", back_populates="review_requests")
    officer = relationship("User", foreign_keys=[officer_id])
    citizen = relationship("User", foreign_keys=[citizen_id])
