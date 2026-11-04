import logging
import uuid
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.config import settings
from app.rag.embeddings import VECTOR_DIMENSION, get_embedding_service
from app.rag.ingestion.sources import OFFICIAL_SOURCES_DATA, OFFICIAL_FORMS_DATA
from app.rag.ingestion.chunker import DocumentChunker

logger = logging.getLogger("consolith.rag.qdrant")

_qdrant_client_instance: Optional[QdrantClient] = None

def get_qdrant_client() -> QdrantClient:
    """Returns singleton Qdrant client connection (in-process or external)."""
    global _qdrant_client_instance
    if _qdrant_client_instance is None:
        if settings.QDRANT_IN_PROCESS or settings.QDRANT_LOCATION:
            loc = settings.QDRANT_LOCATION or ":memory:"
            logger.info("Initializing in-process Qdrant client (location=%s)", loc)
            _qdrant_client_instance = QdrantClient(location=loc)
        else:
            logger.info("Connecting to external Qdrant at %s:%d", settings.QDRANT_HOST, settings.QDRANT_PORT)
            _qdrant_client_instance = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                timeout=5.0
            )
    return _qdrant_client_instance


def reset_qdrant_client():
    """Resets client instance (used in tests to simulate fresh process restarts)."""
    global _qdrant_client_instance
    _qdrant_client_instance = None


def ensure_collections():
    """
    Idempotently verifies and creates Qdrant collections for official knowledge and forms.
    Uses 1024-dimensional vectors with Cosine distance metric.
    """
    client = get_qdrant_client()
    existing_collections = [c.name for c in client.get_collections().collections]

    collections_to_init = [
        settings.QDRANT_KNOWLEDGE_COLLECTION,
        settings.QDRANT_FORMS_COLLECTION
    ]

    for col_name in collections_to_init:
        if col_name not in existing_collections:
            logger.info("Creating Qdrant collection: %s (dim=%d, Cosine)", col_name, VECTOR_DIMENSION)
            client.create_collection(
                collection_name=col_name,
                vectors_config=VectorParams(size=VECTOR_DIMENSION, distance=Distance.COSINE)
            )
            # In server mode, create payload index. Local Qdrant ignores payload indexes.
            if not (settings.QDRANT_IN_PROCESS or settings.QDRANT_LOCATION):
                try:
                    client.create_payload_index(
                        collection_name=col_name,
                        field_name="document_category",
                        field_schema="keyword"
                    )
                    client.create_payload_index(
                        collection_name=col_name,
                        field_name="verification_status",
                        field_schema="keyword"
                    )
                except Exception as e:
                    logger.warning("Payload index creation skipped: %s", e)
            logger.info("Successfully initialized collection %s", col_name)
        else:
            logger.debug("Qdrant collection %s already exists.", col_name)


def ensure_knowledge_indexed(force_reindex: bool = False) -> Dict[str, int]:
    """
    Verifies collections exist and seeds official knowledge & forms if empty.
    Runs automatically on startup, making in-process / in-memory Qdrant fully self-contained
    without requiring external database tables or separate migration hooks.
    """
    ensure_collections()
    client = get_qdrant_client()

    k_col = settings.QDRANT_KNOWLEDGE_COLLECTION
    f_col = settings.QDRANT_FORMS_COLLECTION

    chunks_indexed = 0
    forms_indexed = 0

    # 1. Knowledge collection count
    try:
        k_count = client.count(collection_name=k_col).count
    except Exception:
        k_count = 0

    if k_count == 0 or force_reindex:
        chunker = DocumentChunker()
        emb_svc = get_embedding_service()
        all_chunks = []
        for src in OFFICIAL_SOURCES_DATA:
            if not src.get("is_active", True) or src.get("verification_status", "verified") != "verified":
                continue
            all_chunks.extend(chunker.chunk_source(src))

        if all_chunks:
            texts = [c["content"] for c in all_chunks]
            embeddings = emb_svc.embed_documents(texts)
            points = []
            for chunk, emb in zip(all_chunks, embeddings):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=emb,
                        payload=chunk
                    )
                )
            client.upsert(collection_name=k_col, points=points)
            chunks_indexed = len(points)
            logger.info("Seeded %d official knowledge chunks into Qdrant collection '%s'", chunks_indexed, k_col)

    # 2. Forms collection count
    try:
        f_count = client.count(collection_name=f_col).count
    except Exception:
        f_count = 0

    if f_count == 0 or force_reindex:
        emb_svc = get_embedding_service()
        form_points = []
        for frm in OFFICIAL_FORMS_DATA:
            if not frm.get("is_active", True) or frm.get("verification_status", "verified") != "verified":
                continue
            summary = f"{frm['form_name']} - {frm['purpose']}. Applicable for {frm['document_category']} {', '.join(frm.get('applicable_issue_types', []))}"
            emb = emb_svc.embed_query(summary)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, frm["form_id"]))
            form_points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=frm
                )
            )
        if form_points:
            client.upsert(collection_name=f_col, points=form_points)
            forms_indexed = len(form_points)
            logger.info("Seeded %d official forms into Qdrant collection '%s'", forms_indexed, f_col)

    return {
        "chunks_indexed": chunks_indexed,
        "forms_indexed": forms_indexed,
        "total_chunks": client.count(collection_name=k_col).count,
        "total_forms": client.count(collection_name=f_col).count
    }
