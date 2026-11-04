import uuid
import hashlib
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from qdrant_client.models import PointStruct

from app.config import settings
from app.models.knowledge_source import KnowledgeSource
from app.models.official_form import OfficialForm
from app.rag.ingestion.sources import OFFICIAL_SOURCES_DATA, OFFICIAL_FORMS_DATA
from app.rag.ingestion.chunker import DocumentChunker
from app.rag.embeddings import get_embedding_service
from app.rag.qdrant import get_qdrant_client, ensure_collections

logger = logging.getLogger("consolith.rag.ingestion")

class KnowledgeIngestionService:
    """
    Ingests and synchronizes official government knowledge sources and form catalogs.
    Stores metadata in PostgreSQL and indexes semantic vectors in Qdrant collections.
    """

    def __init__(self, db: Session):
        self.db = db
        self.chunker = DocumentChunker()
        self.embedding_service = get_embedding_service()
        self.qdrant = get_qdrant_client()

    def sync_all(self) -> Dict[str, Any]:
        """Runs complete synchronization of sources, forms, and vector collections."""
        ensure_collections()

        sources_synced = self.sync_knowledge_sources()
        forms_synced = self.sync_official_forms()
        chunks_indexed = self.index_chunks_in_qdrant()
        forms_indexed = self.index_forms_in_qdrant()

        return {
            "sources_synced": sources_synced,
            "forms_synced": forms_synced,
            "chunks_indexed": chunks_indexed,
            "forms_indexed": forms_indexed,
            "status": "success"
        }

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Computes deterministic SHA-256 hash of content for drift detection."""
        normalized = (content or "").strip().encode("utf-8")
        return hashlib.sha256(normalized).hexdigest()

    def sync_knowledge_sources(self) -> int:
        """Upserts verified official government guidelines into PostgreSQL knowledge_sources."""
        synced_count = 0
        for src in OFFICIAL_SOURCES_DATA:
            content = src["content"].strip()
            content_hash = self.compute_content_hash(content)

            existing = self.db.query(KnowledgeSource).filter(
                KnowledgeSource.source_id == src["source_id"]
            ).first()

            if existing:
                existing.title = src["title"]
                existing.issuing_authority = src["issuing_authority"]
                existing.document_type = src["document_type"]
                existing.document_category = src["document_category"]
                existing.source_url = src["source_url"]
                existing.version = src.get("version")
                existing.content_hash = content_hash
                existing.raw_content = content
                existing.verification_status = src.get("verification_status", "verified")
                existing.is_active = src.get("is_active", True)
            else:
                new_src = KnowledgeSource(
                    source_id=src["source_id"],
                    title=src["title"],
                    issuing_authority=src["issuing_authority"],
                    document_type=src["document_type"],
                    document_category=src["document_category"],
                    source_url=src["source_url"],
                    jurisdiction=src.get("jurisdiction", "India"),
                    language=src.get("language", "en"),
                    version=src.get("version"),
                    content_hash=content_hash,
                    raw_content=content,
                    verification_status=src.get("verification_status", "verified"),
                    is_active=src.get("is_active", True),
                )
                self.db.add(new_src)

            synced_count += 1

        self.db.commit()
        logger.info("Synchronized %d official knowledge sources in PostgreSQL.", synced_count)
        return synced_count

    def sync_official_forms(self) -> int:
        """Upserts verified official forms into PostgreSQL official_forms table."""
        synced_count = 0
        for frm in OFFICIAL_FORMS_DATA:
            existing = self.db.query(OfficialForm).filter(
                OfficialForm.form_id == frm["form_id"]
            ).first()

            if existing:
                existing.form_name = frm["form_name"]
                existing.document_category = frm["document_category"]
                existing.purpose = frm["purpose"]
                existing.issuing_authority = frm["issuing_authority"]
                existing.official_download_url = frm["official_download_url"]
                existing.instructions_source_id = frm.get("instructions_source_id")
                existing.applicable_issue_types = frm.get("applicable_issue_types", [])
                existing.applicable_conditions = frm.get("applicable_conditions", [])
                existing.verification_status = frm.get("verification_status", "verified")
                existing.is_active = frm.get("is_active", True)
            else:
                new_frm = OfficialForm(
                    form_id=frm["form_id"],
                    form_name=frm["form_name"],
                    document_category=frm["document_category"],
                    purpose=frm["purpose"],
                    issuing_authority=frm["issuing_authority"],
                    official_download_url=frm["official_download_url"],
                    instructions_source_id=frm.get("instructions_source_id"),
                    applicable_issue_types=frm.get("applicable_issue_types", []),
                    applicable_conditions=frm.get("applicable_conditions", []),
                    verification_status=frm.get("verification_status", "verified"),
                    is_active=frm.get("is_active", True),
                )
                self.db.add(new_frm)

            synced_count += 1

        self.db.commit()
        logger.info("Synchronized %d official forms in PostgreSQL.", synced_count)
        return synced_count

    def index_chunks_in_qdrant(self) -> int:
        """Extracts semantic chunks from official sources and indexes into Qdrant."""
        all_chunks: List[Dict[str, Any]] = []
        for src in OFFICIAL_SOURCES_DATA:
            # Only index active and verified statutory sources
            if not src.get("is_active", True) or src.get("verification_status", "verified") != "verified":
                continue
            chunks = self.chunker.chunk_source(src)
            all_chunks.extend(chunks)

        if not all_chunks:
            return 0

        texts = [c["content"] for c in all_chunks]
        embeddings = self.embedding_service.embed_documents(texts)

        points = []
        for chunk, emb in zip(all_chunks, embeddings):
            # Stable UUID from chunk_id
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))
            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=chunk
                )
            )

        self.qdrant.upsert(
            collection_name=settings.QDRANT_KNOWLEDGE_COLLECTION,
            points=points
        )
        logger.info("Indexed %d knowledge chunks in Qdrant collection '%s'.", len(points), settings.QDRANT_KNOWLEDGE_COLLECTION)
        return len(points)

    def index_forms_in_qdrant(self) -> int:
        """Indexes official forms with descriptions and conditions into Qdrant."""
        points = []
        for frm in OFFICIAL_FORMS_DATA:
            # Only index active and verified forms
            if not frm.get("is_active", True) or frm.get("verification_status", "verified") != "verified":
                continue
            summary = f"{frm['form_name']} - {frm['purpose']}. Applicable for {frm['document_category']} {', '.join(frm.get('applicable_issue_types', []))}"
            emb = self.embedding_service.embed_query(summary)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, frm["form_id"]))
            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=frm
                )
            )

        self.qdrant.upsert(
            collection_name=settings.QDRANT_FORMS_COLLECTION,
            points=points
        )
        logger.info("Indexed %d official forms in Qdrant collection '%s'.", len(points), settings.QDRANT_FORMS_COLLECTION)
        return len(points)
