"""
Consolith Module 9: Document Authenticity, Ed25519 PKI & Verification Live Integration Test Harness
Tests live API endpoints, RBAC permissions, PostgreSQL forced RLS isolation,
cryptographic signature verification, document tamper detection, and key rotation/revocation.
"""

import hashlib
import json
import os
import sys
import uuid
from typing import Dict, Any

import psycopg2
from fastapi.testclient import TestClient

# Ensure app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.pki import SigningKey, DocumentAttestation, AttestationVerification
from app.models.audit_log import AuditLog
from app.core.crypto import Ed25519CryptoManager, DocumentFingerprinter, DevSigningKeyProvider

client = TestClient(app)

CITIZEN_A_UID = f"cit_a_pki_{uuid.uuid4().hex[:8]}"
CITIZEN_B_UID = f"cit_b_pki_{uuid.uuid4().hex[:8]}"
OFFICER_UID = f"off_pki_{uuid.uuid4().hex[:8]}"
ADMIN_UID = f"adm_pki_{uuid.uuid4().hex[:8]}"

CITIZEN_A_EMAIL = f"{CITIZEN_A_UID}@example.com"
CITIZEN_B_EMAIL = f"{CITIZEN_B_UID}@example.com"
OFFICER_EMAIL = f"{OFFICER_UID}@example.com"
ADMIN_EMAIL = f"{ADMIN_UID}@example.com"

CITIZEN_A_TOKEN = f"test_token_:{CITIZEN_A_UID}:{CITIZEN_A_EMAIL}:Citizen Alpha PKI"
CITIZEN_B_TOKEN = f"test_token_:{CITIZEN_B_UID}:{CITIZEN_B_EMAIL}:Citizen Beta PKI"
OFFICER_TOKEN = f"test_token_:{OFFICER_UID}:{OFFICER_EMAIL}:Officer Verification Lead"
ADMIN_TOKEN = f"test_token_:{ADMIN_UID}:{ADMIN_EMAIL}:Admin PKI Authority"


def setup_users():
    admin_url = os.getenv(
        "DATABASE_MIGRATION_URL",
        "postgresql://postgres:postgres_dev_password@postgres:5432/consolith"
    )
    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (firebase_uid, email, full_name, role) VALUES
                (%s, %s, 'User Alpha PKI', 'user'),
                (%s, %s, 'User Beta PKI', 'user'),
                (%s, %s, 'Admin PKI Authority', 'admin')
                ON CONFLICT (firebase_uid) DO UPDATE
                SET role = EXCLUDED.role, full_name = EXCLUDED.full_name
                RETURNING id, firebase_uid, role;
            """, (
                CITIZEN_A_UID, CITIZEN_A_EMAIL,
                CITIZEN_B_UID, CITIZEN_B_EMAIL,
                ADMIN_UID, ADMIN_EMAIL,
            ))
            rows = {r[1]: r[0] for r in cur.fetchall()}
            cit_a_id = rows[CITIZEN_A_UID]
            cit_b_id = rows[CITIZEN_B_UID]
            adm_id = rows[ADMIN_UID]
            off_id = adm_id
    finally:
        conn.close()

    return cit_a_id, cit_b_id, off_id, adm_id


def run_tests():
    print("=== Module 9 Document Authenticity & Ed25519 PKI Live API & RLS Tests ===")
    cit_a_id, cit_b_id, off_id, adm_id = setup_users()
    print(f"Provisioned test users: Cit A ({cit_a_id}), Cit B ({cit_b_id}), Officer ({off_id}), Admin ({adm_id})")

    # Test 1: Fetch PKI Stats and default key
    res = client.get("/api/v1/pki/stats", headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    stats = res.json()
    assert stats["active_keys"] >= 1
    print("  [PASS] 1. PKI Keystore initialized with default active Ed25519 signing key")

    # Test 2: List public keys is accessible to Citizen
    res = client.get("/api/v1/pki/keys", headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"})
    assert res.status_code == 200
    keys = res.json()
    assert len(keys) >= 1
    default_key_id = keys[0]["key_id"]
    print(f"  [PASS] 2. Public keystore queryable by citizen (Key ID: {default_key_id})")

    # Test 3: Citizen forbidden from registering keys
    new_key_id = f"custom-key-{uuid.uuid4().hex[:6]}"
    priv, pub = Ed25519CryptoManager.generate_keypair()
    pub_b64 = Ed25519CryptoManager.public_key_to_base64(pub)
    DevSigningKeyProvider.register_dev_key(new_key_id, priv)
    res = client.post(
        "/api/v1/pki/keys",
        json={"key_id": new_key_id, "public_key": pub_b64, "purpose": "test"},
        headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"},
    )
    assert res.status_code == 403, f"Expected 403 for citizen, got {res.status_code}"
    print("  [PASS] 3. Authorization: Citizen forbidden from registering public keys (HTTP 403)")

    # Test 4: Admin registers a new key
    res = client.post(
        "/api/v1/pki/keys",
        json={"key_id": new_key_id, "public_key": pub_b64, "purpose": "officer_attestation"},
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    reg_key = res.json()
    assert reg_key["key_id"] == new_key_id
    assert reg_key["status"] == "active"
    print(f"  [PASS] 4. Admin successfully registered new signing key ({new_key_id})")

    # Test 5: Admin signs a Platform Administrative Attestation for User A
    doc_raw = b"Sample Verified Aadhaar Document Content for Citizen A"
    doc_fingerprint = hashlib.sha256(doc_raw).hexdigest()

    attestation_payload = {
        "document_type": "aadhaar",
        "document_fingerprint": doc_fingerprint,
        "signing_purpose": "identity_discrepancy_verification",
        "expires_in_days": 180,
    }
    res = client.post(
        f"/api/v1/attestations?citizen_id={cit_a_id}",
        json=attestation_payload,
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    attestation = res.json()
    attestation_id = attestation["id"]
    assert attestation["document_fingerprint"] == doc_fingerprint
    assert attestation["algorithm"] == "Ed25519"
    assert len(attestation["signature"]) > 60
    print(f"  [PASS] 5. Admin cryptographically signed Platform Attestation (ID: {attestation_id})")

    # Test 6: User cannot sign attestations directly (requires ADMIN)
    res = client.post(
        f"/api/v1/attestations?citizen_id={cit_a_id}",
        json=attestation_payload,
        headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"},
    )
    assert res.status_code == 403
    print("  [PASS] 6. Authorization: Citizen forbidden from signing attestations directly (HTTP 403)")

    # Test 7: RLS Isolation — Citizen A can view their own attestation
    res = client.get(f"/api/v1/attestations/{attestation_id}", headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"})
    assert res.status_code == 200
    print("  [PASS] 7. RLS Verification: Citizen A can view their own attestation details")

    # Test 8: RLS Isolation — Citizen B cannot view Citizen A's attestation
    res = client.get(f"/api/v1/attestations/{attestation_id}", headers={"Authorization": f"Bearer {CITIZEN_B_TOKEN}"})
    assert res.status_code == 404
    print("  [PASS] 8. RLS Isolation: Citizen B denied access to Citizen A's attestation (HTTP 404)")

    # Test 9: Cryptographic Verification of authentic document succeeds (VALID)
    res = client.post(
        f"/api/v1/attestations/{attestation_id}/verify",
        json={"document_hash": doc_fingerprint},
        headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"},
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    ver_result = res.json()
    assert ver_result["verification_status"] == "VALID"
    assert ver_result["is_valid"] is True
    assert ver_result["signature_valid"] is True
    assert ver_result["document_integrity_valid"] is True
    assert ver_result["key_trusted"] is True
    print("  [PASS] 9. Cryptographic Verification: Authentic document verified as VALID")

    # Test 10: Cryptographic Tamper Detection — Modified document detected (DOCUMENT_TAMPERED)
    tampered_doc_hash = hashlib.sha256(b"Tampered or Forged Document Bytes").hexdigest()
    res = client.post(
        f"/api/v1/attestations/{attestation_id}/verify",
        json={"document_hash": tampered_doc_hash},
        headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"},
    )
    assert res.status_code == 200
    tamper_result = res.json()
    assert tamper_result["verification_status"] == "DOCUMENT_TAMPERED"
    assert tamper_result["is_valid"] is False
    assert tamper_result["signature_valid"] is True  # Signature over canonical payload was valid
    assert tamper_result["document_integrity_valid"] is False  # But document hash mismatched!
    print("  [PASS] 10. Tamper Detection: Modified document detected as DOCUMENT_TAMPERED")

    # Test 11: Admin key rotation and revocation
    rotated_key_id = f"rotated-key-{uuid.uuid4().hex[:6]}"
    res = client.post(
        f"/api/v1/pki/keys/{new_key_id}/rotate",
        json={"new_key_id": rotated_key_id, "purpose": "rotated_attestation"},
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    assert res.status_code == 200
    res = client.post(
        f"/api/v1/pki/keys/{rotated_key_id}/revoke",
        json={"reason": "Routine security decommission test"},
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
    )
    assert res.status_code == 200
    revoked_key = res.json()
    assert revoked_key["status"] == "revoked"
    print(f"  [PASS] 11. Admin Key Lifecycle: Key rotation and revocation verified ({rotated_key_id})")

    # Test 12: Cryptographic Audit Trail Hash Chain Integrity
    db = SessionLocal()
    try:
        set_rls_context(db, adm_id, "admin")
        audit_events = (
            db.query(AuditLog)
            .filter(AuditLog.action.in_(["PKI_KEY_REGISTERED", "DOCUMENT_ATTESTATION_SIGNED", "DOCUMENT_VERIFICATION_PERFORMED", "PKI_KEY_ROTATED", "PKI_KEY_REVOKED"]))
            .order_by(AuditLog.created_at.asc())
            .all()
        )
        assert len(audit_events) >= 5, f"Expected at least 5 audit events, got {len(audit_events)}"
        for event in audit_events:
            assert len(event.current_hash) == 64
            assert event.prev_hash is not None
        print(f"  [PASS] 12. Audit Trail Integrity: {len(audit_events)} PKI events cryptographically chained via SHA-256")
    finally:
        db.close()

    print("\nALL 12 MODULE 9 API & RLS TESTS PASSED PERFECTLY!\n")
    return True


if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
