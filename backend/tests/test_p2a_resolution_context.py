"""
CONVELINA - Phase P2A AI Resolution Assistant Context Grounding Test Battery
Tests server-side ResolutionContextService, secure API endpoint, RAG orchestrator
grounding, privacy minimization, OCR quality warnings, and tamper-evident audit logging.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.audit_log import AuditLog
from app.services.resolution_context_service import ResolutionContextService
from app.rag.assistant.orchestrator import RAGOrchestrator

client = TestClient(app)


def create_test_user_session():
    """Helper to provision a synthetic user and return auth headers and UUID."""
    uid = f"p2a_{uuid.uuid4().hex[:8]}"
    email = f"{uid}@convelina.test"
    name = f"Test User {uid}"
    headers = {"Authorization": f"Bearer test_token_:{uid}:{email}:{name}"}

    resp = client.post(
        "/api/v1/auth/provision",
        headers=headers,
        json={"email": email, "full_name": name},
    )
    assert resp.status_code in (200, 201), f"Provisioning failed: {resp.text}"
    user_id = uuid.UUID(resp.json()["id"])
    return headers, user_id


def seed_document(
    user_id: uuid.UUID,
    doc_type: str,
    extracted_fields: dict,
    ocr_status: str = "completed",
    masked_id: str = "TEST-DOC-1234",
) -> Document:
    """Helper to directly seed a document record under RLS context."""
    db = SessionLocal()
    try:
        set_rls_context(db, user_id, "user")
        doc_id = uuid.uuid4()
        doc = Document(
            id=doc_id,
            user_id=user_id,
            document_type=doc_type,
            file_path=f"ephemeral://test_{uuid.uuid4().hex[:12]}",
            file_hash=uuid.uuid4().hex,
            ocr_status=ocr_status,
            extracted_fields=extracted_fields,
            masked_id=masked_id,
        )
        db.add(doc)
        db.commit()
        return doc
    finally:
        db.close()


def seed_conflict_with_metadata(
    user_id: uuid.UUID,
    doc_a: Document,
    doc_b: Document,
    field_name: str = "full_name",
    val_a: str = "M Ajay",
    val_b: str = "Ajay Muthu",
    classification: str = "INITIAL_AMBIGUITY",
    severity: str = "medium",
    requires_manual_review: bool = True,
    confidence_score: float = 0.85,
    possible_causes: list = None,
    recommended_action: str = "Update PAN card name to match Aadhaar full name via Form 49A",
) -> Conflict:
    """Helper to seed a conflict with rich Phase P1/P2 metadata."""
    db = SessionLocal()
    try:
        set_rls_context(db, user_id, "user")
        c_id = uuid.uuid4()
        meta = {
            "classification": classification,
            "confidence_score": confidence_score,
            "requires_manual_review": requires_manual_review,
            "possible_causes": possible_causes or ["Single initial expansion ambiguity (M vs Muthu)"],
            "recommended_action": recommended_action,
            "overall_classification": "AMBIGUOUS_NEEDS_REVIEW",
            "evidence": ["Aadhaar has single initial 'M'", "PAN has patronymic 'Muthu'"],
        }
        conf = Conflict(
            id=c_id,
            user_id=user_id,
            doc_a_id=doc_a.id,
            doc_b_id=doc_b.id,
            conflict_type="unresolvable-needs-evidence",
            severity=severity,
            field_name=field_name,
            value_a=val_a,
            value_b=val_b,
            description="Initial expansion discrepancy between Aadhaar and PAN",
            status="detected",
            comparison_method="deterministic_p0_engine",
            similarity_score=round(confidence_score * 100, 2),
            metadata_=meta,
        )
        db.add(conf)
        db.commit()
        return conf
    finally:
        db.close()


class TestP2AResolutionContextGrounding:
    """Dedicated test suite for Phase P2A Resolution Assistant Grounding."""

    def test_01_user_can_access_own_resolution_context(self):
        """1. Authenticated user can fetch their own verified ResolutionContext."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "M Ajay", "overall_ocr_confidence": 0.95})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay Muthu", "overall_ocr_confidence": 0.92})
        conf = seed_conflict_with_metadata(user_id, doc1, doc2)

        resp = client.get(
            f"/api/v1/assistant/resolution-context/{conf.id}",
            headers=headers,
        )
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        assert data["conflict_id"] == str(conf.id)
        assert data["field_name"] == "full_name"
        assert data["deterministic_classification"] == "INITIAL_AMBIGUITY"
        assert data["confidence_score"] == 0.85
        assert data["requires_manual_review"] is True
        assert "Aadhaar Card" in str(data["document_types"]) or "aadhaar" in data["document_types"]
        assert "PAN Card" in str(data["document_types"]) or "pan" in data["document_types"]
        assert data["statutory_disclaimer"] == "AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION"

    def test_02_cross_user_conflict_access_is_rejected(self):
        """2. Cross-user access to another user's conflict is rejected."""
        headers_a, user_a = create_test_user_session()
        headers_b, user_b = create_test_user_session()

        doc1 = seed_document(user_a, "aadhaar", {"full_name": "Ajay Kumar"})
        doc2 = seed_document(user_a, "pan", {"full_name": "Ajay Kumar"})
        conf = seed_conflict_with_metadata(user_a, doc1, doc2)

        # User B attempts to access User A's conflict
        resp = client.get(
            f"/api/v1/assistant/resolution-context/{conf.id}",
            headers=headers_b,
        )
        assert resp.status_code in (403, 404)

    def test_03_aadhaar_sensitive_identifiers_remain_masked(self):
        """3. Aadhaar numbers in values or descriptions remain strictly masked."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "Ajay", "aadhaar_number": "XXXX-XXXX-9876"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay"})
        # Intentionally seed a value containing an unmasked 12-digit Aadhaar pattern
        conf = seed_conflict_with_metadata(
            user_id,
            doc1,
            doc2,
            val_a="Aadhaar 1234 5678 9876 linked",
            val_b="Aadhaar 9876 5432 1098 linked",
        )

        resp = client.get(
            f"/api/v1/assistant/resolution-context/{conf.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "1234 5678 9876" not in data["value_a"]
        assert "XXXX-XXXX-9876" in data["value_a"]
        assert "9876 5432 1098" not in data["value_b"]
        assert "XXXX-XXXX-1098" in data["value_b"]

    def test_04_resolution_context_uses_database_metadata(self):
        """4. ResolutionContext derives directly from stored deterministic metadata."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "M Ajay"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay Muthu"})
        rec_action = "File Form 49A with gazette notification"
        causes = ["Patronymic expanded into surname field"]
        conf = seed_conflict_with_metadata(
            user_id,
            doc1,
            doc2,
            classification="TRUNCATION_OR_PARTIAL_MATCH",
            recommended_action=rec_action,
            possible_causes=causes,
        )

        resp = client.get(
            f"/api/v1/assistant/resolution-context/{conf.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deterministic_classification"] == "TRUNCATION_OR_PARTIAL_MATCH"
        assert data["recommended_action"] == rec_action
        assert data["possible_causes"] == causes

    def test_05_client_cannot_inject_fake_classification(self):
        """5. Client cannot override or inject fake classification via parameters."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "M Ajay"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay Muthu"})
        conf = seed_conflict_with_metadata(user_id, doc1, doc2, classification="INITIAL_AMBIGUITY")

        # Attempt to pass fake classification in query params
        resp = client.get(
            f"/api/v1/assistant/resolution-context/{conf.id}?classification=EXACT_MATCH&confidence_score=1.0",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Must retain real database value, ignoring client injection
        assert data["deterministic_classification"] == "INITIAL_AMBIGUITY"
        assert data["confidence_score"] == 0.85

    def test_06_deterministic_classification_reaches_orchestrator(self):
        """6. RAG Orchestrator case context receives deterministic findings from ResolutionContextService."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "M Ajay"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay Muthu"})
        conf = seed_conflict_with_metadata(user_id, doc1, doc2, classification="INITIAL_AMBIGUITY")

        db = SessionLocal()
        try:
            set_rls_context(db, user_id, "user")
            orchestrator = RAGOrchestrator(db)
            case_ctx = orchestrator._build_minimal_case_context(user_id=user_id, conflict_id=conf.id)

            assert case_ctx["deterministic_findings"] is not None
            findings = case_ctx["deterministic_findings"]
            assert findings["classification"] == "INITIAL_AMBIGUITY"
            assert findings["field_name"] == "full_name"
            assert findings["confidence_score"] == 0.85
            assert findings["requires_manual_review"] is True
            assert findings["statutory_disclaimer"] == "AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION"
        finally:
            db.close()

    def test_07_low_ocr_confidence_warning_is_preserved(self):
        """7. Low OCR confidence (< 60%) generates a clear warning in ResolutionContext."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "Ajay", "overall_ocr_confidence": 0.42})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay", "overall_ocr_confidence": 0.90})
        conf = seed_conflict_with_metadata(
            user_id,
            doc1,
            doc2,
            classification="LOW_CONFIDENCE_NEEDS_REVIEW",
            requires_manual_review=True,
        )

        resp = client.get(
            f"/api/v1/assistant/resolution-context/{conf.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ocr_quality_warning"] is not None
        assert "60%" in data["ocr_quality_warning"]
        assert data["requires_manual_review"] is True

    def test_08_manual_review_requirement_is_preserved(self):
        """8. Ambiguous or critical discrepancies strictly preserve requires_manual_review flag."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "Ajay Kumar"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Vijay Kumar"})
        conf = seed_conflict_with_metadata(
            user_id,
            doc1,
            doc2,
            classification="MISMATCH",
            severity="critical",
            requires_manual_review=True,
        )

        resp = client.get(
            f"/api/v1/assistant/resolution-context/{conf.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["requires_manual_review"] is True

    def test_09_audit_event_generated_for_context_creation(self):
        """9. Audit log entry is generated with action 'resolution_context_generated'."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "M Ajay"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay Muthu"})
        conf = seed_conflict_with_metadata(user_id, doc1, doc2)

        resp = client.get(
            f"/api/v1/assistant/resolution-context/{conf.id}",
            headers=headers,
        )
        assert resp.status_code == 200

        # Query audit_log via raw SQL with user RLS context
        db = SessionLocal()
        try:
            set_rls_context(db, user_id, "user")
            audit = db.execute(
                text("SELECT action, entity_type, entity_id, user_id, details FROM audit_log WHERE action = 'resolution_context_generated' AND entity_id = :eid ORDER BY created_at DESC LIMIT 1;"),
                {"eid": conf.id},
            ).mappings().first()

            assert audit is not None
            assert audit["action"] == "resolution_context_generated"
            assert audit["user_id"] == user_id
            assert audit["details"]["field_name"] == "full_name"
            assert audit["details"]["deterministic_classification"] == "INITIAL_AMBIGUITY"
        finally:
            db.close()

    def test_10_audit_event_generated_for_resolution_guidance(self):
        """10. Requesting conflict explanation or guidance creates 'resolution_guidance_requested' audit event."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "M Ajay"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay Muthu"})
        conf = seed_conflict_with_metadata(user_id, doc1, doc2)

        # Call chat with conflict_id
        resp = client.post(
            "/api/v1/assistant/chat",
            headers=headers,
            json={
                "message": "Why was my name flagged as ambiguous?",
                "conflict_id": str(conf.id),
            },
        )
        assert resp.status_code == 200

        db = SessionLocal()
        try:
            set_rls_context(db, user_id, "user")
            audit = db.execute(
                text("SELECT action, entity_type, entity_id, user_id, details FROM audit_log WHERE action = 'resolution_guidance_requested' AND entity_id = :eid ORDER BY created_at DESC LIMIT 1;"),
                {"eid": conf.id},
            ).mappings().first()

            assert audit is not None
            assert audit["action"] == "resolution_guidance_requested"
            assert audit["user_id"] == user_id
        finally:
            db.close()

    def test_11_missing_conflict_behaves_safely(self):
        """11. Requesting non-existent conflict returns 404 safely."""
        headers, _ = create_test_user_session()
        random_id = uuid.uuid4()
        resp = client.get(
            f"/api/v1/assistant/resolution-context/{random_id}",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_12_legacy_generic_assistant_chat_works_without_conflict_id(self):
        """12. Assistant continues to function for generic inquiries without conflict_id."""
        headers, user_id = create_test_user_session()
        resp = client.post(
            "/api/v1/assistant/chat",
            headers=headers,
            json={
                "message": "Which documents can prove my date of birth for EPFO update?",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "conversation_id" in data
        assert "message_id" in data
        assert "response" in data
