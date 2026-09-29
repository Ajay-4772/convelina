import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class SigningKey(Base):
    __tablename__ = "signing_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_id = Column(String(64), unique=True, nullable=False, index=True)
    public_key = Column(String(128), nullable=False)
    fingerprint = Column(String(64), nullable=False, index=True)
    algorithm = Column(String(20), nullable=False, default="Ed25519")
    purpose = Column(String(100), nullable=False, default="document_attestation")
    status = Column(String(20), nullable=False, default="active", index=True)
    valid_from = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    creator = relationship("User", foreign_keys=[created_by])
    attestations = relationship("DocumentAttestation", back_populates="signing_key")

    def to_dict(self):
        return {
            "id": str(self.id),
            "key_id": self.key_id,
            "public_key": self.public_key,
            "fingerprint": self.fingerprint,
            "algorithm": self.algorithm,
            "purpose": self.purpose,
            "status": self.status,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revocation_reason": self.revocation_reason,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DocumentAttestation(Base):
    __tablename__ = "document_attestations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    correction_draft_id = Column(UUID(as_uuid=True), ForeignKey("correction_drafts.id", ondelete="SET NULL"), nullable=True)
    citizen_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    document_fingerprint = Column(String(64), nullable=False, index=True)
    signing_key_id = Column(UUID(as_uuid=True), ForeignKey("signing_keys.id", ondelete="RESTRICT"), nullable=False)
    key_id = Column(String(64), nullable=False)
    canonical_payload = Column(JSONB, nullable=False)
    signature = Column(String(256), nullable=False)
    algorithm = Column(String(20), nullable=False, default="Ed25519")
    status = Column(String(20), nullable=False, default="valid")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    citizen = relationship("User", foreign_keys=[citizen_id])
    officer = relationship("User", foreign_keys=[officer_id])
    signing_key = relationship("SigningKey", back_populates="attestations")
    document = relationship("Document", foreign_keys=[document_id])
    verifications = relationship("AttestationVerification", back_populates="attestation", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "document_id": str(self.document_id) if self.document_id else None,
            "case_id": str(self.case_id) if self.case_id else None,
            "correction_draft_id": str(self.correction_draft_id) if self.correction_draft_id else None,
            "citizen_id": str(self.citizen_id),
            "officer_id": str(self.officer_id),
            "document_type": self.document_type,
            "document_fingerprint": self.document_fingerprint,
            "signing_key_id": str(self.signing_key_id),
            "key_id": self.key_id,
            "canonical_payload": self.canonical_payload,
            "signature": self.signature,
            "algorithm": self.algorithm,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AttestationVerification(Base):
    __tablename__ = "attestation_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attestation_id = Column(UUID(as_uuid=True), ForeignKey("document_attestations.id", ondelete="CASCADE"), nullable=False, index=True)
    verifier_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    verification_status = Column(String(30), nullable=False)
    details = Column(JSONB, nullable=False, default=dict)
    verified_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    attestation = relationship("DocumentAttestation", back_populates="verifications")
    verifier = relationship("User", foreign_keys=[verifier_id])

    def to_dict(self):
        return {
            "id": str(self.id),
            "attestation_id": str(self.attestation_id),
            "verifier_id": str(self.verifier_id) if self.verifier_id else None,
            "verification_status": self.verification_status,
            "details": self.details or {},
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
        }
