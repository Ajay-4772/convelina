"""
Phase P3A: Conversational Workspace Foundation Test Battery.
Verifies:
1. Server-side PII sanitization (Aadhaar, PAN, phone number pre-persistence masking).
2. AssistantConversation pinning, archiving, and response_language persistence.
3. MessageAttachment model, relationships, and foreign key cascading.
4. Assistant router endpoints: PATCH /conversations/{id}, GET /conversations/search.
5. Cross-user Row-Level Security isolation.
6. Audit logging of PII masking and conversation updates.
"""

import uuid
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.core.sanitizer import (
    redact_aadhaar,
    redact_pan,
    redact_phone,
    sanitize_pii,
)
from app.models.user import User
from app.models.assistant import AssistantConversation, AssistantMessage, MessageAttachment
from app.models.audit_log import AuditLog
from app.rag.assistant.orchestrator import RAGOrchestrator
from app.rag.schemas import ConversationUpdateRequest

client = TestClient(app)


# ---------------------------------------------------------------------------
# Test Fixtures & Utilities
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def create_user_helper(prefix="p3a"):
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
    return uuid.UUID(resp.json()["id"])


@pytest.fixture
def p3a_users(db: Session):
    uid_a = create_user_helper("p3a_uA")
    uid_b = create_user_helper("p3a_uB")

    set_rls_context(db, uid_a, "user")
    user_a = db.query(User).filter(User.id == uid_a).first()

    set_rls_context(db, uid_b, "user")
    user_b = db.query(User).filter(User.id == uid_b).first()

    return user_a, user_b


# ---------------------------------------------------------------------------
# 1. PII Sanitizer Unit Tests
# ---------------------------------------------------------------------------

def test_redact_aadhaar_formats():
    """Validates masking across spaced, hyphenated, and continuous Aadhaar formats."""
    # Spaced
    text1 = "My Aadhaar card number is 2345 6789 0123."
    res1, count1 = redact_aadhaar(text1)
    assert count1 == 1
    assert res1 == "My Aadhaar card number is XXXX-XXXX-0123."

    # Hyphenated
    text2 = "Check reference 9876-5432-1098 please."
    res2, count2 = redact_aadhaar(text2)
    assert count2 == 1
    assert res2 == "Check reference XXXX-XXXX-1098 please."

    # Continuous
    text3 = "UID: 112233445566."
    res3, count3 = redact_aadhaar(text3)
    assert count3 == 1
    assert res3 == "UID: XXXX-XXXX-5566."


def test_redact_pan_format():
    """Validates masking of 10-character PAN identifiers."""
    text = "Income tax PAN ABCDE1234F has mismatch with Aadhaar."
    res, count = redact_pan(text)
    assert count == 1
    assert res == "Income tax PAN XXXXX1234F has mismatch with Aadhaar."


def test_redact_phone_format():
    """Validates masking of Indian 10-digit mobile phone numbers."""
    text = "Contact me at +91 9876543210 or 8765432109."
    res, count = redact_phone(text)
    assert count == 2
    assert "XXXXXX3210" in res
    assert "XXXXXX2109" in res


def test_sanitize_pii_composite():
    """Validates multi-identifier sanitization in a single combined pass."""
    dirty_text = (
        "Hello, my Aadhaar is 2345 6789 0123, PAN is ABCDE1234F, "
        "and mobile is 9876543210. Why is my name mismatched?"
    )
    clean_text, was_redacted, summary = sanitize_pii(dirty_text)
    assert was_redacted is True
    assert summary["aadhaar_redactions"] == 1
    assert summary["pan_redactions"] == 1
    assert summary["phone_redactions"] == 1
    assert "2345 6789 0123" not in clean_text
    assert "ABCDE1234F" not in clean_text
    assert "9876543210" not in clean_text
    assert "XXXX-XXXX-0123" in clean_text
    assert "XXXXX1234F" in clean_text
    assert "XXXXXX3210" in clean_text


def test_sanitize_pii_no_op():
    """Validates that non-PII text is unchanged and marked unredacted."""
    safe_text = "What is the procedure for updating date of birth in my passport?"
    clean_text, was_redacted, summary = sanitize_pii(safe_text)
    assert was_redacted is False
    assert clean_text == safe_text
    assert summary["total_redactions"] == 0


# ---------------------------------------------------------------------------
# 2. Database Models & Schema Extensions Tests
# ---------------------------------------------------------------------------

def test_conversation_defaults_and_pins(db: Session, p3a_users):
    user_a, _ = p3a_users
    set_rls_context(db, user_a.id, "user")

    conv = AssistantConversation(
        user_id=user_a.id,
        title="EPFO Name Correction Inquiry",
    )
    db.add(conv)
    db.commit()

    # In PostgreSQL RLS, commit resets transaction session variables; re-apply for next tx
    set_rls_context(db, user_a.id, "user")
    db.refresh(conv)

    # Defaults check
    assert conv.is_pinned is False
    assert conv.is_archived is False
    assert conv.response_language == "en"

    # Update pinning
    conv.is_pinned = True
    conv.response_language = "ta"
    db.commit()

    set_rls_context(db, user_a.id, "user")
    db.refresh(conv)

    conv_dict = conv.to_dict()
    assert conv_dict["is_pinned"] is True
    assert conv_dict["response_language"] == "ta"


def test_message_attachments_lifecycle(db: Session, p3a_users):
    user_a, _ = p3a_users
    set_rls_context(db, user_a.id, "user")

    conv = AssistantConversation(user_id=user_a.id, title="Attachment Test Thread")
    db.add(conv)
    db.flush()

    msg = AssistantMessage(
        conversation_id=conv.id,
        user_id=user_a.id,
        role="user",
        content="Here is a screenshot of the EPFO rejection notice.",
        message_type="image_analysis",
    )
    db.add(msg)
    db.flush()

    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    att = MessageAttachment(
        message_id=msg.id,
        user_id=user_a.id,
        file_name="epfo_rejection.png",
        mime_type="image/png",
        file_size_bytes=1048576,
        storage_ref="ephemeral/epfo_rejection_abc123.png",
        extracted_text="Member name mismatch with Aadhaar database.",
        is_temporary=True,
        expires_at=expires,
    )
    db.add(att)
    db.commit()

    set_rls_context(db, user_a.id, "user")
    db.refresh(msg)

    # Verify serialization includes attachment
    msg_dict = msg.to_dict()
    assert msg_dict["message_type"] == "image_analysis"
    assert len(msg_dict["attachments"]) == 1
    assert msg_dict["attachments"][0]["file_name"] == "epfo_rejection.png"
    assert msg_dict["attachments"][0]["is_temporary"] is True

    # Cascade deletion check: deleting conversation removes message and attachment
    db.delete(conv)
    db.commit()

    set_rls_context(db, user_a.id, "user")
    att_check = db.query(MessageAttachment).filter(MessageAttachment.id == att.id).first()
    assert att_check is None


# ---------------------------------------------------------------------------
# 3. RAGOrchestrator Pre-Persistence PII Sanitization & Audit
# ---------------------------------------------------------------------------

def test_orchestrator_pre_persistence_sanitization(db: Session, p3a_users):
    user_a, _ = p3a_users
    set_rls_context(db, user_a.id, "user")

    orchestrator = RAGOrchestrator(db)
    raw_prompt = "My Aadhaar is 2345 6789 0123 and PAN is ABCDE1234F. How do I fix the name spelling?"

    result = orchestrator.answer_question(
        user_id=user_a.id,
        question=raw_prompt,
        language="en"
    )

    conv_id = uuid.UUID(result["conversation_id"])

    # Re-apply RLS context after answer_question's internal commit
    set_rls_context(db, user_a.id, "user")

    # Query the stored user message from PostgreSQL
    user_msg = db.query(AssistantMessage).filter(
        AssistantMessage.conversation_id == conv_id,
        AssistantMessage.role == "user"
    ).first()

    assert user_msg is not None
    # Crucial: Raw 12-digit Aadhaar and PAN MUST NOT exist in the database!
    assert "2345 6789 0123" not in user_msg.content
    assert "ABCDE1234F" not in user_msg.content
    assert "XXXX-XXXX-0123" in user_msg.content
    assert "XXXXX1234F" in user_msg.content

    # Check that audit log recorded the masking event
    audit_entry = db.query(AuditLog).filter(
        AuditLog.action == "pii_masked_in_chat",
        AuditLog.user_id == user_a.id
    ).first()

    assert audit_entry is not None
    assert audit_entry.details["aadhaar_redactions"] == 1
    assert audit_entry.details["pan_redactions"] == 1


# ---------------------------------------------------------------------------
# 4. Assistant Router Endpoints & Search Tests
# ---------------------------------------------------------------------------

def test_router_list_and_patch_conversation(db: Session, p3a_users):
    from app.routers.assistant import list_conversations, update_conversation
    user_a, _ = p3a_users
    set_rls_context(db, user_a.id, "user")

    # 1. Create two conversations
    c1 = AssistantConversation(user_id=user_a.id, title="Unpinned Thread", is_pinned=False)
    c2 = AssistantConversation(user_id=user_a.id, title="Pinned Priority Thread", is_pinned=True)
    db.add_all([c1, c2])
    db.commit()

    # 2. List conversations: pinned should come first
    list_res = list_conversations(current_user=user_a, db=db)
    assert list_res.total >= 2
    assert list_res.conversations[0].is_pinned is True

    # 3. Patch conversation 1: pin it and rename it
    update_req = ConversationUpdateRequest(
        title="Renamed Thread Alpha",
        is_pinned=True,
        response_language="hi"
    )
    patched = update_conversation(
        conversation_id=str(c1.id),
        req=update_req,
        current_user=user_a,
        db=db
    )
    assert patched.title == "Renamed Thread Alpha"
    assert patched.is_pinned is True
    assert patched.response_language == "hi"


def test_router_search_conversations(db: Session, p3a_users):
    from app.routers.assistant import search_conversations
    user_a, _ = p3a_users
    set_rls_context(db, user_a.id, "user")

    # 1. Create conversation with distinct title
    c_title = AssistantConversation(
        user_id=user_a.id,
        title="UniqueTitleSearchingForGazette",
    )
    db.add(c_title)
    db.flush()

    # 2. Create conversation where only the message content has keyword
    c_msg = AssistantConversation(
        user_id=user_a.id,
        title="General Query",
    )
    db.add(c_msg)
    db.flush()

    m = AssistantMessage(
        conversation_id=c_msg.id,
        user_id=user_a.id,
        role="user",
        content="Where can I download the Central Gazette format for father name change?",
    )
    db.add(m)
    db.commit()

    # Search for "Gazette"
    search_res = search_conversations(q="Gazette", current_user=user_a, db=db)
    assert search_res.total >= 2

    matching_titles = [r.conversation.title for r in search_res.results]
    assert "UniqueTitleSearchingForGazette" in matching_titles
    assert "General Query" in matching_titles


# ---------------------------------------------------------------------------
# 5. Row-Level Security Cross-User Isolation
# ---------------------------------------------------------------------------

def test_cross_user_rls_isolation(db: Session, p3a_users):
    from app.routers.assistant import update_conversation, search_conversations, delete_conversation
    from fastapi import HTTPException
    user_a, user_b = p3a_users

    # Create conversation under User A
    set_rls_context(db, user_a.id, "user")
    conv_a = AssistantConversation(user_id=user_a.id, title="User A Private Secret Conversation")
    db.add(conv_a)
    db.commit()

    # 1. User B tries to update User A's conversation -> 404
    with pytest.raises(HTTPException) as exc_info:
        update_conversation(
            conversation_id=str(conv_a.id),
            req=ConversationUpdateRequest(title="Hacked Title"),
            current_user=user_b,
            db=db
        )
    assert exc_info.value.status_code == 404

    # 2. User B tries to delete User A's conversation -> 404
    with pytest.raises(HTTPException) as exc_info:
        delete_conversation(
            conversation_id=str(conv_a.id),
            current_user=user_b,
            db=db
        )
    assert exc_info.value.status_code == 404

    # 3. User B searches for "Private Secret" -> 0 results
    search_res = search_conversations(q="Private Secret", current_user=user_b, db=db)
    assert search_res.total == 0
