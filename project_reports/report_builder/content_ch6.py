# -*- coding: utf-8 -*-
"""
Chapter 6: REQUIREMENTS, PLANNING, AND DESIGN CONSIDERATIONS generator
Includes Requirements Traceability Matrix (Table 6.1), Detailed Use Case Specs,
Statutory & Technical Standards, Risk Analysis Matrix (Table 6.2),
Gantt Chart Timeline (Fig 6.1), and Work Breakdown Structure (Table 6.3).
Written in cohesive, academic paragraphs with NO bullet points.
"""

from .styles import (
    add_chapter_title, add_heading_1, add_heading_2, add_heading_3,
    add_body_paragraph, add_figure_block, add_table_block
)
from docx.shared import Inches

def build_chapter_6(doc, assets_dir):
    add_chapter_title(doc, "6", "REQUIREMENTS, PLANNING, AND DESIGN CONSIDERATIONS")

    add_heading_1(doc, "6.1 Requirements Traceability Matrix")
    add_body_paragraph(
        doc,
        "Requirements traceability is an essential software engineering discipline that maps stakeholder needs and high-level project objectives "
        "directly to specific functional requirements, architectural subsystems, and validation criteria. Maintaining rigorous traceability ensures "
        "that every functional capability contributes directly to the project's foundational mission while confirming that no extraneous, ungrounded "
        "features are introduced into the system design."
    )
    add_body_paragraph(
        doc,
        "Table 6.1 presents the comprehensive Requirements Traceability Matrix established for CONVELINA. The matrix establishes bidirectional "
        "traceability linking high-level citizen and administrative needs to specific functional requirements (FR-01 through FR-12), architectural "
        "subsystems, and formal verification methodologies."
    )

    rtm_headers = ["Stakeholder Need", "Req. ID", "System Subsystem", "Design Mechanism", "Verification Method"]
    rtm_rows = [
        ("Demographic Privacy Compliance", "FR-03", "Ingestion & Redaction Module", "Automated regex masking of first 8 Aadhaar digits; ephemeral buffer wipe.", "Unit testing on synthetic 12-digit Aadhaar patterns; memory leak inspection."),
        ("Explainable Name Matching", "FR-06", "Conflict Detection Engine", "Hybrid scoring: 0.40 Jaro-Winkler + 0.30 Levenshtein + 0.30 Token Sort.", "Benchmarking against 500+ synthetic Indian name and initial expansion pairs."),
        ("Legal Precedence Arbitration", "FR-08", "Precedence Arbitration Matrix", "Deterministic rule matrix enforcing Class 10 certificate primacy for DOB.", "Logical edge-case testing against DoPT and MEA statutory rules."),
        ("Zero-Hallucination Guidance", "FR-09", "Statutory RAG Subsystem", "Qdrant vector search with hard 0.55 similarity floor; citation extraction.", "Adversarial querying with ungrounded legal topics; verifying refusal fallback."),
        ("Verifiable Correction Affidavits", "FR-10, 11", "Attestation & PKI CA Engine", "Standardized PDF synthesis; Ed25519 digital signature; verification QR code.", "Offline cryptographic signature verification via public key registry."),
        ("Multi-Tenant Isolation", "FR-01", "PostgreSQL Database Layer", "Forced Row-Level Security policies; non-superuser consolith_app role.", "Cross-tenant IDOR penetration tests attempting lateral document reads."),
        ("Tamper-Evident Audit Trails", "FR-12", "Audit Logging Subsystem", "PostgreSQL statement triggers blocking UPDATE/DELETE; SHA-256 chaining.", "Executing malicious mutation SQL queries; verifying transaction abort exceptions.")
    ]
    add_table_block(
        doc,
        "6.1",
        "Requirements Traceability Matrix of CONVELINA Mapping Stakeholder Needs to Architectural Components",
        rtm_headers,
        rtm_rows,
        col_widths=[Inches(1.3), Inches(0.7), Inches(1.2), Inches(1.6), Inches(1.2)]
    )

    add_heading_1(doc, "6.2 Detailed Use-Case Specifications")
    add_body_paragraph(
        doc,
        "To provide rigorous behavioral specifications for the use cases outlined in Chapter 4, the primary operational workflows are formalized into "
        "detailed use-case specifications describing actors, triggers, preconditions, main execution flows, and postconditions."
    )
    add_heading_2(doc, "6.2.1 Use Case UC-01: Document Upload and Ephemeral Ingestion")
    add_body_paragraph(
        doc,
        "Actor: Authenticated Citizen. Preconditions: Citizen is logged in with an active JWT session; document file is an image or PDF under 10 MB. "
        "Trigger: Citizen drops an identity document file onto the upload interface. Main Flow: (1) The frontend validates file size and MIME format. "
        "(2) FastAPI receives the file into volatile memory and verifies genuine magic bytes. (3) Tesseract OCR extracts text tokens and localized "
        "bounding boxes. (4) The parser isolates demographic entities. (5) Regex filters mask the first 8 digits of any detected Aadhaar number. "
        "(6) The raw image buffer is permanently purged from memory in a mandatory 'finally:' execution block. (7) Extracted fields are symmetrically "
        "encrypted with Fernet and saved to PostgreSQL under the citizen's tenant ID. Postconditions: Demographic metadata is securely persisted; raw "
        "scan files are zeroized with zero permanent disk footprint. Exception Flow: If the file is corrupted, malformed, or exceeds 10 MB, the system "
        "rejects the upload with an HTTP 400 error and displays a plain-language error notification."
    )
    add_heading_2(doc, "6.2.2 Use Case UC-02: Cross-Document Discrepancy Detection")
    add_body_paragraph(
        doc,
        "Actor: Authenticated Citizen. Preconditions: At least two identity documents are persisted in the citizen's private workspace. Trigger: Citizen "
        "clicks 'Run Cross-Document Comparison'. Main Flow: (1) The conflict engine queries all documents belonging to the citizen's tenant ID. "
        "(2) The engine executes pairwise string matching across common demographic attributes using the composite similarity metric. (3) Discrepancies "
        "are categorized into High, Medium, or Low severity. (4) Precedence rules identify the legally authoritative document for each conflict. "
        "(5) Inconsistencies are rendered on the citizen's dashboard with color-coded severity badges and mathematical similarity breakdowns. "
        "Postconditions: Conflict records are persisted in the conflicts table. Exception Flow: If extracted text contains severe OCR noise or "
        "unresolvable ambiguity, the field is flagged as 'Unresolvable — Needs Manual Review'."
    )
    add_heading_2(doc, "6.2.3 Use Case UC-03: Grounded Statutory RAG Consultation")
    add_body_paragraph(
        doc,
        "Actor: Authenticated Citizen. Preconditions: Detected discrepancies exist in the workspace. Trigger: Citizen submits a natural language question "
        "regarding correction procedures. Main Flow: (1) The assistant generates a 1024-dimensional dense vector embedding of the query and discrepancy "
        "context. (2) The system queries Qdrant for top matching statutory chunks. (3) The similarity score is checked against the 0.55 floor. (4) If "
        "the score meets or exceeds 0.55, the retrieved text is injected into a constrained prompt template. (5) The LLM generates procedural guidance "
        "incorporating exact circular titles, gazette dates, and form numbers. (6) Citations are validated before streaming the response to the user. "
        "Postconditions: The query and response are displayed in the chat interface. Exception Flow: If similarity is below 0.55 or the AI service is "
        "offline, the system displays: 'Assistant service is not currently available. Please try again later.'"
    )
    add_heading_2(doc, "6.2.4 Use Case UC-04: Automated Correction Affidavit Synthesis")
    add_body_paragraph(
        doc,
        "Actor: Authenticated Citizen. Preconditions: A confirmed discrepancy has been evaluated by the conflict engine. Trigger: Citizen clicks "
        "'Generate Rectification Affidavit'. Main Flow: (1) The system retrieves the citizen's verified demographic coordinates and the conflicting "
        "document records. (2) The template engine selects the appropriate legal declaration format (e.g., 'One and the Same Person' declaration). "
        "(3) The document is compiled into a standardized PDF containing official legal clauses, a formal draft disclaimer, and placeholder fields. "
        "(4) The PDF digest is signed using the system's Ed25519 private key. (5) A verification QR code is embedded in the document footer. "
        "(6) An immutable audit entry is appended to the audit ledger. Postconditions: The pre-filled PDF is rendered for instant download. Exception "
        "Flow: If unresolved template placeholders exist, document generation is blocked until required fields are completed."
    )

    add_heading_1(doc, "6.3 Design Constraints and Regulatory Standards Compliance")
    add_body_paragraph(
        doc,
        "To ensure that CONVELINA is legally defensible, ethically sound, and architecturally resilient, the Phase I design strictly adheres to "
        "established statutory public mandates and international cybersecurity standards."
    )
    add_heading_2(doc, "6.3.1 Statutory Standards: Aadhaar Act 2016 and Bharatiya Sakshya Adhiniyam 2023")
    add_body_paragraph(
        doc,
        "Section 29 of the Aadhaar Act 2016 strictly prohibits the long-term unauthorized storage or publication of core biometric and demographic "
        "identity numbers. CONVELINA operationalizes this statutory constraint through mandatory automated redaction of the initial eight digits of "
        "Aadhaar numbers and ephemeral unlinking of raw document scans. Symmetrically, Section 63 of the Bharatiya Sakshya Adhiniyam 2023 (which "
        "modernized and replaced Section 65B of the Indian Evidence Act 1872) governs the admissibility of electronic records in legal proceedings. "
        "By sealing all generated affidavits with Ed25519 asymmetric digital signatures and maintaining an unbroken, append-only SHA-256 hash-chained "
        "audit ledger, CONVELINA ensures that electronic rectification instruments satisfy strict statutory requirements for non-repudiation."
    )
    add_heading_2(doc, "6.3.2 Technical Standards: ISO/IEC 27001, OWASP API Top 10, and RFC 8785")
    add_body_paragraph(
        doc,
        "From an information security perspective, the architecture complies with ISO/IEC 27001 controls governing access control, cryptography, and "
        "operations security. The platform implements comprehensive defenses against the OWASP API Security Top 10 vulnerabilities: Broken Object Level "
        "Authorization (BOLA) is neutralized at the database engine level via forced PostgreSQL Row-Level Security; Injection attacks are eliminated "
        "through SQLAlchemy parameterized object-relational mapping; and Security Misconfiguration is prevented by strict production validators that "
        "fail closed on default secrets. Document signing enforces RFC 8785 JSON Canonicalization Scheme (JCS) to ensure deterministic cryptographic "
        "hashing across heterogeneous operating system architectures."
    )

    add_heading_1(doc, "6.4 Risk Analysis and Mitigation Strategies")
    add_body_paragraph(
        doc,
        "A comprehensive risk assessment was performed to anticipate potential technical, security, operational, and regulatory failure modes, "
        "formulating proactive architectural mitigations for each identified risk. Table 6.2 outlines the risk matrix established for CONVELINA."
    )

    risk_headers = ["Risk Domain", "Identified Risk Event", "Severity & Likelihood", "Architectural & Procedural Mitigation Strategy"]
    risk_rows = [
        ("Technical", "OCR mischaracterization on degraded or low-contrast identity cards.", "High Impact, Medium Likelihood", "Implement adaptive morphological thresholding; enforce confidence thresholds (>=80%); route low-confidence scans to human review."),
        ("Technical", "Out-of-memory (OOM) container crashes during multi-page PDF processing.", "High Impact, Low Likelihood", "Cap PDF rasterization at 3 pages maximum; set single-worker concurrency (WEB_CONCURRENCY=1) preserving 639 MB RAM headroom."),
        ("AI / RAG", "Large language model hallucination of non-existent gazette rules or fees.", "High Impact, Medium Likelihood", "Enforce strict 0.55 Qdrant cosine similarity floor; prepend verified circular text; require explicit citations; validate against source metadata."),
        ("Security", "Cross-tenant identity data traversal or privilege escalation attacks.", "Critical Impact, Low Likelihood", "Enable and FORCE Row-Level Security on all tables; connect via unprivileged role consolith_app; enforce database triggers on user roles."),
        ("Legal", "Citizen misinterpreting AI guidance as definitive government adjudication.", "High Impact, Low Likelihood", "Embed prominent statutory disclaimers on all UI cards and generated affidavits; state explicitly that platform is advisory and non-governmental."),
        ("Operational", "Audit trail tampering or retroactive modification of dispute logs.", "Critical Impact, Low Likelihood", "Enforce database triggers that unconditionally raise exceptions on UPDATE/DELETE; chain SHA-256 record hashes cryptographically.")
    ]
    add_table_block(
        doc,
        "6.2",
        "Comprehensive Risk Analysis, Impact Assessment, and Architectural Mitigation Strategies for CONVELINA",
        risk_headers,
        risk_rows,
        col_widths=[Inches(1.0), Inches(1.6), Inches(1.2), Inches(1.9)]
    )

    add_heading_1(doc, "6.5 Project Development Plan and Work Breakdown Structure")
    add_body_paragraph(
        doc,
        "The project development roadmap is structured across two distinct academic phases: Phase I (comprising foundational research, problem "
        "formulation, mathematical modeling, UML design, database architecture, and initial module validation) and Phase II (encompassing end-to-end "
        "pipeline implementation, multilingual OCR expansion, comprehensive testing, and final system submission). Figure 6.1 illustrates the "
        "project development timeline and Gantt chart spanning the six-month academic duration."
    )

    fig_time = f"{assets_dir}/fig_6_1_timeline.png"
    add_figure_block(
        doc,
        fig_time,
        "6.1",
        "CONVELINA Project Development Timeline and Work Breakdown Structure (WBS) Gantt Chart Spanning Phase I and Phase II"
    )

    add_body_paragraph(
        doc,
        "Table 6.3 articulates the detailed Work Breakdown Structure (WBS), delineating the specific work packages, tasks, and concrete deliverables "
        "associated with the successful completion of Phase I and the planned milestones for Phase II."
    )

    wbs_headers = ["Phase & Module", "Work Package Description", "Primary Engineering Tasks", "Status / Milestone Deliverable"]
    wbs_rows = [
        ("Phase I: Inception", "Problem Formulation & Literature Review", "Review 10 foundational papers; identify civic tech gaps; formalize aim and 9 objectives.", "COMPLETED: Chapters 1 and 2 delivered with zero-hallucination citations."),
        ("Phase I: Analysis", "System Analysis & Feasibility Study", "Analyze existing workflows; formulate functional (12) and non-functional (10) requirements.", "COMPLETED: Chapter 3 delivered with feasibility studies and requirements."),
        ("Phase I: Design", "UML Modeling & Algorithm Design", "Generate DFDs (0 & 1), UML models (Use Case, Class, Sequence, Collab, Activity); formalize algorithms.", "COMPLETED: Chapter 4 delivered with 6 UML models and 3 formal algorithms."),
        ("Phase I: Architecture", "Database & Security Architecture", "Design 10 relational tables, forced RLS policies, Ed25519 PKI CA engine, and audit ledger.", "COMPLETED: Chapter 5 delivered with ER diagram and deployment architecture."),
        ("Phase I: Planning", "Requirements Traceability & Risk Plan", "Formulate traceability matrix, risk mitigation strategies, and 6-month development schedule.", "COMPLETED: Chapter 6 delivered with formal matrices and Gantt schedule."),
        ("Phase II: Development", "End-to-End Pipeline Implementation", "Integrate Next.js App Router, FastAPI backend, Tesseract OCR, and in-process Qdrant.", "PLANNED: Complete codebase integration and containerized orchestration."),
        ("Phase II: Evaluation", "System Verification & Academic Report", "Execute multi-tenant penetration tests, empirical benchmarks, and final Phase II thesis.", "PLANNED: Comprehensive system validation and final project demonstration.")
    ]
    add_table_block(
        doc,
        "6.3",
        "Work Breakdown Structure (WBS) Matrix Delineating Phase I Completed Milestones and Phase II Implementation Roadmap",
        wbs_headers,
        wbs_rows,
        col_widths=[Inches(1.2), Inches(1.5), Inches(1.8), Inches(1.2)]
    )

    add_heading_1(doc, "6.6 Chapter Summary")
    add_body_paragraph(
        doc,
        "This chapter detailed the essential planning, requirements traceability, and design constraints governing CONVELINA. The Requirements "
        "Traceability Matrix mapped stakeholder needs to functional components, supported by detailed use-case specifications for core system "
        "operations. Mandatory statutory compliance with the Aadhaar Act 2016 and the Bharatiya Sakshya Adhiniyam 2023 was articulated alongside "
        "ISO/IEC 27001 and OWASP API security standards. A proactive risk analysis matrix evaluated technical, security, and legal failure modes, "
        "formulating robust architectural mitigations. Finally, the project development timeline and Work Breakdown Structure confirmed the successful "
        "completion of Phase I design deliverables and established a clear roadmap for Phase II full-scale implementation."
    )

    doc.add_page_break()

