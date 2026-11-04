# CONVELINA — End-to-End Data Flow Architecture

**Classification:** Technical Architecture Specification  
**Status:** EVIDENCE-BASED IMPLEMENTATION TRACE  

---

## 1. Document Lifecycle & Upload Flow

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen Browser
    participant API as FastAPI Gateway
    participant Val as Magic Byte Validator
    participant Disk as Ephemeral Storage (/tmp)
    participant OCR as Tesseract 5.5 Engine
    participant Mask as Aadhaar Masker & Fernet
    participant DB as PostgreSQL (Forced RLS)

    Citizen->>API: POST /api/v1/documents/upload (multipart, Bearer JWT)
    API->>API: Enforce 1MB chunked stream (abort if > 10MB)
    API->>Val: Validate magic bytes (%PDF-, \x89PNG, \xff\xd8\xff)
    Val-->>API: Format confirmed valid
    API->>Disk: Write temporary file (POSIX 0600)
    API->>OCR: Rasterize PDF & execute Tesseract OCR
    OCR-->>API: Extracted raw text stream
    API->>Mask: Check Aadhaar Verhoeff checksum & mask first 8 digits (XXXX-XXXX-1234)
    Mask->>Mask: Encrypt sensitive payload at rest via Fernet
    API->>DB: INSERT into documents under consolith_app (RLS tenant scope)
    API->>Disk: Shred & unlink temporary file (finally block)
    API-->>Citizen: HTTP 201 Created (Document metadata, masked identifiers)
```

### Ingestion Security Controls:
1. **Size Boundary**: Bounded 1MB chunked reads abort immediately with HTTP 413 if the payload exceeds 10MB.
2. **Header Integrity**: Magic byte inspection eliminates extension-spoofing vectors.
3. **Aadhaar Privacy**: First 8 digits masked immediately; raw file destroyed from ephemeral storage before HTTP response returns.

---

## 2. Deterministic Conflict Detection Flow

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen Browser
    participant API as FastAPI Gateway
    participant Engine as Conflict Engine
    participant Norm as Field Normalizer
    participant Match as Phonetic & Fuzzy Matcher
    participant DB as PostgreSQL (Forced RLS)

    Citizen->>API: POST /api/v1/conflicts/detect (Bearer JWT)
    API->>DB: Fetch citizen's active decrypted document records under RLS
    DB-->>API: Document list (Doc A, Doc B, ...)
    API->>Engine: Generate canonical pairwise comparisons (doc_a_id < doc_b_id)
    loop For each comparable attribute (Name, DOB, Parent, Gender)
        Engine->>Norm: Normalize strings (strip titles, whitespace collapse, calendar dates)
        Norm-->>Engine: Normalized tokens
        Engine->>Match: Run Levenshtein distance, token_sort_ratio, Double Metaphone
        Match-->>Engine: Discrepancy detected with similarity score & severity
    end
    Engine->>DB: Idempotent upsert into `conflicts` table under RLS
    Engine->>DB: Record detection event in `audit_log` with SHA-256 chain
    DB-->>API: Saved conflicts
    API-->>Citizen: HTTP 200 OK (List of discrepancies with side-by-side values)
```

---

## 3. RAG Knowledge Assistant & Retrieval Flow

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen Browser
    participant API as FastAPI Assistant Router
    participant Embed as Deterministic BGE Service
    participant Qdrant as Qdrant Vector DB
    participant LLM as Google Gemini (1.5-Flash)
    participant Val as Citation Validator
    participant DB as PostgreSQL (Forced RLS)

    Citizen->>API: POST /api/v1/assistant/chat {message, conversation_id, conflict_id}
    API->>DB: Fetch active conflict context if provided (under RLS)
    API->>Embed: Project query into 1024-dim normalized dense vector
    Embed-->>API: Query vector
    API->>Qdrant: Search `consolith_knowledge` (Top-K=5)
    Qdrant-->>API: Retrieved procedural chunks with cosine similarity
    API->>API: Filter chunks: discard all chunks with score < 0.55 floor
    alt No chunks exceed 0.55 floor
        API-->>Citizen: HTTP 200 OK (Insufficient evidence notice; decline to guess)
    else Verified evidence available
        API->>LLM: Format strict XML prompt with case context, sources, and history
        alt Gemini API unavailable / error
            API-->>Citizen: "Assistant service is not currently available. Please try again later."
        else Gemini returns structured JSON
            LLM-->>API: Structured response {answer, resolution_steps, forms, citations}
            API->>Val: Cross-check every citation against retrieved chunk text
            Val-->>API: Verified grounded answer
            API->>DB: Persist user & assistant messages in assistant_messages (RLS)
            API-->>Citizen: HTTP 200 OK (Grounded guidance, source badges, verified forms)
        end
    end
```

---

## 4. Cryptographic Attestation & Audit Trail Flow

```mermaid
sequenceDiagram
    autonumber
    actor Officer as Verification Officer / Admin
    participant API as FastAPI PKI Router
    participant PKI as Ed25519 Keystore
    participant Hash as SHA-256 Audit Chainer
    participant DB as PostgreSQL (Forced RLS)

    Officer->>API: POST /api/v1/pki/attestations/issue (Bearer JWT)
    API->>DB: Retrieve case dossier and verified document fingerprint
    API->>PKI: Serialize canonical payload (RFC 8785)
    PKI->>PKI: Generate Ed25519 digital signature (RFC 8032)
    API->>DB: INSERT into `document_attestations` (RLS protected)
    API->>Hash: Fetch latest audit log hash via `get_latest_audit_hash()`
    Hash->>Hash: Compute SHA-256 (previous_hash + event_data)
    Hash->>DB: INSERT into `audit_log` (Statement trigger blocks UPDATE/DELETE)
    API-->>Officer: HTTP 201 Created (Attestation record, verifiable QR code payload)
```

---

## 5. Account Deletion & Data Purge Flow

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen Browser
    participant API as FastAPI Auth Router
    participant DB as PostgreSQL (Forced RLS)

    Citizen->>API: DELETE /api/v1/auth/account (Bearer JWT)
    API->>DB: Initialize citizen tenant RLS context (`SET LOCAL app.current_user_id`)
    API->>DB: CASCADE DELETE from `users` table:
    Note over DB: Cascade removes documents, conflicts, correction drafts,<br/>assistant conversations, and case review requests.
    API->>DB: Append immutable audit record `USER_ACCOUNT_DELETED`
    API-->>Citizen: HTTP 204 No Content
    Citizen->>Citizen: Invalidate client tokens and redirect to `/`
```

