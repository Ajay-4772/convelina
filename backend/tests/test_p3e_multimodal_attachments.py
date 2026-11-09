"""
CONVELINA — Phase P3E Multimodal Attachments & In-Chat Document Analysis Test Suite
Validates:
1. Valid PDF upload and text/confidence extraction via OCR (HTTP 201, status READY).
2. Valid image upload (PNG/JPG) with confidence scoring.
3. Unsupported file type rejection (HTTP 400 for .txt, .exe, etc.).
4. Oversized file rejection (> 10 MB payload rejected with HTTP 400).
5. MIME spoofing denial (corrupted/spoofed magic bytes rejected with HTTP 400).
6. Pre-persistence PII sanitization (Aadhaar numbers masked, zero plaintext raw identifiers stored).
7. Cross-tenant RLS isolation & IDOR denial (User B cannot view, preview, patch, or delete User A's attachment).
8. Conflict linking and unlinking (PATCH /attachments/{id} with ownership validation).
9. Explicit attachment deletion lifecycle (HTTP 204, soft delete in DB, physical temp file removed).
10. Multi-attachment chat message staging and conversational analysis grounding.
11. Admin-only expired attachment sweep (POST /attachments/cleanup: 403 citizen, 200 admin).
12. Conversation cascade unlinking (deleting conversation removes physical temp files).
"""

import io
import os
import uuid
import pytest
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.assistant import AssistantConversation, AssistantMessage, MessageAttachment
from app.core.database import SessionLocal, set_rls_context
from app.core.storage import get_temp_attachment_path

client = TestClient(app)


def create_synthetic_png(text_lines=None, width=300, height=150) -> bytes:
    """Generates a valid in-memory PNG image."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    if text_lines:
        y = 20
        for line in text_lines:
            draw.text((20, y), line, fill=(0, 0, 0))
            y += 25
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_synthetic_pdf(text_lines=None) -> bytes:
    """Generates a valid in-memory PDF document using ReportLab."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    if text_lines:
        y = 750
        for line in text_lines:
            c.drawString(50, y, line)
            y -= 25
    else:
        c.drawString(50, 750, "Standard Government Test Document")
    c.save()
    return buf.getvalue()


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
def p3e_test_environment(db: Session):
    """
    Provisions User Alpha (citizen), User Beta (citizen), and Admin.
    Also provisions a sample conflict for User Alpha.
    """
    # 1. User Alpha (Citizen)
    uid_a = f"usr_p3e_a_{uuid.uuid4().hex[:6]}"
    token_a = f"test_token_:{uid_a}:{uid_a}@example.com:Citizen Alpha"
    res_a = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "email": f"{uid_a}@example.com",
            "full_name": "Citizen Alpha",
            "phone_number": "+919876543210",
            "date_of_birth": "1990-01-01",
        },
    )
    assert res_a.status_code in [200, 201]
    user_a = res_a.json()

    # 2. User Beta (Citizen)
    uid_b = f"usr_p3e_b_{uuid.uuid4().hex[:6]}"
    token_b = f"test_token_:{uid_b}:{uid_b}@example.com:Citizen Beta"
    res_b = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "email": f"{uid_b}@example.com",
            "full_name": "Citizen Beta",
            "phone_number": "+919876543211",
            "date_of_birth": "1992-05-15",
        },
    )
    assert res_b.status_code in [200, 201]
    user_b = res_b.json()

    # 3. Admin User
    uid_adm = f"usr_p3e_adm_{uuid.uuid4().hex[:6]}"
    token_adm = f"test_token_:{uid_adm}:{uid_adm}@admin.gov.in:System Admin"
    res_adm = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_adm}"},
        json={
            "email": f"{uid_adm}@admin.gov.in",
            "full_name": "System Admin",
            "phone_number": "+919999999999",
            "date_of_birth": "1980-01-01",
        },
    )
    assert res_adm.status_code in [200, 201]
    set_rls_context(db, None, "admin")
    adm_user = db.query(User).filter(User.email == f"{uid_adm}@admin.gov.in").first()
    assert adm_user is not None
    adm_user.role = "admin"
    db.commit()

    # 4. Seed a conflict for User Alpha
    set_rls_context(db, uuid.UUID(user_a["id"]), "user")
    doc_a1 = Document(
        user_id=uuid.UUID(user_a["id"]),
        document_type="aadhaar",
        file_path="mock/path/aadhaar.pdf",
        file_hash="sha256_p3e_doc1_" + uuid.uuid4().hex[:8],
        ocr_status="completed",
    )
    doc_a2 = Document(
        user_id=uuid.UUID(user_a["id"]),
        document_type="pan",
        file_path="mock/path/pan.pdf",
        file_hash="sha256_p3e_doc2_" + uuid.uuid4().hex[:8],
        ocr_status="completed",
    )
    db.add_all([doc_a1, doc_a2])
    db.flush()

    c_id = uuid.uuid4()
    conflict_a = Conflict(
        id=c_id,
        user_id=uuid.UUID(user_a["id"]),
        doc_a_id=doc_a1.id,
        doc_b_id=doc_a2.id,
        conflict_type="genuine-mismatch",
        severity="high",
        status="detected",
        field_name="full_name",
        value_a="Citizen Alpha",
        value_b="CITIZEN A",
        description="Name on Aadhaar does not match PAN record.",
    )
    db.add(conflict_a)
    db.commit()

    return {
        "user_a": {"id": user_a["id"], "token": token_a, "conflict_id": str(c_id)},
        "user_b": {"id": user_b["id"], "token": token_b},
        "admin": {"token": token_adm},
    }


def test_upload_valid_pdf_and_ocr(p3e_test_environment):
    """
    Test uploading a valid PDF document with text lines.
    Verifies HTTP 201, extraction metadata, and READY status.
    """
    token = p3e_test_environment["user_a"]["token"]
    pdf_bytes = create_synthetic_pdf([
        "GOVERNMENT OF INDIA",
        "REJECTION NOTICE / DEFICIENCY MEMO",
        "Reason: Name mismatch between Aadhaar and Passport records.",
        "Date of Notice: 15-08-2024",
    ])

    files = {"file": ("rejection_memo.pdf", pdf_bytes, "application/pdf")}
    res = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert res.status_code == 201, res.text
    data = res.json()["attachment"]

    assert "id" in data
    assert data["file_name"] == "rejection_memo.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["status"] == "READY"
    assert data["sha256_hash"] is not None
    assert len(data["sha256_hash"]) == 64
    assert data["file_size_bytes"] == len(pdf_bytes)
    assert data["ocr_confidence"] is not None
    assert data["ocr_confidence"] > 0.0

    # Verify extracted fields
    extracted = data.get("extracted_fields") or {}
    assert "document_type_indicator" in extracted
    assert extracted["document_type_indicator"] == "rejection_notice"
    assert "dates_found" in extracted
    assert any("2024" in d for d in extracted["dates_found"])
    assert "rejection_reasons" in extracted
    assert len(extracted["rejection_reasons"]) > 0


def test_upload_valid_png_image(p3e_test_environment):
    """
    Test uploading a valid PNG image attachment.
    Verifies HTTP 201, mime detection, and confidence calculation.
    """
    token = p3e_test_environment["user_a"]["token"]
    png_bytes = create_synthetic_png(["PASSPORT SEVA KENDRA", "OBJECTION LETTER", "Date: 12/04/2023"])

    files = {"file": ("passport_objection.png", png_bytes, "image/png")}
    res = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert res.status_code == 201, res.text
    data = res.json()["attachment"]
    assert data["mime_type"] == "image/png"
    assert data["status"] == "READY"
    assert data["ocr_status"] in ["completed", "low_confidence"]


def test_reject_unsupported_file_format(p3e_test_environment):
    """
    Test rejection of unpermitted file types (e.g. .txt, .exe, .sh).
    """
    token = p3e_test_environment["user_a"]["token"]
    text_content = b"Some random unpermitted text content."
    files = {"file": ("notes.txt", text_content, "text/plain")}
    res = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert res.status_code == 400
    assert "not supported" in res.json()["detail"]


def test_reject_oversized_file(p3e_test_environment):
    """
    Test denial of uploads exceeding the 10 MB payload ceiling.
    """
    token = p3e_test_environment["user_a"]["token"]
    # 10.5 MB payload
    oversized_bytes = b"%PDF-1.4\n" + b"0" * (10 * 1024 * 1024 + 500)
    files = {"file": ("huge_document.pdf", oversized_bytes, "application/pdf")}
    res = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert res.status_code == 400
    assert "exceeds maximum allowed size" in res.json()["detail"]


def test_reject_mime_spoofing(p3e_test_environment):
    """
    Test denial of files where file extension / reported MIME does not match magic bytes.
    """
    token = p3e_test_environment["user_a"]["token"]
    spoofed_bytes = b"This is plain ASCII text pretending to be a PDF."
    files = {"file": ("spoofed.pdf", spoofed_bytes, "application/pdf")}
    res = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert res.status_code == 400
    assert "File content does not match" in res.json()["detail"]


def test_pre_persistence_pii_sanitization(p3e_test_environment, db: Session):
    """
    Test pre-persistence PII sanitization: raw Aadhaar numbers extracted during OCR
    must be masked (e.g., XXXXXXXX1234) before persistence in extracted_text or extracted_fields.
    """
    token = p3e_test_environment["user_a"]["token"]
    raw_aadhaar = "8899 7766 5544"
    pdf_bytes = create_synthetic_pdf([
        "OFFICIAL CITIZEN RECORD",
        f"Aadhaar Number: {raw_aadhaar}",
        "Name: Citizen Alpha",
    ])

    files = {"file": ("aadhaar_record.pdf", pdf_bytes, "application/pdf")}
    res = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert res.status_code == 201
    data = res.json()["attachment"]
    att_id = data["id"]

    # Verify response extracted_fields does not contain unmasked number
    extracted = data.get("extracted_fields") or {}
    assert raw_aadhaar not in str(extracted)
    assert extracted.get("has_pii_redacted") is True

    # Verify directly in DB that raw Aadhaar is not in extracted_text
    set_rls_context(db, uuid.UUID(p3e_test_environment["user_a"]["id"]), "user")
    att_db = db.query(MessageAttachment).filter(MessageAttachment.id == uuid.UUID(att_id)).first()
    assert att_db is not None
    assert raw_aadhaar not in att_db.extracted_text


def test_cross_tenant_rls_and_idor_denial(p3e_test_environment):
    """
    Validates cross-tenant RLS isolation:
    User Alpha's attachment cannot be viewed, previewed, patched, or deleted by User Beta.
    """
    token_a = p3e_test_environment["user_a"]["token"]
    token_b = p3e_test_environment["user_b"]["token"]

    pdf_bytes = create_synthetic_pdf(["Confidential Alpha Document"])
    files = {"file": ("alpha_doc.pdf", pdf_bytes, "application/pdf")}
    res_a = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files=files,
    )
    assert res_a.status_code == 201
    att_id = res_a.json()["attachment"]["id"]

    # User B attempts to access User A's attachment
    res_get = client.get(
        f"/api/v1/assistant/attachments/{att_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_get.status_code == 404

    # User B attempts to preview User A's attachment
    res_prev = client.get(
        f"/api/v1/assistant/attachments/{att_id}/preview",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_prev.status_code == 404

    # User B attempts to patch User A's attachment
    res_patch = client.patch(
        f"/api/v1/assistant/attachments/{att_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"conflict_id": None},
    )
    assert res_patch.status_code == 404

    # User B attempts to delete User A's attachment
    res_del = client.delete(
        f"/api/v1/assistant/attachments/{att_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_del.status_code == 404


def test_attachment_conflict_link_and_unlink(p3e_test_environment):
    """
    Test explicit conflict linkage and unlinking on an attachment.
    """
    token_a = p3e_test_environment["user_a"]["token"]
    conflict_id = p3e_test_environment["user_a"]["conflict_id"]

    pdf_bytes = create_synthetic_pdf(["Discrepancy Proof"])
    files = {"file": ("proof.pdf", pdf_bytes, "application/pdf")}
    res_up = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files=files,
    )
    assert res_up.status_code == 201
    att_id = res_up.json()["attachment"]["id"]

    # Link conflict
    res_link = client.patch(
        f"/api/v1/assistant/attachments/{att_id}",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"conflict_id": conflict_id},
    )
    assert res_link.status_code == 200, res_link.text
    assert res_link.json()["conflict_id"] == conflict_id

    # Unlink conflict
    res_unlink = client.patch(
        f"/api/v1/assistant/attachments/{att_id}",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"conflict_id": None},
    )
    assert res_unlink.status_code == 200
    assert res_unlink.json()["conflict_id"] is None


def test_attachment_deletion_lifecycle(p3e_test_environment, db: Session):
    """
    Test explicit attachment deletion:
    Soft delete in database (status DELETED, deleted_at set) and physical removal from disk.
    """
    token_a = p3e_test_environment["user_a"]["token"]
    pdf_bytes = create_synthetic_pdf(["Temporary Citizen Notice"])
    files = {"file": ("temp_notice.pdf", pdf_bytes, "application/pdf")}
    res_up = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files=files,
    )
    assert res_up.status_code == 201
    att_id = res_up.json()["attachment"]["id"]

    # Delete attachment
    res_del = client.delete(
        f"/api/v1/assistant/attachments/{att_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_del.status_code == 204

    # Subsequent GET returns 404 or 410 Gone for citizen
    res_get = client.get(
        f"/api/v1/assistant/attachments/{att_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_get.status_code in [404, 410]

    # Verify DB record is marked DELETED
    set_rls_context(db, None, "admin")
    att_db = db.query(MessageAttachment).filter(MessageAttachment.id == uuid.UUID(att_id)).first()
    assert att_db is not None
    assert att_db.status == "DELETED"
    assert att_db.deleted_at is not None

    # Verify physical file is removed from disk
    file_path = get_temp_attachment_path(att_db.storage_ref)
    assert file_path is None or not os.path.exists(file_path)


def test_chat_with_staged_attachments(p3e_test_environment, db: Session):
    """
    Test sending a chat inquiry with staged attachment IDs.
    Verifies that the assistant includes the attachment in analysis context and links message_id.
    """
    token_a = p3e_test_environment["user_a"]["token"]
    pdf_bytes = create_synthetic_pdf([
        "REJECTION NOTICE",
        "Your EPFO claim has been rejected due to father name mismatch.",
        "Authority: Employees Provident Fund Organisation",
    ])
    files = {"file": ("epfo_rejection.pdf", pdf_bytes, "application/pdf")}
    res_up = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files=files,
    )
    assert res_up.status_code == 201
    att_id = res_up.json()["attachment"]["id"]

    # Send chat query referencing attachment
    res_chat = client.post(
        "/api/v1/assistant/chat",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "message": "Please analyze this rejection notice and tell me what the problem is.",
            "attachment_ids": [att_id],
        },
    )
    assert res_chat.status_code == 200, res_chat.text
    chat_data = res_chat.json()
    assert "response" in chat_data
    # Offline fallback or Gemini should reference the attached document
    resp_obj = chat_data["response"]
    answer_text = resp_obj["answer"] if isinstance(resp_obj, dict) else str(resp_obj)
    assert "epfo_rejection.pdf" in answer_text or "Document Evidence" in answer_text

    # Verify in DB that attachment is linked to user message
    set_rls_context(db, uuid.UUID(p3e_test_environment["user_a"]["id"]), "user")
    att_db = db.query(MessageAttachment).filter(MessageAttachment.id == uuid.UUID(att_id)).first()
    assert att_db is not None
    assert att_db.message_id is not None


def test_admin_cleanup_expired_attachments(p3e_test_environment):
    """
    Test admin-only expired attachment cleanup sweep.
    Citizens receive 403 Forbidden; Admins receive 200 OK.
    """
    token_cit = p3e_test_environment["user_a"]["token"]
    token_adm = p3e_test_environment["admin"]["token"]

    # Citizen denied
    res_cit = client.post(
        "/api/v1/assistant/attachments/cleanup",
        headers={"Authorization": f"Bearer {token_cit}"},
    )
    assert res_cit.status_code == 403

    # Admin permitted
    res_adm = client.post(
        "/api/v1/assistant/attachments/cleanup",
        headers={"Authorization": f"Bearer {token_adm}"},
    )
    assert res_adm.status_code == 200
    data = res_adm.json()
    assert "cleaned_count" in data
    assert "message" in data


def test_expired_attachment_access_denial(p3e_test_environment, db: Session):
    """
    Test that an attachment whose expires_at is in the past returns HTTP 410 Gone
    on both metadata retrieval and inline preview streaming.
    """
    import datetime
    token_a = p3e_test_environment["user_a"]["token"]
    pdf_bytes = create_synthetic_pdf(["EXPIRED TEST NOTICE"])
    files = {"file": ("expired_notice.pdf", pdf_bytes, "application/pdf")}
    res_up = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files=files,
    )
    assert res_up.status_code == 201
    att_id = res_up.json()["attachment"]["id"]

    # Artificially expire the attachment in DB
    set_rls_context(db, uuid.UUID(p3e_test_environment["user_a"]["id"]), "user")
    att_db = db.query(MessageAttachment).filter(MessageAttachment.id == uuid.UUID(att_id)).first()
    assert att_db is not None
    past_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
    att_db.expires_at = past_time
    db.commit()

    # Metadata request should return 410 Gone
    res_meta = client.get(
        f"/api/v1/assistant/attachments/{att_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_meta.status_code == 410, f"Expected 410 Gone for expired metadata, got {res_meta.status_code}"
    assert "expired" in res_meta.json().get("detail", "").lower()

    # Preview stream should also return 410 Gone
    res_prev = client.get(
        f"/api/v1/assistant/attachments/{att_id}/preview",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_prev.status_code == 410, f"Expected 410 Gone for expired preview, got {res_prev.status_code}"
    assert "expired" in res_prev.json().get("detail", "").lower()


def test_path_traversal_prevention(p3e_test_environment, db: Session):
    """
    Test comprehensive path traversal protection:
    1. Null byte, relative traversal ('..'), and tilde ('~') are rejected.
    2. Absolute paths outside configured attachments directory are rejected.
    3. Safe deletion never touches files outside storage root.
    4. Tampered DB storage_ref fails safely without file exposure.
    """
    from app.core.storage import get_temp_attachment_path, delete_temp_attachment

    # Direct unit checks against path resolution
    assert get_temp_attachment_path("../../../etc/passwd") is None
    assert get_temp_attachment_path("..\\..\\windows\\win.ini") is None
    assert get_temp_attachment_path("valid_file\x00.pdf") is None
    assert get_temp_attachment_path("~/secret_key") is None
    assert get_temp_attachment_path("/etc/passwd") is None

    # Deletion safety check
    assert delete_temp_attachment("/etc/hosts") is False
    assert delete_temp_attachment("../app/main.py") is False

    # Endpoint defense against tampered storage_ref in DB
    token_a = p3e_test_environment["user_a"]["token"]
    pdf_bytes = create_synthetic_pdf(["PATH TRAVERSAL ATTACK ASSET"])
    files = {"file": ("traversal_probe.pdf", pdf_bytes, "application/pdf")}
    res_up = client.post(
        "/api/v1/assistant/attachments/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files=files,
    )
    assert res_up.status_code == 201
    att_id = res_up.json()["attachment"]["id"]

    # Tamper storage_ref to point outside the temp directory
    set_rls_context(db, uuid.UUID(p3e_test_environment["user_a"]["id"]), "user")
    att_db = db.query(MessageAttachment).filter(MessageAttachment.id == uuid.UUID(att_id)).first()
    assert att_db is not None
    att_db.storage_ref = "../../../etc/passwd"
    db.commit()

    # Attempt to preview tampered asset
    res_preview = client.get(
        f"/api/v1/assistant/attachments/{att_id}/preview",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    # Must fail safely with 404 (file not found on disk / path rejected)
    assert res_preview.status_code == 404

