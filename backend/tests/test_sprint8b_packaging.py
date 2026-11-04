import pytest
import uuid
import numpy as np
from typing import Dict, Any

from app.config import settings
from app.rag.embeddings import (
    DeterministicHashEmbeddingService,
    DeterministicBGEEmbeddingService,
    VECTOR_DIMENSION,
    get_embedding_service,
)
from app.rag.qdrant import (
    get_qdrant_client,
    reset_qdrant_client,
    ensure_collections,
    ensure_knowledge_indexed,
)
from app.rag.retrieval.retriever import HybridRetriever
from app.rag.generation.llm_provider import (
    GoogleGeminiProvider,
    SERVICE_UNAVAILABLE_MESSAGE,
    get_llm_provider,
)


class TestEmbeddingImplementationAndRetrieval:
    """Task 3: Validate embedding implementation, vector dimensions, and retrieval characteristics."""

    def test_embedding_dimensions_and_determinism(self):
        svc = DeterministicHashEmbeddingService(dimension=1024)
        emb1 = svc.embed_query("Aadhaar date of birth update")
        emb2 = svc.embed_query("Aadhaar date of birth update")
        emb_diff = svc.embed_query("Passport police verification")

        assert len(emb1) == 1024
        assert len(emb2) == 1024
        assert emb1 == emb2  # Bit-for-bit exact reproducibility
        assert emb1 != emb_diff

        # Unit length (L2 norm should be 1.0)
        norm = np.linalg.norm(np.array(emb1))
        assert abs(norm - 1.0) < 1e-5

    def test_backward_compatible_alias(self):
        # Both classes must point to the same implementation
        assert DeterministicBGEEmbeddingService is DeterministicHashEmbeddingService
        svc = get_embedding_service()
        assert isinstance(svc, DeterministicHashEmbeddingService)

    def test_exact_keywords_vs_synonyms_cosine_divergence(self):
        """
        Confirms Task 3 finding:
        Shared keywords produce high positive cosine similarity (> 0.70).
        Synonyms with zero lexical overlap produce negative or near-zero similarity (< 0.0),
        failing the 0.55 similarity floor as expected for a unigram hash projection.
        """
        svc = DeterministicHashEmbeddingService(dimension=1024)

        def cos_sim(t1: str, t2: str) -> float:
            v1 = np.array(svc.embed_query(t1))
            v2 = np.array(svc.embed_query(t2))
            return float(np.dot(v1, v2))

        q = "Aadhaar name correction"
        t_keywords = "Aadhaar name update guidelines"
        t_synonyms = "UIDAI resident demographic modification"
        t_unrelated = "chocolate cake baking recipe"

        sim_keywords = cos_sim(q, t_keywords)
        sim_synonyms = cos_sim(q, t_synonyms)
        sim_unrelated = cos_sim(q, t_unrelated)

        assert sim_keywords >= 0.70  # Passes 0.55 floor
        assert sim_synonyms < 0.0   # Fails 0.55 floor
        assert abs(sim_unrelated) < 1e-4  # Zero orthogonal similarity


class TestInProcessQdrantLifecycle:
    """Task 2: Validate in-process Qdrant mode, collection seeding, retrieval, and restart."""

    def test_in_process_qdrant_seeding_and_retrieval(self, monkeypatch):
        # Ensure in-process memory mode
        monkeypatch.setattr(settings, "QDRANT_IN_PROCESS", True)
        monkeypatch.setattr(settings, "QDRANT_LOCATION", ":memory:")
        reset_qdrant_client()

        # Seed knowledge
        result = ensure_knowledge_indexed()
        assert result["chunks_indexed"] >= 20
        assert result["forms_indexed"] >= 5
        assert result["total_chunks"] >= 20

        # Retrieve through HybridRetriever
        retriever = HybridRetriever()
        results = retriever.retrieve("Aadhaar name correction", document_category="aadhaar", top_k=3)
        assert len(results) > 0
        top = results[0]
        assert top["issuing_authority"] == "Unique Identification Authority of India (UIDAI)"
        assert "Aadhaar" in top["title"] or "UIDAI" in top["title"]
        assert top["score"] >= 0.55

    def test_in_process_qdrant_restart_simulation(self, monkeypatch):
        """Simulates container cold start / process restart where in-memory state vanishes."""
        monkeypatch.setattr(settings, "QDRANT_IN_PROCESS", True)
        monkeypatch.setattr(settings, "QDRANT_LOCATION", ":memory:")

        # Process 1 starts and indexes
        reset_qdrant_client()
        res1 = ensure_knowledge_indexed()
        assert res1["chunks_indexed"] >= 20

        # Process 1 terminates: memory wiped
        reset_qdrant_client()

        # Process 2 starts: collections and points reconstructed cleanly from canonical code sources
        res2 = ensure_knowledge_indexed()
        assert res2["chunks_indexed"] >= 20
        assert res2["total_chunks"] >= 20


class TestDocumentHandlingAndProductionSafetyValidation:
    """Task 4 & Task 7: Validate production settings, retention policy, and LLM safeguards."""

    def test_production_validator_enforces_delete_after_ocr(self, monkeypatch):
        from app.config import Settings
        from cryptography.fernet import Fernet

        valid_fernet = Fernet.generate_key().decode()

        # Production with invalid retention policy must fail closed
        with pytest.raises(ValueError, match="Privacy violation: STORAGE_RETENTION_POLICY must be 'delete_after_ocr'"):
            Settings(
                ENVIRONMENT="production",
                DEBUG=False,
                STORAGE_RETENTION_POLICY="retain_temp",
                ENCRYPTION_KEY=valid_fernet,
                DATABASE_URL="postgresql://consolith_app:valid_password_here@postgres:5432/consolith",
                FIREBASE_PROJECT_ID="convelina-prod",
                CORS_ORIGINS=["https://convelina.vercel.app"],
                TEST_MODE_ALLOW_SIMULATED_TOKENS=False,
            )

    def test_production_validator_allows_disabled_gemini(self):
        from app.config import Settings
        from cryptography.fernet import Fernet

        valid_fernet = Fernet.generate_key().decode()

        # Production with GEMINI_ENABLED=False should not require GEMINI_API_KEY
        s = Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            STORAGE_RETENTION_POLICY="delete_after_ocr",
            ENCRYPTION_KEY=valid_fernet,
            DATABASE_URL="postgresql://consolith_app:valid_password_here@postgres:5432/consolith",
            FIREBASE_PROJECT_ID="convelina-prod",
            CORS_ORIGINS=["https://convelina.vercel.app"],
            GEMINI_ENABLED=False,
            GEMINI_API_KEY=None,
            TEST_MODE_ALLOW_SIMULATED_TOKENS=False,
        )
        assert s.GEMINI_ENABLED is False

    def test_gemini_disabled_safe_degradation_message(self, monkeypatch):
        """Task 7: When LLM is disabled or unconfigured, it must safely return the exact fallback message."""
        provider = GoogleGeminiProvider(api_key=None)
        assert provider.is_configured is False
        assert provider.generate("Test prompt") == SERVICE_UNAVAILABLE_MESSAGE
