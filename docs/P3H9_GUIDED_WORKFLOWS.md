# P3H.9 — Interactive Guided QA Workflows (14 End-to-End Scenarios)

## Overview

This guide provides exhaustive, step-by-step instructions for testing and validating all **14 core workflows** of CONVELINA using the **Application Explorer** (`/dev/explorer`) and the citizen and administrator interfaces.

Each workflow explicitly states whether it operates in **REAL** mode (live database read/write, live cryptographic hashing) or **SIMULATED** mode (local development token simulation, disabled third-party cloud API).

---

## Workflow Directory

```
1.  Register & Sign In (Simulated Dev Mode)
2.  Upload a Synthetic Identity Document
3.  Review & Confirm Extracted Fields (Stage 5)
4.  View Identity Library & Ephemeral Masking
5.  Compare Two Identity Documents (Deterministic Matching)
6.  Review Discrepancy Inconsistency Details
7.  Start Conversational AI Assistant Thread
8.  Ask Guidance on a Specific Conflict
9.  Grounded Retrieval (BM25 vs Vector Search)
10. Browse Official Repository & Forms
11. Save Preparation Checklist Progress
12. Generate Correction Representation Draft
13. Download Attested Document (Ed25519 PKI)
14. Administrator Console & Platform Telemetry
```

---

### Workflow 1: Register & Sign In (Simulated Dev Mode)
- **Classification**: `SIMULATED` (Local Dev Token Simulation Active; Live Google Cloud Firebase Blocked)
- **Step-by-Step Instructions**:
  1. Open `/dev/explorer` and click the **Test Accounts** tab.
  2. Click **"Simulate Citizen A Session (Aarav Sharma)"** (or navigate to `/login` and submit synthetic credentials).
  3. Observe the immediate activation of `localStorage.convelina_test_token`.
  4. The client redirects to `/app`.
- **Expected Results**:
  - The top bar displays `Aarav Sharma` with a personalized greeting ("Good morning, Aarav Sharma").
  - The sub-header confirms `Overview • Active Citizen Session`.
- **Underlying APIs**:
  - `POST /api/v1/dev/provision-test-account`
  - `GET /api/v1/auth/me` (Bearer test token)
- **Database & Storage Changes**:
  - User record verified/created in PostgreSQL `users` table with `role = 'user'`.

---

### Workflow 2: Upload a Synthetic Identity Document
- **Classification**: `REAL` (Live file upload, live in-memory OCR extraction, live database insertion)
- **Step-by-Step Instructions**:
  1. Navigate to `/app/inconsistencies`.
  2. In the **Upload Identity Credential** section, select Document Type: `Aadhaar Card`.
  3. Upload a synthetic PDF (or click **"Download Sample Synthetic Aadhaar"** from the dev explorer).
  4. Click **"Upload & Process Document"**.
- **Expected Results**:
  - Progress indicator shows extraction.
  - The document appears in the library as `Processing` or `Ready for Review`.
  - Aadhaar number is masked (`XXXX-XXXX-1098`).
- **Underlying APIs**:
  - `POST /api/v1/documents/upload` (multipart/form-data)
- **Database & Storage Changes**:
  - Row created in `documents` table under caller's RLS scope.
  - In-memory OCR extracts text; binary saved temporarily to local temp storage.

---

### Workflow 3: Review & Confirm Extracted Fields (Stage 5 Review)
- **Classification**: `REAL` (PostgreSQL update under forced RLS)
- **Step-by-Step Instructions**:
  1. On `/app/inconsistencies`, click **"Review Extracted Fields"** on the newly uploaded document.
  2. Inspect the extracted fields in the modal (Name, DOB, Gender, Father's Name).
  3. If necessary, correct any typographical error.
  4. Click **"Confirm & Lock Fields"**.
- **Expected Results**:
  - Document status updates to `Confirmed`.
  - Field inputs lock; `is_citizen_confirmed` becomes `true`.
- **Underlying APIs**:
  - `PATCH /api/v1/documents/{id}/fields`
  - `POST /api/v1/documents/{id}/confirm`
- **Database & Storage Changes**:
  - `documents.confirmed_fields` updated with citizen review.
  - `citizen_confirmed_at` timestamp recorded.

---

### Workflow 4: View Identity Library & Ephemeral Masking
- **Classification**: `REAL` (Live PostgreSQL query with forced RLS)
- **Step-by-Step Instructions**:
  1. Navigate to `/app/inconsistencies`.
  2. Observe the cards in the **Identity Document Library**.
- **Expected Results**:
  - Only documents uploaded by the current citizen are visible.
  - All sensitive identifier numbers are masked.
  - Document type badges (Aadhaar, PAN, Passport) display correctly.
- **Underlying APIs**:
  - `GET /api/v1/documents`
- **Database & Storage Changes**:
  - Read-only execution under `consolith_app` role.

---

### Workflow 5: Compare Two Identity Documents (Deterministic Matching)
- **Classification**: `REAL` (Deterministic multi-field comparison engine execution)
- **Step-by-Step Instructions**:
  1. Ensure at least two confirmed documents exist in `/app/inconsistencies` (e.g., Aadhaar and PAN).
  2. Click **"Detect All Inconsistencies"** (or select checkboxes on two documents and click **"Compare Selected"**).
  3. Wait 1-2 seconds for the deterministic engine to analyze field values.
- **Expected Results**:
  - Engine reports detected discrepancies with exact field-level comparison.
  - Initial expansions (e.g., `A. Sharma` vs `Aarav Sharma`) are classified as `Initial Expansion / Ambiguity` rather than a complete name mismatch.
- **Underlying APIs**:
  - `POST /api/v1/conflicts/compare`
  - `POST /api/v1/conflicts/detect`
- **Database & Storage Changes**:
  - Row created in `conflicts` table for each detected discrepancy with severity and evidence JSONB.

---

### Workflow 6: Review Discrepancy Inconsistency Details
- **Classification**: `REAL` (Live query of conflict details and resolution mappings)
- **Step-by-Step Instructions**:
  1. In `/app/inconsistencies`, scroll to the **Detected Inconsistencies** section.
  2. Click **"Inspect Discrepancy"** on any discrepancy card.
  3. Review the discrepancy severity, evidence, statutory rules, and recommended procedural path.
- **Expected Results**:
  - Detailed modal opens displaying side-by-side field values, potential causes, and statutory citations.
- **Underlying APIs**:
  - `GET /api/v1/conflicts/{id}`
  - `GET /api/v1/assistant/resolution-context/{id}`
- **Database & Storage Changes**:
  - Read-only execution.

---

### Workflow 7: Start Conversational AI Assistant Thread
- **Classification**: `REAL` (Conversational thread persistence in PostgreSQL)
- **Step-by-Step Instructions**:
  1. Navigate to `/app/assistant`.
  2. Click **"New Consultation"** in the sidebar.
  3. Enter a title (or leave default) and submit.
- **Expected Results**:
  - A new chat thread is created and selected in the active conversation list.
- **Underlying APIs**:
  - `POST /api/v1/assistant/conversations`
- **Database & Storage Changes**:
  - Row inserted in `conversations` table linked to caller's `user_id`.

---

### Workflow 8: Ask Guidance on a Specific Conflict
- **Classification**: `REAL` (BM25 statutory retrieval active; Gemini LLM simulation mode)
- **Step-by-Step Instructions**:
  1. In `/app/assistant`, open a conversation linked to a conflict (or type: *"How do I fix a name mismatch between my Aadhaar and PAN card?"*).
  2. Press **Send**.
- **Expected Results**:
  - Assistant responds with structured, grounded steps:
    1. Gazette notification guidance or Annexure E representation.
    2. Relevant official forms (Form 49A, UIDAI Update Form).
    3. Potential future implications (EPFO, Passport delays).
- **Underlying APIs**:
  - `POST /api/v1/assistant/conversations/{id}/messages`
- **Database & Storage Changes**:
  - User message and assistant response persisted in `messages` table.

---

### Workflow 9: Grounded Retrieval (BM25 vs Vector Search)
- **Classification**: `REAL` (Live BM25 lexical search over statutory corpus + live Qdrant collection)
- **Step-by-Step Instructions**:
  1. Open `/dev/explorer` and view the **Overview & Health** card for Qdrant and Retrieval.
  2. Open `/app/assistant` and inquire about a statutory regulation: *"What are the UIDAI SOP requirements for first name changes?"*
- **Expected Results**:
  - Response retrieves matching chunks from UIDAI circulars and Form 49A guidance with source citations.
- **Underlying APIs**:
  - `GET /api/v1/knowledge/search`
  - `POST /api/v1/knowledge/hybrid-search`
- **Database & Storage Changes**:
  - Vector similarity query against Qdrant collection `statutory_documents` (cosine metric).

---

### Workflow 10: Browse Official Repository & Forms
- **Classification**: `REAL` (Static disk catalog + PostgreSQL official forms registry)
- **Step-by-Step Instructions**:
  1. Navigate to `/app/forms`.
  2. Browse available official forms (Aadhaar Enrolment Form, PAN Form 49A, EPFO Joint Declaration).
  3. Filter by category: `Aadhaar`, `PAN`, `Passport`, `EPFO`.
  4. Click on any form card to inspect detailed statutory information.
- **Expected Results**:
  - Form details page loads showing issuing authority, description, prescribed fees, and required supporting documents.
- **Underlying APIs**:
  - `GET /api/v1/repository/resources`
  - `GET /api/v1/repository/resources/{id}`
- **Database & Storage Changes**:
  - Read-only queries against `official_forms`.

---

### Workflow 11: Save Preparation Checklist Progress
- **Classification**: `REAL` (Persistent PostgreSQL checklist storage under forced RLS)
- **Step-by-Step Instructions**:
  1. Navigate to `/app/forms/DOC_001` (or click on any form from `/app/forms`).
  2. In the **Interactive Citizen Checklist**, click the checkbox for an item (e.g., *"Identity Proof Prepared"*).
  3. Refresh the browser page (`F5` or `Ctrl+R`).
- **Expected Results**:
  - The checked item remains checked after the page reloads.
  - Open `/dev/explorer` > **Persistence Inspector** > verify that the completed count is recorded in `citizen_checklist_progress`.
- **Underlying APIs**:
  - `PUT /api/v1/repository/checklists/{id}/progress`
  - `GET /api/v1/repository/checklists/{id}/progress`
- **Database & Storage Changes**:
  - Upsert on `citizen_checklist_progress` table.

---

### Workflow 12: Generate Correction Representation Draft
- **Classification**: `REAL` (Formal petition generation, version archiving, and cryptographic hashing)
- **Step-by-Step Instructions**:
  1. Navigate to `/app/inconsistencies`.
  2. In the **Detected Inconsistencies** card, click **"Draft Formal Petition / Representation"**.
  3. Select document type (e.g. `Identity Correction Request`).
  4. Review generated legal text, citation to official rules, and placeholders.
  5. Edit the explanation field and click **"Save & Confirm Representation"**.
- **Expected Results**:
  - Draft is saved as version 1.0 with a cryptographic SHA-256 content hash.
- **Underlying APIs**:
  - `POST /api/v1/correction-drafts`
  - `POST /api/v1/correction-drafts/{id}/confirm`
- **Database & Storage Changes**:
  - Insert into `correction_drafts` and `correction_draft_versions`.

---

### Workflow 13: Download Attested Document (Ed25519 PKI)
- **Classification**: `REAL` (RFC 8032 Ed25519 digital signature generation)
- **Step-by-Step Instructions**:
  1. In `/app/inconsistencies`, locate the confirmed draft.
  2. Click **"Download Verified Representation (PDF)"**.
  3. Open the downloaded PDF.
- **Expected Results**:
  - The document contains the formal representation text, confirmed demographic fields, and an Ed25519 digital signature attestation footer.
- **Underlying APIs**:
  - `GET /api/v1/correction-drafts/{id}/download?format=pdf`
  - `POST /api/v1/pki/attest/{document_id}`
- **Database & Storage Changes**:
  - Row created in `pki_attestations` recording signature bytes, key ID, and timestamp.

---

### Workflow 14: Administrator Console & Platform Telemetry
- **Classification**: `REAL` (Live platform metrics, user table, catalog synchronization, immutable audit log)
- **Step-by-Step Instructions**:
  1. Open `/dev/explorer` > **Test Accounts** tab.
  2. Click **"Simulate Admin Session (AJAY M)"**.
  3. Navigate to `/admin`.
  4. Inspect the 6 operational metric cards (Users, Uploaded Documents, Detected Discrepancies, Assistant Messages, PKI Attestations, Immutable Audit Events).
  5. Click **"Sync Catalog"** under Official Repository to synchronize forms.
  6. Inspect the **Immutable Audit Trail** section.
- **Expected Results**:
  - Admin Console renders without Access Denied.
  - Metrics accurately reflect real PostgreSQL counts.
  - Non-admin attempts to access `/admin` or `/api/v1/admin/*` are strictly blocked.
- **Underlying APIs**:
  - `GET /api/v1/admin/overview-stats`
  - `GET /api/v1/admin/users`
  - `POST /api/v1/knowledge/admin/forms/sync`
  - `GET /api/v1/admin/system-activity`
- **Database & Storage Changes**:
  - Audit logging of admin actions; database triggers prevent modification or deletion of audit records.
