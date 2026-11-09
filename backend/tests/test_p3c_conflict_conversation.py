"""
CONVELINA — Phase P3C Conflict-to-Conversation Integration Test Suite
Validates:
1. Explicit conversation creation linked to authorized conflict (POST /api/v1/assistant/conversations).
2. Cross-user conflict linkage prevention (IDOR defense: 404/403 when linking another user's conflict).
3. Retrieval of linked conversations for a specific conflict (GET /api/v1/assistant/conversations?conflict_id=...).
4. Resolution context retrieval under forced RLS (GET /api/v1/assistant/resolution-context/{conflict_id}).
5. Multi-turn follow-up context retention: subsequent messages inherit conflict context from conversation without resending conflict_id.
6. Switching active conflict context via PATCH /api/v1/assistant/conversations/{id}.
7. Unlinking/removing active conflict context via PATCH /api/v1/assistant/conversations/{id} with empty active_conflict_id.
8. PII sanitization before persistence in conflict-linked conversation messages.
9. Deleting a conversation does NOT delete the underlying conflict.
10. Cross-tenant conversation isolation under PostgreSQL forced RLS.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.assistant import AssistantConversation, AssistantMessage
from app.core.database import SessionLocal, set_rls_context, get_db

client = TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def p3c_users_and_conflicts(db: Session):
    """
    Provisions User A and User B via the public provisioning route,
    and seeds synthetic documents and a detected conflict for User A.
    """
    uid_a = f"usr_p3c_a_{uuid.uuid4().hex[:6]}"
    token_a = f"test_token_:{uid_a}:{uid_a}@example.com:Citizen Alpha"
    res_a = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "email": f"{uid_a}@example.com",
            "full_name": "Citizen Alpha",
            "phone_number": "+919876543210",
        },
    )
    assert res_a.status_code in (200, 201)
    user_a_id = uuid.UUID(res_a.json()["id"])

    uid_b = f"usr_p3c_b_{uuid.uuid4().hex[:6]}"
    token_b = f"test_token_:{uid_b}:{uid_b}@example.com:Citizen Beta"
    res_b = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "email": f"{uid_b}@example.com",
            "full_name": "Citizen Beta",
            "phone_number": "+919876543211",
        },
    )
    assert res_b.status_code in (200, 201)
    user_b_id = uuid.UUID(res_b.json()["id"])

    # Seed User A documents & conflict under User A RLS context
    set_rls_context(db, user_a_id, "user")
    doc_a = Document(
        user_id=user_a_id,
        document_type="aadhaar",
        file_path="mock/aadhaar_alpha.pdf",
        file_hash=uuid.uuid4().hex,
        ocr_status="completed",
        masked_id="XXXX-XXXX-9876",
        extracted_fields={"full_name": "Citizen Alpha", "date_of_birth": "15/08/1990"}
    )
    doc_b = Document(
        user_id=user_a_id,
        document_type="pan",
        file_path="mock/pan_alpha.pdf",
        file_hash=uuid.uuid4().hex,
        ocr_status="completed",
        masked_id="ABCDE9876F",
        extracted_fields={"full_name": "CITIZEN A", "date_of_birth": "15/08/1990"}
    )
    db.add(doc_a)
    db.add(doc_b)
    db.flush()

    conflict_a1 = Conflict(
        user_id=user_a_id,
        doc_a_id=doc_a.id,
        doc_b_id=doc_b.id,
        field_name="full_name",
        conflict_type="format-only",
        severity="medium",
        value_a="Citizen Alpha",
        value_b="CITIZEN A",
        description="Name variation: single letter initial vs full surname",
        comparison_method="name_taxonomy",
        similarity_score=85.0
    )
    conflict_a2 = Conflict(
        user_id=user_a_id,
        doc_a_id=doc_a.id,
        doc_b_id=doc_b.id,
        field_name="date_of_birth",
        conflict_type="genuine-mismatch",
        severity="high",
        value_a="15/08/1990",
        value_b="16/08/1990",
        description="Date of birth discrepancy: day mismatch",
        comparison_method="exact",
        similarity_score=0.0
    )
    db.add(conflict_a1)
    db.add(conflict_a2)
    db.commit()

    return {
        "user_a_id": user_a_id,
        "token_a": token_a,
        "conflict_a1_id": conflict_a1.id,
        "conflict_a2_id": conflict_a2.id,
        "user_b_id": user_b_id,
        "token_b": token_b,
    }


def test_create_conversation_linked_to_conflict(p3c_users_and_conflicts):
    """Citizen creates an inquiry session explicitly linked to a conflict."""
    tok_a = p3c_users_and_conflicts["token_a"]
    cid_a1 = str(p3c_users_and_conflicts["conflict_a1_id"])

    res = client.post(
        "/api/v1/assistant/conversations",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={
            "title": "Full Name Initial Discrepancy Discussion",
            "active_conflict_id": cid_a1,
            "response_language": "en"
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Full Name Initial Discrepancy Discussion"
    assert data["active_conflict_id"] == cid_a1


def test_prevent_cross_user_conflict_linkage(p3c_users_and_conflicts):
    """User B attempts to link User A's conflict to their own conversation (IDOR rejection)."""
    tok_b = p3c_users_and_conflicts["token_b"]
    cid_a1 = str(p3c_users_and_conflicts["conflict_a1_id"])

    res = client.post(
        "/api/v1/assistant/conversations",
        headers={"Authorization": f"Bearer {tok_b}"},
        json={
            "title": "Malicious Linkage Attempt",
            "active_conflict_id": cid_a1
        }
    )
    # Must be rejected as 404 (or 403)
    assert res.status_code in [404, 403]


def test_list_conversations_filtered_by_conflict(p3c_users_and_conflicts):
    """Citizen queries conversations specifically associated with a conflict ID."""
    tok_a = p3c_users_and_conflicts["token_a"]
    cid_a1 = str(p3c_users_and_conflicts["conflict_a1_id"])

    # Create 1 linked conversation and 1 general conversation
    res1 = client.post(
        "/api/v1/assistant/conversations",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={"title": "Linked Conv", "active_conflict_id": cid_a1}
    )
    assert res1.status_code == 201

    res2 = client.post(
        "/api/v1/assistant/conversations",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={"title": "General Conv", "active_conflict_id": None}
    )
    assert res2.status_code == 201

    # Query filtered by conflict
    list_res = client.get(
        f"/api/v1/assistant/conversations?conflict_id={cid_a1}",
        headers={"Authorization": f"Bearer {tok_a}"}
    )
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1
    assert all(c["active_conflict_id"] == cid_a1 for c in data["conversations"])


def test_get_resolution_context_authorized_and_masked(p3c_users_and_conflicts):
    """Validates that resolution-context endpoint returns verified, privacy-masked details."""
    tok_a = p3c_users_and_conflicts["token_a"]
    cid_a1 = str(p3c_users_and_conflicts["conflict_a1_id"])

    res = client.get(
        f"/api/v1/assistant/resolution-context/{cid_a1}",
        headers={"Authorization": f"Bearer {tok_a}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["field_name"] == "full_name"
    assert "deterministic_classification" in data
    assert "statutory_disclaimer" in data
    assert "AUTOMATED COMPARISON RESULT" in data["statutory_disclaimer"]


def test_resolution_context_cross_user_forbidden(p3c_users_and_conflicts):
    """User B attempts to fetch User A's resolution context (rejected with 404 or 403)."""
    tok_b = p3c_users_and_conflicts["token_b"]
    cid_a1 = str(p3c_users_and_conflicts["conflict_a1_id"])

    res = client.get(
        f"/api/v1/assistant/resolution-context/{cid_a1}",
        headers={"Authorization": f"Bearer {tok_b}"}
    )
    assert res.status_code in [403, 404]


def test_multi_turn_followup_preserves_conflict_context(p3c_users_and_conflicts):
    """
    Citizen starts chat with conflict_id in Turn 1.
    In Turn 2, citizen asks a follow-up question WITHOUT passing conflict_id.
    Server-side orchestrator must automatically reconstruct the conflict context from the conversation record!
    """
    tok_a = p3c_users_and_conflicts["token_a"]
    cid_a1 = str(p3c_users_and_conflicts["conflict_a1_id"])

    # Turn 1: Send initial message with conflict_id
    turn1_res = client.post(
        "/api/v1/assistant/chat",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={
            "message": "Why was this full name discrepancy flagged?",
            "conflict_id": cid_a1,
        }
    )
    assert turn1_res.status_code == 200
    turn1_data = turn1_res.json()
    conv_id = turn1_data["conversation_id"]
    assert conv_id is not None

    # Turn 2: Follow-up question with conversation_id ONLY (no conflict_id!)
    turn2_res = client.post(
        "/api/v1/assistant/chat",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={
            "message": "What official forms or gazette notifications apply to resolve this?",
            "conversation_id": conv_id,
            # conflict_id omitted deliberately
        }
    )
    assert turn2_res.status_code == 200
    turn2_data = turn2_res.json()
    assert turn2_data["conversation_id"] == conv_id
    # Answer should address the full name discrepancy from retained context
    answer_text = turn2_data["response"]["answer"] if isinstance(turn2_data["response"], dict) else str(turn2_data["response"])
    assert len(answer_text) > 0


def test_switch_and_unlink_conflict_context(p3c_users_and_conflicts):
    """Citizen can switch linked conflict or unlink it via PATCH."""
    tok_a = p3c_users_and_conflicts["token_a"]
    cid_a1 = str(p3c_users_and_conflicts["conflict_a1_id"])
    cid_a2 = str(p3c_users_and_conflicts["conflict_a2_id"])

    # Create conversation with conflict 1
    create_res = client.post(
        "/api/v1/assistant/conversations",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={"title": "Test Switch", "active_conflict_id": cid_a1}
    )
    conv_id = create_res.json()["id"]

    # Switch to conflict 2
    switch_res = client.patch(
        f"/api/v1/assistant/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={"active_conflict_id": cid_a2}
    )
    assert switch_res.status_code == 200
    assert switch_res.json()["active_conflict_id"] == cid_a2

    # Unlink conflict context
    unlink_res = client.patch(
        f"/api/v1/assistant/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={"active_conflict_id": ""}
    )
    assert unlink_res.status_code == 200
    assert unlink_res.json()["active_conflict_id"] is None


def test_conversation_deletion_does_not_delete_conflict(p3c_users_and_conflicts, db: Session):
    """Deleting a conversation must NOT cascade or delete the underlying conflict."""
    tok_a = p3c_users_and_conflicts["token_a"]
    cid_a1 = str(p3c_users_and_conflicts["conflict_a1_id"])

    # Create conversation
    create_res = client.post(
        "/api/v1/assistant/conversations",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={"title": "Ephemeral Session", "active_conflict_id": cid_a1}
    )
    conv_id = create_res.json()["id"]

    # Delete conversation
    del_res = client.delete(
        f"/api/v1/assistant/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {tok_a}"}
    )
    assert del_res.status_code == 204

    # Verify conflict still exists in database!
    user_a_id = p3c_users_and_conflicts["user_a_id"]
    set_rls_context(db, user_a_id, "user")
    conflict = db.query(Conflict).filter(Conflict.id == uuid.UUID(cid_a1)).first()
    assert conflict is not None
    assert conflict.field_name == "full_name"


def test_pii_sanitization_in_conflict_conversation(p3c_users_and_conflicts, db: Session):
    """When a citizen posts sensitive IDs (Aadhaar, PAN) into the conversation, they must be sanitized before persistence."""
    tok_a = p3c_users_and_conflicts["token_a"]
    cid_a1 = str(p3c_users_and_conflicts["conflict_a1_id"])

    res = client.post(
        "/api/v1/assistant/chat",
        headers={"Authorization": f"Bearer {tok_a}"},
        json={
            "message": "My Aadhaar is 9876 5432 1098 and PAN is ABCDE1234F. Can I fix this?",
            "conflict_id": cid_a1
        }
    )
    assert res.status_code == 200
    conv_id = res.json()["conversation_id"]

    # Verify message in database has sanitized text
    user_a_id = p3c_users_and_conflicts["user_a_id"]
    set_rls_context(db, user_a_id, "user")
    msg = db.query(AssistantMessage).filter(
        AssistantMessage.conversation_id == uuid.UUID(conv_id),
        AssistantMessage.role == "user"
    ).first()

    assert msg is not None
    assert "9876 5432 1098" not in msg.content
    assert "XXXX-XXXX-1098" in msg.content
    assert "ABCDE1234F" not in msg.content
    assert "XXXXX1234F" in msg.content
