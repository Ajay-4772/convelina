# CONVELINA — Architecture Decision Records (ADRs)

**Classification:** Architectural Governance  
**Status:** ACTIVE & ENFORCED  

---

## Index of Architecture Decision Records

* [ADR-001: Multi-Container Foundation](#adr-001-multi-container-foundation)
* [ADR-002: Forced Row-Level Security with Dedicated Non-Superuser Role](#adr-002-forced-row-level-security-with-dedicated-non-superuser-role)
* [ADR-003: Connection-Pooling Safe Session Context Variables](#adr-003-connection-pooling-safe-session-context-variables)
* [ADR-004: Ephemeral Document Storage & Post-OCR Shredding](#adr-004-ephemeral-document-storage--post-ocr-shredding)
* [ADR-005: Deterministic Conflict Engine Independent of LLMs](#adr-005-deterministic-conflict-engine-independent-of-llms)
* [ADR-006: Single-Provider Google Gemini RAG Architecture & Relevance Floor](#adr-006-single-provider-google-gemini-rag-architecture--relevance-floor)
* [ADR-007: Cryptographically Chained Append-Only Audit Trail](#adr-007-cryptographically-chained-append-only-audit-trail)
* [ADR-008: Ed25519 Digital Signatures with RFC 8785 Canonical JSON Serialization](#adr-008-ed25519-digital-signatures-with-rfc-8785-canonical-json-serialization)
* [ADR-009: Google Stitch Design System & Next.js App Router Structure](#adr-009-google-stitch-design-system--nextjs-app-router-structure)
* [ADR-010: Retention of Modular Monolith Over Microservices](#adr-010-retention-of-modular-monolith-over-microservices)

---

### ADR-001: Multi-Container Foundation
- **Date:** 2026-09-29  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** Developers and deployment targets need deterministic, zero-configuration local orchestration.  
- **Decision:** Orchestrate PostgreSQL 16 Alpine, Qdrant vector DB, FastAPI, and Next.js frontend using Docker Compose with internal network isolation and distinct service health checks.  
- **Consequences:** Eliminates host dependency mismatches (e.g. Poppler, Tesseract C++ libraries); enables identical test execution in CI and local machines.

---

### ADR-002: Forced Row-Level Security with Dedicated Non-Superuser Role
- **Date:** 2026-09-29  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** Table owners and superusers bypass RLS policies by default in PostgreSQL. Application-level tenant checks are susceptible to developer error.  
- **Decision:** Enable and **force** Row-Level Security (`ALTER TABLE ... FORCE ROW LEVEL SECURITY`) across all tenant-data tables. Configure the application connection pool strictly under `consolith_app`, a non-superuser role with least privileges.  
- **Consequences:** Database engine mathematically guarantees that User B querying the database directly receives 0 rows when attempting to inspect User A's credentials, conflicts, or drafts.

---

### ADR-003: Connection-Pooling Safe Session Context Variables
- **Date:** 2026-09-29  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** When pooled database connections are reused across HTTP transactions, uninitialized or reset session parameters evaluate to empty strings `""` rather than `NULL`. Direct casting (`::uuid`) throws unhandled database exceptions.  
- **Decision:** All RLS policies referencing session parameters must wrap reads in `NULLIF(current_setting('app.current_user_id', true), '')::uuid`.  
- **Consequences:** Complete resilience against connection pooling reuse anomalies in PgBouncer, SQLAlchemy, or asyncpg pools.

---

### ADR-004: Ephemeral Document Storage & Post-OCR Shredding
- **Date:** 2026-09-29  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** The Aadhaar Act (2016) and UIDAI circulars strictly forbid long-term storage of raw Aadhaar card images or unmasked 12-digit identity numbers.  
- **Decision:** Uploaded documents are saved to an ephemeral directory (`/tmp/consolith/temp_docs`) with restricted `0600` POSIX permissions. Following Tesseract OCR extraction and Verhoeff-validated first-8-digit masking (`XXXX-XXXX-1234`), the temporary file is unlinked immediately in a `finally:` block. Sensitive extracted text is encrypted at rest via Fernet.  
- **Consequences:** Complies with Indian statutory privacy mandates; eliminates long-term liability from data breach of raw identity scans.

---

### ADR-005: Deterministic Conflict Engine Independent of LLMs
- **Date:** 2026-09-30  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** LLMs suffer from non-deterministic outputs and hallucinations, making them unsafe for determining whether a citizen's name or date of birth matches across legal records.  
- **Decision:** Implement discrepancy detection using 100% deterministic algorithms (Levenshtein distance, RapidFuzz `token_sort_ratio`, Soundex, Jellyfish Double Metaphone, and calendar parsing with year-only compatibility). The comparison engine executes with zero LLM involvement.  
- **Consequences:** 100% reproducible results, zero hallucinated discrepancies, high throughput, and complete legal defensibility.

---

### ADR-006: Single-Provider Google Gemini RAG Architecture & Relevance Floor
- **Date:** 2026-09-30  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** Statutory guidance must be grounded in verified circulars from UIDAI, NSDL, MEA, EPFO, and CBSE without inventing procedures. Multi-provider fallbacks introduce prompt incompatibilities.  
- **Decision:** Enforce Google Gemini as the single approved LLM provider. Impose a cosine similarity relevance floor of $\ge 0.55$ in Qdrant hybrid retrieval. Enforce strict citation validation. If Gemini is unavailable or evidence falls below the floor, return the exact contract message: `"Assistant service is not currently available. Please try again later."`  
- **Consequences:** Zero hallucinated circulars or non-existent government forms; predictable service failure modes without ungrounded guessing.

---

### ADR-007: Cryptographically Chained Append-Only Audit Trail
- **Date:** 2026-09-30  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** Discrepancy audits and officer decisions require forensic integrity that cannot be modified even by database administrators.  
- **Decision:** Implement a PostgreSQL statement trigger `block_audit_log_mutation()` blocking any `UPDATE` or `DELETE` on the `audit_log` table. Each audit entry computes its SHA-256 hash by cryptographically incorporating the hash of the preceding record (`previous_hash`).  
- **Consequences:** Complete tamper-evidence; any post-hoc modification breaks the cryptographic hash chain and is immediately detectable.

---

### ADR-008: Ed25519 Digital Signatures with RFC 8785 Canonical JSON Serialization
- **Date:** 2026-09-30  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** Attested identity packages and verification dossiers must be portable and verifiable offline by third-party authorities without exposing underlying PII.  
- **Decision:** Attestations are serialized using RFC 8785 (Canonical JSON) and digitally signed using Ed25519 (RFC 8032 Edwards-curve digital signatures). Only the SHA-256 document fingerprint and cryptographic signature are stored in public verification records.  
- **Consequences:** Millisecond signature verification; immunity to key-ordering serialization discrepancies; zero PII leakage during public verification.

---

### ADR-009: Google Stitch Design System & Next.js App Router Structure
- **Date:** 2026-10-28  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** The citizen workspace previously relied on a single 1,488-line file with tab-switching, lacking deep-linking, maintainability, and clean visual restraint.  
- **Decision:** Decompose the citizen experience into modular Next.js 14 App Router routes (`/app`, `/app/inconsistencies`, `/app/assistant`, `/app/assistant/[conversationId]`, `/app/forms`, `/app/forms/[formId]`, `/app/profile`) wrapped in a shared `WorkspaceShell`. Codify the Google Stitch design tokens (`#FAF9F6`, `#111111`, `#FFFFFF`, `#E7E5E0`, Merriweather, Inter) and remove global sensitive search.  
- **Consequences:** Bookmarkable URLs, isolated state management, zero horizontal overflow, and high aesthetic discipline.

---

### ADR-010: Retention of Modular Monolith Over Microservices
- **Date:** 2026-10-28  
- **Status:** ACCEPTED & IMPLEMENTED  
- **Context:** Premature microservice decomposition introduces distributed transaction complexity, network overhead, and complex deployment pipelines.  
- **Decision:** Retain CONVELINA as a modular monolith. All modules (Auth, Upload, Conflict, RAG, Drafts, Cases, PKI, Admin) reside within a clean, decoupled FastAPI package sharing PostgreSQL and Qdrant.  
- **Consequences:** Zero distributed network failures; instant ACID transactions; low hosting overhead; rapid development and auditability.

