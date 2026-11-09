"""
CONVELINA — Phase P3D.1 Official Form Authenticity & Security Audit Test Suite

Validates:
1. ReportLab-generated PDFs CANNOT receive OFFICIAL_ORIGINAL or OFFICIAL_COPY status (HTTP 400).
2. Synthetic and application-generated documents CANNOT appear as verified government forms (is_official_government_form is False).
3. Verified original documents require authentic non-ReportLab file and display real source URL.
4. Invalid or missing provenance results in rejection or appropriate downgrade.
5. File hash mismatch prevents download (HTTP 409 File Integrity Failure).
6. Revoked and deactivated forms CANNOT be downloaded by citizens (HTTP 403).
7. Unauthorized (unauthenticated) users CANNOT access protected files (HTTP 401).
8. ADMIN-only verification and provenance changes (RBAC enforcement: 403 for citizens).
9. Path traversal protection on download and preview endpoints.
10. Audit event logging integrity on downloads and verification updates.
"""

import hashlib
import io
import os
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.official_form import OfficialForm
from app.models.audit_log import AuditLog
from app.core.database import SessionLocal, set_rls_context
from app.core.storage import get_official_form_path, save_official_form_asset, ensure_official_forms_dir
from app.rag.forms.catalog import FormCatalogService

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        set_rls_context(session, None, "admin")
        FormCatalogService.sync_seed_forms(session)
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def user_and_admin_tokens(db: Session):
    """
    Provisions a standard citizen user and an administrator.
    """
    uid_citizen = f"usr_audit_cit_{uuid.uuid4().hex[:6]}"
    token_citizen = f"test_token_:{uid_citizen}:{uid_citizen}@example.com:Citizen Audit"
    res_cit = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_citizen}"},
        json={
            "email": f"{uid_citizen}@example.com",
            "full_name": "Citizen Audit",
            "phone_number": "+919876543210",
            "date_of_birth": "1990-01-01",
        },
    )
    assert res_cit.status_code in [200, 201]
    cit_data = res_cit.json()

    # Provision Admin
    uid_admin = f"usr_audit_adm_{uuid.uuid4().hex[:6]}"
    token_admin = f"test_token_:{uid_admin}:{uid_admin}@admin.gov.in:Admin Audit"
    res_adm = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "email": f"{uid_admin}@admin.gov.in",
            "full_name": "Admin Audit",
            "phone_number": "+919999999999",
            "date_of_birth": "1980-01-01",
        },
    )
    assert res_adm.status_code in [200, 201]

    # Elevate admin in DB
    set_rls_context(db, None, "admin")
    admin_user = db.query(User).filter(User.email == f"{uid_admin}@admin.gov.in").first()
    assert admin_user is not None
    admin_user.role = "admin"
    db.commit()

    return {
        "citizen": {
            "token": token_citizen,
            "id": cit_data["id"],
            "email": cit_data["email"],
        },
        "admin": {
            "token": token_admin,
            "id": str(admin_user.id),
            "email": admin_user.email,
        },
    }


def test_reportlab_pdf_cannot_receive_official_original_status(db: Session, user_and_admin_tokens: dict):
    """
    TEST 1: ReportLab-generated PDFs CANNOT receive OFFICIAL_ORIGINAL status.
    Attempting to verify an application-generated ReportLab asset as OFFICIAL_ORIGINAL must raise HTTP 400.
    """
    admin_token = user_and_admin_tokens["admin"]["token"]
    form_id = "form_aadhaar_update_adult"

    # Admin attempts to promote ReportLab asset to OFFICIAL_ORIGINAL
    res = client.put(
        f"/api/v1/knowledge/admin/forms/{form_id}/verification",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "verification_status": "verified",
            "provenance": "OFFICIAL_ORIGINAL",
            "review_notes": "Attempting illegal promotion of ReportLab asset to official original",
        },
    )
    assert res.status_code == 400
    assert "ReportLab" in res.json()["detail"] or "official provenance" in res.json()["detail"]


def test_seeded_forms_classified_as_application_generated(db: Session):
    """
    TEST 2: All 8 seeded forms are honest APPLICATION_GENERATED templates.
    None of them may have is_official_government_form == True or verification_status == 'verified'.
    """
    from app.rag.ingestion.sources import OFFICIAL_FORMS_DATA
    seeded_ids = [item["form_id"] for item in OFFICIAL_FORMS_DATA]
    set_rls_context(db, None, "admin")
    forms = db.query(OfficialForm).filter(OfficialForm.form_id.in_(seeded_ids)).all()
    assert len(forms) == 8

    for form in forms:
        f_dict = form.to_dict()
        assert f_dict["provenance"] in ("APPLICATION_GENERATED", "SYNTHETIC_TEST_ASSET")
        assert f_dict["verification_status"] == "unverified"
        assert f_dict["is_official_government_form"] is False
        assert f_dict["official_download_url"].startswith("http")


def test_verified_original_requires_authentic_non_reportlab_file(db: Session, user_and_admin_tokens: dict):
    """
    TEST 3: Verified original documents require authentic non-ReportLab file and display real source.
    """
    admin_token = user_and_admin_tokens["admin"]["token"]
    set_rls_context(db, None, "admin")

    # 1. Create a genuine non-ReportLab PDF asset
    genuine_pdf_content = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF"
    test_form_id = f"form_test_authentic_{uuid.uuid4().hex[:6]}"
    
    save_official_form_asset(test_form_id, genuine_pdf_content)

    new_form = OfficialForm(
        form_id=test_form_id,
        form_name="Authentic Ministry Circular Form",
        document_category="passport",
        purpose="Authentic government document test",
        issuing_authority="Ministry of External Affairs",
        official_download_url="https://passportindia.gov.in/test.pdf",
        storage_path=f"{test_form_id}.pdf",
        file_size_bytes=len(genuine_pdf_content),
        sha256_hash=hashlib.sha256(genuine_pdf_content).hexdigest(),
        provenance="UNVERIFIED",
        verification_status="unverified",
        is_active=True,
    )
    db.add(new_form)
    db.commit()

    # 2. Promote with authentic file
    res = client.put(
        f"/api/v1/knowledge/admin/forms/{test_form_id}/verification",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "verification_status": "verified",
            "provenance": "OFFICIAL_ORIGINAL",
            "provenance_notes": "Verified authentic official publication.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["provenance"] == "OFFICIAL_ORIGINAL"
    assert data["verification_status"] == "verified"
    assert data["is_official_government_form"] is True
    assert data["official_download_url"] == "https://passportindia.gov.in/test.pdf"


def test_invalid_provenance_rejected(db: Session, user_and_admin_tokens: dict):
    """
    TEST 4: Invalid provenance strings are strictly rejected.
    """
    admin_token = user_and_admin_tokens["admin"]["token"]
    res = client.put(
        "/api/v1/knowledge/admin/forms/form_pan_csf_correction/verification",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "verification_status": "unverified",
            "provenance": "FABRICATED_DOC",
        },
    )
    assert res.status_code == 400
    assert "Invalid provenance" in res.json()["detail"]


def test_file_hash_mismatch_prevents_download(db: Session, user_and_admin_tokens: dict):
    """
    TEST 5: File hash mismatch prevents download (HTTP 409 Conflict / Integrity Failure).
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]
    set_rls_context(db, None, "admin")

    form = db.query(OfficialForm).filter(OfficialForm.form_id == "form_pan_csf_correction").first()
    assert form is not None
    original_hash = form.sha256_hash

    try:
        # Deliberately corrupt the recorded hash in database
        form.sha256_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        db.commit()

        set_rls_context(db, None, "user")
        res = client.get(
            "/api/v1/knowledge/forms/form_pan_csf_correction/download",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert res.status_code == 409
        assert "integrity check failed" in res.json()["detail"].lower()
    finally:
        set_rls_context(db, None, "admin")
        fresh = db.query(OfficialForm).filter(OfficialForm.form_id == "form_pan_csf_correction").first()
        if fresh:
            fresh.sha256_hash = original_hash
            db.commit()


def test_revoked_form_cannot_be_downloaded(db: Session, user_and_admin_tokens: dict):
    """
    TEST 6: Revoked forms CANNOT be downloaded by citizens (HTTP 403 Forbidden).
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]
    admin_token = user_and_admin_tokens["admin"]["token"]
    form_id = "form_epf_joint_declaration"

    set_rls_context(db, None, "admin")
    form = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
    assert form is not None
    original_status = form.verification_status

    try:
        form.verification_status = "revoked"
        db.commit()

        # Citizen attempts to download -> 403
        set_rls_context(db, None, "user")
        res_cit = client.get(
            f"/api/v1/knowledge/forms/{form_id}/download",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert res_cit.status_code == 403
        assert "revoked" in res_cit.json()["detail"].lower()

        # Admin can still inspect / download for audit
        set_rls_context(db, None, "admin")
        res_adm = client.get(
            f"/api/v1/knowledge/forms/{form_id}/download",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res_adm.status_code == 200
    finally:
        set_rls_context(db, None, "admin")
        fresh = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
        if fresh:
            fresh.verification_status = original_status
            db.commit()


def test_deactivated_form_cannot_be_downloaded(db: Session, user_and_admin_tokens: dict):
    """
    TEST 7: Deactivated forms (is_active=False) CANNOT be downloaded by citizens (HTTP 403).
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]
    form_id = "form_passport_reissue"

    set_rls_context(db, None, "admin")
    form = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
    assert form is not None

    try:
        form.is_active = False
        db.commit()

        set_rls_context(db, None, "user")
        res_cit = client.get(
            f"/api/v1/knowledge/forms/{form_id}/download",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        # PostgreSQL Forced RLS filters out inactive rows for non-admins (404), or route rejects (403)
        assert res_cit.status_code in [403, 404]
    finally:
        set_rls_context(db, None, "admin")
        fresh = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
        if fresh:
            fresh.is_active = True
            db.commit()


def test_unauthorized_users_cannot_access_protected_files():
    """
    TEST 8: Unauthenticated users CANNOT download or preview forms (HTTP 401).
    """
    res_dl = client.get("/api/v1/knowledge/forms/form_aadhaar_update_adult/download")
    assert res_dl.status_code == 401

    res_prev = client.get("/api/v1/knowledge/forms/form_aadhaar_update_adult/preview")
    assert res_prev.status_code == 401


def test_admin_only_verification_changes(db: Session, user_and_admin_tokens: dict):
    """
    TEST 9: Regular citizens CANNOT modify verification status or provenance (HTTP 403).
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]
    res = client.put(
        "/api/v1/knowledge/admin/forms/form_aadhaar_update_adult/verification",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={
            "verification_status": "verified",
            "provenance": "OFFICIAL_ORIGINAL",
        },
    )
    assert res.status_code == 403


def test_path_traversal_protection(db: Session, user_and_admin_tokens: dict):
    """
    TEST 10: Path traversal attempts are strictly blocked.
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]

    # Traversal in form_id URL
    res = client.get(
        "/api/v1/knowledge/forms/..%2F..%2Fetc%2Fpasswd/download",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res.status_code in [400, 404]


def test_safe_content_disposition_and_headers(db: Session, user_and_admin_tokens: dict):
    """
    TEST 11: Validates safe Content-Disposition and provenance headers:
    Application-generated forms receive TEMPLATE_ filename and X-Convelina headers.
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]
    res = client.get(
        "/api/v1/knowledge/forms/form_aadhaar_update_adult/download",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res.status_code == 200
    assert "TEMPLATE_form_aadhaar_update_adult.pdf" in res.headers["Content-Disposition"]
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Convelina-Provenance"] in ("APPLICATION_GENERATED", "SYNTHETIC_TEST_ASSET")
    assert res.headers["X-Convelina-Verification-Status"] == "unverified"
    assert "uidai.gov.in" in res.headers["X-Convelina-Official-Source-URL"]


def test_download_audit_event_logged(db: Session, user_and_admin_tokens: dict):
    """
    TEST 12: Form downloads create an append-only audit event in audit_log.
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]
    citizen_id = user_and_admin_tokens["citizen"]["id"]

    res = client.get(
        "/api/v1/knowledge/forms/form_pan_csf_correction/download",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res.status_code == 200

    set_rls_context(db, None, "admin")
    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "official_form_downloaded",
            AuditLog.user_id == uuid.UUID(citizen_id),
        )
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert audit is not None
    assert audit.details["form_id"] == "form_pan_csf_correction"
    assert audit.details["provenance"] in ("APPLICATION_GENERATED", "SYNTHETIC_TEST_ASSET")

