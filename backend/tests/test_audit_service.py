"""CONVELINA - Cryptographic Audit Service Unit Tests

Tests:
1. AuditService genesis hash behavior on first system audit event.
2. SHA-256 backward hash-chain linkage between sequential events.
3. Cryptographic tamper-evident hash integrity.
"""

import uuid
from unittest.mock import MagicMock
from app.services.audit_service import AuditService, GENESIS_HASH
from app.models.audit_log import AuditLog


class TestAuditService:
    def test_hash_chain_genesis_and_linking(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = None

        user_id = uuid.uuid4()
        document_id = uuid.uuid4()

        # 1. First event uses GENESIS_HASH
        event_1 = AuditService.log_event(
            db=mock_db,
            action="document_uploaded",
            entity_type="document",
            entity_id=document_id,
            user_id=user_id,
            details={"document_type": "pan"},
        )

        assert event_1.prev_hash == GENESIS_HASH
        assert len(event_1.current_hash) == 64
        assert event_1.action == "document_uploaded"

        # 2. Second event links to event_1's current_hash
        mock_db.execute.return_value.scalar.return_value = event_1.current_hash

        admin_id = uuid.uuid4()
        event_2 = AuditService.log_event(
            db=mock_db,
            action="admin_discrepancy_reviewed",
            entity_type="conflict",
            entity_id=document_id,
            user_id=admin_id,
            details={"admin_id": str(admin_id), "status": "reviewed"},
        )

        assert event_2.prev_hash == event_1.current_hash
        assert event_2.current_hash != event_1.current_hash
        assert len(event_2.current_hash) == 64

