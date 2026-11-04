#!/usr/bin/env python3
"""
CONVELINA Host Migration Runner
Executes version-controlled SQL migrations in backend/migrations against PostgreSQL.
Supports APP_DB_PASSWORD synchronization and schema_migrations tracking.
"""

import os
import sys

# Ensure backend package is in python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.core.migrate import run_migrations

if __name__ == "__main__":
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "migrations")
    sys.exit(run_migrations(migrations_dir=migrations_dir))
