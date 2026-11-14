"""
Phase P3A.3: Scalable Cursor-Based Conversation Message Pagination Test Battery.
Verifies:
1. First-page retrieval (default and custom limits, chronological ordering).
2. Multi-page traversal with next_cursor backward into chat history.
3. Stable tie-breaking when messages share identical timestamps.
4. Complete duplicate and missing-message prevention across pagination boundaries.
5. Safe handling of invalid, malformed, and tampered cursors (HTTP 400).
6. Multi-tenant RLS isolation and rejection of cross-conversation cursor manipulation.
7. Empty conversation pagination handling.
8. Page size bounds validation (ge=1, le=100).
9. Resilience to concurrent message insertions.
"""

import base64
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.user import User
from app.models.assistant import AssistantConversation, AssistantMessage
from app.routers.assistant import encode_cursor

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def create_user_helper(prefix="p3a3"):
    uid = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{uid}@gmail.com"
    name = f"Test Citizen {uid}"
    headers = {"Authorization": f"Bearer test_token_:{uid}:{email}:{name}"}

    resp = client.post(
        "/api/v1/auth/provision",
        headers=headers,
        json={"email": email, "full_name": name},
    )
    assert resp.status_code in (200, 201), f"Provisioning failed: {resp.text}"
    return uuid.UUID(resp.json()["id"]), headers


@pytest.fixture
def p3a3_users(db: Session):
    uid_a, headers_a = create_user_helper("p3a3_uA")
    uid_b, headers_b = create_user_helper("p3a3_uB")

    set_rls_context(db, uid_a, "user")
    user_a = db.query(User).filter(User.id == uid_a).first()

    set_rls_context(db, uid_b, "user")
    user_b = db.query(User).filter(User.id == uid_b).first()

    return (user_a, headers_a), (user_b, headers_b)


def test_empty_conversation_pagination(db: Session, p3a3_users):
    """Empty conversation returns 200 OK with total=0, empty list, has_more=False, next_cursor=None."""
    (user_a, headers_a), _ = p3a3_users
    set_rls_context(db, user_a.id, "user")

    conv = AssistantConversation(
        user_id=user_a.id,
        title="Empty Test Chat",
    )
    db.add(conv)
    db.commit()

    resp = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages",
        headers=headers_a
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 0
    assert data["messages"] == []
    assert data["has_more"] is False
    assert data["next_cursor"] is None
    assert data["prev_cursor"] is None


def test_first_page_retrieval_and_ordering(db: Session, p3a3_users):
    """First page retrieval returns latest messages in ascending chronological order."""
    (user_a, headers_a), _ = p3a3_users
    set_rls_context(db, user_a.id, "user")

    conv = AssistantConversation(
        user_id=user_a.id,
        title="15 Message Chat",
    )
    db.add(conv)
    db.flush()

    base_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    for i in range(15):
        msg = AssistantMessage(
            conversation_id=conv.id,
            user_id=user_a.id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i:02d}",
            created_at=base_time + timedelta(minutes=i),
        )
        db.add(msg)
    db.commit()

    resp = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=5",
        headers=headers_a
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 15
    assert len(data["messages"]) == 5
    assert data["has_more"] is True
    assert data["next_cursor"] is not None

    # Verify messages are the 5 latest (indices 10 to 14) in ascending chronological order
    expected_contents = [f"Message {i:02d}" for i in range(10, 15)]
    actual_contents = [m["content"] for m in data["messages"]]
    assert actual_contents == expected_contents


def test_multi_page_traversal_and_zero_duplicate_prevention(db: Session, p3a3_users):
    """Iterating all pages reconstructs the full message history with 0 duplicates and 0 omissions."""
    (user_a, headers_a), _ = p3a3_users
    set_rls_context(db, user_a.id, "user")

    conv = AssistantConversation(
        user_id=user_a.id,
        title="Full Traversal Chat",
    )
    db.add(conv)
    db.flush()

    base_time = datetime.now(timezone.utc) - timedelta(hours=1)
    for i in range(15):
        msg = AssistantMessage(
            conversation_id=conv.id,
            user_id=user_a.id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i:02d}",
            created_at=base_time + timedelta(minutes=i),
        )
        db.add(msg)
    db.commit()

    all_retrieved = []
    seen_ids = set()
    current_cursor = None
    page_count = 0

    while True:
        url = f"/api/v1/assistant/conversations/{conv.id}/messages?limit=5"
        if current_cursor:
            url += f"&before={current_cursor}"

        resp = client.get(url, headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()
        page_count += 1

        page_msgs = data["messages"]
        assert len(page_msgs) <= 5

        # Check for duplicates across pages
        for m in page_msgs:
            assert m["id"] not in seen_ids, f"Duplicate message ID {m['id']} detected across pages"
            seen_ids.add(m["id"])

        # Prepend to aggregate history (since each page is older than the previous)
        all_retrieved = page_msgs + all_retrieved

        if not data["has_more"]:
            assert data["next_cursor"] is None
            break

        assert data["next_cursor"] is not None
        current_cursor = data["next_cursor"]

    assert page_count == 3
    assert len(all_retrieved) == 15
    assert [m["content"] for m in all_retrieved] == [f"Message {i:02d}" for i in range(15)]


def test_stable_timestamp_tie_breaking(db: Session, p3a3_users):
    """Messages with identical created_at timestamps are tie-broken stably by UUID."""
    (user_a, headers_a), _ = p3a3_users
    set_rls_context(db, user_a.id, "user")

    conv = AssistantConversation(
        user_id=user_a.id,
        title="Identical Timestamp Chat",
    )
    db.add(conv)
    db.flush()

    shared_time = datetime.now(timezone.utc)
    for i in range(6):
        msg = AssistantMessage(
            conversation_id=conv.id,
            user_id=user_a.id,
            role="user",
            content=f"Tie Message {i}",
            created_at=shared_time,
        )
        db.add(msg)
    db.commit()

    # Page 1: limit 3
    resp1 = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=3",
        headers=headers_a
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1["messages"]) == 3
    assert data1["has_more"] is True
    cursor = data1["next_cursor"]
    assert cursor is not None

    # Page 2: limit 3 with before=cursor
    resp2 = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=3&before={cursor}",
        headers=headers_a
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["messages"]) == 3
    assert data2["has_more"] is False

    # Check zero overlap
    ids_p1 = {m["id"] for m in data1["messages"]}
    ids_p2 = {m["id"] for m in data2["messages"]}
    assert ids_p1.isdisjoint(ids_p2)
    assert len(ids_p1.union(ids_p2)) == 6


def test_invalid_and_malformed_cursors(db: Session, p3a3_users):
    """Invalid cursor encodings return HTTP 400 Bad Request."""
    (user_a, headers_a), _ = p3a3_users
    set_rls_context(db, user_a.id, "user")

    conv = AssistantConversation(
        user_id=user_a.id,
        title="Invalid Cursor Test",
    )
    db.add(conv)
    db.commit()

    # 1. Non-base64 string
    resp = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?before=not_valid_b64!!!",
        headers=headers_a
    )
    assert resp.status_code == 400
    assert "Invalid pagination cursor format" in resp.json()["detail"]

    # 2. Base64 without delimiter pipe
    b64_no_pipe = base64.urlsafe_b64encode(b"invalid_payload").decode()
    resp = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?before={b64_no_pipe}",
        headers=headers_a
    )
    assert resp.status_code == 400
    assert "Invalid pagination cursor format" in resp.json()["detail"]

    # 3. Base64 with invalid timestamp and UUID
    b64_bad_data = base64.urlsafe_b64encode(b"2026-99-99T99:99:99|not-a-uuid").decode()
    resp = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?before={b64_bad_data}",
        headers=headers_a
    )
    assert resp.status_code == 400
    assert "Invalid pagination cursor format" in resp.json()["detail"]


def test_cursor_manipulation_and_cross_tenant_rejection(db: Session, p3a3_users):
    """Foreign message cursors and unauthorized conversations are strictly rejected."""
    (user_a, headers_a), (user_b, headers_b) = p3a3_users

    # Citizen A setup
    set_rls_context(db, user_a.id, "user")
    conv_a = AssistantConversation(user_id=user_a.id, title="Citizen A Chat")
    db.add(conv_a)
    db.flush()
    msg_a = AssistantMessage(
        conversation_id=conv_a.id,
        user_id=user_a.id,
        role="user",
        content="Confidential query by Citizen A",
        created_at=datetime.now(timezone.utc)
    )
    db.add(msg_a)
    db.commit()

    # Citizen B setup
    set_rls_context(db, user_b.id, "user")
    conv_b = AssistantConversation(user_id=user_b.id, title="Citizen B Chat")
    db.add(conv_b)
    db.flush()
    msg_b = AssistantMessage(
        conversation_id=conv_b.id,
        user_id=user_b.id,
        role="user",
        content="Citizen B message",
        created_at=datetime.now(timezone.utc)
    )
    db.add(msg_b)
    db.commit()

    # 1. Citizen B queries Citizen A's conversation directly -> 404
    resp_unauth = client.get(
        f"/api/v1/assistant/conversations/{conv_a.id}/messages",
        headers=headers_b
    )
    assert resp_unauth.status_code == 404

    # 2. Citizen B crafts a cursor with Citizen A's message ID and queries Citizen B's conversation -> 400
    tampered_cursor = encode_cursor(msg_a.created_at, str(msg_a.id))
    resp_tamper = client.get(
        f"/api/v1/assistant/conversations/{conv_b.id}/messages?before={tampered_cursor}",
        headers=headers_b
    )
    assert resp_tamper.status_code == 400
    assert "Invalid pagination cursor: message not found in this conversation" in resp_tamper.json()["detail"]


def test_page_size_minimum_and_maximum_validation(db: Session, p3a3_users):
    """Enforces server-side limit boundaries: ge=1, le=100."""
    (user_a, headers_a), _ = p3a3_users
    set_rls_context(db, user_a.id, "user")

    conv = AssistantConversation(user_id=user_a.id, title="Boundary Test Chat")
    db.add(conv)
    db.commit()

    # limit=0 is rejected with 422
    resp_zero = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=0",
        headers=headers_a
    )
    assert resp_zero.status_code == 422

    # limit=-1 is rejected with 422
    resp_neg = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=-1",
        headers=headers_a
    )
    assert resp_neg.status_code == 422

    # limit=101 is rejected with 422
    resp_over = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=101",
        headers=headers_a
    )
    assert resp_over.status_code == 422

    # limit=1 is accepted with 200
    resp_min = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=1",
        headers=headers_a
    )
    assert resp_min.status_code == 200

    # limit=100 is accepted with 200
    resp_max = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=100",
        headers=headers_a
    )
    assert resp_max.status_code == 200


def test_concurrent_message_insertion_resilience(db: Session, p3a3_users):
    """New messages inserted after initial page retrieval do not corrupt older page pagination."""
    (user_a, headers_a), _ = p3a3_users
    set_rls_context(db, user_a.id, "user")

    conv = AssistantConversation(user_id=user_a.id, title="Concurrent Chat")
    db.add(conv)
    db.flush()

    base_time = datetime.now(timezone.utc) - timedelta(minutes=20)
    for i in range(10):
        msg = AssistantMessage(
            conversation_id=conv.id,
            user_id=user_a.id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Initial Msg {i}",
            created_at=base_time + timedelta(minutes=i),
        )
        db.add(msg)
    db.commit()

    # 1. Fetch latest page of 5 (initial msgs 5..9)
    resp1 = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=5",
        headers=headers_a
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert [m["content"] for m in data1["messages"]] == [f"Initial Msg {i}" for i in range(5, 10)]
    next_cursor = data1["next_cursor"]
    assert next_cursor is not None

    # 2. Concurrently insert a newer message (index 10)
    set_rls_context(db, user_a.id, "user")
    concurrent_msg = AssistantMessage(
        conversation_id=conv.id,
        user_id=user_a.id,
        role="user",
        content="Concurrent New Msg 10",
        created_at=datetime.now(timezone.utc),
    )
    db.add(concurrent_msg)
    db.commit()

    # 3. Request older page using next_cursor
    resp2 = client.get(
        f"/api/v1/assistant/conversations/{conv.id}/messages?limit=5&before={next_cursor}",
        headers=headers_a
    )
    assert resp2.status_code == 200
    data2 = resp2.json()

    # The older page correctly returns initial msgs 0..4 without skipping or including msg 10
    assert len(data2["messages"]) == 5
    assert [m["content"] for m in data2["messages"]] == [f"Initial Msg {i}" for i in range(5)]
    assert data2["has_more"] is False
