"""
CONVELINA Database Migration Module
Provides deliberate, sequential, idempotent SQL migration execution
with schema_migrations tracking and application role synchronization.
"""

import os
import sys
import glob
import logging
import psycopg2

logger = logging.getLogger("convelina.migrations")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DATABASE_MIGRATION_URL = os.getenv(
    "DATABASE_MIGRATION_URL",
    os.getenv("DATABASE_URL", "postgresql://postgres:postgres_dev_password@localhost:5432/consolith")
)

APP_DB_PASSWORD = os.getenv("APP_DB_PASSWORD")

def run_migrations(migrations_dir: str = None) -> int:
    """Executes pending SQL migrations sequentially under administrative credentials."""
    logger.info("==================================================")
    logger.info("   CONVELINA Database Migration Engine")
    logger.info("==================================================")
    
    if not migrations_dir:
        # Determine migrations directory relative to package or app root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidate_dirs = [
            os.path.join(base_dir, "migrations"),
            os.path.join(base_dir, "backend", "migrations"),
            "/app/migrations"
        ]
        for d in candidate_dirs:
            if os.path.isdir(d):
                migrations_dir = d
                break

    if not migrations_dir or not os.path.isdir(migrations_dir):
        logger.error(f"Migration directory not found in candidate paths")
        return 1

    migration_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
    if not migration_files:
        logger.error(f"No .sql migration files found in {migrations_dir}")
        return 1

    # Obfuscate credentials for safe logging
    db_target = DATABASE_MIGRATION_URL.split("@")[-1] if "@" in DATABASE_MIGRATION_URL else "target"
    logger.info(f"Target database: {db_target}")
    logger.info(f"Discovered {len(migration_files)} migration files in {migrations_dir}")

    try:
        conn = psycopg2.connect(DATABASE_MIGRATION_URL)
        conn.autocommit = True
    except Exception as e:
        logger.error(f"Unable to connect to database for migrations: {e}")
        return 1

    try:
        with conn.cursor() as cur:
            # 1. Ensure schema_migrations table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)

            # 2. Query already applied migrations
            cur.execute("SELECT version FROM schema_migrations;")
            applied = {row[0] for row in cur.fetchall()}

            # 3. Apply pending migrations sequentially
            applied_count = 0
            for migration_path in migration_files:
                filename = os.path.basename(migration_path)
                if filename in applied:
                    logger.info(f"  [SKIPPED] {filename} (already applied)")
                    continue

                logger.info(f"  [APPLYING] {filename}...")
                with open(migration_path, "r", encoding="utf-8") as f:
                    sql = f.read()

                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (version) VALUES (%s);", (filename,))
                applied_count += 1
                logger.info(f"  [OK] Applied {filename} successfully.")

            # 4. If APP_DB_PASSWORD is provided, synchronize consolith_app password
            if APP_DB_PASSWORD:
                logger.info("Synchronizing 'consolith_app' role credentials with environment...")
                cur.execute("""
                    DO $$
                    BEGIN
                        IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'consolith_app') THEN
                            EXECUTE format('ALTER ROLE consolith_app WITH LOGIN PASSWORD %L', %s);
                        END IF;
                    END
                    $$;
                """, (APP_DB_PASSWORD,))
                logger.info("  [OK] Application role 'consolith_app' credentials synchronized.")

        logger.info("==================================================")
        logger.info(f" Migrations complete: {applied_count} applied, {len(applied)} previously applied.")
        logger.info("==================================================")
        return 0

    except Exception as e:
        logger.error(f"Fatal error during migration execution: {e}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(run_migrations())

