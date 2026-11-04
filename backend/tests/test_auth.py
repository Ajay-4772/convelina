import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.user import User

client = TestClient(app)

# Test Fixture IDs
TEST_CITIZEN_UID = f"test_cit_{uuid.uuid4().hex[:8]}"
TEST_OFFICER_UID = f"test_off_{uuid.uuid4().hex[:8]}"
TEST_ADMIN_UID = f"test_adm_{uuid.uuid4().hex[:8]}"

CITIZEN_TOKEN = f"test_token_:{TEST_CITIZEN_UID}:citizen@example.test:Test Citizen"
OFFICER_TOKEN = f"test_token_:{TEST_OFFICER_UID}:officer@example.test:Test Officer"
ADMIN_TOKEN = f"test_token_:{TEST_ADMIN_UID}:admin@example.test:Test Admin"

@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    # Enable test mode token verifier for isolated unit tests
    from app.config import settings
    prev = settings.TEST_MODE_ALLOW_SIMULATED_TOKENS
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = True
    yield
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = prev

def test_missing_auth_header():
    """Unauthenticated request must return 401 Unauthorized."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "Authorization header is missing" in resp.json()["detail"]

def test_malformed_auth_header():
    """Malformed header must return 401."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "InvalidFormatToken"})
    assert resp.status_code == 401
    assert "Invalid Authorization header format" in resp.json()["detail"]

def test_expired_token():
    """Expired token must return 401."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test_token_expired"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()

def test_invalid_token():
    """Invalid token must return 401."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer test_token_invalid"})
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()

def test_user_provisioning_default_role():
    """New user must be provisioned with role 'user' regardless of client input."""
    payload = {
        "full_name": "Ajay Raman",
        "role": "admin" # Client attempts to inject role
    }
    resp = client.post(
        "/api/v1/auth/provision",
        json=payload,
        headers={"Authorization": f"Bearer {CITIZEN_TOKEN}"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["firebase_uid"] == TEST_CITIZEN_UID
    assert data["full_name"] == "Ajay Raman"
    assert data["role"] in ["user", "citizen"] # Strict enforcement: role is user, NOT admin!

def test_idempotent_provisioning():
    """Subsequent provisioning updates name without creating duplicates or altering role."""
    payload = {"full_name": "Ajay Raman Updated"}
    resp = client.post(
        "/api/v1/auth/provision",
        json=payload,
        headers={"Authorization": f"Bearer {CITIZEN_TOKEN}"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Ajay Raman Updated"
    assert data["role"] in ["user", "citizen"]

def test_get_me_citizen():
    """Provisioned citizen can fetch their profile."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {CITIZEN_TOKEN}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["firebase_uid"] == TEST_CITIZEN_UID
    assert data["role"] in ["user", "citizen"]

def test_user_access_control():
    """User can access user endpoints, but receives 403 Forbidden on admin endpoints."""
    # 1. User endpoint -> 200
    resp = client.get("/api/v1/auth/user-only", headers={"Authorization": f"Bearer {CITIZEN_TOKEN}"})
    assert resp.status_code == 200
    assert resp.json()["role"] in ["user", "citizen"]

    # 2. Legacy alias endpoint -> 200
    resp = client.get("/api/v1/auth/citizen-only", headers={"Authorization": f"Bearer {CITIZEN_TOKEN}"})
    assert resp.status_code == 200

    # 3. Admin endpoint -> 403 Forbidden
    resp = client.get("/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {CITIZEN_TOKEN}"})
    assert resp.status_code == 403


def test_admin_access_control():
    """Admin can access admin endpoint."""
    # Provision admin in DB
    client.post(
        "/api/v1/auth/provision",
        json={"full_name": "Admin Verma"},
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
    )
    # Set role to admin directly in DB (via authorized admin context)
    db = SessionLocal()
    db.execute(text("SET LOCAL app.current_user_role = 'admin';"))
    db.execute(text("UPDATE users SET role = 'admin' WHERE firebase_uid = :uid;"), {"uid": TEST_ADMIN_UID})
    db.commit()
    db.close()

    # Admin accesses admin endpoint -> 200
    resp = client.get("/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert resp.status_code == 200
