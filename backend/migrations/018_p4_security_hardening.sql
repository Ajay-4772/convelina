-- Consolith Migration 018: Phase P4 Security Hardening & Concurrency Protection
-- 1. Serializes audit log hash chaining via advisory transaction locks (eliminates concurrency races)
-- 2. Hardens get_latest_audit_hash() to prevent forking of cryptographic proofs

BEGIN;

CREATE OR REPLACE FUNCTION public.get_latest_audit_hash()
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path TO 'public'
AS $$
DECLARE
    v_hash text;
BEGIN
    -- Advisory transaction lock serializes audit log hash chaining across concurrent transactions
    PERFORM pg_advisory_xact_lock(hashtext('convelina_audit_log_lock'));

    SELECT current_hash INTO v_hash
    FROM audit_log
    ORDER BY created_at DESC, id DESC
    LIMIT 1;

    RETURN COALESCE(v_hash, '0000000000000000000000000000000000000000000000000000000000000000');
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_latest_audit_hash() TO consolith_app;

COMMIT;

