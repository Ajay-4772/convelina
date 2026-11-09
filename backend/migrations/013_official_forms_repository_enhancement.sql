-- Migration 013: Official Forms Repository Enhancement
-- Extends official_forms table with integrity hash, file metadata,
-- storage reference, and extended statutory metadata.

ALTER TABLE official_forms
    ADD COLUMN IF NOT EXISTS file_size_bytes INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100) DEFAULT 'application/pdf',
    ADD COLUMN IF NOT EXISTS file_format VARCHAR(20) DEFAULT 'pdf',
    ADD COLUMN IF NOT EXISTS sha256_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS storage_path VARCHAR(512),
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS metadata_payload JSONB DEFAULT '{}'::jsonb;

-- Indexes for performant form retrieval and integrity queries
CREATE INDEX IF NOT EXISTS idx_official_forms_sha256 ON official_forms(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_official_forms_active_verified ON official_forms(document_category, verification_status, is_active);

-- Ensure consolith_app non-superuser role maintains permissions under forced RLS
GRANT SELECT, INSERT, UPDATE, DELETE ON official_forms TO consolith_app;

