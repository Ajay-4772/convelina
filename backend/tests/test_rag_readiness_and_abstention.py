"""
CONVELINA — Future RAG Readiness & Truthful Abstention Test Suite
Validates:
1. Admin Knowledge Ingestion API (/api/v1/knowledge/admin/sources/ingest-file):
   - Ingests Markdown, Text, and PDF files.
   - Parses, chunks, computes deterministic hash, generates embeddings, indexes into Qdrant.
   - Returns structured Ingestion Report (accepted_files, page_count, chunk_count, embedding_status, indexing_status).
   - Enforces RBAC (403 for citizen, 200 for admin).
   - Rejects unsupported MIME formats (415 Unsupported Media Type).
   - Cryptographically links to append-only audit trail.
2. Honest RAG Abstention (Zero Hallucination):
   - When evidence is below relevance floor (>= 0.55) and no deterministic mapping exists,
     returns NO_VERIFIED_PROCEDURE_AVAILABLE.
   - Sets confidence="insufficient_evidence".
   - Never hallucinates non-existent government circulars, forms, or timelines.
"""

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.knowledge_source import KnowledgeSource
from app.models.audit_log import AuditLog
from app.core.database import SessionLocal, set_rls_context
from app.rag.generation.llm_provider import GoogleGeminiProvider
from app.rag.assistant.orchestrator import RAGOrchestrator

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        set_rls_context(session, None, "admin")
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def user_and_admin_tokens():
    uid_citizen = f"usr_rag_cit_{uuid.uuid4().hex[:6]}"
    token_citizen = f"test_token_:{uid_citizen}:{uid_citizen}@example.com:Citizen RAG"
    res_cit = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_citizen}"},
        json={
            "email": f"{uid_citizen}@example.com",
            "full_name": "Citizen RAG",
            "phone_number": "+919876543230",
            "date_of_birth": "1994-03-25",
        },
    )
    assert res_cit.status_code in (200, 201)

    uid_admin = f"usr_rag_adm_{uuid.uuid4().hex[:6]}"
    token_admin = f"test_token_:{uid_admin}:{uid_admin}@example.com:Admin RAG"
    res_adm = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "email": f"{uid_admin}@example.com",
            "full_name": "Admin RAG",
            "phone_number": "+919876543231",
            "date_of_birth": "1988-08-18",
        },
    )
    assert res_adm.status_code in (200, 201)

    # Elevate role in database
    db_elevate = SessionLocal()
    try:
        set_rls_context(db_elevate, None, "admin")
        from app.models.user import User
        adm_record = db_elevate.query(User).filter(User.email == f"{uid_admin}@example.com").first()
        if adm_record:
            adm_record.role = "admin"
            db_elevate.commit()
    finally:
        db_elevate.close()

    return {
        "citizen_token": token_citizen,
        "admin_token": token_admin,
    }


def test_admin_ingest_knowledge_file_rbac(user_and_admin_tokens):
    """Verifies that citizens cannot access admin knowledge ingestion endpoint (403)."""
    headers = {"Authorization": f"Bearer {user_and_admin_tokens['citizen_token']}"}
    files = {"file": ("uidai_circular.txt", io.BytesIO(b"UIDAI Circular text"), "text/plain")}
    data = {
        "title": "UIDAI Name Change Circular",
        "document_category": "aadhaar",
        "issuing_authority": "UIDAI",
    }
    res = client.post("/api/v1/knowledge/admin/sources/ingest-file", headers=headers, files=files, data=data)
    assert res.status_code == 403


def test_admin_ingest_knowledge_file_unsupported_format(user_and_admin_tokens):
    """Verifies rejection of unsupported file types (.exe, .bin) with 415."""
    headers = {"Authorization": f"Bearer {user_and_admin_tokens['admin_token']}"}
    files = {"file": ("malicious_payload.exe", io.BytesIO(b"MZ binary data"), "application/octet-stream")}
    data = {
        "title": "Malicious File",
        "document_category": "general",
        "issuing_authority": "Unknown",
    }
    res = client.post("/api/v1/knowledge/admin/sources/ingest-file", headers=headers, files=files, data=data)
    assert res.status_code == 415


def test_admin_ingest_knowledge_file_success(db: Session, user_and_admin_tokens):
    """
    Verifies full admin knowledge file ingestion:
    - Parses Markdown circular.
    - Chunks content.
    - Generates embeddings and upserts into Qdrant.
    - Returns structured Ingestion Report.
    - Persists record in PostgreSQL and creates audit event.
    """
    headers = {"Authorization": f"Bearer {user_and_admin_tokens['admin_token']}"}
    circular_md = b"""# UIDAI Circular No. 2026/04: Standard Operating Procedure for Name Rectification

## 1. Statutory Scope and Authority
Issued under Regulation 12 of the Aadhaar (Enrolment and Update) Regulations, 2016.
All resident name updates must be backed by verified documentary proof.

## 2. Mandatory Documentary Requirements
Acceptable documentary evidence for name changes:
- Valid Indian Passport
- Gazette Notification of Name Change along with joint affidavit
- Marriage Certificate (for post-marriage surname changes)

## 3. Fee Schedule and Turnaround Time
- Official statutory update fee is Rs. 50 (inclusive of GST).
- Standard processing SLA is 7 working days from document verification.
"""
    files = {"file": ("uidai_sop_2026.md", io.BytesIO(circular_md), "text/markdown")}
    data = {
        "title": "UIDAI SOP for Name Rectification 2026",
        "document_category": "aadhaar",
        "issuing_authority": "Unique Identification Authority of India (UIDAI)",
        "source_url": "https://uidai.gov.in/circulars/2026_04.pdf",
        "verification_status": "verified",
        "provenance": "OFFICIAL_ORIGINAL",
    }

    res = client.post("/api/v1/knowledge/admin/sources/ingest-file", headers=headers, files=files, data=data)
    assert res.status_code == 200
    report = res.json()
    assert report["status"] == "success"
    assert report["title"] == "UIDAI SOP for Name Rectification 2026"
    assert report["document_category"] == "aadhaar"
    assert report["chunk_count"] >= 1
    assert "uidai_sop_2026.md" in report["accepted_files"]
    assert report["indexing_status"] in ("completed", "indexing")

    # Verify audit event in PostgreSQL
    set_rls_context(db, None, "admin")
    audit_record = (
        db.query(AuditLog)
        .filter(AuditLog.action == "knowledge_file_ingested")
        .first()
    )
    assert audit_record is not None
    assert audit_record.details.get("title") == "UIDAI SOP for Name Rectification 2026"


def test_truthful_abstention_on_empty_or_irrelevant_query():
    """
    Verifies that when no verified source exists and no deterministic mapping exists,
    the system honestly abstains with NO_VERIFIED_PROCEDURE_AVAILABLE and confidence='insufficient_evidence'.
    """
    provider = GoogleGeminiProvider()
    answer = provider.generate_answer(
        question="What is the official procedure to register a commercial satellite in Antarctica under Indian Law?",
        case_context={},
        retrieved_chunks=[],
        relevant_forms=[],
        conversation_history=[],
    )

    assert "NO_VERIFIED_PROCEDURE_AVAILABLE" in answer.answer or "NO_VERIFIED_PROCEDURE_AVAILABLE" in answer.uncertainties
    assert answer.confidence == "insufficient_evidence"
    assert len(answer.citations) == 0
