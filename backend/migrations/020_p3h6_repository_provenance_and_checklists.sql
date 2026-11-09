-- Migration 020: Citizen Document Repository, Provenance Taxonomy, and Verification States (P3H.6)
-- Expands provenance classifications and verification states across the official document repository.

-- 1. Update check constraint on official_forms for 7 standard provenance classifications
ALTER TABLE official_forms
    DROP CONSTRAINT IF EXISTS chk_official_forms_provenance;

ALTER TABLE official_forms
    ADD CONSTRAINT chk_official_forms_provenance
    CHECK (provenance IN (
        'OFFICIAL_ORIGINAL',
        'OFFICIAL_COPY',
        'GOVERNMENT_REFERENCE',
        'HISTORICAL_REFERENCE',
        'APPLICATION_GENERATED',
        'SYNTHETIC_DEVELOPMENT_SAMPLE',
        'SYNTHETIC_TEST_ASSET',
        'UNVERIFIED_SOURCE',
        'UNVERIFIED'
    ));

-- 2. Update check constraint on official_forms for 5 standard verification states
ALTER TABLE official_forms
    DROP CONSTRAINT IF EXISTS chk_official_forms_verification_status;

ALTER TABLE official_forms
    ADD CONSTRAINT chk_official_forms_verification_status
    CHECK (verification_status IN (
        'verified',
        'needs_review',
        'outdated',
        'retired',
        'source_metadata_conflict',
        'unverified',
        'provisional',
        'revoked'
    ));

-- 3. Also update official_form_versions if table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'official_form_versions') THEN
        ALTER TABLE official_form_versions
            DROP CONSTRAINT IF EXISTS chk_official_form_versions_provenance;
        ALTER TABLE official_form_versions
            ADD CONSTRAINT chk_official_form_versions_provenance
            CHECK (provenance IN (
                'OFFICIAL_ORIGINAL',
                'OFFICIAL_COPY',
                'GOVERNMENT_REFERENCE',
                'HISTORICAL_REFERENCE',
                'APPLICATION_GENERATED',
                'SYNTHETIC_DEVELOPMENT_SAMPLE',
                'SYNTHETIC_TEST_ASSET',
                'UNVERIFIED_SOURCE',
                'UNVERIFIED'
            ));
    END IF;
END $$;

-- 4. Create index for fast multi-attribute repository filtering
CREATE INDEX IF NOT EXISTS idx_official_forms_category_provenance_status
    ON official_forms(document_category, provenance, verification_status, is_active);
