import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import SessionLocal, set_rls_context
from sqlalchemy import text

def main():
    db = SessionLocal()
    try:
        print("=== Database Role and Identity ===")
        role_info = db.execute(text("SELECT current_user, current_database(), session_user;")).fetchone()
        print(f"Connected as: {role_info}")

        print("\n=== users_role_check Constraint ===")
        res = db.execute(text("""
            SELECT conname, pg_get_constraintdef(c.oid) 
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            WHERE t.relname = 'users' AND c.conname = 'users_role_check';
        """)).fetchall()
        for r in res:
            print(f"{r[0]}: {r[1]}")

        print("\n=== Users Table Distinct Roles (under Admin context) ===")
        set_rls_context(db, None, "admin")
        roles = db.execute(text("SELECT role, count(*) FROM users GROUP BY role;")).fetchall()
        for r in roles:
            print(f"Role: {r[0]}, Count: {r[1]}")

        user_rows = db.execute(text("SELECT id, email, role, full_name FROM users;")).fetchall()
        for u in user_rows:
            print(f"User: id={u[0]}, email={u[1]}, role={u[2]}, name={u[3]}")

        print("\n=== Check All RLS Policies Across All Tables ===")
        policies = db.execute(text("""
            SELECT tablename, policyname, roles, cmd, qual 
            FROM pg_policies 
            WHERE schemaname = 'public' 
            ORDER BY tablename, policyname;
        """)).fetchall()
        officer_policies = []
        for p in policies:
            qual_str = str(p[4]) if p[4] else ""
            if "officer" in p[1].lower() or "officer" in qual_str.lower():
                officer_policies.append(p)
        print(f"Total active RLS policies: {len(policies)}")
        print(f"Policies referencing 'officer': {len(officer_policies)}")
        for op in officer_policies:
            print(f"  Table: {op[0]}, Policy: {op[1]}, Command: {op[3]}, Qual: {op[4]}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
