#!/usr/bin/env python3
"""
CONVELINA - Administrative Role Provisioning Script (CLI)

Allows authorized system operators with direct database access to securely
promote a user to the 'admin' role. Bypasses client-driven injection and
records an immutable, hash-chained audit event.

Usage:
    python backend/scripts/promote_admin.py --email admin@example.com
    python backend/scripts/promote_admin.py --user-id 12345678-1234-1234-1234-123456789abc
"""

import sys
import argparse
import logging
from uuid import UUID

from app.core.database import SessionLocal, set_rls_context
from app.models.user import User
from app.services.audit_service import AuditService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("promote_admin")


def promote_user_to_admin(email: str = None, user_id_str: str = None) -> bool:
    db = SessionLocal()
    try:
        # Step 1: Set database administrative session context to satisfy PostgreSQL anti-escalation trigger
        db.execute(text("SET LOCAL app.current_user_role = 'admin';"))

        # Step 2: Resolve user
        user = None
        if user_id_str:
            try:
                uid = UUID(user_id_str)
                user = db.query(User).filter(User.id == uid).first()
            except ValueError:
                logger.error(f"Invalid UUID string: {user_id_str}")
                return False
        elif email:
            clean_email = email.strip().lower()
            user = db.query(User).filter(func.lower(User.email) == clean_email).first()

        if not user:
            logger.error(f"Target user not found (email={email}, user_id={user_id_str}).")
            return False

        if user.role == "admin":
            logger.info(f"User {user.email} ({user.id}) is already an administrator. No changes made.")
            return True

        old_role = user.role
        user.role = "admin"

        # Step 3: Record immutable audit trail entry
        AuditService.log_event(
            db=db,
            action="admin_promoted_via_cli",
            entity_type="user",
            entity_id=user.id,
            user_id=user.id,
            details={
                "email": user.email,
                "previous_role": old_role,
                "new_role": "admin",
                "method": "cli_script",
            },
        )

        db.commit()
        logger.info(f"SUCCESS: Promoted user {user.email} (ID: {user.id}) from '{old_role}' to 'admin'.")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to promote user: {e}")
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Securely promote a CONVELINA user to administrator.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--email", help="Email address of the user to promote")
    group.add_argument("--user-id", dest="user_id", help="UUID of the user to promote")

    args = parser.parse_args()

    # Import SQLAlchemy text and func inside main execution context
    from sqlalchemy import text, func

    success = promote_user_to_admin(email=args.email, user_id_str=args.user_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    from sqlalchemy import text, func
    main()
