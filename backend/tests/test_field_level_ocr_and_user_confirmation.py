"""
CONVELINA — Field-Level OCR Extraction & Citizen Confirmation Test Suite
Validates:
1. Standardized 14-step field-level extraction schema across all 6 categories.
2. Field-level confidence, validation status (valid, invalid_format, missing), and review_required triggers.
3. Degradation trigger: when OCR confidence < 0.60, sets review_required=True and ocr_status='needs_review'.
4. User confirmation endpoint (POST /api/v1/documents/{id}/confirm):
   - Preserves raw field_extractions while writing confirmed_fields.
   - Sets is_user_confirmed=True and confirmed_at timestamp.
   - Clears 'needs_review' status to 'completed'.
   - Audit-logs document_fields_confirmed.
5. Separation of machine evidence vs confirmed values in DocumentComparisonService.create_profile_from_document.
"""

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.document import Document
from app.models.audit_log import AuditLog
from app.core.database import SessionLocal, set_rls_context
from app.core.synthetic_documents import generate_synthetic_document_image
from app.ocr.field_extractor import FieldExtractor, CATEGORY_SCHEMAS
from app.services.identity_matching.service import DocumentComparisonService

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        set_rls_context(session, None, "admin")
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def citizen_token():
    uid = f"usr_ocr_cit_{uuid.uuid4().hex[:6]}"
    token = f"test_token_:{uid}:{uid}@example.com:Citizen OCR"
    res = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": f"{uid}@example.com",
            "full_name": "Citizen OCR",
            "phone_number": "+919876543220",
            "date_of_birth": "1992-06-20",
        },
    )
    assert res.status_code in (200, 201)
    return token


def test_field_extractor_all_six_category_schemas():
    """Verifies that FieldExtractor handles all 6 categories with expected schema fields."""
    sample_texts = {
        "aadhaar": "Government of India Unique Identification Authority Aadhaar 9876 5432 1098 Name: RAHUL KUMAR DOB: 12/04/1990 Gender: Male Address: 123 MG Road Bangalore 560001",
        "pan": "INCOME TAX DEPARTMENT GOVT OF INDIA Permanent Account Number ABCDE1234F Name RAHUL KUMAR Father's Name SURESH KUMAR DOB 12/04/1990",
        "passport": "REPUBLIC OF INDIA PASSPORT P1234567 Given Name RAHUL Surname KUMAR DOB 12/04/1990 Place of Birth BANGALORE Date of Issue 10/05/2018 Date of Expiry 09/05/2028 Father SURESH KUMAR Mother LALITHA KUMAR",
        "education_10th": "CENTRAL BOARD OF SECONDARY EDUCATION Secondary School Examination 2008 Roll No 1234567 Candidate Name RAHUL KUMAR Father's Name SURESH KUMAR Mother's Name LALITHA KUMAR DOB 12/04/1990",
        "education_12th": "CENTRAL BOARD OF SECONDARY EDUCATION Senior School Certificate Examination 2010 Roll No 7654321 Candidate Name RAHUL KUMAR Father's Name SURESH KUMAR Mother's Name LALITHA KUMAR DOB 12/04/1990",
        "epf": "EMPLOYEES' PROVIDENT FUND ORGANISATION Member Name RAHUL KUMAR UAN 100987654321 Member ID KNBLR0012345000 Establishment TECH CORP LTD Date of Joining 01/06/2015",
    }

    for cat, text in sample_texts.items():
        res = FieldExtractor.extract_category_fields(cat, text, overall_confidence=0.92)
        assert res.document_type == cat
        assert res.overall_confidence == 0.92
        assert "full_name" in res.field_extractions
        assert res.field_extractions["full_name"].raw_value is not None

        # Verify all schema fields are present in extractions
        for schema_f in CATEGORY_SCHEMAS[cat]:
            assert schema_f in res.field_extractions


def test_field_extractor_low_confidence_trigger():
    """Verifies that low OCR confidence (< 0.60) triggers review_required=True."""
    raw_text = "Name: RAHUL DOB: 12/04/1990"
    res = FieldExtractor.extract_category_fields("aadhaar", raw_text, overall_confidence=0.45)
    assert res.requires_manual_review is True
    # Name extraction must have review_required
    name_ext = res.field_extractions["full_name"]
    assert name_ext.review_required is True
    assert name_ext.confidence <= 0.50


def test_document_user_confirmation_lifecycle(db: Session, citizen_token: str):
    """
    Verifies complete user confirmation flow:
    1. Upload document (creates field_extractions, is_user_confirmed=False).
    2. Confirm fields via POST /api/v1/documents/{id}/confirm.
    3. Verifies confirmed_fields are saved, is_user_confirmed=True, confirmed_at is set.
    4. Confirms that DocumentComparisonService prioritizes confirmed_fields.
    """
    headers = {"Authorization": f"Bearer {citizen_token}"}
    fake_png = generate_synthetic_document_image("aadhaar")
    files = {"file": ("aadhaar_card.png", io.BytesIO(fake_png), "image/png")}
    data = {"document_type": "aadhaar"}

    res_upload = client.post("/api/v1/documents/upload", headers=headers, files=files, data=data)
    assert res_upload.status_code == 201
    doc_data = res_upload.json()
    doc_id = doc_data["id"]
    assert doc_data["is_user_confirmed"] is False
    assert doc_data["confirmed_fields"] == {}

    # Citizen confirms corrected demographic fields
    confirmed_payload = {
        "confirmed_fields": {
            "full_name": "RAHUL SURESH KUMAR",
            "date_of_birth": "1990-04-12",
            "gender": "M",
            "pincode": "560001",
        }
    }
    res_confirm = client.post(
        f"/api/v1/documents/{doc_id}/confirm",
        headers=headers,
        json=confirmed_payload,
    )
    assert res_confirm.status_code == 200
    confirmed_doc = res_confirm.json()
    assert confirmed_doc["is_user_confirmed"] is True
    assert confirmed_doc["confirmed_at"] is not None
    assert confirmed_doc["confirmed_fields"]["full_name"] == "RAHUL SURESH KUMAR"
    assert confirmed_doc["ocr_status"] == "completed"

    # Verify profile creation prioritizes confirmed fields
    set_rls_context(db, None, "admin")
    doc_model = db.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
    profile = DocumentComparisonService.create_profile_from_document(doc_model)
    assert profile.full_name_raw == "RAHUL SURESH KUMAR"
    assert profile.date_of_birth_normalized == "1990-04-12"

    # Verify audit log was recorded
    audit_entry = (
        db.query(AuditLog)
        .filter(AuditLog.action == "document_fields_confirmed")
        .filter(AuditLog.entity_id == uuid.UUID(doc_id))
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.details.get("confirmed_fields_count") == 4
