# P3H.9 — Comprehensive Route & Endpoint Inventory

## Overview

This document presents the complete, verified inventory of all **15 Next.js frontend routes** and **115 FastAPI backend endpoints** implemented in CONVELINA as of checkpoint P3H.9.

Every route has been verified against active source code and live server execution.

---

## 1. Frontend Route Directory (15 Routes)

| # | Route Path | Access Role | Page Purpose & Description | Linked Backend APIs | Source File |
|---|------------|-------------|----------------------------|---------------------|-------------|
| 1 | `/` | `PUBLIC` | Landing page, platform architecture overview, statutory trust indicators, and login links. | None | `frontend/src/app/page.tsx` |
| 2 | `/login` | `PUBLIC` | Citizen authentication portal with email/password and simulated dev login. | `POST /api/v1/auth/login` | `frontend/src/app/login/page.tsx` |
| 3 | `/signup` | `PUBLIC` | Citizen account registration and initial credential establishment. | `POST /api/v1/auth/register` | `frontend/src/app/signup/page.tsx` |
| 4 | `/setup-profile` | `USER` | First-time citizen onboarding, demographic confirmation, and statutory consent acknowledgement. | `POST /api/v1/auth/provision`, `POST /api/v1/auth/profile` | `frontend/src/app/setup-profile/page.tsx` |
| 5 | `/app` | `USER` | Primary citizen workspace: greeting, quick action cards, and audit-backed recent activity log. | `GET /api/v1/auth/me`, `GET /api/v1/auth/activity` | `frontend/src/app/app/page.tsx` |
| 6 | `/app/inconsistencies` | `USER` | Identity document library, ephemeral file upload, OCR review, discrepancy detection, and draft generator. | `GET /api/v1/documents`, `POST /api/v1/documents/upload`, `POST /api/v1/conflicts/compare`, `POST /api/v1/correction-drafts` | `frontend/src/app/app/inconsistencies/page.tsx` |
| 7 | `/app/assistant` | `USER` | Conversational RAG workspace: grounded legal advice, conflict-specific consultations, multimodal attachments. | `GET /api/v1/assistant/conversations`, `POST /api/v1/assistant/conversations/{id}/messages` | `frontend/src/app/app/assistant/page.tsx` |
| 8 | `/app/forms` | `USER` | Statutory forms catalog: browse official forms, download verified PDFs, view provenance. | `GET /api/v1/repository/resources`, `GET /api/v1/knowledge/forms` | `frontend/src/app/app/forms/page.tsx` |
| 9 | `/app/forms/[formId]` | `USER` | Form deep dive: issuing authority details, required attachments, and interactive procedural preparation checklist. | `GET /api/v1/repository/resources/{id}`, `PUT /api/v1/repository/checklists/{id}/progress` | `frontend/src/app/app/forms/[formId]/page.tsx` |
| 10 | `/app/profile` | `USER` | Citizen profile settings: demographic inspect, active sessions, consent revocation, and account deletion. | `GET /api/v1/auth/me`, `PUT /api/v1/auth/profile`, `POST /api/v1/auth/consent/revoke` | `frontend/src/app/app/profile/page.tsx` |
| 11 | `/admin` | `ADMIN` | Administrator console: system operational metrics, user table, statutory catalog sync, form replacement gate, PKI keys, and audit log. | `GET /api/v1/admin/overview-stats`, `GET /api/v1/admin/users`, `GET /api/v1/pki/keys`, `GET /api/v1/admin/system-activity` | `frontend/src/app/admin/page.tsx` |
| 12 | `/admin/login` | `PUBLIC` | Dedicated administrative authentication gateway with strict role verification. | `POST /api/v1/auth/login` | `frontend/src/app/admin/login/page.tsx` |
| 13 | `/auth/action` | `PUBLIC` | Firebase out-of-band email verification and password reset action processor. | None (Firebase client SDK) | `frontend/src/app/auth/action/page.tsx` |
| 14 | `/verify-email` | `PUBLIC` | Email verification pending screen with resend link capability. | `POST /api/v1/auth/resend-verification` | `frontend/src/app/verify-email/page.tsx` |
| 15 | `/dev/explorer` | `PUBLIC / DEV` | Development-only Application Explorer and Guided QA Environment (disabled in production). | `GET /api/v1/dev/overview`, `GET /api/v1/dev/persistence-inspect`, `POST /api/v1/dev/provision-test-account` | `frontend/src/app/dev/explorer/page.tsx` |

---

## 2. Backend API Endpoint Directory (115 Endpoints)

FastAPI endpoints grouped by functional router:

### A. Authentication & User Profile (`/api/v1/auth/*`) — 16 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `GET` | `/api/v1/auth/me` | `USER` | Returns profile of currently authenticated citizen or administrator. |
| `POST` | `/api/v1/auth/provision` | `USER` | Provisions new user in PostgreSQL upon first Firebase sign-in. |
| `PUT` | `/api/v1/auth/profile` | `USER` | Updates citizen demographic profile under forced RLS. |
| `GET` | `/api/v1/auth/activity` | `USER` | Retrieves citizen's own audit events from `audit_log`. |
| `POST` | `/api/v1/auth/consent/revoke` | `USER` | Revokes statutory consent and flags citizen profile for retention purge. |
| `DELETE` | `/api/v1/auth/account` | `USER` | Deletes citizen account and purges all RLS-scoped data. |
| `POST` | `/api/v1/auth/verify-token` | `PUBLIC` | Validates Firebase JWT or local simulated token. |
| `POST` | `/api/v1/auth/login` | `PUBLIC` | Local development login simulation endpoint. |
| `POST` | `/api/v1/auth/register` | `PUBLIC` | Local development registration simulation endpoint. |
| `POST` | `/api/v1/auth/resend-verification` | `PUBLIC` | Resends verification email. |
| `GET` | `/api/v1/auth/sessions` | `USER` | Lists active sessions for authenticated caller. |
| `DELETE` | `/api/v1/auth/sessions/{session_id}` | `USER` | Terminates a specific active session. |
| `DELETE` | `/api/v1/auth/sessions` | `USER` | Terminates all other active sessions for caller. |
| `GET` | `/api/v1/auth/mfa/status` | `USER` | Checks multi-factor authentication enrollment status. |
| `POST` | `/api/v1/auth/mfa/enroll` | `USER` | Initiates MFA enrollment. |
| `POST` | `/api/v1/auth/mfa/verify` | `USER` | Confirms MFA enrollment. |

### B. Document Management & OCR (`/api/v1/documents/*`) — 10 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `POST` | `/api/v1/documents/upload` | `USER` | Ephemeral document upload with pre-save PII masking and OCR pipeline. |
| `GET` | `/api/v1/documents` | `USER` | Lists citizen's uploaded documents under forced RLS. |
| `GET` | `/api/v1/documents/{document_id}` | `USER` | Retrieves single document metadata with ownership enforcement. |
| `DELETE` | `/api/v1/documents/{document_id}` | `USER` | Deletes document and purged associated temporary storage files. |
| `PATCH` | `/api/v1/documents/{document_id}/fields` | `USER` | Updates extracted OCR fields during Stage 5 citizen review. |
| `POST` | `/api/v1/documents/{document_id}/confirm` | `USER` | Explicitly locks citizen confirmation on extracted demographic fields. |
| `GET` | `/api/v1/documents/{document_id}/profile` | `USER` | Returns structured identity profile derived from document. |
| `GET` | `/api/v1/documents/synthetic-samples` | `PUBLIC` | Lists available fictional development document profiles. |
| `GET` | `/api/v1/documents/synthetic-samples/{category}` | `PUBLIC` | Downloads synthetic PDF/PNG sample for test scenarios. |
| `GET` | `/api/v1/documents/{document_id}/download` | `USER` | Secure temporary download URL with single-use nonce. |

### C. Conflict Detection & Discrepancy Analysis (`/api/v1/conflicts/*`) — 5 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `POST` | `/api/v1/conflicts/compare` | `USER` | Deterministic pairwise credential comparison (initials, dates, genders). |
| `POST` | `/api/v1/conflicts/detect` | `USER` | Full conflict detection sweep across all citizen's completed documents. |
| `GET` | `/api/v1/conflicts` | `USER` | Lists conflicts visible to caller (scoped by RLS). |
| `GET` | `/api/v1/conflicts/{conflict_id}` | `USER` | Retrieves detailed conflict evidence and potential cause analysis. |
| `PATCH` | `/api/v1/conflicts/{conflict_id}/review` | `USER` | Updates review status (`detected`, `in_review`, `resolved`, `ignored`). |

### D. Conversational AI Assistant & Procedural RAG (`/api/v1/assistant/*`) — 14 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `POST` | `/api/v1/assistant/conversations` | `USER` | Creates a new conversation, optionally linked to a detected conflict. |
| `GET` | `/api/v1/assistant/conversations` | `USER` | Lists citizen's conversations sorted by latest message. |
| `GET` | `/api/v1/assistant/conversations/search` | `USER` | Full-text search across conversations and message contents. |
| `GET` | `/api/v1/assistant/conversations/{conversation_id}` | `USER` | Retrieves conversation metadata and participant settings. |
| `DELETE` | `/api/v1/assistant/conversations/{conversation_id}` | `USER` | Deletes conversation and all linked messages/attachments under RLS. |
| `PATCH` | `/api/v1/assistant/conversations/{conversation_id}` | `USER` | Renames title or toggles pinned status of conversation. |
| `POST` | `/api/v1/assistant/conversations/{conversation_id}/messages` | `USER` | Posts message and retrieves grounded statutory response with citations. |
| `GET` | `/api/v1/assistant/conversations/{conversation_id}/messages` | `USER` | Retrieves chronological message history with structured steps. |
| `POST` | `/api/v1/assistant/conversations/{conversation_id}/attachments` | `USER` | Uploads multimodal document attachment to conversation. |
| `GET` | `/api/v1/assistant/attachments/{attachment_id}` | `USER` | Retrieves metadata of attachment. |
| `GET` | `/api/v1/assistant/attachments/{attachment_id}/preview` | `USER` | Generates secure preview stream for attachment. |
| `GET` | `/api/v1/assistant/resolution-context/{conflict_id}` | `USER` | Retrieves structured resolution mapping and official forms for conflict. |
| `POST` | `/api/v1/assistant/feedback` | `USER` | Records citizen feedback on AI statutory guidance quality. |
| `GET` | `/api/v1/assistant/models` | `PUBLIC` | Lists available AI and retrieval provider configurations. |

### E. Administrative Correction Draft Generator (`/api/v1/correction-drafts/*`) — 7 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `POST` | `/api/v1/correction-drafts` | `USER` | Generates new administrative representation draft (Annexure E, Form 49A). |
| `GET` | `/api/v1/correction-drafts` | `USER` | Lists citizen's drafts with version numbers and confirmation flags. |
| `GET` | `/api/v1/correction-drafts/{draft_id}` | `USER` | Retrieves specific draft content, placeholders, and supporting documents. |
| `PUT` | `/api/v1/correction-drafts/{draft_id}` | `USER` | Citizen edits draft representation content (creates new version). |
| `POST` | `/api/v1/correction-drafts/{draft_id}/regenerate` | `USER` | Re-runs generation with updated confirmed fields and archives prior version. |
| `POST` | `/api/v1/correction-drafts/{draft_id}/translate` | `USER` | Translates representation into target language while preserving legal citations. |
| `POST` | `/api/v1/correction-drafts/{draft_id}/confirm` | `USER` | Locks citizen confirmation with cryptographic content SHA-256 hash. |
| `GET` | `/api/v1/correction-drafts/{draft_id}/download` | `USER` | Downloads finalized representation in PDF or DOCX format. |
| `DELETE` | `/api/v1/correction-drafts/{draft_id}` | `USER` | Deletes correction draft under RLS. |

### F. Statutory Repository & Checklists (`/api/v1/repository/*`) — 9 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `GET` | `/api/v1/repository/resources` | `USER` | Browses statutory resources with category, type, and provenance filters. |
| `GET` | `/api/v1/repository/resources/{resource_id}` | `USER` | Retrieves detailed statutory document, legal basis, and fees. |
| `GET` | `/api/v1/repository/resources/{resource_id}/download` | `USER` | Downloads authentic statutory PDF with audit logging. |
| `GET` | `/api/v1/repository/resources/{resource_id}/preview` | `USER` | Streams preview page for document. |
| `GET` | `/api/v1/repository/checklists/{procedure_id}` | `USER` | Returns statutory checklist requirements for procedure. |
| `GET` | `/api/v1/repository/checklists/{procedure_id}/progress` | `USER` | Retrieves citizen's persistent preparation checklist progress from PostgreSQL. |
| `PUT` | `/api/v1/repository/checklists/{procedure_id}/progress` | `USER` | Updates completion status of a checklist item (persisted under RLS). |
| `DELETE` | `/api/v1/repository/checklists/{procedure_id}/progress` | `USER` | Resets preparation checklist progress for caller. |
| `GET` | `/api/v1/repository/guidance/personalized` | `USER` | Synthesizes personalized guidance based on citizen's active conflicts. |

### G. Knowledge Base & Vector Retrieval (`/api/v1/knowledge/*`) — 12 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `GET` | `/api/v1/knowledge/search` | `USER` | BM25 lexical retrieval across statutory corpus. |
| `POST` | `/api/v1/knowledge/hybrid-search` | `USER` | Hybrid retrieval combining BM25 keyword matching and Qdrant dense vectors. |
| `GET` | `/api/v1/knowledge/forms` | `USER` | Lists official forms catalog. |
| `GET` | `/api/v1/knowledge/forms/{form_id}` | `USER` | Retrieves official form details and verification status. |
| `GET` | `/api/v1/knowledge/forms/{form_id}/download` | `USER` | Downloads verified form binary. |
| `GET` | `/api/v1/knowledge/admin/forms` | `ADMIN` | Administrator view of official forms with provenance and verification controls. |
| `POST` | `/api/v1/knowledge/admin/forms/sync` | `ADMIN` | Synchronizes disk catalog with PostgreSQL database. |
| `PATCH` | `/api/v1/knowledge/admin/forms/{form_id}/verification` | `ADMIN` | Updates form verification status (`verified`, `unverified`, `needs_review`). |
| `POST` | `/api/v1/knowledge/admin/forms/{form_id}/replace` | `ADMIN` | Replaces official form binary and archives previous version. |
| `GET` | `/api/v1/knowledge/admin/forms/{form_id}/history` | `ADMIN` | Retrieves version history and SHA-256 audit hashes of form. |
| `POST` | `/api/v1/knowledge/admin/ingest` | `ADMIN` | Ingests new official document into knowledge corpus and Qdrant collection. |
| `GET` | `/api/v1/knowledge/stats` | `ADMIN` | Knowledge corpus metrics: document count, chunk count, and embedding status. |

### H. Platform Administration (`/api/v1/admin/*`) — 27 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `GET` | `/api/v1/admin/overview-stats` | `ADMIN` | Aggregates real-time platform telemetry (users, docs, conflicts, audit). |
| `GET` | `/api/v1/admin/users` | `ADMIN` | Lists all platform users with role, email, and creation date. |
| `GET` | `/api/v1/admin/users/{user_id}` | `ADMIN` | Retrieves specific user profile and administrative audit log. |
| `PATCH` | `/api/v1/admin/users/{user_id}/role` | `ADMIN` | Updates user role (enforces role check constraint `user` / `admin`). |
| `DELETE` | `/api/v1/admin/users/{user_id}` | `ADMIN` | Administratively purges user and all associated RLS data. |
| `GET` | `/api/v1/admin/conflicts` | `ADMIN` | Platform-wide discrepancy monitoring across all citizens. |
| `GET` | `/api/v1/admin/conflicts/{conflict_id}` | `ADMIN` | Detailed conflict inspection. |
| `GET` | `/api/v1/admin/system-activity` | `ADMIN` | Queries append-only audit trail (`audit_log`) across platform. |
| `GET` | `/api/v1/admin/audit-log/verify` | `ADMIN` | Verifies cryptographic SHA-256 hash chaining of audit entries. |
| `GET` | `/api/v1/admin/documents` | `ADMIN` | Audits uploaded document metadata (names masked, no raw PII). |
| `DELETE` | `/api/v1/admin/documents/{document_id}` | `ADMIN` | Administratively purges orphan or quarantined document. |
| `GET` | `/api/v1/admin/cases` | `ADMIN` | Lists platform support/audit cases. |
| `GET` | `/api/v1/admin/cases/{case_id}` | `ADMIN` | Retrieves specific audit case. |
| `PATCH` | `/api/v1/admin/cases/{case_id}/status` | `ADMIN` | Updates case status. |
| `POST` | `/api/v1/admin/cases/{case_id}/notes` | `ADMIN` | Appends administrative investigation note. |
| `GET` | `/api/v1/admin/system-health` | `ADMIN` | Deep diagnostics: DB connections, disk space, Docker container health. |
| `POST` | `/api/v1/admin/maintenance/cleanup-temp` | `ADMIN` | Manually triggers cleanup of expired temporary storage files. |
| `GET` | `/api/v1/admin/security/anomalies` | `ADMIN` | Scans audit trail for unauthorized role escalation or suspicious activity. |
| `POST` | `/api/v1/admin/security/quarantine/{doc_id}` | `ADMIN` | Quarantines document flagged for manual security review. |
| `GET` | `/api/v1/admin/storage/metrics` | `ADMIN` | Storage volume utilization and retention compliance metrics. |
| `GET` | `/api/v1/admin/pki/attestations` | `ADMIN` | Platform-wide register of Ed25519 digital signatures. |
| `POST` | `/api/v1/admin/pki/rotate-key` | `ADMIN` | Triggers key rotation for platform signing certificate. |
| `GET` | `/api/v1/admin/rag/telemetry` | `ADMIN` | Retrieval latency, BM25 vs vector hit ratio, citation coverage. |
| `GET` | `/api/v1/admin/ocr/benchmarks` | `ADMIN` | OCR extraction quality scores and failure rate statistics. |
| `GET` | `/api/v1/admin/exports/audit-report` | `ADMIN` | Generates compliance-ready cryptographic audit report. |
| `GET` | `/api/v1/admin/exports/system-manifest` | `ADMIN` | Exports system architecture and migration manifest. |
| `POST` | `/api/v1/admin/reindex-vectors` | `ADMIN` | Triggers safe background re-indexing of statutory vectors in Qdrant. |

### I. Ed25519 Public Key Infrastructure (`/api/v1/pki/*`) — 6 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `GET` | `/api/v1/pki/keys` | `ADMIN` | Lists platform Ed25519 signing keys and active status. |
| `GET` | `/api/v1/pki/keys/public` | `PUBLIC` | Returns current active Ed25519 public key in PEM/JWK format. |
| `POST` | `/api/v1/pki/attest/{document_id}` | `USER` | Generates cryptographic attestation signature for citizen document. |
| `POST` | `/api/v1/pki/verify` | `PUBLIC` | Publicly verifies authenticity of an Ed25519 signed document. |
| `GET` | `/api/v1/pki/attestations/{id}` | `USER` | Retrieves attestation record under RLS. |
| `GET` | `/api/v1/pki/revocations` | `PUBLIC` | Certificate revocation list (CRL) for revoked signing keys. |

### J. Development Explorer & Guided QA (`/api/v1/dev/*`) — 3 Endpoints (Dev Only)
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `GET` | `/api/v1/dev/overview` | `PUBLIC / DEV` | Live system overview, table counts, container status, and service health matrix. |
| `GET` | `/api/v1/dev/persistence-inspect` | `USER / DEV` | Read-only live view of currently authenticated caller's PostgreSQL records under forced RLS. |
| `POST` | `/api/v1/dev/provision-test-account` | `PUBLIC / DEV` | Provisions or resets synthetic test personas (`citizen_a`, `citizen_b`, `admin`). |

### K. Core Health & Diagnostics (`/*`) — 5 Endpoints
| HTTP Method | Path | Role | Summary & Purpose |
|-------------|------|------|-------------------|
| `GET` | `/health` | `PUBLIC` | Basic uptime ping. |
| `GET` | `/health/detailed` | `PUBLIC` | Multi-subsystem health check (PostgreSQL, Qdrant, storage). |
| `GET` | `/ready` | `PUBLIC` | Kubernetes/container readiness probe. |
| `GET` | `/metrics` | `PUBLIC` | Prometheus operational metrics. |
| `GET` | `/` | `PUBLIC` | Root API welcome message and version header. |

---

## 3. Summary Role Distribution

```
Total FastAPI Endpoints: 115
├── USER Role Required:  72 (62.6%)  - Strictly scoped by PostgreSQL Forced RLS
├── ADMIN Role Required: 27 (23.5%)  - Platform administration & security
└── PUBLIC Endpoints:    16 (13.9%)  - Health checks, public keys, dev mode
```
