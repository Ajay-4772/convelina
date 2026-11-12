-- ==============================================================================
-- CONVELINA Migration 022: Security Master Directive Database Hardening
-- 1. Hardens email_otps with hashed OTP storage, attempt lockout tracking,
--    and strictly scoped RLS (eliminating wide-open USING (true)).
-- 2. Normalizes official_form_versions admin policy to use current_app_user_role().
-- ==============================================================================

-- 1. Harden email_otps schema
ALTER TABLE email_otps
    ADD COLUMN IF NOT EXISTS otp_hash VARCHAR(128),
    ADD COLUMN IF NOT EXISTS otp_salt VARCHAR(64),
    ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS verification_token_hash VARCHAR(128),
    ADD COLUMN IF NOT EXISTS request_ip VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_email_otps_ip_created
    ON email_otps(request_ip, created_at);

-- 2. Replace permissive email_otps RLS policy with session-scoped isolation
ALTER TABLE email_otps ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_otps FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS p_email_otps_app_all ON email_otps;
DROP POLICY IF EXISTS p_email_otps_scoped ON email_otps;
CREATE POLICY p_email_otps_scoped ON email_otps
    FOR ALL
    TO consolith_app
    USING (
        LOWER(email) = LOWER(NULLIF(current_setting('app.otp_email', true), ''))
        OR current_app_user_role() = 'admin'
    )
    WITH CHECK (
        LOWER(email) = LOWER(NULLIF(current_setting('app.otp_email', true), ''))
        OR current_app_user_role() = 'admin'
    );

-- 3. Normalize official_form_versions admin policy to use safe NULLIF helper
DROP POLICY IF EXISTS p_form_versions_admin_modify ON official_form_versions;
CREATE POLICY p_form_versions_admin_modify ON official_form_versions
    FOR ALL
    TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

