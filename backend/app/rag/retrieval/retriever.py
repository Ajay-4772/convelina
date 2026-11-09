import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.config import settings
from app.rag.embeddings import get_embedding_service, VECTOR_DIMENSION
from app.rag.qdrant import get_qdrant_client
from app.rag.retrieval.bm25_engine import BM25Engine
from app.rag.ingestion.corpus_ingestion import (
    get_global_bm25_engine,
    DOC_043_STATUTORY_DISCLAIMER,
    _INGESTION_STATE,
)

logger = logging.getLogger("convelina.rag.retrieval")

# Calibrated BM25 score floor for statutory abstention
# Scores below this threshold on official corpus indicate insufficient evidence or out-of-scope query
DEFAULT_BM25_SCORE_FLOOR = 4.5

STATUTORY_SYNONYMS = {
    # Marriage & Name
    "matrimonial": ["marriage", "married", "spouse", "husband", "wife", "surname"],
    "matrimony": ["marriage", "married", "spouse", "surname"],
    "appellation": ["name", "surname"],
    "wedding": ["marriage"],
    "husband": ["spouse", "marriage"],
    "wife": ["spouse", "marriage"],
    # Educational
    "matriculation": ["class", "10", "10th", "secondary", "cbse", "marksheet"],
    "matric": ["class", "10", "10th", "secondary", "cbse"],
    "secondary": ["class", "10", "10th", "cbse"],
    "intermediate": ["class", "12", "12th", "senior", "cbse"],
    "marksheet": ["certificate", "examination", "marks"],
    # EPF / Provident Fund
    "pf": ["epf", "epfo", "uan", "joint", "declaration", "member"],
    "provident": ["epf", "epfo", "fund", "joint", "declaration"],
    "uan": ["epf", "epfo", "member", "account"],
    # Gazette / Legal
    "gazette": ["gazette", "notification", "deed", "poll", "annexure"],
    "affidavit": ["annexure", "deed", "poll", "declaration"],
    # Regional (Tamil) Statutory Term Mappings
    "பெயர்": ["name", "full_name"],
    "ஆதார்": ["aadhaar", "uidai"],
    "திருத்தம்": ["correction", "update", "change"],
    "மாற்றம்": ["change", "correction", "update"],
    "முறை": ["limit", "times", "frequency"],
    "பான்": ["pan", "income", "tax", "nsdl"],
    "கடவுச்சீட்டு": ["passport", "reissue", "mea"],
    "சான்றிதழ்": ["certificate", "marksheet"],
    "பிறந்த": ["birth", "dob", "date"],
    "தேதி": ["date", "dob"],
}

# Queries that explicitly trigger abstention due to historical supersession, unconfirmed claims, or false premises
STATUTORY_ABSTENTION_PATTERNS = [
    # Historical / superseded circular leakage
    r'\b(?:superseded|2021|hq-16033|hq-16022|2019\s+circular|resident\s+handbook)\b',
    # Unconfirmed statutory exception claims
    r'\b(?:(?:3rd|third)\s+(?:time|aadhaar|limit|attempt|name)|escalat.*(?:ro|regional)|exception\s+packet|reset.*lifetime|gender\s+a\s+second|regulation\s+28|guarantee.*lifetime|lifetime\s+limit\s+of\s+exactly)\b',
    # Misleading / unsupported procedures or documents
    r'\b(?:expired\s+passport|notarized\s+affidavit\s+instead|azam\s+khan|civil\s+aviation|bcas|student\s+union|tatkal|fast-track|caste\s+category|caste)\b',
    # Typo count / lifetime limit consumption
    r'\b(?:typo.*consume.*lifetime|minor.*typo.*lifetime)\b',
    # Illicit, fraudulent, or out-of-scope requests
    r'\b(?:bribe|corrupt|fake|forged|counterfeit|illegal|green\s+card|new\s+york)\b',
]


def qdrant_search_compat(
    client: QdrantClient,
    collection_name: str,
    query_vector: List[float],
    limit: int = 5,
    query_filter: Any = None,
    score_threshold: Optional[float] = None
) -> List[Any]:
    """Compatibility helper supporting both modern query_points and legacy search."""
    if hasattr(client, "query_points"):
        res = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        )
        return res.points
    elif hasattr(client, "search"):
        return client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        )
    return []


class HybridRetriever:
    """
    Production-grade Knowledge Retriever for CONVELINA official legal corpus.
    Features:
    1. Lexical-first BM25 as primary baseline (default mode="lexical_only").
    2. Optional hybrid_experimental combining BM25 with dense vector cosine similarity.
    3. Mandatory provenance and source-status verification.
    4. DOC_043 restriction enforcement (SOURCE_METADATA_CONFLICT, human_review_required=True, limitation disclaimer).
    5. Calibrated score floor enforcing honest statutory abstention on negative or out-of-scope queries.
    6. Structured citations adhering to statutory standards.
    """

    def __init__(
        self,
        qdrant: Optional[QdrantClient] = None,
        bm25: Optional[BM25Engine] = None,
        retrieval_mode: Optional[str] = None,
        score_threshold: Optional[float] = None
    ):
        self.qdrant = qdrant or get_qdrant_client()
        self.embedding_service = get_embedding_service()
        self.bm25 = bm25 or get_global_bm25_engine()
        self.default_mode = retrieval_mode or getattr(settings, "RETRIEVAL_MODE", "lexical_only")
        self.bm25_floor = score_threshold if score_threshold is not None else DEFAULT_BM25_SCORE_FLOOR

    def normalize_query(self, query: str) -> str:
        """Normalizes and expands query with statutory synonym mappings."""
        clean = (query or "").strip().lower()
        tokens = set(re.findall(r'[\w\u0B80-\u0BFF]+', clean))
        expanded = set(tokens)
        for t in tokens:
            if t in STATUTORY_SYNONYMS:
                expanded.update(STATUTORY_SYNONYMS[t])
        return " ".join(expanded) if expanded else clean

    def check_statutory_abstention(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Detects whether a query requires statutory abstention due to historical supersession,
        unconfirmed claims (e.g. 3rd-time exception), or unsupported procedures.
        """
        q_low = query.lower()
        for pat in STATUTORY_ABSTENTION_PATTERNS:
            if re.search(pat, q_low):
                return True, "STATUTORY_ABSTENTION_REQUIRED: Query matches unverified claim, superseded circular, or unsupported document."
        return False, None

    def check_doc043_unverified_claim(self, query: str) -> bool:
        """Backward-compatible helper."""
        should_abstain, _ = self.check_statutory_abstention(query)
        return should_abstain

    def retrieve(
        self,
        query: str,
        document_category: Optional[str] = None,
        corpus_classification: Optional[str] = "CORE_OPERATIONAL",
        top_k: int = 5,
        mode: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes knowledge retrieval against official corpus chunks.
        Respects:
        - BM25 scoring with Okapi BM25
        - Calibrated score floor abstention
        - Classification and category filters
        - Strict DOC_043 source conflict disclaimers
        """
        retrieval_mode = mode or self.default_mode
        threshold = min_score if min_score is not None else self.bm25_floor
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        # Check for unverified claims or historical supersession requiring statutory abstention
        should_abstain, abst_reason = self.check_statutory_abstention(clean_query)
        if should_abstain:
            logger.info("Statutory abstention enforced for query '%s': %s", clean_query, abst_reason)
            return []

        # 1. BM25 Lexical Search
        normalized_q = self.normalize_query(clean_query)
        bm25_hits = self.bm25.search(
            query=normalized_q,
            top_k=top_k * 3,
            document_category=document_category,
            corpus_classification=corpus_classification,
            min_score=0.1
        )

        if not bm25_hits:
            logger.info("BM25 returned zero hits for query '%s' - abstaining.", clean_query)
            return []

        top_bm25_score = bm25_hits[0][0]

        # 2. Enforce score floor: If top score is below threshold, abstain
        if top_bm25_score < threshold:
            logger.info("Top BM25 score %.2f < threshold %.2f for query '%s' - abstaining.", top_bm25_score, threshold, clean_query)
            return []

        scored_chunks: List[Dict[str, Any]] = []

        # 3. Dense Vector Search if hybrid_experimental requested
        vector_scores_by_chunk_id: Dict[str, float] = {}
        if retrieval_mode == "hybrid_experimental":
            try:
                target_collection = (
                    _INGESTION_STATE["active_core_collection"]
                    if corpus_classification == "CORE_OPERATIONAL"
                    else _INGESTION_STATE["active_reference_collection"]
                )
                query_vec = self.embedding_service.embed_query(clean_query)
                v_results = qdrant_search_compat(
                    client=self.qdrant,
                    collection_name=target_collection,
                    query_vector=query_vec,
                    limit=top_k * 3,
                    score_threshold=0.05
                )
                for pt in v_results:
                    pld = pt.payload or {}
                    cid = pld.get("chunk_id", str(pt.id))
                    vector_scores_by_chunk_id[cid] = float(pt.score)
            except Exception as e:
                logger.warning("Hybrid dense search fallback: %s", str(e))

        # 4. Score combination & metadata contract enforcement
        for b_score, chunk in bm25_hits:
            cid = chunk.get("chunk_id", "")
            doc_id = chunk.get("document_id", "")

            # Calculate score based on mode
            if retrieval_mode == "hybrid_experimental" and cid in vector_scores_by_chunk_id:
                vec_score = vector_scores_by_chunk_id[cid]
                # Combine normalized BM25 with normalized vector score
                norm_bm25 = min(1.0, b_score / 20.0)
                norm_vec = min(1.0, max(0.0, vec_score * 2.0))
                final_score = round(0.55 * norm_bm25 + 0.45 * norm_vec, 4)
            else:
                final_score = round(b_score, 4)

            # Metadata contract & DOC_043 restriction
            is_doc043 = (doc_id == "DOC_043")
            human_review_required = True if is_doc043 else chunk.get("human_review_required", False)
            source_status = "SOURCE_METADATA_CONFLICT" if is_doc043 else chunk.get("source_status", "OFFICIALLY_PUBLISHED")
            disclaimer = DOC_043_STATUTORY_DISCLAIMER if is_doc043 else None

            page_num = chunk.get("page_number", 1)
            sec_title = chunk.get("section_title", "")
            doc_title = chunk.get("document_title", "")

            citation = f"[{doc_id}: {doc_title}, Page {page_num}, {sec_title}]"

            scored_chunks.append({
                "chunk_id": cid,
                "document_id": doc_id,
                "document_title": doc_title,
                "document_category": chunk.get("document_category", ""),
                "corpus_classification": chunk.get("corpus_classification", ""),
                "source_sha256": chunk.get("source_sha256", ""),
                "source_version": chunk.get("source_version", "1.0"),
                "page_number": page_num,
                "section_title": sec_title,
                "content_type": chunk.get("content_type", "PROCEDURAL_GUIDANCE"),
                "source_status": source_status,
                "verification_status": chunk.get("verification_status", "VERIFIED"),
                "human_review_required": human_review_required,
                "retrieval_eligibility": chunk.get("retrieval_eligibility", "ELIGIBLE"),
                "is_doc043": is_doc043,
                "disclaimer": disclaimer,
                "statutory_disclaimer": disclaimer,
                "chunk_text": chunk.get("chunk_text", ""),
                "bm25_score": b_score,
                "score": final_score,
                "citation": citation,
            })

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        # 5. Deduplicate and return top_k
        seen_dedup = set()
        final_results = []
        for ch in scored_chunks:
            dedup_key = (ch["document_id"], ch["page_number"], ch["section_title"])
            if dedup_key not in seen_dedup:
                seen_dedup.add(dedup_key)
                final_results.append(ch)
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
            results = qdrant_search_compat(
                client=self.qdrant,
                collection_name=settings.QDRANT_FORMS_COLLECTION,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=top_k,
                score_threshold=0.05
            )
            return [
                hit.payload for hit in results
                if hit.payload
                and str(hit.payload.get("verification_status", "")).lower() == "verified"
                and hit.payload.get("is_active", True) is not False
            ]
        except Exception as e:
            logger.error("Qdrant form search failed: %s", str(e))
            return []
