-- CONVELINA — Migration 016: Synthetic Forms, Version History, OCR Confirmation & Future RAG Readiness
-- 1. Document user confirmation and structured field-level extraction metadata
-- 2. Official form version history archive table for admin replacement workflow
-- 3. Knowledge source ingestion metadata expansion for future verified corpus

-- 1. Extend documents table for citizen field confirmation & field-level OCR metadata
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS confirmed_fields JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS is_user_confirmed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP WITH TIME ZONE NULL,
    ADD COLUMN IF NOT EXISTS field_extractions JSONB DEFAULT '{}'::jsonb;

-- Allow 'needs_review' in documents ocr_status check constraint
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_ocr_status_check;
ALTER TABLE documents ADD CONSTRAINT documents_ocr_status_check CHECK (ocr_status IN ('pending', 'processing', 'completed', 'failed', 'flagged', 'needs_review'));

CREATE INDEX IF NOT EXISTS idx_documents_user_confirmed ON documents(user_id, is_user_confirmed);

-- 2. Official Form Versions Table (Audit & Replacement History)
CREATE TABLE IF NOT EXISTS official_form_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id VARCHAR(100) NOT NULL,
    version VARCHAR(30) NULL,
    form_name VARCHAR(255) NOT NULL,
    document_category VARCHAR(50) NOT NULL,
    issuing_authority VARCHAR(150) NOT NULL,
    purpose TEXT NOT NULL,
    official_download_url VARCHAR(512) NOT NULL,
    sha256_hash VARCHAR(64) NULL,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    storage_path VARCHAR(512) NULL,
    provenance VARCHAR(30) NOT NULL DEFAULT 'SYNTHETIC_TEST_ASSET',
    provenance_notes TEXT NULL,
    verification_status VARCHAR(20) NOT NULL DEFAULT 'unverified',
    retired_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    retired_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_official_form_versions_form_id ON official_form_versions(form_id, retired_at DESC);

-- Enable and FORCE Row-Level Security on official_form_versions
ALTER TABLE official_form_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE official_form_versions FORCE ROW LEVEL SECURITY;

-- Read policy: Public/Authenticated users can view archived form history
CREATE POLICY p_form_versions_read ON official_form_versions
    FOR SELECT
    TO PUBLIC
    USING (TRUE);

-- Admin modification policy: Only administrators can insert/manage version archives
CREATE POLICY p_form_versions_admin_modify ON official_form_versions
    FOR ALL
    TO PUBLIC
    USING (
        current_setting('app.current_user_role', true) = 'admin'
    )
    WITH CHECK (
        current_setting('app.current_user_role', true) = 'admin'
    );

GRANT SELECT, INSERT, UPDATE, DELETE ON official_form_versions TO consolith_app;

-- 3. Extend knowledge_sources table for future RAG ingestion workflows
ALTER TABLE knowledge_sources
    ADD COLUMN IF NOT EXISTS ingestion_status VARCHAR(30) DEFAULT 'completed',
    ADD COLUMN IF NOT EXISTS uploaded_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS review_notes TEXT NULL,
    ADD COLUMN IF NOT EXISTS publication_date TIMESTAMP WITH TIME ZONE NULL,
    ADD COLUMN IF NOT EXISTS correction_category VARCHAR(50) NULL;

CREATE INDEX IF NOT EXISTS idx_knowledge_sources_category_status
    ON knowledge_sources(document_category, verification_status, is_active);
