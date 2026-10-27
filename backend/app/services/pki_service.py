"""
CONVELINA PKI & Verification Service
Implements Ed25519 key lifecycle management, canonical attestation signing,
and multi-factor cryptographic verification (tamper detection, revocation, expiration).
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.crypto import (
    CanonicalJSONSerializer,
    DocumentFingerprinter,
    Ed25519CryptoManager,
    DevSigningKeyProvider,
)
from app.models.pki import SigningKey, DocumentAttestation, AttestationVerification
from app.models.case import Case
from app.models.document import Document
from app.schemas.pki import (
    DocumentAttestationCreate,
    SigningKeyCreate,
    SigningKeyRevokeRequest,
    SigningKeyRotateRequest,
    VerificationResultResponse,
    PKIStatsResponse,
)
from app.services.audit_service import AuditService


class PKIVerificationStatus:
    VALID = "VALID"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    DOCUMENT_TAMPERED = "DOCUMENT_TAMPERED"
    EXPIRED = "EXPIRED"
    REVOKED_KEY = "REVOKED_KEY"
    UNTRUSTED_KEY = "UNTRUSTED_KEY"
    UNVERIFIABLE = "UNVERIFIABLE"
    UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION"


class PKIService:
    DEFAULT_KEY_ID = "consolith-officer-key-2026-v1"

    @classmethod
    def ensure_default_signing_key(cls, db: Session) -> SigningKey:
        """
        Ensures at least one active Ed25519 signing key exists in the database.
        Registers the default dev key if none is present.
        """
        default_key = (
            db.query(SigningKey)
            .filter(SigningKey.key_id == cls.DEFAULT_KEY_ID, SigningKey.status == "active")
            .first()
        )
        if default_key:
            return default_key

        active_key = (
            db.query(SigningKey)
            .filter(SigningKey.status == "active")
            .order_by(SigningKey.created_at.asc())
            .first()
        )
        if active_key:
            return active_key

        priv, pub_b64, fingerprint = DevSigningKeyProvider.create_or_get_default_dev_key(cls.DEFAULT_KEY_ID)
        
        new_key = SigningKey(
            id=uuid.uuid4(),
            key_id=cls.DEFAULT_KEY_ID,
            public_key=pub_b64,
            fingerprint=fingerprint,
            algorithm="Ed25519",
            purpose="document_attestation",
            status="active",
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=730),  # 2 years
            created_at=datetime.now(timezone.utc),
        )
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        return new_key

    @classmethod
    def list_keys(cls, db: Session) -> List[SigningKey]:
        cls.ensure_default_signing_key(db)
        return db.query(SigningKey).order_by(SigningKey.created_at.desc()).all()

    @classmethod
    def get_key_by_id(cls, db: Session, key_id: str) -> Optional[SigningKey]:
        return db.query(SigningKey).filter(SigningKey.key_id == key_id).first()

    @classmethod
    def register_key(cls, db: Session, key_in: SigningKeyCreate, admin_id: UUID) -> SigningKey:
        existing = db.query(SigningKey).filter(SigningKey.key_id == key_in.key_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Signing key with key_id '{key_in.key_id}' already exists",
            )

        try:
            pub = Ed25519CryptoManager.public_key_from_base64(key_in.public_key)
            fingerprint = Ed25519CryptoManager.compute_public_key_fingerprint(pub)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 Ed25519 public key: {str(e)}",
            )

        key = SigningKey(
            id=uuid.uuid4(),
            key_id=key_in.key_id,
            public_key=key_in.public_key,
            fingerprint=fingerprint,
            algorithm="Ed25519",
            purpose=key_in.purpose,
            status="active",
            valid_from=datetime.now(timezone.utc),
            valid_until=key_in.valid_until,
            created_by=admin_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(key)
        AuditService.log_event(
            db=db,
            action="PKI_KEY_REGISTERED",
            entity_type="signing_key",
            entity_id=key.id,
            user_id=admin_id,
            details={"key_id": key.key_id, "fingerprint": key.fingerprint},
        )
        db.commit()
        return key

    @classmethod
    def rotate_key(cls, db: Session, old_key_id: str, req: SigningKeyRotateRequest, admin_id: UUID) -> SigningKey:
        old_key = db.query(SigningKey).filter(SigningKey.key_id == old_key_id).first()
        if not old_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Key '{old_key_id}' not found",
            )

        # Mark old key inactive
        old_key.status = "inactive"

        # Generate or register new key
        if req.new_public_key:
            pub = Ed25519CryptoManager.public_key_from_base64(req.new_public_key)
            fingerprint = Ed25519CryptoManager.compute_public_key_fingerprint(pub)
            pub_b64 = req.new_public_key
        else:
            # Generate new keypair in dev provider
            priv, pub_b64, fingerprint = DevSigningKeyProvider.create_or_get_default_dev_key(req.new_key_id)

        new_key = SigningKey(
            id=uuid.uuid4(),
            key_id=req.new_key_id,
            public_key=pub_b64,
            fingerprint=fingerprint,
            algorithm="Ed25519",
            purpose=req.purpose,
            status="active",
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=730),
            created_by=admin_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(new_key)
        AuditService.log_event(
            db=db,
            action="PKI_KEY_ROTATED",
            entity_type="signing_key",
            entity_id=new_key.id,
            user_id=admin_id,
            details={
                "previous_key_id": old_key_id,
                "new_key_id": req.new_key_id,
                "new_fingerprint": fingerprint,
            },
        )
        db.commit()
        return new_key

    @classmethod
    def revoke_key(cls, db: Session, key_id: str, req: SigningKeyRevokeRequest, admin_id: UUID) -> SigningKey:
        key = db.query(SigningKey).filter(SigningKey.key_id == key_id).first()
        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Key '{key_id}' not found",
            )
        if key.status == "revoked":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Key '{key_id}' is already revoked",
            )

        key.status = "revoked"
        key.revoked_at = datetime.now(timezone.utc)
        key.revocation_reason = req.reason
        AuditService.log_event(
            db=db,
            action="PKI_KEY_REVOKED",
            entity_type="signing_key",
            entity_id=key.id,
            user_id=admin_id,
            details={"key_id": key.key_id, "reason": req.reason},
        )
        db.commit()
        return key

    @classmethod
    def create_attestation(
        cls,
        db: Session,
        attestation_in: DocumentAttestationCreate,
        officer_id: UUID,
        citizen_id: UUID,
    ) -> DocumentAttestation:
        """
        Signs an eligible document or case attestation using an active Ed25519 signing key.
        Builds the canonical deterministic payload, calculates signature, and audits.
        """
        # Validate fingerprint format
        if not DocumentFingerprinter.validate_hash_format(attestation_in.document_fingerprint):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document_fingerprint format. Must be a 64-character SHA-256 hex string.",
            )

        # Select signing key
        if attestation_in.key_id:
            signing_key = db.query(SigningKey).filter(SigningKey.key_id == attestation_in.key_id).first()
            if not signing_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Signing key '{attestation_in.key_id}' not found",
                )
            if signing_key.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Signing key '{attestation_in.key_id}' is not active (status: {signing_key.status})",
                )
        else:
            signing_key = cls.ensure_default_signing_key(db)

        # Retrieve private key from DevSigningKeyProvider (or HSM/KMS boundary)
        private_key = DevSigningKeyProvider.get_dev_key(signing_key.key_id)
        if not private_key:
            # Re-generate/fetch from provider if dev key
            private_key, _, _ = DevSigningKeyProvider.create_or_get_default_dev_key(signing_key.key_id)

        attestation_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=attestation_in.expires_in_days) if attestation_in.expires_in_days else None

        # Build versioned canonical signed payload
        canonical_payload = {
            "schema_version": "1.0",
            "attestation_id": str(attestation_id),
            "document_type": attestation_in.document_type,
            "document_fingerprint": attestation_in.document_fingerprint.lower(),
            "hash_algorithm": "SHA-256",
            "signing_algorithm": "Ed25519",
            "key_id": signing_key.key_id,
            "key_fingerprint": signing_key.fingerprint,
            "signing_purpose": attestation_in.signing_purpose,
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "issuer": "CONVELINA Verification PKI",
            "citizen_id": str(citizen_id),
            "officer_id": str(officer_id),
            "case_id": str(attestation_in.case_id) if attestation_in.case_id else None,
            "document_id": str(attestation_in.document_id) if attestation_in.document_id else None,
            "policy_version": "2026.1",
        }

        # Deterministic cryptographic signature
        signature_b64 = Ed25519CryptoManager.sign_payload(private_key, canonical_payload)

        attestation = DocumentAttestation(
            id=attestation_id,
            document_id=attestation_in.document_id,
            case_id=attestation_in.case_id,
            correction_draft_id=attestation_in.correction_draft_id,
            citizen_id=citizen_id,
            officer_id=officer_id,
            document_type=attestation_in.document_type,
            document_fingerprint=attestation_in.document_fingerprint.lower(),
            signing_key_id=signing_key.id,
            key_id=signing_key.key_id,
            canonical_payload=canonical_payload,
            signature=signature_b64,
            algorithm="Ed25519",
            status="valid",
            expires_at=expires_at,
            created_at=now,
        )
        db.add(attestation)
        AuditService.log_event(
            db=db,
            action="DOCUMENT_ATTESTATION_SIGNED",
            entity_type="document_attestation",
            entity_id=attestation.id,
            user_id=officer_id,
            details={
                "document_fingerprint": attestation.document_fingerprint,
                "key_id": signing_key.key_id,
                "document_type": attestation.document_type,
            },
        )
        db.commit()
        return attestation

    @classmethod
    def verify_attestation(
        cls,
        db: Session,
        attestation_id: UUID,
        document_hash: Optional[str] = None,
        verifier_id: Optional[UUID] = None,
        simulate_tamper: bool = False,
    ) -> VerificationResultResponse:
        """
        Executes multi-factor cryptographic verification for a given attestation:
        1. Checks payload format & schema version.
        2. Looks up public key by key_id and checks revocation & expiration.
        3. Verifies Ed25519 signature mathematically against canonical payload.
        4. Verifies attestation expiration date.
        5. Verifies document fingerprint consistency against supplied document hash.
        Records the verification event in database and audit trail.
        """
        attestation = db.query(DocumentAttestation).filter(DocumentAttestation.id == attestation_id).first()
        if not attestation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attestation '{attestation_id}' not found",
            )

        now = datetime.now(timezone.utc)
        payload = attestation.canonical_payload or {}
        key_id = attestation.key_id
        doc_fp = attestation.document_fingerprint

        # If simulate_tamper is requested, overwrite test hash with mismatched hash
        if simulate_tamper:
            document_hash = "000000000000000000000000000000000000000000000000000000000000dead"

        # Check Schema Version
        schema_version = payload.get("schema_version")
        if schema_version != "1.0":
            return cls._record_and_return_verification(
                db=db,
                attestation=attestation,
                verifier_id=verifier_id,
                status_code=PKIVerificationStatus.UNSUPPORTED_VERSION,
                summary=f"Unsupported payload schema version '{schema_version}'. Expected '1.0'.",
                sig_valid=False,
                doc_valid=False,
                key_trusted=False,
                key_status="unknown",
            )

        # Lookup Signing Key
        signing_key = db.query(SigningKey).filter(SigningKey.key_id == key_id).first()
        if not signing_key:
            return cls._record_and_return_verification(
                db=db,
                attestation=attestation,
                verifier_id=verifier_id,
                status_code=PKIVerificationStatus.UNTRUSTED_KEY,
                summary=f"The signing key '{key_id}' is not in CONVELINA's trusted PKI keystore.",
                sig_valid=False,
                doc_valid=False,
                key_trusted=False,
                key_status="untrusted",
            )

        key_status = signing_key.status

        # Check Key Revocation
        if key_status == "revoked":
            return cls._record_and_return_verification(
                db=db,
                attestation=attestation,
                verifier_id=verifier_id,
                status_code=PKIVerificationStatus.REVOKED_KEY,
                summary=f"The signing key '{key_id}' was revoked on {signing_key.revoked_at}. Reason: {signing_key.revocation_reason or 'No reason specified'}.",
                sig_valid=False,
                doc_valid=False,
                key_trusted=False,
                key_status=key_status,
            )

        # Check Key Expiration
        if signing_key.valid_until and now > signing_key.valid_until:
            return cls._record_and_return_verification(
                db=db,
                attestation=attestation,
                verifier_id=verifier_id,
                status_code=PKIVerificationStatus.EXPIRED,
                summary=f"The signing key '{key_id}' expired on {signing_key.valid_until.isoformat()}.",
                sig_valid=False,
                doc_valid=False,
                key_trusted=True,
                key_status="expired",
            )

        # Mathematical Ed25519 Signature Verification
        is_signature_valid = Ed25519CryptoManager.verify_signature(
            public_key_b64=signing_key.public_key,
            signature_b64=attestation.signature,
            canonical_payload=payload,
        )

        if not is_signature_valid:
            return cls._record_and_return_verification(
                db=db,
                attestation=attestation,
                verifier_id=verifier_id,
                status_code=PKIVerificationStatus.INVALID_SIGNATURE,
                summary="The cryptographic signature does not match the canonical signed payload and public key. Signature verification failed.",
                sig_valid=False,
                doc_valid=False,
                key_trusted=True,
                key_status=key_status,
            )

        # Check Attestation Expiration
        if attestation.expires_at and now > attestation.expires_at:
            return cls._record_and_return_verification(
                db=db,
                attestation=attestation,
                verifier_id=verifier_id,
                status_code=PKIVerificationStatus.EXPIRED,
                summary=f"This document attestation expired on {attestation.expires_at.isoformat()}.",
                sig_valid=True,
                doc_valid=True,
                key_trusted=True,
                key_status=key_status,
            )

        # Check Document Fingerprint Integrity
        doc_integrity_valid = True
        if document_hash:
            if document_hash.lower() != doc_fp.lower():
                return cls._record_and_return_verification(
                    db=db,
                    attestation=attestation,
                    verifier_id=verifier_id,
                    status_code=PKIVerificationStatus.DOCUMENT_TAMPERED,
                    summary=f"Document tampering detected! The presented document fingerprint ({document_hash[:16]}...) does not match the cryptographically signed fingerprint ({doc_fp[:16]}...).",
                    sig_valid=True,
                    doc_valid=False,
                    key_trusted=True,
                    key_status=key_status,
                    details={
                        "presented_fingerprint": document_hash.lower(),
                        "signed_fingerprint": doc_fp.lower(),
                    },
                )

        # All checks passed: VALID
        return cls._record_and_return_verification(
            db=db,
            attestation=attestation,
            verifier_id=verifier_id,
            status_code=PKIVerificationStatus.VALID,
            summary="Cryptographic Ed25519 signature is VALID, signing key is trusted, and document integrity is verified.",
            sig_valid=True,
            doc_valid=True,
            key_trusted=True,
            key_status=key_status,
        )

    @classmethod
    def _record_and_return_verification(
        cls,
        db: Session,
        attestation: DocumentAttestation,
        verifier_id: Optional[UUID],
        status_code: str,
        summary: str,
        sig_valid: bool,
        doc_valid: bool,
        key_trusted: bool,
        key_status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> VerificationResultResponse:
        verification_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        record_details = details or {}
        record_details["summary"] = summary

        # Persist verification record
        rec = AttestationVerification(
            id=verification_id,
            attestation_id=attestation.id,
            verifier_id=verifier_id,
            verification_status=status_code,
            details=record_details,
            verified_at=now,
        )
        db.add(rec)
        AuditService.log_event(
            db=db,
            action="DOCUMENT_VERIFICATION_PERFORMED",
            entity_type="document_attestation",
            entity_id=attestation.id,
            user_id=verifier_id or attestation.citizen_id,
            details={
                "verification_status": status_code,
                "key_id": attestation.key_id,
                "is_valid": status_code == PKIVerificationStatus.VALID,
            },
        )
        db.commit()

        return VerificationResultResponse(
            verification_status=status_code,
            is_valid=(status_code == PKIVerificationStatus.VALID),
            human_readable_summary=summary,
            signature_valid=sig_valid,
            document_integrity_valid=doc_valid,
            key_trusted=key_trusted,
            key_status=key_status,
            attestation_id=str(attestation.id),
            key_id=attestation.key_id,
            fingerprint=attestation.document_fingerprint,
            details=record_details,
            verified_at=now.isoformat(),
        )

    @classmethod
    def get_stats(cls, db: Session) -> PKIStatsResponse:
        cls.ensure_default_signing_key(db)
        total_att = db.query(func.count(DocumentAttestation.id)).scalar() or 0
        valid_att = db.query(func.count(DocumentAttestation.id)).filter(DocumentAttestation.status == "valid").scalar() or 0
        revoked_att = db.query(func.count(DocumentAttestation.id)).filter(DocumentAttestation.status == "revoked").scalar() or 0
        total_ver = db.query(func.count(AttestationVerification.id)).scalar() or 0
        valid_ver = db.query(func.count(AttestationVerification.id)).filter(AttestationVerification.verification_status == "VALID").scalar() or 0
        tampered_ver = db.query(func.count(AttestationVerification.id)).filter(AttestationVerification.verification_status == "DOCUMENT_TAMPERED").scalar() or 0
        active_keys = db.query(func.count(SigningKey.id)).filter(SigningKey.status == "active").scalar() or 0
        revoked_keys = db.query(func.count(SigningKey.id)).filter(SigningKey.status == "revoked").scalar() or 0

        return PKIStatsResponse(
            total_attestations=total_att,
            valid_attestations=valid_att,
            revoked_attestations=revoked_att,
            total_verifications=total_ver,
            valid_verifications=valid_ver,
            tampered_detections=tampered_ver,
            active_keys=active_keys,
            revoked_keys=revoked_keys,
        )
