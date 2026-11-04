# -*- coding: utf-8 -*-
"""
Chapter 4: METHODOLOGY AND SYSTEM DESIGN generator for CONVELINA Academic Report.
Includes DFDs (Level 0 and 1), UML Diagrams (Use Case, Class, Collaboration, Sequence, Activity),
Methodology Workflow, Mathematical Formulations, Algorithms, Pseudocode, and Module Decompositions.
Written in cohesive, academic paragraphs with NO bullet points.
"""

from .styles import (
    add_chapter_title, add_heading_1, add_heading_2, add_heading_3,
    add_body_paragraph, add_figure_block, add_table_block, add_algorithm_box
)
from docx.shared import Inches

def build_chapter_4(doc, assets_dir):
    add_chapter_title(doc, "4", "METHODOLOGY AND SYSTEM DESIGN")

    add_heading_1(doc, "4.1 Methodological Framework")
    add_body_paragraph(
        doc,
        "The engineering methodology adopted for CONVELINA follows a structured, five-stage sequential pipeline designed to transform "
        "unstructured, heterogeneous identity document scans into verified, cryptographically attested legal correction instruments. The "
        "methodological framework encompasses: (1) Secure Ingestion and Ephemeral PII Sanitization, (2) Layout-Aware Optical Character "
        "Recognition and Entity Parsing, (3) Multi-Algorithmic Fuzzy Conflict Detection and Precedence Arbitration, (4) Grounded Statutory "
        "Retrieval-Augmented Generation, and (5) Asymmetric Cryptographic Attestation and Hash-Chained Audit Logging. Each stage enforces "
        "strict data validation contracts, ensuring that processing failures, ambiguous optical inputs, or statutory uncertainties are "
        "safely trapped and routed to human review pathways rather than propagating erroneous assertions through the system."
    )

    add_heading_1(doc, "4.2 System Context and Trust Boundaries")
    add_body_paragraph(
        doc,
        "Establishing explicit trust boundaries is paramount when designing software systems that handle sensitive national identification "
        "records. CONVELINA defines three distinct architectural trust zones: the Untrusted Client Zone, the Secure Processing Zone, and the "
        "Isolated Data Persistence Zone. The Untrusted Client Zone encompasses public citizen web browsers, unauthenticated HTTP requests, and "
        "raw multipart file uploads. The Secure Processing Zone consists of the containerized FastAPI application runtime, where temporary file "
        "buffers are isolated in volatile memory, sanitized via MIME magic byte verification, and purged immediately following OCR feature extraction. "
        "The Isolated Data Persistence Zone comprises the PostgreSQL database cluster and the Qdrant vector database, protected behind database-level "
        "forced Row-Level Security (RLS) policies and network firewalls that deny public ingress."
    )

    add_heading_1(doc, "4.3 Data Flow Diagrams")
    add_body_paragraph(
        doc,
        "Data Flow Diagrams (DFDs) provide a hierarchical, process-centric representation of how information moves through CONVELINA, illustrating "
        "external entities, internal transformations, and data stores across varying levels of abstraction."
    )
    add_heading_2(doc, "4.3.1 Context-Level Data Flow Diagram (DFD Level 0)")
    add_body_paragraph(
        doc,
        "The Level 0 Data Flow Diagram, depicted in Figure 4.1, models CONVELINA as a single unified system and illustrates its primary boundary "
        "interactions with external entities and persistent data stores. The two principal external actors are the Citizen/Resident and the "
        "Verification Officer. The Citizen submits multi-format document scans and natural language discrepancy queries, receiving structured "
        "inconsistency reports and pre-filled correction affidavits. The Verification Officer submits administrative review requests and audit "
        "queries, receiving verification dossiers and tamper-evident attestation records. External data interactions are partitioned between Data "
        "Store D1 (Statutory Gazette & Circular Knowledge Base) and Data Store D2 (Tenant Documents, Conflict Records, and the Hash-Chained Audit Ledger)."
    )

    fig_dfd0 = f"{assets_dir}/fig_4_1_dfd_level_0.png"
    add_figure_block(
        doc,
        fig_dfd0,
        "4.1",
        "Level 0 Context Data Flow Diagram of CONVELINA Showing External Entities, Primary System Processes, and Core Data Stores"
    )

    add_heading_2(doc, "4.3.2 Functional Decomposition Data Flow Diagram (DFD Level 1)")
    add_body_paragraph(
        doc,
        "The Level 1 Data Flow Diagram, illustrated in Figure 4.2, decomposes the primary CONVELINA process into four interconnected sub-processes: "
        "Process 1.0 (Ingestion and Optical Character Recognition), Process 2.0 (Fuzzy Conflict Detection and Precedence Scoring), Process 3.0 "
        "(Statutory RAG Legal Guidance), and Process 4.0 (Ed25519 Cryptographic Signing and Audit Chaining). When an identity scan is uploaded, "
        "Process 1.0 validates the file format, extracts demographic entities, masks sensitive Aadhaar digits, encrypts the payload, and persists "
        "the record to Data Store D1 (Documents Store). Raw image bytes are purged from memory."
    )
    add_body_paragraph(
        doc,
        "Process 2.0 retrieves the cleaned demographic entities, executes cross-document pairwise comparisons, and stores detected discrepancies in "
        "Data Store D2 (Inconsistencies Store). When the citizen seeks resolution, Process 3.0 embeds the conflict description and queries Data Store "
        "D3 (Legal Knowledge Vector DB), retrieving verified statutory circulars and synthesizing a step-by-step resolution pathway. Finally, Process "
        "4.0 compiles the pre-filled legal affidavit, seals the document hash with an Ed25519 digital signature, and appends a cryptographically "
        "linked transaction record to Data Store D4 (Audit Log Ledger)."
    )

    fig_dfd1 = f"{assets_dir}/fig_4_2_dfd.png"
    add_figure_block(
        doc,
        fig_dfd1,
        "4.2",
        "Level 1 Data Flow Diagram of CONVELINA Illustrating Internal Functional Processes, Intermediate Data Flows, and Data Stores"
    )

    add_heading_1(doc, "4.4 Unified Modeling Language (UML) Design Models")
    add_body_paragraph(
        doc,
        "To provide a comprehensive structural, behavioral, and architectural specification of CONVELINA, the system design incorporates six formal "
        "Unified Modeling Language (UML) models capturing user roles, class hierarchies, object collaborations, execution sequences, operational "
        "activities, and overall project workflow."
    )

    add_heading_2(doc, "4.4.1 Use Case Diagram")
    add_body_paragraph(
        doc,
        "The Use Case Diagram, shown in Figure 4.3, formalizes the system boundary and defines the interactions between supported user personas and "
        "system capabilities. The platform supports three primary actors: the Citizen/Resident, the Verification Officer, and the System Administrator, "
        "alongside the backend CONVELINA Core AI / Certificate Authority system actor."
    )
    add_body_paragraph(
        doc,
        "The Citizen actor initiates use cases including Upload and Mask Identity Documents, Detect Clerical Inconsistencies, Consult Statutory "
        "RAG Assistant, and Generate Rectification Affidavit. The Verification Officer engages with Review and Audit Discrepancies, Issue Ed25519 "
        "PKI Attestations, and Verify Tamper-Evident Logs. The Administrator oversees user account provisioning, signing key rotation, and system "
        "telemetry monitoring. Core AI and CA services provide automated backend support for OCR parsing, vector retrieval, and cryptographic signing."
    )

    fig_uc = f"{assets_dir}/fig_4_4_usecase.png"
    add_figure_block(
        doc,
        fig_uc,
        "4.3",
        "Use Case Diagram of CONVELINA Defining Functional Boundaries and Persona Interactions for Citizens, Officers, and Administrators"
    )

    add_heading_2(doc, "4.4.2 System Class Diagram")
    add_body_paragraph(
        doc,
        "The System Class Diagram, depicted in Figure 4.4, models the object-oriented structure of CONVELINA, illustrating core abstractions, their "
        "encapsulated attributes, primary operations, and inter-class relationships. The architecture comprises six central classes: "
        "DocumentIngestionManager, ConflictDetectionEngine, RAGStatutoryAssistant, SecurityPolicyEnforcer, AffidavitGenerator, and PKIAttestationEngine."
    )
    add_body_paragraph(
        doc,
        "The DocumentIngestionManager encapsulates methods for MIME validation, OCR extraction, Aadhaar redaction, and Fernet encryption. It invokes "
        "the ConflictDetectionEngine, which encapsulates string similarity algorithms, precedence classification, and unresolvable conflict handling. "
        "The SecurityPolicyEnforcer interfaces directly with PostgreSQL session contexts, ensuring that tenant scoping and role-based policies "
        "are enforced prior to any database read or write operation. The AffidavitGenerator interfaces with the PKIAttestationEngine, which signs "
        "document digests using Ed25519 private keys and appends immutable records to the hash-chained audit ledger."
    )

    fig_class = f"{assets_dir}/fig_4_3_class.png"
    add_figure_block(
        doc,
        fig_class,
        "4.4",
        "System Class Diagram of CONVELINA Encapsulating Primary Object Abstractions, Encapsulated Attributes, Methods, and Associations"
    )

    add_heading_2(doc, "4.4.3 Collaboration Diagram")
    add_body_paragraph(
        doc,
        "The Object Collaboration Diagram, presented in Figure 4.5, illustrates the structural messaging paths and object-oriented dispatch sequence "
        "during an active conflict resolution session. When a citizen interacts with the ClientApp interface, the client dispatches document payloads "
        "to the FastAPIGateway. The gateway coordinates with the SecurityPolicyEnforcer to initialize the PostgreSQL RLS context, invokes the "
        "ConflictEngine for multi-algorithmic comparison, routes semantic queries to the RAGVectorEngine for statutory clause retrieval, and triggers "
        "the PKISigningCA to generate verifiable Ed25519 attestations and append audit entries."
    )

    fig_collab = f"{assets_dir}/fig_4_5_collaboration.png"
    add_figure_block(
        doc,
        fig_collab,
        "4.5",
        "Object Collaboration Diagram Illustrating Inter-Component Messaging Paths During End-to-End Conflict Resolution"
    )

    add_heading_2(doc, "4.4.4 Sequence Diagram")
    add_body_paragraph(
        doc,
        "The Sequence Diagram, illustrated in Figure 4.6, delineates the exact chronological timeline of method invocations and asynchronous "
        "operations during a complete citizen session. The execution begins when the citizen uploads identity scans via the frontend user interface. "
        "The frontend dispatches an authenticated multipart POST request to the FastAPI application layer with a Bearer JWT token."
    )
    add_body_paragraph(
        doc,
        "Upon receiving the request, FastAPI immediately executes a transaction-local session command against PostgreSQL: SET LOCAL app.current_tenant_id "
        "equaling the authenticated citizen UUID, establishing a strict RLS boundary. The OCR pipeline extracts demographic attributes, executes "
        "Aadhaar masking, and stores the encrypted payload. The conflict engine executes pairwise fuzzy comparison and returns discrepancy scores. "
        "The citizen queries the RAG engine, which searches Qdrant using dense vector embeddings, enforces the 0.55 similarity floor, and returns "
        "grounded correction steps. Upon user confirmation, the system compiles the PDF affidavit, signs its SHA-256 digest with Ed25519, appends an "
        "immutable record to the audit ledger, and returns the pre-filled, signed document to the citizen workspace."
    )

    fig_seq = f"{assets_dir}/fig_4_6_sequence.png"
    add_figure_block(
        doc,
        fig_seq,
        "4.6",
        "Sequence Diagram of CONVELINA Depicting the Chronological Method Execution Sequence from Ingestion to Attestation"
    )

    add_heading_2(doc, "4.4.5 Activity Diagram")
    add_body_paragraph(
        doc,
        "The Activity Diagram, shown in Figure 4.7, maps the procedural workflow, branching logic, and decision criteria governing system execution. "
        "Following document upload and OCR extraction, the system performs an automated quality check on optical extraction confidence. If extraction "
        "confidence falls below 80% or characters exhibit ambiguous native script transliteration, the system branches to a fail-safe exception handler, "
        "marking the record as 'Unresolvable — Needs Manual Review' and notifying the citizen to provide a clearer scan."
    )
    add_body_paragraph(
        doc,
        "If extraction confidence satisfies the quality threshold, the workflow transitions to cross-document comparison. If no inconsistencies are "
        "detected across demographic fields, the documents are marked verified and no further action is required. If discrepancies are detected, the "
        "system executes legal precedence arbitration, queries the statutory knowledge base via RAG, synthesizes the pre-filled correction affidavit, "
        "generates an Ed25519 cryptographic seal, and appends a tamper-evident audit record before concluding the process."
    )

    fig_act = f"{assets_dir}/fig_4_7_activity.png"
    add_figure_block(
        doc,
        fig_act,
        "4.7",
        "Activity Diagram of CONVELINA Mapping Procedural Workflows, Confidence Gate Decision Logic, and Manual Review Exception Paths"
    )

    add_heading_2(doc, "4.4.6 Project Methodology Workflow")
    add_body_paragraph(
        doc,
        "The complete end-to-end operational pipeline of CONVELINA is synthesized in Figure 4.8. The methodology workflow illustrates the progression "
        "of citizen identity artifacts across the five core engineering phases: Phase 1 Secure Ingestion, Phase 2 Hybrid OCR Extraction, Phase 3 Fuzzy "
        "Conflict Engine, Phase 4 Statutory RAG Guidance, and Phase 5 Attestation and Audit. This modular progression ensures that each stage performs "
        "a distinct transformation while maintaining absolute data integrity and verifiable auditability throughout."
    )

    fig_meth = f"{assets_dir}/fig_4_8_methodology.png"
    add_figure_block(
        doc,
        fig_meth,
        "4.8",
        "Project Methodology Workflow Across the Five Core Pipeline Stages of the CONVELINA Platform"
    )

    add_heading_1(doc, "4.5 Algorithms and Mathematical Formulations")
    add_body_paragraph(
        doc,
        "The algorithmic foundation of CONVELINA operationalizes multi-algorithmic fuzzy string matching, legal precedence arbitration, and dense "
        "vector semantic retrieval into rigorous mathematical formulations and deterministic execution logic."
    )

    add_heading_2(doc, "4.5.1 Multi-Algorithmic Identity Matching and Similarity Scoring")
    add_body_paragraph(
        doc,
        "To reliably evaluate variations in Indian personal names, father's names, and demographic attributes without misinterpreting clerical "
        "variations as deliberate fraud, CONVELINA implements a composite similarity metric combining three complementary algorithms: Jaro-Winkler "
        "similarity (S_jw), Levenshtein distance ratio (S_lev), and Token Sort ratio (S_ts)."
    )
    add_body_paragraph(
        doc,
        "The Jaro similarity metric measures the proportion of common matching characters within a half-length matching window and counts character "
        "transpositions. Winkler's extension incorporates an additive prefix weighting factor: S_jw = S_jaro + (l * p * (1 - S_jaro)), where l "
        "denotes the length of the common initial prefix (up to a maximum of 4 characters) and p represents a standard scaling constant set to 0.1. "
        "Jaro-Winkler excels at identifying shared root prefixes in Indian names."
    )
    add_body_paragraph(
        doc,
        "The Levenshtein similarity ratio evaluates the minimum number of single-character insertions, deletions, and substitutions required to "
        "transform sequence s1 into s2: S_lev = 1 - (LevenshteinDistance(s1, s2) / max(len(s1), len(s2))). This metric quantifies typographical "
        "substitutions and character dropouts."
    )
    add_body_paragraph(
        doc,
        "The Token Sort ratio tokenizes the string into individual words, converts all characters to lowercase, eliminates punctuation, sorts the "
        "tokens alphabetically, and computes the sequence similarity between the reconstructed token strings: S_ts = TokenSort(s1, s2). This heuristic "
        "effectively accommodates Indian naming conventions where honorific titles, surnames, and given names appear in inverted order (e.g., 'RAMAN "
        "VIKRAM' versus 'VIKRAM RAMAN')."
    )
    add_body_paragraph(
        doc,
        "The composite similarity score S is formulated as a normalized linear weighted combination: S = 0.40 * S_jw + 0.30 * S_lev + 0.30 * S_ts. "
        "Table 4.1 outlines the algorithmic metrics, their operational weights, and their specific detection strengths."
    )

    sim_headers = ["Similarity Metric", "Mathematical Formulation", "Assigned Weight", "Primary Detection Strength"]
    sim_rows = [
        ("Jaro-Winkler (S_jw)", "S_jaro + (l * p * (1 - S_jaro))", "0.40", "Prefix-aligned variations, patronymic initials, and root name expansions."),
        ("Levenshtein Ratio (S_lev)", "1 - (LevDistance / max_length)", "0.30", "Single-character typographical substitutions and clerical character dropouts."),
        ("Token Sort Ratio (S_ts)", "FuzzyMatch(SortedTokens(s1), SortedTokens(s2))", "0.30", "Word order permutations, surname-given name inversions, and multi-word names.")
    ]
    add_table_block(
        doc,
        "4.1",
        "Multi-Algorithmic String Similarity Metrics, Formulations, and Weight Distribution in CONVELINA",
        sim_headers,
        sim_rows,
        col_widths=[Inches(1.4), Inches(2.0), Inches(0.9), Inches(1.4)]
    )

    add_body_paragraph(
        doc,
        "Algorithm 4.1 formalizes the multi-algorithmic identity matching and precedence scoring procedure implemented in CONVELINA."
    )

    alg1_steps = [
        "Initialize discrepancy list C = [] and normalized attribute dictionary.",
        "For each common demographic field f in {Full_Name, DOB, Father_Name, Gender} do:",
        "    val_A = Normalize_String(Doc_A[f]); val_B = Normalize_String(Doc_B[f])",
        "    If f == 'DOB' then:",
        "        date_A = Parse_ISO_Date(val_A); date_B = Parse_ISO_Date(val_B)",
        "        If date_A != date_B then:",
        "            precedence = Arbitrate_Precedence(Doc_A, Doc_B, 'DOB')",
        "            Append {field: 'DOB', val_a: val_A, val_b: val_B, score: 0.0, severity: 'HIGH', precedence: precedence} to C",
        "    Else if f in {'Full_Name', 'Father_Name'} then:",
        "        score_jw = Compute_Jaro_Winkler(val_A, val_B)",
        "        score_lev = Compute_Levenshtein_Ratio(val_A, val_B)",
        "        score_ts = Compute_Token_Sort_Ratio(val_A, val_B)",
        "        composite_S = (0.40 * score_jw) + (0.30 * score_lev) + (0.30 * score_ts)",
        "        If composite_S < 0.70 then: severity = 'HIGH' (Formal Gazette Notification Required)",
        "        Else if 0.70 <= composite_S < 0.95 then: severity = 'MEDIUM' (Clerical Initial Expansion / Affidavit Valid)",
        "        Else if 0.95 <= composite_S < 1.0 then: severity = 'LOW' (Minor Whitespace / Formatting Variation)",
        "        If composite_S < 1.0 then:",
        "            precedence = Arbitrate_Precedence(Doc_A, Doc_B, f)",
        "            Append {field: f, val_a: val_A, val_b: val_B, score: composite_S, severity: severity, precedence: precedence} to C",
        "Return discrepancy list C."
    ]
    add_algorithm_box(
        doc,
        "4.1",
        "Cross-Document Multi-Algorithmic Identity Matching and Severity Classification",
        "Extracted demographic dictionaries Doc_A, Doc_B across supported identity documents.",
        "Discrepancy list C containing similarity scores, severity classifications, and precedence verdicts.",
        alg1_steps
    )

    add_heading_2(doc, "4.5.2 Statutory Legal Precedence Arbitration")
    add_body_paragraph(
        doc,
        "In administrative law, conflicting documents cannot be arbitrated by arbitrary majority voting or simple chronological creation order. "
        "Instead, Indian public administration enforces rigid statutory hierarchies depending on the specific demographic attribute in dispute. "
        "CONVELINA codifies these legal rules into a deterministic Statutory Legal Precedence Arbitration Matrix, formalized in Table 4.2."
    )

    prec_headers = ["Demographic Field", "Statutory Primary Document", "Subordinate Documents", "Governing Statutory Authority / Administrative Rule"]
    prec_rows = [
        ("Date of Birth (DOB)", "Class 10 Matriculation Certificate / Municipal Birth Certificate", "Aadhaar Card, PAN Card, Voter ID, Passport", "Department of Personnel & Training (DoPT) Office Memorandum; MEA Passport Rules 2016."),
        ("Full Legal Name (Substantial Change)", "Official Gazette of India Notification", "All secondary identity credentials", "Ministry of Home Affairs Gazette Notification Guidelines; UIDAI Name Change Circular 2021."),
        ("Full Legal Name (Initial Expansion)", "Class 10 Certificate / Indian Passport", "Aadhaar Card, PAN Card (Form 49A)", "NSDL Income Tax PAN Allotment Guidelines; Annexure-E Passport Seva Joint Declaration."),
        ("Father's Name", "Class 10 Marks Card / Birth Certificate", "Aadhaar Card, EPFO Member Record", "Central Board of Secondary Education Bye-laws; EPFO Joint Declaration Operating Procedure 2023.")
    ]
    add_table_block(
        doc,
        "4.2",
        "Statutory Legal Precedence Arbitration Matrix Governing Cross-Document Identity Inconsistencies",
        prec_headers,
        prec_rows,
        col_widths=[Inches(1.2), Inches(1.6), Inches(1.3), Inches(1.6)]
    )

    add_heading_2(doc, "4.5.3 Grounded RAG Retrieval with Similarity Floor Validation")
    add_body_paragraph(
        doc,
        "To prevent large language models from hallucinating procedural rules, CONVELINA implements an authoritative Retrieval-Augmented Generation "
        "algorithm. When a citizen submits a discrepancy query or requests procedural rectification advice, the query text q is embedded into a dense "
        "1024-dimensional vector v_q. The system executes an approximate nearest neighbor search across the Qdrant vector database indexing verified "
        "statutory circulars, computing cosine similarity: CosineSim(v_q, v_d) = (v_q . v_d) / (||v_q|| * ||v_d||)."
    )
    add_body_paragraph(
        doc,
        "Crucially, the system enforces a strict similarity floor: Threshold_Floor = 0.55. If the maximum similarity score among retrieved chunks falls "
        "below 0.55, the algorithm automatically aborts generative synthesis and returns a safe, deterministic fallback message: 'Assistant service is "
        "not currently available. Please try again later.' If retrieved chunks exceed the floor, they are prepended as strict grounding context to a "
        "constrained LLM prompt, mandating exact statutory citations and prohibiting speculative legal advice. Algorithm 4.2 formalizes this procedure."
    )

    alg2_steps = [
        "Receive user query string q and detected discrepancy context C.",
        "Compute dense vector embedding: v_q = Embed_Query(q + ' ' + C.field + ' ' + C.severity).",
        "Query Qdrant statutory knowledge index using HNSW cosine distance: results = Qdrant_Search(collection='statutory_knowledge', vector=v_q, limit=3).",
        "Extract top chunk c_top and evaluate similarity score: score_sim = results[0].score.",
        "If score_sim < 0.55 then:",
        "    Log audit event: RAG_RETRIEVAL_BELOW_FLOOR with score_sim.",
        "    Return safe response: 'Assistant service is not currently available. Please try again later. (Context below confidence floor)'.",
        "Else:",
        "    Construct constrained grounding prompt incorporating c_top.text, statutory circular title, and official gazette date.",
        "    Enforce prompt constraints: 'Cite exact circular numbers. Prohibit speculative procedural claims. Do not claim universal legal validity.'",
        "    Synthesize grounded procedural guidance: response_text = LLM_Generate(prompt).",
        "    Validate citation references in response_text against retrieved chunk metadata.",
        "    Return {guidance: response_text, citations: c_top.citations, confidence: score_sim}."
    ]
    add_algorithm_box(
        doc,
        "4.2",
        "Grounded Statutory RAG Retrieval with Similarity Floor Enforcement",
        "Citizen query string q, discrepancy record C, and Qdrant statutory vector index.",
        "Statutorily grounded procedural guidance with verifiable citations or safe fallback refusal.",
        alg2_steps
    )

    add_heading_2(doc, "4.5.4 End-to-End Pipeline Execution Pseudocode")
    add_body_paragraph(
        doc,
        "The end-to-end execution of the complete CONVELINA processing pipeline—from unauthenticated file upload through RLS session scoping, OCR "
        "parsing, conflict evaluation, RAG guidance, affidavit generation, and Ed25519 cryptographic attestation—is formalized in Algorithm 4.3."
    )

    alg3_steps = [
        "BEGIN CONVELINA_PIPELINE(citizen_token, uploaded_files):",
        "    resident_id, user_role = Validate_JWT_Token(citizen_token)",
        "    db_conn = Acquire_Database_Connection(role='consolith_app')",
        "    EXECUTE db_conn: SET LOCAL app.current_tenant_id = resident_id;",
        "    EXECUTE db_conn: SET LOCAL app.current_user_role = user_role;",
        "    extracted_docs = []",
        "    FOR EACH file IN uploaded_files DO:",
        "        raw_bytes = Read_Transient_Bytes(file)",
        "        Validate_MIME_Magic_Bytes(raw_bytes)  # Enforce PDF/PNG/JPEG",
        "        doc_type = Classify_Document_Type(raw_bytes)",
        "        raw_text = Execute_Tesseract_OCR(raw_bytes, doc_type)",
        "        Purge_Memory_Buffer(raw_bytes)  # Immediate ephemeral wipe",
        "        masked_entities = Mask_Aadhaar_First_Eight(Parse_Entities(raw_text, doc_type))",
        "        encrypted_payload = Fernet_Encrypt(masked_entities)",
        "        doc_id = db_conn.INSERT_DOCUMENT(tenant_id=resident_id, doc_type=doc_type, payload=encrypted_payload)",
        "        Append {id: doc_id, entities: masked_entities, type: doc_type} to extracted_docs",
        "    END FOR",
        "    conflicts = Run_Cross_Document_Comparison(extracted_docs)",
        "    IF conflicts IS NOT EMPTY THEN:",
        "        FOR EACH c IN conflicts DO:",
        "            statutes = Execute_RAG_Search(c, floor=0.55)",
        "            guidance = Synthesize_Grounded_Steps(c, statutes)",
        "            affidavit_pdf = Generate_PreFilled_Affidavit(resident_id, c, guidance)",
        "            sig_bytes = Ed25519_Sign(Private_Key, SHA256(affidavit_pdf))",
        "            qr_seal = Generate_QR_Code(affidavit_id, SHA256(affidavit_pdf), sig_bytes)",
        "            db_conn.APPEND_AUDIT_LOG(tenant_id=resident_id, action='ATTESTATION_ISSUED', hash=SHA256(sig_bytes))",
        "        END FOR",
        "    END IF",
        "    db_conn.Commit() and Release_Connection()",
        "    Return {status: 'SUCCESS', extracted: extracted_docs, conflicts: conflicts, affidavits: generated_affidavits}",
        "END CONVELINA_PIPELINE"
    ]
    add_algorithm_box(
        doc,
        "4.3",
        "End-to-End CONVELINA Ingestion, Conflict Detection, and Attestation Pipeline",
        "Citizen authentication token, uploaded document scan files.",
        "Structured demographic records, discrepancy evaluations, grounded guidance, and digitally signed affidavits.",
        alg3_steps
    )

    add_heading_1(doc, "4.6 Module Decomposition Description")
    add_body_paragraph(
        doc,
        "CONVELINA is engineered with a modular monolith architectural philosophy, dividing core responsibilities into six cohesive, loosely "
        "coupled modules that communicate over strictly typed interface contracts."
    )
    add_heading_2(doc, "4.6.1 Module 1: Document Ingestion and Entity Masking")
    add_body_paragraph(
        doc,
        "The Ingestion Module provides secure HTTP multipart upload endpoints supporting PDF, JPEG, and PNG formats up to 10 MB. Upon receipt, the "
        "module inspects file headers to verify genuine MIME magic bytes, rejecting masqueraded executables. Files are streamed directly into "
        "transient RAM buffers without writing unencrypted temporary files to shared storage volumes. In strict compliance with Section 29 of the "
        "Aadhaar Act 2016, the module regex-identifies 12-digit Aadhaar sequences and immediately overwrites the first eight digits with masking "
        "characters (e.g., 'XXXX-XXXX-4041'). Raw image buffers are zeroized immediately following OCR processing."
    )
    add_heading_2(doc, "4.6.2 Module 2: OCR Parsing and Demographic Extraction")
    add_body_paragraph(
        doc,
        "This module integrates Tesseract 5.5.0 and Poppler utility libraries with customized layout heuristics tailored for Indian identity cards. "
        "The parser handles four major document typologies: Aadhaar (extracting resident name, C/O guardian name, gender, and DOB/YOB), PAN cards "
        "(extracting the 10-character alphanumeric identifier, holder name, father's name, and DOB), Indian Passports (decoding the two-line Machine "
        "Readable Zone according to ICAO Doc 9303 standards), and Educational Marksheets (isolating candidate, parental, and birth records)."
    )
    add_heading_2(doc, "4.6.3 Module 3: Conflict Detection and Precedence Engine")
    add_body_paragraph(
        doc,
        "The Conflict Detection Engine executes pairwise cross-document evaluations across corresponding demographic fields. It integrates the "
        "composite similarity metric (Jaro-Winkler, Levenshtein, and Token Sort) to classify discrepancies into High, Medium, and Low severity tiers. "
        "Crucially, the module applies statutory legal precedence rules, identifying which document serves as the legal benchmark for resolving each "
        "specific conflict, such as enforcing the legal supremacy of Class 10 certificates over secondary records for date of birth disputes."
    )
    add_heading_2(doc, "4.6.4 Module 4: Statutory RAG Knowledge Base and Assistant")
    add_body_paragraph(
        doc,
        "The Statutory RAG Assistant constitutes the legal reasoning core of the platform. Interfacing with an in-process Qdrant vector database "
        "indexing official gazettes, UIDAI circulars, NSDL instructions, and Passport Seva rules, the module converts citizen queries into dense "
        "vector representations. It enforces the strict 0.55 similarity floor: if retrieved contexts fall below this threshold, the assistant safely "
        "declines to speculate and flags the issue for human verification, eliminating AI hallucinations in legal guidance."
    )
    add_heading_2(doc, "4.6.5 Module 5: Correction Document and Affidavit Generator")
    add_body_paragraph(
        doc,
        "Once a discrepancy resolution path is established, this module synthesizes legally standardized correction instruments. Populating official "
        "templates, it generates bilingual sworn 'One and the Same Person' affidavits, MEA Annexure-E deed polls, and EPFO Joint Declarations. Each "
        "document embeds a high-density verification QR code containing document SHA-256 digests and cryptographic signature metadata."
    )
    add_heading_2(doc, "4.6.6 Module 6: Officer Verification and Tamper Audit Module")
    add_body_paragraph(
        doc,
        "The Verification and Audit Module provides administrative oversight for government verification officers. Officers can inspect discrepancy "
        "dossiers, examine side-by-side OCR diffs, and validate digital attestations. All system operations—uploads, conflict evaluations, queries, and "
        "attestations—are recorded in an append-only audit_log table. Database triggers completely block UPDATE and DELETE queries, while each record's "
        "SHA-256 hash chains cryptographically to the preceding entry, providing immutable auditability under the Bharatiya Sakshya Adhiniyam 2023."
    )

    add_heading_1(doc, "4.7 Chapter Summary")
    add_body_paragraph(
        doc,
        "This chapter formulated the complete methodology and system design for CONVELINA. The system context and three-tier trust boundaries were "
        "defined, followed by detailed Level 0 and Level 1 Data Flow Diagrams. Six comprehensive UML design models articulated user roles, class "
        "structures, messaging collaborations, chronological execution sequences, and decision activity workflows. Mathematical formulations for "
        "hybrid fuzzy matching, legal precedence arbitration, and dense vector retrieval were formalized into three core algorithms and complete "
        "pipeline execution pseudocode. Finally, the modular decomposition of the platform into six cohesive functional modules was established, "
        "providing the theoretical and structural foundation for the detailed system architecture presented in Chapter 5."
    )

    doc.add_page_break()

