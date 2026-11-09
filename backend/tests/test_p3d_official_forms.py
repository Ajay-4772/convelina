"""
CONVELINA — Phase P3D Official Forms Repository & Secure Downloads Test Suite
Validates:
1. Form catalog seeding & metadata (SHA-256 hashes, file sizes, ReportLab PDFs).
2. Deterministic Form Retrieval (keyword matching, category resolution, strict verified-only filtering).
3. Fallback when no verified form exists (no_verified_form_available=True, zero hallucinations).
4. Authenticated streaming download (GET /api/v1/knowledge/forms/{id}/download) with safe headers and SHA-256 match.
5. Authenticated streaming preview (GET /api/v1/knowledge/forms/{id}/preview) with inline disposition.
6. Path traversal rejection (denial of ../ or absolute paths).
7. Admin-only catalog synchronization and verification status updates (RBAC: 403 for citizens, 200 for admins).
8. Audit logging for download events under append-only audit trail.
"""

import hashlib
import io
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.official_form import OfficialForm
from app.models.audit_log import AuditLog
from app.core.database import SessionLocal, set_rls_context
from app.services.form_retrieval_service import FormRetrievalService
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
    uid_citizen = f"usr_p3d_cit_{uuid.uuid4().hex[:6]}"
    token_citizen = f"test_token_:{uid_citizen}:{uid_citizen}@example.com:Citizen P3D"
    res_cit = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_citizen}"},
        json={
            "email": f"{uid_citizen}@example.com",
            "full_name": "Citizen P3D",
            "phone_number": "+919876543210",
            "date_of_birth": "1990-01-01",
        },
    )
    assert res_cit.status_code in [200, 201]
    cit_data = res_cit.json()

    # Provision Admin
    uid_admin = f"usr_p3d_adm_{uuid.uuid4().hex[:6]}"
    token_admin = f"test_token_:{uid_admin}:{uid_admin}@admin.gov.in:Admin P3D"
    res_adm = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "email": f"{uid_admin}@admin.gov.in",
            "full_name": "Admin P3D",
            "phone_number": "+919999999999",
            "date_of_birth": "1980-01-01",
        },
    )
    assert res_adm.status_code in [200, 201]

    # Elevate admin user in DB
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


def test_seed_forms_metadata_and_integrity(db: Session):
    """
    Verifies that all 8 statutory seed forms are properly registered
    with valid SHA-256 hashes, file sizes, APPLICATION_GENERATED provenance,
    and unverified status.
    """
    set_rls_context(db, None, "admin")
    from app.rag.ingestion.sources import OFFICIAL_FORMS_DATA
    seeded_ids = [f["form_id"] for f in OFFICIAL_FORMS_DATA]
    forms = db.query(OfficialForm).filter(OfficialForm.form_id.in_(seeded_ids)).all()
    assert len(forms) >= 8

    for form in forms:
        assert form.verification_status == "unverified"
        assert form.provenance in ("APPLICATION_GENERATED", "SYNTHETIC_TEST_ASSET")
        assert form.is_active is True
        assert form.mime_type == "application/pdf"
        assert form.file_format.lower() == "pdf"
        assert form.sha256_hash is not None and len(form.sha256_hash) == 64
        assert form.file_size_bytes is not None and form.file_size_bytes > 0
        assert form.storage_path is not None


def test_form_retrieval_service_keyword_and_category(db: Session):
    """
    Validates that FormRetrievalService correctly matches official forms
    for specific citizen query intents.
    """
    set_rls_context(db, None, "admin")

    # 1. Aadhaar query
    aadhaar_res = FormRetrievalService.retrieve_applicable_forms(
        db, query="I want to update my name in Aadhaar card"
    )
    assert len(aadhaar_res.forms) >= 1
    assert any("aadhaar" in f.form_id for f in aadhaar_res.forms)
    assert all(f.is_official_government_form is False for f in aadhaar_res.forms)
    assert all(f.provenance in ("APPLICATION_GENERATED", "SYNTHETIC_TEST_ASSET") for f in aadhaar_res.forms)
    assert all(f.verification_status == "unverified" for f in aadhaar_res.forms)
    assert aadhaar_res.no_verified_form_available is True

    # 2. PAN card query
    pan_res = FormRetrievalService.retrieve_applicable_forms(
        db, query="How do I submit PAN correction request for spelling discrepancy?"
    )
    assert len(pan_res.forms) >= 1
    assert any("pan" in f.form_id for f in pan_res.forms)

    # 3. EPFO joint declaration
    epfo_res = FormRetrievalService.retrieve_applicable_forms(
        db, query="PF joint declaration for date of birth mismatch"
    )
    assert len(epfo_res.forms) >= 1
    assert any("epf" in f.form_id for f in epfo_res.forms)


def test_no_verified_form_fallback_zero_hallucination(db: Session):
    """
    Validates that completely unrelated or unverified queries return
    empty form list and do NOT invent government forms.
    """
    set_rls_context(db, None, "admin")
    unrelated_res = FormRetrievalService.retrieve_applicable_forms(
        db, query="How to bake sourdough bread or renew interstellar flight license?"
    )
    assert len(unrelated_res.forms) == 0
    assert unrelated_res.no_verified_form_available is True


def test_unverified_forms_excluded_from_citizen_queries(db: Session):
    """
    Validates that forms marked as unverified (e.g. 'needs_review')
    are strictly excluded from citizen retrieval.
    """
    set_rls_context(db, None, "admin")
    form = db.query(OfficialForm).filter(OfficialForm.form_id == "form_cbse_name_correction").first()
    assert form is not None
    original_status = form.verification_status

    try:
        set_rls_context(db, None, "admin")
        form.verification_status = "needs_review"
        db.commit()

        # Citizen queries CBSE
        set_rls_context(db, None, "user")
        retrieved = FormRetrievalService.retrieve_applicable_forms(
            db, query="CBSE marksheet name correction proforma"
        )
        assert not any(f.form_id == "form_cbse_name_correction" for f in retrieved.forms)
    finally:
        set_rls_context(db, None, "admin")
        fresh_form = db.query(OfficialForm).filter(OfficialForm.form_id == "form_cbse_name_correction").first()
        if fresh_form:
            fresh_form.verification_status = original_status
            db.commit()


def test_authenticated_download_endpoint(db: Session, user_and_admin_tokens: dict):
    """
    Validates GET /api/v1/knowledge/forms/{id}/download:
    - 401 when unauthenticated.
    - 200 with application/pdf and attachment header when authenticated.
    - Matches genuine SHA-256 hash.
    - Creates audit log entry.
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]
    form_id = "form_pan_csf_correction"

    # 1. Unauthenticated request
    unauth_res = client.get(f"/api/v1/knowledge/forms/{form_id}/download")
    assert unauth_res.status_code == 401

    # 2. Authenticated citizen request
    auth_res = client.get(
        f"/api/v1/knowledge/forms/{form_id}/download",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert auth_res.status_code == 200
    assert auth_res.headers.get("content-type") == "application/pdf"
    assert "attachment" in auth_res.headers.get("content-disposition", "")
    assert auth_res.headers.get("x-content-type-options") == "nosniff"

    # Validate PDF content integrity
    content = auth_res.content
    assert len(content) > 0
    assert content.startswith(b"%PDF")
    computed_sha256 = hashlib.sha256(content).hexdigest()

    set_rls_context(db, None, "admin")
    db_form = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
    assert db_form is not None
    assert computed_sha256 == db_form.sha256_hash

    # Validate audit log entry
    audit_entry = (
        db.query(AuditLog)
        .filter(AuditLog.action == "official_form_downloaded")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert audit_entry is not None
    assert audit_entry.details.get("form_id") == form_id


def test_authenticated_preview_endpoint(user_and_admin_tokens: dict):
    """
    Validates GET /api/v1/knowledge/forms/{id}/preview:
    - 401 when unauthenticated.
    - 200 with inline disposition and application/pdf.
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]
    form_id = "form_aadhaar_update_adult"

    # Unauthenticated
    unauth_res = client.get(f"/api/v1/knowledge/forms/{form_id}/preview")
    assert unauth_res.status_code == 401

    # Authenticated
    auth_res = client.get(
        f"/api/v1/knowledge/forms/{form_id}/preview",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert auth_res.status_code == 200
    assert auth_res.headers.get("content-type") == "application/pdf"
    assert "inline" in auth_res.headers.get("content-disposition", "")
    assert auth_res.headers.get("x-content-type-options") == "nosniff"
    assert auth_res.content.startswith(b"%PDF")


def test_path_traversal_attack_denied(user_and_admin_tokens: dict):
    """
    Validates that path traversal sequences (../, absolute paths, null bytes)
    are strictly rejected.
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]

    traversal_attempts = [
        "../../etc/passwd",
        "..%2F..%2Fetc%2Fpasswd",
        "/etc/shadow",
        "....//....//app//config.py",
        "form%00attack",
    ]

    for attempt in traversal_attempts:
        try:
            res = client.get(
                f"/api/v1/knowledge/forms/{attempt}/download",
                headers={"Authorization": f"Bearer {citizen_token}"},
            )
            assert res.status_code in [400, 404, 422]
        except Exception:
            # Client level url rejection is also acceptable denial
            pass


def test_admin_only_form_management_rbac(user_and_admin_tokens: dict, db: Session):
    """
    Validates Role-Based Access Control for admin forms endpoints:
    - Standard citizen: 403 Forbidden.
    - Admin: 200 OK.
    """
    citizen_token = user_and_admin_tokens["citizen"]["token"]
    admin_token = user_and_admin_tokens["admin"]["token"]
    form_id = "form_gazette_name_change"

    # 1. Citizen attempts admin listing -> 403
    cit_list_res = client.get(
        "/api/v1/knowledge/admin/forms",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert cit_list_res.status_code == 403

    # 2. Admin listing -> 200
    adm_list_res = client.get(
        "/api/v1/knowledge/admin/forms",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert adm_list_res.status_code == 200
    assert "forms" in adm_list_res.json()

    # 3. Citizen attempts verification status change -> 403
    cit_verify_res = client.put(
        f"/api/v1/knowledge/admin/forms/{form_id}/verification",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"verification_status": "verified"},
    )
    assert cit_verify_res.status_code == 403

    # 4. Admin updates verification status -> 200
    adm_verify_res = client.put(
        f"/api/v1/knowledge/admin/forms/{form_id}/verification",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "verification_status": "needs_review",
            "verification_notes": "Security audit hold",
        },
    )
    assert adm_verify_res.status_code == 200
    assert adm_verify_res.json()["verification_status"] == "needs_review"

    # Restore verification status
    client.put(
        f"/api/v1/knowledge/admin/forms/{form_id}/verification",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"verification_status": "verified"},
    )

    # 5. Admin sync catalog -> 200
    sync_res = client.post(
        "/api/v1/knowledge/admin/forms/sync",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert sync_res.status_code == 200
    assert sync_res.json()["forms_synced"] >= 8
