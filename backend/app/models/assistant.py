import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

def utc_now() -> datetime:
    """Helper returning timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)

class AssistantConversation(Base):
    __tablename__ = "assistant_conversations"

    id: Any = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Any = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Any = Column(String(255), nullable=False, default="New Conversation")
    active_case_id: Any = Column(UUID(as_uuid=True), nullable=True)
    active_conflict_id: Any = Column(UUID(as_uuid=True), ForeignKey("conflicts.id", ondelete="SET NULL"), nullable=True)
    is_pinned: Any = Column(Boolean, nullable=False, default=False)
    is_archived: Any = Column(Boolean, nullable=False, default=False)
    response_language: Any = Column(String(10), nullable=False, default="en")
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", backref="assistant_conversations")
    active_conflict = relationship("Conflict", backref="conversations")
    messages = relationship("AssistantMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AssistantMessage.created_at.asc()")

    def to_dict(self) -> Dict[str, Any]:
        msgs = getattr(self, "messages", None)
        msg_count = len(msgs) if isinstance(msgs, list) else 0
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": str(self.title),
            "active_case_id": str(self.active_case_id) if self.active_case_id else None,
            "active_conflict_id": str(self.active_conflict_id) if self.active_conflict_id else None,
            "is_pinned": bool(self.is_pinned),
            "is_archived": bool(self.is_archived),
            "response_language": str(self.response_language) if self.response_language else "en",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": msg_count,
        }

class AssistantMessage(Base):
    __tablename__ = "assistant_messages"
    __table_args__ = (
        Index("idx_assistant_msg_pagination", "conversation_id", "created_at", "id"),
    )

    id: Any = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Any = Column(UUID(as_uuid=True), ForeignKey("assistant_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Any = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Any = Column(String(20), nullable=False)  # user, assistant, system
    content: Any = Column(Text, nullable=False)
    message_type: Any = Column(String(30), nullable=False, default="chat")
    structured_response: Any = Column(JSONB, nullable=False, default=dict)
    citations: Any = Column(JSONB, nullable=False, default=list)
    tokens_used: Any = Column(Integer, nullable=False, default=0)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation = relationship("AssistantConversation", back_populates="messages")
    user = relationship("User", backref="assistant_messages")
    attachments = relationship("MessageAttachment", back_populates="message", cascade="all, delete-orphan", order_by="MessageAttachment.created_at.asc()")

    def to_dict(self) -> Dict[str, Any]:
        atts = getattr(self, "attachments", None)
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "role": self.role,
            "content": self.content,
            "message_type": self.message_type or "chat",
            "structured_response": self.structured_response or {},
            "citations": self.citations or [],
            "tokens_used": self.tokens_used,
            "attachments": [a.to_dict() for a in atts] if isinstance(atts, list) else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class MessageAttachment(Base):
    __tablename__ = "message_attachments"

    id: Any = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Any = Column(UUID(as_uuid=True), ForeignKey("assistant_messages.id", ondelete="CASCADE"), nullable=True, index=True)
    conversation_id: Any = Column(UUID(as_uuid=True), ForeignKey("assistant_conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    conflict_id: Any = Column(UUID(as_uuid=True), ForeignKey("conflicts.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Any = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name: Any = Column(String(255), nullable=False)
    mime_type: Any = Column(String(100), nullable=False)
    file_size_bytes: Any = Column(Integer, nullable=False)
    storage_ref: Any = Column(String(512), nullable=False)
    sha256_hash: Any = Column(String(64), nullable=True)
    extracted_text: Any = Column(Text, nullable=True)
    extracted_fields: Any = Column(JSONB, nullable=False, default=dict)
    ocr_confidence: Any = Column(Float, nullable=True)
    ocr_status: Any = Column(String(30), nullable=False, default="pending")
    status: Any = Column(String(30), nullable=False, default="UPLOADED")
    error_message: Any = Column(Text, nullable=True)
    is_temporary: Any = Column(Boolean, nullable=False, default=True)
    expires_at: Any = Column(DateTime(timezone=True), nullable=False)
    deleted_at: Any = Column(DateTime(timezone=True), nullable=True)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    message = relationship("AssistantMessage", back_populates="attachments")
    conversation = relationship("AssistantConversation", backref="attachments")
    conflict = relationship("Conflict", backref="attachments")
    user = relationship("User")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "message_id": str(self.message_id) if self.message_id else None,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "conflict_id": str(self.conflict_id) if self.conflict_id else None,
            "user_id": str(self.user_id),
            "file_name": str(self.file_name) if self.file_name is not None else "",
            "mime_type": str(self.mime_type) if self.mime_type is not None else "",
            "file_size_bytes": int(self.file_size_bytes) if self.file_size_bytes is not None else 0,
            "storage_ref": str(self.storage_ref) if self.storage_ref is not None else "",
            "sha256_hash": str(self.sha256_hash) if self.sha256_hash else None,
            "extracted_text": str(self.extracted_text) if self.extracted_text else None,
            "extracted_fields": dict(self.extracted_fields) if isinstance(self.extracted_fields, dict) else {},
            "ocr_confidence": float(self.ocr_confidence) if self.ocr_confidence is not None else None,
            "ocr_status": str(self.ocr_status or "pending"),
            "status": str(self.status or "UPLOADED"),
            "error_message": str(self.error_message) if self.error_message else None,
            "is_temporary": bool(self.is_temporary),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
