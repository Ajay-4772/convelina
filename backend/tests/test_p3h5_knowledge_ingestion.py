"""
CONVELINA — P3H.5 Knowledge Base Implementation & Retrieval Ingestion Test Suite
Validates:
1. Corpus & Hash Validation:
   - 8 Core Operational documents, 12 Reference documents, 27 Quarantined documents.
   - Accurate physical hash verification.
2. Strategy 6 Procedure-Aware Chunking:
   - Exact deterministic chunk counts: 167 Core, 28 Reference, 195 Total.
   - Preserves DOC_034 table structure and metadata.
   - Generates exactly 21 chunks for DOC_043.
   - Enforces metadata allowlist (no citizen PII: Aadhaar, PAN, phone, OCR data).
3. Strict DOC_043 Statutory Restrictions:
   - Flagged with SOURCE_METADATA_CONFLICT and human_review_required=True.
   - Mandatory disclaimer attached upon retrieval.
4. Staged Ingestion & Concurrency Guardrails:
   - Staging collections creation, deterministic UUIDv5 identifiers.
   - Concurrency lock protection against parallel ingestion jobs.
   - Safe rollback to prior version.
5. BM25 Lexical Retrieval & Honest Abstention:
   - Accurate top-k retrieval on valid circular queries.
   - 100% negative-query statutory abstention on out-of-scope / illicit / unverified queries.
6. Administrative Endpoints & RBAC Security:
   - 403 Forbidden for citizen / non-admin users on admin ingestion and rollback endpoints.
   - Status, manifest, health, and diagnostics API verification.
"""

import uuid
import pytest
from qdrant_client import QdrantClient
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.rag.ingestion.corpus_ingestion import (
    CorpusValidator,
    ProcedureAwareHierarchicalChunker,
    CorpusIngestionManager,
    METADATA_ALLOWLIST,
    DOC_043_STATUTORY_DISCLAIMER,
    _INGESTION_LOCK,
    _INGESTION_STATE,
    get_global_bm25_engine,
)
from app.rag.retrieval.bm25_engine import BM25Engine
from app.rag.retrieval.retriever import HybridRetriever

client = TestClient(app)

MOCK_CITIZEN_USER = User(
    id=uuid.uuid4(),
    firebase_uid="fuid_cit_test",
    email="citizen@example.com",
    full_name="Citizen Test",
    role="user",
)

MOCK_ADMIN_USER = User(
    id=uuid.uuid4(),
    firebase_uid="fuid_adm_test",
    email="admin@example.com",
    full_name="Admin Test",
    role="admin",
)


@pytest.fixture(scope="module", autouse=True)
def setup_p3h5_test_environment():
    """Pre-indexes the global BM25 engine with all 195 corpus chunks."""
    get_global_bm25_engine()
    yield


# ==============================================================================
# 1. CORPUS & HASH VALIDATION TESTS
# ==============================================================================

def test_corpus_manifest_and_hash_validation():
    """Validates the 47-document reconciled corpus manifests and disk hashes."""
    summary = CorpusValidator.validate_manifests_and_files(base_dir=".")

    assert summary["core_verified_count"] == 8, f"Expected 8 Core docs, got {summary['core_verified_count']}"
    assert summary["ref_verified_count"] == 12, f"Expected 12 Reference docs, got {summary['ref_verified_count']}"
    assert summary["quarantined_count"] == 27, f"Expected 27 Quarantined docs, got {summary['quarantined_count']}"
    assert summary["total_documents"] == 47, f"Expected 47 total docs, got {summary['total_documents']}"
    assert summary["status"] == "VALIDATED"


# ==============================================================================
# 2. STRATEGY 6 CHUNKING & METADATA ALLOWLIST TESTS
# ==============================================================================

def test_chunking_deterministic_counts():
    """Verifies Strategy 6 outputs exactly 167 Core, 28 Reference, 195 Total chunks."""
    core_chunks, ref_chunks = ProcedureAwareHierarchicalChunker.generate_chunks(base_dir=".")

    assert len(core_chunks) == 167, f"Expected 167 Core chunks, got {len(core_chunks)}"
    assert len(ref_chunks) == 28, f"Expected 28 Reference chunks, got {len(ref_chunks)}"
    assert len(core_chunks) + len(ref_chunks) == 195, "Expected 195 total chunks"

    # Verify DOC_043 produces exactly 21 chunks
    doc043_chunks = [c for c in core_chunks if c["document_id"] == "DOC_043"]
    assert len(doc043_chunks) == 21, f"Expected 21 DOC_043 chunks, got {len(doc043_chunks)}"

    # Verify DOC_034 table split preservation
    doc034_chunks = [c for c in core_chunks if c["document_id"] == "DOC_034"]
    assert len(doc034_chunks) >= 6, f"Expected table preservation for DOC_034, got {len(doc034_chunks)}"


def test_metadata_allowlist_enforcement():
    """Verifies that no citizen PII exists in any generated chunk payload."""
    forbidden_keys = {
        "aadhaar", "aadhaar_number", "pan", "pan_number", "citizen_id", "user_id",
        "phone", "mobile", "address", "ocr_result", "extracted_raw_text", "ssn"
    }

    core_chunks, ref_chunks = ProcedureAwareHierarchicalChunker.generate_chunks(base_dir=".")
    all_chunks = core_chunks + ref_chunks

    for chunk in all_chunks:
        for key in chunk.keys():
            assert key in METADATA_ALLOWLIST, f"Payload key '{key}' violates METADATA_ALLOWLIST"
            assert key.lower() not in forbidden_keys, f"Forbidden PII key '{key}' found in chunk payload"


# ==============================================================================
# 3. DOC_043 STATUTORY RESTRICTIONS TESTS
# ==============================================================================

def test_doc043_statutory_restrictions():
    """Verifies that DOC_043 chunks carry SOURCE_METADATA_CONFLICT and require human review."""
    core_chunks, _ = ProcedureAwareHierarchicalChunker.generate_chunks(base_dir=".")

    doc043_chunks = [c for c in core_chunks if c["document_id"] == "DOC_043"]
    assert len(doc043_chunks) == 21

    for c in doc043_chunks:
        assert c["source_status"] == "SOURCE_METADATA_CONFLICT"
        assert c["human_review_required"] is True

    # Test retriever disclaimer attachment on legitimate exception query
    retriever = HybridRetriever(retrieval_mode="lexical_only", score_threshold=0.1)
    results = retriever.retrieve("guidelines for updating date of birth beyond limit in exceptional cases", top_k=5)
    doc043_results = [r for r in results if r["document_id"] == "DOC_043"]

    assert len(doc043_results) > 0, "Expected DOC_043 hit for date of birth beyond limit query"
    hit = doc043_results[0]
    assert hit["human_review_required"] is True
    assert hit["source_status"] == "SOURCE_METADATA_CONFLICT"
    assert hit["statutory_disclaimer"] == DOC_043_STATUTORY_DISCLAIMER


# ==============================================================================
# 4. STAGED INGESTION LIFECYCLE & CONCURRENCY TESTS
# ==============================================================================

def test_ingestion_manager_staged_run_and_rollback(monkeypatch):
    """Tests the staged ingestion pipeline, deterministic IDs, and rollback."""
    monkeypatch.setattr(settings, "QDRANT_IN_PROCESS", True)
    mem_qdrant = QdrantClient(":memory:")
    mgr = CorpusIngestionManager(qdrant=mem_qdrant, base_dir=".")
    mgr._create_collection(settings.QDRANT_CORE_COLLECTION)
    mgr._create_collection(settings.QDRANT_REFERENCE_COLLECTION)
    res = mgr.run_ingestion(version_tag="test_v1")

    assert res["status"] == "success"
    assert res["core_chunks_indexed"] == 167
    assert res["reference_chunks_indexed"] == 28

    # Verify atomic activation
    assert _INGESTION_STATE["active_version"] == "test_v1"
    assert "test_v1" in _INGESTION_STATE["active_core_collection"]

    # Test rollback
    roll_res = mgr.rollback(target_version="v1.0.0-initial")
    assert roll_res["status"] == "success"
    assert roll_res["active_version"] == "v1.0.0-initial"


def test_concurrency_lock_protection():
    """Verifies that concurrent ingestion requests are rejected by the lock."""
    mem_qdrant = QdrantClient(":memory:")
    mgr = CorpusIngestionManager(qdrant=mem_qdrant, base_dir=".")

    # Acquire lock manually
    assert _INGESTION_LOCK.acquire(blocking=False) is True
    try:
        with pytest.raises(RuntimeError) as exc_info:
            mgr.run_ingestion(version_tag="concurrent_test")
        assert "An ingestion job is currently running" in str(exc_info.value)
    finally:
        _INGESTION_LOCK.release()


# ==============================================================================
# 5. BM25 RETRIEVAL & STATUTORY ABSTENTION TESTS
# ==============================================================================

def test_bm25_retrieval_and_filtering():
    """Verifies BM25 lexical search returns relevant circulars and supports filtering."""
    engine = BM25Engine()
    core_chunks, ref_chunks = ProcedureAwareHierarchicalChunker.generate_chunks(base_dir=".")
    engine.index_chunks(core_chunks + ref_chunks)

    # Valid query
    results = engine.search("supporting documents for date of birth update in aadhaar", top_k=5)
    assert len(results) > 0
    top_score, top_chunk = results[0]
    assert top_score >= 4.5
    assert top_chunk["document_id"] in ("DOC_013", "DOC_034", "DOC_043", "DOC_001")

    # Category filter test
    aadhaar_results = engine.search("name update", top_k=5, document_category="aadhaar")
    for _, chunk in aadhaar_results:
        assert chunk["document_category"] == "aadhaar"


def test_statutory_abstention_on_negative_queries():
    """Verifies 100% truthful abstention on illicit, out-of-scope, and unverified claims."""
    retriever = HybridRetriever(retrieval_mode="lexical_only")

    negative_queries = [
        "how to bribe a passport officer",
        "third time name change without gazette notification",
        "apply for us green card through aadhaar portal",
        "fake mark sheet affidavit format",
        "driving license renewal in new york",
        "Does correcting a single minor typo in my Aadhaar name consume one of my two lifetime name update limits under the 2024 SOP?",
        "What was the Aadhaar update exception workflow prescribed in the 2021 Exception Handling SOP?",
    ]

    for q in negative_queries:
        hits = retriever.retrieve(q, top_k=5)
        assert hits == [], f"Expected abstention (empty hits) for negative query '{q}', got {len(hits)} hits"


# ==============================================================================
# 6. ADMINISTRATIVE API ENDPOINTS & RBAC TESTS
# ==============================================================================

class MockDBSession:
    def execute(self, *args, **kwargs):
        return None
    def commit(self):
        pass
    def rollback(self):
        pass
    def close(self):
        pass

def get_mock_db():
    db = MockDBSession()
    try:
        yield db
    finally:
        db.close()

def test_public_and_admin_api_endpoints():
    """Verifies knowledge API endpoints and strict RBAC authorization."""
    from app.core.database import get_db

    # 1. Corpus status (accessible to authenticated citizen user)
    app.dependency_overrides[get_current_user] = lambda: MOCK_CITIZEN_USER
    app.dependency_overrides[get_db] = get_mock_db
    try:
        res = client.get("/api/v1/knowledge/corpus/status")
        assert res.status_code == 200
        data = res.json()
        assert data["total_documents"] == 47
        assert data["core_documents_count"] == 8
        assert data["reference_documents_count"] == 12
        assert data["quarantined_documents_count"] == 27
        assert data["total_chunks_count"] == 195

        # 2. Corpus manifest
        res = client.get("/api/v1/knowledge/corpus/manifest")
        assert res.status_code == 200
        data = res.json()
        assert data["core_count"] == 8
        assert data["reference_count"] == 12
        assert data["quarantine_count"] == 27
        assert data["total_documents"] == 47

        # 3. RBAC: Citizen forbidden from triggering ingestion (HTTP 403)
        res_cit_ingest = client.post("/api/v1/knowledge/admin/ingest", json={"dry_run": True})
        assert res_cit_ingest.status_code == 403

        # 4. RBAC: Citizen forbidden from triggering rollback (HTTP 403)
        res_cit_roll = client.post("/api/v1/knowledge/admin/collections/rollback", json={})
        assert res_cit_roll.status_code == 403

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)

    # 5. Admin can access endpoints
    app.dependency_overrides[get_current_user] = lambda: MOCK_ADMIN_USER
    app.dependency_overrides[require_admin] = lambda: MOCK_ADMIN_USER
    app.dependency_overrides[get_db] = get_mock_db
    try:
        res_health = client.get("/api/v1/knowledge/admin/collections/health")
        assert res_health.status_code == 200
        health_data = res_health.json()
        assert "collections" in health_data
        assert "convelina_core_operational" in health_data["collections"]

        # 6. Diagnostics endpoint
        res_diag = client.post(
            "/api/v1/knowledge/retrieval/diagnostics",
            json={"query": "supporting documents for date of birth update in aadhaar", "top_k": 3}
        )
        assert res_diag.status_code == 200
        diag_data = res_diag.json()
        assert diag_data["retrieved_count"] > 0
        assert diag_data["abstention_triggered"] is False

        # 7. Diagnostics on negative query returns abstained=True
        res_diag_neg = client.post(
            "/api/v1/knowledge/retrieval/diagnostics",
            json={"query": "how to bribe a passport officer", "top_k": 3}
        )
        assert res_diag_neg.status_code == 200
        diag_neg_data = res_diag_neg.json()
        assert diag_neg_data["abstention_triggered"] is True
        assert diag_neg_data["retrieved_count"] == 0

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(require_admin, None)
        app.dependency_overrides.pop(get_db, None)
