# -*- coding: utf-8 -*-
"""
Chapter 5: SYSTEM ARCHITECTURE AND DETAILED DESIGN generator for CONVELINA Academic Report.
Includes Layered Architecture, OCR, Discrepancy Engine, RAG, Database Schema (Table 5.1),
ER Diagram (Fig 5.2), Deployment Diagram (Fig 5.3), Security Diagram (Fig 5.4), RLS, Ed25519 PKI, Audit Ledger.
Written in cohesive, academic paragraphs with NO bullet points.
"""

from .styles import (
    add_chapter_title, add_heading_1, add_heading_2, add_heading_3,
    add_body_paragraph, add_figure_block, add_table_block
)
from docx.shared import Inches

def build_chapter_5(doc, assets_dir):
    add_chapter_title(doc, "5", "SYSTEM ARCHITECTURE AND DETAILED DESIGN")

    add_heading_1(doc, "5.1 Layered Architecture Overview")
    add_body_paragraph(
        doc,
        "The architecture of CONVELINA is engineered around a clean, decoupled three-tier modular monolith pattern, structured into three "
        "interoperating architectural tiers: the Presentation Layer, the Application and Business Logic Layer, and the Data Persistence and "
        "Cryptographic Security Layer. This layered architecture ensures strict separation of concerns, enforces uniform security boundaries, "
        "and optimizes computational resource utilization across diverse deployment environments."
    )
    add_body_paragraph(
        doc,
        "Figure 5.1 illustrates the high-level layered system architecture of CONVELINA. The Presentation Layer interfaces with citizens and public "
        "officers through modern, responsive web workspaces. The Application Layer executes asynchronous processing pipelines for secure file "
        "ingestion, optical character recognition, multi-algorithmic fuzzy matching, and statutory knowledge retrieval. The Persistence and "
        "Security Layer provides multi-tenant data storage protected by PostgreSQL forced Row-Level Security, an in-process Qdrant vector database, "
        "and an internal Ed25519 Public Key Infrastructure (PKI) Certificate Authority engine."
    )

    fig_arch = f"{assets_dir}/fig_5_1_architecture.png"
    add_figure_block(
        doc,
        fig_arch,
        "5.1",
        "High-Level Layered System Architecture Diagram of CONVELINA Partitioned Across Presentation, Application, and Persistence Tiers"
    )

    add_heading_1(doc, "5.2 Presentation Layer Design")
    add_body_paragraph(
        doc,
        "The Presentation Layer is developed using Next.js 14, React, and TypeScript, leveraging the Next.js App Router for server-rendered "
        "performance and robust client-side interactivity. The user interface adheres strictly to an editorial, trustworthy design system inspired "
        "by the Google Stitch aesthetic guidelines. The visual palette employs clean, high-contrast, light-theme editorial tones: crisp warm off-white "
        "(#FAF9F6), deep slate (#111111), pure white surface containers (#FFFFFF), and subtle 1px hairline borders (#E7E5E0), intentionally avoiding "
        "distracting dark modes, vivid neon accents, or frivolous animations."
    )
    add_body_paragraph(
        doc,
        "Typography is carefully paired to convey institutional authority and readability: Merriweather serif headings communicate formal legal "
        "authenticity, while Inter sans-serif body typography provides optimal legibility across mobile devices and desktop displays. The presentation "
        "layer is partitioned into two specialized user workspaces: the Citizen Identity Workspace (providing intuitive drag-and-drop document "
        "upload, discrepancy inspection cards, interactive statutory RAG chat, and one-click affidavit generation) and the Administrative Verification "
        "Console (enabling public officers to audit discrepancy dossiers, inspect side-by-side OCR diffs, verify Ed25519 signatures, and review the "
        "cryptographic audit ledger)."
    )

    add_heading_1(doc, "5.3 Application and Business Logic Layer")
    add_body_paragraph(
        doc,
        "The Application and Business Logic Layer is powered by FastAPI, an asynchronous, high-throughput Python 3.11 web framework. FastAPI handles "
        "authenticated HTTP routing, multipart request streaming, asynchronous task coordination, and interface encapsulation across four "
        "specialized computational subsystems."
    )
    add_heading_2(doc, "5.3.1 Secure Document Ingestion and Magic Byte Validation")
    add_body_paragraph(
        doc,
        "Document ingestion endpoints enforce rigorous defense-in-depth validation prior to allocating processing resources. When a citizen uploads "
        "a document, the ingestion handler inspects the leading file bytes (magic bytes) to verify genuine MIME encoding (specifically verifying "
        "PDF headers '%PDF-', JPEG headers '0xFF 0xD8 0xFF', and PNG headers '0x89 0x50 0x4E 0x47'). File sizes are restricted to a maximum of 10 MB "
        "to prevent memory exhaustion attacks. Uploaded file names are strictly sanitized to eliminate directory traversal sequences (such as '../'), "
        "and payloads are ingested directly into transient memory streams without staging unencrypted files on shared disk volumes."
    )
    add_heading_2(doc, "5.3.2 Layout-Aware OCR Parsing and Field Extraction")
    add_body_paragraph(
        doc,
        "The optical extraction engine pairs Tesseract OCR 5.5.0 with Poppler rendering utilities. For multi-page PDF documents, the system "
        "rasterizes pages at 300 DPI up to a maximum limit of three pages, bounding peak memory consumption under 300 MB. To extract structured "
        "demographic entities from visually diverse Indian identity cards, the engine applies document-specific layout heuristics. The Aadhaar parser "
        "locates name, care-of (C/O) guardian lines, gender, and birth dates using localized bounding boxes. The PAN parser extracts the 10-character "
        "alphanumeric Permanent Account Number and verifies its structural syntax against Income Tax Department checksum rules. The Passport parser "
        "decodes the Machine Readable Zone (MRZ) according to ICAO Doc 9303 standards, while educational marksheet parsers isolate candidate and "
        "parental identifiers from tabulated examination layouts."
    )
    add_heading_2(doc, "5.3.3 Ephemeral Processing and Aadhaar Act Section 29 Compliance")
    add_body_paragraph(
        doc,
        "Compliance with Section 29 of the Aadhaar Act 2016 is enforced at the core architectural level. The system treats all raw identity card scans "
        "as strictly ephemeral data. Immediately following feature extraction and entity parsing, an unhandled exception trap in a mandatory 'finally:' "
        "execution block unlinks, zeroizes, and purges the temporary image buffer from memory. The platform permanently forbids long-term storage of raw "
        "identity scans. Furthermore, regular expression filters detect 12-digit Aadhaar numbers and automatically mask the initial eight digits, "
        "preserving only the last four digits (e.g., 'XXXX-XXXX-4041') across all database payloads, UI displays, and log outputs. Extracted metadata "
        "persisted in the database is encrypted at rest using Fernet symmetric encryption."
    )
    add_heading_2(doc, "5.3.4 Deterministic Discrepancy Detection Engine")
    add_body_paragraph(
        doc,
        "The Conflict Detection Engine operates 100% deterministically, executing independently of external network connectivity or large language model "
        "availability. The engine performs cross-document pairwise comparisons across all extracted demographic fields using the composite similarity "
        "metric S = 0.40 * S_jw + 0.30 * S_lev + 0.30 * S_ts. Discrepancies are categorized into High Severity (S < 0.70, indicating substantial "
        "structural mismatches that require formal gazette publication), Medium Severity (0.70 <= S < 0.95, representing initial expansions or clerical "
        "spelling variations resolvable via sworn affidavits), and Low Severity (0.95 <= S < 1.0, covering whitespace anomalies or casing differences)."
    )
    add_heading_2(doc, "5.3.5 Contextual RAG Knowledge Retrieval Subsystem")
    add_body_paragraph(
        doc,
        "The Statutory RAG Subsystem provides authoritative, hallucination-resistant procedural guidance. To achieve zero-cost, self-contained "
        "operation without external vector cloud dormancy risks, CONVELINA embeds an in-process Qdrant vector database running directly within the "
        "FastAPI runtime. On container cold start, the engine automatically indexes 25 official circular chunks and 6 downloadable government forms "
        "in under 200 milliseconds. When a citizen submits an inquiry, the query is converted into a 1024-dimensional dense vector representation and "
        "matched against statutory chunks using cosine distance. Crucially, the system enforces a strict similarity floor of 0.55: if retrieved "
        "chunks score below this threshold, generative synthesis is aborted, and the platform safely returns a deterministic fallback notification."
    )

    add_heading_1(doc, "5.4 Database and Data Model Design")
    add_body_paragraph(
        doc,
        "The data persistence layer is architected on PostgreSQL 16, a robust, enterprise-grade relational database management system. A relational "
        "model is uniquely suited for CONVELINA because identity credentials, demographic attributes, conflict records, and audit events possess "
        "strictly structured schemas, strong foreign key dependencies, and rigorous ACID transaction requirements."
    )
    add_heading_2(doc, "5.4.1 Relational Schema Specification")
    add_body_paragraph(
        doc,
        "The database schema comprises ten primary normalized relational entities, detailed in Table 5.1. Every entity holding user or document data "
        "incorporates a mandatory tenant_id foreign key linking the record directly to the authenticated user UUID."
    )

    tbl_headers = ["Table Name", "Primary Key", "Foreign Keys", "Core Attributes & Data Types", "Operational Purpose"]
    tbl_rows = [
        ("users", "id (UUID)", "None", "firebase_uid (VARCHAR), email (VARCHAR), role (VARCHAR), full_name (VARCHAR), created_at (TIMESTAMP)", "Manages user identity, authentication coordinates, and RBAC permissions."),
        ("documents", "id (UUID)", "tenant_id -> users(id)", "document_type (VARCHAR), extracted_fields (JSONB), storage_hash (VARCHAR), is_verified (BOOLEAN)", "Maintains encrypted demographic payloads and verification status per document."),
        ("conflicts", "id (UUID)", "tenant_id -> users(id), doc_a_id, doc_b_id", "field_name (VARCHAR), severity (VARCHAR), similarity_score (FLOAT), precedence_doc (VARCHAR)", "Stores pairwise demographic discrepancy evaluations, scores, and precedence."),
        ("correction_drafts", "id (UUID)", "tenant_id -> users(id), conflict_id", "template_type (VARCHAR), affidavit_text (TEXT), status (VARCHAR), created_at (TIMESTAMP)", "Stores synthesized legal affidavit texts, deed polls, and joint declarations."),
        ("signing_keys", "id (UUID)", "None", "key_id (VARCHAR), public_key_pem (TEXT), algorithm (VARCHAR), is_active (BOOLEAN), created_at (TIMESTAMP)", "Maintains the internal Certificate Authority public key registry for signature validation."),
        ("document_attestations", "id (UUID)", "tenant_id -> users(id), draft_id, key_id", "signature_bytes (BYTEA), document_sha256 (VARCHAR), verification_qr (TEXT)", "Records Ed25519 digital signatures and QR verification metadata for affidavits."),
        ("cases", "id (UUID)", "citizen_id, assigned_officer -> users(id)", "status (VARCHAR), priority (VARCHAR), resolution_notes (TEXT), created_at (TIMESTAMP)", "Manages verification officer review workflows, state transitions, and assignments."),
        ("case_evidence", "id (UUID)", "case_id -> cases(id), doc_id", "evidence_type (VARCHAR), remarks (TEXT), submitted_at (TIMESTAMP)", "Associates specific document artifacts and discrepancy records with active cases."),
        ("audit_log", "id (UUID)", "tenant_id -> users(id)", "action (VARCHAR), entity_id (UUID), current_hash (VARCHAR), prev_hash (VARCHAR), created_at (TIMESTAMP)", "Maintains an immutable, append-only, SHA-256 hash-chained audit ledger."),
        ("email_otps", "id (UUID)", "None", "email (VARCHAR), otp_hash (VARCHAR), attempts (INTEGER), expires_at (TIMESTAMP)", "Manages transient 6-digit email one-time passcodes with 5-minute expiry windows.")
    ]
    add_table_block(
        doc,
        "5.1",
        "Relational Database Schema Specification of the CONVELINA Platform",
        tbl_headers,
        tbl_rows,
        col_widths=[Inches(1.1), Inches(0.8), Inches(1.1), Inches(1.6), Inches(1.1)]
    )

    add_heading_2(doc, "5.4.2 Entity-Relationship (ER) Diagram")
    add_body_paragraph(
        doc,
        "Figure 5.2 presents the complete Entity-Relationship (ER) diagram illustrating the structural topology of the CONVELINA database. The diagram "
        "depicts primary keys, foreign key constraints, and relational cardinalities across all core tables, highlighting strict tenant containment."
    )

    fig_er = f"{assets_dir}/fig_5_2_er_diagram.png"
    add_figure_block(
        doc,
        fig_er,
        "5.2",
        "Entity-Relationship (ER) Diagram of CONVELINA Illustrating Relational Schema Entities, Primary/Foreign Keys, and Cardinalities"
    )

    add_heading_2(doc, "5.4.3 Database Security: Forced Row-Level Security and Dedicated Roles")
    add_body_paragraph(
        doc,
        "To guarantee absolute multi-tenant isolation, CONVELINA enforces PostgreSQL Row-Level Security (RLS) directly at the database engine level. "
        "Unlike conventional applications that rely on application-level WHERE clauses, CONVELINA activates ALTER TABLE ... ENABLE ROW LEVEL SECURITY "
        "and FORCE ROW LEVEL SECURITY across all application tables. Under forced RLS, table owners and superusers cannot accidentally bypass security "
        "policies during query execution."
    )
    add_body_paragraph(
        doc,
        "Runtime database connections are strictly restricted to a dedicated, unprivileged PostgreSQL role named consolith_app (configured with "
        "rolsuper=false). During each citizen session, FastAPI initializes transaction-local session settings: SET LOCAL app.current_tenant_id = '<uuid>'. "
        "To prevent connection-pooling failures when connection poolers (such as Supavisor or PgBouncer) reset connections with empty strings, session "
        "evaluations in RLS policies utilize safe NULLIF casting: NULLIF(current_setting('app.current_tenant_id', true), '')::uuid. Furthermore, an "
        "anti-escalation database trigger on the users table automatically aborts any attempt by non-administrators to alter their role."
    )

    add_heading_1(doc, "5.5 Cryptographic Attestation and Audit Subsystem")
    add_body_paragraph(
        doc,
        "The cryptographic attestation subsystem provides legal non-repudiation and evidentiary authenticity for all generated correction "
        "instruments, adhering to Section 63 of the Bharatiya Sakshya Adhiniyam 2023."
    )
    add_heading_2(doc, "5.5.1 Internal Ed25519 PKI Digital Signature Authority")
    add_body_paragraph(
        doc,
        "CONVELINA incorporates an internal Public Key Infrastructure (PKI) Certificate Authority engine utilizing Ed25519 elliptic-curve digital "
        "signatures (RFC 8032). When a pre-filled affidavit or deed poll is synthesized, the system serializes the canonical document payload "
        "according to RFC 8785 JSON canonicalization rules, computes its SHA-256 cryptographic digest, and signs the digest using the CA's active "
        "Ed25519 private key. The resulting 64-byte signature provides mathematical proof of document origin and integrity, verifying that the "
        "correction instrument was generated through CONVELINA's verified statutory pipeline without post-synthesis alteration."
    )
    add_heading_2(doc, "5.5.2 Verifiable QR Code Structure")
    add_body_paragraph(
        doc,
        "Every compiled correction document embeds a high-density, standardized QR code in its footer. The QR code encodes a structured JSON payload "
        "containing: the affidavit UUID, the resident's masked identifier, the conflicting document categories, the SHA-256 document hash, the "
        "signing key ID, the base64-encoded Ed25519 signature, and an offline verification URL. This enables gazetted verification officers, public "
        "notaries, and passport authorities to authenticate the physical or digital document instantaneously using any standard mobile camera or "
        "offline verification tool without requiring direct access to CONVELINA's internal database."
    )
    add_heading_2(doc, "5.5.3 Append-Only SHA-256 Hash-Chained Audit Ledger")
    add_body_paragraph(
        doc,
        "To provide tamper-evident record keeping, all system actions—document uploads, conflict evaluations, statutory queries, affidavit emissions, "
        "and officer reviews—are recorded in an append-only audit_log table. Immutability is enforced through a PostgreSQL statement-level trigger "
        "(block_audit_log_mutation) that unconditionally raises an exception and aborts any SQL UPDATE or DELETE command executed against the table."
    )
    add_body_paragraph(
        doc,
        "Furthermore, each audit record implements cryptographic hash chaining. When a new audit entry is inserted, a database trigger retrieves the "
        "cryptographic hash of the immediately preceding record (prev_hash) and computes the current record's hash: current_hash = SHA256(prev_hash + "
        "tenant_id + action + entity_id + created_at). This creates an unbroken, tamper-evident cryptographic blockchain within the relational database. "
        "Any attempt to retroactively modify an audit row or insert an unauthorized transaction invalidates the cryptographic hash chain, providing "
        "indisputable forensic evidence of database tampering."
    )

    add_heading_1(doc, "5.6 Deployment Architecture Design")
    add_body_paragraph(
        doc,
        "The deployment architecture of CONVELINA is designed for high reliability, strict network isolation, and minimal operational overhead. "
        "Figure 5.3 illustrates the containerized deployment topology, partitioned into three isolated tiers: the Client Tier, the Application Tier, "
        "and the Data and Security Tier."
    )
    add_body_paragraph(
        doc,
        "The Client Tier delivers the Next.js frontend across mobile and desktop browsers over HTTPS (TLS 1.3). The Application Tier runs a "
        "single-worker FastAPI container on Google Cloud Run (configured with 1 vCPU and 1 GB RAM under unprivileged user 'appuser' UID 10001). The "
        "container embeds the in-process Qdrant vector engine, Tesseract OCR 5.5.0, and the fuzzy conflict engine. Running a single worker with "
        "asynchronous I/O guarantees a 639 MB (62.4%) safety margin during 3-page PDF rasterization, completely eliminating Out-Of-Memory (OOM) crashes. "
        "The Data Tier connects via SSL to a PostgreSQL 16 cluster hosted on Supabase in Mumbai (ap-south-1), enforcing forced RLS and pooling safety."
    )

    fig_dep = f"{assets_dir}/fig_5_3_deployment.png"
    add_figure_block(
        doc,
        fig_dep,
        "5.3",
        "Proposed Containerized Cloud Run and Database Deployment Architecture of CONVELINA"
    )

    add_heading_1(doc, "5.7 Security and Privacy Trust Boundaries")
    add_body_paragraph(
        doc,
        "Figure 5.4 details the security architecture and privacy trust boundaries implemented across the CONVELINA platform. The system establishes "
        "two distinct trust barriers dividing the architecture into three zones: the Untrusted Zone (public internet, unauthenticated client browsers, "
        "and raw file uploads), the Secure Processing Zone (volatile memory buffers, magic byte validation, regex Aadhaar masking, and immediate file "
        "unlinking), and the Isolated Data Persistence Zone (non-superuser database roles, forced RLS tenant scoping, Fernet payload encryption, and "
        "immutable hash-chained audit ledgers). This architecture guarantees that even if a presentation-layer vulnerability occurs, sensitive "
        "demographic records remain cryptographically protected and physically isolated from lateral traversal."
    )

    fig_sec = f"{assets_dir}/fig_5_4_security.png"
    add_figure_block(
        doc,
        fig_sec,
        "5.4",
        "Security and Privacy Data-Flow Diagram Illustrating Trust Boundaries, Sanitization Filters, and Isolated Persistence Zones"
    )

    add_heading_1(doc, "5.8 Chapter Summary")
    add_body_paragraph(
        doc,
        "This chapter articulated the detailed architectural design of CONVELINA across its presentation, application, and persistence tiers. The "
        "editorial user interface design was presented, followed by the layout-aware OCR extraction pipeline, ephemeral memory purging, and the "
        "deterministic discrepancy engine. The in-process Qdrant vector database was detailed alongside the 0.55 similarity floor. The relational "
        "database schema was specified across ten normalized tables, supported by the complete Entity-Relationship diagram. Finally, PostgreSQL "
        "forced Row-Level Security, the Ed25519 PKI attestation engine, the append-only SHA-256 audit ledger, and the multi-tier deployment and security "
        "trust boundary architectures were formalized, establishing a comprehensive engineering blueprint for the system."
    )

    doc.add_page_break()
