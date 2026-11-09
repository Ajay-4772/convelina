import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base

def utc_now() -> datetime:
    """Helper returning timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)

class OfficialForm(Base):
    __tablename__ = "official_forms"

    id: Any = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id: Any = Column(String(100), unique=True, nullable=False, index=True)
    form_name: Any = Column(String(255), nullable=False)
    document_category: Any = Column(String(50), nullable=False, index=True)
    purpose: Any = Column(Text, nullable=False)
    description: Any = Column(Text, nullable=True)
    issuing_authority: Any = Column(String(150), nullable=False)
    official_download_url: Any = Column(String(512), nullable=False)
    instructions_source_id: Any = Column(String(100), nullable=True)
    applicable_issue_types: Any = Column(JSONB, nullable=False, default=list)
    applicable_conditions: Any = Column(JSONB, nullable=False, default=list)
    language: Any = Column(String(10), nullable=False, default="en")
    version: Any = Column(String(30), nullable=True)
    effective_date: Any = Column(DateTime(timezone=True), nullable=True)
    last_verified_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    verification_status: Any = Column(String(20), nullable=False, default="unverified")
    is_active: Any = Column(Boolean, nullable=False, default=True)

    # Document Provenance & Authenticity Classification (P3D.1)
    provenance: Any = Column(String(30), nullable=False, default="UNVERIFIED")
    provenance_notes: Any = Column(Text, nullable=True)
    official_source_published_at: Any = Column(DateTime(timezone=True), nullable=True)
    verified_by_user_id: Any = Column(UUID(as_uuid=True), nullable=True)

    # Enhanced P3D storage and cryptographic integrity fields
    file_size_bytes: Any = Column(Integer, nullable=False, default=0)
    mime_type: Any = Column(String(100), nullable=False, default="application/pdf")
    file_format: Any = Column(String(20), nullable=False, default="pdf")
    sha256_hash: Any = Column(String(64), nullable=True, index=True)
    storage_path: Any = Column(String(512), nullable=True)
    metadata_payload: Any = Column(JSONB, nullable=False, default=dict)

    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "form_id": self.form_id,
            "form_name": self.form_name,
            "document_category": self.document_category,
            "purpose": self.purpose,
            "description": self.description or self.purpose,
            "issuing_authority": self.issuing_authority,
            "official_download_url": self.official_download_url,
            "instructions_source_id": self.instructions_source_id,
            "applicable_issue_types": self.applicable_issue_types or [],
            "applicable_conditions": self.applicable_conditions or [],
            "language": self.language,
            "version": self.version,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "verification_status": self.verification_status,
            "is_active": bool(self.is_active),
            "provenance": self.provenance or "UNVERIFIED",
            "provenance_notes": self.provenance_notes,
            "official_source_published_at": self.official_source_published_at.isoformat() if self.official_source_published_at else None,
            "verified_by_user_id": str(self.verified_by_user_id) if self.verified_by_user_id else None,
            "file_size_bytes": int(self.file_size_bytes or 0),
            "mime_type": self.mime_type or "application/pdf",
            "file_format": self.file_format or "pdf",
            "sha256_hash": self.sha256_hash,
            "storage_path": self.storage_path,
            "metadata_payload": self.metadata_payload or {},
            "is_official_government_form": (
                self.provenance in ("OFFICIAL_ORIGINAL", "OFFICIAL_COPY")
                and self.verification_status == "verified"
            ),
            "is_synthetic_sample": (
                self.provenance in ("SYNTHETIC_DEVELOPMENT_SAMPLE", "SYNTHETIC_TEST_ASSET", "APPLICATION_GENERATED")
            ),
            "disclaimer": (
                "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM"
                if self.provenance in ("SYNTHETIC_DEVELOPMENT_SAMPLE", "SYNTHETIC_TEST_ASSET", "APPLICATION_GENERATED")
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OfficialFormVersion(Base):
    __tablename__ = "official_form_versions"

    id: Any = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id: Any = Column(String(100), nullable=False, index=True)
    version: Any = Column(String(30), nullable=True)
    form_name: Any = Column(String(255), nullable=False)
    document_category: Any = Column(String(50), nullable=False)
    issuing_authority: Any = Column(String(150), nullable=False)
    purpose: Any = Column(Text, nullable=False)
    official_download_url: Any = Column(String(512), nullable=False)
    sha256_hash: Any = Column(String(64), nullable=True)
    file_size_bytes: Any = Column(Integer, nullable=False, default=0)
    storage_path: Any = Column(String(512), nullable=True)
    provenance: Any = Column(String(30), nullable=False, default="SYNTHETIC_TEST_ASSET")
    provenance_notes: Any = Column(Text, nullable=True)
    verification_status: Any = Column(String(20), nullable=False, default="unverified")
    retired_by_user_id: Any = Column(UUID(as_uuid=True), nullable=True)
    retired_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "form_id": self.form_id,
            "version": self.version,
            "form_name": self.form_name,
            "document_category": self.document_category,
            "issuing_authority": self.issuing_authority,
            "purpose": self.purpose,
            "official_download_url": self.official_download_url,
            "sha256_hash": self.sha256_hash,
            "file_size_bytes": int(self.file_size_bytes or 0),
            "storage_path": self.storage_path,
            "provenance": self.provenance,
            "provenance_notes": self.provenance_notes,
            "verification_status": self.verification_status,
            "retired_by_user_id": str(self.retired_by_user_id) if self.retired_by_user_id else None,
            "retired_at": self.retired_at.isoformat() if self.retired_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

