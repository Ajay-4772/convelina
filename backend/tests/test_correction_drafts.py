"""Consolith - Module 7 Tests

Tests the Correction Document Generator:
- DocumentValidator checks (placeholders, disclaimers, warnings)
- Gemini-only architecture enforcement (Mocked success vs unconfigured vs failure)
- Service unavailable message enforcement: "Assistant service is not currently available. Please try again later."
- No fallback rule-based generation or secondary providers
- PDF generation via ReportLab (valid bytes, formatting)
- DOCX generation via python-docx (valid bytes, formatting)
"""

import io
import pytest
from unittest.mock import MagicMock, patch
from app.services.document_generator import (
    CorrectionDocumentGenerator,
    DocumentValidator,
    DRAFT_DISCLAIMER,
    SUPPORTED_DOCUMENT_TYPES,
)
from app.services.document_exporter import DocumentExporter
from app.rag.generation.llm_provider import GEMINI_UNAVAILABLE_MESSAGE


class TestDocumentValidator:
    def test_detects_unresolved_placeholders(self):
        content = f"{DRAFT_DISCLAIMER}\n\nTo,\nThe Regional Passport Officer\nSubject: Request to rectify [Applicant Name]\nEnclosures: None"
        res = DocumentValidator.validate(content)
        assert res["is_valid"] is True
        assert "Applicant Name" in res["unresolved_placeholders"]
        assert any("unresolved placeholder" in w for w in res["warnings"])

    def test_detects_missing_disclaimer(self):
        content = "To Whom It May Concern\nPlease correct my name in PAN records.\nEnclosures: Aadhaar Copy"
        res = DocumentValidator.validate(content)
        assert res["has_disclaimer"] is False
        assert any("Draft disclaimer was missing" in w for w in res["warnings"])

    def test_clean_document_validation(self):
        content = f"{DRAFT_DISCLAIMER}\n\nTo,\nUnique Identification Authority of India\nSubject: Correction\nEnclosures:\n- Class 10 Certificate"
        res = DocumentValidator.validate(content)
        assert res["is_valid"] is True
        assert len(res["unresolved_placeholders"]) == 0
        assert res["has_disclaimer"] is True


class TestCorrectionDocumentGenerator:
    def test_gemini_unconfigured_fails_safely_with_exact_message(self):
        generator = CorrectionDocumentGenerator()
        # Force LLM provider to appear unconfigured
        generator.llm_provider.api_key = None
        generator.llm_provider.client = None

        success, content, sources, val = generator.generate_draft(
            document_type="correction_request_letter",
            document_category="pan",
            conflicting_field="name",
            confirmed_fields={"applicant_name": "Rajesh Kumar"},
        )

        assert success is False
        assert content == "Assistant service is not currently available. Please try again later."
        assert val["is_valid"] is False

    @patch("app.rag.generation.llm_provider.GoogleGeminiProvider.generate")
    def test_gemini_failure_returns_exact_service_unavailable_message(self, mock_generate):
        mock_generate.side_effect = Exception("Google API quota exhausted or connection timeout")

        generator = CorrectionDocumentGenerator()
        generator.llm_provider.api_key = "test_gemini_key"
        generator.llm_provider.client = MagicMock()
        generator.llm_provider.raw_client = MagicMock()

        success, content, sources, val = generator.generate_draft(
            document_type="correction_request_letter",
            document_category="passport",
            conflicting_field="date_of_birth",
            confirmed_fields={"requested_value": "1995-05-12"},
        )

        assert success is False
        assert content == "Assistant service is not currently available. Please try again later."
        assert val["is_valid"] is False

    @patch("app.rag.generation.llm_provider.GoogleGeminiProvider.generate")
    def test_successful_gemini_generation_includes_disclaimer_and_placeholders(self, mock_generate):
        mock_output = (
            "To,\nThe Regional Passport Office, Delhi\n\n"
            "Subject: Correction of Date of Birth in Passport Records\n\n"
            "Sir/Madam,\nI, Rajesh Kumar, request to correct my date of birth from [Recorded DOB] to 12/05/1995.\n\n"
            "Enclosures:\n1. Birth Certificate"
        )
        mock_generate.return_value = mock_output

        generator = CorrectionDocumentGenerator()
        generator.llm_provider.api_key = "test_gemini_key"
        generator.llm_provider.client = MagicMock()
        generator.llm_provider.raw_client = MagicMock()

        # Mock retriever to avoid external dependencies in unit test
        generator.retriever = MagicMock()
        generator.retriever.retrieve.return_value = [
            {
                "title": "Passport Rules 1980 - DOB Rectification",
                "issuing_authority": "Ministry of External Affairs",
                "document_category": "passport",
                "score": 0.88,
                "source_url": "https://passportindia.gov.in",
                "content": "Official circular for passport date of birth correction.",
            }
        ]

        success, content, sources, val = generator.generate_draft(
            document_type="correction_request_letter",
            document_category="passport",
            conflicting_field="date_of_birth",
            confirmed_fields={
                "applicant_name": "Rajesh Kumar",
                "requested_value": "12/05/1995",
            },
        )

        assert success is True
        assert DRAFT_DISCLAIMER in content
        assert "Regional Passport Office" in content
        assert len(sources) == 1
        assert sources[0]["authority"] == "Ministry of External Affairs"
        assert "Recorded DOB" in val["unresolved_placeholders"]


class TestDocumentExporter:
    def test_export_pdf_creates_valid_pdf_stream(self):
        title = "PAN Card Name Correction Application"
        content = f"{DRAFT_DISCLAIMER}\n\nTo,\nNSDL e-Gov / Protean\n\nSubject: Name Correction\n\nEnclosures:\n- Aadhaar Card"
        pdf_bytes = DocumentExporter.export_pdf(title, content)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 500
        # Check standard PDF magic header %PDF-
        assert pdf_bytes.startswith(b"%PDF-")

    def test_export_docx_creates_valid_docx_stream(self):
        title = "Aadhaar Date of Birth Rectification Request"
        content = f"{DRAFT_DISCLAIMER}\n\nTo,\nUIDAI Regional Office\n\nSubject: DOB Update\n\n- Enclosure 1: Birth Certificate [Unverified]"
        docx_bytes = DocumentExporter.export_docx(title, content)

        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 500
        # DOCX is a zip archive, starts with PK (0x50, 0x4B)
        assert docx_bytes.startswith(b"PK")
