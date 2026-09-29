-- Migration 005: Advanced Context-Aware RAG Knowledge Base, Official Forms, and AI Assistant

-- 1. Official Knowledge Sources (Authoritative government procedures, circulars, and SOPs)
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    issuing_authority VARCHAR(150) NOT NULL,
    document_type VARCHAR(50) NOT NULL DEFAULT 'guideline',
    document_category VARCHAR(50) NOT NULL, -- aadhaar, pan, passport, epf, education
    source_url VARCHAR(512) NOT NULL,
    jurisdiction VARCHAR(50) NOT NULL DEFAULT 'India',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_date TIMESTAMPTZ,
    last_verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version VARCHAR(30),
    content_hash VARCHAR(64) NOT NULL,
    verification_status VARCHAR(20) NOT NULL DEFAULT 'verified',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    raw_content TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_sources_category ON knowledge_sources(document_category);
CREATE INDEX IF NOT EXISTS idx_knowledge_sources_status ON knowledge_sources(verification_status, is_active);

-- 2. Official Forms Catalog
CREATE TABLE IF NOT EXISTS official_forms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id VARCHAR(100) UNIQUE NOT NULL,
    form_name VARCHAR(255) NOT NULL,
    document_category VARCHAR(50) NOT NULL,
    purpose TEXT NOT NULL,
    issuing_authority VARCHAR(150) NOT NULL,
    official_download_url VARCHAR(512) NOT NULL,
    instructions_source_id VARCHAR(100),
    applicable_issue_types JSONB NOT NULL DEFAULT '[]'::jsonb,
    applicable_conditions JSONB NOT NULL DEFAULT '[]'::jsonb,
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    version VARCHAR(30),
    effective_date TIMESTAMPTZ,
    last_verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    verification_status VARCHAR(20) NOT NULL DEFAULT 'verified',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_official_forms_category ON official_forms(document_category);
CREATE INDEX IF NOT EXISTS idx_official_forms_status ON official_forms(verification_status, is_active);

-- 3. Assistant Conversations (Scoped to authenticated citizen)
CREATE TABLE IF NOT EXISTS assistant_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'New Conversation',
    active_case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
    active_conflict_id UUID REFERENCES conflicts(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assistant_conv_user ON assistant_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_assistant_conv_conflict ON assistant_conversations(active_conflict_id);

-- 4. Assistant Messages
CREATE TABLE IF NOT EXISTS assistant_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES assistant_conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    structured_response JSONB DEFAULT '{}'::jsonb,
    citations JSONB DEFAULT '[]'::jsonb,
    tokens_used INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assistant_msg_conv ON assistant_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_assistant_msg_user ON assistant_messages(user_id);

-- 5. Row-Level Security Configuration

-- Enable & FORCE RLS on all 4 tables
ALTER TABLE knowledge_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_sources FORCE ROW LEVEL SECURITY;

ALTER TABLE official_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE official_forms FORCE ROW LEVEL SECURITY;

ALTER TABLE assistant_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE assistant_conversations FORCE ROW LEVEL SECURITY;

ALTER TABLE assistant_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE assistant_messages FORCE ROW LEVEL SECURITY;

-- Knowledge Sources & Official Forms Policies:
-- Read-only for authenticated callers (active & verified sources); Full access for admin
CREATE POLICY p_knowledge_read ON knowledge_sources
    FOR SELECT TO consolith_app
    USING (is_active = TRUE OR current_app_user_role() = 'admin');

CREATE POLICY p_knowledge_admin_modify ON knowledge_sources
    FOR ALL TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

CREATE POLICY p_forms_read ON official_forms
    FOR SELECT TO consolith_app
    USING (is_active = TRUE OR current_app_user_role() = 'admin');

CREATE POLICY p_forms_admin_modify ON official_forms
    FOR ALL TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

-- Assistant Conversations Policies:
-- Citizens see and modify only their own conversations
CREATE POLICY p_conv_citizen ON assistant_conversations
    FOR ALL TO consolith_app
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY p_conv_admin ON assistant_conversations
    FOR ALL TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

-- Assistant Messages Policies:
-- Citizens see and insert only their own messages
CREATE POLICY p_msg_citizen ON assistant_messages
    FOR ALL TO consolith_app
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY p_msg_admin ON assistant_messages
    FOR ALL TO consolith_app
    USING (current_app_user_role() = 'admin')
    WITH CHECK (current_app_user_role() = 'admin');

-- 6. Permissions to non-superuser application role
GRANT SELECT, INSERT, UPDATE, DELETE ON knowledge_sources TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON official_forms TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON assistant_conversations TO consolith_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON assistant_messages TO consolith_app;
