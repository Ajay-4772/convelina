-- Migration 021: Citizen Checklist Progress Persistence and Row-Level Security
-- Persists citizen preparation checklist progress in PostgreSQL with forced RLS.

BEGIN;

CREATE TABLE IF NOT EXISTS citizen_checklist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    procedure_id VARCHAR(100) NOT NULL,
    item_id VARCHAR(100) NOT NULL,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_citizen_checklist_user_proc_item UNIQUE (user_id, procedure_id, item_id)
);

-- Force Row-Level Security on citizen_checklist_items
ALTER TABLE citizen_checklist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE citizen_checklist_items FORCE ROW LEVEL SECURITY;

-- Drop existing policies if re-running
DROP POLICY IF EXISTS citizen_checklist_items_select ON citizen_checklist_items;
DROP POLICY IF EXISTS citizen_checklist_items_insert ON citizen_checklist_items;
DROP POLICY IF EXISTS citizen_checklist_items_update ON citizen_checklist_items;
DROP POLICY IF EXISTS citizen_checklist_items_delete ON citizen_checklist_items;

-- Scoped RLS Policies: Citizens can only read and manipulate their own checklist items; Admins have read access
CREATE POLICY citizen_checklist_items_select ON citizen_checklist_items
    FOR SELECT
    USING (
        user_id = current_app_user_id()
        OR current_app_user_role() = 'admin'
    );

CREATE POLICY citizen_checklist_items_insert ON citizen_checklist_items
    FOR INSERT
    WITH CHECK (
        user_id = current_app_user_id()
        OR current_app_user_role() = 'admin'
    );

CREATE POLICY citizen_checklist_items_update ON citizen_checklist_items
    FOR UPDATE
    USING (
        user_id = current_app_user_id()
        OR current_app_user_role() = 'admin'
    )
    WITH CHECK (
        user_id = current_app_user_id()
        OR current_app_user_role() = 'admin'
    );

CREATE POLICY citizen_checklist_items_delete ON citizen_checklist_items
    FOR DELETE
    USING (
        user_id = current_app_user_id()
        OR current_app_user_role() = 'admin'
    );

-- Grant DML permissions to non-superuser application role
GRANT SELECT, INSERT, UPDATE, DELETE ON citizen_checklist_items TO consolith_app;

-- Indexes for efficient lookup
CREATE INDEX IF NOT EXISTS idx_citizen_checklists_user_proc
    ON citizen_checklist_items(user_id, procedure_id);

CREATE INDEX IF NOT EXISTS idx_citizen_checklists_proc_item
    ON citizen_checklist_items(procedure_id, item_id);

COMMIT;

