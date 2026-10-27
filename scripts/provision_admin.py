"""
Consolith Security Utilities: Secure Admin Provisioning Script
Usage:
    python scripts/provision_admin.py --email admin@example.com --name "System Administrator"

This script provisions or elevates an administrator account in the Consolith PostgreSQL database.
It cryptographically records the authorization event into the immutable audit trail.
"""

import sys
import os
import argparse
import hashlib
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

def parse_args():
    parser = argparse.ArgumentParser(description="Securely provision an administrator account for Consolith.")
    parser.add_argument("--email", required=True, help="Verified administrator email address")
    parser.add_argument("--name", default="System Administrator", help="Full name of administrator")
    parser.add_argument("--db-url", default=None, help="PostgreSQL connection string (defaults to DATABASE_URL)")
    return parser.parse_args()

def main():
    args = parse_args()
    email = args.email.strip().lower()
    full_name = args.name.strip()

    # Determine database URL
    db_url = args.db_url or os.getenv(
        "DATABASE_URL", 
        "postgresql://consolith_app:consolith_secure_app_pw@localhost:5432/consolith"
    )

    print(f"[CONSOLITH ADMIN PROVISIONER]")
    print(f"Target Email: {email}")
    print(f"Target Name:  {full_name}")

    try:
        engine = create_engine(db_url)
        with engine.begin() as conn:
            # 1. Check if user already exists
            select_query = text("SELECT id, role, email FROM users WHERE LOWER(email) = :email")
            result = conn.execute(select_query, {"email": email}).fetchone()

            if result:
                user_id = result[0]
                old_role = result[1]
                print(f"Existing user found: ID={user_id}, Current Role={old_role}")
                
                if old_role == "admin":
                    print("User is already configured as an administrator. No changes required.")
                    return

                update_query = text("UPDATE users SET role = 'admin', updated_at = NOW() WHERE id = :user_id")
                conn.execute(update_query, {"user_id": user_id})
                print(f"Successfully elevated user {user_id} to 'admin' role.")
            else:
                user_id = uuid.uuid4()
                firebase_uid = f"admin_prov_{uuid.uuid4().hex[:16]}"
                insert_query = text("""
                    INSERT INTO users (id, firebase_uid, email, full_name, role, created_at, updated_at)
                    VALUES (:id, :firebase_uid, :email, :full_name, 'admin', NOW(), NOW())
                """)
                conn.execute(insert_query, {
                    "id": user_id,
                    "firebase_uid": firebase_uid,
                    "email": email,
                    "full_name": full_name
                })
                print(f"Created new administrator account: ID={user_id}")

            # 2. Record immutable audit log entry
            details_payload = {
                "action": "ADMIN_PROVISIONED",
                "target_email": email,
                "target_user_id": str(user_id),
                "authorized_by": "SYSTEM_CLI",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            details_json = json.dumps(details_payload, sort_keys=True)
            prev_hash = "0" * 64
            # Attempt to fetch previous audit hash for cryptographic chaining
            last_audit = conn.execute(text("SELECT record_hash FROM audit_log ORDER BY created_at DESC LIMIT 1")).fetchone()
            if last_audit and last_audit[0]:
                prev_hash = last_audit[0]

            record_hash = hashlib.sha256(f"{prev_hash}:{details_json}".encode("utf-8")).hexdigest()

            conn.execute(text("""
                INSERT INTO audit_log (id, user_id, action, resource_type, details, record_hash, previous_hash, created_at)
                VALUES (:id, :user_id, 'ADMIN_PROVISIONED', 'SYSTEM', :details::jsonb, :record_hash, :prev_hash, NOW())
            """), {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "details": details_json,
                "record_hash": record_hash,
                "prev_hash": prev_hash
            })

            print(f"Immutable audit entry committed. Hash: {record_hash[:16]}...")
            print("\n[SUCCESS] Administrator provisioned successfully.")
            print("The administrator can now sign in with this email at the admin portal.")

    except Exception as e:
        print(f"\n[ERROR] Failed to provision administrator: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
