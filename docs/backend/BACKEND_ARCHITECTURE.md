# CONVELINA — Backend Architecture & Application Core Specification

```
+---------------------------------------------------------------------------------------------------------+
| APPLICATION TIER: Python 3.11 | FastAPI (Starlette) | Uvicorn uvloop | Pydantic v2 Rust | SQLAlchemy 2.0 |
+---------------------------------------------------------------------------------------------------------+
```

**Classification:** Technical Architecture Specification  
**Component:** `backend/`  
**Status:** Production Verified | 85/85 Passing Pytest Tests  

---

## 1. Executive Overview

The CONVELINA backend is a high-performance asynchronous API engine built with **FastAPI** on **Python 3.11**. It executes non-blocking I/O via `uvloop`, coordinates native C/C++ computer vision libraries for ephemeral OCR, runs SIMD-accelerated discrepancy matching algorithms, grounds LLM advice via vector similarity search, and digitally signs approved dossiers using Ed25519 asymmetric cryptography.

---

## 2. Directory Architecture & Modular Subsystems

```
backend/
├── app/
│   ├── main.py                               # FastAPI application lifecycle, security headers & CORS
│   ├── config.py                             # Pydantic Settings (validated environment variables)
│   ├── core/                                 # Database & Infrastructure Foundation
│   │   ├── database.py                       # SQLAlchemy session factory, pool settings & RLS context
│   │   ├── migrate.py                        # Automated DDL migration runner & constraint creator
│   │   ├── validator.py                      # Magic-byte file inspector & stream size checker
│   │   └── firebase.py                       # Firebase Admin SDK initialization & RS256 token decoding
│   ├── dependencies/                         # Scoped FastAPI Route Guards
│   │   └── auth.py                           # require_authenticated_user, require_user, require_admin
│   ├── engine/                               # Discrepancy & Matching Core
│   │   ├── matcher.py                        # SIMD RapidFuzz Levenshtein & Jellyfish Double Metaphone
│   │   └── normalizer.py                     # Unicode NFKC normalization, honorific & calendar parsing
│   ├── models/                               # SQLAlchemy ORM Data Models
│   │   ├── user.py                           # User, EmailOTP
│   │   ├── document.py                       # Document (encrypted payload)
│   │   ├── conflict.py                       # Conflict (composite unique constraint)
│   │   ├── audit_log.py                      # AuditLog (immutable ledger)
│   │   └── pki.py                            # DocumentAttestation (Ed25519 digital signature)
│   ├── ocr/                                  # Computer Vision Ingestion Subsystem
│   │   ├── engine.py                         # Tesseract 5.5 + Poppler C++ rasterizer
│   │   └── parsers/                          # Document parsers (aadhaar.py, pan.py, passport.py)
│   ├── rag/                                  # Cognitive Vector & Assistant Subsystem
│   │   ├── qdrant.py                         # Qdrant client & collection indexer
│   │   ├── embeddings.py                     # Deterministic 1024-dim dense vector generator
│   │   └── assistant/orchestrator.py         # Grounding engine, relevance floor (>= 0.55), Gemini API
│   ├── routers/                              # REST API Route Controllers
│   │   ├── auth.py                           # /api/v1/auth (signup, login, OTP verify, /me)
│   │   ├── documents.py                      # /api/v1/documents (upload, preview, delete)
│   │   ├── conflicts.py                      # /api/v1/conflicts (detect, list, resolve)
│   │   ├── assistant.py                      # /api/v1/assistant (chat, conversations, citations)
│   │   ├── knowledge.py                      # /api/v1/knowledge (official circulars & forms)
│   │   ├── pki.py                            # /api/v1/pki (issue attestations, verify QR payloads)
│   │   └── admin.py                          # /api/v1/admin (audit logs, metrics, user directory, conflict & doc monitoring)
│   ├── schemas/                              # Pydantic v2 Rust Schema DTOs
│   │   ├── auth.py, document.py, conflict.py, assistant.py, pki.py
│   │   └── ...
│   └── services/                             # Domain Business Services
│       ├── audit_service.py                  # SHA-256 Merkle-style hash chainer & trigger manager
│       ├── encryption.py                     # Symmetric Fernet AES-256 encryption at rest
│       ├── email_service.py                  # Resend API transactional OTP email delivery
│       ├── document_exporter.py              # Standardized PDF & DOCX affidavit generator
│       └── pki_service.py                    # RFC 8785 canonical JSON & Ed25519 key management
├── tests/                                    # Pytest Test Suite (85 unit, integration, and RLS tests)
├── requirements.txt                          # Python pinned dependencies
├── pytest.ini                                # Test runner configuration
└── Dockerfile                                # Multi-stage production container build
```

---

## 3. Core Subsystem Workflows

### 3.1 Ephemeral Ingestion & Aadhaar Act Compliance
Implemented in [`backend/app/routers/documents.py`](file:///c:/Users/ajaya/Desktop/consolin/backend/app/routers/documents.py) and [`backend/app/ocr/parsers/aadhaar.py`](file:///c:/Users/ajaya/Desktop/consolin/backend/app/ocr/parsers/aadhaar.py):
1. **Magic-Byte Sniffing**: Inspects the first 8 bytes (`%PDF-`, `\x89PNG`, `\xff\xd8\xff`) to reject extension spoofing.
2. **POSIX 0600 Ephemeral Scratch**: Writes temporary files to `/tmp` with restricted permissions.
3. **Verhoeff Checksum**: Validates 12-digit Aadhaar numbers using dihedral group $D_5$ permutations.
4. **8-Digit Masking**: Masks sensitive numbers (`XXXX-XXXX-1234`).
5. **Fernet AES-256**: Encrypts sensitive extracted fields at rest.
6. **Mandatory Unlinking**: Calls `os.unlink()` in a guaranteed Python `finally` block to prevent disk persistence.

### 3.2 SIMD Discrepancy Matching
Implemented in [`backend/app/engine/matcher.py`](file:///c:/Users/ajaya/Desktop/consolin/backend/app/engine/matcher.py):
- **RapidFuzz C++ AVX2**: Calculates Levenshtein distance and Token Sort Ratio in sub-microseconds.
- **Jellyfish Double Metaphone**: Phonetically resolves Indian name variations (e.g. *Laxmi* vs *Lakshmi*, *Chandra* vs *Chander*).
- **Canonical Ordering**: Locks comparisons to `doc_a_id < doc_b_id` to eliminate reverse-pair duplication.

### 3.3 Zero-Hallucination Legal RAG
Implemented in [`backend/app/rag/assistant/orchestrator.py`](file:///c:/Users/ajaya/Desktop/consolin/backend/app/rag/assistant/orchestrator.py):
- Indexes 25 official Indian Gazettes and circulars in Qdrant.
- Enforces a hard **cosine relevance floor of 0.55**. Queries falling below this floor return a grounded refusal rather than guessing.
- Validates every generated citation against retrieved source chunk tokens before returning the response.

---

## 4. Execution & Testing Commands

```bash
# Run local development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run full test suite with Pytest
pytest -v

# Run RLS isolation tests specifically
pytest backend/tests/test_rls_isolation.py -v
```

