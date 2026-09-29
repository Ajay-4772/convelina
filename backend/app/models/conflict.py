import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

class Conflict(Base):
    __tablename__ = "conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_a_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    doc_b_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    conflict_type = Column(String(30), nullable=False)
    severity = Column(String(10), nullable=False)
    field_name = Column(String(100), nullable=False)
    value_a = Column(Text, nullable=False)
    value_b = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="detected")
    comparison_method = Column(String(50), nullable=True, default="exact")
    similarity_score = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    doc_a = relationship("Document", foreign_keys=[doc_a_id], backref="conflicts_as_a")
    doc_b = relationship("Document", foreign_keys=[doc_b_id], backref="conflicts_as_b")
    user = relationship("User", backref="conflicts")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "doc_a_id": str(self.doc_a_id),
            "doc_b_id": str(self.doc_b_id),
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "field_name": self.field_name,
            "value_a": self.value_a,
            "value_b": self.value_b,
            "description": self.description,
            "status": self.status,
            "comparison_method": self.comparison_method,
            "similarity_score": float(self.similarity_score) if self.similarity_score is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
