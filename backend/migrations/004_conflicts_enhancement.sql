-- Migration 004: Conflict Detection Enhancement
-- Adds comparison_method, similarity_score, and unique constraint for idempotent conflict detection

ALTER TABLE conflicts
    ADD COLUMN IF NOT EXISTS comparison_method VARCHAR(50) DEFAULT 'exact',
    ADD COLUMN IF NOT EXISTS similarity_score NUMERIC(5,2) DEFAULT NULL;

-- Create unique constraint to ensure idempotency when running conflict detection across document pairs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_conflicts_pair_field'
    ) THEN
        ALTER TABLE conflicts
            ADD CONSTRAINT uq_conflicts_pair_field UNIQUE (user_id, doc_a_id, doc_b_id, field_name);
    END IF;
END $$;

-- Grant permissions to non-superuser application role
GRANT SELECT, INSERT, UPDATE, DELETE ON conflicts TO consolith_app;
