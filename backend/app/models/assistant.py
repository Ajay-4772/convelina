import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean, Float
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("assistant_messages.id", ondelete="CASCADE"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("assistant_conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    conflict_id = Column(UUID(as_uuid=True), ForeignKey("conflicts.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_ref = Column(String(512), nullable=False)
    sha256_hash = Column(String(64), nullable=True)
    extracted_text = Column(Text, nullable=True)
    extracted_fields = Column(JSONB, nullable=False, default=dict)
    ocr_confidence = Column(Float, nullable=True)
    ocr_status = Column(String(30), nullable=False, default="pending")
    status = Column(String(30), nullable=False, default="UPLOADED")
    error_message = Column(Text, nullable=True)
    is_temporary = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    message = relationship("AssistantMessage", back_populates="attachments")
    conversation = relationship("AssistantConversation", backref="attachments")
    conflict = relationship("Conflict", backref="attachments")
    user = relationship("User")

    def to_dict(self):
        return {
            "id": str(self.id),
            "message_id": str(self.message_id) if self.message_id else None,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "conflict_id": str(self.conflict_id) if self.conflict_id else None,
            "user_id": str(self.user_id),
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "file_size_bytes": self.file_size_bytes,
            "storage_ref": self.storage_ref,
            "sha256_hash": self.sha256_hash,
            "extracted_text": self.extracted_text,
            "extracted_fields": self.extracted_fields or {},
            "ocr_confidence": float(self.ocr_confidence) if self.ocr_confidence is not None else None,
            "ocr_status": self.ocr_status or "pending",
            "status": self.status or "UPLOADED",
            "error_message": self.error_message,
            "is_temporary": bool(self.is_temporary),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
