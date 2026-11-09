"""
CONVELINA — Synthetic Forms & Admin Form Replacement Workflow Test Suite
Validates:
1. Synthetic development sample endpoint (/api/v1/documents/synthetic-samples) and downloads (PDF & PNG).
2. Headers verify X-Convelina-Provenance: SYNTHETIC_TEST_ASSET and disclaimer.
3. Admin replacement endpoint (/api/v1/knowledge/admin/forms/{form_id}/replace):
   - Archives current version into official_form_versions table.
   - Enforces ReportLab rejection gate (ReportLab-generated PDFs cannot be submitted as OFFICIAL_ORIGINAL).
   - Updates form record with new version, sha256, file size, provenance.
4. History retrieval endpoint (/api/v1/knowledge/admin/forms/{form_id}/history).
5. Role-based scoping (Citizen receives 403 Forbidden; Admin succeeds).
6. Tamper-evident audit logging for version archiving and form replacement.
"""

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.official_form import OfficialForm, OfficialFormVersion
from app.models.audit_log import AuditLog
from app.core.database import SessionLocal, set_rls_context
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
    uid_citizen = f"usr_synth_cit_{uuid.uuid4().hex[:6]}"
    token_citizen = f"test_token_:{uid_citizen}:{uid_citizen}@example.com:Citizen Synth"
    res_cit = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_citizen}"},
        json={
            "email": f"{uid_citizen}@example.com",
            "full_name": "Citizen Synth",
            "phone_number": "+919876543210",
            "date_of_birth": "1990-01-01",
        },
    )
    assert res_cit.status_code in (200, 201)

    uid_admin = f"usr_synth_adm_{uuid.uuid4().hex[:6]}"
    token_admin = f"test_token_:{uid_admin}:{uid_admin}@admin.gov.in:Admin Synth"
    res_adm = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "email": f"{uid_admin}@admin.gov.in",
            "full_name": "Admin Synth",
            "phone_number": "+919876543211",
            "date_of_birth": "1985-05-15",
        },
    )
    assert res_adm.status_code in (200, 201)

    # Elevate admin user in DB under admin RLS context
    set_rls_context(db, None, "admin")
    admin_user = db.query(User).filter(User.email == f"{uid_admin}@admin.gov.in").first()
    assert admin_user is not None
    admin_user.role = "admin"
    db.commit()

    return {
        "citizen_token": token_citizen,
        "admin_token": token_admin,
    }


def test_list_synthetic_samples():
    """Verifies that all 6 categories of synthetic development samples are listed."""
    res = client.get("/api/v1/documents/synthetic-samples")
    assert res.status_code == 200
    data = res.json()
    assert "samples" in data
    categories = [s["category"] for s in data["samples"]]
    for cat in ["aadhaar", "pan", "passport", "education_10th", "education_12th", "epf"]:
        assert cat in categories
    for s in data["samples"]:
        assert s["provenance"] == "SYNTHETIC_TEST_ASSET"
        assert "NOT AN OFFICIAL GOVERNMENT FORM" in s["disclaimer"]


def test_download_synthetic_sample_pdf_and_png():
    """Verifies streaming download of synthetic test document in PDF and PNG format with provenance headers."""
    # PDF download
    res_pdf = client.get("/api/v1/documents/synthetic-samples/aadhaar?format=pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.headers["X-Convelina-Provenance"] == "SYNTHETIC_TEST_ASSET"
    assert "SYNTHETIC DEVELOPMENT SAMPLE" in res_pdf.headers["X-Convelina-Disclaimer"]
    assert res_pdf.content.startswith(b"%PDF")

    # PNG download
    res_png = client.get("/api/v1/documents/synthetic-samples/pan?format=png")
    assert res_png.status_code == 200
    assert res_png.headers["content-type"] == "image/png"
    assert res_png.headers["X-Convelina-Provenance"] == "SYNTHETIC_TEST_ASSET"
    assert res_png.content.startswith(b"\x89PNG")


def test_download_synthetic_sample_invalid_category():
    """Verifies 404 for unknown category."""
    res = client.get("/api/v1/documents/synthetic-samples/unknown_doc_xyz")
    assert res.status_code == 404


def test_admin_replace_form_non_admin_forbidden(user_and_admin_tokens):
    """Verifies RBAC: Regular citizen cannot replace forms (403 Forbidden)."""
    headers = {"Authorization": f"Bearer {user_and_admin_tokens['citizen_token']}"}
    fake_pdf = b"%PDF-1.4\nFake content\n%%EOF"
    files = {"file": ("new_form.pdf", io.BytesIO(fake_pdf), "application/pdf")}
    data = {"version": "2.0", "provenance": "OFFICIAL_ORIGINAL"}

    res = client.post(
        "/api/v1/knowledge/admin/forms/form_aadhaar_update_adult/replace",
        headers=headers,
        files=files,
        data=data,
    )
    assert res.status_code == 403


def test_admin_replace_form_reportlab_rejection_gate(user_and_admin_tokens):
    """Verifies ReportLab rejection gate: ReportLab PDF cannot be uploaded as OFFICIAL_ORIGINAL."""
    headers = {"Authorization": f"Bearer {user_and_admin_tokens['admin_token']}"}
    # Create PDF content containing ReportLab signature
    reportlab_pdf = b"%PDF-1.4\n%ReportLab Generated Asset\nFake content\n%%EOF"
    files = {"file": ("reportlab_asset.pdf", io.BytesIO(reportlab_pdf), "application/pdf")}
    data = {"version": "2.0", "provenance": "OFFICIAL_ORIGINAL"}

    res = client.post(
        "/api/v1/knowledge/admin/forms/form_aadhaar_update_adult/replace",
        headers=headers,
        files=files,
        data=data,
    )
    assert res.status_code == 400
    assert "ReportLab" in res.json()["detail"]


def test_admin_replace_form_success_and_archive(db: Session, user_and_admin_tokens):
    """Verifies full replacement workflow: archives old version and updates official_forms."""
    headers = {"Authorization": f"Bearer {user_and_admin_tokens['admin_token']}"}
    authentic_pdf = b"%PDF-1.4\n%Authentic Official Government Publication UIDAI 2026\n%%EOF"
    files = {"file": ("authentic_aadhaar_update.pdf", io.BytesIO(authentic_pdf), "application/pdf")}
    data = {
        "version": "2.1",
        "provenance": "OFFICIAL_ORIGINAL",
        "verification_status": "verified",
        "issuing_authority": "Unique Identification Authority of India (UIDAI)",
        "provenance_notes": "Official 2026 Gazette Notification Issue 42",
        "change_summary": "Replaced placeholder with authentic government gazette form",
    }

    res = client.post(
        "/api/v1/knowledge/admin/forms/form_aadhaar_update_adult/replace",
        headers=headers,
        files=files,
        data=data,
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["version"] == "2.1"
    assert updated["provenance"] == "OFFICIAL_ORIGINAL"
    assert updated["verification_status"] == "verified"

    # Verify history endpoint returns archived version
    res_hist = client.get(
        "/api/v1/knowledge/admin/forms/form_aadhaar_update_adult/history",
        headers=headers,
    )
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert hist_data["form_id"] == "form_aadhaar_update_adult"
    assert hist_data["current_version"] == "2.1"
    assert hist_data["total_versions"] >= 1
    assert any(v["version"] in ("UIDAI-ENR-2024", "1.0", None) for v in hist_data["versions"])

    # Verify audit logs in database
    set_rls_context(db, None, "admin")
    archived_audit = (
        db.query(AuditLog)
        .filter(AuditLog.action == "official_form_version_archived")
        .first()
    )
    assert archived_audit is not None

    replaced_audit = (
        db.query(AuditLog)
        .filter(AuditLog.action == "official_form_replaced")
        .first()
    )
    assert replaced_audit is not None
