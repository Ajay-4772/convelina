"""
CONVELINA - Phase P2B Official Knowledge Base & Conflict-to-Resolution Mapping Tests
Tests:
1. Knowledge source model and lifecycle verification states (verified, needs_review, outdated, retired).
2. Content hash integrity and drift detection across revisions.
3. Taxonomy coverage for all 6 document types (Aadhaar, PAN, Passport, Class 10, Class 12, EPF).
4. Aadhaar <-> PAN name discrepancy deterministic resolution mapping (Form CSF).
5. Aadhaar <-> Class 10 DOB discrepancy deterministic resolution mapping (UIDAI Adult Form, Matriculation proof).
6. EPF <-> Aadhaar discrepancy deterministic resolution mapping (Joint Declaration).
7. Passport major name change deterministic resolution mapping (Annexure E, Gazette Notification).
8. Low OCR confidence fail-safe mapping (flagged for manual review, warns against statutory submission).
9. Non-Latin script fail-safe mapping (requires certified translation).
10. Form catalog filtering by category and issue type.
11. Admin knowledge management endpoint RBAC (User 403 Forbidden, Admin 200 OK).
12. RAG Orchestrator grounded resolution context integration with deterministic mapping.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.user import User
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.knowledge_source import KnowledgeSource
from app.models.official_form import OfficialForm
from app.rag.schemas import SourceVerificationStatus, UpdateVerificationStatusRequest
from app.rag.ingestion.service import KnowledgeIngestionService
from app.rag.forms.catalog import FormCatalogService
from app.services.resolution_mapping_service import ResolutionMappingService, KNOWN_OFFICIAL_FORMS
from app.services.resolution_context_service import ResolutionContextService
from app.rag.assistant.orchestrator import RAGOrchestrator

client = TestClient(app)


def create_test_user_session(role: str = "user"):
    """Provisions a test user with the specified role."""
    uid = f"p2b_{role}_{uuid.uuid4().hex[:8]}"
    email = f"{uid}@convelina.test"
    name = f"Test {role.capitalize()} {uid}"
    headers = {"Authorization": f"Bearer test_token_:{uid}:{email}:{name}"}

    resp = client.post(
        "/api/v1/auth/provision",
        headers=headers,
        json={"email": email, "full_name": name},
    )
    assert resp.status_code in (200, 201), f"Provisioning failed: {resp.text}"
    user_id = uuid.UUID(resp.json()["id"])

    # If admin role requested, elevate in db
    if role == "admin":
        db = SessionLocal()
        try:
            db.execute(text("SET LOCAL app.current_user_role = 'admin'; UPDATE users SET role = 'admin' WHERE id = :uid;"), {"uid": str(user_id)})
            db.commit()
        finally:
            db.close()

    return headers, user_id


def seed_document(user_id: uuid.UUID, doc_type: str, extracted_fields: dict) -> Document:
    """Helper to seed a document under RLS context."""
    db = SessionLocal()
    try:
        set_rls_context(db, user_id, "user")
        doc = Document(
            id=uuid.uuid4(),
            user_id=user_id,
            document_type=doc_type,
            file_path=f"ephemeral://test_{uuid.uuid4().hex[:12]}",
            file_hash=uuid.uuid4().hex,
            ocr_status="completed",
            extracted_fields=extracted_fields,
            masked_id="TEST-DOC-1234",
        )
        db.add(doc)
        db.commit()
        return doc
    finally:
        db.close()


def seed_conflict(user_id: uuid.UUID, doc_a: Document, doc_b: Document, field_name: str, classification: str, metadata: dict = None) -> Conflict:
    """Helper to seed a conflict record under RLS context."""
    db = SessionLocal()
    try:
        set_rls_context(db, user_id, "user")
        meta = metadata or {}
        meta.setdefault("classification", classification)
        meta.setdefault("confidence_score", 0.88)
        meta.setdefault("possible_causes", ["Record mismatch"])
        meta.setdefault("recommended_action", "Review and submit correction.")

        conflict = Conflict(
            id=uuid.uuid4(),
            user_id=user_id,
            doc_a_id=doc_a.id,
            doc_b_id=doc_b.id,
            field_name=field_name,
            value_a=doc_a.extracted_fields.get(field_name, "Value A"),
            value_b=doc_b.extracted_fields.get(field_name, "Value B"),
            description=f"Discrepancy detected in {field_name}: {classification}",
            similarity_score=85,
            severity="medium",
            conflict_type="format-only",
            status="detected",
            comparison_method="deterministic_p0_engine",
            metadata_=meta,
        )
        db.add(conflict)
        db.commit()
        return conflict
    finally:
        db.close()


# =============================================================================
# 1. Knowledge Source Models & Verification States
# =============================================================================

def test_knowledge_source_models_and_verification_states():
    """Validates lifecycle verification states (verified, needs_review, outdated, retired)."""
    assert SourceVerificationStatus.VERIFIED == "verified"
    assert SourceVerificationStatus.NEEDS_REVIEW == "needs_review"
    assert SourceVerificationStatus.OUTDATED == "outdated"
    assert SourceVerificationStatus.RETIRED == "retired"

    _, admin_id = create_test_user_session("admin")

    db = SessionLocal()
    try:
        set_rls_context(db, admin_id, "admin")
        test_source = KnowledgeSource(
            source_id=f"test_src_{uuid.uuid4().hex[:8]}",
            title="Test Guideline Verification",
            issuing_authority="Test Authority",
            document_type="guideline",
            document_category="pan",
            source_url="https://tin-nsdl.com",
            content_hash="abc123hash",
            raw_content="Sample guideline text",
            verification_status=SourceVerificationStatus.VERIFIED.value,
            is_active=True,
        )
        db.add(test_source)
        db.commit()

        set_rls_context(db, admin_id, "admin")
        loaded = db.query(KnowledgeSource).filter(KnowledgeSource.id == test_source.id).first()
        assert loaded is not None
        assert loaded.verification_status == "verified"

        # Update verification state to needs_review
        loaded.verification_status = SourceVerificationStatus.NEEDS_REVIEW.value
        db.commit()

        set_rls_context(db, admin_id, "admin")
        updated = db.query(KnowledgeSource).filter(KnowledgeSource.id == test_source.id).first()
        assert updated.verification_status == "needs_review"

        # Cleanup
        db.delete(updated)
        db.commit()
    finally:
        db.close()


# =============================================================================
# 2. Content Hash Integrity & Drift Detection
# =============================================================================

def test_content_hash_integrity_and_drift_detection():
    """Validates that compute_content_hash creates reproducible SHA-256 hashes and detects drift."""
    text1 = "UIDAI Aadhaar Enrolment Policy 2024"
    text2 = "UIDAI Aadhaar Enrolment Policy 2024"
    text_modified = "UIDAI Aadhaar Enrolment Policy 2025 Revised"

    hash1 = KnowledgeIngestionService.compute_content_hash(text1)
    hash2 = KnowledgeIngestionService.compute_content_hash(text2)
    hash_mod = KnowledgeIngestionService.compute_content_hash(text_modified)

    assert hash1 == hash2, "Content hashes must be deterministic and identical for same content"
    assert len(hash1) == 64, "SHA-256 content hash must be 64 hexadecimal characters"
    assert hash1 != hash_mod, "Content drift must produce a distinct hash"


# =============================================================================
# 3. Taxonomy Coverage for all Six Document Types
# =============================================================================

def test_taxonomy_coverage_all_six_categories():
    """Confirms all 6 supported document categories are covered in official knowledge base."""
    expected_categories = {"aadhaar", "pan", "passport", "education_10th", "education_12th", "epf"}

    from app.rag.ingestion.sources import OFFICIAL_SOURCES_DATA, OFFICIAL_FORMS_DATA

    source_cats = {s["document_category"] for s in OFFICIAL_SOURCES_DATA}
    form_cats = {f["document_category"] for f in OFFICIAL_FORMS_DATA}

    # Normalize category names
    normalized_source_cats = set()
    for c in source_cats:
        if c == "education":
            normalized_source_cats.add("education_10th")
        else:
            normalized_source_cats.add(c)

    assert "aadhaar" in normalized_source_cats
    assert "pan" in normalized_source_cats
    assert "passport" in normalized_source_cats
    assert "epf" in normalized_source_cats
    assert "education_10th" in normalized_source_cats
    assert "education_12th" in normalized_source_cats

    assert "aadhaar" in form_cats
    assert "pan" in form_cats
    assert "passport" in form_cats
    assert "epf" in form_cats


# =============================================================================
# 4. Aadhaar <-> PAN Name Discrepancy Mapping
# =============================================================================

def test_aadhaar_pan_name_discrepancy_resolution_mapping():
    """Validates deterministic mapping for Aadhaar <-> PAN name discrepancy (Form CSF)."""
    mapping = ResolutionMappingService.map_conflict(
        field_name="full_name",
        deterministic_classification="SURNAME_ABSENT_IN_ONE",
        document_types=["aadhaar", "pan"],
    )

    assert mapping.target_document_category == "pan"
    assert "Income Tax Department" in mapping.authority_name or "Protean" in mapping.authority_name
    assert mapping.procedure_type == "minor_correction"
    assert len(mapping.prescribed_forms) >= 1
    assert mapping.prescribed_forms[0].form_id == "form_pan_csf_correction"
    assert "tin-nsdl.com" in mapping.prescribed_forms[0].official_download_url
    assert any("PAN card" in doc for doc in mapping.document_checklist)
    assert any("Section 272B" in rule for rule in mapping.statutory_rules)


# =============================================================================
# 5. Aadhaar <-> Class 10 DOB Discrepancy Mapping
# =============================================================================

def test_aadhaar_class10_dob_discrepancy_resolution_mapping():
    """Validates deterministic mapping for Aadhaar <-> Class 10 DOB discrepancy."""
    mapping = ResolutionMappingService.map_conflict(
        field_name="date_of_birth",
        deterministic_classification="DOB_INCONSISTENCY",
        document_types=["aadhaar", "education_10th"],
    )

    assert mapping.target_document_category == "aadhaar"
    assert "UIDAI" in mapping.authority_name or "Unique Identification" in mapping.authority_name
    assert mapping.procedure_type == "statutory_linkage"
    assert len(mapping.prescribed_forms) >= 1
    assert mapping.prescribed_forms[0].form_id == "form_aadhaar_update_adult"
    assert any("Class 10" in doc for doc in mapping.document_checklist)
    assert any("ONLY ONCE" in rule for rule in mapping.statutory_rules)


# =============================================================================
# 6. EPF <-> Aadhaar Discrepancy Mapping (Joint Declaration)
# =============================================================================

def test_epf_aadhaar_discrepancy_joint_declaration_mapping():
    """Validates deterministic mapping for EPF <-> Aadhaar demographic alignment."""
    mapping = ResolutionMappingService.map_conflict(
        field_name="full_name",
        deterministic_classification="INITIAL_AMBIGUITY",
        document_types=["epf", "aadhaar"],
    )

    assert mapping.target_document_category == "epf"
    assert "Employees' Provident Fund" in mapping.authority_name or "EPFO" in mapping.authority_name
    assert mapping.procedure_type == "statutory_linkage"
    form_ids = [f.form_id for f in mapping.prescribed_forms]
    assert "form_epf_joint_declaration" in form_ids
    assert any("employer" in doc.lower() for doc in mapping.document_checklist)
    assert any("Section 142" in rule for rule in mapping.statutory_rules)


# =============================================================================
# 7. Passport Major Name Change Mapping
# =============================================================================

def test_passport_major_name_change_gazette_mapping():
    """Validates deterministic mapping for Passport major name change requiring Gazette & Annexure E."""
    mapping = ResolutionMappingService.map_conflict(
        field_name="full_name",
        deterministic_classification="HIGH_RISK_GENUINE_MISMATCH",
        document_types=["passport", "aadhaar"],
    )

    assert mapping.target_document_category == "passport"
    assert "Ministry of External Affairs" in mapping.authority_name
    assert mapping.procedure_type == "major_name_change"
    form_ids = [f.form_id for f in mapping.prescribed_forms]
    assert "form_passport_reissue" in form_ids
    assert "form_passport_annexure_e" in form_ids
    assert "form_gazette_name_change" in form_ids
    assert any("Gazette" in doc for doc in mapping.document_checklist)
    assert any("newspaper" in doc.lower() for doc in mapping.document_checklist)


# =============================================================================
# 8. Low OCR Confidence Fail-Safe Mapping
# =============================================================================

def test_low_ocr_confidence_failsafe_mapping():
    """Validates that low OCR confidence prevents automatic statutory filing and mandates re-scan."""
    mapping = ResolutionMappingService.map_conflict(
        field_name="full_name",
        deterministic_classification="LOW_CONFIDENCE_NEEDS_REVIEW",
        document_types=["aadhaar", "pan"],
        ocr_quality_warning="OCR confidence below 60%",
    )

    assert mapping.target_document_category == "scan_quality_review"
    assert mapping.procedure_type == "manual_review"
    assert mapping.action_priority == "high"
    assert len(mapping.prescribed_forms) == 0  # No statutory form until clean scan
    assert any("300+ DPI" in doc for doc in mapping.document_checklist)
    assert any("NOT be initiated" in rule for rule in mapping.statutory_rules)


# =============================================================================
# 9. Non-Latin Script Fail-Safe Mapping
# =============================================================================

def test_non_latin_script_failsafe_mapping():
    """Validates that non-Latin/Indic script triggers certified translation requirement."""
    mapping = ResolutionMappingService.map_conflict(
        field_name="full_name",
        deterministic_classification="UNRESOLVABLE_NON_LATIN_SCRIPT",
        document_types=["aadhaar", "pan"],
        non_latin_warning="Non-Latin Indic script detected",
    )

    assert mapping.target_document_category == "certified_translation"
    assert mapping.procedure_type == "manual_review"
    assert mapping.action_priority == "high"
    assert any("translation" in doc.lower() for doc in mapping.document_checklist)
    assert any("Non-Latin" in rule for rule in mapping.statutory_rules)


# =============================================================================
# 10. Form Catalog Filtering by Category and Issue Type
# =============================================================================

def test_form_catalog_filtering_by_category_and_issue():
    """Validates FormCatalogService filtering across categories and issues."""
    _, admin_id = create_test_user_session("admin")
    db = SessionLocal()
    try:
        set_rls_context(db, admin_id, "admin")
        # Ingestion service sync ensures forms exist in DB
        ingest = KnowledgeIngestionService(db)
        ingest.sync_official_forms()

        # 1. Filter by category
        pan_forms = FormCatalogService.list_forms(db, category="pan")
        assert len(pan_forms) >= 1
        assert all(f.document_category == "pan" for f in pan_forms)

        # 2. Filter by issue type
        dob_forms = FormCatalogService.list_forms(db, issue_type="date_of_birth")
        assert len(dob_forms) >= 2
        for f in dob_forms:
            assert "date_of_birth" in f.applicable_issue_types

        # 3. Lookup specific form
        pan_csf = FormCatalogService.get_form_by_id(db, "form_pan_csf_correction")
        assert pan_csf is not None
        assert pan_csf.form_id == "form_pan_csf_correction"
        assert "tin-nsdl.com" in pan_csf.official_download_url
    finally:
        db.close()


# =============================================================================
# 11. Admin Knowledge Management RBAC Enforcement
# =============================================================================

def test_admin_knowledge_management_rbac_enforcement():
    """Verifies that normal users receive 403 while admins can manage sources."""
    user_headers, _ = create_test_user_session("user")
    admin_headers, _ = create_test_user_session("admin")

    # 1. Normal user denied admin source listing
    resp_user = client.get("/api/v1/knowledge/admin/sources", headers=user_headers)
    assert resp_user.status_code == 403

    # 2. Admin allowed source listing
    resp_admin = client.get("/api/v1/knowledge/admin/sources", headers=admin_headers)
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    assert "sources" in data
    assert "total" in data

    # 3. Normal user denied verification status update
    resp_user_up = client.put(
        "/api/v1/knowledge/admin/sources/src_uidai_update_policy_2024/verification",
        headers=user_headers,
        json={"verification_status": "verified"},
    )
    assert resp_user_up.status_code == 403

    # 4. Admin updates verification status
    resp_admin_up = client.put(
        "/api/v1/knowledge/admin/sources/src_uidai_update_policy_2024/verification",
        headers=admin_headers,
        json={"verification_status": "verified", "review_notes": "Automated regression verification"},
    )
    assert resp_admin_up.status_code == 200
    assert resp_admin_up.json()["verification_status"] == "verified"


# =============================================================================
# 12. RAG Orchestrator Grounded Resolution Answer Generation
# =============================================================================

def test_rag_orchestrator_grounded_resolution_answer_generation():
    """Verifies that RAG Orchestrator case context integrates deterministic resolution mapping."""
    user_headers, user_id = create_test_user_session("user")

    doc_a = seed_document(user_id, "aadhaar", {"full_name": "Aarav Sharma", "date_of_birth": "1990-05-15"})
    doc_b = seed_document(user_id, "pan", {"full_name": "Aarav", "date_of_birth": "1990-05-15"})
    conflict = seed_conflict(user_id, doc_a, doc_b, "full_name", "SURNAME_ABSENT_IN_ONE")

    # Test resolution context retrieval via service
    db = SessionLocal()
    try:
        set_rls_context(db, user_id, "user")
        res_ctx = ResolutionContextService.get_resolution_context(db, user_id, conflict.id)
        assert res_ctx.resolution_mapping is not None
        assert res_ctx.resolution_mapping.target_document_category == "pan"
        assert res_ctx.resolution_mapping.procedure_type == "minor_correction"
        assert len(res_ctx.resolution_mapping.prescribed_forms) >= 1
        assert res_ctx.statutory_disclaimer == "AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION"

        # Test RAG case context building
        orchestrator = RAGOrchestrator(db)
        case_ctx = orchestrator._build_minimal_case_context(user_id, conflict.id)
        assert case_ctx["resolution_mapping"] is not None
        assert case_ctx["resolution_mapping"]["target_document_category"] == "pan"
        assert case_ctx["deterministic_findings"]["classification"] == "SURNAME_ABSENT_IN_ONE"
    finally:
        db.close()
