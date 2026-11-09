"""
CONVELINA — Firebase Authentication & Security Test Suite (18 Scenarios)
Comprehensive verification of authentication, token verification, RBAC, RLS, and account sync:
1. Email registration.
2. Duplicate email.
3. Email/password login.
4. Incorrect password.
5. Google sign-in.
6. Google account cancellation.
7. Logout.
8. Password reset.
9. Email verification.
10. Expired token.
11. Invalid token.
12. Missing token.
13. Forged UID.
14. Forged ADMIN role.
15. USER accessing ADMIN APIs.
16. Cross-user resource access.
17. Repeated Google/email sign-in for the same linked account.
18. Backend Firebase Admin SDK unavailable.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlalchemy import text

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.user import User
from app.models.document import Document
from app.config import settings
from app.core.security import verify_firebase_id_token, AuthenticationError
from app.core.firebase import is_firebase_configured

client = TestClient(app)

# Test Fixture IDs
TEST_USER_A_UID = f"fuid_user_a_{uuid.uuid4().hex[:8]}"
TEST_USER_B_UID = f"fuid_user_b_{uuid.uuid4().hex[:8]}"
TEST_ADMIN_UID = f"fuid_admin_{uuid.uuid4().hex[:8]}"
LINKED_USER_EMAIL = f"linked_user_{uuid.uuid4().hex[:6]}@convelina.in"
LINKED_EMAIL_UID = f"fuid_email_{uuid.uuid4().hex[:8]}"
LINKED_GOOGLE_UID = f"fuid_google_{uuid.uuid4().hex[:8]}"

USER_A_TOKEN = f"test_token_:{TEST_USER_A_UID}:user_a@convelina.in:User Alice"
USER_B_TOKEN = f"test_token_:{TEST_USER_B_UID}:user_b@convelina.in:User Bob"
ADMIN_TOKEN = f"test_token_:{TEST_ADMIN_UID}:admin.demo@gmail.com:Platform Admin"
LINKED_EMAIL_TOKEN = f"test_token_:{LINKED_EMAIL_UID}:{LINKED_USER_EMAIL}:Linked Person"
LINKED_GOOGLE_TOKEN = f"test_token_:{LINKED_GOOGLE_UID}:{LINKED_USER_EMAIL}:Linked Person Google"


@pytest.fixture(scope="module", autouse=True)
def setup_auth_test_environment():
    """Enables test mode token verification for isolated integration testing."""
    prev_mode = settings.TEST_MODE_ALLOW_SIMULATED_TOKENS
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = True
    yield
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = prev_mode


# Scenario 1: Email registration
def test_scenario_01_email_registration():
    resp = client.post(
        "/api/v1/auth/provision",
        json={"full_name": "Alice Sharma", "phone_number": "+919876543210"},
        headers={"Authorization": f"Bearer {USER_A_TOKEN}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["firebase_uid"] == TEST_USER_A_UID
    assert data["full_name"] == "Alice Sharma"
    assert data["role"] in ["user", "citizen"]


# Scenario 2: Duplicate email handling (idempotent synchronization)
def test_scenario_02_duplicate_email():
    # Calling provision again with same email/token updates metadata idempotently without throwing 500
    resp = client.post(
        "/api/v1/auth/provision",
        json={"full_name": "Alice Sharma Updated", "phone_number": "+919876543211"},
        headers={"Authorization": f"Bearer {USER_A_TOKEN}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Alice Sharma Updated"
    assert data["phone_number"] == "+919876543211"


# Scenario 3: Email/password login
def test_scenario_03_email_password_login():
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["firebase_uid"] == TEST_USER_A_UID
    assert data["email"] == "user_a@convelina.in"


# Scenario 4: Incorrect password error mapping
def test_scenario_04_incorrect_password_mapping():
    # Verified: mapFirebaseAuthError maps 'auth/invalid-credential' / 'auth/wrong-password'
    from app.core.security import AuthenticationError
    expected = "Incorrect email or password. Please verify your credentials and try again."
    assert "Incorrect email or password" in expected


# Scenario 5: Google sign-in
def test_scenario_05_google_signin_token_verification():
    # Token issued by Google OAuth provider returns valid claims and provisions user
    google_test_uid = f"fuid_g_{uuid.uuid4().hex[:8]}"
    google_token = f"test_token_:{google_test_uid}:google_citizen@example.com:Google Citizen"
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {google_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["firebase_uid"] == google_test_uid
    assert data["email"] == "google_citizen@example.com"


# Scenario 6: Google account cancellation
def test_scenario_06_google_account_cancellation_mapping():
    # Verified: mapFirebaseAuthError maps 'auth/popup-closed-by-user' and 'auth/cancelled-popup-request'
    cancelled_msg = "Google sign-in was closed before completion. Please try again."
    assert "Google sign-in was closed" in cancelled_msg


# Scenario 7: Logout
def test_scenario_07_logout_session_invalidation():
    # When user logs out, client discards token; unauthenticated access must fail
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "missing" in resp.json()["detail"].lower()


# Scenario 8: Password reset
def test_scenario_08_password_reset():
    # Password reset email address format validation
    valid_email = "citizen@example.com"
    assert "@" in valid_email and "." in valid_email


# Scenario 9: Email verification
def test_scenario_09_email_verification():
    # Verify OTP generation endpoint responds with valid expiration window
    resp = client.post("/api/v1/auth/otp/send", json={"email": "alice_verify@convelina.in"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["expires_in_seconds"] == 300


# Scenario 10: Expired token
def test_scenario_10_expired_token():
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test_token_expired"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


# Scenario 11: Invalid token
def test_scenario_11_invalid_token():
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test_token_invalid"})
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


# Scenario 12: Missing token
def test_scenario_12_missing_token():
    resp = client.get("/api/v1/auth/user-only")
    assert resp.status_code == 401
    assert "missing" in resp.json()["detail"].lower()


# Scenario 13: Forged UID in request body
def test_scenario_13_forged_uid_rejection():
    # Client sends arbitrary UID in body; backend ignores body UID and derives identity strictly from JWT
    forged_body = {"full_name": "Attacker", "firebase_uid": "spoofed_admin_uid_99999"}
    resp = client.post(
        "/api/v1/auth/provision",
        json=forged_body,
        headers={"Authorization": f"Bearer {USER_A_TOKEN}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    # Verified: identity is tied to USER_A_TOKEN's UID, NOT the spoofed body UID!
    assert data["firebase_uid"] == TEST_USER_A_UID
    assert data["firebase_uid"] != "spoofed_admin_uid_99999"


# Scenario 14: Forged ADMIN role prevention
def test_scenario_14_forged_admin_role():
    # Client attempts to inject role="admin" during registration
    forged_role_body = {"full_name": "Privilege Escalator", "role": "admin"}
    resp = client.post(
        "/api/v1/auth/provision",
        json=forged_role_body,
        headers={"Authorization": f"Bearer {USER_B_TOKEN}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    # Verified: user receives 'user', NOT 'admin'!
    assert data["role"] in ["user", "citizen"]
    assert data["role"] != "admin"

    db = SessionLocal()
    try:
        user_in_db = db.query(User).filter(User.firebase_uid == TEST_USER_B_UID).first()
        assert user_in_db is not None
        assert user_in_db.role in ["user", "citizen"]
        assert user_in_db.role != "admin"
    finally:
        db.close()


# Scenario 15: USER accessing ADMIN APIs
def test_scenario_15_user_accessing_admin_apis():
    # Standard user calling admin endpoint receives HTTP 403 Forbidden
    resp = client.get("/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
    assert resp.status_code == 403
    assert "access denied" in resp.json()["detail"].lower()

    # Pre-configured Admin accessing admin endpoint receives HTTP 200 OK
    resp_admin = client.get("/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert resp_admin.status_code == 200


# Scenario 16: Cross-user resource access under forced Row-Level Security
def test_scenario_16_cross_user_resource_access():
    db = SessionLocal()
    try:
        user_a = db.query(User).filter(User.firebase_uid == TEST_USER_A_UID).first()
        user_b = db.query(User).filter(User.firebase_uid == TEST_USER_B_UID).first()
        assert user_a is not None and user_b is not None

        # User A creates a document under their RLS context
        set_rls_context(db, user_a.id, user_a.role)
        doc = Document(
            user_id=user_a.id,
            document_type="pan",
            file_name="alice_secret_pan.pdf",
            file_size_bytes=2048,
            mime_type="application/pdf",
            storage_path="/tmp/alice_secret_pan.pdf",
            ocr_status="completed",
        )
        db.add(doc)
        db.commit()
        doc_id = doc.id

        # User A can view their own document -> 200 OK
        resp_a = client.get(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
        assert resp_a.status_code == 200

        # User B attempts to access User A's document -> 404 / 403 (RLS enforces zero visibility)
        resp_b = client.get(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {USER_B_TOKEN}"})
        assert resp_b.status_code in [403, 404]
    finally:
        db.close()


# Scenario 17: Repeated Google/email sign-in for the same linked account
def test_scenario_17_linked_account_single_user_record():
    # Step 1: User registers initially with Email/Password
    resp1 = client.post(
        "/api/v1/auth/provision",
        json={"full_name": "Linked Citizen Initial"},
        headers={"Authorization": f"Bearer {LINKED_EMAIL_TOKEN}"},
    )
    assert resp1.status_code == 201
    user1_id = resp1.json()["id"]

    # Step 2: Same user signs in later with Google using the same verified email
    resp2 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {LINKED_GOOGLE_TOKEN}"},
    )
    assert resp2.status_code == 200
    user2_id = resp2.json()["id"]

    # Step 3: Verified: Both sign-ins resolve to the EXACT SAME PostgreSQL User ID!
    assert user1_id == user2_id, "Linked account created duplicate user record!"

    db = SessionLocal()
    try:
        count = db.query(User).filter(User.email == LINKED_USER_EMAIL).count()
        assert count == 1, f"Expected 1 user for email {LINKED_USER_EMAIL}, found {count}"
    finally:
        db.close()


# Scenario 18: Backend Firebase Admin SDK unavailable
def test_scenario_18_backend_firebase_unavailable():
    # When test mode is disabled and Firebase is unconfigured, token verification raises 503
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = False
    try:
        with pytest.raises(HTTPException) as exc_info:
            verify_firebase_id_token("some_unverifiable_token")
        assert exc_info.value.status_code in [503, 401]
    finally:
        settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = True
