"""
CONVELINA Document Authenticity & Ed25519 PKI Router
Provides API endpoints for public key management, attestation signing,
cryptographic verification, and tamper detection.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db, set_rls_context
from app.models.user import User
from app.models.pki import SigningKey, DocumentAttestation, AttestationVerification
from app.dependencies.auth import get_current_user, require_admin, require_officer
from app.schemas.pki import (
    SigningKeyCreate,
    SigningKeyResponse,
    SigningKeyRevokeRequest,
    SigningKeyRotateRequest,
    DocumentAttestationCreate,
    DocumentAttestationResponse,
    AttestationVerifyRequest,
    VerificationResultResponse,
    PKIStatsResponse,
)
from app.services.pki_service import PKIService

router = APIRouter(prefix="/api/v1", tags=["authenticity_and_pki"])


# ==============================================================================
# PKI Key Lifecycle Endpoints
# ==============================================================================

@router.get("/pki/stats", response_model=PKIStatsResponse)
def get_pki_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns platform-wide PKI and attestation statistics for the dashboard."""
    set_rls_context(db, current_user.id, current_user.role)
    return PKIService.get_stats(db)


@router.get("/pki/keys", response_model=List[SigningKeyResponse])
def list_signing_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists all public signing keys in the keystore.
    Public keys are public by definition to allow signature verification.
    """
    set_rls_context(db, current_user.id, current_user.role)
    keys = PKIService.list_keys(db)
    return [SigningKeyResponse(**k.to_dict()) for k in keys]


@router.post("/pki/keys", response_model=SigningKeyResponse, status_code=status.HTTP_201_CREATED)
def register_signing_key(
    req: SigningKeyCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Registers a new Ed25519 public key in the keystore. Restricted to Admins."""
    set_rls_context(db, current_admin.id, current_admin.role)
    key = PKIService.register_key(db, req, current_admin.id)
    return SigningKeyResponse(**key.to_dict())


@router.post("/pki/keys/{key_id}/rotate", response_model=SigningKeyResponse)
def rotate_signing_key(
    key_id: str,
    req: SigningKeyRotateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Rotates an active signing key.
    Marks the old key as inactive and registers the new key.
    Historical signatures signed with the previous key remain valid.
    Restricted to Admins."""
    set_rls_context(db, current_admin.id, current_admin.role)
    key = PKIService.rotate_key(db, key_id, req, current_admin.id)
    return SigningKeyResponse(**key.to_dict())


@router.post("/pki/keys/{key_id}/revoke", response_model=SigningKeyResponse)
def revoke_signing_key(
    key_id: str,
    req: SigningKeyRevokeRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """
    Revokes a compromised or decommissioned signing key.
    Requires an explicit written justification.
    Restricted to Admins."""
    set_rls_context(db, current_admin.id, current_admin.role)
    key = PKIService.revoke_key(db, key_id, req, current_admin.id)
    return SigningKeyResponse(**key.to_dict())


# ==============================================================================
# Document Attestation & Signing Endpoints
# ==============================================================================

@router.post("/attestations", response_model=DocumentAttestationResponse, status_code=status.HTTP_201_CREATED)
def create_document_attestation(
    req: DocumentAttestationCreate,
    citizen_id: UUID = Query(..., description="Target citizen whose document/case is being attested"),
    db: Session = Depends(get_db),
    current_officer: User = Depends(require_officer),
):
    """
    Cryptographically signs an attestation for a document or verified case using Ed25519.
    Creates a deterministic canonical signed payload and appends to the immutable audit trail.
    Restricted to Officers and Admins."""
    set_rls_context(db, current_officer.id, current_officer.role)
    attestation = PKIService.create_attestation(
        db=db,
        attestation_in=req,
        officer_id=current_officer.id,
        citizen_id=citizen_id,
    )
    return DocumentAttestationResponse(**attestation.to_dict())


@router.get("/attestations", response_model=List[DocumentAttestationResponse])
def list_attestations(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists document attestations within the caller's permitted RLS scope.
    Citizens view only their own attestations.
    Officers view attestations they signed or cases assigned to them.
    Admins view all platform attestations."""
    set_rls_context(db, current_user.id, current_user.role)
    attestations = (
        db.query(DocumentAttestation)
        .order_by(DocumentAttestation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [DocumentAttestationResponse(**a.to_dict()) for a in attestations]


@router.get("/attestations/{attestation_id}", response_model=DocumentAttestationResponse)
def get_attestation(
    attestation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves full attestation metadata including canonical payload and signature."""
    set_rls_context(db, current_user.id, current_user.role)
    attestation = db.query(DocumentAttestation).filter(DocumentAttestation.id == attestation_id).first()
    if not attestation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attestation not found or access denied",
        )
    return DocumentAttestationResponse(**attestation.to_dict())


@router.post("/attestations/{attestation_id}/verify", response_model=VerificationResultResponse)
def verify_document_attestation(
    attestation_id: UUID,
    req: Optional[AttestationVerifyRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Executes cryptographic signature verification and tamper detection for an attestation:
    - Verifies Ed25519 signature validity against canonical payload.
    - Checks public key trust status and revocation.
    - Checks document fingerprint consistency against supplied document hash.
    - Returns structured result: VALID, DOCUMENT_TAMPERED, INVALID_SIGNATURE, EXPIRED, REVOKED_KEY.
    - Persists verification record and logs tamper-evident audit event."""
    set_rls_context(db, current_user.id, current_user.role)
    doc_hash = req.document_hash if req else None
    simulate_tamper = req.simulate_tamper if req else False

    result = PKIService.verify_attestation(
        db=db,
        attestation_id=attestation_id,
        document_hash=doc_hash,
        verifier_id=current_user.id,
        simulate_tamper=simulate_tamper,
    )
    return result


@router.get("/attestations/{attestation_id}/verifications", response_model=List[Dict[str, Any]])
def get_attestation_verifications(
    attestation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns historical verification events for a specific attestation."""
    set_rls_context(db, current_user.id, current_user.role)
    records = (
        db.query(AttestationVerification)
        .filter(AttestationVerification.attestation_id == attestation_id)
        .order_by(AttestationVerification.verified_at.desc())
        .all()
    )
    return [r.to_dict() for r in records]


@router.get("/verifications/recent", response_model=List[Dict[str, Any]])
def get_recent_verifications(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns recent platform verification events within permitted RLS scope."""
    set_rls_context(db, current_user.id, current_user.role)
    records = (
        db.query(AttestationVerification)
        .order_by(AttestationVerification.verified_at.desc())
        .limit(limit)
        .all()
    )
    return [r.to_dict() for r in records]
