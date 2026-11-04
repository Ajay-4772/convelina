# -*- coding: utf-8 -*-
"""
Chapter 1: INTRODUCTION generator for CONVELINA Academic Report.
Written in cohesive, academic paragraphs with NO bullet points.
"""

from .styles import (
    add_chapter_title, add_heading_1, add_heading_2, add_heading_3,
    add_body_paragraph, add_figure_block
)

def build_chapter_1(doc, assets_dir):
    add_chapter_title(doc, "1", "INTRODUCTION")

    add_heading_1(doc, "1.1 Overview of the Project")
    add_body_paragraph(
        doc,
        "In the contemporary landscape of public digital governance, sovereign foundational identification "
        "systems constitute the essential infrastructure through which citizens exercise civil rights, access welfare "
        "entitlements, participate in modern financial markets, and engage in international employment and education. "
        "Within the Republic of India, the rapid rollout of national digital identification platforms over the past two "
        "decades has produced a multifaceted identity ecosystem. Foundational registries such as Aadhaar, administered "
        "by the Unique Identification Authority of India (UIDAI), serve as ubiquitous proof of residence and biometric "
        "de-duplication. Simultaneously, functional identity registries established under distinct administrative mandates, "
        "such as the Permanent Account Number (PAN) issued by the Income Tax Department, the Indian Passport issued by "
        "the Ministry of External Affairs (MEA), the Universal Account Number (UAN) governed by the Employees' Provident "
        "Fund Organisation (EPFO), and secondary education certificates issued by the Central Board of Secondary "
        "Education (CBSE) and State Examination Boards, form the legal bedrock of civic identification."
    )
    add_body_paragraph(
        doc,
        "While each individual statutory registry has succeeded in establishing substantial coverage within its respective "
        "administrative domain, these systems were instituted asynchronously across several decades. Consequently, each "
        "department adopted independent data entry protocols, unique schema constraints, disparate transliteration schemes, "
        "and idiosyncratic naming conventions. This structural divergence has produced a pervasive systemic challenge: "
        "millions of Indian citizens possess subtle, clerical discrepancies across their foundational identity documents. "
        "A citizen may be registered under an abbreviated patronymic initial on their school certificate and Aadhaar card, "
        "while their PAN card mandates the expansion of all initials into full alphabetic surnames. Similarly, slight "
        "transliteration variations between Indic scripts and the Latin alphabet, inverted date of birth formats, and "
        "typographical errors introduced during historical manual transcription create widespread incompatibilities."
    )
    add_body_paragraph(
        doc,
        "The project, CONVELINA: An AI-Powered Identity Document Conflict Detection and Government Correction Assistance "
        "System Using LLMs and RAG, proposes an autonomous, intelligent, and secure technological solution designed to "
        "reconcile cross-document demographic inconsistencies. The platform ingests heterogeneous document scans, enforces "
        "rigorous statutory data minimization and demographic privacy safeguards, performs multi-algorithmic fuzzy entity "
        "matching across corresponding demographic fields, arbitrates legal precedence in accordance with official Indian "
        "administrative jurisprudence, provides grounded procedural guidance through a Retrieval-Augmented Generation "
        "assistant, and synthesizes cryptographically attested sworn affidavits to streamline formal statutory correction."
    )

    add_heading_1(doc, "1.2 Problem Definition")
    add_body_paragraph(
        doc,
        "The fundamental problem addressed by this project is the lack of an accessible, automated, and legally grounded "
        "mechanism for Indian citizens to detect, interpret, and resolve clerical discrepancies across their identity "
        "documents before submitting high-stakes administrative applications. In contemporary practice, when an individual "
        "attempts to execute mandatory inter-registry linkages, such as seeding their Aadhaar number with their PAN card, "
        "applying for a passport renewal, or claiming accumulated retirement savings from EPFO, automated departmental "
        "gateways enforce rigid, binary string matching. Even minor clerical variances, such as an expanded father's initial "
        "or a swapped day and month in a birth date string, result in immediate, uninformative rejection."
    )
    add_body_paragraph(
        doc,
        "Citizens confronting these rejections face severe administrative friction. The official statutory procedures "
        "governing demographic corrections are dispersed across hundreds of administrative circulars, gazette notifications, "
        "and departmental office memorandums published by UIDAI, Protean (NSDL), UTIITSL, MEA Passport Seva, and EPFO. "
        "These guidelines are articulated in complex administrative and legal jargon, making it exceedingly difficult for the "
        "average citizen to determine whether their specific discrepancy constitutes a minor clerical variation resolvable "
        "through a simple self-declaration affidavit, or a substantial legal name change necessitating a formal notification "
        "in the Gazette of India."
    )
    add_body_paragraph(
        doc,
        "Due to procedural obscurity, vulnerable citizens and rural residents are systematically exploited by unregulated "
        "intermediaries, deed writers, and legal touts operating outside government offices. These intermediaries frequently "
        "charge exorbitant fees for drafting legally defective affidavits or incorrect application forms. Consequently, public "
        "verification officers at Passport Seva Kendras and EPFO regional offices report high rejection rates for submitted "
        "correction dossiers, exacerbating administrative backlogs and citizen distress. Furthermore, the conventional practice "
        "of transmitting unmasked, unencrypted physical and digital photocopies of identity records over insecure commercial "
        "channels exposes citizens to identity theft and violates mandatory provisions of the Aadhaar Act 2016."
    )

    add_heading_1(doc, "1.3 Motivation and Societal Imperative")
    add_body_paragraph(
        doc,
        "The motivation for CONVELINA arises directly from the intersection of social justice, administrative efficiency, "
        "and technological empowerment. In an increasingly digital society, an unrectified identity discrepancy is not a "
        "mere clerical inconvenience; it is a structural barrier that impedes economic survival and social mobility. When an "
        "elderly pensioner's date of birth in their EPF account diverges from their Aadhaar record by a single digit, their "
        "pension settlement is frozen. When a graduating student's name on their Class 10 marksheet differs from their passport "
        "application due to an expanded initial, their international scholarship or employment visa is indefinitely stalled."
    )
    add_body_paragraph(
        doc,
        "Democratizing access to legal and procedural guidance through explainable artificial intelligence provides an equitable "
        "remedy. By transitioning identity reconciliation from an opaque, intermediary-dominated ordeal into a transparent, "
        "autonomous digital experience, CONVELINA empowers citizens to understand the exact nature of their document conflicts, "
        "ascertain the applicable statutory precedents, and generate verifiable, legally compliant correction instruments at "
        "zero monetary cost. For public administrative bodies, the platform acts as an intelligent pre-submission filter that "
        "dramatically reduces the submission of defective petitions, alleviating administrative fatigue and preserving public "
        "resources for genuine dispute resolution."
    )

    add_heading_1(doc, "1.4 Aim of the Project")
    add_body_paragraph(
        doc,
        "The primary aim of this project is to research, design, and architect an enterprise-grade, privacy-first software "
        "platform, named CONVELINA, that autonomously detects cross-document demographic conflicts across diverse Indian identity "
        "records, determines legal precedence according to prevailing administrative regulations, provides grounded, "
        "hallucination-resistant procedural guidance using Retrieval-Augmented Generation, and synthesizes cryptographically "
        "sealed, standardized legal correction instruments to facilitate seamless civic reconciliation."
    )

    add_heading_1(doc, "1.5 Specific Objectives")
    add_body_paragraph(
        doc,
        "To achieve the overarching aim, the project is structured around nine specific, interdependent engineering and "
        "research objectives, executed in rigorous academic detail without reliance on ungrounded speculative assertions:"
    )
    add_body_paragraph(
        doc,
        "1. Architectural Modeling of Ingestion and Optical Character Recognition Pipeline: To formulate a robust layout-aware "
        "computer vision pipeline capable of ingesting diverse Indian identity document formats (Aadhaar, PAN, Passport, "
        "Educational Marksheets, and EPF records), extracting structured demographic key-value pairs while handling complex "
        "document backgrounds, security patterns, and regional typography."
    )
    add_body_paragraph(
        doc,
        "2. Mandatory Ephemeral Data Privacy and Demographic Masking: To enforce strict adherence to Section 29 of the Aadhaar "
        "Act 2016 by engineering regex-driven redaction algorithms that automatically mask the initial eight digits of all "
        "detected Aadhaar numbers, encrypt transient payloads with Fernet symmetric cryptography, and permanently unlink and "
        "purge raw document scan files from host memory immediately following feature extraction."
    )
    add_body_paragraph(
        doc,
        "3. Formulation of Multi-Algorithmic Fuzzy Conflict Detection Engine: To design a multi-tiered string comparison and "
        "entity alignment framework combining Jaro-Winkler prefix weighting, Levenshtein edit distance, and phonetic Token Sort "
        "heuristics to quantify character substitutions, patronymic initial expansions, and date inversions with mathematical "
        "transparency and explainable severity categorization."
    )
    add_body_paragraph(
        doc,
        "4. Statutory Legal Precedence Arbitration Formulation: To establish deterministic decision matrices grounded in Indian "
        "administrative jurisprudence that arbitrate hierarchical supremacy among conflicting documents, notably enforcing the "
        "legal primacy of Class 10 matriculation certificates for date of birth disputes and gazette notifications for legal name changes."
    )
    add_body_paragraph(
        doc,
        "5. Hallucination-Resistant Statutory RAG Knowledge Retrieval: To architect a specialized Retrieval-Augmented Generation "
        "subsystem interfacing with an in-process Qdrant vector database indexing verified statutory circulars and gazette orders, "
        "enforcing a strict cosine similarity floor of 0.55 to completely prevent AI speculation or fabricated procedural requirements."
    )
    add_body_paragraph(
        doc,
        "6. Automated Legal Correction Instrument Synthesis: To design standardized document synthesis modules that populate "
        "legally valid correction instruments, including bilingual sworn 'One and the Same Person' affidavits, MEA Annexure-E "
        "deed polls, and EPFO Joint Declarations containing embedded high-density verification QR codes."
    )
    add_body_paragraph(
        doc,
        "7. Asymmetric Public Key Cryptographic Attestation Subsystem: To engineer an internal Ed25519 Public Key Infrastructure (PKI) "
        "attestation service that digitally signs generated correction artifacts and produces tamper-evident verification metadata "
        "satisfying evidentiary requirements under Section 63 of the Bharatiya Sakshya Adhiniyam 2023."
    )
    add_body_paragraph(
        doc,
        "8. Database-Enforced Tenant Isolation and Append-Only Audit Integrity: To configure PostgreSQL forced Row-Level Security "
        "(RLS) under a dedicated non-superuser role (consolith_app) preventing lateral cross-tenant data traversal, coupled with "
        "database statement triggers that enforce cryptographic SHA-256 hash chaining and absolute immutability on audit logs."
    )
    add_body_paragraph(
        doc,
        "9. Dual-Persona Operational Workspace Architecture: To formulate an intuitive, accessible presentation tier featuring "
        "a Citizen Workspace for autonomous document inspection and an Administrative Verification Console enabling public "
        "officers to audit discrepancy dossiers, inspect cryptographic attestations, and verify hash-chained ledger histories."
    )

    add_heading_1(doc, "1.6 Project Domain and Interdisciplinary Scope")
    add_body_paragraph(
        doc,
        "The project resides at the critical interdisciplinary nexus of Artificial Intelligence, Natural Language Processing, "
        "Applied Cryptography, Information Security, and Public Sector e-Governance Technology. Within the domain of Artificial "
        "Intelligence, the project emphasizes Explainable AI (XAI) and semantic search, departing from opaque black-box models "
        "to ensure that every algorithmic conflict score is interpretable and directly attributable to specific character "
        "differences. Natural Language Processing techniques are leveraged for token normalization, syntactic entity extraction, "
        "and statutory text comprehension across multilingual Indian document contexts."
    )
    add_body_paragraph(
        doc,
        "From an Information Security and Cryptographic standpoint, CONVELINA incorporates zero-trust architectural principles, "
        "elliptic curve digital signatures (Ed25519), symmetric envelope encryption (Fernet), and cryptographic hash chaining "
        "(SHA-256). In the realm of e-Governance and Administrative Law, the platform operationalizes public law statutes, "
        "translating complex government gazettes and statutory regulations into deterministic rules and grounded generative "
        "reasoning chains that comply with Indian constitutional privacy mandates."
    )

    add_heading_1(doc, "1.7 Scope of the Project")
    add_body_paragraph(
        doc,
        "The technical and functional scope of the project encompasses several clearly defined operational boundaries, "
        "guaranteeing depth of implementation while maintaining architectural integrity."
    )
    add_heading_2(doc, "1.7.1 Supported Document Classes")
    add_body_paragraph(
        doc,
        "The Phase I design provides dedicated extraction heuristics, field normalization rules, and discrepancy matching "
        "for five foundational Indian document categories: the Aadhaar Card (UIDAI), the Permanent Account Number Card (Income Tax "
        "Department / NSDL / UTIITSL), the Indian Passport (Ministry of External Affairs), Educational Matriculation and Secondary "
        "School Marksheets (CBSE and State Examination Boards), and the Universal Account Number Member Profile (EPFO)."
    )
    add_heading_2(doc, "1.7.2 Analytical and Algorithmic Scope")
    add_body_paragraph(
        doc,
        "The algorithmic scope encompasses pairwise cross-document demographic comparison covering four core attributes: "
        "Full Legal Name, Date of Birth, Father's or Guardian's Name, and Gender. Discrepancies are quantitatively classified "
        "into High Severity (major structural mismatches requiring formal gazette publication), Medium Severity (initial expansions, "
        "spelling variations, and inverted date formats resolvable via sworn affidavits or joint declarations), and Low Severity "
        "(insignificant formatting variances, whitespace anomalies, or minor case differences)."
    )
    add_heading_2(doc, "1.7.3 Security and Governance Scope")
    add_body_paragraph(
        doc,
        "Security boundaries include complete database-level multi-tenant isolation via PostgreSQL forced Row-Level Security, "
        "zero-knowledge ephemeral document storage wherein raw scan images are deleted immediately after optical feature "
        "extraction, Fernet encryption for all demographic payloads at rest, asymmetric digital attestation via Ed25519 "
        "key pairs, and append-only tamper-evident audit logging with trigger-enforced prohibition of update and delete queries."
    )
    add_heading_2(doc, "1.7.4 Boundaries and Exclusions")
    add_body_paragraph(
        doc,
        "To preserve absolute legal correctness and maintain institutional trust, the scope of CONVELINA is subject to strict "
        "statutory exclusions. The system functions strictly as an advisory, conflict detection, and procedural assistance "
        "platform; it does not constitute an official government adjudicating authority and does not possess legal authority to "
        "declare which document is definitively valid in a dispute. Furthermore, the system does not directly mutate government "
        "databases, does not claim live API integration with UIDAI, PAN, or Passport Seva production endpoints, and does not "
        "replace the statutory discretion of gazetted verification officers. Any discrepancy characterized by unresolvable "
        "optical ambiguity, low confidence scores, or contradictory evidence is explicitly routed to human review pathways."
    )

    add_heading_1(doc, "1.8 Significance and Expected Contributions of Phase I")
    add_body_paragraph(
        doc,
        "The Phase I engineering design of CONVELINA delivers several significant contributions to academic literature and civic "
        "technology practice. First, it formalizes a hybrid fuzzy string comparison methodology specifically optimized for the "
        "unique linguistic patterns and patronymic naming conventions prevalent in Indian identity registries. Second, it "
        "introduces an architectural framework for Retrieval-Augmented Generation in public administration that enforces strict "
        "similarity floors to eliminate speculative hallucinations. Third, it demonstrates the practical application of database-"
        "enforced Row-Level Security and cryptographic tamper-evident logging to protect citizen privacy under strict data protection "
        "mandates. Finally, it provides a comprehensive, validated system architecture, data models, UML designs, and procedural "
        "algorithms that serve as a reproducible foundation for complete full-stack implementation."
    )

    add_heading_1(doc, "1.9 System Context Overview")
    add_body_paragraph(
        doc,
        "The overall operational context of CONVELINA within its external environment is illustrated in Figure 1.1. As depicted, "
        "the platform acts as a secure intermediary between individual citizens seeking identity clarification, official statutory "
        "authorities publishing regulatory circulars, and public verification officers reviewing rectification dossiers. The system "
        "maintains strict trust boundaries, isolating untrusted citizen file uploads from the internal core processing engine, "
        "and safeguarding sensitive demographic records behind cryptographically fortified persistence tiers."
    )

    fig_path = f"{assets_dir}/fig_1_1_context.png"
    add_figure_block(
        doc,
        fig_path,
        "1.1",
        "System Context Diagram of CONVELINA Illustrating External Entities, Trust Boundaries, and Primary Information Flows"
    )

    add_heading_1(doc, "1.10 Organization of the Report")
    add_body_paragraph(
        doc,
        "This Phase I project report is organized into seven comprehensive chapters, structured logically to guide the reader "
        "from problem formulation through detailed architectural design and future scope:"
    )
    add_body_paragraph(
        doc,
        "Chapter 1 introduces the background of Indian foundational identity infrastructure, defines the demographic discrepancy "
        "problem, outlines the aim and nine specific objectives, defines project scope and boundaries, presents expected "
        "contributions, and illustrates the system context."
    )
    add_body_paragraph(
        doc,
        "Chapter 2 provides a comprehensive literature survey examining exactly ten traceable, foundational peer-reviewed research "
        "papers across string distance metrics, record linkage, optical character recognition, vector information retrieval, "
        "transformers, retrieval-augmented generation, approximate nearest neighbor graphs, elliptic curve cryptography, and "
        "language model hallucination surveys, concluding with a literature synthesis and research gap analysis."
    )
    add_body_paragraph(
        doc,
        "Chapter 3 presents the system analysis, detailing the operational characteristics and limitations of existing manual "
        "correction procedures, articulating the proposed CONVELINA architecture and its advantages, providing technical, "
        "operational, economic, and social feasibility studies, and formalizing comprehensive functional and non-functional requirements."
    )
    add_body_paragraph(
        doc,
        "Chapter 4 articulates the methodology and system design, incorporating context-level (Level 0) and functional (Level 1) "
        "Data Flow Diagrams, complete Unified Modeling Language (UML) structural and behavioral models (Use Case, Class, Sequence, "
        "Collaboration, and Activity diagrams), and detailed mathematical formulations, algorithms, and execution pseudocode."
    )
    add_body_paragraph(
        doc,
        "Chapter 5 details the system architecture and detailed design, dissecting the presentation, application, and persistence "
        "layers, explaining layout-aware OCR parsing, ephemeral PII masking, the deterministic discrepancy engine, Qdrant vector "
        "retrieval, PostgreSQL forced Row-Level Security, the Ed25519 PKI attestation engine, the SHA-256 audit ledger, the relational "
        "database schema, the Entity-Relationship (ER) diagram, and deployment topology."
    )
    add_body_paragraph(
        doc,
        "Chapter 6 elaborates on requirements traceability, use-case specifications, statutory standards compliance (Aadhaar Act 2016 "
        "and Bharatiya Sakshya Adhiniyam 2023), ISO/IEC 27001 information security guidelines, comprehensive risk analysis and "
        "mitigation strategies, and the realistic Phase I development timeline and work breakdown structure."
    )
    add_body_paragraph(
        doc,
        "Chapter 7 concludes the Phase I report by summarizing the architectural achievements, verifying design boundaries, "
        "articulating technical limitations and operational assumptions, and presenting a phased roadmap for future enhancements, "
        "including DigiLocker integration, vernacular voice interfaces, and automated portal robotic process automation."
    )

    doc.add_page_break()

