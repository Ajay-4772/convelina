"""Consolith - Append-Only Cryptographic Audit Log Service

Provides tamper-evident event logging where each audit event's current_hash
is cryptographically linked to the previous event's current_hash using SHA-256.
Database triggers on `audit_log` block any UPDATE or DELETE operations.
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Appends a cryptographically chained audit record to the immutable audit_log."""
        details_dict = details or {}

        # 1. Fetch latest audit event's hash to maintain hash chain
        # Uses SECURITY DEFINER function to read the true system-wide latest hash regardless of tenant RLS scope
        from sqlalchemy import text
        res = db.execute(text("SELECT get_latest_audit_hash();")).scalar()
        prev_hash = res or GENESIS_HASH

        # 2. Compute SHA-256 hash
        payload_string = (
            f"{prev_hash}|"
            f"{str(user_id) if user_id else ''}|"
            f"{action}|"
            f"{entity_type}|"
            f"{str(entity_id) if entity_id else ''}|"
            f"{json.dumps(details_dict, sort_keys=True)}"
        )
        current_hash = hashlib.sha256(payload_string.encode("utf-8")).hexdigest()

        # 3. Create and persist record
        audit_record = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details_dict,
            prev_hash=prev_hash,
            current_hash=current_hash,
        )
        db.add(audit_record)
        db.flush()
        return audit_record
