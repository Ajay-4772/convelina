#!/usr/bin/env python3
"""
Consolith Migration Runner
Executes version-controlled SQL migrations in backend/migrations against PostgreSQL.
"""

import os
import sys
import glob
import psycopg2

DATABASE_URL = os.getenv(
    "DATABASE_MIGRATION_URL",
    "postgresql://postgres:postgres_dev_password@localhost:5432/consolith"
)

def run_migrations():
    print("==================================================")
    print("        Consolith Database Migration Runner")
    print("==================================================")
    
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "migrations")
    migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
    
    if not migration_files:
        print("[FAIL] No migration files found in backend/migrations")
        return 1

    print(f"Connecting to database: {DATABASE_URL.split('@')[-1]}")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
    except Exception as e:
        print(f"[FAIL] Unable to connect to database: {e}")
        return 1

    try:
        with conn.cursor() as cur:
            # Create schema_migrations table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)

            # Fetch already applied migrations
            cur.execute("SELECT version FROM schema_migrations;")
            applied = {row[0] for row in cur.fetchall()}

            for migration_path in migration_files:
                filename = os.path.basename(migration_path)
                if filename in applied:
                    print(f"  [SKIPPED] {filename} (already applied)")
                    continue

                print(f"  [APPLYING] {filename}...")
                with open(migration_path, "r", encoding="utf-8") as f:
                    sql = f.read()

                # Execute migration
                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (version) VALUES (%s);", (filename,))
                print(f"  [OK] Applied {filename} successfully.")

        print("==================================================")
        print("  ALL MIGRATIONS APPLIED SUCCESSFULLY!")
        print("==================================================")
        return 0
    except Exception as e:
        print(f"[FAIL] Error applying migrations: {e}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(run_migrations())
