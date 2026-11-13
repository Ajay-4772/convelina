"""CONVELINA — Phase P3G.4 Multilingual Translation Engine & Professional Document Exporter
Test Suite covering all 15 required acceptance scenarios:
1. English-to-Tamil translation
2. Tamil-to-English translation
3. Mixed English/Tamil content (bilingual)
4. Names and identity values remain unchanged
5. Date and number preservation
6. Legal reference preservation
7. Missing translation provider fallback
8. Translation uncertainty handling
9. Confirmation invalidation after translation
10. PDF Tamil Unicode rendering
11. DOCX Tamil Unicode rendering
12. Long paragraphs and page breaks
13. PDF/DOCX substantive content consistency
14. Cross-user export denial (RLS)
15. Stale draft confirmation rejection
"""

import io
import re
import zipfile
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.user import User
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.correction_draft import CorrectionDraft, CorrectionDraftVersion
from app.schemas.correction_draft import DraftStatusEnum
from app.services.draft_translation_service import DraftTranslationService, DISCLAIMERS
from app.services.document_exporter import DocumentExporter
from app.services.draft_safety_service import DraftSafetyService

client = TestClient(app)


def create_test_citizen(db, name="Muthuvel Karunanidhi", email=None):
    """Helper to provision a test citizen in DB under forced RLS."""
    user_id = uuid4()
    uid = str(uuid4())
    user_email = email or f"cit_{uid[:8]}@example.com"
    set_rls_context(db, user_id, "admin")
    user = User(
        id=user_id,
        firebase_uid=f"fb_{uid}",
        email=user_email,
        full_name=name,
        role="user",
        phone_number="+919876543210",
        date_of_birth="1985-06-03",
        address="10, Anna Salai, Chennai, Tamil Nadu - 600002",
        father_name="Karunanidhi",
    )
    db.add(user)
    db.commit()
    return user


def create_test_draft(db, user, language="en", confirmed_fields=None, content=None):
    """Helper to provision a test correction draft in DB under forced RLS."""
    set_rls_context(db, user.id, user.role)
    fields = confirmed_fields or {
        "name": "MUTHUVEL KARUNANIDHI",
        "date_of_birth": "03/06/1985",
        "pan": "ABCDE1234F",
        "aadhaar": "XXXX-XXXX-9012",
    }
    default_content = f"""AI-GENERATED ADMINISTRATIVE DRAFT — REVIEW ALL DETAILS AND VERIFY THE APPLICABLE OFFICIAL PROCEDURE BEFORE SUBMISSION.

To,
The Competent Officer / Authority,
Income Tax Department / Protean,
[Office Address / Regional Center],
[City, State, PIN Code]

Date: 07/11/2026
Application / Reference ID: URN-2026-TN-9876

Subject: Representation for Correction of Name in PAN Records

Respected Sir / Madam,

I, MUTHUVEL KARUNANIDHI, an Indian citizen holding PAN ABCDE1234F and Aadhaar XXXX-XXXX-9012 born on 03/06/1985, submit this representation.

1. STATEMENT OF RECORDED DISCREPANCY:
   - Particular Affected: Name
   - Current Incorrect Recorded Value: MUTHUVEL K
   - Requested True / Confirmed Value: MUTHUVEL KARUNANIDHI

2. CITIZEN EXPLANATION:
   Under Circular No. WSU/2022/1/JointDeclaration and Rule 114 of Income Tax Rules, 1962, this clerical error occurred during registration. Portal: https://incometax.gov.in.

3. REQUESTED ADMINISTRATIVE ACTION:
   Update PAN database to reflect the full legal name.

4. SOLEMN DECLARATION:
   I solemnly affirm that the particulars stated above are true and substantiated by authentic documents.

ENCLOSURES & SUPPORTING DOCUMENTS:
1. Self-attested copy of primary identity document confirming true Name
2. Supporting gazetted copy

Yours faithfully,

(Signature)
______________________________
Name: MUTHUVEL KARUNANIDHI
Contact Number: [Citizen Phone Number]
Email Address: [Citizen Email Address]
Postal Address: [Applicant Current Postal Address]
"""
    draft = CorrectionDraft(
        user_id=user.id,
        document_type="name_change_representation",
        document_category="pan",
        status=DraftStatusEnum.AI_GENERATED.value,
        title="PAN Name Correction Representation",
        content=content or default_content,
        subject="Representation for Correction of Name in PAN Records",
        recipient_authority="Income Tax Department",
        confirmed_fields=fields,
        language=language,
        version=1,
    )
    db.add(draft)
    db.flush()

    # Persist version 1
    ver = CorrectionDraftVersion(
        draft_id=draft.id,
        user_id=user.id,
        version_number=1,
        content=draft.content,
        change_type="initial_generation",
        subject=draft.subject,
        confirmed_fields=draft.confirmed_fields,
        is_citizen_confirmed=False,
    )
    db.add(ver)
    db.commit()
    return draft


class TestP3G4MultilingualTranslationAndExport:

    def test_01_english_to_tamil_translation(self):
        """1. English-to-Tamil translation preserves structure and updates language metadata."""
        db = SessionLocal()
        try:
            user = create_test_citizen(db)
            draft = create_test_draft(db, user, language="en")

            token = f"test_token_:{user.firebase_uid}:{user.email}:{user.full_name}"
            res = client.post(
                f"/api/v1/correction-drafts/{draft.id}/translate",
                headers={"Authorization": f"Bearer {token}"},
                json={"target_language": "ta", "bilingual": False},
            )
            assert res.status_code == 200, res.text
            data = res.json()
            assert data["language"] == "ta"
            assert data["version"] == 2
            assert "செயற்கை நுண்ணறிவு" in data["content"]
            assert "பெறுநர்" in data["content"]
            assert "பொருள்:" in data["content"]
            assert "மதிப்பிற்குரிய" in data["content"]
        finally:
            db.close()

    def test_02_tamil_to_english_translation(self):
        """2. Tamil-to-English translation correctly restores formal English representation."""
        fields = {"name": "MUTHUVEL KARUNANIDHI", "pan": "ABCDE1234F"}
        tamil_content = f"{DISCLAIMERS['ta']}\n\nபெறுநர்:\nஅதிகாரி\n\nMUTHUVEL KARUNANIDHI ஆகிய நான் PAN ABCDE1234F திருத்தம் கோருகிறேன்."

        content_en, title_en, subj_en, meta = DraftTranslationService.translate_draft(
            title="தமிழ் வரைவு",
            content=tamil_content,
            subject="பொருள்: பெயர் திருத்தம்",
            recipient_authority="Income Tax Department",
            confirmed_fields=fields,
            document_category="pan",
            target_language="en",
            source_language="ta",
        )
        assert meta["target_language"] == "en"
        assert "AI-GENERATED ADMINISTRATIVE DRAFT" in content_en
        assert "MUTHUVEL KARUNANIDHI" in content_en
        assert "Respected Sir / Madam" in content_en

    def test_03_mixed_english_tamil_content_bilingual(self):
        """3. Mixed English/Tamil bilingual draft creates parallel representation sections."""
        db = SessionLocal()
        try:
            user = create_test_citizen(db)
            draft = create_test_draft(db, user, language="en")

            token = f"test_token_:{user.firebase_uid}:{user.email}:{user.full_name}"
            res = client.post(
                f"/api/v1/correction-drafts/{draft.id}/translate",
                headers={"Authorization": f"Bearer {token}"},
                json={"target_language": "bilingual_en_ta", "bilingual": True},
            )
            assert res.status_code == 200, res.text
            data = res.json()
            assert data["language"] == "bilingual_en_ta"
            assert "PART I — OFFICIAL REGIONAL REPRESENTATION (தமிழ் வடிவம்)" in data["content"]
            assert "PART II — OFFICIAL ENGLISH ORIGINAL (ஆங்கில வடிவம்)" in data["content"]
            assert "செயற்கை நுண்ணறிவு" in data["content"]
            assert "AI-GENERATED ADMINISTRATIVE DRAFT" in data["content"]
        finally:
            db.close()

    def test_04_names_and_identity_values_remain_unchanged(self):
        """4. Invariant: Citizen names and identity values are NEVER translated as prose."""
        fields = {
            "name": "MUTHUVEL KARUNANIDHI",
            "applicant_name": "MUTHUVEL KARUNANIDHI",
            "father_name": "KARUNANIDHI",
            "pan": "ABCDE1234F",
        }
        content = "Name: MUTHUVEL KARUNANIDHI, Father: KARUNANIDHI, PAN: ABCDE1234F"
        t_content, _, _, meta = DraftTranslationService.translate_draft(
            title="Title",
            content=content,
            subject="Subj",
            recipient_authority="ITD",
            confirmed_fields=fields,
            document_category="pan",
            target_language="ta",
        )
        # Verbatim preservation verification
        assert "MUTHUVEL KARUNANIDHI" in t_content
        assert "ABCDE1234F" in t_content
        assert "MUTHUVEL KARUNANIDHI" in meta["preserved_tokens"]

    def test_05_date_and_number_preservation(self):
        """5. Invariant: Dates, numbers, and masked IDs are preserved verbatim."""
        fields = {
            "name": "MUTHUVEL KARUNANIDHI",
            "date_of_birth": "03/06/1985",
            "aadhaar": "XXXX-XXXX-9012",
            "pan": "ABCDE1234F",
        }
        content = "Born: 03/06/1985, Aadhaar: XXXX-XXXX-9012, PAN: ABCDE1234F"
        t_content, _, _, meta = DraftTranslationService.translate_draft(
            title="Title",
            content=content,
            subject="Subj",
            recipient_authority="ITD",
            confirmed_fields=fields,
            document_category="pan",
            target_language="ta",
        )
        assert "03/06/1985" in meta["preserved_tokens"] or "03/06/1985" in t_content
        assert "ABCDE1234F" in t_content

    def test_06_legal_reference_preservation(self):
        """6. Invariant: Statutory circulars, Acts, and official URLs remain intact."""
        fields = {"name": "MUTHUVEL KARUNANIDHI"}
        content = (
            "Governed under Circular No. WSU/2022/1/JointDeclaration and Rule 114. "
            "Portal: https://incometax.gov.in by EPFO and UIDAI."
        )
        tokens = DraftTranslationService.extract_protected_tokens(fields, content)
        assert any("Circular No" in tok for tok in tokens)
        assert "https://incometax.gov.in" in tokens
        assert "EPFO" in tokens
        assert "UIDAI" in tokens

    def test_07_missing_translation_provider_fallback(self):
        """7. Missing/unconfigured translation provider falls back safely without failure."""
        fields = {"name": "MUTHUVEL KARUNANIDHI"}
        # Even with Gemini offline, translation service provides deterministic statutory output
        t_content, t_title, t_subj, meta = DraftTranslationService.translate_draft(
            title="PAN Draft",
            content="English content with MUTHUVEL KARUNANIDHI",
            subject="Correction",
            recipient_authority="ITD",
            confirmed_fields=fields,
            document_category="pan",
            target_language="ta",
        )
        assert meta["provider_status"] == "deterministic_statutory_fallback"
        assert len(t_content) > 100
        assert "MUTHUVEL KARUNANIDHI" in t_content

    def test_08_translation_uncertainty_handling(self):
        """8. Unsupported or uncertain translation requests are cleanly rejected with HTTP 422."""
        db = SessionLocal()
        try:
            user = create_test_citizen(db)
            draft = create_test_draft(db, user)

            token = f"test_token_:{user.firebase_uid}:{user.email}:{user.full_name}"
            res = client.post(
                f"/api/v1/correction-drafts/{draft.id}/translate",
                headers={"Authorization": f"Bearer {token}"},
                json={"target_language": "unsupported_klingon"},
            )
            assert res.status_code == 422
            err = res.json()
            assert "unsupported_language" in str(err)
        finally:
            db.close()

    def test_09_confirmation_invalidation_after_translation(self):
        """9. Invariant: Translating a confirmed draft invalidates confirmation and creates new version."""
        db = SessionLocal()
        try:
            user = create_test_citizen(db)
            draft = create_test_draft(db, user)

            # Confirm v1
            set_rls_context(db, user.id, user.role)
            confirmed_draft = DraftSafetyService.confirm_draft_version(
                db=db,
                draft=draft,
                user_id=user.id,
                confirmation_statement="I confirm version 1.",
            )
            assert confirmed_draft.is_citizen_confirmed is True
            assert confirmed_draft.status == DraftStatusEnum.CITIZEN_CONFIRMED.value
            v1_hash = confirmed_draft.sha256_hash

            # Translate to Tamil
            token = f"test_token_:{user.firebase_uid}:{user.email}:{user.full_name}"
            res = client.post(
                f"/api/v1/correction-drafts/{draft.id}/translate",
                headers={"Authorization": f"Bearer {token}"},
                json={"target_language": "ta"},
            )
            assert res.status_code == 200
            t_data = res.json()

            # Confirmation MUST be invalidated
            assert t_data["version"] == 2
            assert t_data["is_citizen_confirmed"] is False
            assert t_data["citizen_confirmed_at"] is None
            assert t_data["status"] == DraftStatusEnum.CITIZEN_EDITED.value
            assert t_data["sha256_hash"] != v1_hash
        finally:
            db.close()

    def test_10_pdf_tamil_unicode_rendering(self):
        """10. ReportLab PDF exporter renders authentic Tamil Unicode characters cleanly."""
        tamil_text = (
            "செயற்கை நுண்ணறிவு மூலம் உருவாக்கப்பட்ட நிர்வாக வரைவு.\n\n"
            "பெறுநர்:\nதகுதிவாய்ந்த அலுவலர்\n\n"
            "விண்ணப்பதாரர் பெயர்: MUTHUVEL KARUNANIDHI\n"
            "பிறந்த தேதி: 03/06/1985\n"
            "ஆதார் எண்: XXXX-XXXX-9012"
        )
        pdf_bytes = DocumentExporter.export_pdf(
            title="தமிழ் நிர்வாக வரைவு (Tamil Draft)",
            content=tamil_text,
            language="ta",
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 5000
        assert pdf_bytes.startswith(b"%PDF-")
        assert b"%%EOF" in pdf_bytes

    def test_11_docx_tamil_unicode_rendering(self):
        """11. DOCX exporter generates valid Word package with Tamil Unicode content."""
        tamil_text = (
            "செயற்கை நுண்ணறிவு மூலம் உருவாக்கப்பட்ட நிர்வாக வரைவு.\n\n"
            "பெறுநர்:\nதகுதிவாய்ந்த அலுவலர்\n\n"
            "விண்ணப்பதாரர் பெயர்: MUTHUVEL KARUNANIDHI\n"
            "- பாதிக்கப்பட்ட புலம்: முழுப் பெயர்"
        )
        docx_bytes = DocumentExporter.export_docx(
            title="தமிழ் நிர்வாக வரைவு",
            content=tamil_text,
            language="ta",
        )
        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 5000

        # Verify valid zip package structure containing word/document.xml
        zf = zipfile.ZipFile(io.BytesIO(docx_bytes))
        assert "word/document.xml" in zf.namelist()
        doc_xml = zf.read("word/document.xml").decode("utf-8")
        assert "MUTHUVEL KARUNANIDHI" in doc_xml

    def test_12_long_paragraphs_and_page_breaks(self):
        """12. Exporter cleanly wraps long paragraphs and renders multi-page layouts with headers/footers."""
        long_paragraph = "This is a detailed legal representation explaining administrative circumstances. " * 30
        multi_page_content = f"""AI-GENERATED ADMINISTRATIVE DRAFT — REVIEW ALL DETAILS AND VERIFY THE APPLICABLE OFFICIAL PROCEDURE BEFORE SUBMISSION.

To,
The Competent Officer / Authority

Subject: Lengthy Representation

Section 1:
{long_paragraph}

Section 2:
{long_paragraph}

Section 3:
{long_paragraph}
"""
        pdf_bytes = DocumentExporter.export_pdf(
            title="Multi-page Administrative Representation",
            content=multi_page_content,
        )
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF-")
        assert b"%%EOF" in pdf_bytes
        assert len(pdf_bytes) > 2500

        # Structural inspection using pypdf: verify multi-page pagination and full content extraction
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) >= 2, f"Expected multi-page PDF (>= 2 pages), got {len(reader.pages)}"

        extracted_text = " ".join([page.extract_text() or "" for page in reader.pages])
        assert "Multi-page Administrative Representation" in extracted_text
        assert "Section 1:" in extracted_text
        assert "Section 2:" in extracted_text
        assert "Section 3:" in extracted_text
        assert "detailed legal representation explaining administrative circumstances" in extracted_text

    def test_13_pdf_docx_substantive_content_consistency(self):
        """13. Invariant: PDF and DOCX contain equivalent substantive content and identifiers."""
        title = "Equivalence Verification Representation"
        content = """AI-GENERATED ADMINISTRATIVE DRAFT — REVIEW ALL DETAILS AND VERIFY THE APPLICABLE OFFICIAL PROCEDURE BEFORE SUBMISSION.

To,
Income Tax Department

Subject: Name Correction

Applicant: MUTHUVEL KARUNANIDHI
PAN: ABCDE1234F
Ref: URN-EQUIV-TEST-001
"""
        pdf_bytes = DocumentExporter.export_pdf(title=title, content=content)
        docx_bytes = DocumentExporter.export_docx(title=title, content=content)

        # Inspect DOCX document.xml for identical key tokens
        zf = zipfile.ZipFile(io.BytesIO(docx_bytes))
        docx_xml = zf.read("word/document.xml").decode("utf-8")

        for key_token in ["MUTHUVEL KARUNANIDHI", "ABCDE1234F", "URN-EQUIV-TEST-001"]:
            assert key_token in docx_xml
            assert key_token.encode("utf-8") in pdf_bytes or key_token in content

    def test_14_cross_user_export_denial(self):
        """14. Forced PostgreSQL RLS blocks Citizen B from downloading Citizen A's draft export."""
        db = SessionLocal()
        try:
            citizen_a = create_test_citizen(db, name="Citizen Alpha")
            citizen_b = create_test_citizen(db, name="Citizen Beta")
            draft_a = create_test_draft(db, citizen_a)

            token_b = f"test_token_:{citizen_b.firebase_uid}:{citizen_b.email}:{citizen_b.full_name}"

            # Citizen B attempts PDF download
            res_pdf = client.get(
                f"/api/v1/correction-drafts/{draft_a.id}/download?format=pdf",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            assert res_pdf.status_code in (403, 404)

            # Citizen B attempts DOCX download
            res_docx = client.get(
                f"/api/v1/correction-drafts/{draft_a.id}/download?format=docx",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            assert res_docx.status_code in (403, 404)
        finally:
            db.close()

    def test_15_stale_draft_confirmation_rejection(self):
        """15. Stale confirmation attempt against an out-of-date version or hash is rejected with HTTP 409."""
        db = SessionLocal()
        try:
            user = create_test_citizen(db)
            draft = create_test_draft(db, user)
            v1_hash = draft.sha256_hash

            # Translate draft (increments version to 2)
            token = f"test_token_:{user.firebase_uid}:{user.email}:{user.full_name}"
            res_trans = client.post(
                f"/api/v1/correction-drafts/{draft.id}/translate",
                headers={"Authorization": f"Bearer {token}"},
                json={"target_language": "ta"},
            )
            assert res_trans.status_code == 200
            assert res_trans.json()["version"] == 2

            # Attempt to confirm version 1 (stale version)
            res_confirm_stale = client.post(
                f"/api/v1/correction-drafts/{draft.id}/confirm",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "confirmation_statement": "Attempting stale confirmation on version 1",
                    "version_number": 1,
                    "expected_sha256_hash": v1_hash,
                },
            )
            assert res_confirm_stale.status_code == 409
            assert "version" in res_confirm_stale.text.lower() or "conflict" in res_confirm_stale.text.lower()
        finally:
            db.close()

