-- Consolith Migration 006: Module 7 Correction Document Generator
-- Creates correction_drafts and correction_draft_versions with Forced Row-Level Security

-- 1. Correction Drafts Table
CREATE TABLE IF NOT EXISTS correction_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conflict_id UUID REFERENCES conflicts(id) ON DELETE SET NULL,
    document_type VARCHAR(50) NOT NULL, -- e.g. "correction_request_letter", "supporting_document_checklist", "declaration_draft"
    document_category VARCHAR(50) NOT NULL, -- e.g. "pan", "aadhaar", "passport", "epf", "education"
    status VARCHAR(20) NOT NULL DEFAULT 'draft', -- draft, edited, approved
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    confirmed_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_references JSONB NOT NULL DEFAULT '[]'::jsonb,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_correction_drafts_user ON correction_drafts(user_id);
CREATE INDEX IF NOT EXISTS idx_correction_drafts_conflict ON correction_drafts(conflict_id);
CREATE INDEX IF NOT EXISTS idx_correction_drafts_status ON correction_drafts(status);

-- 2. Correction Draft Versions Table (Audit & history tracking)
CREATE TABLE IF NOT EXISTS correction_draft_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID NOT NULL REFERENCES correction_drafts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    content TEXT NOT NULL,
    change_type VARCHAR(50) NOT NULL DEFAULT 'initial_generation', -- initial_generation, user_edit, regeneration
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_correction_draft_versions_draft ON correction_draft_versions(draft_id);
CREATE INDEX IF NOT EXISTS idx_correction_draft_versions_user ON correction_draft_versions(user_id);

-- 3. Row-Level Security Configuration

-- Enable & FORCE RLS on both tables
ALTER TABLE correction_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE correction_drafts FORCE ROW LEVEL SECURITY;

ALTER TABLE correction_draft_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE correction_draft_versions FORCE ROW LEVEL SECURITY;

-- Citizen Scoping Policies for correction_drafts
CREATE POLICY p_drafts_citizen ON correction_drafts
    FOR ALL TO consolith_app
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY p_drafts_officer_read ON correction_drafts
    FOR SELECT TO consolith_app
    USING (current_app_user_role() IN ('officer', 'admin'));

-- Citizen Scoping Policies for correction_draft_versions
CREATE POLICY p_draft_versions_citizen ON correction_draft_versions
    FOR ALL TO consolith_app
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY p_draft_versions_officer_read ON correction_draft_versions
    FOR SELECT TO consolith_app
    USING (current_app_user_role() IN ('officer', 'admin'));

-- 4. Permissions to non-superuser application role
GRANT SELECT, INSERT, UPDATE, DELETE ON correction_drafts TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON correction_draft_versions TO consolith_app;
