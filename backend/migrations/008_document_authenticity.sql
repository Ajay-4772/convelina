-- ==============================================================================
-- Consolith Migration 008: Document Authenticity, Ed25519 PKI & Attestations
-- ==============================================================================

-- 1. Create `signing_keys` table
CREATE TABLE IF NOT EXISTS signing_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_id VARCHAR(64) UNIQUE NOT NULL,
    public_key VARCHAR(128) NOT NULL,
    fingerprint VARCHAR(64) NOT NULL,
    algorithm VARCHAR(20) NOT NULL DEFAULT 'Ed25519',
    purpose VARCHAR(100) NOT NULL DEFAULT 'document_attestation',
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'revoked', 'expired')),
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revocation_reason TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signing_keys_key_id ON signing_keys(key_id);
CREATE INDEX IF NOT EXISTS idx_signing_keys_status ON signing_keys(status);
CREATE INDEX IF NOT EXISTS idx_signing_keys_fingerprint ON signing_keys(fingerprint);

-- 2. Create `document_attestations` table
CREATE TABLE IF NOT EXISTS document_attestations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
    correction_draft_id UUID REFERENCES correction_drafts(id) ON DELETE SET NULL,
    citizen_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    officer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    document_type VARCHAR(50) NOT NULL,
    document_fingerprint VARCHAR(64) NOT NULL,
    signing_key_id UUID NOT NULL REFERENCES signing_keys(id) ON DELETE RESTRICT,
    key_id VARCHAR(64) NOT NULL,
    canonical_payload JSONB NOT NULL,
    signature VARCHAR(256) NOT NULL,
    algorithm VARCHAR(20) NOT NULL DEFAULT 'Ed25519',
    status VARCHAR(20) NOT NULL DEFAULT 'valid' CHECK (status IN ('valid', 'revoked', 'expired')),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_attestations_doc ON document_attestations(document_id);
CREATE INDEX IF NOT EXISTS idx_attestations_case ON document_attestations(case_id);
CREATE INDEX IF NOT EXISTS idx_attestations_citizen ON document_attestations(citizen_id);
CREATE INDEX IF NOT EXISTS idx_attestations_officer ON document_attestations(officer_id);
CREATE INDEX IF NOT EXISTS idx_attestations_fingerprint ON document_attestations(document_fingerprint);

-- 3. Create `attestation_verifications` table
CREATE TABLE IF NOT EXISTS attestation_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attestation_id UUID REFERENCES document_attestations(id) ON DELETE CASCADE,
    verifier_id UUID REFERENCES users(id) ON DELETE SET NULL,
    verification_status VARCHAR(30) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verifications_attestation ON attestation_verifications(attestation_id);
CREATE INDEX IF NOT EXISTS idx_verifications_verifier ON attestation_verifications(verifier_id);

-- 4. Enable and Force Row Level Security (RLS)
ALTER TABLE signing_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE signing_keys FORCE ROW LEVEL SECURITY;

ALTER TABLE document_attestations ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_attestations FORCE ROW LEVEL SECURITY;

ALTER TABLE attestation_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE attestation_verifications FORCE ROW LEVEL SECURITY;

-- 5. Policies for `signing_keys`
-- Anyone authenticated can view public keys (public by definition for verification)
DROP POLICY IF EXISTS p_signing_keys_select ON signing_keys;
CREATE POLICY p_signing_keys_select ON signing_keys
    FOR SELECT
    TO consolith_app
    USING (true);

-- Only Admin can insert, update, or revoke keys
DROP POLICY IF EXISTS p_signing_keys_admin_mod ON signing_keys;
CREATE POLICY p_signing_keys_admin_mod ON signing_keys
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

-- 6. Policies for `document_attestations`
-- Admin: full management access
DROP POLICY IF EXISTS p_attestations_admin ON document_attestations;
CREATE POLICY p_attestations_admin ON document_attestations
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

-- Officer: can view and create attestations they sign, or for cases assigned to them
DROP POLICY IF EXISTS p_attestations_officer ON document_attestations;
CREATE POLICY p_attestations_officer ON document_attestations
    FOR ALL
    TO consolith_app
    USING (
        current_app_user_role() = 'officer' AND (
            officer_id = current_app_user_id() OR
            case_id IN (SELECT id FROM cases WHERE assigned_officer_id = current_app_user_id())
        )
    )
    WITH CHECK (
        current_app_user_role() = 'officer' AND officer_id = current_app_user_id()
    );

-- Citizen: can only view attestations for their own records
DROP POLICY IF EXISTS p_attestations_citizen_select ON document_attestations;
CREATE POLICY p_attestations_citizen_select ON document_attestations
    FOR SELECT
    TO consolith_app
    USING (
        current_app_user_role() = 'citizen' AND citizen_id = current_app_user_id()
    );

-- 7. Policies for `attestation_verifications`
DROP POLICY IF EXISTS p_verifications_admin ON attestation_verifications;
CREATE POLICY p_verifications_admin ON attestation_verifications
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_verifications_officer ON attestation_verifications;
CREATE POLICY p_verifications_officer ON attestation_verifications
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'officer')
    WITH CHECK (current_app_user_role() = 'officer');

DROP POLICY IF EXISTS p_verifications_citizen_select ON attestation_verifications;
CREATE POLICY p_verifications_citizen_select ON attestation_verifications
    FOR SELECT
    TO consolith_app
    USING (
        current_app_user_role() = 'citizen' AND (
            verifier_id = current_app_user_id() OR
            attestation_id IN (SELECT id FROM document_attestations WHERE citizen_id = current_app_user_id())
        )
    );

DROP POLICY IF EXISTS p_verifications_citizen_insert ON attestation_verifications;
CREATE POLICY p_verifications_citizen_insert ON attestation_verifications
    FOR INSERT
    TO consolith_app
    WITH CHECK (
        current_app_user_role() = 'citizen' AND verifier_id = current_app_user_id()
    );

-- 8. Grant permissions to dedicated non-superuser role `consolith_app`
GRANT SELECT, INSERT, UPDATE, DELETE ON signing_keys TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON document_attestations TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON attestation_verifications TO consolith_app;

-- 9. Seed default root signing key for verification keystore
INSERT INTO signing_keys (
    key_id, public_key, fingerprint, algorithm, purpose, status, valid_from, valid_until
) VALUES (
    'consolith-officer-key-2026-v1',
    'IpX+wKf2HhXTzHW0rX70/bTUzRswahXg6D2YOBLqidw=',
    '835dcda1335bbfb2b5c1b1d15eeb7a4474a4cb1f70aa9fdf41b78158c250290c',
    'Ed25519',
    'document_attestation',
    'active',
    NOW(),
    NOW() + INTERVAL '2 years'
) ON CONFLICT (key_id) DO NOTHING;

