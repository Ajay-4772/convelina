-- Migration 003: Secure User Identity Resolution & Provisioning Functions

-- Function 1: Resolve user by verified Firebase UID
CREATE OR REPLACE FUNCTION resolve_user_by_firebase_uid(p_firebase_uid TEXT)
RETURNS TABLE (
    id UUID,
    firebase_uid VARCHAR,
    email VARCHAR,
    full_name VARCHAR,
    role VARCHAR,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.firebase_uid, u.email, u.full_name, u.role, u.created_at, u.updated_at
    FROM users u
    WHERE u.firebase_uid = p_firebase_uid;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Provision or synchronize citizen account
-- Enforces that new accounts ALWAYS receive the 'citizen' role.
-- Any client attempt to choose a role is completely ignored.
CREATE OR REPLACE FUNCTION provision_citizen_user(
    p_firebase_uid TEXT,
    p_email TEXT,
    p_full_name TEXT
)
RETURNS TABLE (
    id UUID,
    firebase_uid VARCHAR,
    email VARCHAR,
    full_name VARCHAR,
    role VARCHAR,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_user users%ROWTYPE;
BEGIN
    -- Concurrent-safe upsert using unique constraint name to avoid PL/pgSQL variable ambiguity
    INSERT INTO users (firebase_uid, email, full_name, role)
    VALUES (p_firebase_uid, p_email, p_full_name, 'citizen')
    ON CONFLICT ON CONSTRAINT users_firebase_uid_key DO UPDATE
    SET full_name = EXCLUDED.full_name,
        updated_at = NOW()
    RETURNING * INTO v_user;

    RETURN QUERY
    SELECT v_user.id, v_user.firebase_uid, v_user.email, v_user.full_name, v_user.role, v_user.created_at, v_user.updated_at;
END;
$$ LANGUAGE plpgsql;

-- Grant execution to non-superuser application role
GRANT EXECUTE ON FUNCTION resolve_user_by_firebase_uid(TEXT) TO consolith_app;
GRANT EXECUTE ON FUNCTION provision_citizen_user(TEXT, TEXT, TEXT) TO consolith_app;
