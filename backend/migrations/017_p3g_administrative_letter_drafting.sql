-- Consolith Migration 017: Module 7 / Phase P3G Administrative Letter Drafting & Petition Generation
-- 1. Updates RLS policies to enforce clean USER / ADMIN scoping under consolith_app non-superuser role
-- 2. Removes obsolete officer read policies while maintaining strict FORCE ROW LEVEL SECURITY
-- 3. Extends correction_drafts and correction_draft_versions with statutory metadata, confirmation state, and SHA-256 hash tracking

BEGIN;

-- ==============================================================================
-- 1. Extend correction_drafts with P3G statutory drafting fields
-- ==============================================================================

ALTER TABLE correction_drafts
    ADD COLUMN IF NOT EXISTS recipient_authority VARCHAR(255),
    ADD COLUMN IF NOT EXISTS subject VARCHAR(255),
    ADD COLUMN IF NOT EXISTS user_explanation TEXT,
    ADD COLUMN IF NOT EXISTS requested_action TEXT,
    ADD COLUMN IF NOT EXISTS supporting_documents JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS disclaimer TEXT NOT NULL DEFAULT 'AI-GENERATED ADMINISTRATIVE DRAFT — REVIEW ALL DETAILS AND VERIFY THE APPLICABLE OFFICIAL PROCEDURE BEFORE SUBMISSION.',
    ADD COLUMN IF NOT EXISTS is_citizen_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS citizen_confirmed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS confirmed_version_number INT,
    ADD COLUMN IF NOT EXISTS sha256_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS file_path VARCHAR(512),
    ADD COLUMN IF NOT EXISTS language VARCHAR(32) NOT NULL DEFAULT 'en';

CREATE INDEX IF NOT EXISTS idx_correction_drafts_is_confirmed ON correction_drafts(is_citizen_confirmed);
CREATE INDEX IF NOT EXISTS idx_correction_drafts_category ON correction_drafts(document_category);
CREATE INDEX IF NOT EXISTS idx_correction_drafts_doc_type ON correction_drafts(document_type);

-- ==============================================================================
-- 2. Extend correction_draft_versions with immutable audit & confirmation fields
-- ==============================================================================

ALTER TABLE correction_draft_versions
    ADD COLUMN IF NOT EXISTS recipient_authority VARCHAR(255),
    ADD COLUMN IF NOT EXISTS subject VARCHAR(255),
    ADD COLUMN IF NOT EXISTS confirmed_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS supporting_documents JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS source_references JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS is_citizen_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS citizen_confirmed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS sha256_hash VARCHAR(64);

-- ==============================================================================
-- 3. Modernize & Harden Row-Level Security (RLS) for USER and ADMIN Roles
-- ==============================================================================

-- Drop demonstrably obsolete officer read policies (officer role was deprecated in Migration 010)
DROP POLICY IF EXISTS p_drafts_officer_read ON correction_drafts;
DROP POLICY IF EXISTS p_draft_versions_officer_read ON correction_draft_versions;

-- Update citizen/user scoping policies
DROP POLICY IF EXISTS p_drafts_citizen ON correction_drafts;
DROP POLICY IF EXISTS p_drafts_user ON correction_drafts;
CREATE POLICY p_drafts_user ON correction_drafts
    FOR ALL TO consolith_app
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

DROP POLICY IF EXISTS p_draft_versions_citizen ON correction_draft_versions;
DROP POLICY IF EXISTS p_draft_versions_user ON correction_draft_versions;
CREATE POLICY p_draft_versions_user ON correction_draft_versions
    FOR ALL TO consolith_app
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

-- Add authoritative admin policies (strictly role = 'admin')
DROP POLICY IF EXISTS p_drafts_admin ON correction_drafts;
CREATE POLICY p_drafts_admin ON correction_drafts
    FOR ALL TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_draft_versions_admin ON correction_draft_versions;
CREATE POLICY p_draft_versions_admin ON correction_draft_versions
    FOR ALL TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

-- Re-assert FORCED RLS on both tables
ALTER TABLE correction_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE correction_drafts FORCE ROW LEVEL SECURITY;

ALTER TABLE correction_draft_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE correction_draft_versions FORCE ROW LEVEL SECURITY;

-- Ensure privileges granted to application non-superuser role
GRANT SELECT, INSERT, UPDATE, DELETE ON correction_drafts TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON correction_draft_versions TO consolith_app;

COMMIT;

