-- Migration 011: Conflict Metadata for Phase P1 Identity Comparison Engine
-- Adds metadata JSONB column to conflicts table to store rich P0 diagnostics

ALTER TABLE conflicts
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Ensure permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON conflicts TO consolith_app;

