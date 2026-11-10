# P3H.9 — CONVELINA Application Explorer & Guided QA Environment

## Executive Summary

The **CONVELINA Application Explorer** (`/dev/explorer`) is a dedicated internal engineering and QA dashboard designed to provide developers, product reviewers, and test engineers with immediate, transparent, and structured access to every aspect of the running CONVELINA system.

Built strictly for local development and QA verification, the Explorer aggregates live runtime telemetry, comprehensive route inventories, feature-to-code mapping, 14 interactive step-by-step walkthroughs, test-account simulators, a live PostgreSQL forced-RLS persistence inspector, and an administrative telemetry console.

---

## 1. Safety & Production Guardrails

To prevent data leakage, accidental disclosure of internal system architecture, or unauthorized test-account simulation in production, the Explorer is protected by dual-layer client and server guardrails:

### Client-Side Guardrail
- **Route**: `frontend/src/app/dev/explorer/page.tsx`
- **Protection**: If `NEXT_PUBLIC_ENVIRONMENT === "production"`, the page terminates execution and renders a strict `404 - Development Only Route` screen.
- **Header Badge**: Prominently displays `CONVELINA DEV QA ENVIRONMENT • INTERNAL EXPLORATION ONLY` in bright amber at the top of the interface.

### Server-Side Guardrail
- **Endpoints**: `/api/v1/dev/*`
- **Protection**: Every endpoint invokes `verify_dev_mode()`. If `settings.ENVIRONMENT.lower() == "production"`, the server immediately raises `HTTP 403 Forbidden` (`{"detail": "Development endpoints are strictly disabled in production."}`).
- **Configuration**: Dev endpoints and simulated tokens are conditionally registered only when the host environment is not production.

---

## 2. Seven Core Functional Explorer Sections

The Application Explorer organizes system inspection into 7 tabs:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ CONVELINA DEV QA ENVIRONMENT • INTERNAL EXPLORATION ONLY                                    │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ [1. Overview & Health] [2. Route Explorer] [3. Feature Guide] [4. Interactive Workflows]     │
│ [5. Test Accounts]     [6. Persistence Inspector]            [7. Admin Explorer]            │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Tab 1: Overview & Live Health
Aggregates live runtime diagnostics across all backend subsystems:
- **FastAPI Backend**: Reports active version (1.0.0), environment mode, and debug flag.
- **PostgreSQL 16**: Validates connection to port 5432, verifies the dedicated non-superuser role `consolith_app`, confirms that all 21 application tables have `FORCE ROW LEVEL SECURITY` enabled, and verifies persistent mount `consolin_pgdata`.
- **Qdrant Vector Database**: Queries port 6333, confirms durable collection storage (`consolin_qdrant_data`), and validates the `statutory_documents` collection (384-dimensional cosine index).
- **Firebase Authentication**: Clearly marked as **SIMULATED** in local development mode. Accurately reports that live Google cloud credentials are not configured and local tokens are safely utilized without compromising authorization checks.
- **Gemini LLM Provider**: Clearly marked as **BLOCKED / DISABLED BY DEFAULT**. Explains deterministic BM25 retrieval fallback and statutory citation enforcement.
- **OCR Engine**: Reports Tesseract OCR with deterministic heuristic and regular expression fallback with pre-save PII masking.
- **Ed25519 PKI Attestation**: Active RFC 8032 digital signature engine for document verification.

### Tab 2: Route Explorer
Provides an interactive inventory of all 15 Next.js frontend routes and 115 FastAPI backend endpoints.
- Displays HTTP methods, route paths, access role requirements (`PUBLIC`, `USER`, `ADMIN`), and underlying controller/service files.
- Includes clickable direct navigation links to every frontend page for instant manual QA.

### Tab 3: Feature Guide
Exhaustively documents the 8 core features of CONVELINA:
1. Citizen Profile & Ephemeral Verification
2. Ephemeral Ingestion & PII Masking
3. OCR Extraction & Stage 5 Field Review
4. Deterministic Conflict Detection Engine
5. Conversational AI Workspace & Procedural RAG
6. Administrative Correction Draft Generator
7. Statutory Forms Repository & Checklist Preparation
8. Administrator Audit Ledger & Document Security Gate

Each feature card details:
- **What it does** (Core purpose)
- **What data it reads** (Input entities and sources)
- **What data it modifies** (State changes and storage)
- **Where data persists** (PostgreSQL tables, Qdrant vectors, local temporary directory)
- **Code locations** (Exact backend routers, services, frontend components)
- **Known limitations** (Realistic assessment of development status)

### Tab 4: Interactive Workflows (14 Guided QA Walkthroughs)
Provides structured, numbered walkthroughs covering every core user journey:
1. Register & Sign In (Simulated Dev Mode)
2. Upload Synthetic Identity Document
3. Review & Confirm OCR Fields
4. View Identity Library
5. Compare Two Identity Documents (Deterministic Matching)
6. Review Inconsistency Details
7. Start AI Assistant Conversation
8. Ask Guidance on a Specific Conflict
9. Grounded Retrieval (BM25 vs Vector)
10. Browse Official Repository & Forms
11. Save Checklist Progress (Persistent PostgreSQL Checklists)
12. Generate Correction Representation Draft
13. Download Attested Document (Ed25519 Signed)
14. Admin Console & Platform Telemetry

Each walkthrough explicitly identifies whether it operates in **REAL** mode (live database read/write, live comparison) or **SIMULATED** mode (local test token, disabled cloud API).

### Tab 5: Test-Account Management & Simulator
Provides a one-click session switcher between synthetic personas:
- **Citizen A (`citizen_a@example.com` / Aarav Sharma)**: Standard citizen persona with conflicting Aadhaar and PAN documents.
- **Citizen B (`citizen_b@example.com` / Priya Patel)**: Fresh citizen persona with zero uploaded documents to test multi-tenant isolation.
- **Platform Admin (`admin@convelina.gov.in` / AJAY M)**: Platform administrator persona with full telemetry, catalog sync, and audit ledger access.
- **Session Reset**: Clears `convelina_test_token` and reloads the application.

### Tab 6: Live PostgreSQL Persistence Inspector
A real-time, read-only diagnostic inspector querying the PostgreSQL database through `/api/v1/dev/persistence-inspect` under the currently active user session:
- Proves that Row-Level Security (RLS) is active by showing only records owned by the authenticated caller.
- Lists uploaded documents with masked IDs and storage locations.
- Lists detected discrepancies with masked values and severity.
- Lists persistent checklist procedures with completed items count.
- Lists generated correction drafts with current version and confirmation status.
- Displays an **Entity Storage & Tenancy Protection Matrix** detailing all 10 core entities, their database tables, primary keys, and RLS policy descriptions.

### Tab 7: Admin Explorer
Previews and explores administrative capabilities:
- Real-time operational metric collection (`GET /api/v1/admin/overview-stats`).
- Catalog synchronization and statutory form verification (`GET /api/v1/knowledge/admin/forms`).
- Form replacement and rejection safety gate (`POST /api/v1/knowledge/admin/forms/{id}/replace`).
- Platform Ed25519 PKI keystore (`GET /api/v1/pki/keys`).
- Cryptographic append-only audit trail (`GET /api/v1/admin/system-activity`).

---

## 3. Verification & Acceptance

The Application Explorer has been verified through an automated end-to-end Playwright test suite (`frontend/e2e/p3h9_explorer_and_qa.spec.ts`):
- **Test 1**: Explorer Interface, Architecture & Live Health Inspection (**PASSED in 12.2s**)
- **Test 2**: Full Citizen A Workflow, Persistence & Inspector Verification (**PASSED in 55.9s**)
- **Test 3**: Citizen B Multi-Tenant Isolation & Zero Leakage (**PASSED in 23.5s**)
- **Test 4**: Administrative Authorization Boundaries & Admin Console (**PASSED in 31.2s**)
- **Total Suite Execution**: 4 passed in 2.2 minutes.
