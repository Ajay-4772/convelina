-- Migration 001: Initial Schema for Consolith
-- Tables: users, documents, conflicts, cases, case_evidence, audit_log, digital_signatures

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'citizen' CHECK (role IN ('citizen', 'officer', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. Documents Table (Tier 1 document types supported)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('aadhaar', 'pan', 'passport', 'education_10th', 'education_12th', 'epf_record', 'other')),
    file_path VARCHAR(512) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    ocr_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (ocr_status IN ('pending', 'processing', 'completed', 'failed', 'flagged')),
    extracted_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    masked_id VARCHAR(50),
    encrypted_data TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);

-- 3. Conflicts Table
CREATE TABLE IF NOT EXISTS conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    doc_a_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    doc_b_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    conflict_type VARCHAR(30) NOT NULL CHECK (conflict_type IN ('format-only', 'genuine-mismatch', 'unresolvable-needs-evidence')),
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    field_name VARCHAR(100) NOT NULL,
    value_a TEXT NOT NULL,
    value_b TEXT NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'detected' CHECK (status IN ('detected', 'resolved', 'ignored', 'in_review')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conflicts_user_id ON conflicts(user_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_docs ON conflicts(doc_a_id, doc_b_id);

-- 4. Cases Table (Verification cases for citizen correction assistance)
CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    citizen_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_officer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'under_review', 'resolved', 'rejected', 'info_requested')),
    title VARCHAR(255) NOT NULL,
    evidence_notes TEXT,
    officer_notes TEXT,
    resolution_notes TEXT,
    resolution_signature TEXT,
    resolution_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cases_citizen_id ON cases(citizen_id);
CREATE INDEX IF NOT EXISTS idx_cases_officer_id ON cases(assigned_officer_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);

-- 5. Case Evidence Table
CREATE TABLE IF NOT EXISTS case_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_case_evidence_case ON case_evidence(case_id);

-- 6. Audit Log Table (Append-Only Hash-Chained Trail)
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    prev_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at);

-- 7. Digital Signatures Table (Ed25519 officer resolutions)
CREATE TABLE IF NOT EXISTS digital_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    officer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    public_key VARCHAR(128) NOT NULL,
    signature VARCHAR(256) NOT NULL,
    signed_data_hash VARCHAR(64) NOT NULL,
    algorithm VARCHAR(20) NOT NULL DEFAULT 'Ed25519',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_digital_signatures_case ON digital_signatures(case_id);
CREATE INDEX IF NOT EXISTS idx_digital_signatures_officer ON digital_signatures(officer_id);
