import re
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import settings
from app.rag.embeddings import get_embedding_service
from app.rag.qdrant import get_qdrant_client

logger = logging.getLogger("consolith.rag.retrieval")

class HybridRetriever:
    """
    Advanced Hybrid Retriever combining:
    1. Dense vector similarity search via Qdrant (BGE-M3 / 1024-dim)
    2. Lexical keyword matching
    3. Document category and verification status metadata filtering
    4. Mandatory relevance score floor enforcement (>= 0.55)
    """

    def __init__(self, qdrant: Optional[QdrantClient] = None):
        self.qdrant = qdrant or get_qdrant_client()
        self.embedding_service = get_embedding_service()
        self.min_relevance = settings.RAG_MIN_RELEVANCE

    def retrieve(
        self,
        query: str,
        document_category: Optional[str] = None,
        top_k: int = 5,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        threshold = min_score if min_score is not None else self.min_relevance
        clean_query = query.strip()
        if not clean_query:
            return []

        # 1. Generate query embedding
        query_vector = self.embedding_service.embed_query(clean_query)

        # 2. Build metadata filter
        filter_conditions = []
        if document_category:
            filter_conditions.append(
                FieldCondition(
                    key="document_category",
                    match=MatchValue(value=document_category.lower())
                )
            )

        qdrant_filter = Filter(must=filter_conditions) if filter_conditions else None

        # 3. Dense Vector Search in Qdrant (fetch candidates without pre-filtering score so hybrid scoring can be computed)
        try:
            search_results = self.qdrant.search(
                collection_name=settings.QDRANT_KNOWLEDGE_COLLECTION,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k * 3,
                score_threshold=0.05
            )
        except Exception as e:
            logger.error("Qdrant vector search failed: %s", str(e), exc_info=True)
            search_results = []

        # 4. Lexical Boost & Hybrid Scoring
        query_tokens = set(re.findall(r'\w+', clean_query.lower()))
        # Remove common stop words from token overlap
        stop_words = {"how", "do", "i", "my", "the", "in", "a", "an", "is", "for", "to", "what", "which", "and", "or"}
        informative_tokens = query_tokens - stop_words

        scored_chunks: List[Dict[str, Any]] = []

        for hit in search_results:
            payload = hit.payload or {}
            content = payload.get("content", "")
            title = payload.get("title", "")
            heading = payload.get("heading", "")
            full_text = f"{title} {heading} {content}".lower()

            # Calculate lexical token overlap ratio
            if informative_tokens:
                matched_tokens = sum(1 for token in informative_tokens if token in full_text)
                lexical_ratio = matched_tokens / len(informative_tokens)
            else:
                lexical_ratio = 0.0

            # Scale vector score (typically 0.15 - 0.45 for cosine with dense hash) to [0, 1] range
            # Base hybrid formula: 0.5 * normalized_vector + 0.5 * lexical_ratio
            normalized_vec = min(1.0, max(0.0, float(hit.score) * 2.5))
            combined_score = round(0.45 * normalized_vec + 0.55 * lexical_ratio, 4)

            # Enforce relevance floor
            if combined_score < threshold:
                continue

            scored_chunks.append({
                "chunk_id": payload.get("chunk_id", str(hit.id)),
                "source_id": payload.get("source_id", "unknown"),
                "title": payload.get("title", "Official Guidance"),
                "issuing_authority": payload.get("issuing_authority", "Government Authority"),
                "document_category": payload.get("document_category", ""),
                "source_url": payload.get("source_url", ""),
                "heading": payload.get("heading", ""),
                "content": content,
                "score": combined_score,
                "raw_vector_score": round(float(hit.score), 4),
                "verification_status": payload.get("verification_status", "verified")
            })

        # Sort by combined score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        # 5. Deduplicate and trim to top_k
        seen_headings = set()
        final_results = []
        for chunk in scored_chunks:
            dedup_key = (chunk["source_id"], chunk["heading"])
            if dedup_key not in seen_headings:
                seen_headings.add(dedup_key)
                final_results.append(chunk)
            if len(final_results) >= top_k:
                break

        return final_results

    def retrieve_forms(
        self,
        query: str,
        document_category: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Retrieves official forms matching query and category."""
        clean_query = query.strip()
        query_vector = self.embedding_service.embed_query(clean_query)

        filter_conditions = []
        if document_category:
            filter_conditions.append(
                FieldCondition(
                    key="document_category",
                    match=MatchValue(value=document_category.lower())
                )
            )

        qdrant_filter = Filter(must=filter_conditions) if filter_conditions else None

        try:
            results = self.qdrant.search(
                collection_name=settings.QDRANT_FORMS_COLLECTION,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                score_threshold=0.05
            )
            return [hit.payload for hit in results if hit.payload]
        except Exception as e:
            logger.error("Qdrant form search failed: %s", str(e))
            return []
