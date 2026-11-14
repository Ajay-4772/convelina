import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.main import app
from app.core.database import get_db, set_rls_context, SessionLocal
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.checklist import CitizenChecklistItem
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.assistant import AssistantConversation, AssistantMessage
from app.config import settings

client = TestClient(app)

@pytest.fixture
def test_users(db_session: Session):
    """Creates two distinct synthetic users for RLS persistence testing."""
    set_rls_context(db_session, None, "admin")
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    user_a = User(
        id=user_a_id,
        firebase_uid=f"fb_pers_a_{user_a_id.hex[:8]}",
        email=f"pers.a.{user_a_id.hex[:6]}@example.com",
        full_name="Persistent Citizen A",
        role="user",
    )
    user_b = User(
        id=user_b_id,
        firebase_uid=f"fb_pers_b_{user_b_id.hex[:8]}",
        email=f"pers.b.{user_b_id.hex[:6]}@example.com",
        full_name="Persistent Citizen B",
        role="user",
    )

    db_session.add(user_a)
    db_session.add(user_b)
    db_session.commit()

    return user_a, user_b


@pytest.fixture
def db_session():
    """Provides a database session for test execution."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_runtime_health_diagnostics():
    """
    Test 1: Health endpoint returns comprehensive separate service statuses
    FastAPI, PostgreSQL, Migrations, Qdrant, OCR Engine, Storage, Firebase, Gemini.
    """
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "healthy"
    services = data["services"]

    # Individual service checks
    assert services["fastapi"]["status"] == "up"
    assert services["postgres"]["status"] == "up"
    assert services["postgres"]["role"] == "consolith_app"
    assert services["database_migrations"]["status"] == "up"
    assert services["database_migrations"]["applied_count"] >= 22
    assert services["database_migrations"]["latest_applied"] in (
        "021_citizen_checklist_progress.sql",
        "022_security_hardening.sql",
        "023_assistant_message_pagination_index.sql",
    )
    assert services["qdrant"]["status"] == "up"
    assert services["ocr_engine"]["status"] == "up"
    assert services["storage"]["status"] == "up"
    assert services["firebase_auth"]["status"] in ("configured", "unconfigured")
    assert services["gemini"]["status"] == "disabled"


def test_checklist_persistence_and_isolation(test_users, db_session):
    """
    Test 2: Citizen checklist persistence & RLS isolation
    - Citizen A saves checklist progress in PostgreSQL
    - Progress survives reload and query
    - Citizen B cannot see or overwrite Citizen A's progress
    - Validation prevents invalid procedure or item IDs
    """
    user_a, user_b = test_users
    proc_id = "aadhaar_name_update"
    item_id = "REQ_AAD_NAME_INITIAL_EXPANSION_04"

    # 1. Citizen A: initial empty progress
    app.dependency_overrides[get_current_user] = lambda: user_a
    try:
        resp = client.get(f"/api/v1/repository/checklists/{proc_id}/progress")
        assert resp.status_code == 200
        prog_a = resp.json()
        assert prog_a["procedure_id"] == proc_id
        assert prog_a["completed_items"] == []

        # 2. Citizen A: completes an item
        put_resp = client.put(
            f"/api/v1/repository/checklists/{proc_id}/progress",
            json={"item_id": item_id, "is_completed": True},
        )
        assert put_resp.status_code == 200
        updated_a = put_resp.json()
        assert item_id in updated_a["completed_items"]
        assert updated_a["items_progress"][item_id] is True

        # 3. Simulate browser refresh: GET progress again
        refresh_resp = client.get(f"/api/v1/repository/checklists/{proc_id}/progress")
        assert refresh_resp.status_code == 200
        refreshed_a = refresh_resp.json()
        assert item_id in refreshed_a["completed_items"]

        # 4. Input validation: invalid item ID rejected
        bad_item_resp = client.put(
            f"/api/v1/repository/checklists/{proc_id}/progress",
            json={"item_id": "NON_EXISTENT_REQ_999", "is_completed": True},
        )
        assert bad_item_resp.status_code == 400
        assert "not a valid requirement" in bad_item_resp.json()["detail"]

        # 5. Citizen B: RLS isolation check
        app.dependency_overrides[get_current_user] = lambda: user_b
        resp_b = client.get(f"/api/v1/repository/checklists/{proc_id}/progress")
        assert resp_b.status_code == 200
        prog_b = resp_b.json()
        # Citizen B sees NO completed items (isolated from Citizen A)
        assert item_id not in prog_b["completed_items"]
        assert prog_b["completed_items"] == []

        # Direct DB query verification
        set_rls_context(db_session, user_b.id, user_b.role)
        b_records = db_session.query(CitizenChecklistItem).filter(
            CitizenChecklistItem.procedure_id == proc_id
        ).all()
        assert len(b_records) == 0, "Citizen B under RLS must see 0 checklist items from Citizen A"

    finally:
        app.dependency_overrides.clear()


def test_document_and_conflict_persistence(test_users, db_session):
    """
    Test 3: Document and conflict records persist in PostgreSQL under RLS
    """
    user_a, user_b = test_users
    set_rls_context(db_session, user_a.id, "user")

    # Insert document for Citizen A
    doc_a = Document(
        id=uuid.uuid4(),
        user_id=user_a.id,
        document_type="aadhaar",
        file_path="/storage/docs/pers_aadhaar.pdf",
        file_hash="hash_pers_aadhaar_123",
        masked_id="XXXX-XXXX-9999",
        extracted_fields={"name": "Aarav Sharma", "dob": "1990-05-15"},
        ocr_status="completed",
        is_user_confirmed=True,
        confirmed_fields={"name": "Aarav Sharma", "dob": "1990-05-15"},
    )
    db_session.add(doc_a)

    # Insert conflict for Citizen A
    conflict_a = Conflict(
        id=uuid.uuid4(),
        user_id=user_a.id,
        field_name="name",
        conflict_type="genuine-mismatch",
        severity="high",
        status="detected",
        value_a="Aarav Sharma",
        value_b="A. Sharma",
        description="Name discrepancy between Aadhaar and PAN",
        doc_a_id=doc_a.id,
        doc_b_id=doc_a.id,
    )
    db_session.add(conflict_a)
    db_session.commit()

    # Query as Citizen A via API
    app.dependency_overrides[get_current_user] = lambda: user_a
    try:
        # Documents endpoint
        doc_resp = client.get("/api/v1/documents/")
        assert doc_resp.status_code == 200
        docs_data = doc_resp.json()
        doc_ids = [d["id"] for d in docs_data["documents"]]
        assert str(doc_a.id) in doc_ids

        # Conflicts endpoint
        conf_resp = client.get("/api/v1/conflicts/")
        assert conf_resp.status_code == 200
        conf_data = conf_resp.json()
        conf_ids = [c["id"] for c in conf_data["conflicts"]]
        assert str(conflict_a.id) in conf_ids

        # Query as Citizen B via API: must be isolated
        app.dependency_overrides[get_current_user] = lambda: user_b
        doc_resp_b = client.get("/api/v1/documents/")
        assert str(doc_a.id) not in [d["id"] for d in doc_resp_b.json()["documents"]]

        conf_resp_b = client.get("/api/v1/conflicts/")
        assert str(conflict_a.id) not in [c["id"] for c in conf_resp_b.json()["conflicts"]]

    finally:
        app.dependency_overrides.clear()


def test_conversation_persistence(test_users, db_session):
    """
    Test 4: Assistant conversations and messages persist in PostgreSQL
    """
    user_a, user_b = test_users
    set_rls_context(db_session, user_a.id, "user")

    # Create conversation for Citizen A
    conv_a = AssistantConversation(
        id=uuid.uuid4(),
        user_id=user_a.id,
        title="PAN Name Correction Help",
    )
    db_session.add(conv_a)
    db_session.flush()

    msg_a = AssistantMessage(
        id=uuid.uuid4(),
        conversation_id=conv_a.id,
        user_id=user_a.id,
        role="user",
        content="How do I change my name in PAN?",
    )
    db_session.add(msg_a)
    db_session.commit()

    # Query as Citizen A
    app.dependency_overrides[get_current_user] = lambda: user_a
    try:
        resp = client.get(f"/api/v1/assistant/conversations/{conv_a.id}/messages")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "How do I change my name in PAN?"

        # Citizen B cannot access Citizen A's conversation
        app.dependency_overrides[get_current_user] = lambda: user_b
        resp_b = client.get(f"/api/v1/assistant/conversations/{conv_a.id}/messages")
        assert resp_b.status_code == 404

    finally:
        app.dependency_overrides.clear()

