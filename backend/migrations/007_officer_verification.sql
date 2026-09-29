-- Consolith Migration 007: Module 8 Officer Verification Workflow
-- Standardizes case review states, enables conflict & draft linking, creates case_review_requests, and enforces Forced RLS.

-- 1. Update cases table status constraint and link fields
ALTER TABLE cases DROP CONSTRAINT IF EXISTS cases_status_check;

ALTER TABLE cases ADD CONSTRAINT cases_status_check 
    CHECK (status IN (
        'pending_assignment',
        'assigned',
        'under_review',
        'additional_information_requested',
        'information_submitted',
        'approved',
        'rejected',
        'closed'
    ));

ALTER TABLE cases ALTER COLUMN status TYPE VARCHAR(50);
ALTER TABLE cases ALTER COLUMN status SET DEFAULT 'pending_assignment';

-- Add conflict_id and correction_draft_id references if not present
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cases' AND column_name = 'conflict_id') THEN
        ALTER TABLE cases ADD COLUMN conflict_id UUID REFERENCES conflicts(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cases' AND column_name = 'correction_draft_id') THEN
        ALTER TABLE cases ADD COLUMN correction_draft_id UUID REFERENCES correction_drafts(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cases' AND column_name = 'review_started_at') THEN
        ALTER TABLE cases ADD COLUMN review_started_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cases' AND column_name = 'decision') THEN
        ALTER TABLE cases ADD COLUMN decision VARCHAR(30);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cases' AND column_name = 'decision_reason') THEN
        ALTER TABLE cases ADD COLUMN decision_reason TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cases' AND column_name = 'decision_timestamp') THEN
        ALTER TABLE cases ADD COLUMN decision_timestamp TIMESTAMPTZ;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_cases_conflict_id ON cases(conflict_id);
CREATE INDEX IF NOT EXISTS idx_cases_correction_draft_id ON cases(correction_draft_id);

-- 2. Create case_review_requests table for Officer <-> Citizen clarifications
CREATE TABLE IF NOT EXISTS case_review_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    officer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    citizen_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_details TEXT NOT NULL,
    request_reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'responded', 'closed')),
    response_text TEXT,
    response_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_review_requests_case ON case_review_requests(case_id);
CREATE INDEX IF NOT EXISTS idx_review_requests_officer ON case_review_requests(officer_id);
CREATE INDEX IF NOT EXISTS idx_review_requests_citizen ON case_review_requests(citizen_id);
CREATE INDEX IF NOT EXISTS idx_review_requests_status ON case_review_requests(status);

-- 3. Enable & FORCE Row-Level Security on case_review_requests
ALTER TABLE case_review_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_review_requests FORCE ROW LEVEL SECURITY;

-- 4. Define RLS Policies for case_review_requests
DROP POLICY IF EXISTS p_review_req_admin ON case_review_requests;
CREATE POLICY p_review_req_admin ON case_review_requests
    FOR ALL TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

DROP POLICY IF EXISTS p_review_req_officer ON case_review_requests;
CREATE POLICY p_review_req_officer ON case_review_requests
    FOR ALL TO consolith_app
    USING (current_app_user_role() = 'officer' AND officer_id = current_app_user_id())
    WITH CHECK (current_app_user_role() = 'officer' AND officer_id = current_app_user_id());

DROP POLICY IF EXISTS p_review_req_citizen ON case_review_requests;
CREATE POLICY p_review_req_citizen ON case_review_requests
    FOR ALL TO consolith_app
    USING (citizen_id = current_app_user_id())
    WITH CHECK (citizen_id = current_app_user_id());

-- 5. Grant non-superuser application role permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON cases TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON case_evidence TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON case_review_requests TO consolith_app;
GRANT SELECT, INSERT ON audit_log TO consolith_app;

-- 6. Helper function for tamper-evident hash chaining across RLS contexts
CREATE OR REPLACE FUNCTION public.get_latest_audit_hash()
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $$
DECLARE
    v_hash text;
BEGIN
    SELECT current_hash INTO v_hash
    FROM audit_log
    ORDER BY created_at DESC, id DESC
    LIMIT 1;
    RETURN COALESCE(v_hash, '0000000000000000000000000000000000000000000000000000000000000000');
END;
$$;
GRANT EXECUTE ON FUNCTION public.get_latest_audit_hash() TO consolith_app;

