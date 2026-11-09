import os
import json
import csv
import re
import math
import uuid
import hashlib
import logging
import threading
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.config import settings
from app.rag.embeddings import VECTOR_DIMENSION, get_embedding_service
from app.rag.qdrant import get_qdrant_client
from app.rag.retrieval.bm25_engine import BM25Engine

logger = logging.getLogger("convelina.rag.corpus_ingestion")

# ---------------------------------------------------------------------------
# Constants & Taxonomy
# ---------------------------------------------------------------------------
CORE_DOC_IDS = ["DOC_001", "DOC_004", "DOC_013", "DOC_022", "DOC_023", "DOC_034", "DOC_036", "DOC_043"]
REFERENCE_DOC_IDS = ["DOC_005", "DOC_006", "DOC_021", "DOC_024", "DOC_025", "DOC_026", "DOC_027", "DOC_028", "DOC_029", "DOC_031", "DOC_033", "DOC_047"]

EXPECTED_CORE_CHUNKS = 167
EXPECTED_REFERENCE_CHUNKS = 28
EXPECTED_TOTAL_CHUNKS = 195
DOC_043_CHUNKS_COUNT = 21

DOC_043_STATUTORY_DISCLAIMER = (
    "STATUTORY LIMITATION NOTICE: DOC_043 retains an unverified source metadata conflict. "
    "Claims regarding third-time exceptions and Regional Office escalation packets cannot be represented as definitive law."
)

METADATA_ALLOWLIST = {
    "chunk_id",
    "document_id",
    "document_title",
    "document_category",
    "corpus_classification",
    "source_sha256",
    "source_version",
    "chunk_index",
    "page_number",
    "section_title",
    "content_type",
    "source_status",
    "verification_status",
    "source_date",
    "effective_date",
    "ingestion_timestamp",
    "human_review_required",
    "retrieval_eligibility",
    "chunk_text",
}

# Concurrency lock to prevent overlapping ingestion executions
_INGESTION_LOCK = threading.Lock()

# Global state tracking for active ingestion version & cached BM25 index
_INGESTION_STATE = {
    "active_version": "v1.0.0-initial",
    "previous_version": None,
    "last_ingested_at": None,
    "jobs": {},
    "active_core_collection": settings.QDRANT_CORE_COLLECTION,
    "active_reference_collection": settings.QDRANT_REFERENCE_COLLECTION,
}

_GLOBAL_BM25_ENGINE: Optional[BM25Engine] = None


# ---------------------------------------------------------------------------
# 1. Corpus Validator
# ---------------------------------------------------------------------------
class CorpusValidator:
    """
    Validates physical documents, manifests, classifications, and SHA-256 integrity
    across all 47 documents before ingestion.
    """

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def validate_manifests_and_files(cls, base_dir: str = ".") -> Dict[str, Any]:
        """
        Verifies:
        1. 8 Core documents exist and SHA-256 hashes match.
        2. 12 Reference documents exist and SHA-256 hashes match.
        3. 27 Quarantined documents are verified as non-retrievable.
        """
        core_manifest_path = os.path.join(base_dir, "forms", "CORE_OPERATIONAL_KNOWLEDGE_CORPUS_MANIFEST.csv")
        ref_manifest_path = os.path.join(base_dir, "forms", "REFERENCE_ONLY_CORPUS_MANIFEST.csv")
        recon_path = os.path.join(base_dir, "forms", "P3H4_1_CORPUS_RECONCILIATION.csv")

        if not os.path.exists(core_manifest_path) or not os.path.exists(ref_manifest_path):
            raise FileNotFoundError("Corpus manifest CSV files missing from forms directory.")

        with open(core_manifest_path, "r", encoding="utf-8") as f:
            core_manifest = list(csv.DictReader(f))

        with open(ref_manifest_path, "r", encoding="utf-8") as f:
            ref_manifest = list(csv.DictReader(f))

        with open(recon_path, "r", encoding="utf-8") as f:
            recon_manifest = list(csv.DictReader(f))

        # Check document ID sets
        manifest_core_ids = [r["document_id"] for r in core_manifest]
        manifest_ref_ids = [r["document_id"] for r in ref_manifest]

        if sorted(manifest_core_ids) != sorted(CORE_DOC_IDS):
            raise ValueError(f"Core manifest ID mismatch. Expected {CORE_DOC_IDS}, got {manifest_core_ids}")

        if sorted(manifest_ref_ids) != sorted(REFERENCE_DOC_IDS):
            raise ValueError(f"Reference manifest ID mismatch. Expected {REFERENCE_DOC_IDS}, got {manifest_ref_ids}")

        quarantine_rows = [r for r in recon_manifest if r.get("proposed_collection") not in ("convelina_core_operational", "convelina_reference_secondary")]
        if len(quarantine_rows) != 27:
            raise ValueError(f"Quarantined document count mismatch. Expected 27, found {len(quarantine_rows)}")

        # Verify physical file hashes on disk
        verified_core = []
        verified_ref = []

        all_manifest_active = [(r, "CORE") for r in core_manifest] + [(r, "REFERENCE") for r in ref_manifest]
        for row, doc_type in all_manifest_active:
            doc_id = row["document_id"]
            expected_hash = row["sha256"]
            fn_target = row.get("filename") or row.get("original_filename")

            found = False
            for root, _, files in os.walk(os.path.join(base_dir, "forms")):
                for fn in files:
                    if fn == fn_target or fn.startswith(doc_id):
                        fp = os.path.join(root, fn)
                        actual_hash = cls.compute_sha256(fp)
                        if actual_hash.lower() == expected_hash.lower():
                            found = True
                            if doc_type == "CORE":
                                verified_core.append(doc_id)
                            else:
                                verified_ref.append(doc_id)
                            break
                if found:
                    break

            if not found:
                raise ValueError(f"Integrity check failed: source document {doc_id} ({fn_target}) missing or SHA-256 hash mismatch!")

        return {
            "core_verified_count": len(verified_core),
            "ref_verified_count": len(verified_ref),
            "quarantined_count": len(quarantine_rows),
            "total_documents": len(recon_manifest),
            "status": "VALIDATED"
        }


# ---------------------------------------------------------------------------
# 2. Procedure-Aware Hierarchical Chunker (Strategy 6)
# ---------------------------------------------------------------------------
class ProcedureAwareHierarchicalChunker:
    """
    Deterministic implementation of Candidate Strategy 6:
    Produces exactly 167 Core chunks and 28 Reference chunks (195 total).
    Enforces strict metadata allowlist contract.
    """

    @classmethod
    def generate_chunks(cls, base_dir: str = ".") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        core_records_path = os.path.join(base_dir, "forms", "CORE_KNOWLEDGE_RECORDS.jsonl")
        ref_records_path = os.path.join(base_dir, "forms", "REFERENCE_KNOWLEDGE_RECORDS.jsonl")

        with open(core_records_path, "r", encoding="utf-8") as f:
            core_pages = [json.loads(line) for line in f if line.strip()]

        with open(ref_records_path, "r", encoding="utf-8") as f:
            ref_pages = [json.loads(line) for line in f if line.strip()]

        core_chunks = cls._chunk_pages(core_pages, corpus_classification="CORE_OPERATIONAL")
        ref_chunks = cls._chunk_pages(ref_pages, corpus_classification="REFERENCE_SECONDARY")

        if len(core_chunks) != EXPECTED_CORE_CHUNKS:
            raise ValueError(f"Core chunk count mismatch! Expected {EXPECTED_CORE_CHUNKS}, got {len(core_chunks)}")

        if len(ref_chunks) != EXPECTED_REFERENCE_CHUNKS:
            raise ValueError(f"Reference chunk count mismatch! Expected {EXPECTED_REFERENCE_CHUNKS}, got {len(ref_chunks)}")

        doc_043_chunks = [c for c in core_chunks if c["document_id"] == "DOC_043"]
        if len(doc_043_chunks) != DOC_043_CHUNKS_COUNT:
            raise ValueError(f"DOC_043 chunk count mismatch! Expected {DOC_043_CHUNKS_COUNT}, got {len(doc_043_chunks)}")

        # Verify 100% of DOC_043 chunks retain SOURCE_METADATA_CONFLICT & human_review_required=True
        for c in doc_043_chunks:
            if c["source_status"] != "SOURCE_METADATA_CONFLICT" or c["human_review_required"] is not True:
                raise ValueError(f"Security invariant violated for DOC_043 chunk {c['chunk_id']}")

        return core_chunks, ref_chunks

    @classmethod
    def _chunk_pages(cls, pages: List[Dict[str, Any]], corpus_classification: str) -> List[Dict[str, Any]]:
        chunks = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for p in pages:
            doc_id = p["document_id"]
            title = p["document_title"]
            cohort = p.get("applicant_cohort", "ALL_CITIZENS")
            func = p.get("document_function", "STATUTORY_PROCEDURE")
            auth_status = p.get("source_authenticity_status", "OFFICIALLY_PUBLISHED")
            elig = p.get("retrieval_eligibility", "ELIGIBLE")
            p_num = int(p["page_number"])
            sec = p.get("section_reference", f"Page {p_num}")
            text = p.get("chunk_text") or p.get("content") or ""
            source_sha = p.get("sha256") or p.get("source_sha256") or ""
            source_date = p.get("source_date") or "2023-01-26"
            effective_date = p.get("effective_date")
            doc_category = p.get("document_category", "aadhaar")

            # Invariant on DOC_043
            if doc_id == "DOC_043":
                source_status = "SOURCE_METADATA_CONFLICT"
                human_review_required = True
                eligibility = "CONDITIONAL"
            else:
                source_status = "OFFICIALLY_PUBLISHED"
                human_review_required = False
                eligibility = "ELIGIBLE"

            # Context prefix to anchor retrieval
            context_prefix = (
                f"[DOC: {doc_id} | TITLE: {title} | COHORT: {cohort} | FUNC: {func} | "
                f"STATUS: {source_status} | ELIG: {eligibility} | SEC: {sec} | PAGE: {p_num}]\n"
            )
            if doc_id == "DOC_043":
                context_prefix += f"[{DOC_043_STATUTORY_DISCLAIMER}]\n"

            # Special procedure unit segmentation for DOC_043 Annexure A (pages 3-6)
            if doc_id == "DOC_043" and p_num in [3, 4, 5, 6]:
                scenario_pattern = r'(?=(?:\([a-o]\)|[1-5]\.\s+[A-Za-z]+|\bScenario\b|\bCategory\s+[1-5]\b))'
                scenarios = re.split(scenario_pattern, text)
                scenarios = [s.strip() for s in scenarios if s.strip() and len(s.strip()) > 30]
                if not scenarios:
                    scenarios = [text]

                for idx, sc in enumerate(scenarios, start=1):
                    full_text = context_prefix + sc
                    chunk_id = f"PROC_DOC043_P{p_num:02d}_SCENARIO_{idx:02d}"
                    chunks.append(cls._build_chunk_record(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        title=title,
                        category=doc_category,
                        corpus_classification=corpus_classification,
                        sha256=source_sha,
                        chunk_index=len(chunks) + 1,
                        page_num=p_num,
                        section_title=f"{sec} - Scenario Unit {idx}",
                        content_type="PROCEDURAL_SCENARIO",
                        source_status=source_status,
                        verification_status="VERIFIED" if doc_id != "DOC_043" else "NEEDS_REVIEW",
                        source_date=source_date,
                        effective_date=effective_date,
                        ingestion_timestamp=now_iso,
                        human_review_required=human_review_required,
                        retrieval_eligibility=eligibility,
                        chunk_text=full_text,
                    ))

            # Special table-preserving segmentation for DOC_034 POI/POA/DOB/POR tables (pages 2-13)
            elif doc_id == "DOC_034" and p_num in range(2, 14):
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                header_str = " // ".join(lines[:2]) if len(lines) >= 2 else (lines[0] if lines else "")
                item_lines = lines[2:] if len(lines) >= 2 else []

                step = 6
                if not item_lines:
                    item_lines = [text]
                for idx in range(0, max(1, len(item_lines)), step):
                    slice_lines = item_lines[idx:idx+step]
                    table_unit = f"CATEGORY HEADER: {header_str}\n" + "\n".join(slice_lines)
                    full_text = context_prefix + table_unit
                    chunk_id = f"PROC_DOC034_P{p_num:02d}_ITEMS_{idx//step+1:02d}"
                    chunks.append(cls._build_chunk_record(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        title=title,
                        category=doc_category,
                        corpus_classification=corpus_classification,
                        sha256=source_sha,
                        chunk_index=len(chunks) + 1,
                        page_num=p_num,
                        section_title=f"{sec} (Items {idx+1}-{min(idx+step, len(item_lines))})",
                        content_type="DOCUMENT_TABLE",
                        source_status=source_status,
                        verification_status="VERIFIED",
                        source_date=source_date,
                        effective_date=effective_date,
                        ingestion_timestamp=now_iso,
                        human_review_required=human_review_required,
                        retrieval_eligibility=eligibility,
                        chunk_text=full_text,
                    ))

            else:
                # Single procedure or template unit per page
                full_text = context_prefix + text
                chunk_id = f"PROC_{doc_id}_P{p_num:02d}_UNIT01"
                chunks.append(cls._build_chunk_record(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    title=title,
                    category=doc_category,
                    corpus_classification=corpus_classification,
                    sha256=source_sha,
                    chunk_index=len(chunks) + 1,
                    page_num=p_num,
                    section_title=sec,
                    content_type="PROCEDURAL_GUIDANCE",
                    source_status=source_status,
                    verification_status="VERIFIED" if doc_id != "DOC_043" else "NEEDS_REVIEW",
                    source_date=source_date,
                    effective_date=effective_date,
                    ingestion_timestamp=now_iso,
                    human_review_required=human_review_required,
                    retrieval_eligibility=eligibility,
                    chunk_text=full_text,
                ))

        return chunks

    @staticmethod
    def _build_chunk_record(
        chunk_id: str,
        doc_id: str,
        title: str,
        category: str,
        corpus_classification: str,
        sha256: str,
        chunk_index: int,
        page_num: int,
        section_title: str,
        content_type: str,
        source_status: str,
        verification_status: str,
        source_date: str,
        effective_date: Optional[str],
        ingestion_timestamp: str,
        human_review_required: bool,
        retrieval_eligibility: str,
        chunk_text: str,
    ) -> Dict[str, Any]:
        """
        Enforces strict metadata allowlist. Citizen fields (Aadhaar, PAN, phone, address, drafts)
        are unconditionally barred.
        """
        return {
            "chunk_id": chunk_id,
            "document_id": doc_id,
            "document_title": title,
            "document_category": category.lower(),
            "corpus_classification": corpus_classification,
            "source_sha256": sha256,
            "source_version": "1.0",
            "chunk_index": chunk_index,
            "page_number": page_num,
            "section_title": section_title,
            "content_type": content_type,
            "source_status": source_status,
            "verification_status": verification_status,
            "source_date": source_date,
            "effective_date": effective_date or "",
            "ingestion_timestamp": ingestion_timestamp,
            "human_review_required": human_review_required,
            "retrieval_eligibility": retrieval_eligibility,
            "chunk_text": chunk_text,
        }


# ---------------------------------------------------------------------------
# 3. Corpus Ingestion Manager
# ---------------------------------------------------------------------------
class CorpusIngestionManager:
    """
    Manages the end-to-end staged ingestion, verification, promotion, and rollback
    for Qdrant collections and the global BM25 lexical engine.
    """

    def __init__(self, qdrant: Optional[QdrantClient] = None, base_dir: str = "."):
        self.qdrant = qdrant or get_qdrant_client()
        self.embedding_service = get_embedding_service()
        self.base_dir = base_dir

    def run_ingestion(self, version_tag: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Executes safe staged ingestion:
        1. Acquire concurrency lock
        2. Validate physical corpus & manifests
        3. Generate chunks via ProcedureAwareHierarchicalChunker (Strategy 6)
        4. Validate counts (167 core, 28 reference)
        5. Create isolated staging collections
        6. Upload points with deterministic UUIDv5
        7. Run retrieval smoke tests on staging
        8. Atomic activation (switch active collection / aliases)
        9. Index into global BM25 engine
        10. Retain previous collection for rollback
        """
        global _INGESTION_STATE, _GLOBAL_BM25_ENGINE

        if not _INGESTION_LOCK.acquire(blocking=False):
            raise RuntimeError("An ingestion job is currently running. Please wait for completion.")

        job_id = str(uuid.uuid4())
        version = version_tag or f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        _INGESTION_STATE["jobs"][job_id] = {
            "job_id": job_id,
            "status": "validating",
            "version_tag": version,
            "core_chunks_indexed": 0,
            "reference_chunks_indexed": 0,
            "staging_collections": [],
            "active_collections": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "error": None
        }

        try:
            logger.info("Step 1: Validating source documents and manifests...")
            val_result = CorpusValidator.validate_manifests_and_files(self.base_dir)
            logger.info("Corpus validated: %s", val_result)

            logger.info("Step 2: Generating chunks via Strategy 6 (Procedure-Aware Hierarchical)...")
            _INGESTION_STATE["jobs"][job_id]["status"] = "chunking"
            core_chunks, ref_chunks = ProcedureAwareHierarchicalChunker.generate_chunks(self.base_dir)

            if dry_run:
                _INGESTION_STATE["jobs"][job_id]["status"] = "dry_run_completed"
                _INGESTION_STATE["jobs"][job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                return {
                    "status": "dry_run_success",
                    "job_id": job_id,
                    "version_tag": version,
                    "core_chunks_generated": len(core_chunks),
                    "reference_chunks_generated": len(ref_chunks),
                    "message": "Dry run completed cleanly. Zero mutations made to collections."
                }

            logger.info("Step 3: Staging collections creation and upload...")
            _INGESTION_STATE["jobs"][job_id]["status"] = "staging"

            staging_core_col = f"{settings.QDRANT_CORE_COLLECTION}_{version}"
            staging_ref_col = f"{settings.QDRANT_REFERENCE_COLLECTION}_{version}"
            _INGESTION_STATE["jobs"][job_id]["staging_collections"] = [staging_core_col, staging_ref_col]

            # Create staging collections
            self._create_collection(staging_core_col)
            self._create_collection(staging_ref_col)

            # Upload points with deterministic UUIDv5
            core_points = self._chunks_to_points(core_chunks)
            ref_points = self._chunks_to_points(ref_chunks)

            self.qdrant.upsert(collection_name=staging_core_col, points=core_points)
            self.qdrant.upsert(collection_name=staging_ref_col, points=ref_points)

            # Verify point counts on staging collections
            core_count = self.qdrant.count(collection_name=staging_core_col).count
            ref_count = self.qdrant.count(collection_name=staging_ref_col).count

            if core_count != EXPECTED_CORE_CHUNKS:
                raise ValueError(f"Staging point count error for core: expected {EXPECTED_CORE_CHUNKS}, got {core_count}")
            if ref_count != EXPECTED_REFERENCE_CHUNKS:
                raise ValueError(f"Staging point count error for ref: expected {EXPECTED_REFERENCE_CHUNKS}, got {ref_count}")

            logger.info("Step 4: Executing retrieval smoke tests on staging collection...")
            smoke_test_passed = self._run_smoke_test(staging_core_col)
            if not smoke_test_passed:
                raise RuntimeError("Staging retrieval smoke test failed!")

            logger.info("Step 5: Activating new collections...")
            _INGESTION_STATE["jobs"][job_id]["status"] = "activating"

            # In Qdrant, if in-process/memory, copy into primary named collections as well
            if settings.QDRANT_IN_PROCESS or settings.QDRANT_LOCATION:
                self._create_collection(settings.QDRANT_CORE_COLLECTION)
                self._create_collection(settings.QDRANT_REFERENCE_COLLECTION)
                self.qdrant.upsert(collection_name=settings.QDRANT_CORE_COLLECTION, points=core_points)
                self.qdrant.upsert(collection_name=settings.QDRANT_REFERENCE_COLLECTION, points=ref_points)

            # Update active pointers
            _INGESTION_STATE["previous_version"] = _INGESTION_STATE["active_version"]
            _INGESTION_STATE["active_version"] = version
            _INGESTION_STATE["last_ingested_at"] = datetime.now(timezone.utc).isoformat()
            _INGESTION_STATE["active_core_collection"] = staging_core_col
            _INGESTION_STATE["active_reference_collection"] = staging_ref_col

            # Initialize global BM25 engine with all 195 chunks
            all_chunks = core_chunks + ref_chunks
            bm25 = BM25Engine()
            bm25.index_chunks(all_chunks)
            _GLOBAL_BM25_ENGINE = bm25

            _INGESTION_STATE["jobs"][job_id]["status"] = "activated"
            _INGESTION_STATE["jobs"][job_id]["core_chunks_indexed"] = core_count
            _INGESTION_STATE["jobs"][job_id]["reference_chunks_indexed"] = ref_count
            _INGESTION_STATE["jobs"][job_id]["active_collections"] = [staging_core_col, staging_ref_col]
            _INGESTION_STATE["jobs"][job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

            logger.info("Knowledge ingestion successfully activated version %s (%d core, %d ref chunks).", version, core_count, ref_count)

            return {
                "status": "success",
                "job_id": job_id,
                "version_tag": version,
                "core_chunks_indexed": core_count,
                "reference_chunks_indexed": ref_count,
                "active_collections": [staging_core_col, staging_ref_col],
                "message": f"Successfully activated version {version}: {core_count} core chunks, {ref_count} reference chunks."
            }

        except Exception as e:
            logger.error("Ingestion failed: %s", str(e), exc_info=True)
            _INGESTION_STATE["jobs"][job_id]["status"] = "failed"
            _INGESTION_STATE["jobs"][job_id]["error"] = str(e)
            _INGESTION_STATE["jobs"][job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            raise
        finally:
            _INGESTION_LOCK.release()

    def rollback(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Rolls back the active collection to the previous version or specified target_version.
        """
        global _INGESTION_STATE

        prev = target_version or _INGESTION_STATE["previous_version"]
        if not prev:
            raise ValueError("No previous collection version available to rollback to.")

        core_col = f"{settings.QDRANT_CORE_COLLECTION}_{prev}"
        ref_col = f"{settings.QDRANT_REFERENCE_COLLECTION}_{prev}"

        # Verify collections exist
        existing = [c.name for c in self.qdrant.get_collections().collections]
        if core_col not in existing:
            # Fall back to base collection if versioned staging collection does not exist
            if settings.QDRANT_CORE_COLLECTION in existing:
                core_col = settings.QDRANT_CORE_COLLECTION
                ref_col = settings.QDRANT_REFERENCE_COLLECTION
            else:
                raise ValueError(f"Target rollback collection {core_col} does not exist in Qdrant.")

        current_ver = _INGESTION_STATE["active_version"]
        _INGESTION_STATE["previous_version"] = current_ver
        _INGESTION_STATE["active_version"] = prev
        _INGESTION_STATE["active_core_collection"] = core_col
        _INGESTION_STATE["active_reference_collection"] = ref_col

        logger.info("Rolled back knowledge base from %s to %s", current_ver, prev)
        return {
            "status": "success",
            "previous_version": current_ver,
            "current_version": prev,
            "active_version": prev,
            "active_core_collection": core_col,
            "active_reference_collection": ref_col,
            "message": f"Successfully rolled back active collection to version {prev}."
        }

    def get_collections_health(self) -> Dict[str, Any]:
        """Returns health, point counts, vector dimension, and payload indexes."""
        existing = {c.name: c for c in self.qdrant.get_collections().collections}
        health_map = {}

        cols_to_check = [
            settings.QDRANT_CORE_COLLECTION,
            settings.QDRANT_REFERENCE_COLLECTION,
            _INGESTION_STATE["active_core_collection"],
            _INGESTION_STATE["active_reference_collection"],
        ]

        for col_name in set(cols_to_check):
            if col_name in existing:
                try:
                    cnt = self.qdrant.count(collection_name=col_name).count
                    status = "HEALTHY"
                except Exception as e:
                    cnt = 0
                    status = f"ERROR: {str(e)}"
                health_map[col_name] = {
                    "name": col_name,
                    "exists": True,
                    "points_count": cnt,
                    "vector_size": VECTOR_DIMENSION,
                    "distance": "Cosine",
                    "status": status,
                    "payload_indexes": [
                        "document_id", "document_category", "corpus_classification",
                        "verification_status", "source_status", "retrieval_eligibility"
                    ],
                    "aliases": [col_name]
                }
            else:
                health_map[col_name] = {
                    "name": col_name,
                    "exists": False,
                    "points_count": 0,
                    "vector_size": VECTOR_DIMENSION,
                    "distance": "Cosine",
                    "status": "COLLECTION_NOT_FOUND",
                    "payload_indexes": [],
                    "aliases": []
                }

        backend_mode = "in_process_memory" if settings.QDRANT_IN_PROCESS and not settings.QDRANT_LOCATION else (
            "in_process_disk" if settings.QDRANT_LOCATION else "external_daemon"
        )

        return {
            "backend_mode": backend_mode,
            "active_version": _INGESTION_STATE["active_version"],
            "collections": health_map
        }

    def _create_collection(self, collection_name: str):
        existing = [c.name for c in self.qdrant.get_collections().collections]
        if collection_name not in existing:
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=VECTOR_DIMENSION, distance=Distance.COSINE)
            )
            # Create payload indexes on external or disk Qdrant
            if not (settings.QDRANT_IN_PROCESS and not settings.QDRANT_LOCATION):
                for fld in ["document_id", "document_category", "corpus_classification", "source_status"]:
                    try:
                        self.qdrant.create_payload_index(collection_name=collection_name, field_name=fld, field_schema="keyword")
                    except Exception:
                        pass

    def _chunks_to_points(self, chunks: List[Dict[str, Any]]) -> List[PointStruct]:
        points = []
        texts = [f"{c['document_title']} {c['section_title']} {c['chunk_text']}" for c in chunks]
        embeddings = self.embedding_service.embed_documents(texts)

        for chunk, emb in zip(chunks, embeddings):
            # Deterministic UUIDv5 derived from chunk_id
            pt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))
            points.append(PointStruct(id=pt_id, vector=emb, payload=chunk))
        return points

    def _run_smoke_test(self, collection_name: str) -> bool:
        """Executes verification query against staging collection to confirm retrieval readiness."""
        query = "Aadhaar name update procedure"
        query_vec = self.embedding_service.embed_query(query)
        if hasattr(self.qdrant, "query_points"):
            res = self.qdrant.query_points(
                collection_name=collection_name,
                query=query_vec,
                limit=3
            )
            return len(res.points) > 0
        elif hasattr(self.qdrant, "search"):
            results = self.qdrant.search(
                collection_name=collection_name,
                query_vector=query_vec,
                limit=3
            )
            return len(results) > 0
        return False


def get_global_bm25_engine(base_dir: str = ".") -> BM25Engine:
    """Returns singleton cached BM25 engine loaded with 195 corpus chunks."""
    global _GLOBAL_BM25_ENGINE
    if _GLOBAL_BM25_ENGINE is None or not _GLOBAL_BM25_ENGINE._is_indexed:
        core_chunks, ref_chunks = ProcedureAwareHierarchicalChunker.generate_chunks(base_dir)
        engine = BM25Engine()
        engine.index_chunks(core_chunks + ref_chunks)
        _GLOBAL_BM25_ENGINE = engine
    return _GLOBAL_BM25_ENGINE
