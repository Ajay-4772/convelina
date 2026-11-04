"""
CONVELINA - Phase P2C LLM Grounding, Real Provider Safety & Citation Validation Test Battery.
Tests:
1. Google Gemini Provider invocation & live JSON parsing.
2. Offline statutory fallback when Gemini is disabled (is_fallback=True, provider_status='fallback_offline').
3. Graceful handling of API authentication errors (401/403).
4. Transient error retry loop with exponential backoff (429 RateLimit).
5. Retries exhaustion fallback.
6. Network timeout handling.
7. Strict filtering of unverified knowledge sources (status != 'verified').
8. Strict filtering of outdated and retired knowledge sources.
9. Relevance score floor enforcement (< 0.55 returns empty -> explicit abstention).
10. Grounded output validator: stripping hallucinated citations and URLs.
11. Mandatory statutory disclaimer enforcement on all outputs.
12. Zero unmasked raw PII / Aadhaar leakage into prompts.
13. API endpoint (/api/v1/assistant/chat) integration with offline grounding.
14. Strict Cross-user RLS boundary enforcement for assistant conversations.
"""

import uuid
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.config import settings
from app.core.database import SessionLocal, set_rls_context
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.assistant import AssistantConversation, AssistantMessage
from app.rag.schemas import GroundedAnswer, SourceCitation
from app.rag.generation.llm_provider import GoogleGeminiProvider, MANDATORY_STATUTORY_DISCLAIMER
from app.rag.generation.output_validator import GroundedOutputValidator
from app.rag.retrieval.retriever import HybridRetriever
from app.rag.assistant.orchestrator import RAGOrchestrator

client = TestClient(app)


def create_test_user_session(prefix="p2c"):
    """Helper to provision a synthetic user and return auth headers and UUID."""
    uid = f"{prefix}_{uuid.uuid4().hex[:8]}"
    email = f"{uid}@convelina.test"
    name = f"Test Citizen {uid}"
    headers = {"Authorization": f"Bearer test_token_:{uid}:{email}:{name}"}

    resp = client.post(
        "/api/v1/auth/provision",
        headers=headers,
        json={"email": email, "full_name": name},
    )
    assert resp.status_code in (200, 201), f"Provisioning failed: {resp.text}"
    user_id = uuid.UUID(resp.json()["id"])
    return headers, user_id


def seed_document(user_id: uuid.UUID, doc_type: str, extracted_fields: dict) -> Document:
    """Helper to seed a document under user's RLS context."""
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
            masked_id=f"TEST-{doc_type.upper()}-1234",
        )
        db.add(doc)
        db.commit()
        return doc
    finally:
        db.close()


def seed_conflict(
    user_id: uuid.UUID,
    doc_a: Document,
    doc_b: Document,
    field_name: str = "full_name",
    val_a: str = "K SATHISH KUMAR",
    val_b: str = "SATHISH KUMAR",
    classification: str = "INITIAL_AMBIGUITY",
    requires_manual_review: bool = True,
    confidence_score: float = 0.85,
) -> Conflict:
    """Helper to seed a conflict with rich deterministic classification."""
    db = SessionLocal()
    try:
        set_rls_context(db, user_id, "user")
        conf = Conflict(
            id=uuid.uuid4(),
            user_id=user_id,
            doc_a_id=doc_a.id,
            doc_b_id=doc_b.id,
            conflict_type="unresolvable-needs-evidence",
            severity="medium",
            field_name=field_name,
            value_a=val_a,
            value_b=val_b,
            description=f"Inconsistency in {field_name} between {doc_a.document_type} and {doc_b.document_type}",
            status="detected",
            comparison_method="deterministic_p0_engine",
            similarity_score=round(confidence_score * 100, 2),
            metadata_={
                "classification": classification,
                "confidence_score": confidence_score,
                "requires_manual_review": requires_manual_review,
                "overall_classification": "AMBIGUOUS_NEEDS_REVIEW",
                "evidence": ["Initial 'K' absent in Document B"],
            },
        )
        db.add(conf)
        db.commit()
        return conf
    finally:
        db.close()


SAMPLE_CHUNKS = [
    {
        "chunk_id": "chunk_uidai_01",
        "source_id": "circ_uidai_2020_01",
        "title": "UIDAI Name Change Guidelines",
        "issuing_authority": "UIDAI",
        "source_url": "https://uidai.gov.in/circulars/name-correction",
        "document_category": "aadhaar",
        "verification_status": "verified",
        "content": "For minor name correction (spelling/initial expansion), submit standard Certificate issued by Gazetted Officer or Educational Board.",
        "score": 0.88,
    },
    {
        "chunk_id": "chunk_pan_01",
        "source_id": "circ_nsdl_pan_01",
        "title": "NSDL PAN Correction Instructions",
        "issuing_authority": "Income Tax Department / NSDL",
        "source_url": "https://www.onlineservices.nsdl.com/paam/endUserRegisterContact.html",
        "document_category": "pan",
        "verification_status": "verified",
        "content": "Submit Form 49A with Aadhaar as proof of identity to update PAN card name.",
        "score": 0.82,
    },
]

SAMPLE_FORMS = [
    {
        "form_id": "form_uidai_cert",
        "form_name": "UIDAI Standard Certificate for Address/Name Update",
        "document_category": "aadhaar",
        "purpose": "Standard identity and address certificate for Aadhaar enrollment/update",
        "issuing_authority": "UIDAI",
        "official_download_url": "https://uidai.gov.in/images/commdoc/valid_documents_list.pdf",
        "verification_status": "verified",
        "is_active": True,
    }
]


class TestP2CLLMGroundedIntelligence:
    """Dedicated test battery for Phase P2C."""

    def test_01_gemini_provider_live_mocked_success(self):
        """1. Live Gemini generation with valid mocked response parses JSON and sets operational status."""
        mock_gemini_response = MagicMock()
        mock_gemini_response.text = json.dumps({
            "answer": "CONVELINA detected an initial expansion discrepancy. Under UIDAI circulars, you can update your name via standard certificate.",
            "issue_summary": "Name initial expansion discrepancy",
            "resolution_steps": [
                {
                    "step_number": 1,
                    "title": "Gather Certificate",
                    "description": "Obtain standard gazetted certificate.",
                    "required_documents": ["Standard Certificate"],
                    "official_portal_or_form": "https://uidai.gov.in"
                }
            ],
            "potential_future_implications": [],
            "uncertainties": [],
            "citations": [
                {
                    "source_id": "circ_uidai_2020_01",
                    "title": "UIDAI Name Change Guidelines",
                    "authority": "UIDAI",
                    "url": "https://uidai.gov.in/circulars/name-correction"
                }
            ],
            "confidence": "supported"
        })

        provider = GoogleGeminiProvider(api_key="test_api_key_valid", model="gemini-1.5-flash")
        provider.client = MagicMock()
        provider.client.generate_content.return_value = mock_gemini_response

        with patch("app.config.settings.GEMINI_ENABLED", True):
            ans = provider.generate_answer(
                question="How do I update my name?",
                case_context={"deterministic_findings": {"field_name": "full_name"}},
                retrieved_chunks=SAMPLE_CHUNKS,
                relevant_forms=SAMPLE_FORMS,
                conversation_history=[]
            )

        assert isinstance(ans, GroundedAnswer)
        assert ans.is_fallback is False
        assert ans.provider_status == "operational"
        assert ans.confidence == "supported"
        assert len(ans.citations) == 1
        assert ans.citations[0].source_id == "circ_uidai_2020_01"
        assert ans.citations[0].url == "https://uidai.gov.in/circulars/name-correction"
        assert MANDATORY_STATUTORY_DISCLAIMER in ans.answer

    def test_02_gemini_disabled_returns_structured_statutory_fallback(self):
        """2. When Gemini is disabled (GEMINI_ENABLED=False), safe 3-layer statutory fallback is generated."""
        provider = GoogleGeminiProvider(api_key=None)

        case_context = {
            "deterministic_findings": {
                "field_name": "full_name",
                "classification": "INITIAL_AMBIGUITY",
                "confidence_score": 0.85,
                "requires_manual_review": True,
            },
            "resolution_mapping": {
                "procedure_name": "Minor Name Correction via Aadhaar Update",
                "procedure_type": "minor_correction",
                "authority_name": "UIDAI",
                "authority_portal": "https://myaadhaar.uidai.gov.in/",
                "submission_channel": "online_portal",
                "prescribed_forms": [
                    {
                        "form_id": "form_uidai_cert",
                        "form_name": "UIDAI Standard Certificate",
                        "issuing_authority": "UIDAI",
                        "official_download_url": "https://uidai.gov.in/standard_cert.pdf",
                        "purpose": "Aadhaar update"
                    }
                ],
                "document_checklist": ["Gazetted Officer Certificate", "PAN Card copy"],
                "statutory_rules": ["Aadhaar allows name correction up to two times in a lifetime."]
            }
        }

        with patch("app.config.settings.GEMINI_ENABLED", False):
            ans = provider.generate_answer(
                question="How do I fix this discrepancy?",
                case_context=case_context,
                retrieved_chunks=SAMPLE_CHUNKS,
                relevant_forms=SAMPLE_FORMS,
                conversation_history=[]
            )

        assert isinstance(ans, GroundedAnswer)
        assert ans.is_fallback is True
        assert ans.provider_status == "fallback_offline"
        # Layer A check
        assert "Layer A: Deterministic Identity Finding" in ans.answer
        assert "INITIAL_AMBIGUITY" in ans.answer
        # Layer B check
        assert "Layer B: Verified Statutory Guidance" in ans.answer
        assert "Minor Name Correction via Aadhaar Update" in ans.answer
        # Layer C check
        assert "Layer C: Manual Review & Statutory Boundaries" in ans.answer
        assert MANDATORY_STATUTORY_DISCLAIMER in ans.answer
        # Verified citations attached
        assert len(ans.citations) >= 1
        assert ans.citations[0].source_id == "circ_uidai_2020_01"

    def test_03_gemini_auth_error_handles_safely_without_crash(self):
        """3. When Gemini encounters a 401/403 API key error, it reverts immediately to statutory fallback."""
        provider = GoogleGeminiProvider(api_key="invalid_test_key")
        provider.client = MagicMock()
        provider.client.generate_content.side_effect = Exception("401 API_KEY_INVALID: User not found or key revoked")

        with patch("app.config.settings.GEMINI_ENABLED", True):
            ans = provider.generate_answer(
                question="What is the official procedure?",
                case_context={"deterministic_findings": {}},
                retrieved_chunks=SAMPLE_CHUNKS,
                relevant_forms=[],
                conversation_history=[]
            )

        assert isinstance(ans, GroundedAnswer)
        assert ans.is_fallback is True
        assert ans.provider_status == "fallback_offline"
        assert len(ans.citations) >= 1
        assert MANDATORY_STATUTORY_DISCLAIMER in ans.answer

    def test_04_gemini_rate_limit_retry_and_recovery(self):
        """4. When Gemini returns transient 429, retry succeeds and yields operational response."""
        mock_gemini_response = MagicMock()
        mock_gemini_response.text = json.dumps({
            "answer": "Recovered successfully on retry.",
            "issue_summary": "Name update procedure",
            "resolution_steps": [],
            "citations": [{"source_id": "circ_uidai_2020_01"}],
            "confidence": "supported"
        })

        provider = GoogleGeminiProvider(api_key="test_key", max_retries=1, backoff_factor=1.0)
        provider.client = MagicMock()
        # Fail once with 429, then succeed
        provider.client.generate_content.side_effect = [
            Exception("429 ResourceExhausted: rate limit exceeded"),
            mock_gemini_response,
        ]

        with patch("app.config.settings.GEMINI_ENABLED", True), patch("time.sleep", return_value=None):
            ans = provider.generate_answer(
                question="How do I update?",
                case_context={},
                retrieved_chunks=SAMPLE_CHUNKS,
                relevant_forms=[],
                conversation_history=[]
            )

        assert ans.is_fallback is False
        assert ans.provider_status == "operational"
        assert "Recovered successfully" in ans.answer

    def test_05_gemini_rate_limit_exhaustion_falls_back(self):
        """5. When all Gemini retries fail with 429, it falls back to statutory resolution."""
        provider = GoogleGeminiProvider(api_key="test_key", max_retries=1, backoff_factor=1.0)
        provider.client = MagicMock()
        provider.client.generate_content.side_effect = Exception("429 ResourceExhausted: quota exceeded")

        with patch("app.config.settings.GEMINI_ENABLED", True), patch("time.sleep", return_value=None):
            ans = provider.generate_answer(
                question="How do I update?",
                case_context={},
                retrieved_chunks=SAMPLE_CHUNKS,
                relevant_forms=[],
                conversation_history=[]
            )

        assert ans.is_fallback is True
        assert ans.provider_status == "fallback_offline"

    def test_06_gemini_timeout_handling(self):
        """6. When Gemini times out, it falls back gracefully."""
        provider = GoogleGeminiProvider(api_key="test_key", max_retries=0)
        provider.client = MagicMock()
        provider.client.generate_content.side_effect = TimeoutError("Request timed out after 15 seconds")

        with patch("app.config.settings.GEMINI_ENABLED", True):
            ans = provider.generate_answer(
                question="How do I update?",
                case_context={},
                retrieved_chunks=SAMPLE_CHUNKS,
                relevant_forms=[],
                conversation_history=[]
            )

        assert ans.is_fallback is True
        assert ans.provider_status == "fallback_offline"

    def test_07_retriever_filters_unverified_sources(self):
        """7. HybridRetriever strictly excludes unverified or inactive sources."""
        mock_qdrant = MagicMock()
        
        hit_verified = MagicMock()
        hit_verified.id = "hit1"
        hit_verified.score = 0.9
        hit_verified.payload = {
            "source_id": "circ_valid_01",
            "title": "Valid Circular",
            "verification_status": "verified",
            "is_active": True,
            "content": "Official valid circular instructions",
        }

        hit_unverified = MagicMock()
        hit_unverified.id = "hit2"
        hit_unverified.score = 0.95
        hit_unverified.payload = {
            "source_id": "circ_unverified_02",
            "title": "Unverified Circular",
            "verification_status": "needs_review",
            "is_active": True,
            "content": "Draft instructions not yet vetted",
        }

        hit_inactive = MagicMock()
        hit_inactive.id = "hit3"
        hit_inactive.score = 0.92
        hit_inactive.payload = {
            "source_id": "circ_inactive_03",
            "title": "Inactive Circular",
            "verification_status": "verified",
            "is_active": False,
            "content": "Old instructions",
        }

        mock_qdrant.search.return_value = [hit_verified, hit_unverified, hit_inactive]

        retriever = HybridRetriever(qdrant=mock_qdrant)
        retriever.embedding_service = MagicMock()
        retriever.embedding_service.embed_query.return_value = [0.1] * 1024

        results = retriever.retrieve("official circular instructions", min_score=0.1)
        source_ids = [r["source_id"] for r in results]

        assert "circ_valid_01" in source_ids
        assert "circ_unverified_02" not in source_ids
        assert "circ_inactive_03" not in source_ids

    def test_08_retriever_filters_outdated_and_retired_sources(self):
        """8. HybridRetriever strictly rejects outdated and retired sources."""
        mock_qdrant = MagicMock()

        hit_outdated = MagicMock()
        hit_outdated.id = "hit_outdated"
        hit_outdated.score = 0.88
        hit_outdated.payload = {
            "source_id": "circ_old_rule",
            "title": "Old Aadhaar Policy 2018",
            "verification_status": "outdated",
            "is_active": True,
            "content": "Superseded guidelines",
        }

        hit_retired = MagicMock()
        hit_retired.id = "hit_retired"
        hit_retired.score = 0.89
        hit_retired.payload = {
            "source_id": "circ_retired_rule",
            "title": "Retired Rule",
            "verification_status": "retired",
            "is_active": True,
            "content": "Retired circular",
        }

        mock_qdrant.search.return_value = [hit_outdated, hit_retired]

        retriever = HybridRetriever(qdrant=mock_qdrant)
        retriever.embedding_service = MagicMock()
        retriever.embedding_service.embed_query.return_value = [0.1] * 1024

        results = retriever.retrieve("aadhaar policy", min_score=0.1)
        assert len(results) == 0

    def test_09_retriever_relevance_floor_triggers_explicit_abstention(self):
        """9. When all retrieved chunks fall below 0.55 relevance floor, provider produces explicit abstention."""
        provider = GoogleGeminiProvider(api_key=None)

        ans = provider.generate_answer(
            question="What is the weather in Delhi?",
            case_context={},
            retrieved_chunks=[],  # Simulates below floor / empty retrieval
            relevant_forms=[],
            conversation_history=[]
        )

        assert ans.confidence == "insufficient_evidence"
        assert ans.provider_status == "insufficient_evidence"
        assert "No official procedural guidance could be verified" in ans.answer
        assert ">= 0.55" in ans.answer
        assert MANDATORY_STATUTORY_DISCLAIMER in ans.answer

    def test_10_output_validator_strips_hallucinated_citations(self):
        """10. GroundedOutputValidator strips non-existent source IDs and preserves official URLs."""
        raw_answer = {
            "answer": "Procedure explained here.",
            "citations": [
                {
                    "source_id": "fake_hallucinated_source_999",
                    "title": "Phishing or Made-up Doc",
                    "url": "http://scam-site.in/fake-form"
                },
                {
                    "source_id": "circ_uidai_2020_01",
                    "title": "Tampered Title",
                    "url": "http://tampered-url.com"  # Model altered URL
                }
            ],
            "confidence": "supported"
        }

        validated = GroundedOutputValidator.validate_and_filter_citations(
            raw_answer_dict=raw_answer,
            retrieved_chunks=SAMPLE_CHUNKS,
            is_fallback=False,
            provider_status="operational"
        )

        assert isinstance(validated, GroundedAnswer)
        # Fake source was stripped
        source_ids = [c.source_id for c in validated.citations]
        assert "fake_hallucinated_source_999" not in source_ids
        # Valid source was retained with authoritative official URL restored!
        assert "circ_uidai_2020_01" in source_ids
        uidai_cit = next(c for c in validated.citations if c.source_id == "circ_uidai_2020_01")
        assert uidai_cit.url == "https://uidai.gov.in/circulars/name-correction"

    def test_11_output_validator_enforces_mandatory_statutory_disclaimer(self):
        """11. GroundedOutputValidator always ensures mandatory statutory disclaimer is appended."""
        raw_answer = {
            "answer": "This is a direct advice without disclaimer.",
            "citations": [],
            "confidence": "supported"
        }

        validated = GroundedOutputValidator.validate_and_filter_citations(
            raw_answer_dict=raw_answer,
            retrieved_chunks=SAMPLE_CHUNKS,
            is_fallback=False
        )

        assert MANDATORY_STATUTORY_DISCLAIMER in validated.answer

    def test_12_zero_raw_pii_in_llm_prompt_and_context(self):
        """12. Privacy check: Raw 12-digit Aadhaar number is never leaked into RAG case context."""
        headers, user_id = create_test_user_session("p2c_privacy")
        # Seed Aadhaar with raw 12-digit number
        doc_a = seed_document(user_id, "aadhaar", {
            "full_name": "Rohan Sharma",
            "aadhaar_number": "999988887777",
            "dob": "1990-01-01"
        })
        doc_b = seed_document(user_id, "pan", {
            "full_name": "Rohan S",
            "pan_number": "ABCDE1234F"
        })
        conf = seed_conflict(user_id, doc_a, doc_b, "full_name", "Rohan Sharma", "Rohan S")

        db = SessionLocal()
        try:
            set_rls_context(db, user_id, "user")
            orchestrator = RAGOrchestrator(db)
            conf_id = uuid.UUID(str(conf.id))
            case_ctx = orchestrator._build_minimal_case_context(user_id, conf_id)

            ctx_json = json.dumps(case_ctx)
            # Ensure raw Aadhaar number does NOT appear anywhere in the context
            assert "999988887777" not in ctx_json
        finally:
            db.close()

    def test_13_assistant_chat_api_endpoint_offline_grounding(self):
        """13. Real API test: POST /api/v1/assistant/chat returns 200 with structured grounded guidance."""
        headers, user_id = create_test_user_session("p2c_chat")
        doc_a = seed_document(user_id, "aadhaar", {"full_name": "Priya Nair"})
        doc_b = seed_document(user_id, "pan", {"full_name": "Priya K Nair"})
        conf = seed_conflict(user_id, doc_a, doc_b, "full_name", "Priya Nair", "Priya K Nair")

        resp = client.post(
            "/api/v1/assistant/chat",
            headers=headers,
            json={
                "message": "How do I resolve the middle name discrepancy between my Aadhaar and PAN?",
                "conflict_id": str(conf.id),
            },
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "conversation_id" in data
        assert "message_id" in data
        assert "response" in data

        response_obj = data["response"]
        assert "answer" in response_obj
        assert response_obj["is_fallback"] is True  # In test environment, Gemini is offline
        assert response_obj["provider_status"] == "fallback_offline"
        assert MANDATORY_STATUTORY_DISCLAIMER in response_obj["answer"]

        # Verify DB persistence under citizen RLS
        db = SessionLocal()
        try:
            set_rls_context(db, user_id, "user")
            msg = db.query(AssistantMessage).filter(
                AssistantMessage.id == uuid.UUID(data["message_id"]),
                AssistantMessage.user_id == user_id
            ).first()
            assert msg is not None
            assert msg.structured_response.get("is_fallback") is True
            assert msg.structured_response.get("provider_status") == "fallback_offline"
        finally:
            db.close()

    def test_14_assistant_chat_cross_user_isolation(self):
        """14. Cross-user security: User A cannot query or ground against User B's conflict."""
        headers_a, user_a = create_test_user_session("p2c_user_a")
        headers_b, user_b = create_test_user_session("p2c_user_b")

        # User B has a conflict
        doc_b1 = seed_document(user_b, "aadhaar", {"full_name": "Private User B"})
        doc_b2 = seed_document(user_b, "pan", {"full_name": "Private B"})
        conf_b = seed_conflict(user_b, doc_b1, doc_b2, "full_name", "Private User B", "Private B")

        # User A attempts to chat referencing User B's conflict_id
        resp = client.post(
            "/api/v1/assistant/chat",
            headers=headers_a,
            json={
                "message": "Explain this conflict",
                "conflict_id": str(conf_b.id),
            },
        )
        # Should succeed without leaking User B's conflict (reconstructed context is None or empty)
        assert resp.status_code == 200
        data = resp.json()
        # Verify User B's private name is NOT present in User A's answer
        assert "Private User B" not in data["response"]["answer"]
