-- Consolith Migration 019: Unique User Email Constraint and Auth Hardening
-- 1. Enforces unique case-insensitive email constraint across users table
-- 2. Prevents race conditions during concurrent user provisioning
-- 3. Hardens index for fast case-insensitive email lookups

BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_lower_email_unique ON users(LOWER(email));

COMMIT;
