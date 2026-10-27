# Project Context: CONVELINA
**Tagline**: *Statutory Document Discrepancy Detection & Clerical Correction Platform*

## 1. What CONVELINA is

CONVELINA is an AI-powered statutory document reconciliation and verification platform that detects conflicts across Indian identity records (Aadhaar, PAN, Passport, 10th/12th certificates, EPF records) — such as names spelled differently across records, or genuine mismatches in parents' names, dates of birth, or addresses — and provides grounded, source-cited statutory guidance using Retrieval-Augmented Generation (RAG). Built with enterprise-grade Row-Level Security, Ed25519 PKI digital attestations, and cryptographic SHA-256 audit chaining.

---

## 2. The Problem It Solves

1. **Format inconsistencies across documents** (e.g. "M Ajay" vs "Ajay M" vs "M. Ajay") cause false-positive mismatches in naive matching systems, even though they refer to the same person.
2. **Genuine data mismatches** (e.g. a father's name "Muthu" on Aadhaar vs "Muthukumar M" on a school certificate) block real processes — passport issuance, scholarship disbursement, EPFO claims, bank KYC — and citizens usually only discover this at rejection time.
3. **No existing consumer product** combines multi-document upload, automated cross-document mismatch detection, and plain-language correction guidance in one place. This was confirmed through research: DigiLocker is a repository, not a reconciler; B2B KYC APIs (HyperVerge, Signzy, Surepass, IDfy, Karza) sell mismatch detection only to banks/NBFCs, not citizens; existing correction help is either generic static content or paid human-agent services.
4. **Citizens without sufficient proof to self-correct a document** currently have no structured path — today this is ad hoc and can take months through existing channels.

---

## 3. Worked Example — Running Test Case

- **Ajay's Documents:**
  - Aadhaar reads "M Ajay"
  - 10th certificate reads "Ajay M"
  - 12th transfer certificate reads "M. Ajay"
  - **Classification:** **format-only**, same person, no action needed (standardizing before passport application recommended).
- **Father's Name Comparison:**
  - Father's Aadhaar reads "Muthu"
  - Ajay's 10th certificate lists father's name as "Muthukumar M"
  - **Classification:** **genuine mismatch, high severity** — can block passport verification and scholarship processing; explain with cited sources and offer correction affidavit draft.
- **Verification Case Escalation:**
  - Father has no proof to correct driving licence ("Muthu M" vs current Aadhaar "Muthu") -> raise a verification case reviewed by an officer role.

---

## 4. Target Users

- **Citizens**: upload and check their own documents.
- **Officers**: review verification cases where citizen lacks proof to self-correct.
- **Admins**: manage the knowledge base of official correction procedures.

---

## 5. Scope Boundaries (Locked)

- **Tier 1 (Built & Supported):** Aadhaar, PAN, Passport, 10th/12th certificates, EPF records.
- **Tier 2 (Architecture extensible, do not build yet):** Voter ID, Driving Licence, Birth Certificate, Transfer Certificate.
- **Tier 3 (Future only, do not build):** Community/income/native certificates, Ration Card, APAAR ID.

### Hard Constraints
- **No long-term storage of Aadhaar numbers or document images** beyond active processing requirements (Aadhaar Act restriction).
- **No live integration with any government portal, no auto-submission.** System provides guidance and drafts only.
- **Never describe the system as "unhackable."** Focus on *tamper-evidence* (cryptographic signing, hash-chained audit logs).
- **No scope expansion mid-build.** Maintain academic timeline discipline.

---

## 6. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), TypeScript (strict mode), Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI, Pydantic v2 |
| OCR / Matching Microservice | Separate containerized Python service — Tesseract (OCR), RapidFuzz (fuzzy matching), Jellyfish (phonetic matching) |
| Relational Database | PostgreSQL 16+, with Row-Level Security enabled AND forced on every table holding user data |
| Vector Database | Qdrant (self-hosted via Docker) |
| Embeddings | BGE-M3 |
| RAG Orchestration | LangChain |
| LLM (Generation) | Anthropic Claude via Claude API (cost-appropriate model, configurable via ENV) |
| Auth | Firebase Authentication, with server-side JWT re-verification on every backend route |
| File Storage | Firebase Storage, short-lived retention only |
| Security / Integrity | Internal PKI/CA with Ed25519 signatures; Fernet encryption at rest; append-only hash-chained audit log |
| Containerization | Docker, Docker Compose |
| Deployment | Cloud-first (Vercel + Railway) with path to self-hosted private VPS |

*(Note: CPU-only hardware makes local LLMs non-viable; use hosted Claude API).*

---

## 7. Non-Negotiable Security Requirements

1. **Row-Level Security (RLS):** Enabled and **forced** on every table holding user data. Directly verify against live DB (`pg_policies`, `pg_tables.rowsecurity`, `pg_tables.forcerowsecurity`).
2. **Role & Ownership Re-verification:** Every backend route re-verifies caller role and ownership server-side.
3. **Dedicated Non-Superuser DB Role:** Backend must connect using a dedicated non-superuser role (superusers bypass RLS).
4. **Connection Pooling Trap:** PostgreSQL session variables revert to `""` (empty string) on connection reuse, not `NULL`. Use `NULLIF(current_setting(...), '')::uuid` and test repeated requests across pooled connections.
5. **Aadhaar Protection:** Mask all but the last 4 digits in UI/logs, encrypt at rest with Fernet, never log in plaintext.
6. **Append-Only Audit Log:** Database trigger blocking `UPDATE`/`DELETE` on existing audit rows; verify by attempting deletion.
7. **Zero Secrets in VCS:** Rigorous `.gitignore`, staged file content scans before commit.

---

## 8. Non-Negotiable Correctness & Honesty Requirements

1. **No Hallucinated RAG Answers:** Relevance-score floor (e.g. 0.55). If nothing relevant is retrieved, explicitly decline to answer.
2. **Post-Generation Citation Validation:** Validate every cited URL/source against retrieved context.
3. **Procedural Knowledge Only:** Only ingest genuine procedural content (forms, rules, steps); do not ingest superficial portal/login pages. Document gaps honestly.
4. **Fail-Safe Conflict Detection:** Non-Latin script or low OCR confidence returns "unresolvable — needs manual review". Never guess.
5. **Meaningful Tests:** Tests must have real failure modes.
6. **Key Edge Cases in Regression Battery:**
   - Initials vs full names ("R Karthik" vs "Karthik Raman" -> unresolvable).
   - Gendered similar names ("Deepak"/"Deepika", "Kumar"/"Kumari", "Sunil"/"Sunita" -> distinct, not same person).
   - Truncated names ("Muthu" vs "Muthukumar" -> truncation, not typo).
   - Honorifics as given names ("Kumari", "Selvi" -> preserved, not stripped).
   - Transliteration variants ("Rajeev"/"Rajiv", "Lakshmi"/"Laxmi" -> likely same person).

---

## 9. Build Order

1. **Foundation** — Next.js frontend + FastAPI backend + PostgreSQL + Qdrant (Docker Compose).
2. **Database schema + Row-Level Security** — Tables, forced RLS, non-superuser role, live DB verification.
3. **Authentication** — Firebase Auth, JWT verification, RLS session variable mapping, pool reuse isolation tests.
4. **Document upload + OCR pipeline** — Upload, Tesseract OCR with confidence scoring, masking, encryption, audit logging.
5. **Conflict detection engine** — RapidFuzz + Jellyfish, 40+ case regression battery covering edge cases.
6. **RAG knowledge base + AI assistant** — Verified procedural sources, score floor, citation validator.
7. **Correction document generator** — Pre-filled affidavits & declarations (Tier 1 docs).
8. **Officer verification workflow** — Officer queue, RLS-scoped assignment, approval/rejection.
9. **Document authenticity / verification module** — OCR-vs-text-layer, Ed25519 digital signature PKI/CA.
10. **Security hardening pass** — Full penetration/isolation audit, privilege escalation check.
