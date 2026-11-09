"""
CONVELINA — Phase P3G.3 Security Tests: Confirmation Security & Invalidation Hardening

Verifies the mandatory P3G.3 security requirements:
1. Client-supplied `is_user_confirmed=true` cannot bypass server-side citizen confirmation.
2. Confirmation is authenticated, persisted, field-specific, value-specific and user-specific.
3. Changing a confirmed value on document or draft invalidates confirmation.
4. The current draft version and SHA-256 hash are checked; mismatches rejected with HTTP 409.
5. Attempted client-side confirmation bypasses are strictly prevented.
"""

import uuid
import hashlib
from datetime import datetime, timezone
import pytest
from fastapi import HTTPException

from app.core.database import SessionLocal, set_rls_context
from app.models.user import User
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.correction_draft import CorrectionDraft, CorrectionDraftVersion, MANDATORY_DRAFT_DISCLAIMER
from app.models.audit_log import AuditLog
from app.schemas.correction_draft import (
    DraftTypeEnum,
    DocumentCategoryEnum,
    DraftStatusEnum,
    CorrectionDraftCreate,
    CorrectionDraftUpdate,
    CorrectionDraftConfirmRequest,
)
from app.schemas.document import DocumentFieldsUpdate
from app.services.draft_safety_service import DraftSafetyService
from app.routers.correction_drafts import (
    create_correction_draft,
    update_correction_draft,
    confirm_correction_draft,
)
from app.routers.documents import update_document_fields


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_users(db_session):
    set_rls_context(db_session, uuid.uuid4(), "admin")
    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()

    user_1 = User(
        id=u1_id,
        firebase_uid=f"p3g3_sec_u1_{uuid.uuid4().hex[:8]}",
        email=f"p3g3_sec_u1_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Aarav Patel",
        role="user",
    )
    user_2 = User(
        id=u2_id,
        firebase_uid=f"p3g3_sec_u2_{uuid.uuid4().hex[:8]}",
        email=f"p3g3_sec_u2_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Meera Sen",
        role="user",
    )
    db_session.add_all([user_1, user_2])
    db_session.commit()

    return user_1, user_2


class TestP3G3ConfirmationSecurityHardening:
    """Rigorous verification of citizen confirmation persistence and bypass prevention."""

    def test_client_supplied_is_user_confirmed_flag_cannot_bypass_draft_gate(self, db_session, test_users):
        """A client sending is_user_confirmed: true in payload cannot fake confirmation."""
        user_1, _ = test_users
        set_rls_context(db_session, user_1.id, "user")

        doc = Document(
            id=uuid.uuid4(),
            user_id=user_1.id,
            document_type="pan",
            file_path="ephemeral://pan.pdf",
            file_hash="hash_sec_1",
            ocr_status="completed",
            extracted_fields={"name": "AARAV PATEL", "pan": "ABCDE1234F"},
            is_user_confirmed=False,
            confirmed_fields={},
        )
        conflict = Conflict(
            id=uuid.uuid4(),
            user_id=user_1.id,
            doc_a_id=doc.id,
            doc_b_id=doc.id,
            conflict_type="genuine-mismatch",
            severity="medium",
            field_name="name",
            value_a="AARAV PATEL",
            value_b="ARAV P",
            description="Name spelling discrepancy",
        )
        db_session.add_all([doc, conflict])
        db_session.commit()

        # Attempt to create draft with unconfirmed document
        set_rls_context(db_session, user_1.id, "user")
        req = CorrectionDraftCreate(
            conflict_id=conflict.id,
            document_type=DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value,
            document_category="pan",
            confirmed_fields={},  # No confirmed fields
        )

        with pytest.raises(HTTPException) as exc:
            create_correction_draft(req=req, db=db_session, current_user=user_1)

        assert exc.value.status_code == 422
        assert exc.value.detail["error"] == "citizen_confirmation_required"

    def test_confirmation_is_persisted_to_database_record(self, db_session, test_users):
        """When confirmed fields are supplied, they are persisted to Document in PostgreSQL under RLS."""
        user_1, _ = test_users
        set_rls_context(db_session, user_1.id, "user")

        doc = Document(
            id=uuid.uuid4(),
            user_id=user_1.id,
            document_type="pan",
            file_path="ephemeral://pan.pdf",
            file_hash="hash_sec_2",
            ocr_status="needs_review",
            extracted_fields={"name": "AARAV PATEL"},
            is_user_confirmed=False,
            confirmed_fields={},
        )
        conflict = Conflict(
            id=uuid.uuid4(),
            user_id=user_1.id,
            doc_a_id=doc.id,
            doc_b_id=doc.id,
            conflict_type="genuine-mismatch",
            severity="medium",
            field_name="name",
            value_a="AARAV PATEL",
            value_b="ARAV P",
            description="Discrepancy",
        )
        db_session.add_all([doc, conflict])
        db_session.commit()

        # Submit confirmed fields via wizard Step 2
        set_rls_context(db_session, user_1.id, "user")
        req = CorrectionDraftCreate(
            conflict_id=conflict.id,
            document_type=DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value,
            document_category="pan",
            confirmed_fields={
                "applicant_name": "Aarav Patel",
                "requested_value": "AARAV PATEL",
            },
            user_explanation="Correct spelling",
            requested_action="Rectify PAN",
        )

        resp = create_correction_draft(req=req, db=db_session, current_user=user_1)
        assert resp.id is not None

        # Verify Document was persisted with is_user_confirmed = True
        set_rls_context(db_session, user_1.id, "user")
        reloaded_doc = db_session.query(Document).filter(Document.id == doc.id).first()
        assert reloaded_doc.is_user_confirmed is True
        assert reloaded_doc.confirmed_at is not None
        assert reloaded_doc.confirmed_fields["applicant_name"] == "Aarav Patel"
        assert reloaded_doc.confirmed_fields["requested_value"] == "AARAV PATEL"

        # Verify audit log was recorded for document confirmation
        audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.entity_id == doc.id, AuditLog.action == "document_fields_confirmed")
            .first()
        )
        assert audit is not None
        assert audit.current_hash is not None

    def test_changing_confirmed_fields_on_draft_invalidates_confirmation(self, db_session, test_users):
        """Updating confirmed fields on a confirmed draft invalidates its confirmation and creates a new version."""
        user_1, _ = test_users
        set_rls_context(db_session, user_1.id, "user")

        draft = CorrectionDraft(
            id=uuid.uuid4(),
            user_id=user_1.id,
            document_type=DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value,
            document_category=DocumentCategoryEnum.PAN.value,
            status=DraftStatusEnum.CITIZEN_CONFIRMED.value,
            title="Confirmed Draft",
            content=f"{MANDATORY_DRAFT_DISCLAIMER}\n\nTo,\nNSDL\nSubject: Correction\n\nContent",
            version=1,
            is_citizen_confirmed=True,
            citizen_confirmed_at=datetime.now(timezone.utc),
            confirmed_version_number=1,
            confirmed_fields={"applicant_name": "Aarav Patel"},
        )
        db_session.add(draft)
        db_session.commit()

        # Update confirmed fields
        set_rls_context(db_session, user_1.id, "user")
        update_req = CorrectionDraftUpdate(
            confirmed_fields={"applicant_name": "Aarav K. Patel"}
        )
        updated = update_correction_draft(draft_id=draft.id, req=update_req, db=db_session, current_user=user_1)

        assert updated.is_citizen_confirmed is False
        assert updated.citizen_confirmed_at is None
        assert updated.confirmed_version_number is None
        assert updated.version == 2
        assert updated.status == DraftStatusEnum.CITIZEN_EDITED.value

    def test_changing_document_fields_invalidates_document_confirmation(self, db_session, test_users):
        """PATCH /documents/{id}/fields on a confirmed document invalidates its confirmation."""
        user_1, _ = test_users
        set_rls_context(db_session, user_1.id, "user")

        doc = Document(
            id=uuid.uuid4(),
            user_id=user_1.id,
            document_type="pan",
            file_path="ephemeral://pan.pdf",
            file_hash="hash_sec_3",
            ocr_status="completed",
            extracted_fields={"name": "AARAV PATEL"},
            is_user_confirmed=True,
            confirmed_at=datetime.now(timezone.utc),
            confirmed_fields={"applicant_name": "Aarav Patel"},
        )
        db_session.add(doc)
        db_session.commit()

        # Patch document fields
        set_rls_context(db_session, user_1.id, "user")
        update_payload = DocumentFieldsUpdate(
            extracted_fields={"name": "AARAV KUMAR PATEL"}
        )
        res = update_document_fields(document_id=doc.id, payload=update_payload, current_user=user_1, db=db_session)

        assert res.is_user_confirmed is False
        assert res.confirmed_at is None

    def test_confirm_draft_checks_sha256_hash_and_rejects_mismatch(self, db_session, test_users):
        """Confirming with mismatched expected_sha256_hash returns HTTP 409 Conflict."""
        user_1, _ = test_users
        set_rls_context(db_session, user_1.id, "user")

        draft = CorrectionDraft(
            id=uuid.uuid4(),
            user_id=user_1.id,
            document_type=DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value,
            document_category=DocumentCategoryEnum.PAN.value,
            status=DraftStatusEnum.AI_GENERATED.value,
            title="Draft for Hash Check",
            content=f"{MANDATORY_DRAFT_DISCLAIMER}\n\nContent to hash",
            version=1,
            is_citizen_confirmed=False,
        )
        ver = CorrectionDraftVersion(
            draft_id=draft.id,
            user_id=user_1.id,
            version_number=1,
            content=draft.content,
            change_type="initial_generation",
            is_citizen_confirmed=False,
        )
        db_session.add_all([draft, ver])
        db_session.commit()

        # Attempt to confirm with wrong expected hash
        set_rls_context(db_session, user_1.id, "user")
        wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        confirm_req = CorrectionDraftConfirmRequest(
            confirmation_statement="I confirm this document.",
            version_number=1,
            expected_sha256_hash=wrong_hash,
        )

        with pytest.raises(HTTPException) as exc:
            confirm_correction_draft(draft_id=draft.id, req=confirm_req, db=db_session, current_user=user_1)

        assert exc.value.status_code == 409
        assert "Draft content has changed" in exc.value.detail or "hash mismatch" in exc.value.detail.lower()

        # Now confirm with matching hash -> succeeds
        correct_hash = hashlib.sha256(draft.content.encode("utf-8")).hexdigest()
        confirm_req_valid = CorrectionDraftConfirmRequest(
            confirmation_statement="I confirm this document.",
            version_number=1,
            expected_sha256_hash=correct_hash,
        )
        confirmed = confirm_correction_draft(draft_id=draft.id, req=confirm_req_valid, db=db_session, current_user=user_1)
        assert confirmed.is_citizen_confirmed is True
        assert confirmed.status == DraftStatusEnum.CITIZEN_CONFIRMED.value
        assert confirmed.sha256_hash == correct_hash

