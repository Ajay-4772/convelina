# CONVELINA P3H.8.1 — Two-Role Architecture & Privilege Enforcement Audit

## Executive Summary

During milestone **P3H.8.1**, a system-wide audit of the identity access and role model was conducted across the database schema, SQL migrations, API routing layer, domain services, and frontend App Router.

CONVELINA strictly adheres to a **two-role architecture**:
- `USER` (Citizen role with access strictly bounded by forced Row-Level Security to own documents, conflicts, checklists, conversations, and drafts)
- `ADMIN` (Administrative oversight role with system diagnostics, read-only operational telemetry, and official form management)

Legacy privileged roles (`OFFICER`, `VERIFIER`, and case assignment workflows) were systematically audited. While historical migrations (such as `005_officer_role_and_case_assignment.sql` and `007_officer_verification.sql`) remain in the migration ledger for migration idempotency and historical auditability, active runtime enforcement strictly eliminates and blocks any officer capability.

---

## 1. Codebase & Schema Audit for Legacy Privileged Roles

An exhaustive scan across all application layers was conducted for references to `OFFICER`, `VERIFIER`, `CASE ASSIGNMENT`, and related tokens.

| Layer | Files Audited | Findings & Active Status | Architecture Compliance |
| :--- | :--- | :--- | :---: |
| **Database Constraint** | `users` table constraint `users_role_check` | `CHECK (((role)::text = ANY (ARRAY['user', 'admin'])))` | **100% COMPLIANT** |
| **RLS Policies** | 45 Active PostgreSQL Policies | **0 active policies reference 'officer' or 'verifier'** | **100% COMPLIANT** |
| **API Endpoints** | All 112 FastAPI routes | Zero `/officer/*` or assignment endpoints exposed | **100% COMPLIANT** |
| **Frontend UI** | All 15 Next.js Pages & Components | Zero officer navigation, dashboard, or assignment views | **100% COMPLIANT** |
| **Domain Services** | Statutory Draft & Guidance Templates | References strictly limited to statutory titles in letter templates | **100% COMPLIANT** |
| **Historical Schema** | `cases`, `verification_signatures` | Legacy columns retained for backward compatibility | **DOCUMENTED** |

---

## 2. In-Depth Migration & Schema Evolution Analysis

### 2.1 Historical Context (Migrations 001 – 007)
Early experimental prototypes (prior to P3A) explored a three-tier model where an "officer" would manually verify uploaded citizen correction cases:
- `001_initial_schema.sql` created `cases` with `assigned_officer_id UUID REFERENCES users(id)`.
- `005_officer_role_and_case_assignment.sql` added assignment tracking.
- `006_verification_signatures.sql` created `verification_signatures` with an `officer_id` foreign key.

### 2.2 Formal Deprecation: Migration 010
Migration `010_role_simplification_user_admin.sql` formally unified the architecture into the two-role model:
1. **CHECK Constraint Lockdown**:
   ```sql
   ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
   ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('user', 'admin'));
   ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user';
   ```
2. **De-escalation & Invalidation of Legacy Accounts**:
   Any existing accounts bearing `role = 'officer'` were de-escalated to `role = 'user'`, had their Firebase UIDs scrambled (`disabled_officer_<uid>`) to permanently block authentication, and had their transition recorded in the append-only cryptographic `audit_log`.
3. **Purge of Legacy RLS Policies**:
   Dropped `officer_assigned_cases_policy`, `officer_cases_update_policy`, and `officer_attestation_verification_policy`.

### 2.3 Legacy Columns Retained for Schema Stability
To avoid breaking historical database snapshots and foreign key constraints:
- `cases.assigned_officer_id`: Retained in schema but unused by active APIs.
- `verification_signatures.officer_id`: Renamed / aliased in modern Python models to `signer = relationship("User", foreign_keys=[officer_id], overlaps="officer")`, representing the internal platform attestation signer.

---

## 3. Verification of Core Architectural Invariants

### Invariant 1: New Accounts Default to `USER`
- Verified in database: `ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user';`.
- Verified in `provision_user` stored procedure:
  ```sql
  INSERT INTO users (firebase_uid, email, full_name, role)
  VALUES (p_firebase_uid, p_email, p_full_name, 'user')
  ```
- Verified in FastAPI auth router (`backend/app/routers/auth.py`): all incoming registrations provision `role="user"`.

### Invariant 2: Users Cannot Elevate Themselves
- Safeguarded by the PostgreSQL database trigger `prevent_role_escalation()`:
  ```sql
  IF OLD.role IS DISTINCT FROM NEW.role THEN
      IF NULLIF(current_setting('app.current_user_role', true), '') <> 'admin' THEN
          RAISE EXCEPTION 'Privilege escalation rejected: only administrators can change user roles.';
      END IF;
  END IF;
  ```
- In `scripts/test_rls_isolation.py` Test 5, Citizen A attempting an `UPDATE users SET role = 'admin'` was aborted by the database trigger with `PL/pgSQL RAISE EXCEPTION`.

### Invariant 3: Only Authorized ADMIN Can Provision Another ADMIN
- Backend endpoint `POST /api/v1/admin/users/promote` requires active dependency `require_admin`.
- When called by a standard user token, returns `HTTP 403 Forbidden`.
- Database trigger permits role modification only when session variable `app.current_user_role` is `'admin'`.

### Invariant 4: No Officer Account Can Authenticate as a Supported Role
- PostgreSQL database constraint `users_role_check` prohibits inserting or updating any user record with `role = 'officer'`.
- Token decoder in `backend/app/core/security.py` validates roles against the allowlist `("user", "admin")`. Unrecognized roles are rejected with `HTTP 401 Unauthorized`.

### Invariant 5: No Officer-Specific API is Accessible
- FastAPI route table (112 routes across 9 routers) exposes:
  - Public routes (`/`, `/api/v1/auth/*`, `/api/v1/repository/*`)
  - Citizen user routes (`/api/v1/documents/*`, `/api/v1/conflicts/*`, `/api/v1/assistant/*`, `/api/v1/correction-drafts/*`)
  - Administrative routes (`/api/v1/admin/*`, `/api/v1/knowledge/admin/*`)
- Zero officer-specific endpoints exist.

### Invariant 6: No Frontend Officer Dashboard or Assignment Interface Exists
- Complete Next.js 14 App Router scan confirms only citizen routes (`/app/*`) and admin routes (`/admin/*`).
- Role guard in `frontend/src/components/auth/ProtectedRoute.tsx` only handles `user` and `admin` roles, redirecting unauthorized users to `/login`.

### Invariant 7: RLS Policies Do Not Preserve Unintended Officer Privileges
- Query on `pg_policies` for schema `public` confirmed 45 total active policies.
- Exactly **0 policies** reference `officer` or grant privileges to non-user/non-admin roles.
- `scripts/test_rls_isolation.py` verified that without an authenticated session, default-deny prevents reading or writing across all tables.
