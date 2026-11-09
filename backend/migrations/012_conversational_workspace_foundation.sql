-- Migration 012: Conversational Workspace Foundation
-- Adds conversation pinning, archiving, response language preferences,
-- message types, and message attachments table with kernel forced RLS.

-- 1. Extend assistant_conversations
ALTER TABLE assistant_conversations
    ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS response_language VARCHAR(10) NOT NULL DEFAULT 'en';

CREATE INDEX IF NOT EXISTS idx_assistant_conv_pinned ON assistant_conversations(user_id, is_pinned);
CREATE INDEX IF NOT EXISTS idx_assistant_conv_updated ON assistant_conversations(user_id, updated_at DESC);

-- 2. Extend assistant_messages
ALTER TABLE assistant_messages
    ADD COLUMN IF NOT EXISTS message_type VARCHAR(30) NOT NULL DEFAULT 'chat';

CREATE INDEX IF NOT EXISTS idx_assistant_msg_type ON assistant_messages(message_type);

-- 3. Create message_attachments table
CREATE TABLE IF NOT EXISTS message_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES assistant_messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes INT NOT NULL,
    storage_ref VARCHAR(512) NOT NULL,
    extracted_text TEXT,
    is_temporary BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_msg_attachments_msg ON message_attachments(message_id);
CREATE INDEX IF NOT EXISTS idx_msg_attachments_user ON message_attachments(user_id);
CREATE INDEX IF NOT EXISTS idx_msg_attachments_expires ON message_attachments(is_temporary, expires_at);

-- 4. Kernel Row-Level Security on message_attachments
ALTER TABLE message_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_attachments FORCE ROW LEVEL SECURITY;

CREATE POLICY p_att_citizen ON message_attachments
    FOR ALL TO consolith_app
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY p_att_admin ON message_attachments
    FOR ALL TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

-- 5. Grant permissions to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON message_attachments TO consolith_app;

