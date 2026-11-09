import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base


class CitizenChecklistItem(Base):
    """
    Persistent state of citizen preparation checklist items.
    Enforces Row-Level Security: citizens can only query and mutate their own checklist progress.
    """
    __tablename__ = "citizen_checklist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    procedure_id = Column(String(100), nullable=False, index=True)
    item_id = Column(String(100), nullable=False)
    is_completed = Column(Boolean, nullable=False, default=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "procedure_id", "item_id", name="uq_citizen_checklist_user_proc_item"),
    )

