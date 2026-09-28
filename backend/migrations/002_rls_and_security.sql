-- Migration 002: Row-Level Security (RLS), Role Scoping, and Security Triggers

-- 1. Create Dedicated Non-Superuser Application Role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'consolith_app') THEN
        CREATE ROLE consolith_app WITH LOGIN PASSWORD 'consolith_secure_app_pw' NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
    END IF;
END
$$;

-- Grant permissions to application role
GRANT USAGE ON SCHEMA public TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO consolith_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO consolith_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO consolith_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO consolith_app;

-- 2. Safe Session Context Helper Functions
-- Connection pooling safe: handles empty strings and nulls safely without UUID parse exceptions
CREATE OR REPLACE FUNCTION current_app_user_id() RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_user_id', true), '')::uuid;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION current_app_user_role() RETURNS TEXT AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_user_role', true), '');
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- 3. Privilege Escalation Prevention Trigger on `users`
-- Prevents citizens or non-admins from changing their role to 'admin' or 'officer'
CREATE OR REPLACE FUNCTION prevent_role_escalation()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.role IS DISTINCT FROM OLD.role THEN
        IF current_app_user_role() != 'admin' THEN
            RAISE EXCEPTION 'Privilege escalation rejected: only administrators can change user roles.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_role_escalation ON users;
CREATE TRIGGER trg_prevent_role_escalation
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION prevent_role_escalation();

-- 4. Audit Log Immutability Trigger
-- Enforces true append-only audit trail: any UPDATE or DELETE is rejected
CREATE OR REPLACE FUNCTION block_audit_log_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log is append-only. Modification or deletion of audit records is strictly prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_block_audit_log_mutation ON audit_log;
CREATE TRIGGER trg_block_audit_log_mutation
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH STATEMENT
EXECUTE FUNCTION block_audit_log_mutation();

-- 5. Enable and FORCE Row-Level Security on all user-data tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;

ALTER TABLE conflicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE conflicts FORCE ROW LEVEL SECURITY;

ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE cases FORCE ROW LEVEL SECURITY;

ALTER TABLE case_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_evidence FORCE ROW LEVEL SECURITY;

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log FORCE ROW LEVEL SECURITY;

ALTER TABLE digital_signatures ENABLE ROW LEVEL SECURITY;
ALTER TABLE digital_signatures FORCE ROW LEVEL SECURITY;

-- 6. Define Policies for `users`
DROP POLICY IF EXISTS p_users_admin ON users;
CREATE POLICY p_users_admin ON users
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_users_citizen ON users;
CREATE POLICY p_users_citizen ON users
    FOR ALL
    TO consolith_app
    USING (id = current_app_user_id())
    WITH CHECK (id = current_app_user_id());

DROP POLICY IF EXISTS p_users_officer_select ON users;
CREATE POLICY p_users_officer_select ON users
    FOR SELECT
    TO consolith_app
    USING (
        current_app_user_role() = 'officer' AND (
            id = current_app_user_id() OR
            id IN (SELECT citizen_id FROM cases WHERE assigned_officer_id = current_app_user_id())
        )
    );

-- 7. Define Policies for `documents`
DROP POLICY IF EXISTS p_documents_admin ON documents;
CREATE POLICY p_documents_admin ON documents
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_documents_citizen ON documents;
CREATE POLICY p_documents_citizen ON documents
    FOR ALL
    TO consolith_app
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

DROP POLICY IF EXISTS p_documents_officer_select ON documents;
CREATE POLICY p_documents_officer_select ON documents
    FOR SELECT
    TO consolith_app
    USING (
        current_app_user_role() = 'officer' AND
        user_id IN (SELECT citizen_id FROM cases WHERE assigned_officer_id = current_app_user_id())
    );

-- 8. Define Policies for `conflicts`
DROP POLICY IF EXISTS p_conflicts_admin ON conflicts;
CREATE POLICY p_conflicts_admin ON conflicts
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_conflicts_citizen ON conflicts;
CREATE POLICY p_conflicts_citizen ON conflicts
    FOR ALL
    TO consolith_app
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

DROP POLICY IF EXISTS p_conflicts_officer_select ON conflicts;
CREATE POLICY p_conflicts_officer_select ON conflicts
    FOR SELECT
    TO consolith_app
    USING (
        current_app_user_role() = 'officer' AND
        user_id IN (SELECT citizen_id FROM cases WHERE assigned_officer_id = current_app_user_id())
    );

-- 9. Define Policies for `cases`
DROP POLICY IF EXISTS p_cases_admin ON cases;
CREATE POLICY p_cases_admin ON cases
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_cases_citizen ON cases;
CREATE POLICY p_cases_citizen ON cases
    FOR ALL
    TO consolith_app
    USING (citizen_id = current_app_user_id())
    WITH CHECK (citizen_id = current_app_user_id());

DROP POLICY IF EXISTS p_cases_officer ON cases;
CREATE POLICY p_cases_officer ON cases
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'officer' AND assigned_officer_id = current_app_user_id())
    WITH CHECK (current_app_user_role() = 'officer' AND assigned_officer_id = current_app_user_id());

-- 10. Define Policies for `case_evidence`
DROP POLICY IF EXISTS p_evidence_admin ON case_evidence;
CREATE POLICY p_evidence_admin ON case_evidence
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_evidence_citizen ON case_evidence;
CREATE POLICY p_evidence_citizen ON case_evidence
    FOR ALL
    TO consolith_app
    USING (case_id IN (SELECT id FROM cases WHERE citizen_id = current_app_user_id()))
    WITH CHECK (case_id IN (SELECT id FROM cases WHERE citizen_id = current_app_user_id()));

DROP POLICY IF EXISTS p_evidence_officer ON case_evidence;
CREATE POLICY p_evidence_officer ON case_evidence
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'officer' AND case_id IN (SELECT id FROM cases WHERE assigned_officer_id = current_app_user_id()))
    WITH CHECK (current_app_user_role() = 'officer' AND case_id IN (SELECT id FROM cases WHERE assigned_officer_id = current_app_user_id()));

-- 11. Define Policies for `audit_log`
DROP POLICY IF EXISTS p_audit_admin ON audit_log;
CREATE POLICY p_audit_admin ON audit_log
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_audit_insert_auth ON audit_log;
CREATE POLICY p_audit_insert_auth ON audit_log
    FOR INSERT
    TO consolith_app
    WITH CHECK (current_app_user_id() IS NOT NULL);

DROP POLICY IF EXISTS p_audit_citizen_select ON audit_log;
CREATE POLICY p_audit_citizen_select ON audit_log
    FOR SELECT
    TO consolith_app
    USING (user_id = current_app_user_id());

DROP POLICY IF EXISTS p_audit_officer_select ON audit_log;
CREATE POLICY p_audit_officer_select ON audit_log
    FOR SELECT
    TO consolith_app
    USING (
        current_app_user_role() = 'officer' AND (
            user_id = current_app_user_id() OR
            entity_id IN (SELECT id FROM cases WHERE assigned_officer_id = current_app_user_id())
        )
    );

-- 12. Define Policies for `digital_signatures`
DROP POLICY IF EXISTS p_signatures_admin ON digital_signatures;
CREATE POLICY p_signatures_admin ON digital_signatures
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_signatures_citizen_select ON digital_signatures;
CREATE POLICY p_signatures_citizen_select ON digital_signatures
    FOR SELECT
    TO consolith_app
    USING (case_id IN (SELECT id FROM cases WHERE citizen_id = current_app_user_id()));

DROP POLICY IF EXISTS p_signatures_officer ON digital_signatures;
CREATE POLICY p_signatures_officer ON digital_signatures
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'officer' AND officer_id = current_app_user_id())
    WITH CHECK (current_app_user_role() = 'officer' AND officer_id = current_app_user_id());
