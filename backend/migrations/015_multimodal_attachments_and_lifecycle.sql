-- Migration 015: Multimodal Attachments & Confidential Lifecycle (Phase P3E)
-- Enhances message_attachments table to support pre-send upload lifecycle:
-- UPLOADED -> VALIDATING -> PROCESSING -> READY -> EXPIRED / DELETED
-- Links attachments to conversations and optional conflicts under forced RLS.

-- 1. Make message_id nullable to allow pre-message upload staging
ALTER TABLE message_attachments 
    ALTER COLUMN message_id DROP NOT NULL;

-- 2. Add conversational and conflict context links
ALTER TABLE message_attachments
    ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES assistant_conversations(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS conflict_id UUID REFERENCES conflicts(id) ON DELETE SET NULL;

-- 3. Add explicit lifecycle status, cryptographic hash, and OCR extraction fields
ALTER TABLE message_attachments
    ADD COLUMN IF NOT EXISTS status VARCHAR(30) NOT NULL DEFAULT 'UPLOADED',
    ADD COLUMN IF NOT EXISTS sha256_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS ocr_confidence NUMERIC(5, 4),
    ADD COLUMN IF NOT EXISTS ocr_status VARCHAR(30) NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS extracted_fields JSONB DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS error_message TEXT,
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

-- 4. Enforce strict lifecycle status domain constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_att_status'
    ) THEN
        ALTER TABLE message_attachments
            ADD CONSTRAINT chk_att_status
            CHECK (status IN ('UPLOADED', 'VALIDATING', 'PROCESSING', 'READY', 'FAILED', 'EXPIRED', 'DELETED'));
    END IF;
END $$;

-- 5. Indexes for fast lookup, user isolation, and automated expiry cleanup
CREATE INDEX IF NOT EXISTS idx_msg_attachments_conv ON message_attachments(conversation_id);
CREATE INDEX IF NOT EXISTS idx_msg_attachments_conflict ON message_attachments(conflict_id);
CREATE INDEX IF NOT EXISTS idx_msg_attachments_user_status ON message_attachments(user_id, status);
CREATE INDEX IF NOT EXISTS idx_msg_attachments_expiry_sweep ON message_attachments(is_temporary, expires_at) WHERE deleted_at IS NULL;

-- 6. Ensure runtime permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON message_attachments TO consolith_app;

