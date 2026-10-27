"""CONVELINA - Module 8 Case Workflow State Machine

Enforces strict, validated state transitions for verification cases.
Permissible states:
- pending_assignment
- assigned
- under_review
- additional_information_requested
- information_submitted
- approved
- rejected
- closed
"""

from typing import Set, Dict
from fastapi import HTTPException, status

VALID_CASE_STATES: Set[str] = {
    "pending_assignment",
    "assigned",
    "under_review",
    "additional_information_requested",
    "information_submitted",
    "approved",
    "rejected",
    "closed",
}

# Explicit permissible transitions map: current_state -> {allowed_next_states}
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "pending_assignment": {"assigned", "closed"},
    "assigned": {"under_review", "assigned", "closed"},  # "assigned" allows reassignment
    "under_review": {
        "additional_information_requested",
        "approved",
        "rejected",
        "assigned",  # reassigned while reviewing
        "closed",
    },
    "additional_information_requested": {
        "information_submitted",
        "rejected",
        "closed",
    },
    "information_submitted": {
        "under_review",
        "additional_information_requested",
        "approved",
        "rejected",
        "closed",
    },
    "approved": {"closed"},
    "rejected": {"under_review", "closed"},  # allows authorized appeal / reopened review
    "closed": set(),  # terminal state
}


class CaseWorkflowManager:
    @staticmethod
    def validate_transition(current_state: str, next_state: str) -> None:
        """Validates that a proposed state transition is permissible."""
        if current_state not in VALID_CASE_STATES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid current case state: '{current_state}'.",
            )

        if next_state not in VALID_CASE_STATES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target case state: '{next_state}'.",
            )

        allowed = ALLOWED_TRANSITIONS.get(current_state, set())
        if next_state not in allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Illegal state transition from '{current_state}' to '{next_state}'. "
                    f"Permissible transitions: {sorted(list(allowed)) or 'None (Terminal state)'}"
                ),
            )
