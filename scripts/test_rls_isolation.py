#!/usr/bin/env python3
"""
Consolith Row-Level Security (RLS) & Isolation Test Suite
Verifies:
1. Runtime connection uses non-superuser role (consolith_app).
2. Unauthenticated default-deny isolation (0 rows).
3. Citizen cross-document read isolation (Citizen A cannot read Citizen B).
4. Citizen cross-document write isolation (Citizen A cannot modify Citizen B).
5. Privilege escalation defense (Citizen cannot self-promote to admin).
6. Officer case scoping (Officer only sees explicitly assigned cases & docs).
7. Admin visibility policy.
8. Append-only audit trail immutability (UPDATE and DELETE blocked by trigger).
9. Connection pooling safety (empty-string UUID cast trap prevention).
"""

import os
import sys
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_urls():
    # Detect if running inside docker container or host
    import socket
    host = "localhost"
    try:
        socket.gethostbyname("postgres")
        host = "postgres"
    except Exception:
        host = "localhost"
        
    app_url = os.getenv(
        "DATABASE_URL",
        f"postgresql://consolith_app:consolith_secure_app_pw@{host}:5432/consolith"
    )
    admin_url = os.getenv(
        "DATABASE_MIGRATION_URL",
        f"postgresql://postgres:postgres_dev_password@{host}:5432/consolith"
    )
    return app_url, admin_url

APP_DB_URL, ADMIN_DB_URL = get_db_urls()

# Synthetic test UUIDs
CITIZEN_A_ID = str(uuid.uuid4())
CITIZEN_B_ID = str(uuid.uuid4())
ADMIN_ID = str(uuid.uuid4())

DOC_A_ID = str(uuid.uuid4())
DOC_B_ID = str(uuid.uuid4())
AUDIT_ID = str(uuid.uuid4())
KEY_ID = str(uuid.uuid4())
ATTESTATION_A_ID = str(uuid.uuid4())
ATTESTATION_B_ID = str(uuid.uuid4())

def seed_synthetic_fixtures():
    print("[SETUP] Seeding synthetic test fixtures via administrative connection...")
    conn = psycopg2.connect(ADMIN_DB_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        # Disable trigger during fixture cleanup via superuser admin session
        cur.execute("ALTER TABLE audit_log DISABLE TRIGGER trg_block_audit_log_mutation;")
        cur.execute("DELETE FROM attestation_verifications;")
        cur.execute("DELETE FROM document_attestations;")
        cur.execute("DELETE FROM signing_keys;")
        cur.execute("DELETE FROM digital_signatures;")
        cur.execute("DELETE FROM case_evidence;")
        cur.execute("DELETE FROM cases;")
        cur.execute("DELETE FROM conflicts;")
        cur.execute("DELETE FROM documents;")
        cur.execute("DELETE FROM audit_log;")
        cur.execute("DELETE FROM users;")
        cur.execute("ALTER TABLE audit_log ENABLE TRIGGER trg_block_audit_log_mutation;")

        # Insert users under 2-role model ('user' and 'admin')
        cur.execute("""
            INSERT INTO users (id, firebase_uid, email, full_name, role) VALUES
            (%s, 'fb_cit_a', 'citizen.a@synthetic.test', 'Ajay Kumar', 'user'),
            (%s, 'fb_cit_b', 'citizen.b@synthetic.test', 'Rohan Sharma', 'user'),
            (%s, 'fb_admin', 'admin.1@synthetic.test', 'Admin Suresh', 'admin');
        """, (CITIZEN_A_ID, CITIZEN_B_ID, ADMIN_ID))

        # Insert documents
        cur.execute("""
            INSERT INTO documents (id, user_id, document_type, file_path, file_hash, masked_id, extracted_fields) VALUES
            (%s, %s, 'aadhaar', '/storage/docs/a_aadhaar.pdf', 'hash_a_123', 'XXXX-XXXX-1234', '{"name": "Ajay Kumar"}'::jsonb),
            (%s, %s, 'pan', '/storage/docs/b_pan.pdf', 'hash_b_456', 'ABCDE1234F', '{"name": "Rohan Sharma"}'::jsonb);
        """, (DOC_A_ID, CITIZEN_A_ID, DOC_B_ID, CITIZEN_B_ID))

        # Insert signing key
        cur.execute("""
            INSERT INTO signing_keys (id, key_id, public_key, fingerprint, algorithm, purpose, status) VALUES
            (%s, 'test-key-1', 'pub_test_123', 'fp_test_123', 'Ed25519', 'document_attestation', 'active');
        """, (KEY_ID,))

        # Insert document attestations
        cur.execute("""
            INSERT INTO document_attestations (id, document_id, citizen_id, officer_id, document_type, document_fingerprint, signing_key_id, key_id, canonical_payload, signature, algorithm, status) VALUES
            (%s, %s, %s, %s, 'aadhaar', '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef', %s, 'test-key-1', '{"test": 1}'::jsonb, 'sig_a', 'Ed25519', 'valid'),
            (%s, %s, %s, %s, 'pan', 'fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210', %s, 'test-key-1', '{"test": 2}'::jsonb, 'sig_b', 'Ed25519', 'valid');
        """, (ATTESTATION_A_ID, DOC_A_ID, CITIZEN_A_ID, ADMIN_ID, KEY_ID,
              ATTESTATION_B_ID, DOC_B_ID, CITIZEN_B_ID, ADMIN_ID, KEY_ID))

        # Insert cryptographically chained audit log entry
        cur.execute("SELECT get_latest_audit_hash();")
        latest_h = cur.fetchone()[0] or '0000000000000000000000000000000000000000000000000000000000000000'
        import hashlib, json
        payload_str = f"{latest_h}|{CITIZEN_A_ID}|DOCUMENT_UPLOAD|documents|{DOC_A_ID}|{json.dumps({}, sort_keys=True)}"
        curr_h = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

        cur.execute("""
            INSERT INTO audit_log (id, user_id, action, entity_type, entity_id, prev_hash, current_hash) VALUES
            (%s, %s, 'DOCUMENT_UPLOAD', 'documents', %s, %s, %s);
        """, (AUDIT_ID, CITIZEN_A_ID, DOC_A_ID, latest_h, curr_h))

    conn.close()
    print("  [OK] Synthetic test fixtures seeded successfully.")

def run_rls_security_tests():
    print("\n==================================================")
    print("   Consolith RLS Security & Isolation Test Suite")
    print("==================================================")
    
    conn = psycopg2.connect(APP_DB_URL)
    conn.autocommit = False
    
    passed_tests = 0
    total_tests = 9

    try:
        # TEST 1: Role privilege check (Must NOT be superuser)
        print("\n[TEST 1/9] Checking database role privileges...")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT current_user, usesuper FROM pg_user WHERE usename = current_user;")
            user_info = cur.fetchone()
            print(f"  Connected as: {user_info['current_user']} (Superuser: {user_info['usesuper']})")
            assert user_info['current_user'] == 'consolith_app', "Connected user must be 'consolith_app'"
            assert user_info['usesuper'] is False, "Application role MUST NOT be a superuser"
            print("  [PASS] Confirmed non-superuser runtime role.")
            passed_tests += 1

        # TEST 2: Unauthenticated Access Isolation (Default-Deny)
        print("\n[TEST 2/9] Testing unauthenticated default-deny isolation...")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Clear session settings
            cur.execute("RESET ALL;")
            cur.execute("SELECT * FROM documents;")
            docs = cur.fetchall()
            cur.execute("SELECT * FROM cases;")
            cases = cur.fetchall()
            cur.execute("SELECT * FROM users;")
            users = cur.fetchall()
            
            print(f"  Unauthenticated visible documents: {len(docs)}, cases: {len(cases)}, users: {len(users)}")
            assert len(docs) == 0, f"Expected 0 documents for unauthenticated user, got {len(docs)}"
            assert len(cases) == 0, f"Expected 0 cases for unauthenticated user, got {len(cases)}"
            assert len(users) == 0, f"Expected 0 users for unauthenticated user, got {len(users)}"
            print("  [PASS] Unauthenticated queries returned 0 rows (Default Deny verified).")
            passed_tests += 1

        # TEST 3: Citizen Cross-Document Read Isolation
        print("\n[TEST 3/9] Testing citizen cross-document read isolation...")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SET LOCAL app.current_user_id = '{CITIZEN_A_ID}';")
            cur.execute("SET LOCAL app.current_user_role = 'citizen';")
            
            cur.execute("SELECT id, masked_id FROM documents;")
            docs = cur.fetchall()
            print(f"  Citizen A queries documents: found {len(docs)} document(s)")
            assert len(docs) == 1, f"Expected exactly 1 document for Citizen A, found {len(docs)}"
            assert str(docs[0]['id']) == DOC_A_ID, "Citizen A must only see their own document"
            
            # Query Citizen B's document directly
            cur.execute(f"SELECT * FROM documents WHERE id = '{DOC_B_ID}';")
            b_docs = cur.fetchall()
            assert len(b_docs) == 0, f"Citizen A must NOT be able to view Citizen B's document"
            print("  [PASS] Citizen A strictly isolated from Citizen B's documents.")
            passed_tests += 1

        # TEST 4: Citizen Cross-Document Write Isolation
        print("\n[TEST 4/9] Testing citizen cross-document write isolation...")
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL app.current_user_id = '{CITIZEN_A_ID}';")
            cur.execute("SET LOCAL app.current_user_role = 'citizen';")
            
            cur.execute(f"UPDATE documents SET masked_id = 'HACKED' WHERE id = '{DOC_B_ID}';")
            rows_updated = cur.rowcount
            print(f"  Citizen A attempt to update Citizen B document: {rows_updated} row(s) updated")
            assert rows_updated == 0, "Citizen A must NOT be able to update Citizen B's records"
            print("  [PASS] Cross-user write attempt blocked by RLS (0 rows affected).")
            passed_tests += 1

        # TEST 5: Privilege Escalation Prevention
        print("\n[TEST 5/9] Testing privilege escalation defense (self-promotion)...")
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL app.current_user_id = '{CITIZEN_A_ID}';")
            cur.execute("SET LOCAL app.current_user_role = 'citizen';")
            
            escalation_blocked = False
            try:
                cur.execute(f"UPDATE users SET role = 'admin' WHERE id = '{CITIZEN_A_ID}';")
            except psycopg2.DatabaseError as e:
                if "Privilege escalation rejected" in str(e):
                    escalation_blocked = True
                    print(f"  Database exception correctly raised: {e.args[0].strip()}")
            conn.rollback() # reset aborted transaction
            
            assert escalation_blocked is True, "Self-promotion from citizen to admin must trigger an exception"
            print("  [PASS] Privilege escalation strictly prevented by database trigger.")
            passed_tests += 1

        # TEST 6: User Attestation RLS Isolation & Deprecated Role Default-Deny
        print("\n[TEST 6/9] Testing user attestation isolation & deprecated role rejection...")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. User A can see their own attestation
            cur.execute(f"SET LOCAL app.current_user_id = '{CITIZEN_A_ID}';")
            cur.execute("SET LOCAL app.current_user_role = 'user';")
            cur.execute("SELECT id, citizen_id FROM document_attestations;")
            attestations_a = cur.fetchall()
            print(f"  User A queries attestations: found {len(attestations_a)} attestation(s)")
            assert len(attestations_a) == 1, f"User A must see only their own attestation, found {len(attestations_a)}"
            assert str(attestations_a[0]['id']) == ATTESTATION_A_ID, "User A saw incorrect attestation"

            # 2. User A cannot see User B's attestation
            cur.execute(f"SELECT * FROM document_attestations WHERE id = '{ATTESTATION_B_ID}';")
            unauthorized_att = cur.fetchall()
            assert len(unauthorized_att) == 0, "User A must NOT see User B's attestation"

            # 3. Deprecated role 'officer' has 0 permissions on attestations (default-deny)
            cur.execute(f"SET LOCAL app.current_user_id = '{CITIZEN_A_ID}';")
            cur.execute("SET LOCAL app.current_user_role = 'officer';")
            cur.execute("SELECT id FROM document_attestations;")
            deprecated_role_att = cur.fetchall()
            assert len(deprecated_role_att) == 0, "Deprecated role 'officer' must have 0 rows (default-deny)"

            print("  [PASS] User attestation RLS isolation and deprecated role rejection verified.")
            passed_tests += 1

        # TEST 7: Admin Visibility Policy
        print("\n[TEST 7/9] Testing admin visibility policy...")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SET LOCAL app.current_user_id = '{ADMIN_ID}';")
            cur.execute("SET LOCAL app.current_user_role = 'admin';")
            
            cur.execute("SELECT count(*) as count FROM users;")
            user_count = cur.fetchone()['count']
            cur.execute("SELECT count(*) as count FROM documents;")
            doc_count = cur.fetchone()['count']
            cur.execute("SELECT count(*) as count FROM cases;")
            case_count = cur.fetchone()['count']
            
            print(f"  Admin sees {user_count} users, {doc_count} documents, {case_count} cases")
            assert user_count == 3, f"Admin must see all 3 users, got {user_count}"
            assert doc_count == 2, f"Admin must see all 2 documents, got {doc_count}"
            print("  [PASS] Admin has authorized full visibility across system entities.")
            passed_tests += 1

        # TEST 8: Append-Only Audit Log Immutability
        print("\n[TEST 8/9] Testing append-only audit trail immutability...")
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL app.current_user_id = '{CITIZEN_A_ID}';")
            cur.execute("SET LOCAL app.current_user_role = 'citizen';")
            
            # Test UPDATE block
            update_blocked = False
            try:
                cur.execute(f"UPDATE audit_log SET action = 'TAMPERED' WHERE id = '{AUDIT_ID}';")
            except psycopg2.DatabaseError as e:
                if "Audit log is append-only" in str(e):
                    update_blocked = True
                    print(f"  UPDATE blocked with exception: {e.args[0].strip()}")
            conn.rollback()
            assert update_blocked is True, "UPDATE on audit_log must be blocked by trigger"
            
            # Test DELETE block
            delete_blocked = False
            try:
                cur.execute(f"DELETE FROM audit_log WHERE id = '{AUDIT_ID}';")
            except psycopg2.DatabaseError as e:
                if "Audit log is append-only" in str(e):
                    delete_blocked = True
                    print(f"  DELETE blocked with exception: {e.args[0].strip()}")
            conn.rollback()
            assert delete_blocked is True, "DELETE on audit_log must be blocked by trigger"
            
            print("  [PASS] Audit log is provably immutable (UPDATE and DELETE blocked).")
            passed_tests += 1

        # TEST 9: Connection Pooling Session Reset & Empty-String UUID Trap
        print("\n[TEST 9/9] Testing connection-pooling session reset & empty string trap...")
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Simulate a connection returned to pool where parameters were set to empty string ""
            cur.execute("SET app.current_user_id = '';")
            cur.execute("SET app.current_user_role = '';")
            
            # This query would fail with invalid syntax if NULLIF was not used in RLS functions
            cur.execute("SELECT * FROM documents;")
            docs = cur.fetchall()
            cur.execute("SELECT * FROM cases;")
            cases = cur.fetchall()
            
            assert len(docs) == 0, "Empty string session must evaluate to NULL and return 0 docs"
            assert len(cases) == 0, "Empty string session must evaluate to NULL and return 0 cases"
            
            # Reset to NULL
            cur.execute("RESET ALL;")
            cur.execute("SELECT * FROM documents;")
            assert len(cur.fetchall()) == 0
            
            print("  [PASS] Connection pooling safely handles empty strings and session resets without crashing.")
            passed_tests += 1

        print("\n==================================================")
        print(f"  ALL {passed_tests}/{total_tests} RLS & ISOLATION TESTS PASSED!")
        print("==================================================")
        return 0

    except Exception as e:
        print(f"\n[FAIL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    seed_synthetic_fixtures()
    sys.exit(run_rls_security_tests())
