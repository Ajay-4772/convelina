# CONVELINA P3H.8 — Migration Validation & Schema Evolution Report

## Executive Summary

This report documents the exhaustive validation of all database migrations from `001` through `021` for the CONVELINA identity platform.

Prior to P3H.8, migration execution had halted due to a unique email constraint conflict in migration `019`. During P3H.8:
1. The unique email conflict was resolved via data sanitation of legacy synthetic test rows.
2. Migration `019_unique_user_email_and_auth_hardening.sql` was applied cleanly.
3. Migration `020_p3h6_repository_provenance_and_checklists.sql` was applied cleanly.
4. Migration `021_citizen_checklist_progress.sql` was authored, reviewed, and applied, introducing persistent citizen checklist progress under forced Row-Level Security (RLS).
5. All 21 migrations were verified in `schema_migrations` with zero pending migrations.

---

## 1. Migration Inventory (001 – 021)

| # | Migration File | Description | Execution Status | RLS Hardening Verified |
| :- | :--- | :--- | :--- | :--- |
| **001** | `001_initial_schema.sql` | Base schema: users, documents, conflicts, cases, audit_log | Applied | Forced RLS Enabled |
| **002** | `002_rls_policies.sql` | Core RLS policies, `set_config` session context | Applied | User isolation verified |
| **003** | `003_audit_triggers.sql` | Immutability triggers on `audit_log`, SHA-256 chaining | Applied | Block UPDATE/DELETE |
| **004** | `004_fix_rls_recursion.sql` | Avoid infinite recursion in role checks | Applied | Direct session checks |
| **005** | `005_officer_role_and_case_assignment.sql` | Officer role permissions and assignment RLS | Applied | Assignment-scoped RLS |
| **006** | `006_verification_signatures.sql` | Cryptographic Ed25519 verification signatures table | Applied | Immutability triggers |
| **007** | `007_admin_role_escalation_fix.sql` | Prevent self-promotion to admin via triggers | Applied | Exception on role escalation |
| **008** | `008_strict_rls_enforcement.sql` | `FORCE ROW LEVEL SECURITY` on all base tables | Applied | Bypass prevention |
| **009** | `009_user_attestation_records.sql` | Statutory legal attestations and declarations | Applied | Attestation isolation |
| **010** | `010_drop_deprecated_verifier.sql` | Remove legacy verifier role, consolidate to officer/admin | Applied | Deprecated role reject |
| **011** | `011_conflict_resolutions.sql` | Conflict resolution action history and tracking | Applied | Citizen isolation |
| **012** | `012_system_config_table.sql` | System configuration key-value storage | Applied | Read-only to app |
| **013** | `013_qdrant_sync_tracking.sql` | Vector ingestion tracking and chunk hashes | Applied | Admin controlled |
| **014** | `014_assistant_conversations.sql` | Multi-turn RAG assistant conversations & messages | Applied | User isolation |
| **015** | `015_audit_hash_chain_function.sql` | Cryptographic hash validation PL/pgSQL function | Applied | Cryptographic integrity |
| **016** | `016_document_metadata_indexes.sql` | Performance indexes on JSONB fields and document hashes | Applied | GIN indexes |
| **017** | `017_p3e_admin_schema.sql` | Administrative platform monitoring & metric tables | Applied | Admin-only access |
| **018** | `018_p3f_audit_and_indexes.sql` | Audit logging speedups, connection pooling safe casts | Applied | `NULLIF(..., '')::uuid` |
| **019** | `019_unique_user_email_and_auth_hardening.sql` | Case-insensitive unique index `idx_users_lower_email_unique` | Applied | Unique email enforcement |
| **020** | `020_p3h6_repository_provenance_and_checklists.sql` | Repository metadata, provenance tracking & doc links | Applied | Provenance verified |
| **021** | `021_citizen_checklist_progress.sql` | Persistent citizen checklist progress & statutory requirements | Applied | Forced RLS & Audit trail |

---

## 2. Remediation of Migration 019 Defect

### 2.1 Issue Identified
Running `scripts/run_migrations.py` initially failed on `019_unique_user_email_and_auth_hardening.sql`:
```text
Fatal error during migration execution: could not create unique index "idx_users_lower_email_unique": 
Key (lower(email::text))=(citizen) is duplicated.
```
Investigation revealed that legacy synthetic tests had inserted two mock users with the exact duplicate string `'citizen'`.

### 2.2 Corrective Sanitation Script
A migration pre-flight sanitation script (`scripts/resolve_duplicates.py`) was executed:
```python
db.execute(text("UPDATE users SET email = 'upload_tester@example.com' WHERE email = 'citizen' AND id = 'b0000000-0000-0000-0000-000000000001'"))
db.execute(text("UPDATE users SET email = 'other_citizen@example.com' WHERE email = 'citizen' AND id = 'b0000000-0000-0000-0000-000000000002'"))
db.commit()
```
Following this cleanup, migration 019 executed cleanly, creating the case-insensitive unique index `idx_users_lower_email_unique`.

---

## 3. Authoring and Structure of Migration 021

Migration `021_citizen_checklist_progress.sql` was authored to eliminate transient React in-memory state and persist checklist preparation across browser sessions:

```sql
CREATE TABLE IF NOT EXISTS citizen_checklist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    procedure_id VARCHAR(100) NOT NULL,
    item_id VARCHAR(100) NOT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_procedure_item UNIQUE (user_id, procedure_id, item_id)
);

CREATE INDEX IF NOT EXISTS idx_checklist_user_procedure 
ON citizen_checklist_items(user_id, procedure_id);

ALTER TABLE citizen_checklist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE citizen_checklist_items FORCE ROW LEVEL SECURITY;

CREATE POLICY citizen_checklist_user_isolation 
ON citizen_checklist_items
FOR ALL
USING (
    user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
    OR NULLIF(current_setting('app.current_user_role', true), '') = 'admin'
)
WITH CHECK (
    user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
    OR NULLIF(current_setting('app.current_user_role', true), '') = 'admin'
);

GRANT SELECT, INSERT, UPDATE, DELETE ON citizen_checklist_items TO consolith_app;
```

---

## 4. Verification Checkpoint

Automated execution of `scripts/run_migrations.py` confirmed:
```text
Found 21 migration files in backend/migrations.
Current applied migrations in database: 21
No pending migrations to apply. Database is fully up to date!
```
The health check endpoint (`/health`) reports:
```json
"database_migrations": {
    "status": "up",
    "applied_count": 21,
    "latest_applied": "021_citizen_checklist_progress.sql"
}
```
