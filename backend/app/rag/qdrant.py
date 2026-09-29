import logging
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.config import settings
from app.rag.embeddings import VECTOR_DIMENSION

logger = logging.getLogger("consolith.rag.qdrant")

_qdrant_client_instance: Optional[QdrantClient] = None

def get_qdrant_client() -> QdrantClient:
    """Returns singleton Qdrant client connection."""
    global _qdrant_client_instance
    if _qdrant_client_instance is None:
        _qdrant_client_instance = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            timeout=5.0
        )
    return _qdrant_client_instance


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
            # Create payload index on document_category for fast filtering
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
            logger.info("Successfully initialized collection and indices for %s", col_name)
        else:
            logger.debug("Qdrant collection %s already exists.", col_name)
