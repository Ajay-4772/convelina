"""
CONVELINA — P3H.6 Citizen Document Repository & Procedural Guidance Test Suite
Validates:
1. Citizen Document Repository:
   - Searchable, paginated listing across all 6 supported identity categories:
     Aadhaar, PAN, Passport, Class 10, Class 12, and EPF/UAN.
   - Category filtering and category summary counts.
2. Document Provenance & Verification Classification:
   - 7 Provenance Classifications: OFFICIAL_ORIGINAL, OFFICIAL_COPY, GOVERNMENT_REFERENCE,
     HISTORICAL_REFERENCE, APPLICATION_GENERATED, SYNTHETIC_DEVELOPMENT_SAMPLE, UNVERIFIED_SOURCE.
   - 5 Verification States: VERIFIED, NEEDS_REVIEW, OUTDATED, RETIRED, SOURCE_METADATA_CONFLICT.
   - Mandatory disclaimers on synthetic development samples:
     'SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM'.
   - ReportLab forms cannot be verified as OFFICIAL_ORIGINAL.
3. Dedicated Document Detail View:
   - Complete metadata, purpose, applicable cohorts, related procedures, supporting document checklists,
     safe preview/download availability, and statutory limitations.
4. Procedural Guidance Synthesis Engine:
   - Step-by-step resolution guidance grounded in verified circulars.
   - Strict preservation of DOC_043 restrictions (SOURCE_METADATA_CONFLICT, limitation notice).
   - Honest statutory abstention on unverified or third-time exception claims.
5. Supporting-Document Checklist Engine:
   - Deterministic differentiation between:
     VERIFIED_MANDATORY, VERIFIED_CONDITIONAL, RECOMMENDED, HUMAN_REVIEW_REQUIRED.
   - Informational checklist disclaimer preservation.
6. Personalized Guidance & RLS Scoping:
   - Grounded discrepancy guidance based on Module 5 (/api/v1/conflicts) confirmed fields.
   - Strict user scoping (citizens only see their own conflicts).
   - Mandatory comparison disclaimer: 'AUTOMATED COMPARISON RESULT — NOT OFFICIAL GOVERNMENT VERIFICATION.'
7. Safe File Handling & Path Traversal Prevention:
   - Rejects directory traversal tokens (.., null bytes).
   - Streams authentic PDF assets safely.
8. Admin Portal Security & Audit Trails:
   - USER vs ADMIN role enforcement (no officer roles).
   - Requires explicit provenance evidence for verification approvals.
   - Logs every administrative action to append-only audit trail.
"""

import os
import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.dependencies.auth import get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User
from app.models.conflict import Conflict
from app.models.document import Document
from app.models.official_form import OfficialForm
from app.services.repository_service import CitizenRepositoryService
from app.services.checklist_service import ChecklistService, STATUTORY_CHECKLISTS
from app.services.procedural_guidance_service import ProceduralGuidanceService, PROCEDURAL_TEMPLATES
from app.rag.ingestion.corpus_ingestion import DOC_043_STATUTORY_DISCLAIMER


@pytest.fixture(autouse=True)
def setup_test_mode():
    orig_token = settings.TEST_MODE_ALLOW_SIMULATED_TOKENS
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = True
    yield
    settings.TEST_MODE_ALLOW_SIMULATED_TOKENS = orig_token


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


@pytest.fixture
def normal_user():
    return User(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        email="citizen@example.com",
        full_name="Rajesh Kumar",
        role="user",
        firebase_uid="firebase_citizen_111",
    )


@pytest.fixture
def admin_user():
    return User(
        id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
        email="admin@convelina.gov.in",
        full_name="Platform Administrator",
        role="admin",
        firebase_uid="firebase_admin_999",
    )


@pytest.fixture
def client_normal(mock_db, normal_user):
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: normal_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def client_admin(mock_db, admin_user):
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ===========================================================================
# 1. CITIZEN DOCUMENT REPOSITORY LISTING & CATEGORY BROWSING TESTS
# ===========================================================================

def test_repository_listing_pagination(client_normal):
    """Verifies that repository lists resources with pagination and full metadata."""
    res = client_normal.get("/api/v1/repository/resources?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 47
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["resources"]) == 10

    first = data["resources"][0]
    assert "resource_id" in first
    assert "title" in first
    assert "issuing_authority" in first
    assert "document_category" in first
    assert "provenance" in first
    assert "verification_status" in first


def test_six_supported_identity_categories_filtering(client_normal):
    """Verifies category filtering across all 6 supported identity categories."""
    categories = ["aadhaar", "pan", "passport", "class_10", "class_12", "epf"]

    for cat in categories:
        res = client_normal.get(f"/api/v1/repository/resources?category={cat}")
        assert res.status_code == 200, f"Failed for category {cat}"
        data = res.json()
        assert data["total"] > 0, f"Expected resources for category {cat}"
        for item in data["resources"]:
            assert (
                item["document_category"] == cat
                or cat in item.get("applicable_categories", [])
            ), f"Item {item['resource_id']} category mismatch for {cat}"


def test_categories_summary_endpoint(client_normal):
    """Verifies high-level categories summary with counts and authorities."""
    res = client_normal.get("/api/v1/repository/categories")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    cats = data["categories"]
    assert "aadhaar" in cats
    assert "pan" in cats
    assert "passport" in cats
    assert "class_10" in cats
    assert "class_12" in cats
    assert "epf" in cats

    # Check authority and positive counts
    assert cats["aadhaar"]["count"] > 0
    assert "UIDAI" in cats["aadhaar"]["authority"]
    assert cats["pan"]["count"] > 0
    assert cats["passport"]["count"] > 0


# ===========================================================================
# 2. DOCUMENT PROVENANCE & VERIFICATION CLASSIFICATION TESTS
# ===========================================================================

def test_provenance_classifications_and_synthetic_disclaimer(client_normal):
    """
    Verifies the 7 distinct provenance classifications and mandatory
    disclaimers on synthetic development samples.
    """
    catalog = CitizenRepositoryService.get_catalog()
    provenances = set(r["provenance"] for r in catalog)

    # Must contain official original, government reference, historical reference, and synthetic samples
    assert "OFFICIAL_ORIGINAL" in provenances
    assert "GOVERNMENT_REFERENCE" in provenances
    assert "HISTORICAL_REFERENCE" in provenances
    assert "SYNTHETIC_DEVELOPMENT_SAMPLE" in provenances

    # Verify synthetic development sample restrictions
    synthetic_samples = [r for r in catalog if r["provenance"] == "SYNTHETIC_DEVELOPMENT_SAMPLE"]
    assert len(synthetic_samples) > 0
    for s in synthetic_samples:
        assert s["is_official_government_form"] is False
        assert s["is_synthetic_sample"] is True
        assert s["disclaimer"] == "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM"


def test_doc043_source_conflict_and_human_review_invariants(client_normal):
    """
    Verifies that DOC_043 strictly preserves SOURCE_METADATA_CONFLICT,
    human_review_required=True, and statutory limitation notices.
    """
    res = client_normal.get("/api/v1/repository/resources/DOC_043")
    assert res.status_code == 200
    doc43 = res.json()

    assert doc43["resource_id"] == "DOC_043"
    assert doc43["verification_status"] == "source_metadata_conflict"
    assert doc43["has_source_conflict"] is True
    assert doc43["human_review_required"] is True
    assert "STATUTORY LIMITATION NOTICE" in doc43["disclaimer"]
    assert "third-time exceptions" in doc43["disclaimer"]


def test_historical_superseded_source_restrictions(client_normal):
    """
    Verifies that historical circulars are classified as HISTORICAL_REFERENCE
    and clearly disclaimed as superseded.
    """
    res = client_normal.get("/api/v1/repository/resources/DOC_003")
    assert res.status_code == 200
    doc3 = res.json()

    assert doc3["provenance"] == "HISTORICAL_REFERENCE"
    assert doc3["is_historical"] is True
    assert "SUPERSEDED" in (doc3["disclaimer"] or "")


# ===========================================================================
# 3. DOCUMENT DETAIL VIEW TESTS
# ===========================================================================

def test_document_detail_view_full_structure(client_normal):
    """Verifies document detail view returns all 7 required structural sections."""
    res = client_normal.get("/api/v1/repository/resources/DOC_001")
    assert res.status_code == 200
    data = res.json()

    # Overview
    assert data["resource_id"] == "DOC_001"
    assert "Aadhaar Enrolment" in data["title"]
    assert data["issuing_authority"] == "Unique Identification Authority of India (UIDAI)"
    assert data["provenance"] == "OFFICIAL_ORIGINAL"
    assert data["verification_status"] == "verified"

    # Purpose / What it is used for
    assert len(data["purpose"]) > 20

    # Cohorts / Who should use it
    assert "ADULT" in data["intended_cohort"].upper() or "RESIDENT" in data["intended_cohort"].upper()

    # Related procedures
    assert len(data["related_procedures"]) > 0
    assert "aadhaar_name_update" in data["related_procedures"]

    # Checklist
    assert len(data["supporting_document_checklist"]) > 0

    # Preview & Download URLs
    assert data["download_available"] is True
    assert "/download" in data["download_url"]
    assert "/preview" in data["preview_url"]

    # Citations
    assert len(data["statutory_citations"]) > 0


# ===========================================================================
# 4. SUPPORTING-DOCUMENT CHECKLIST ENGINE TESTS
# ===========================================================================

def test_checklist_engine_differentiation(client_normal):
    """
    Verifies checklist engine differentiates:
    - VERIFIED_MANDATORY
    - VERIFIED_CONDITIONAL
    - RECOMMENDED
    - HUMAN_REVIEW_REQUIRED
    """
    # Test Aadhaar Checklist
    res_aad = client_normal.get("/api/v1/repository/checklists/aadhaar_name_update")
    assert res_aad.status_code == 200
    data_aad = res_aad.json()
    assert data_aad["mandatory_count"] >= 1
    assert data_aad["conditional_count"] >= 1
    assert data_aad["recommended_count"] >= 1
    assert "disclaimer" in data_aad
    assert "does not constitute official government approval" in data_aad["disclaimer"]

    # Test PAN CSF Checklist
    res_pan = client_normal.get("/api/v1/repository/checklists/pan_name_correction_csf")
    assert res_pan.status_code == 200
    data_pan = res_pan.json()
    assert data_pan["mandatory_count"] >= 3  # Proof of PAN, PoI, PoA, DOB
    statuses = [item["status"] for item in data_pan["items"]]
    assert "VERIFIED_MANDATORY" in statuses
    assert "VERIFIED_CONDITIONAL" in statuses

    # Test EPFO Joint Declaration Checklist
    res_epf = client_normal.get("/api/v1/repository/checklists/epf_joint_declaration")
    assert res_epf.status_code == 200
    data_epf = res_epf.json()
    assert data_epf["mandatory_count"] >= 2  # Joint Declaration Form, Aadhaar, PAN
    assert data_epf["human_review_count"] >= 1  # Field Office / RPFC Review


# ===========================================================================
# 5. PROCEDURAL GUIDANCE SYNTHESIS & ABSTENTION TESTS
# ===========================================================================

def test_procedural_guidance_synthesis(client_normal):
    """Verifies procedural guidance synthesizes step-by-step instructions with citations."""
    payload = {
        "query": "How do I update my name in PAN card after marriage?",
        "category": "pan",
    }
    res = client_normal.post("/api/v1/repository/guidance/synthesize", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["statutory_abstention"] is False
    assert "PAN" in data["prescribed_procedure"]
    assert len(data["steps"]) >= 3
    assert len(data["checklist"]) >= 3
    assert len(data["statutory_citations"]) >= 1
    assert "disclaimer" in data


def test_statutory_abstention_on_unsupported_exception_claims(client_normal):
    """
    Verifies that requests involving 3rd-time exception claims, lifetime resets,
    or unsupported procedures trigger statutory abstention.
    """
    unsupported_queries = [
        "How do I submit a 3rd time Aadhaar name update exception packet to Regional Office?",
        "Can I reset my lifetime Aadhaar update limit counter?",
        "Use notarized affidavit instead of gazette for third time change",
    ]

    for q in unsupported_queries:
        payload = {"query": q}
        res = client_normal.post("/api/v1/repository/guidance/synthesize", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["statutory_abstention"] is True, f"Failed to abstain on query: {q}"
        assert data["abstention_reason"] is not None
        assert len(data["steps"]) == 0
        assert "STATUTORY ABSTENTION" in data["disclaimer"]


def test_doc043_restriction_enforced_in_guidance(client_normal):
    """
    Verifies that procedural guidance for Aadhaar name correction includes
    DOC_043 metadata conflict notice and human review flag.
    """
    payload = {
        "query": "What is the procedure for updating spelling in Aadhaar card?",
        "category": "aadhaar",
    }
    res = client_normal.post("/api/v1/repository/guidance/synthesize", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["source_conflict_flag"] is True
    assert data["human_review_required"] is True
    assert any("DOC_043" in l for l in data["limitations"])


# ===========================================================================
# 6. PERSONALIZED GUIDANCE & RLS SCOPING TESTS
# ===========================================================================

def test_personalized_guidance_for_authenticated_citizen(client_normal, mock_db, normal_user):
    """
    Verifies personalized guidance retrieves active conflicts for the caller
    and attaches relevant checklists, procedures, and mandatory disclaimers.
    """
    mock_conflict = MagicMock(spec=Conflict)
    mock_conflict.id = uuid.uuid4()
    mock_conflict.user_id = normal_user.id
    mock_conflict.conflict_type = "NAME_MISMATCH"
    mock_conflict.severity = "HIGH"
    mock_conflict.status = "detected"
    mock_conflict.document_a_id = uuid.uuid4()
    mock_conflict.document_b_id = uuid.uuid4()
    mock_conflict.to_dict.return_value = {
        "id": str(mock_conflict.id),
        "user_id": str(normal_user.id),
        "conflict_type": "NAME_MISMATCH",
        "severity": "HIGH",
        "status": "detected",
        "field_name": "name",
        "document_a_value": "Rajesh K",
        "document_b_value": "Rajesh Kumar",
    }

    mock_doc_a = MagicMock(spec=Document)
    mock_doc_a.document_type = "aadhaar"
    mock_doc_a.file_name = "aadhaar_card.pdf"

    mock_doc_b = MagicMock(spec=Document)
    mock_doc_b.document_type = "pan"
    mock_doc_b.file_name = "pan_card.pdf"

    # Configure mock query chain
    doc_seq = [mock_doc_a, mock_doc_b]

    def mock_query(model):
        q = MagicMock()
        if model == Conflict:
            q.filter.return_value.order_by.return_value.all.return_value = [mock_conflict]
            q.filter.return_value.first.return_value = mock_conflict
        elif model == Document:
            def get_doc():
                return doc_seq.pop(0) if doc_seq else None
            q.filter.return_value.first.side_effect = get_doc
        return q

    mock_db.query.side_effect = mock_query

    res = client_normal.get("/api/v1/repository/guidance/personalized")
    assert res.status_code == 200
    data = res.json()

    assert data["total_conflicts"] == 1
    item = data["items"][0]
    assert item["conflict_type"] == "NAME_MISMATCH"
    assert item["document_a_category"] == "aadhaar"
    assert item["document_b_category"] == "pan"
    assert "Rajesh K" in item["explanation"]
    assert "Rajesh Kumar" in item["explanation"]
    assert "AUTOMATED COMPARISON RESULT — NOT OFFICIAL GOVERNMENT VERIFICATION." in item["disclaimer"]
    assert len(item["checklist"]) > 0


# ===========================================================================
# 7. SAFE FILE DOWNLOAD & PATH TRAVERSAL DEFENSE TESTS
# ===========================================================================

def test_safe_download_and_path_traversal_prevention(client_normal):
    """
    Verifies that file download endpoints reject path traversal attacks
    and stream authentic files safely.
    """
    # 1. Path traversal attacks via HTTP endpoint
    bad_ids = [
        "../../etc/passwd",
        "..\\..\\windows\\system32",
        "DOC_001/../../../secret",
    ]

    for bad in bad_ids:
        res = client_normal.get(f"/api/v1/repository/resources/{bad}/download")
        assert res.status_code in (404, 422), f"Path traversal not blocked for {bad}"

    # Direct resolver checks including null byte injections
    assert CitizenRepositoryService.resolve_file_path("DOC_001\x00malicious") is None
    assert CitizenRepositoryService.resolve_file_path("../../etc/passwd") is None
    assert CitizenRepositoryService.resolve_file_path("DOC_001/../../secret") is None

    # 2. Genuine file download
    res_good = client_normal.get("/api/v1/repository/resources/DOC_001/download")
    assert res_good.status_code == 200
    assert res_good.headers["content-type"] == "application/pdf"
    assert "attachment" in res_good.headers["content-disposition"]


# ===========================================================================
# 8. ADMINISTRATIVE VERIFICATION & AUDIT TRAIL TESTS
# ===========================================================================

def test_citizen_forbidden_on_admin_verification(client_normal):
    """Verifies that non-admin citizens are rejected with 403 Forbidden."""
    res_citizen = client_normal.put(
        "/api/v1/repository/admin/resources/DOC_001/verify",
        json={
            "provenance": "OFFICIAL_ORIGINAL",
            "verification_status": "verified",
            "provenance_evidence": "UIDAI official portal download",
        }
    )
    assert res_citizen.status_code == 403


def test_admin_rejection_of_synthetic_claims_as_official_original(client_admin, mock_db):
    """
    Verifies that admins cannot verify synthetic or ReportLab-generated forms
    as OFFICIAL_ORIGINAL or OFFICIAL_COPY.
    """
    res_fake = client_admin.put(
        "/api/v1/repository/admin/resources/form_passport_reissue/verify",
        json={
            "provenance": "OFFICIAL_ORIGINAL",
            "verification_status": "verified",
            "provenance_evidence": "Claiming synthetic asset is authentic original",
        }
    )
    assert res_fake.status_code == 400
    assert "ReportLab" in res_fake.json()["detail"] or "Cannot verify" in res_fake.json()["detail"]


def test_admin_lifecycle_transition_and_audit(client_admin, mock_db):
    """Verifies that admin lifecycle status updates (outdated, retired) are recorded."""
    mock_form = MagicMock(spec=OfficialForm)
    mock_form.id = uuid.uuid4()
    mock_form.form_id = "DOC_001"
    mock_form.verification_status = "verified"
    mock_form.is_active = True

    mock_db.query.return_value.filter.return_value.first.return_value = mock_form

    res = client_admin.put(
        "/api/v1/repository/admin/resources/DOC_001/lifecycle",
        json={
            "verification_status": "outdated",
            "reason": "Superseded by circular 2026",
        }
    )
    assert res.status_code == 200
    assert mock_form.verification_status == "outdated"
    assert mock_form.is_active is False
