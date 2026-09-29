"""Consolith - Module 8 Officer Verification Workflow Unit Tests

Tests:
1. CaseWorkflowManager state transitions (valid vs illegal transitions)
2. Terminal states behavior
3. Cryptographic hash-chaining audit service (SHA-256 chain integrity)
"""

import uuid
import pytest
from fastapi import HTTPException
from app.services.case_workflow import CaseWorkflowManager, VALID_CASE_STATES
from app.services.audit_service import AuditService, GENESIS_HASH
from app.models.audit_log import AuditLog
from unittest.mock import MagicMock


class TestCaseWorkflowManager:
    def test_valid_transitions(self):
        # pending_assignment -> assigned
        CaseWorkflowManager.validate_transition("pending_assignment", "assigned")
        # assigned -> under_review
        CaseWorkflowManager.validate_transition("assigned", "under_review")
        # under_review -> additional_information_requested
        CaseWorkflowManager.validate_transition("under_review", "additional_information_requested")
        # additional_information_requested -> information_submitted
        CaseWorkflowManager.validate_transition("additional_information_requested", "information_submitted")
        # information_submitted -> approved
        CaseWorkflowManager.validate_transition("information_submitted", "approved")
        # approved -> closed
        CaseWorkflowManager.validate_transition("approved", "closed")

    def test_illegal_transitions_raise_409(self):
        # Cannot jump from pending_assignment directly to approved
        with pytest.raises(HTTPException) as exc_info:
            CaseWorkflowManager.validate_transition("pending_assignment", "approved")
        assert exc_info.value.status_code == 409

        # Cannot jump from additional_information_requested directly to approved
        with pytest.raises(HTTPException) as exc_info:
            CaseWorkflowManager.validate_transition("additional_information_requested", "approved")
        assert exc_info.value.status_code == 409

    def test_invalid_state_names_raise_400(self):
        with pytest.raises(HTTPException) as exc_info:
            CaseWorkflowManager.validate_transition("invalid_state", "assigned")
        assert exc_info.value.status_code == 400

        with pytest.raises(HTTPException) as exc_info:
            CaseWorkflowManager.validate_transition("assigned", "unknown_target")
        assert exc_info.value.status_code == 400

    def test_reassignment_transitions(self):
        # Reassignment allowed from assigned -> assigned
        CaseWorkflowManager.validate_transition("assigned", "assigned")
        # Reassignment allowed while under_review -> assigned
        CaseWorkflowManager.validate_transition("under_review", "assigned")

    def test_rejection_and_appeal_transitions(self):
        # under_review -> rejected
        CaseWorkflowManager.validate_transition("under_review", "rejected")
        # rejected -> under_review (appeal / reopened)
        CaseWorkflowManager.validate_transition("rejected", "under_review")
        # rejected -> closed
        CaseWorkflowManager.validate_transition("rejected", "closed")


class TestAuditService:
    def test_hash_chain_genesis_and_linking(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar.return_value = None

        user_id = uuid.uuid4()
        case_id = uuid.uuid4()

        # 1. First event uses GENESIS_HASH
        event_1 = AuditService.log_event(
            db=mock_db,
            action="case_submitted",
            entity_type="case",
            entity_id=case_id,
            user_id=user_id,
            details={"title": "Test Case"},
        )

        assert event_1.prev_hash == GENESIS_HASH
        assert len(event_1.current_hash) == 64
        assert event_1.action == "case_submitted"

        # 2. Second event links to event_1's current_hash
        mock_db.execute.return_value.scalar.return_value = event_1.current_hash

        officer_id = uuid.uuid4()
        event_2 = AuditService.log_event(
            db=mock_db,
            action="case_assigned",
            entity_type="case",
            entity_id=case_id,
            user_id=officer_id,
            details={"officer_id": str(officer_id)},
        )

        assert event_2.prev_hash == event_1.current_hash
        assert event_2.current_hash != event_1.current_hash
        assert len(event_2.current_hash) == 64
