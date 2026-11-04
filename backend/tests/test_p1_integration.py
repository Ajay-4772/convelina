"""
CONVELINA - Phase P1 Real Document Processing & Conflict Analysis Integration Suite
Tests the complete user journey and integration requirements:
1. Upload-ready document comparison endpoint
2. Exact match
3. Format-only difference
4. Ambiguous initials
5. Gender-aware mismatch
6. Truncation
7. Low OCR confidence fail-safe
8. Unsupported script fail-safe
9. Missing extraction fields
10. Cross-user document access attempt
11. User attempting to compare another user's document
12. Admin authorization boundaries
13. E2E Demonstration Flow 1: LIKELY_SAME_PERSON (M Ajay vs Ajay M + DOB + Father)
14. E2E Demonstration Flow 2: Father Name Truncation (Muthu vs Muthukumar)
15. Canonical DocumentIdentityProfile Endpoint
16. Document not ready rejected (ocr_status != 'completed')
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from sqlalchemy import text
from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.document import Document
from app.models.conflict import Conflict
from app.services.identity_matching.classification import (
    NameMatchClassification,
    OverallIdentityClassification,
)

client = TestClient(app)


def create_test_user_session(role: str = "user"):
    """Helper to provision a synthetic user and return auth headers and UUID."""
    uid = f"p1_{uuid.uuid4().hex[:8]}"
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


class TestP1IntegrationWorkflow:
    """Comprehensive integration battery for Phase P1."""

    def test_01_upload_ready_document_comparison_endpoint(self):
        """1. Basic document comparison endpoint invocation."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "Ajay Kumar", "date_of_birth": "1995-05-15"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay Kumar", "date_of_birth": "1995-05-15"})

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_classification"] == "EXACT_MATCH"
        assert len(data["documents_compared"]) == 2
        assert "AUTOMATED COMPARISON RESULT" in data["disclaimer"]

    def test_02_exact_match(self):
        """2. Exact match produces EXACT_MATCH, 0 conflicts, no action recommended."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "Rohan Sharma", "date_of_birth": "1990-01-01"})
        doc2 = seed_document(user_id, "passport", {"full_name": "Rohan Sharma", "date_of_birth": "1990-01-01"})

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_classification"] == "EXACT_MATCH"
        assert data["confidence_score"] == 1.0
        assert data["requires_manual_review"] is False
        assert data["action_recommended"] is False
        assert "full_name" in data["matched_fields"]
        assert "date_of_birth" in data["matched_fields"]

    def test_03_format_only_difference(self):
        """3. Case, spacing, or punctuation variations classify as FORMAT_ONLY_MATCH."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "M Ajay", "date_of_birth": "1995-05-15"})
        doc2 = seed_document(user_id, "pan", {"full_name": "M. AJAY", "date_of_birth": "15/05/1995"})

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_classification"] == "FORMAT_ONLY_MATCH"
        assert data["confidence_score"] >= 0.95
        assert data["requires_manual_review"] is False

    def test_04_ambiguous_initials(self):
        """4. Initial vs expanded name in isolation flags AMBIGUOUS_NEEDS_REVIEW."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "pan", {"full_name": "R Karthik"})
        doc2 = seed_document(user_id, "passport", {"full_name": "Karthik Raman"})

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_classification"] == "AMBIGUOUS_NEEDS_REVIEW"
        assert data["requires_manual_review"] is True
        assert data["action_recommended"] is True
        assert "full_name" in data["ambiguous_fields"]

    def test_05_gender_aware_mismatch(self):
        """5. Gender-differentiated pairs (Deepak vs Deepika) MUST trigger GENUINE MISMATCH with critical severity."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "Deepak Kumar"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Deepika Kumar"})

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_classification"] == "MISMATCH"
        assert data["requires_manual_review"] is True
        assert data["action_recommended"] is True
        assert "full_name" in data["conflicting_fields"]

    def test_06_truncation(self):
        """6. Truncated names (Muthu vs Muthukumar) classify as TRUNCATION_OR_PARTIAL_MATCH."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "education_10th", {"full_name": "Muthu"})
        doc2 = seed_document(user_id, "passport", {"full_name": "Muthukumar"})

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_classification"] == "TRUNCATION_OR_PARTIAL_MATCH"
        assert data["requires_manual_review"] is True

    def test_07_low_ocr_confidence(self):
        """7. Low OCR confidence (< 60%) triggers LOW_CONFIDENCE_NEEDS_REVIEW."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(
            user_id,
            "aadhaar",
            {"full_name": "Ajay Kumar", "overall_ocr_confidence": 0.45},
        )
        doc2 = seed_document(
            user_id,
            "pan",
            {"full_name": "Ajay Kumar", "overall_ocr_confidence": 0.95},
        )

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_classification"] == "LOW_CONFIDENCE_NEEDS_REVIEW"
        assert data["requires_manual_review"] is True
        assert any("60%" in w or "confidence" in w.lower() for w in data["warnings"] + [data["explanation"]])

    def test_08_unsupported_script(self):
        """8. Non-Latin Indic script flags UNRESOLVABLE_NEEDS_MANUAL_REVIEW."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "அஜய் குமார்"})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay Kumar"})

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_classification"] == "UNRESOLVABLE_NEEDS_MANUAL_REVIEW"
        assert data["requires_manual_review"] is True

    def test_09_missing_extraction_fields(self):
        """9. Missing demographic fields are safely handled without throwing an internal 500 error."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {})
        doc2 = seed_document(user_id, "pan", {"full_name": "Ajay Kumar"})

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "INSUFFICIENT_DATA" in data["field_results"]["full_name"]["classification"]

    def test_10_cross_user_document_access_attempt(self):
        """10. User 2 attempting to directly retrieve User 1's document or profile is blocked with 404."""
        headers_u1, u1_id = create_test_user_session()
        headers_u2, _ = create_test_user_session()

        doc_u1 = seed_document(u1_id, "aadhaar", {"full_name": "User One"})

        # User 2 attempts to fetch doc_u1
        get_resp = client.get(f"/api/v1/documents/{doc_u1.id}", headers=headers_u2)
        assert get_resp.status_code == 404

        # User 2 attempts to fetch profile of doc_u1
        prof_resp = client.get(f"/api/v1/documents/{doc_u1.id}/profile", headers=headers_u2)
        assert prof_resp.status_code == 404

    def test_11_user_attempting_to_compare_another_users_document(self):
        """11. User 2 attempting to compare their document with User 1's document MUST fail with 404/403."""
        headers_u1, u1_id = create_test_user_session()
        headers_u2, u2_id = create_test_user_session()

        doc_u1 = seed_document(u1_id, "aadhaar", {"full_name": "Citizen One"})
        doc_u2 = seed_document(u2_id, "pan", {"full_name": "Citizen Two"})

        # User 2 submits comparison request with their doc + User 1's doc
        comp_resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers_u2,
            json={"document_ids": [str(doc_u2.id), str(doc_u1.id)]},
        )
        assert comp_resp.status_code in (403, 404)
        assert "access denied" in comp_resp.json()["detail"].lower() or "not found" in comp_resp.json()["detail"].lower()

    def test_12_admin_authorization_boundaries(self):
        """12. Normal user is forbidden from admin endpoints; Admin is authorized."""
        headers_user, _ = create_test_user_session(role="user")
        admin_headers, admin_id = create_test_user_session(role="admin")

        # Promote admin_id to admin role in database via authorized context
        db = SessionLocal()
        db.execute(text("SET LOCAL app.current_user_role = 'admin';"))
        db.execute(text("UPDATE users SET role = 'admin' WHERE id = :uid;"), {"uid": str(admin_id)})
        db.commit()
        db.close()

        # Normal user accessing admin overview-stats -> 403 Forbidden
        u_resp = client.get("/api/v1/admin/overview-stats", headers=headers_user)
        assert u_resp.status_code == 403

        # Admin user accessing admin overview-stats -> 200 OK
        a_resp = client.get("/api/v1/admin/overview-stats", headers=admin_headers)
        assert a_resp.status_code == 200
        assert "users" in a_resp.json()
        assert "total" in a_resp.json()["users"]

    def test_13_demonstration_flow_1_likely_same_person(self):
        """
        13. Demonstration Flow 1:
        Doc A: Name: M Ajay, DOB: 1995-05-15, Father: Muthukumar
        Doc B: Name: Ajay M, DOB: 15/05/1995, Father: Muthukumar
        Expected: LIKELY_SAME_PERSON (corroborated by DOB and Father Name)
        """
        headers, user_id = create_test_user_session()
        doc_a = seed_document(
            user_id,
            "passport",
            {
                "full_name": "M Ajay",
                "date_of_birth": "1995-05-15",
                "father_name": "Muthukumar",
            },
        )
        doc_b = seed_document(
            user_id,
            "aadhaar",
            {
                "full_name": "Ajay M",
                "date_of_birth": "15/05/1995",
                "father_name": "Muthukumar",
            },
        )

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc_a.id), str(doc_b.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_classification"] == "LIKELY_SAME_PERSON"
        assert data["confidence_score"] >= 0.90
        assert data["requires_manual_review"] is False
        assert any("father" in ev.lower() or "birth" in ev.lower() for ev in data["evidence"])

    def test_14_demonstration_flow_2_father_truncation(self):
        """
        14. Demonstration Flow 2:
        Doc A: Father: Muthu
        Doc B: Father: Muthukumar
        Expected: Truncation variation flagged with review recommendation.
        """
        headers, user_id = create_test_user_session()
        doc_a = seed_document(
            user_id,
            "pan",
            {"full_name": "Ajay Kumar", "father_name": "Muthu"},
        )
        doc_b = seed_document(
            user_id,
            "passport",
            {"full_name": "Ajay Kumar", "father_name": "Muthukumar"},
        )

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc_a.id), str(doc_b.id)]},
        )
        assert resp.status_code == 200
        data = resp.json()
        father_res = data["field_results"].get("father_name")
        assert father_res is not None
        assert father_res["classification"] == "TRUNCATION_OR_PARTIAL_MATCH"
        assert father_res["requires_manual_review"] is True

    def test_15_document_profile_endpoint(self):
        """15. GET /api/v1/documents/{id}/profile returns canonical DocumentIdentityProfile."""
        headers, user_id = create_test_user_session()
        doc = seed_document(
            user_id,
            "aadhaar",
            {
                "full_name": "Kumari Selvi M",
                "date_of_birth": "2000-08-15",
                "gender": "Female",
            },
        )

        resp = client.get(f"/api/v1/documents/{doc.id}/profile", headers=headers)
        assert resp.status_code == 200
        profile = resp.json()

        # Raw values preserved
        assert profile["full_name_raw"] == "Kumari Selvi M"
        assert profile["date_of_birth_raw"] == "2000-08-15"

        # Normalized values derived
        assert profile["date_of_birth_normalized"] == "2000-08-15"
        assert profile["birth_year"] == 2000
        assert "kumari" in profile["name_tokens"]
        assert "selvi" in profile["name_tokens"]
        assert "m" in profile["initials"]

    def test_16_not_ready_document_rejected(self):
        """16. Document with ocr_status != 'completed' is rejected from comparison with HTTP 400."""
        headers, user_id = create_test_user_session()
        doc1 = seed_document(user_id, "aadhaar", {"full_name": "Ajay Kumar"}, ocr_status="completed")
        doc2 = seed_document(user_id, "pan", {}, ocr_status="pending")

        resp = client.post(
            "/api/v1/conflicts/compare",
            headers=headers,
            json={"document_ids": [str(doc1.id), str(doc2.id)]},
        )
        assert resp.status_code == 400
        assert "not ready" in resp.json()["detail"].lower()

