"""CONVELINA - Officer Verification Workflow Router

Provides secure endpoints for authorized verification officers:
- Access only assigned discrepancy cases.
- Start review, request clarification from citizens, approve, reject, or return for revision.
- Record decisions with mandatory justifications and immutable audit logs.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user, require_officer
from app.models.user import User
from app.models.case import Case, CaseReviewRequest
from app.models.conflict import Conflict
from app.models.correction_draft import CorrectionDraft
from app.models.audit_log import AuditLog
from app.schemas.case import (
    CaseResponse,
    CaseListResponse,
    CaseDossierResponse,
    CaseReviewRequestResponse,
    CaseRequestInformationRequest,
    CaseDecisionRequest,
)
from app.services.audit_service import AuditService
from app.services.case_workflow import CaseWorkflowManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/officer", tags=["Officer Verification"])


def get_assigned_case_or_404(case_id: UUID, officer_id: UUID, db: Session) -> Case:
    """Helper ensuring an officer can ONLY view and act upon cases assigned specifically to them."""
    case = (
        db.query(Case)
        .filter(Case.id == case_id, Case.assigned_officer_id == officer_id)
        .first()
    )
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned case not found or access denied.",
        )
    return case


@router.get("/cases", response_model=CaseListResponse)
def list_assigned_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Lists all cases assigned to the authenticated officer (enforcing assignment isolation)."""
    set_rls_context(db, current_user.id, current_user.role)

    query = db.query(Case).filter(Case.assigned_officer_id == current_user.id)
    if status_filter:
        query = query.filter(Case.status == status_filter)

    total = query.count()
    cases = query.order_by(desc(Case.updated_at)).offset(skip).limit(limit).all()

    return CaseListResponse(
        total=total,
        items=[CaseResponse.model_validate(c) for c in cases],
    )


@router.get("/cases/{case_id}", response_model=CaseDossierResponse)
def get_case_dossier(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Retrieves full case dossier including discrepancy, draft, clarification requests, and audit events."""
    set_rls_context(db, current_user.id, current_user.role)
    case = get_assigned_case_or_404(case_id, current_user.id, db)

    conflict_data = None
    if case.conflict_id:
        c = db.query(Conflict).filter(Conflict.id == case.conflict_id).first()
        if c:
            conflict_data = c.to_dict()

    draft_data = None
    if case.correction_draft_id:
        d = db.query(CorrectionDraft).filter(CorrectionDraft.id == case.correction_draft_id).first()
        if d:
            draft_data = {
                "id": str(d.id),
                "title": d.title,
                "content": d.content,
                "version": d.version,
                "status": d.status,
                "confirmed_fields": d.confirmed_fields,
                "source_references": d.source_references,
            }

    requests = (
        db.query(CaseReviewRequest)
        .filter(CaseReviewRequest.case_id == case.id)
        .order_by(desc(CaseReviewRequest.created_at))
        .all()
    )

    audit_logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity_id == case.id)
        .order_by(desc(AuditLog.created_at))
        .all()
    )

    return CaseDossierResponse(
        case=CaseResponse.model_validate(case),
        conflict_details=conflict_data,
        correction_draft=draft_data,
        review_requests=[CaseReviewRequestResponse.model_validate(r) for r in requests],
        audit_history=[
            {
                "id": str(a.id),
                "action": a.action,
                "user_id": str(a.user_id) if a.user_id else None,
                "details": a.details,
                "created_at": a.created_at.isoformat(),
                "current_hash": a.current_hash,
            }
            for a in audit_logs
        ],
    )


@router.post("/cases/{case_id}/start-review", response_model=CaseResponse)
def start_review(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Transitions case to 'under_review' and marks start timestamp."""
    set_rls_context(db, current_user.id, current_user.role)
    case = get_assigned_case_or_404(case_id, current_user.id, db)

    CaseWorkflowManager.validate_transition(case.status, "under_review")
    case.status = "under_review"
    if not case.review_started_at:
        case.review_started_at = datetime.utcnow()

    AuditService.log_event(
        db=db,
        action="review_started",
        entity_type="case",
        entity_id=case.id,
        user_id=current_user.id,
    )

    db.commit()
    return CaseResponse.model_validate(case)


@router.post("/cases/{case_id}/request-information", response_model=CaseReviewRequestResponse)
def request_information(
    case_id: UUID,
    req: CaseRequestInformationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Officer requests additional information or clarification from citizen."""
    set_rls_context(db, current_user.id, current_user.role)
    case = get_assigned_case_or_404(case_id, current_user.id, db)

    CaseWorkflowManager.validate_transition(case.status, "additional_information_requested")
    case.status = "additional_information_requested"

    rev_req = CaseReviewRequest(
        case_id=case.id,
        officer_id=current_user.id,
        citizen_id=case.citizen_id,
        request_details=req.request_details,
        request_reason=req.request_reason,
        status="pending",
    )
    db.add(rev_req)
    db.flush()

    AuditService.log_event(
        db=db,
        action="additional_information_requested",
        entity_type="case",
        entity_id=case.id,
        user_id=current_user.id,
        details={"request_id": str(rev_req.id), "reason": req.request_reason},
    )

    db.commit()
    return CaseReviewRequestResponse.model_validate(rev_req)


@router.post("/cases/{case_id}/approve", response_model=CaseResponse)
def approve_case_draft(
    case_id: UUID,
    req: CaseDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Officer approves correction draft for citizen submission."""
    set_rls_context(db, current_user.id, current_user.role)
    case = get_assigned_case_or_404(case_id, current_user.id, db)

    CaseWorkflowManager.validate_transition(case.status, "approved")
    case.status = "approved"
    case.decision = "approved"
    case.decision_reason = req.decision_reason
    case.decision_timestamp = datetime.utcnow()
    if req.officer_notes:
        case.officer_notes = req.officer_notes

    # Update attached draft status to approved
    if case.correction_draft_id:
        draft = db.query(CorrectionDraft).filter(CorrectionDraft.id == case.correction_draft_id).first()
        if draft:
            draft.status = "approved"

    AuditService.log_event(
        db=db,
        action="draft_approved",
        entity_type="case",
        entity_id=case.id,
        user_id=current_user.id,
        details={"decision_reason": req.decision_reason},
    )

    db.commit()
    return CaseResponse.model_validate(case)


@router.post("/cases/{case_id}/reject", response_model=CaseResponse)
def reject_case_draft(
    case_id: UUID,
    req: CaseDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Officer rejects correction draft with mandatory explanation."""
    set_rls_context(db, current_user.id, current_user.role)
    case = get_assigned_case_or_404(case_id, current_user.id, db)

    CaseWorkflowManager.validate_transition(case.status, "rejected")
    case.status = "rejected"
    case.decision = "rejected"
    case.decision_reason = req.decision_reason
    case.decision_timestamp = datetime.utcnow()
    if req.officer_notes:
        case.officer_notes = req.officer_notes

    AuditService.log_event(
        db=db,
        action="draft_rejected",
        entity_type="case",
        entity_id=case.id,
        user_id=current_user.id,
        details={"decision_reason": req.decision_reason},
    )

    db.commit()
    return CaseResponse.model_validate(case)
