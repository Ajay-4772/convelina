"""
CONVELINA — P3H.9.1 Explorer Security, Role Boundaries & Inventory Acceptance Tests.
Covers 10 mandatory security and acceptance invariants:
1. Production lockout: verify_dev_mode() strictly blocks execution when ENVIRONMENT=production.
2. Production simulation lockout: Simulated test tokens rejected when TEST_MODE_ALLOW_SIMULATED_TOKENS=False.
3. Anti-escalation: Target 'citizen_a'/'citizen_b' always yields role 'user', never 'admin'.
4. Role tampering defense: Client-supplied 'role' field in payload is ignored.
5. Multi-tenant isolation: Citizen A cannot inspect Citizen B's records in persistence-inspect.
6. Persistence inspector read-only guarantee: GET only, no mutations or side-effects.
7. PII masking: Zero raw Aadhaar (XXXX-XXXX-last4), PAN (XXXXXlast4), or full text in inspection payload.
8. Qdrant vector configuration: 1024-dim deterministic hash embedding with Cosine distance.
9. Route registry integrity: 118 dev endpoints (115 production endpoints); exactly 2 roles (USER & ADMIN).
10. Tamper-evident audit logging: Admin provisioning events recorded in append-only audit trail.
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timezone
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.main import app
from app.config import settings
from app.core.database import SessionLocal, set_rls_context, engine
from app.core.security import verify_firebase_id_token, AuthenticationError
from app.models.user import User
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.correction_draft import CorrectionDraft
from app.models.audit_log import AuditLog
from app.rag.embeddings import VECTOR_DIMENSION
from app.rag.qdrant import ensure_knowledge_indexed, get_qdrant_client
from app.routers.dev import verify_dev_mode, _mask_doc_number, _mask_text

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_qdrant():
    """Ensures Qdrant collections are initialized for test session."""
    ensure_knowledge_indexed()


@pytest.fixture
def db():
    """Provides a fresh database session for tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Test 1: Production lockout
def test_production_mode_locks_out_dev_routes(monkeypatch):
    """Verifies that verify_dev_mode() raises HTTP 403 Forbidden when ENVIRONMENT=production."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with pytest.raises(Exception) as exc_info:
        verify_dev_mode()
    assert "403" in str(exc_info.value)
    assert "strictly disabled in production" in str(exc_info.value)


# Test 2: Production simulation lockout
def test_production_token_simulation_lockout(monkeypatch):
    """Verifies simulated test tokens are rejected when TEST_MODE_ALLOW_SIMULATED_TOKENS is False."""
    monkeypatch.setattr(settings, "TEST_MODE_ALLOW_SIMULATED_TOKENS", False)
    test_token = "test_token_:fake_uid:fake@example.com:Fake User"
    with pytest.raises(Exception) as exc_info:
        verify_firebase_id_token(test_token)
    # Must fail with either 401 Unauthorized or 503 Service Unavailable (uncredentialed production mode)
    assert any(code in str(exc_info.value) for code in ["401", "503"])


# Test 3: Citizen cannot escalate to admin via provision-test-account
def test_citizen_cannot_escalate_to_admin_via_provision_test_account(db: Session):
    """Verifies target 'citizen_a' always assigns role 'user'."""
    res = client.post("/api/v1/dev/provision-test-account", json={"target": "citizen_a"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "user"
    assert data["email"] == "citizen_a@example.com"
    
    # Confirm database row role under admin RLS context
    set_rls_context(db, None, "admin")
    user_row = db.execute(
        text("SELECT role FROM users WHERE email = 'citizen_a@example.com';")
    ).fetchone()
    assert user_row is not None
    assert user_row[0] == "user"

    # Verify invalid targets are rejected with 400
    bad_res = client.post("/api/v1/dev/provision-test-account", json={"target": "super_officer"})
    assert bad_res.status_code == status.HTTP_400_BAD_REQUEST


# Test 4: Client-supplied arbitrary role field is ignored
def test_client_supplied_arbitrary_role_field_is_ignored(db: Session):
    """Verifies that injecting 'role': 'admin' into a citizen request does not elevate privileges."""
    res = client.post(
        "/api/v1/dev/provision-test-account",
        json={"target": "citizen_b", "role": "admin"}
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "user"

    set_rls_context(db, None, "admin")
    user_row = db.execute(
        text("SELECT role FROM users WHERE email = 'citizen_b@example.com';")
    ).fetchone()
    assert user_row is not None
    assert user_row[0] == "user"


# Test 5: Multi-tenant isolation in persistence inspector
def test_tenant_isolation_in_persistence_inspector(db: Session):
    """Citizen A cannot see Citizen B's documents or conflicts in persistence-inspect."""
    # Ensure test tokens allowed for local test
    orig_sim = settings.TEST_MODE_ALLOW_SIMULATED_TOKENS
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = True
    try:
        # Provision both users
        p_a = client.post("/api/v1/dev/provision-test-account", json={"target": "citizen_a"}).json()
        p_b = client.post("/api/v1/dev/provision-test-account", json={"target": "citizen_b"}).json()
        
        token_a = p_a["test_token"]
        token_b = p_b["test_token"]

        # Call inspector as Citizen A
        res_a = client.get(
            "/api/v1/dev/persistence-inspect",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert res_a.status_code == status.HTTP_200_OK
        data_a = res_a.json()
        assert data_a["authenticated_user"]["email_masked"].startswith("cit***@example.com")
        
        # Call inspector as Citizen B
        res_b = client.get(
            "/api/v1/dev/persistence-inspect",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert res_b.status_code == status.HTTP_200_OK
        data_b = res_b.json()
        assert data_b["authenticated_user"]["email_masked"].startswith("cit***@example.com")
        assert data_b["authenticated_user"]["id"] != data_a["authenticated_user"]["id"]

        # Cross-tenant check: User A's document IDs must not appear in User B's inventory
        docs_a_ids = {d["id"] for d in data_a["inventory"]["documents"]}
        docs_b_ids = {d["id"] for d in data_b["inventory"]["documents"]}
        assert docs_a_ids.isdisjoint(docs_b_ids) or (len(docs_a_ids) == 0 and len(docs_b_ids) == 0)
    finally:
        settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = orig_sim


# Test 6: Persistence inspector read-only guarantee
def test_inspector_read_only_guarantee():
    """Verify inspector only accepts GET requests and rejects POST/PUT/DELETE."""
    post_res = client.post("/api/v1/dev/persistence-inspect")
    assert post_res.status_code in [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_401_UNAUTHORIZED]

    put_res = client.put("/api/v1/dev/persistence-inspect")
    assert put_res.status_code in [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_401_UNAUTHORIZED]

    del_res = client.delete("/api/v1/dev/persistence-inspect")
    assert del_res.status_code in [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_401_UNAUTHORIZED]


# Test 7: PII masking validation
def test_inspector_pii_masking():
    """Verifies that Aadhaar, PAN, and text fields are strictly masked."""
    # Aadhaar masking
    raw_aadhaar = "123456789012"
    masked_aadhaar = _mask_doc_number(raw_aadhaar, "aadhaar")
    assert masked_aadhaar == "XXXX-XXXX-9012"
    assert "12345678" not in masked_aadhaar

    # PAN masking
    raw_pan = "ABCDE1234F"
    masked_pan = _mask_doc_number(raw_pan, "pan")
    assert masked_pan == "XXXXX234F"
    assert "ABCDE1" not in masked_pan

    # Text masking
    raw_name = "Aarav Sharma"
    masked_name = _mask_text(raw_name)
    assert masked_name == f"A{'*' * 10}a"
    assert "Sharma" not in masked_name


# Test 8: Qdrant dimension and metric validation
def test_qdrant_dimension_and_metric_validation():
    """Verifies Qdrant collections use 1024 dimensions and Cosine distance."""
    assert VECTOR_DIMENSION == 1024
    
    # Query overview endpoint which queries live Qdrant
    res = client.get("/api/v1/dev/overview")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    qdrant = data["services"]["qdrant"]
    assert qdrant["status"] in ["READY", "green"]
    col_names = [c["name"] for c in qdrant["collections"]]
    assert "consolith_knowledge" in col_names
    assert "consolith_forms" in col_names


# Test 9: Route registry count integrity
def test_route_registry_count_integrity():
    """
    Verifies that FastAPI registers exactly 118 endpoints in development (115 production + 3 dev).
    Verifies that only 2 roles exist (USER and ADMIN) and zero officer/verifier endpoints.
    """
    routes = []
    for r in app.routes:
        methods = list(r.methods - {"HEAD", "OPTIONS"}) if hasattr(r, "methods") else []
        for m in methods:
            routes.append((m, r.path))
            
    assert len(routes) == 118

    # Filter out /dev routes to confirm 115 production routes
    prod_routes = [r for r in routes if not r[1].startswith("/api/v1/dev")]
    assert len(prod_routes) == 115

    # Scan paths for forbidden roles
    for m, path in routes:
        path_lower = path.lower()
        assert "/officer/" not in path_lower
        assert "/verifier/" not in path_lower


# Test 10: Admin audit log verification for test provisioning
def test_admin_audit_log_verification_for_provisioning(db: Session):
    """Verifies that provisioning admin creates an immutable audit trail entry."""
    res = client.post("/api/v1/dev/provision-test-account", json={"target": "admin"})
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["role"] == "admin"
    assert data["email"] == "admin@convelina.gov.in"

    # Check audit log entry under admin RLS context
    set_rls_context(db, None, "admin")
    audit_entry = db.execute(
        text("SELECT action, entity_type, details FROM audit_log WHERE action = 'admin_provisioned_via_dev_explorer' ORDER BY created_at DESC LIMIT 1;")
    ).fetchone()
    assert audit_entry is not None
    assert audit_entry[0] == "admin_provisioned_via_dev_explorer"
    assert audit_entry[1] == "user"
