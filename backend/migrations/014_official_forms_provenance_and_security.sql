-- Migration 014: Official Forms Provenance & Security Classification
-- Enforces strict document provenance distinctions:
-- OFFICIAL_ORIGINAL, OFFICIAL_COPY, APPLICATION_GENERATED, SYNTHETIC_TEST_ASSET, UNVERIFIED

ALTER TABLE official_forms
    ADD COLUMN IF NOT EXISTS provenance VARCHAR(30) NOT NULL DEFAULT 'UNVERIFIED'
        CONSTRAINT chk_official_forms_provenance
        CHECK (provenance IN ('OFFICIAL_ORIGINAL', 'OFFICIAL_COPY', 'APPLICATION_GENERATED', 'SYNTHETIC_TEST_ASSET', 'UNVERIFIED')),
    ADD COLUMN IF NOT EXISTS provenance_notes TEXT,
    ADD COLUMN IF NOT EXISTS official_source_published_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS verified_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL;

-- Create index for provenance and status queries
CREATE INDEX IF NOT EXISTS idx_official_forms_provenance_status
    ON official_forms(provenance, verification_status, is_active);

-- Accurately downgrade all existing ReportLab-generated records to APPLICATION_GENERATED and unverified
UPDATE official_forms
SET 
    provenance = 'APPLICATION_GENERATED',
    verification_status = 'unverified',
    provenance_notes = 'Application-generated PDF template created via ReportLab open-source engine. Not an official government publication. Download authentic official original from issuing authority portal.',
    updated_at = NOW()
WHERE storage_path IS NOT NULL AND storage_path LIKE '%.pdf';

