# P3H.11: Reliability, Fault Resilience & Restart Persistence Audit

## Executive Overview

This report documents the reliability, failure resilience, and persistent storage audit of the CONVELINA system under milestone P3H.11.

A resilient government assistance system must withstand container restarts, network partitions, malformed user inputs, and unexpected pipeline crashes without data corruption, ghost records, or memory leaks.

---

## 1. Container Restart & Volume Persistence

The CONVELINA stack utilizes Docker named volumes for both its relational database and vector engine:
- PostgreSQL 16: `consolin_postgres_data`
- Qdrant Vector Database: `consolin_qdrant_data`

### 1.1 Qdrant Restart Verification (`scripts/test_qdrant_restart_persistence.py`)
- **Objective**: Verify that Qdrant collections (`consolith_knowledge` and `consolith_forms`) and their indexed vector points persist across container restarts.
- **Procedure**:
  1. Count active points pre-restart:
     - `consolith_knowledge`: 34 points (vectors: 384-dim, cosine metric).
     - `consolith_forms`: 6 points (vectors: 384-dim, cosine metric).
  2. Execute container restart: `docker restart convelina-qdrant`.
  3. Wait for HTTP readiness on `http://127.0.0.1:6333/readyz`.
  4. Query collection telemetry post-restart.
- **Result**:
  - `consolith_knowledge`: 34 points retained (**100% data preservation**).
  - `consolith_forms`: 6 points retained (**100% data preservation**).
  - Zero dropped points or index rebuilds required.

### 1.2 PostgreSQL 16 Restart & Migration Durability (`test_p3h8_database_persistence.py`)
- **Objective**: Verify that all 21 database migrations, RLS policies, custom PL/pgSQL triggers, and citizen entities survive container restart.
- **Execution**: Verified via `test_runtime_health_diagnostics`:
  - `database_migrations.applied_count`: 21 / 21 applied.
  - `latest_applied`: `021_citizen_checklist_progress.sql`.
  - Forced RLS active across all tables.

---

## 2. Failure Handling & Input Fuzzing

### 2.1 File Validation & Rejection (`test_p3h11_confirmation_security.py`)

| Failure Condition | Attack Payload | Expected Handling | Observed Behavior | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Forbidden Extension** | `malicious_script.exe` | HTTP 400 Bad Request; file not processed | Rejected with *"File type .exe not supported"* | **PASSED** |
| **Corrupted Image Content** | Plaintext bytes named `fake_card.png` | OCR engine fails safely; returns empty extraction or HTTP 400 | Graceful handling; no crash | **PASSED** |
| **Oversized Upload** | 12 MB binary file (> 10 MB limit) | HTTP 400 Bad Request before processing | Rejected with *"File size exceeds 10MB limit"* | **PASSED** |
| **Client Field Injection** | Body with `is_user_confirmed: true` | Server ignores client flag | `is_user_confirmed` initialized as `False` | **PASSED** |
| **Cross-Tenant Attack** | Citizen B attempts to confirm Citizen A's doc | HTTP 404 Not Found (RLS isolation) | HTTP 404 returned; Citizen A untouched | **PASSED** |

### 2.2 Ephemeral Scratch File Cleanup on Failure
- When an upload encounters an error during OCR or database persistence, the scratch file must still be unlinked.
- The router wraps file extraction in a Python `try...finally` block:
  ```python
  scratch_path = Path(tempfile.gettempdir()) / f"convelina_ocr_{uuid.uuid4()}{ext}"
  try:
      with open(scratch_path, "wb") as f:
          f.write(file_bytes)
      extracted_data = await run_ocr_pipeline(scratch_path)
  finally:
      if scratch_path.exists():
          scratch_path.unlink(missing_ok=True)
  ```
- **Audit Verification**: Ephemeral directory was inspected after failed uploads; 0 orphaned scratch files remained.

### 2.3 PostgreSQL Connection-Pooling & Session Reset Traps
- **Vulnerability**: Connection poolers (e.g., PgBouncer) reuse database connections across requests. If a previous request sets a session variable (e.g. `SET LOCAL app.current_user_id = '...'`), an unauthenticated request might inherit that identity if not cleared.
- **Defense**:
  1. Every session starts with an explicit reset.
  2. Queries utilize `NULLIF(current_setting('app.current_user_id', true), '')::uuid`.
  3. Setting an empty string `''` safely casts to `NULL` rather than throwing a PostgreSQL UUID syntax error (`invalid input syntax for type uuid: ""`).
- **Verification**: `test_rls_isolation.py` Test 9 verified that empty session settings do not crash the database connection.

---

## 3. Verification Sign-Off

The storage infrastructure, failure handling routines, and ephemeral cleanup mechanisms demonstrate high fault resilience and zero data loss across container lifecycle events.

