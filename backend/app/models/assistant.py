import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

class AssistantConversation(Base):
    __tablename__ = "assistant_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="New Conversation")
    active_case_id = Column(UUID(as_uuid=True), nullable=True)
    active_conflict_id = Column(UUID(as_uuid=True), ForeignKey("conflicts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="assistant_conversations")
    active_conflict = relationship("Conflict", backref="conversations")
    messages = relationship("AssistantMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AssistantMessage.created_at.asc()")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "active_case_id": str(self.active_case_id) if self.active_case_id else None,
            "active_conflict_id": str(self.active_conflict_id) if self.active_conflict_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0,
        }

class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("assistant_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    structured_response = Column(JSONB, nullable=False, default=dict)
    citations = Column(JSONB, nullable=False, default=list)
    tokens_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    conversation = relationship("AssistantConversation", back_populates="messages")
    user = relationship("User", backref="assistant_messages")

    def to_dict(self):
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "user_id": str(self.user_id),
            "role": self.role,
            "content": self.content,
            "structured_response": self.structured_response or {},
            "citations": self.citations or [],
            "tokens_used": self.tokens_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
