-- ==============================================================================
-- CONVELINA Migration 023: Assistant Message Pagination Composite Index
-- Optimizes backward cursor-based pagination query:
-- WHERE conversation_id = :conv_id AND user_id = :user_id
-- ORDER BY created_at DESC, id DESC LIMIT :limit
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_assistant_msg_pagination
    ON assistant_messages(conversation_id, created_at DESC, id DESC);
