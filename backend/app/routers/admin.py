"""Consolith - Admin Case Assignment & Workload Management Router

Provides administrator endpoints to:
- Inspect eligible cases and officer workloads.
- Assign cases to verified officer accounts.
- Reassign cases with full cryptographic audit logging.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.models.case import Case
from app.schemas.case import (
    CaseResponse,
    CaseListResponse,
    CaseAssignRequest,
    OfficerWorkloadItem,
)
from app.services.audit_service import AuditService
from app.services.case_workflow import CaseWorkflowManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Case Assignment"])


@router.get("/officers", response_model=List[OfficerWorkloadItem])
def list_officers_workload(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Lists all verified officer accounts and their active case workloads."""
    set_rls_context(db, current_user.id, current_user.role)

    officers = db.query(User).filter(User.role == "officer").all()
    results = []

    for off in officers:
        active_count = (
            db.query(func.count(Case.id))
            .filter(
                Case.assigned_officer_id == off.id,
                Case.status.in_(["assigned", "under_review", "additional_information_requested", "information_submitted"]),
            )
            .scalar() or 0
        )
        completed_count = (
            db.query(func.count(Case.id))
            .filter(
                Case.assigned_officer_id == off.id,
                Case.status.in_(["approved", "rejected", "closed"]),
            )
            .scalar() or 0
        )
        results.append(
            OfficerWorkloadItem(
                officer_id=off.id,
                officer_name=off.full_name,
                officer_email=off.email,
                assigned_active_cases=active_count,
                completed_reviews=completed_count,
            )
        )

    return results


@router.get("/cases", response_model=CaseListResponse)
def list_all_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin views all cases across the system."""
    set_rls_context(db, current_user.id, current_user.role)

    query = db.query(Case)
    if status_filter:
        query = query.filter(Case.status == status_filter)

    total = query.count()
    cases = query.order_by(desc(Case.created_at)).offset(skip).limit(limit).all()

    return CaseListResponse(
        total=total,
        items=[CaseResponse.model_validate(c) for c in cases],
    )


@router.post("/cases/{case_id}/assign", response_model=CaseResponse)
def assign_case_to_officer(
    case_id: UUID,
    req: CaseAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Assigns an unassigned or pending case to an authorized officer."""
    set_rls_context(db, current_user.id, current_user.role)

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    # Verify officer exists and has officer role
    officer = db.query(User).filter(User.id == req.officer_id, User.role == "officer").first()
    if not officer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target user is not an active verified officer.")

    CaseWorkflowManager.validate_transition(case.status, "assigned")
    case.assigned_officer_id = officer.id
    case.status = "assigned"

    AuditService.log_event(
        db=db,
        action="case_assigned",
        entity_type="case",
        entity_id=case.id,
        user_id=current_user.id,
        details={"officer_id": str(officer.id), "officer_name": officer.full_name},
    )

    db.commit()
    return CaseResponse.model_validate(case)


@router.post("/cases/{case_id}/reassign", response_model=CaseResponse)
def reassign_case_to_officer(
    case_id: UUID,
    req: CaseAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Reassigns an ongoing case to a different authorized officer."""
    set_rls_context(db, current_user.id, current_user.role)

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    officer = db.query(User).filter(User.id == req.officer_id, User.role == "officer").first()
    if not officer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target user is not an active verified officer.")

    prev_officer_id = str(case.assigned_officer_id) if case.assigned_officer_id else None

    # Transition validation (reassignment permitted from assigned or under_review)
    CaseWorkflowManager.validate_transition(case.status, "assigned")
    case.assigned_officer_id = officer.id
    case.status = "assigned"

    AuditService.log_event(
        db=db,
        action="case_reassigned",
        entity_type="case",
        entity_id=case.id,
        user_id=current_user.id,
        details={
            "previous_officer_id": prev_officer_id,
            "new_officer_id": str(officer.id),
            "new_officer_name": officer.full_name,
        },
    )

    db.commit()
    return CaseResponse.model_validate(case)
