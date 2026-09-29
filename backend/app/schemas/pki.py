from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SigningKeyCreate(BaseModel):
    key_id: str = Field(..., min_length=3, max_length=64, description="Unique human-readable key identifier")
    public_key: str = Field(..., description="Base64 encoded Ed25519 public key")
    purpose: str = Field(default="document_attestation", max_length=100)
    valid_until: Optional[datetime] = None


class SigningKeyRevokeRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500, description="Mandatory reason for key revocation")


class SigningKeyRotateRequest(BaseModel):
    new_key_id: str = Field(..., min_length=3, max_length=64)
    new_public_key: Optional[str] = None
    purpose: str = Field(default="document_attestation", max_length=100)


class SigningKeyResponse(BaseModel):
    id: str
    key_id: str
    public_key: str
    fingerprint: str
    algorithm: str
    purpose: str
    status: str
    valid_from: str
    valid_until: Optional[str] = None
    revoked_at: Optional[str] = None
    revocation_reason: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class DocumentAttestationCreate(BaseModel):
    document_id: Optional[UUID] = None
    case_id: Optional[UUID] = None
    correction_draft_id: Optional[UUID] = None
    document_type: str = Field(..., min_length=2, max_length=50)
    document_fingerprint: str = Field(..., min_length=64, max_length=64, description="SHA-256 hex digest of document")
    key_id: Optional[str] = Field(None, description="Optional key_id; defaults to active system/officer key")
    signing_purpose: str = Field(default="identity_discrepancy_verification", max_length=100)
    expires_in_days: Optional[int] = Field(default=365, ge=1, le=3650)


class DocumentAttestationResponse(BaseModel):
    id: str
    document_id: Optional[str] = None
    case_id: Optional[str] = None
    correction_draft_id: Optional[str] = None
    citizen_id: str
    officer_id: str
    document_type: str
    document_fingerprint: str
    signing_key_id: str
    key_id: str
    canonical_payload: Dict[str, Any]
    signature: str
    algorithm: str
    status: str
    expires_at: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class AttestationVerifyRequest(BaseModel):
    document_hash: Optional[str] = Field(None, min_length=64, max_length=64, description="SHA-256 hash to test integrity against")
    simulate_tamper: Optional[bool] = Field(False, description="Simulate a corrupted document hash to test tamper detection")


class StandaloneVerifyRequest(BaseModel):
    canonical_payload: Dict[str, Any]
    signature: str
    public_key_b64: Optional[str] = None
    key_id: Optional[str] = None
    document_hash: Optional[str] = None


class VerificationResultResponse(BaseModel):
    verification_status: str
    is_valid: bool
    human_readable_summary: str
    signature_valid: bool
    document_integrity_valid: bool
    key_trusted: bool
    key_status: str
    attestation_id: Optional[str] = None
    key_id: str
    fingerprint: Optional[str] = None
    details: Dict[str, Any]
    verified_at: str


class PKIStatsResponse(BaseModel):
    total_attestations: int
    valid_attestations: int
    revoked_attestations: int
    total_verifications: int
    valid_verifications: int
    tampered_detections: int
    active_keys: int
    revoked_keys: int
