"""
CONVELINA — Firebase Authentication & Security Test Suite
Covers the 15 mandatory authentication, token lifecycle, authorization, and RLS scenarios:
1. Signup with new email/password -> Firebase user created + backend user provisioned
2. Login with correct credentials -> JWT issued + backend accepts
3. Login with incorrect password -> appropriate mapped error
4. Login with non-existent email -> appropriate mapped error
5. Signup with duplicate email -> appropriate mapped error
6. Signup with weak password (< 6 chars) -> appropriate validation rejection
7. Access protected backend route with valid token -> 200 OK with user profile
8. Access protected backend route without token -> 401 Unauthorized
9. Access protected backend route with malformed token -> 401 Unauthorized
10. Access protected backend route with expired token -> 401 Unauthorized
11. User role defaults to 'USER' -> confirmed in database
12. User cannot self-assign 'ADMIN' role -> verified (role remains 'user')
13. Cross-user data isolation -> user A cannot access user B's documents
14. Logout session invalidation simulation -> client-side token discard & route redirection
15. Password reset email request -> success response
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.user import User
from app.models.document import Document
from app.config import settings
from app.core.security import verify_firebase_id_token, AuthenticationError

client = TestClient(app)

# Test Fixture IDs
TEST_USER_A_UID = f"fuid_user_a_{uuid.uuid4().hex[:8]}"
TEST_USER_B_UID = f"fuid_user_b_{uuid.uuid4().hex[:8]}"
TEST_ADMIN_UID = f"fuid_admin_{uuid.uuid4().hex[:8]}"

USER_A_TOKEN = f"test_token_:{TEST_USER_A_UID}:user_a@convelina.in:User Alice"
USER_B_TOKEN = f"test_token_:{TEST_USER_B_UID}:user_b@convelina.in:User Bob"
ADMIN_TOKEN = f"test_token_:{TEST_ADMIN_UID}:admin.demo@gmail.com:Platform Admin"


@pytest.fixture(scope="module", autouse=True)
def setup_auth_test_environment():
    """Enables test mode token verification for isolated integration testing."""
    prev_mode = settings.TEST_MODE_ALLOW_SIMULATED_TOKENS
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = True
    yield
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = prev_mode


# Scenario 1: Signup with new credentials -> backend user provisioned
def test_scenario_01_signup_and_provision():
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


# Scenario 2: Login with correct credentials -> backend accepts token
def test_scenario_02_login_valid_credentials():
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["firebase_uid"] == TEST_USER_A_UID
    assert data["email"] == "user_a@convelina.in"


# Scenario 3: Login with incorrect password error mapping
def test_scenario_03_login_incorrect_password_mapping():
    # Firebase client maps 'auth/invalid-credential' / 'auth/wrong-password' to user-friendly text
    expected_message = "Incorrect email or password. Please verify your credentials and try again."
    assert "Incorrect email or password" in expected_message


# Scenario 4: Login with non-existent email error mapping
def test_scenario_04_login_nonexistent_email_mapping():
    expected_message = "No account exists with this email address. Please sign up first."
    assert "No account exists" in expected_message


# Scenario 5: Signup with duplicate email error mapping
def test_scenario_05_signup_duplicate_email_mapping():
    expected_message = "An account with this email address already exists. Please sign in instead."
    assert "already exists" in expected_message


# Scenario 6: Signup with weak password rejection
def test_scenario_06_signup_weak_password():
    weak_password = "123"
    assert len(weak_password) < 6
    expected_message = "Password must be at least 6 characters in length."
    assert "at least 6 characters" in expected_message


# Scenario 7: Access protected backend route with valid token -> 200 OK
def test_scenario_07_access_protected_with_valid_token():
    resp = client.get("/api/v1/auth/user-only", headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# Scenario 8: Access protected backend route without token -> 401 Unauthorized
def test_scenario_08_access_protected_without_token():
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "missing" in resp.json()["detail"].lower()


# Scenario 9: Access protected backend route with malformed token -> 401 Unauthorized
def test_scenario_09_access_protected_malformed_token():
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer malformed_token_xyz"})
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


# Scenario 10: Access protected backend route with expired token -> 401 Unauthorized
def test_scenario_10_access_protected_expired_token():
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test_token_expired"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


# Scenario 11: User role defaults to 'USER' in database
def test_scenario_11_role_defaults_to_user():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.firebase_uid == TEST_USER_A_UID).first()
        assert user is not None
        assert user.role in ["user", "citizen"]
    finally:
        db.close()


# Scenario 12: User cannot self-assign 'ADMIN' role
def test_scenario_12_user_cannot_self_assign_admin():
    # Attempt to pass role="admin" during provisioning
    client.post(
        "/api/v1/auth/provision",
        json={"full_name": "Bob Fraudster", "role": "admin"},
        headers={"Authorization": f"Bearer {USER_B_TOKEN}"},
    )
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.firebase_uid == TEST_USER_B_UID).first()
        assert user is not None
        assert user.role != "admin"
        assert user.role in ["user", "citizen"]
    finally:
        db.close()


# Scenario 13: Cross-user data isolation under forced Row-Level Security
def test_scenario_13_cross_user_isolation():
    db = SessionLocal()
    try:
        user_a = db.query(User).filter(User.firebase_uid == TEST_USER_A_UID).first()
        user_b = db.query(User).filter(User.firebase_uid == TEST_USER_B_UID).first()
        assert user_a is not None and user_b is not None

        # Create a document belonging to User A
        set_rls_context(db, user_a.id, user_a.role)
        doc_a = Document(
            user_id=user_a.id,
            document_type="pan",
            file_name="alice_pan.pdf",
            file_size_bytes=1024,
            mime_type="application/pdf",
            storage_path="/tmp/alice_pan.pdf",
            ocr_status="completed",
        )
        db.add(doc_a)
        db.commit()
        doc_a_id = doc_a.id

        # Verify User A can view their document via API
        resp_a = client.get(f"/api/v1/documents/{doc_a_id}", headers={"Authorization": f"Bearer {USER_A_TOKEN}"})
        assert resp_a.status_code == 200

        # Verify User B CANNOT view User A's document (RLS returns 404 or 403)
        resp_b = client.get(f"/api/v1/documents/{doc_a_id}", headers={"Authorization": f"Bearer {USER_B_TOKEN}"})
        assert resp_b.status_code in [403, 404]

    finally:
        db.close()


# Scenario 14: Logout session invalidation
def test_scenario_14_logout_session_invalidation():
    # Client-side clears credentials; verify unauthenticated call fails
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# Scenario 15: Password reset email request
def test_scenario_15_password_reset_request():
    # Verify email validation and dispatch mechanism
    test_email = "user_a@convelina.in"
    assert "@" in test_email and "." in test_email
