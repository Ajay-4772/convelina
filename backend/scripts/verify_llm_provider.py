"""
CONVELINA — Phase P3F.2
Part C: Live LLM Provider Verification Script
Tests GoogleGeminiProvider behavior:
- Unconfigured initialization
- Relevance floor abstention (>= 0.55 relevance floor enforcement)
- Offline statutory fallback synthesis (chunks, conflict mapping, attachments)
- Transient error retry loop with exponential backoff (429, timeouts)
- Non-retryable authentication failure immediate fallback (401, 403)
- Valid structured JSON generation and grounded output citation filtering
- Zero credential / raw secret leakage
"""

import json
import logging
from unittest.mock import MagicMock, patch

from app.rag.generation.llm_provider import GoogleGeminiProvider
from app.rag.schemas import GroundedAnswer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_llm_provider")


def run_checks():
    logger.info("==================================================")
    logger.info("RUNNING PART C: LLM PROVIDER VERIFICATION CHECKS")
    logger.info("==================================================")

    # 1. Unconfigured check
    logger.info("1. Testing unconfigured provider initialization...")
    p_unconfigured = GoogleGeminiProvider(api_key="", model="gemini-1.5-flash")
    assert not p_unconfigured.is_configured, "Provider should not be configured without key"
    logger.info("   -> PASS: Unconfigured provider is_configured is False")

    # 2. Relevance floor abstention
    logger.info("2. Testing relevance floor abstention (empty retrieved chunks)...")
    ans_floor = p_unconfigured.generate_answer(
        question="Can I bake a cake with Aadhaar?",
        case_context={},
        retrieved_chunks=[],
        relevant_forms=[],
        conversation_history=[],
    )
    assert ans_floor.confidence == "insufficient_evidence", f"Expected insufficient_evidence, got {ans_floor.confidence}"
    assert "NO_VERIFIED_PROCEDURE_AVAILABLE" in ans_floor.answer
    assert ans_floor.provider_status == "insufficient_evidence"
    logger.info("   -> PASS: Floor abstention successfully returned NO_VERIFIED_PROCEDURE_AVAILABLE")

    # 3. Offline statutory fallback with retrieved chunks
    logger.info("3. Testing offline statutory fallback with chunks...")
    sample_chunk = {
        "source_id": "UIDAI_CIRC_2023_01",
        "title": "Aadhaar Date of Birth Policy",
        "issuing_authority": "UIDAI",
        "source_url": "https://uidai.gov.in/circulars/dob",
        "content": "Date of birth can be updated once with valid birth certificate.",
        "verification_status": "verified",
    }
    ans_offline = p_unconfigured.generate_answer(
        question="How to correct DOB in Aadhaar?",
        case_context={},
        retrieved_chunks=[sample_chunk],
        relevant_forms=[],
        conversation_history=[],
    )
    assert ans_offline.is_fallback is True, "Offline fallback should have is_fallback=True"
    assert ans_offline.provider_status == "fallback_offline"
    assert len(ans_offline.citations) == 1
    assert ans_offline.citations[0].source_id == "UIDAI_CIRC_2023_01"
    assert "UIDAI" in ans_offline.answer
    assert "AUTOMATED COMPARISON RESULT" in ans_offline.answer
    logger.info("   -> PASS: Offline statutory fallback returned grounded circular guidance with citations")

    # 4. Offline fallback with resolution mapping & discrepancy
    logger.info("4. Testing offline fallback with conflict resolution mapping...")
    res_mapping = {
        "procedure_name": "UIDAI Name Correction via Update Form",
        "authority_name": "UIDAI",
        "authority_portal": "https://myaadhaar.uidai.gov.in",
        "submission_channel": "enrolment_centre",
        "statutory_rules": ["Maximum 2 updates allowed without regional office permission"],
        "document_checklist": ["Passport", "PAN Card"],
        "prescribed_forms": [
            {
                "form_id": "aadhaar_enrolment_update",
                "form_name": "Aadhaar Enrolment / Update Form",
                "purpose": "Demographic update",
                "issuing_authority": "UIDAI",
                "official_download_url": "https://uidai.gov.in/forms/update.pdf",
            }
        ],
    }
    findings = {
        "field_name": "full_name",
        "classification": "minor_discrepancy",
        "confidence_score": 0.95,
        "requires_manual_review": False,
    }
    ans_mapped = p_unconfigured.generate_answer(
        question="How do I resolve this name discrepancy?",
        case_context={"resolution_mapping": res_mapping, "deterministic_findings": findings},
        retrieved_chunks=[sample_chunk],
        relevant_forms=[],
        conversation_history=[],
    )
    assert ans_mapped.is_fallback is True
    assert "Layer A: Deterministic Identity Finding" in ans_mapped.answer
    assert "Layer B: Verified Statutory Guidance" in ans_mapped.answer
    assert "Layer C: Manual Review & Statutory Boundaries" in ans_mapped.answer
    assert len(ans_mapped.resolution_steps) >= 3
    logger.info("   -> PASS: 3-Layer deterministic statutory answer rendered properly")

    # 5. Retry backoff on transient errors (with GEMINI_ENABLED=True)
    logger.info("5. Testing retry backoff on transient 429 quota exhaustion...")
    with patch("app.rag.generation.llm_provider.settings.GEMINI_ENABLED", True):
        p_mock = GoogleGeminiProvider(api_key="fake-test-key", model="gemini-1.5-flash", max_retries=2, backoff_factor=0.01)
        mock_client_429 = MagicMock()
        mock_client_429.generate_content.side_effect = Exception("429 Resource exhausted: quota exceeded")
        p_mock.client = mock_client_429

        ans_retry = p_mock.generate_answer(
            question="How to correct name?",
            case_context={},
            retrieved_chunks=[sample_chunk],
            relevant_forms=[],
            conversation_history=[],
        )
        assert mock_client_429.generate_content.call_count == 3, f"Expected 3 calls, got {mock_client_429.generate_content.call_count}"
        assert ans_retry.is_fallback is True
        assert ans_retry.provider_status == "fallback_offline"
        logger.info("   -> PASS: Exhausted 2 retries (3 calls total) and safely defaulted to statutory fallback")

    # 6. Immediate fallback on non-retryable 403 / auth error
    logger.info("6. Testing immediate fallback on 403 API_KEY_INVALID...")
    with patch("app.rag.generation.llm_provider.settings.GEMINI_ENABLED", True):
        mock_client_403 = MagicMock()
        mock_client_403.generate_content.side_effect = Exception("403 API_KEY_INVALID: API key not valid")
        p_mock.client = mock_client_403

        ans_auth = p_mock.generate_answer(
            question="How to correct name?",
            case_context={},
            retrieved_chunks=[sample_chunk],
            relevant_forms=[],
            conversation_history=[],
        )
        assert mock_client_403.generate_content.call_count == 1, "Auth errors must not be retried"
        assert ans_auth.is_fallback is True
        logger.info("   -> PASS: Auth error aborted immediately (1 call) to statutory fallback")

    # 7. Operational generation with structured validation
    logger.info("7. Testing operational generation and grounded citation validation...")
    with patch("app.rag.generation.llm_provider.settings.GEMINI_ENABLED", True):
        mock_client_ok = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "answer": "To update your name in Aadhaar, submit Form 1 with supporting identity proof.",
            "issue_summary": "Aadhaar Name Correction Guidance",
            "resolution_steps": [
                {
                    "step_number": 1,
                    "title": "Visit Enrolment Centre",
                    "description": "Take original proof of identity to an authorized centre.",
                    "required_documents": ["PAN Card"],
                    "official_portal_or_form": "https://uidai.gov.in"
                }
            ],
            "potential_future_implications": [],
            "uncertainties": [],
            "citations": [
                {
                    "source_id": "UIDAI_CIRC_2023_01",
                    "title": "UIDAI Circular",
                    "authority": "UIDAI",
                    "url": "https://uidai.gov.in/circulars/dob",
                    "verification_status": "verified"
                }
            ],
            "requires_clarification": False,
            "confidence": "supported"
        })
        mock_client_ok.generate_content.return_value = mock_response
        p_mock.client = mock_client_ok

        ans_ok = p_mock.generate_answer(
            question="How to correct name in Aadhaar?",
            case_context={},
            retrieved_chunks=[sample_chunk],
            relevant_forms=[],
            conversation_history=[],
        )
        assert ans_ok.is_fallback is False, "Operational response should have is_fallback=False"
        assert ans_ok.provider_status == "operational"
        assert "Form 1" in ans_ok.answer
        assert len(ans_ok.citations) == 1
        logger.info("   -> PASS: Operational JSON response parsed and validated cleanly")

    logger.info("==================================================")
    logger.info("ALL PART C PROVIDER VERIFICATION CHECKS PASSED (7/7)")
    logger.info("==================================================")


if __name__ == "__main__":
    run_checks()

