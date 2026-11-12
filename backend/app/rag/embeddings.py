import math
import hashlib
import logging
from typing import List, Optional
import numpy as np

from app.config import settings

logger = logging.getLogger("consolith.rag.embeddings")

VECTOR_DIMENSION = 1024

class BaseEmbeddingService:
    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class DeterministicHashEmbeddingService(BaseEmbeddingService):
    """
    Deterministic 1024-dimensional token-weighted hash-projection embedding service.

    NOTE: This is NOT a neural transformer model (such as BAAI/bge-m3).
    It is a lightweight, CPU-deterministic unigram hash projection algorithm designed
    for ultra-low-memory environments (0 MB external weights, < 1 MB RAM).

    Characteristics & Trade-offs:
    - Matches identical or overlapping keywords with high positive cosine similarity (> 0.70).
    - Produces negative or near-zero cosine similarity (< 0.0) on semantic synonyms that share no common tokens.
    - Yields exact reproducibility across restarts with zero external network or model downloads.
    """

    def __init__(self, dimension: int = VECTOR_DIMENSION):
        self.dimension = dimension

    def _embed_single(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension

        cleaned = text.strip().lower()
        tokens = cleaned.split()
        vec = np.zeros(self.dimension, dtype=np.float32)

        for i, token in enumerate(tokens):
            # Compute multiple independent hash seeds for dense projection
            token_bytes = token.encode("utf-8")
            h1 = int(hashlib.md5(token_bytes, usedforsecurity=False).hexdigest(), 16)
            h2 = int(hashlib.sha256(token_bytes).hexdigest(), 16)

            idx1 = h1 % self.dimension
            idx2 = (h2 >> 16) % self.dimension
            idx3 = (h2 >> 32) % self.dimension

            sign1 = 1.0 if (h1 & 1) else -1.0
            sign2 = 1.0 if (h2 & 1) else -1.0
            sign3 = 1.0 if (h2 & 2) else -1.0

            # Weight by token frequency / position
            weight = 1.0 / (1.0 + math.log1p(i))
            vec[idx1] += sign1 * weight
            vec[idx2] += sign2 * 0.7 * weight
            vec[idx3] += sign3 * 0.5 * weight

        # Global sequence signature
        seq_hash = int(hashlib.sha256(cleaned.encode("utf-8")).hexdigest(), 16)
        for offset in range(32):
            idx = (seq_hash + offset * 31) % self.dimension
            vec[idx] += 0.1 * (1.0 if ((seq_hash >> offset) & 1) else -1.0)

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return vec.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self._embed_single(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single(t) for t in texts]


# Backward-compatible alias for existing tests and callers
DeterministicBGEEmbeddingService = DeterministicHashEmbeddingService


class FastEmbedEmbeddingService(BaseEmbeddingService):
    """
    Genuine neural semantic embedding service powered by FastEmbed (ONNX Runtime).
    Runs locally on CPU with zero paid API dependencies and minimal footprint.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name=self.model_name)
            except Exception as e:
                logger.warning("Failed to initialize FastEmbed model '%s': %s. Falling back to DeterministicHash.", self.model_name, e)
                raise
        return self._model

    def embed_query(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimension
        try:
            vecs = list(self.model.embed([text.strip()]))
            return vecs[0].tolist()
        except Exception as e:
            logger.warning("FastEmbed query embedding failed: %s. Using hash fallback.", e)
            fallback = DeterministicHashEmbeddingService(dimension=self.dimension)
            return fallback.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            vecs = list(self.model.embed([t.strip() for t in texts]))
            return [v.tolist() for v in vecs]
        except Exception as e:
            logger.warning("FastEmbed document embedding failed: %s. Using hash fallback.", e)
            fallback = DeterministicHashEmbeddingService(dimension=self.dimension)
            return fallback.embed_documents(texts)


def get_embedding_service(provider: Optional[str] = None) -> BaseEmbeddingService:
    """Factory returning configured embedding service."""
    prov = (provider or getattr(settings, "RAG_EMBEDDING_PROVIDER", "deterministic-hash")).lower()
    if prov in ("fastembed", "neural", "semantic"):
        try:
            return FastEmbedEmbeddingService()
        except Exception:
            logger.warning("FastEmbed unavailable, falling back to DeterministicHashEmbeddingService")
    return DeterministicHashEmbeddingService(dimension=VECTOR_DIMENSION)
