-- Migration 010: Role Simplification to USER and ADMIN (Officer Role Deprecation)
-- Enforces a strict two-role product model: 'user' and 'admin'.
-- Safely migrates existing 'citizen' accounts to 'user'.
-- Deactivates existing 'officer' accounts for manual review with zero privilege escalation.
-- Drops obsolete officer-specific RLS policies while maintaining strict RLS on all tables.

BEGIN;

-- Step 1: Set migration administrative session context so anti-escalation trigger allows role updates
SET LOCAL app.current_user_role = 'admin';

-- Step 2: Temporarily expand the CHECK constraint to allow 'user' during data migration
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('user', 'citizen', 'officer', 'admin'));

-- Step 3: Safely de-escalate and deactivate any existing officer accounts
-- CRITICAL SECURITY RULE: NEVER escalate officer to admin.
-- We scramble firebase_uid to prevent authentication, append notice to full_name,
-- set role to 'user' (least privilege), and log an immutable audit trail entry.
DO $$
DECLARE
    r RECORD;
    prev_hash_val VARCHAR(64);
    new_hash_val VARCHAR(64);
BEGIN
    FOR r IN SELECT id, email, full_name, firebase_uid FROM users WHERE role = 'officer' LOOP
        -- Query previous audit hash
        SELECT COALESCE(current_hash, 'GENESIS') INTO prev_hash_val
        FROM audit_log ORDER BY created_at DESC, id DESC LIMIT 1;
        
        new_hash_val := encode(digest(
            COALESCE(prev_hash_val, 'GENESIS') || 
            r.id::text || 
            'officer_role_deprecated_account_disabled' || 
            r.id::text || 
            NOW()::text,
            'sha256'
        ), 'hex');

        INSERT INTO audit_log (
            user_id, action, entity_type, entity_id, details, prev_hash, current_hash
        ) VALUES (
            r.id,
            'officer_role_deprecated_account_disabled',
            'user',
            r.id,
            jsonb_build_object(
                'reason', 'Officer role removed from product scope. Account disabled pending manual review.',
                'original_email', r.email,
                'migrated_role', 'user'
            ),
            prev_hash_val,
            new_hash_val
        );

        -- Safely disable the account and de-escalate to 'user'
        UPDATE users
        SET role = 'user',
            firebase_uid = 'disabled_officer_' || firebase_uid,
            full_name = full_name || ' [DEPRECATED OFFICER - MANUAL REVIEW REQUIRED]',
            updated_at = NOW()
        WHERE id = r.id;
    END LOOP;
END $$;

-- Step 4: Migrate all existing 'citizen' accounts to 'user'
UPDATE users
SET role = 'user',
    updated_at = NOW()
WHERE role = 'citizen';

-- Step 5: Tighten the CHECK constraint on users table to enforce strictly 'user' and 'admin'
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('user', 'admin'));
ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user';

-- Step 6: Update provisioning functions to default new accounts to 'user'
CREATE OR REPLACE FUNCTION provision_citizen_user(
    p_firebase_uid TEXT,
    p_email TEXT,
    p_full_name TEXT
)
RETURNS TABLE (
    id UUID,
    firebase_uid VARCHAR,
    email VARCHAR,
    full_name VARCHAR,
    role VARCHAR,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user users%ROWTYPE;
BEGIN
    INSERT INTO users (firebase_uid, email, full_name, role)
    VALUES (p_firebase_uid, p_email, p_full_name, 'user')
    ON CONFLICT ON CONSTRAINT users_firebase_uid_key DO UPDATE
    SET full_name = EXCLUDED.full_name,
        updated_at = NOW()
    RETURNING * INTO v_user;

    RETURN QUERY
    SELECT v_user.id, v_user.firebase_uid, v_user.email, v_user.full_name, v_user.role, v_user.created_at, v_user.updated_at;
END;
$$ LANGUAGE plpgsql;

-- Also create modern alias function provision_user
CREATE OR REPLACE FUNCTION provision_user(
    p_firebase_uid TEXT,
    p_email TEXT,
    p_full_name TEXT
)
RETURNS TABLE (
    id UUID,
    firebase_uid VARCHAR,
    email VARCHAR,
    full_name VARCHAR,
    role VARCHAR,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY SELECT * FROM provision_citizen_user(p_firebase_uid, p_email, p_full_name);
END;
$$ LANGUAGE plpgsql;

-- Step 7: Update RLS policies to align with 'user' and 'admin' roles
-- Drop obsolete officer RLS policies
DROP POLICY IF EXISTS p_users_officer_select ON users;
DROP POLICY IF EXISTS p_documents_officer_select ON documents;
DROP POLICY IF EXISTS p_conflicts_officer_select ON conflicts;
DROP POLICY IF EXISTS p_cases_officer ON cases;
DROP POLICY IF EXISTS p_evidence_officer ON case_evidence;
DROP POLICY IF EXISTS p_audit_officer_select ON audit_log;
DROP POLICY IF EXISTS p_signatures_officer ON digital_signatures;
DROP POLICY IF EXISTS p_review_req_officer ON case_review_requests;
DROP POLICY IF EXISTS p_attestations_officer ON document_attestations;
DROP POLICY IF EXISTS p_verifications_officer ON attestation_verifications;

-- Update document_attestations user select policy
DROP POLICY IF EXISTS p_attestations_citizen_select ON document_attestations;
DROP POLICY IF EXISTS p_attestations_user_select ON document_attestations;
CREATE POLICY p_attestations_user_select ON document_attestations
    FOR SELECT
    TO consolith_app
    USING (
        (current_app_user_role() IN ('user', 'citizen')) AND
        (citizen_id = current_app_user_id())
    );

-- Update attestation_verifications user policies
DROP POLICY IF EXISTS p_verifications_citizen_insert ON attestation_verifications;
DROP POLICY IF EXISTS p_verifications_user_insert ON attestation_verifications;
CREATE POLICY p_verifications_user_insert ON attestation_verifications
    FOR INSERT
    TO consolith_app
    WITH CHECK (
        (current_app_user_role() IN ('user', 'citizen')) AND
        (verifier_id = current_app_user_id())
    );

DROP POLICY IF EXISTS p_verifications_citizen_select ON attestation_verifications;
DROP POLICY IF EXISTS p_verifications_user_select ON attestation_verifications;
CREATE POLICY p_verifications_user_select ON attestation_verifications
    FOR SELECT
    TO consolith_app
    USING (
        (current_app_user_role() IN ('user', 'citizen')) AND
        (
            verifier_id = current_app_user_id() OR
            attestation_id IN (
                SELECT id FROM document_attestations WHERE citizen_id = current_app_user_id()
            )
        )
    );

-- Ensure p_attestations_admin remains authoritative
DROP POLICY IF EXISTS p_attestations_admin ON document_attestations;
CREATE POLICY p_attestations_admin ON document_attestations
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

-- Ensure p_verifications_admin remains authoritative
DROP POLICY IF EXISTS p_verifications_admin ON attestation_verifications;
CREATE POLICY p_verifications_admin ON attestation_verifications
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

-- Step 8: Ensure default Admin signing key exists for platform attestation
INSERT INTO signing_keys (
    id, key_id, public_key, fingerprint, algorithm, purpose, status, valid_from, valid_until
) VALUES (
    '6c42e898-05f6-4e1d-99fa-85cd0a22d532',
    'convelina-admin-key-2026-v1',
    'Z0P8uliZM6jps5S+T8vzvNOUi+G6TzBwQmPNuuUslVI=',
    '9535711fd934bae3a73b40c0d8ed307c44eb6ab62c041f27f8f4615c4bc4cad3',
    'Ed25519',
    'document_attestation',
    'active',
    NOW(),
    NOW() + INTERVAL '2 years'
) ON CONFLICT (key_id) DO NOTHING;

COMMIT;
