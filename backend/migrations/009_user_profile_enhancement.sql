-- ==============================================================================
-- Consolith Migration 009: User Profile Enhancement, OTP Verification & Activity
-- ==============================================================================

-- 1. Add optional profile fields to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(30),
ADD COLUMN IF NOT EXISTS date_of_birth VARCHAR(30),
ADD COLUMN IF NOT EXISTS address TEXT,
ADD COLUMN IF NOT EXISTS father_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS mother_name VARCHAR(255);

-- 2. Email OTP verification table for genuine email OTP onboarding
CREATE TABLE IF NOT EXISTS email_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_email_otps_lookup ON email_otps(email, otp_code, expires_at);

-- 3. Row-Level Security
ALTER TABLE email_otps ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_otps FORCE ROW LEVEL SECURITY;

-- Application role access for OTP validation
DROP POLICY IF EXISTS p_email_otps_app_all ON email_otps;
CREATE POLICY p_email_otps_app_all ON email_otps
    FOR ALL
    TO consolith_app
    USING (true)
    WITH CHECK (true);

-- 4. Grant table privileges to runtime application role
GRANT SELECT, INSERT, UPDATE, DELETE ON email_otps TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON users TO consolith_app;
