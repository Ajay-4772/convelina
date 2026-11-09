# CONVELINA P3H.8 — Application State Architecture & Persistence Inventory

## Executive Summary

During milestone **P3H.8**, an architectural audit of the CONVELINA application state was conducted to identify in-memory transients, verify database persistence invariants, and ensure that critical citizen workflows survive browser refreshes and session disruptions.

Prior to P3H.8, citizen checklist preparation progress on statutory forms (e.g. `/app/forms/[formId]`) was maintained purely in React component state (`useState`), meaning any page navigation or browser reload wiped all preparation progress. In P3H.8, this was replaced with end-to-end database persistence in PostgreSQL backed by forced Row-Level Security.

---

## 1. State Classification & Persistence Inventory

| State Category | Storage Layer | Persistence Invariant | RLS Enforcement | Survives Reload? | Audit Logged? |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Citizen Checklists** | PostgreSQL (`citizen_checklist_items`) | Persistent per citizen, procedure & item | Yes (Forced) | **Yes** | Yes (`UPDATE_CHECKLIST_PROGRESS`) |
| **Citizen Documents** | PostgreSQL (`documents`) + Local Temp File | Metadata & extracted fields persistent; raw file purged after OCR | Yes (Forced) | **Yes** | Yes (`UPLOAD_DOCUMENT`) |
| **Detected Conflicts** | PostgreSQL (`conflicts`) | Deterministic field discrepancies & resolution links | Yes (Forced) | **Yes** | Yes (`DETECT_CONFLICT`) |
| **Correction Cases** | PostgreSQL (`cases`) | Citizen verification cases & officer assignment | Yes (Forced) | **Yes** | Yes (`CREATE_CASE`, `UPDATE_CASE`) |
| **Audit Trail** | PostgreSQL (`audit_log`) | Cryptographic SHA-256 chain; Append-only immutability | Yes (Forced) | **Yes** | Self-evident |
| **Assistant Chat** | PostgreSQL (`assistant_conversations`, `assistant_messages`) | Multi-turn conversational history & citations | Yes (Forced) | **Yes** | Yes (`NEW_CONVERSATION`, `SEND_MESSAGE`) |
| **Ed25519 Signatures** | PostgreSQL (`verification_signatures`) | Digital signatures sealing resolution documents | Yes (Forced) | **Yes** | Yes (`SIGN_VERIFICATION`) |
| **Statutory Knowledge**| Vector DB (Qdrant) + BM25 JSON Manifests | Versioned corpus of official government documents | Public / Read-Only | **Yes** | Yes (Ingestion audit) |
| **Ephemeral UI Filters** | Browser Memory (`useState`) | Category filter, search query string, modal visibility | N/A | No (Ephemeral) | No |

---

## 2. In-Memory Checklist Remediation

### 2.1 Problem Analysis
In `frontend/src/app/app/forms/[formId]/page.tsx`, checklist completion was tracked with:
```typescript
const [completedItems, setCompletedItems] = useState<Record<string, boolean>>({});
```
If a citizen checked off statutory requirements (e.g., obtaining a birth certificate, Gazette notification, or photo identity document) and reloaded the page, all progress was reset to empty.

### 2.2 Implemented Persistent Architecture
1. **Database Schema (`021_citizen_checklist_progress.sql`)**:
   Table `citizen_checklist_items` stores `(user_id, procedure_id, item_id, is_completed, notes, confirmed_at)`.
2. **Backend Domain Service (`backend/app/services/checklist_service.py`)**:
   - `get_user_progress(db, user_id, procedure_id)`: Fetches persistent items under RLS.
   - `update_user_item_progress(db, user_id, procedure_id, item_id, is_completed)`: Updates or inserts completion state, enforces statutory item ID validation, and logs cryptographic audit event before committing.
3. **API Endpoints (`backend/app/routers/repository.py`)**:
   - `GET /api/v1/repository/checklists/{procedure_id}/progress`
   - `PUT /api/v1/repository/checklists/{procedure_id}/progress`
   - `GET /api/v1/repository/resources/{resource_id}/checklist-progress`
4. **Frontend Integration (`frontend/src/app/app/forms/[formId]/page.tsx` & `frontend/src/lib/api.ts`)**:
   - Component loads remote state on mount via `fetchResourceChecklistProgress(resourceId)`.
   - On item click, calls `updateChecklistItemProgress(procedureId, itemId, checked)` with optimistic UI updates and error reversion.

---

## 3. Browser Refresh & Persistence Verification

A dedicated end-to-end integration test (`backend/tests/test_p3h8_database_persistence.py::test_checklist_persistence_and_isolation`) verified that:
1. Citizen A marks requirement `REQ_AAD_NAME_INITIAL_EXPANSION_04` as completed (`PUT` returns 200).
2. Simulated browser refresh via subsequent `GET` query confirms the requirement is present in `completed_items`.
3. An unauthenticated or secondary citizen (Citizen B) querying the same procedure receives an empty checklist, proving strict RLS isolation.
