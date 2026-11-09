"""
CONVELINA — Phase P3G.1 Tests: Migration 017, Models & Schemas

Verifies:
1. Migration 017 schema presence in PostgreSQL.
2. Forced PostgreSQL RLS on correction_drafts and correction_draft_versions with consolith_app non-superuser role.
3. User tenant isolation (User A cannot access User B's drafts or versions).
4. Admin scoping (Admin can view all drafts).
5. Removal of legacy officer policies.
6. Pydantic schema validation, 10 draft types taxonomy, and deterministic compatibility matrix.
"""

import uuid
from datetime import datetime
import pytest
from sqlalchemy import text
from app.core.database import SessionLocal, set_rls_context
from app.models.user import User
from app.models.correction_draft import CorrectionDraft, CorrectionDraftVersion, MANDATORY_DRAFT_DISCLAIMER
from app.schemas.correction_draft import (
    DraftTypeEnum,
    DocumentCategoryEnum,
    DraftStatusEnum,
    DRAFT_COMPATIBILITY_MATRIX,
    is_draft_type_applicable,
    CorrectionDraftCreate,
    CorrectionDraftResponse,
    CorrectionDraftConfirmRequest,
)


class TestP3G1DatabaseSchemaAndRLS:
    """Verifies Migration 017 schema structure and forced RLS policies in PostgreSQL."""

    def test_migration_017_applied_in_schema_migrations(self):
        db = SessionLocal()
        try:
            row = db.execute(text("SELECT version FROM schema_migrations WHERE version = '017_p3g_administrative_letter_drafting.sql'")).first()
            assert row is not None, "Migration 017 must be recorded in schema_migrations"
        finally:
            db.close()

    def test_correction_drafts_columns_exist(self):
        db = SessionLocal()
        try:
            cols = db.execute(text(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'correction_drafts'"
            )).fetchall()
            col_dict = {c[0]: c[1] for c in cols}

            # Check newly added P3G columns
            assert "recipient_authority" in col_dict
            assert "subject" in col_dict
            assert "user_explanation" in col_dict
            assert "requested_action" in col_dict
            assert "supporting_documents" in col_dict
            assert "disclaimer" in col_dict
            assert "is_citizen_confirmed" in col_dict
            assert "citizen_confirmed_at" in col_dict
            assert "confirmed_version_number" in col_dict
            assert "sha256_hash" in col_dict
            assert "file_path" in col_dict
            assert "language" in col_dict
        finally:
            db.close()

    def test_correction_draft_versions_columns_exist(self):
        db = SessionLocal()
        try:
            cols = db.execute(text(
                "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'correction_draft_versions'"
            )).fetchall()
            col_dict = {c[0]: c[1] for c in cols}

            assert "recipient_authority" in col_dict
            assert "subject" in col_dict
            assert "confirmed_fields" in col_dict
            assert "supporting_documents" in col_dict
            assert "source_references" in col_dict
            assert "is_citizen_confirmed" in col_dict
            assert "citizen_confirmed_at" in col_dict
            assert "sha256_hash" in col_dict
        finally:
            db.close()

    def test_officer_policies_are_removed(self):
        """Verifies demonstrably obsolete officer policies have been pruned."""
        db = SessionLocal()
        try:
            policies = db.execute(text(
                "SELECT policyname FROM pg_policies WHERE tablename IN ('correction_drafts', 'correction_draft_versions')"
            )).fetchall()
            policy_names = [p[0] for p in policies]

            assert "p_drafts_officer_read" not in policy_names
            assert "p_draft_versions_officer_read" not in policy_names

            # Modern policies should exist
            assert "p_drafts_user" in policy_names
            assert "p_drafts_admin" in policy_names
            assert "p_draft_versions_user" in policy_names
            assert "p_draft_versions_admin" in policy_names
        finally:
            db.close()

    def test_forced_rls_enabled_on_draft_tables(self):
        """Verifies rowsecurity and relforcerowsecurity are active on both draft tables."""
        db = SessionLocal()
        try:
            res = db.execute(text(
                "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
                "WHERE relname IN ('correction_drafts', 'correction_draft_versions')"
            )).fetchall()
            for r in res:
                relname, rls_enabled, rls_forced = r[0], r[1], r[2]
                assert rls_enabled is True, f"RLS must be enabled on {relname}"
                assert rls_forced is True, f"RLS must be FORCED on {relname}"
        finally:
            db.close()

    def test_user_tenant_isolation_under_consolith_app(self):
        """Verifies user A cannot access user B's draft records."""
        db = SessionLocal()
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()

        try:
            # 0. Provision users first under admin context to satisfy FK constraint
            set_rls_context(db, uuid.uuid4(), "admin")
            user_a = User(
                id=user_a_id,
                firebase_uid=f"test_p3g_user_a_{uuid.uuid4().hex[:8]}",
                email=f"user_a_{uuid.uuid4().hex[:8]}@example.com",
                full_name="User Alpha Test",
                role="user",
            )
            user_b = User(
                id=user_b_id,
                firebase_uid=f"test_p3g_user_b_{uuid.uuid4().hex[:8]}",
                email=f"user_b_{uuid.uuid4().hex[:8]}@example.com",
                full_name="User Beta Test",
                role="user",
            )
            db.add_all([user_a, user_b])
            db.commit()

            # 1. Insert user A draft under user A context
            set_rls_context(db, user_a_id, "user")
            draft_a = CorrectionDraft(
                id=uuid.uuid4(),
                user_id=user_a_id,
                document_type=DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value,
                document_category=DocumentCategoryEnum.PAN.value,
                status=DraftStatusEnum.AI_GENERATED.value,
                title="PAN Name Rectification Draft",
                content="Sample petition content for User A",
                confirmed_fields={"applicant_name": "User Alpha"},
                disclaimer=MANDATORY_DRAFT_DISCLAIMER,
                version=1,
            )
            db.add(draft_a)
            db.commit()

            # 2. Query as user A -> should find 1 draft
            set_rls_context(db, user_a_id, "user")
            found_a = db.query(CorrectionDraft).filter(CorrectionDraft.id == draft_a.id).first()
            assert found_a is not None
            assert found_a.user_id == user_a_id

            # 3. Query as user B -> should return None (isolated)
            set_rls_context(db, user_b_id, "user")
            found_b = db.query(CorrectionDraft).filter(CorrectionDraft.id == draft_a.id).first()
            assert found_b is None, "User B must not see User A's draft"

            # 4. Admin query -> should see the draft
            set_rls_context(db, uuid.uuid4(), "admin")
            found_admin = db.query(CorrectionDraft).filter(CorrectionDraft.id == draft_a.id).first()
            assert found_admin is not None, "Admin must be able to query drafts for platform auditing"

            # Cleanup draft
            set_rls_context(db, user_a_id, "user")
            db.delete(draft_a)
            db.commit()
        finally:
            db.close()


class TestP3G1SchemasAndTaxonomy:
    """Verifies Pydantic schemas, 10 draft types, and deterministic compatibility matrix."""

    def test_ten_draft_types_defined(self):
        expected_types = [
            "identity_correction_request",
            "name_change_representation",
            "dob_rectification_request",
            "address_update_application",
            "parent_name_rectification",
            "educational_certificate_representation",
            "epf_member_correction_request",
            "general_administrative_representation",
            "supporting_document_cover_letter",
            "statutory_petition_representation",
        ]
        enum_values = [e.value for e in DraftTypeEnum]
        for t in expected_types:
            assert t in enum_values, f"DraftTypeEnum must define {t}"

    def test_six_document_categories_defined(self):
        expected_cats = ["aadhaar", "pan", "passport", "education_10th", "education_12th", "epf"]
        enum_values = [e.value for e in DocumentCategoryEnum]
        for c in expected_cats:
            assert c in enum_values, f"DocumentCategoryEnum must define {c}"

    def test_deterministic_compatibility_matrix(self):
        # Educational representation is applicable to education_10th and 12th, not PAN
        assert is_draft_type_applicable(DraftTypeEnum.EDUCATIONAL_CERTIFICATE_REPRESENTATION.value, "education_10th") is True
        assert is_draft_type_applicable(DraftTypeEnum.EDUCATIONAL_CERTIFICATE_REPRESENTATION.value, "education_12th") is True
        assert is_draft_type_applicable(DraftTypeEnum.EDUCATIONAL_CERTIFICATE_REPRESENTATION.value, "pan") is False

        # EPF member correction is applicable to EPF, not Passport
        assert is_draft_type_applicable(DraftTypeEnum.EPF_MEMBER_CORRECTION_REQUEST.value, "epf") is True
        assert is_draft_type_applicable(DraftTypeEnum.EPF_MEMBER_CORRECTION_REQUEST.value, "passport") is False

        # Name change representation is applicable to all 6 categories
        for cat in ["aadhaar", "pan", "passport", "education_10th", "education_12th", "epf"]:
            assert is_draft_type_applicable(DraftTypeEnum.NAME_CHANGE_REPRESENTATION.value, cat) is True

    def test_draft_response_serialization(self):
        draft_id = uuid.uuid4()
        user_id = uuid.uuid4()
        conflict_id = uuid.uuid4()
        now = datetime.utcnow()

        draft = CorrectionDraft(
            id=draft_id,
            user_id=user_id,
            conflict_id=conflict_id,
            document_type=DraftTypeEnum.DOB_RECTIFICATION_REQUEST.value,
            document_category=DocumentCategoryEnum.AADHAAR.value,
            status=DraftStatusEnum.CITIZEN_CONFIRMED.value,
            title="Aadhaar DOB Rectification Request",
            content="Statutory petition body...",
            recipient_authority="Unique Identification Authority of India",
            subject="Application for Date of Birth Rectification",
            user_explanation="Clerical error during 2012 biometric enrolment",
            requested_action="Update recorded DOB to 15/08/1990",
            confirmed_fields={"applicant_name": "Suresh Kumar", "date_of_birth": "15/08/1990"},
            supporting_documents=[{"document_type": "birth_certificate", "verified": True}],
            source_references=[{"source_id": "src_uidai_update_policy_2024", "authority": "UIDAI"}],
            disclaimer=MANDATORY_DRAFT_DISCLAIMER,
            is_citizen_confirmed=True,
            language="en",
            version=2,
            created_at=now,
            updated_at=now,
        )

        resp = CorrectionDraftResponse.model_validate(draft)
        assert resp.id == draft_id
        assert resp.document_type == DraftTypeEnum.DOB_RECTIFICATION_REQUEST.value
        assert resp.status == DraftStatusEnum.CITIZEN_CONFIRMED.value
        assert resp.is_citizen_confirmed is True
        assert resp.recipient_authority == "Unique Identification Authority of India"
        assert resp.disclaimer == MANDATORY_DRAFT_DISCLAIMER
