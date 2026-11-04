# CONVELINA — Master System Architecture & Engineering Blueprint

```
  ██████╗ ██████╗ ███╗   ██╗██╗   ██╗███████╗██╗     ██╗███╗   ██╗ █████╗ 
 ██╔════╝██╔═══██╗████╗  ██║██║   ██║██╔════╝██║     ██║████╗  ██║██╔══██╗
 ██║     ██║   ██║██╔██╗ ██║██║   ██║█████╗  ██║     ██║██╔██╗ ██║███████║
 ██║     ██║   ██║██║╚██╗██║╚██╗ ██╔╝██╔══╝  ██║     ██║██║╚██╗██║██╔══██║
 ╚██████╗╚██████╔╝██║ ╚████║ ╚████╔╝ ███████╗███████╗██║██║ ╚████║██║  ██║
  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═══╝  ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
 High-Assurance AI-Powered Identity Discrepancy Detection & PKI Verification Platform
```

**Document Version:** 2.0.0  
**Classification:** Enterprise System Architecture Specification  
**Status:** Production-Grade / Active Implementation Baseline  
**Maintainer:** CONVELINA Core Engineering & Security Architecture  

---

## 1. Executive System Overview & Mission

**CONVELINA** is a high-assurance, privacy-first identity discrepancy detection and resolution platform. It bridges the critical trust gap between mismatched citizen identity records across Indian government and institutional documents (Aadhaar, PAN, Passport, Driving License, Voter ID, and Educational Certificates).

### Core Architectural Invariants:
1. **Aadhaar Act Section 29 Compliance**: Zero permanent storage of raw Aadhaar images or unmasked numbers. Ephemeral POSIX-restricted file creation, instant Verhoeff checksum validation, immediate 8-digit masking (`XXXX-XXXX-1234`), and atomic shredding before HTTP response termination.
2. **Forced PostgreSQL Row-Level Security (RLS)**: Every tenant table is protected by PostgreSQL kernel-level RLS policies. Runtime connections execute strictly under an unprivileged, non-superuser role (`consolith_app`) using transaction-local session scoping (`SET LOCAL app.current_user_id`) to prevent connection pool data contamination.
3. **Cryptographically Chained Append-Only Audit Trail**: Every administrative, verification, and data mutation event is hashed with SHA-256 and chained to the previous entry. Database statement triggers strictly block `UPDATE` and `DELETE` operations on the audit ledger.
4. **Zero-Hallucination Grounded AI (RAG)**: AI legal guidance is grounded in an indexed Qdrant vector database containing 25 official government gazettes and circulars. A hard cosine similarity floor ($\ge 0.55$) prevents hallucinated procedures; answers below this threshold gracefully decline to answer.
5. **Ed25519 PKI Public Verification**: Approved correction dossiers receive an asymmetric Ed25519 cryptographic signature and verifiable QR code payload, enabling offline, tamper-evident authenticity verification by verifying officers.

---

## 2. Visual Tech Stack Matrix & Technology Inventory

```
+---------------------------------------------------------------------------------------------------------+
|                                        CONVELINA TECH STACK                                             |
+---------------------------------------------------------------------------------------------------------+
| FRONTEND            | Next.js 14 (App Router) | TypeScript 5 | Tailwind CSS | Framer Motion | Lucide     |
| EDGE PROXY          | Caddy 2.8 Server (Auto-TLS, zstd/gzip, 15MB Body Ceiling, Security Headers)        |
| BACKEND ENGINE      | Python 3.11 | FastAPI (Starlette + Pydantic v2 Rust Core) | Uvicorn (uvloop)       |
| COMPUTER VISION     | Tesseract 5.5 OCR | Poppler (pdftoppm) | OpenCV (cv2) | Pillow (PIL) | pdf2image  |
| STRING & PHONETICS  | RapidFuzz (C++ SIMD AVX2) | Jellyfish (Rust/C Double Metaphone) | Levenshtein      |
| RELATIONAL DATABASE | PostgreSQL 16 Alpine (Forced RLS, B-Tree Indexes, Connection Pooling)              |
| VECTOR DATABASE     | Qdrant v1.11 (HNSW Indexing, Cosine Metric, 1024-Dim Vectors, Memory Fallback)     |
| CRYPTOGRAPHY & PKI  | Ed25519 (RFC 8032) | Fernet AES-256 | SHA-256 Chaining | Verhoeff Checksum       |
| IDENTITY & AUTH     | Firebase Admin SDK (RS256 JWT) | Resend API Email OTP (6-Digit CSPRNG) | RBAC    |
| DEVOPS & TESTING    | Docker Multi-Stage | Compose Network Segmentation | Pytest | Playwright | OpenQodex|
+---------------------------------------------------------------------------------------------------------+
```

### Detailed Component Specifications

| Layer / Subsystem | Technology | Version | Architectural Role | Core Technical Advantage |
| :--- | :--- | :--- | :--- | :--- |
| **Presentation Tier** | ![Next.js](https://img.shields.io/badge/Next.js_14-black?style=flat&logo=next.js) ![TypeScript](https://img.shields.io/badge/TypeScript_5-3178C6?style=flat&logo=typescript&logoColor=white) ![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS_3-38B2AC?style=flat&logo=tailwind-css&logoColor=white) | 14.2.14 / TS 5.4 | Citizen Portal, Officer Console, Admin Audit Dashboard | Server-Side Rendering (SSR), zero client bundle leak, strict TypeScript typing, responsive Tailwind utility styling. |
| **Edge Gateway** | ![Caddy](https://img.shields.io/badge/Caddy_Proxy-2.8-00ADD8?style=flat&logo=caddy&logoColor=white) | 2.8.4-alpine | Reverse proxy, TLS termination, request throttling, DoS filtering | Memory-safe Go implementation, automatic Let's Encrypt TLS, HTTP/2 & HTTP/3 support, 15MB body payload ceiling. |
| **API Application Tier** | ![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat&logo=fastapi&logoColor=white) ![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white) ![Pydantic](https://img.shields.io/badge/Pydantic_v2-Rust_Core-E92063?style=flat) | Python 3.11 / FastAPI 0.110 | Asynchronous REST API, schema validation, dependency injection | Non-blocking async event loop (`uvloop`), Rust-powered data parsing via Pydantic v2, automatic OpenAPI contract generation. |
| **Computer Vision / OCR** | ![Tesseract](https://img.shields.io/badge/Tesseract_OCR-5.5-blue?style=flat) ![OpenCV](https://img.shields.io/badge/OpenCV-4.9-5C3EE8?style=flat&logo=opencv&logoColor=white) | Tesseract 5.5 / OpenCV 4.9 | Image binarization, skew correction, text rasterization | C++ native engine execution, Poppler PDF rendering, adaptive thresholding for degraded stamp/seal documents. |
| **Phonetic & Fuzzy Engine** | ![RapidFuzz](https://img.shields.io/badge/RapidFuzz-SIMD_AVX2-critical?style=flat) ![Jellyfish](https://img.shields.io/badge/Jellyfish-Double_Metaphone-orange?style=flat) | RapidFuzz 3.8 / Jellyfish 1.0 | Indian name variation, phonetic matching, OCR typo compensation | C++ compiled SIMD vectorization for sub-microsecond string distance; Double Metaphone handles Indian multilingual phonetics. |
| **Relational Storage** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_Alpine-336791?style=flat&logo=postgresql&logoColor=white) | 16.2-alpine | Core business data, identity records, audit ledger, RLS boundary | Kernel-level Row-Level Security, ACID transactions, non-superuser role separation, composite index query speed. |
| **Vector Engine** | ![Qdrant](https://img.shields.io/badge/Qdrant-v1.11-red?style=flat&logo=qdrant&logoColor=white) | 1.11.0 | High-dimensional semantic search over government legal circulars | HNSW graph indexing, 1024-dimensional dense vectors, sub-5ms cosine retrieval, seamless in-process memory test mode. |
| **Cryptographic PKI** | ![Ed25519](https://img.shields.io/badge/Ed25519-RFC_8032-success?style=flat) ![Cryptography](https://img.shields.io/badge/Cryptography-PyCA-yellow?style=flat) | PyCA Cryptography 42.0 | Asymmetric attestation signing, Fernet AES-256 payload encryption | 128-bit security level, immune to side-channel timing attacks, ultra-compact 64-byte signatures for QR code embedding. |
| **Authentication** | ![Firebase](https://img.shields.io/badge/Firebase_Admin-JWT_RS256-FFA611?style=flat&logo=firebase&logoColor=white) ![Resend](https://img.shields.io/badge/Resend-Email_OTP-000000?style=flat) | Firebase Admin 6.5 / Resend API | User authentication, identity verification, 6-digit OTP delivery | Hardware-backed RS256 token verification, CSPRNG OTP generation with 60-second cooldown and 10/hr IP rate limits. |
| **Orchestration & DevOps**| ![Docker](https://img.shields.io/badge/Docker-Multi--Stage-2496ED?style=flat&logo=docker&logoColor=white) ![Compose](https://img.shields.io/badge/Docker_Compose-Isolated_Nets-2496ED?style=flat) | Docker 26.x / Compose v2 | Isolated multi-container deployment, network segregation | Complete separation of `internal-net` (no host ports) and `public-net`, non-root execution (`security_opt: [no-new-privileges]`). |

---

## 3. Master End-to-End System Architecture Blueprint

The following diagram illustrates the complete architectural blueprint across all client, network, compute, and persistence layers.

```mermaid
flowchart TB
    subgraph Clients["Presentation Layer (Client Browsers)"]
        Citizen["Citizen User Interface<br/>(Next.js 14 / Tailwind / Lucide)<br/>• Document Upload & OCR Status<br/>• Conflict Discrepancy Matrix<br/>• RAG AI Assistant Interface<br/>• Correction Dossier Generator"]
        Officer["Verification Officer Console<br/>(Next.js 14 Admin Portal)<br/>• Case Review Worklist<br/>• Forensic Document Inspector<br/>• Ed25519 Attestation Issuer<br/>• Tamper-Evident Audit Explorer"]
    end

    subgraph Edge["Edge Infrastructure & Gateway Tier"]
        Caddy["Caddy 2.8 Reverse Proxy<br/>(Ports 80 / 443)<br/>• Automatic TLS 1.3 Termination<br/>• zstd / gzip Compression Engine<br/>• Request Body Boundary (Max 15MB)<br/>• Security Headers & X-Frame DENY"]
    end

    subgraph PublicNet["Public Container Network (public-net)"]
        FrontendService["Frontend Container<br/>(Node 20 Alpine / Next.js SSR)<br/>Port 3000"]
        BackendService["Backend Application Container<br/>(FastAPI / Python 3.11 / Uvicorn)<br/>Port 8000 | 4 Async Workers"]
    end

    subgraph InternalNet["Internal Isolated Container Network (internal-net - No Internet / No Host Ports)"]
        subgraph AppCore["FastAPI Backend Modular Subsystems"]
            AuthEngine["Auth & RBAC Module<br/>• Firebase RS256 JWT Decryption<br/>• Resend Email OTP (60s Cooldown)<br/>• Role Guard: Citizen / Officer / Admin"]
            OCREngine["OCR Ingestion Subsystem<br/>• Magic-Byte File Validation<br/>• POSIX 0600 Ephemeral File Storage<br/>• Tesseract 5.5 + Poppler Rasterizer<br/>• Aadhaar Verhoeff & 8-Digit Masking<br/>• Fernet AES-256 Payload Encryption"]
            ConflictEngine["Conflict Detection Subsystem<br/>• Unicode NFKC Normalizer<br/>• SIMD RapidFuzz Levenshtein<br/>• Jellyfish Double Metaphone<br/>• Pairwise Canonical Upsert"]
            RAGEngine["RAG Assistant Orchestrator<br/>• Deterministic Dense Embeddings<br/>• Cosine Similarity Floor (>= 0.55)<br/>• Grounding & Citation Validator<br/>• Circuit Breaker Fallback"]
            PKIEngine["PKI Attestation Engine<br/>• RFC 8785 Canonical JSON<br/>• Ed25519 Digital Signatures<br/>• High-Density QR Synthesis"]
            AuditService["Audit Chaining Engine<br/>• Merkle-Style SHA-256 Link<br/>• Immutable Event Logging"]
        end

        subgraph StorageLayer["Data & Vector Persistence Tier"]
            PostgreSQL[("PostgreSQL 16 Alpine Database<br/>• Forced Row-Level Security (RLS)<br/>• Non-Superuser Role: consolith_app<br/>• Transaction-Local Context (SET LOCAL)<br/>• Statement Trigger: Block UPDATE/DELETE<br/>• B-Tree Composite Indexes")]
            QdrantDB[("Qdrant Vector Database v1.11<br/>• HNSW Vector Graph Index<br/>• 25 Official Indian Gazettes/Circulars<br/>• 1024-Dimensional Dense Vectors<br/>• In-Process Memory Fallback")]
        end
    end

    subgraph External["External Cloud Integrations"]
        FirebaseAPI["Google Firebase Auth<br/>(Identity Provider / Token Issuer)"]
        ResendAPI["Resend Email API<br/>(Transactional OTP Dispatch)"]
        GeminiAPI["Google Gemini 1.5 Flash API<br/>(Strict System Prompt / Grounded Legal RAG)"]
    end

    %% Network Connections
    Citizen -->|"HTTPS / WSS"| Caddy
    Officer -->|"HTTPS / WSS"| Caddy
    Caddy -->|"Reverse Proxy /"| FrontendService
    Caddy -->|"Reverse Proxy /api/*"| BackendService

    FrontendService -.->|"Client Fetch / API Calls"| Caddy
    BackendService --> AuthEngine
    BackendService --> OCREngine
    BackendService --> ConflictEngine
    BackendService --> RAGEngine
    BackendService --> PKIEngine
    BackendService --> AuditService

    AuthEngine -->|"Token Claims"| FirebaseAPI
    AuthEngine -->|"Send OTP Email"| ResendAPI
    RAGEngine -->|"Structured Prompt"| GeminiAPI

    OCREngine -->|"Encrypted Ingestion"| PostgreSQL
    ConflictEngine -->|"Pairwise Upserts"| PostgreSQL
    RAGEngine -->|"Top-K Vector Search"| QdrantDB
    PKIEngine -->|"Attestation Records"| PostgreSQL
    AuditService -->|"Append Immutable Log"| PostgreSQL

    style Caddy fill:#005f73,stroke:#0a9396,stroke-width:2px,color:#fff
    style PostgreSQL fill:#1d3557,stroke:#457b9d,stroke-width:2px,color:#fff
    style QdrantDB fill:#e63946,stroke:#f1faee,stroke-width:2px,color:#fff
    style BackendService fill:#264653,stroke:#2a9d8f,stroke-width:2px,color:#fff
    style FrontendService fill:#2b2d42,stroke:#8d99ae,stroke-width:2px,color:#fff
```

---

## 4. End-to-End System Pipelines & Data Flows

### Pipeline 1: Ephemeral Document Upload & Ingestion Pipeline

This pipeline enforces strict compliance with the **Aadhaar Act Section 29** by eliminating persistent storage of raw identity images and identity numbers.

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen Client
    participant Caddy as Caddy Reverse Proxy
    participant Upload as Document Ingest Router
    participant Validator as Magic-Byte Validator
    participant Disk as Ephemeral Scratch (/tmp)
    participant Tesseract as Tesseract 5.5 OCR
    participant Parser as Document Schema Parser
    participant Fernet as AES-256 Fernet Encryptor
    participant DB as PostgreSQL (RLS Scoped)

    User->>Caddy: POST /api/v1/documents/upload (multipart/form-data)
    Caddy->>Caddy: Validate Payload Size (Ceiling: 15MB)
    Caddy->>Upload: Forward request to FastAPI backend
    Upload->>Validator: Inspect file header magic bytes (%PDF-, \x89PNG, \xff\xd8\xff)
    alt Invalid Header or MIME mismatch
        Validator-->>Upload: Raise 400 Bad Request ("Invalid file format")
        Upload-->>User: HTTP 400 Rejected
    else Valid File Format
        Validator-->>Upload: Header Verified
        Upload->>Disk: Write temporary file with POSIX permissions 0600
        Upload->>Tesseract: Rasterize PDF/image & extract raw text stream
        Tesseract-->>Upload: Raw OCR text output
        Upload->>Parser: Route to specific parser (Aadhaar / PAN / Passport)
        alt Document is Aadhaar
            Parser->>Parser: Validate 12-digit number via Verhoeff Algorithm
            Parser->>Parser: Mask first 8 digits -> XXXX-XXXX-1234
        end
        Parser-->>Upload: Extracted normalized metadata (Name, DOB, Gender, etc.)
        Upload->>Fernet: Encrypt sensitive fields at rest using symmetric AES-256
        Fernet-->>Upload: Encrypted ciphertext
        Upload->>DB: INSERT INTO documents under consolith_app (Scoped to current_user_id)
        Upload->>Disk: Shred & unlink temporary file (finally block guarantee)
        Upload-->>User: HTTP 201 Created (Masked metadata, Document UUID)
    end
```

#### Pipeline Techniques & Controls:
- **Magic-Byte Sniffing**: Prevents executable or malicious payload injection by inspecting the first 8 bytes of the binary stream rather than trusting the `Content-Type` header.
- **POSIX 0600 Ephemeral Sandbox**: Temporary files on disk are readable only by the non-root application process (`convelina`) and exist only for the duration of OCR execution.
- **Verhoeff Checksum**: Detects accidental transcription errors and fake Aadhaar numbers using a dihedral group $D_5$ permutation algorithm.
- **Atomic Unlinking**: File shredding occurs in a mandatory Python `finally` block, ensuring zero residual files even if OCR crashes or throws an exception.

---

### Pipeline 2: Cross-Document Conflict Detection & SIMD Matching Pipeline

```mermaid
flowchart TD
    Start["Trigger: Document Ingestion or Manual POST /api/v1/conflicts/detect"] --> FetchDocs["Fetch Citizen's Active Documents<br/>(PostgreSQL RLS: user_id = current_user_id)"]
    FetchDocs --> Decrypt["Decrypt Sensitive Identity Fields (Fernet AES-256)"]
    Decrypt --> PairGen["Generate Canonical Pairs:<br/>doc_a_id &lt; doc_b_id (Eliminates Duplicate Comparisons)"]
    
    subgraph AttributeMatching["Pairwise Multi-Attribute Evaluation"]
        PairGen --> CompareName["Attribute: Full Name"]
        PairGen --> CompareDOB["Attribute: Date of Birth"]
        PairGen --> CompareParent["Attribute: Parent / Spouse Name"]
        PairGen --> CompareGender["Attribute: Gender"]

        CompareName --> NormName["Unicode NFKC Normalization<br/>Strip Titles (Shri, Smt, Dr)<br/>Whitespace Collapse"]
        NormName --> SIMDMatch["SIMD Accelerated RapidFuzz:<br/>• Levenshtein Distance<br/>• Token Sort Ratio<br/>• Jaro-Winkler Metric"]
        NormName --> PhoneticMatch["Jellyfish Double Metaphone:<br/>Primary & Secondary Phonetic Codes"]
        SIMDMatch & PhoneticMatch --> ScoreName{"Score &lt; 0.90?"}

        CompareDOB --> ParseDOB["Parse Formats:<br/>ISO (YYYY-MM-DD)<br/>Indian (DD/MM/YYYY)<br/>Year-Only (YYYY)"]
        ParseDOB --> ScoreDOB{"Exact Date Mismatch?"}

        CompareParent --> NormParent["Normalize & Double Metaphone"]
        NormParent --> ScoreParent{"Score &lt; 0.85?"}

        CompareGender --> NormGender["Normalize (M/F/O)"]
        NormGender --> ScoreGender{"Mismatch?"}
    end

    ScoreName -->|Yes| FlagName["Flag NAME Discrepancy<br/>Severity: HIGH / MEDIUM"]
    ScoreDOB -->|Yes| FlagDOB["Flag DOB Discrepancy<br/>Severity: CRITICAL"]
    ScoreParent -->|Yes| FlagParent["Flag PARENT Discrepancy<br/>Severity: MEDIUM"]
    ScoreGender -->|Yes| FlagGender["Flag GENDER Discrepancy<br/>Severity: CRITICAL"]

    FlagName & FlagDOB & FlagParent & FlagGender --> UpsertConflict["Idempotent Database Upsert<br/>Constraint: uq_conflicts_pair_field"]
    UpsertConflict --> AuditChaining["Record CONFLICT_DETECTED in Audit Ledger<br/>Compute SHA-256 Linked Hash"]
    AuditChaining --> Result["Return Discrepancy Dossier to Frontend Client"]
```

#### Pipeline Techniques & Controls:
- **Canonical Pair Ordering**: Comparisons are locked to `doc_a_id < doc_b_id`, guaranteeing $O(N(N-1)/2)$ comparisons without duplicate or reverse-pair permutations.
- **Double Metaphone Integration**: Successfully resolves traditional Indian naming variations (e.g., "Chandra" vs "Chander", "Laxmi" vs "Lakshmi") that would trigger false positive conflicts in pure Levenshtein systems.
- **Year-Only Tolerance**: Accurately handles legacy Indian identity cards where only birth year is printed, avoiding false conflict flags when paired with full birth date documents.

---

### Pipeline 3: Zero-Hallucination RAG Assistant & Legal Circular Retrieval Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Citizen as Citizen Client
    participant API as Assistant Router (/api/v1/assistant/chat)
    participant DB as PostgreSQL (RLS)
    participant Embed as Deterministic Embedding Engine
    participant Qdrant as Qdrant Vector Engine (Port 6333)
    participant LLM as Google Gemini 1.5 Flash API
    participant Validator as Citation & Grounding Verifier

    Citizen->>API: POST /api/v1/assistant/chat {message, conflict_id, conversation_id}
    API->>DB: Fetch conflict context & document types under RLS
    DB-->>API: Conflict details (e.g. "Name mismatch between PAN and Aadhaar")
    API->>Embed: Compute 1024-dimensional dense query vector
    Embed-->>API: Query vector embedding
    API->>Qdrant: Execute HNSW vector search (Top-K=5, Collection: consolith_knowledge)
    Qdrant-->>API: Retrieved legal circular chunks with cosine scores
    API->>API: Filter chunks: enforce relevance score floor >= 0.55
    alt Max Score < 0.55 Floor
        API-->>Citizen: Return grounded refusal: "I do not have verified official circulars covering this specific discrepancy. Please consult a verification officer."
    else Chunks >= 0.55 Found
        API->>LLM: Dispatch structured prompt with retrieved context, legal circular text, and strict XML rules
        alt Gemini API Rate Limit / Failure
            API->>API: Activate Circuit Breaker fallback
            API-->>Citizen: Return deterministic procedural fallback based on document pair rulebook
        else Gemini 200 OK
            LLM-->>API: Structured response {answer, resolution_steps, required_forms, citations}
            API->>Validator: Validate that every cited circular ID exists in retrieved chunks
            alt Citation Hallucination Detected
                Validator->>Validator: Strip fabricated citation and attach disclaimer
            end
            Validator-->>API: Verified grounded answer
            API->>DB: INSERT into assistant_messages (RLS protected)
            API-->>Citizen: HTTP 200 OK (Grounded answer with legal badges and official forms)
        end
    end
```

#### Pipeline Techniques & Controls:
- **Cosine Relevance Floor ($\ge 0.55$)**: Mathematically eliminates off-topic or hallucinated LLM responses by dropping non-authoritative chunks.
- **Citation Cross-Verification**: The backend verifies every citation token in the LLM response against the retrieved chunk IDs before serving the payload to the citizen.
- **Circuit Breaker Fallback**: If external LLM APIs fail or exhaust quota, the system seamlessly degrades to deterministic local procedure trees.

---

### Pipeline 4: Officer Verification & Ed25519 PKI Attestation Pipeline

```mermaid
flowchart TD
    OfficerClient["Officer Console (Frontend)"] -->|"POST /api/v1/pki/attestations/issue"| AuthGuard{"Role Guard:<br/>require_officer / require_admin"}
    AuthGuard -->|Denied| HTTP403["HTTP 403 Forbidden"]
    AuthGuard -->|Authorized| FetchCase["Fetch Citizen Case Dossier & Verified Documents (RLS)"]
    
    FetchCase --> Canonicalize["Canonicalize Payload via RFC 8785:<br/>Deterministic Key Ordering, Zero Whitespace,<br/>Strict UTF-8 Encoding"]
    
    Canonicalize --> SignPayload["Ed25519 Private Key Engine (RFC 8032):<br/>Generate 64-Byte Digital Signature over SHA-512 Digest"]
    
    SignPayload --> FormQR["Synthesize Offline Verifiable QR Code Payload:<br/>{doc_id, officer_id, timestamp, signature, pubkey_fingerprint}"]
    
    FormQR --> SaveAttestation["INSERT INTO document_attestations<br/>(Protected by RLS)"]
    
    SaveAttestation --> FetchLastHash["Query Latest Audit Hash: get_latest_audit_hash()"]
    FetchLastHash --> ComputeHash["Compute SHA-256 Link:<br/>SHA256(prev_hash + officer_id + 'ATTESTATION_ISSUED' + details + now)"]
    
    ComputeHash --> InsertAudit["INSERT INTO audit_log<br/>(Trigger Enforces Immutability)"]
    
    InsertAudit --> Response["Return Cryptographic Attestation Certificate + Verifiable QR"]
```

#### Pipeline Techniques & Controls:
- **RFC 8785 Canonical JSON**: Eliminates signature invalidation caused by JSON formatting variations across different operating systems.
- **Ed25519 Asymmetric Cryptography**: Ultra-fast signature verification with 64-byte compact signatures suitable for inclusion inside standard 2D QR barcodes.
- **Dual-Verification Model**: Anyone can verify the attestation offline using CONVELINA's public key without requiring a database query.

---

### Pipeline 5: Append-Only Tamper-Evident SHA-256 Audit Trail Chaining

```mermaid
flowchart LR
    Genesis["Genesis Block<br/>Hash: 0000000000000000..."] --> Entry1["Audit Entry #1<br/>Hash: SHA256(Genesis + Event1)"]
    Entry1 --> Entry2["Audit Entry #2<br/>Hash: SHA256(Hash1 + Event2)"]
    Entry2 --> Entry3["Audit Entry #3<br/>Hash: SHA256(Hash2 + Event3)"]
    Entry3 --> Current["Audit Entry #N<br/>Hash: SHA256(HashN-1 + EventN)"]

    subgraph TriggerProtection["Database Engine Level Security Trigger"]
        MutationAttempt["Attacker / Malicious Script:<br/>UPDATE audit_log OR DELETE FROM audit_log"]
        Trigger{"PostgreSQL Trigger:<br/>block_audit_mutation()"}
        Abort["ABORT TRANSACTION:<br/>RAISE EXCEPTION 'Audit log is append-only'"]
        
        MutationAttempt --> Trigger
        Trigger --> Abort
    end
```

---

## 5. Network Topology, Connectivity & Security Boundaries

```
+---------------------------------------------------------------------------------------------------------+
|                                    OUTSIDE WORLD (INTERNET)                                             |
|                                                |                                                        |
|                                      HTTPS / Port 443 (TLS 1.3)                                         |
|                                                v                                                        |
| +-----------------------------------------------------------------------------------------------------+ |
| | CADDY 2.8 REVERSE PROXY CONTAINER (Edge)                                                            | |
| | - Auto TLS Termination (Let's Encrypt / ZeroSSL)                                                    | |
| | - Rate Limiting & DoS Protection                                                                    | |
| | - Strict Max Request Body: 15MB                                                                     | |
| | - Security Headers: X-Frame DENY, nosniff, CSP default-src 'self'                                  | |
| +-----------------------------------------------------------------------------------------------------+ |
|         |                                                           |                                   |
|         | Reverse Proxy (Port 3000)                                 | Reverse Proxy (Port 8000)         |
|         v                                                           v                                   |
| +------------------------------------+      +---------------------------------------------------------+ |
| | PUBLIC-NET: FRONTEND CONTAINER     |      | PUBLIC-NET & INTERNAL-NET: BACKEND CONTAINER            | |
| | - Next.js 14 App Router (Node 20)  |      | - FastAPI Python 3.11 (4 Uvicorn Workers)               | |
| | - SSR & Client Workspace UI        |      | - Pydantic v2 Rust Schema Core                          | |
| | - Non-Root User Execution          |      | - Non-Superuser DB Connection: consolith_app            | |
| +------------------------------------+      +---------------------------------------------------------+ |
|                                                                     |                                   |
|                                      +------------------------------+--------------------+              |
|                                      | TCP (Port 5432)                                   | TCP (Port 6333) |
|                                      v                                                   v              |
|                     +---------------------------------------+   +-------------------------------------+ |
|                     | INTERNAL-NET: POSTGRESQL 16 CONTAINER |   | INTERNAL-NET: QDRANT VECTOR DB      | |
|                     | - Internal Network ONLY (internal:true)|   | - Internal Network ONLY (internal)  | |
|                     | - ZERO Exposed Host Ports             |   | - ZERO Exposed Host Ports           | |
|                     | - Forced Row-Level Security (RLS)     |   | - 25 Government Circulars Indexed   | |
|                     | - Append-Only Audit Trigger           |   | - Cosine Metric HNSW Graph          | |
|                     +---------------------------------------+   +-------------------------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

### Port & Integration Mapping Table

| Source | Destination | Protocol / Port | Network Boundary | Purpose | Security Controls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Client Browser** | Caddy Proxy | HTTPS / 443 | Internet $\to$ Host | Public ingress for UI and APIs | TLS 1.3, HSTS, 15MB body ceiling, Security Headers |
| **Caddy Proxy** | Frontend Container | HTTP / 3000 | `public-net` | Serves Next.js SSR and client assets | Reverse proxy route: `/` |
| **Caddy Proxy** | Backend Container | HTTP / 8000 | `public-net` | Routes API requests and docs | Reverse proxy route: `/api/*`, `/health` |
| **Backend Container**| PostgreSQL DB | TCP / 5432 | `internal-net` | Relational storage & RLS evaluation | `internal: true`, no exposed ports, `consolith_app` role |
| **Backend Container**| Qdrant Vector DB | TCP / 6333 | `internal-net` | RAG knowledge vector retrieval | `internal: true`, no exposed ports, REST/gRPC API |
| **Backend Container**| Firebase Admin | HTTPS / 443 | Egress $\to$ Google APIs | RS256 token verification | Ephemeral HTTP client with 10s connection timeout |
| **Backend Container**| Google Gemini | HTTPS / 443 | Egress $\to$ Google APIs | RAG answer synthesis | Grounding floor $\ge 0.55$, structured JSON outputs |
| **Backend Container**| Resend Email API | HTTPS / 443 | Egress $\to$ Resend APIs | OTP email dispatch | Bearer token authorization, 60-second cooldown |

---

## 6. Database Entity-Relationship & Row-Level Security Architecture

```mermaid
erDiagram
    users ||--o{ documents : "owns (RLS: user_id = current_user_id)"
    users ||--o{ conflicts : "owns (RLS: user_id = current_user_id)"
    users ||--o{ correction_drafts : "owns (RLS: user_id = current_user_id)"
    users ||--o{ assistant_conversations : "owns (RLS: user_id = current_user_id)"
    users ||--o{ email_otps : "receives"
    
    documents ||--o{ conflicts : "participates in as doc_a or doc_b"
    conflicts ||--o{ correction_drafts : "resolves"
    
    officers ||--o{ document_attestations : "issues (Ed25519 PKI)"
    documents ||--o{ document_attestations : "attested by"
    
    audit_log }|--|| users : "records actor event"

    users {
        uuid id PK
        string email UK
        string full_name
        string role "citizen | officer | admin"
        timestamp created_at
    }

    documents {
        uuid id PK
        uuid user_id FK
        string document_type "aadhaar | pan | passport | dl | voter"
        jsonb extracted_data "Fernet AES-256 Encrypted Payload"
        string status "processed | failed"
        timestamp created_at
    }

    conflicts {
        uuid id PK
        uuid user_id FK
        uuid doc_a_id FK
        uuid doc_b_id FK
        string field_name "name | dob | parent_name | gender"
        string value_a
        string value_b
        float similarity_score
        string severity "critical | high | medium | low"
        string status "detected | resolved | dismissed"
    }

    document_attestations {
        uuid id PK
        uuid document_id FK
        uuid officer_id FK
        string signature_b64 "Ed25519 Signature"
        string public_key_fingerprint
        jsonb canonical_payload "RFC 8785 JSON"
        timestamp issued_at
    }

    audit_log {
        uuid id PK
        uuid user_id FK
        string action "DOCUMENT_UPLOAD | CONFLICT_DETECTED | ATTESTATION_ISSUED"
        string entity_type
        uuid entity_id
        string previous_hash "SHA-256 Link"
        string hash "SHA-256 Digest"
        timestamp created_at "IMMUTABLE"
    }
```

---

## 7. Architectural Techniques & Design Patterns Summary

1. **Non-Superuser RLS Connection Pooling**:  
   Rather than connecting to PostgreSQL as `postgres`, FastAPI connects strictly as the unprivileged role `consolith_app`. Transaction-local variables (`SET LOCAL app.current_user_id = :uid`) guarantee that when the connection returns to the connection pool, user context is automatically dropped.
2. **Connection Pooling UUID Cast Safety**:  
   PostgreSQL throws runtime type errors if an empty string `""` is cast directly to `::uuid`. CONVELINA guards every RLS policy with:
   $$\text{NULLIF}(\text{current\_setting}('app.current\_user\_id', \text{true}), '')::\text{uuid}$$
3. **Zero-PII Storage Post-OCR**:  
   Under Aadhaar Act Section 29, raw document images are never persisted to object storage or database blobs. File bytes exist only in an ephemeral POSIX 0600 file buffer in RAM/`/tmp` and are wiped instantly post-OCR.
4. **SIMD-Accelerated Levenshtein Matching**:  
   Using C++ AVX2 vector instructions via `RapidFuzz`, the discrepancy engine computes tens of thousands of string variations in fractions of a millisecond.
5. **Merkle-Style Audit Integrity**:  
   Every audit entry forms a cryptographic hash chain:
   $$\text{Hash}_n = \text{SHA256}(\text{Hash}_{n-1} \parallel \text{User ID} \parallel \text{Action} \parallel \text{Payload} \parallel \text{Timestamp})$$
   Any manual row deletion or modification immediately breaks the cryptographic verification chain.
6. **Defense-in-Depth Container Hardening**:  
   All Docker containers run under non-root users (`uid 10001`), have `no-new-privileges: true` enabled, and are partitioned across isolated Docker networks (`internal-net` vs `public-net`).

---

*This document serves as the immutable architectural blueprint for CONVELINA.*

