"""CONVELINA - Citizen Case Submission & Tracking Router

Provides citizen-facing endpoints for:
- Submitting an identified conflict and correction draft for verification.
- Tracking review status and officer feedback.
- Responding to officer requests for additional information.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user, require_citizen
from app.models.user import User
from app.models.case import Case, CaseReviewRequest
from app.models.conflict import Conflict
from app.models.correction_draft import CorrectionDraft
from app.schemas.case import (
    CaseCreateRequest,
    CaseResponse,
    CaseListResponse,
    CaseReviewRequestResponse,
    CaseRespondInformationRequest,
    CaseDossierResponse,
)
from app.services.audit_service import AuditService
from app.services.case_workflow import CaseWorkflowManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cases", tags=["Citizen Cases"])


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def submit_case_for_verification(
    req: CaseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_citizen),
):
    """Submits a discrepancy case and draft for officer verification under RLS."""
    set_rls_context(db, current_user.id, current_user.role)

    # 1. Verify conflict ownership if provided
    if req.conflict_id:
        conflict = db.query(Conflict).filter(Conflict.id == req.conflict_id, Conflict.user_id == current_user.id).first()
        if not conflict:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced conflict not found.")

    # 2. Verify correction draft ownership if provided
    if req.correction_draft_id:
        draft = db.query(CorrectionDraft).filter(CorrectionDraft.id == req.correction_draft_id, CorrectionDraft.user_id == current_user.id).first()
        if not draft:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced correction draft not found.")

    # 3. Create case record
    case = Case(
        citizen_id=current_user.id,
        conflict_id=req.conflict_id,
        correction_draft_id=req.correction_draft_id,
        status="pending_assignment",
        title=req.title,
        evidence_notes=req.evidence_notes,
    )
    db.add(case)
    db.flush()

    # 4. Cryptographic audit log
    AuditService.log_event(
        db=db,
        action="case_submitted",
        entity_type="case",
        entity_id=case.id,
        user_id=current_user.id,
        details={"title": case.title, "conflict_id": str(req.conflict_id) if req.conflict_id else None},
    )

    db.commit()
    return CaseResponse.model_validate(case)


@router.get("/my-cases", response_model=CaseListResponse)
def list_my_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_citizen),
):
    """Lists all cases submitted by the authenticated citizen (strictly isolated by RLS)."""
    set_rls_context(db, current_user.id, current_user.role)

    query = db.query(Case).filter(Case.citizen_id == current_user.id)
    total = query.count()
    cases = query.order_by(desc(Case.updated_at)).offset(skip).limit(limit).all()

    return CaseListResponse(
        total=total,
        items=[CaseResponse.model_validate(c) for c in cases],
    )


@router.get("/{case_id}/review-status", response_model=CaseDossierResponse)
def get_case_review_status(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_citizen),
):
    """Retrieves real-time review status, officer decision, and clarification requests for a citizen's case."""
    set_rls_context(db, current_user.id, current_user.role)

    case = db.query(Case).filter(Case.id == case_id, Case.citizen_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

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
            }

    requests = db.query(CaseReviewRequest).filter(CaseReviewRequest.case_id == case.id).order_by(desc(CaseReviewRequest.created_at)).all()

    return CaseDossierResponse(
        case=CaseResponse.model_validate(case),
        conflict_details=conflict_data,
        correction_draft=draft_data,
        review_requests=[CaseReviewRequestResponse.model_validate(r) for r in requests],
        audit_history=[],
    )


@router.post("/{case_id}/review-requests/{request_id}/respond", response_model=CaseReviewRequestResponse)
def respond_to_review_request(
    case_id: UUID,
    request_id: UUID,
    req: CaseRespondInformationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_citizen),
):
    """Citizen responds to an officer's additional information request."""
    set_rls_context(db, current_user.id, current_user.role)

    case = db.query(Case).filter(Case.id == case_id, Case.citizen_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    rev_req = db.query(CaseReviewRequest).filter(
        CaseReviewRequest.id == request_id,
        CaseReviewRequest.case_id == case.id,
        CaseReviewRequest.citizen_id == current_user.id,
    ).first()

    if not rev_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review request not found.")

    if rev_req.status == "responded":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This request has already been answered.")

    # 1. Update review request
    rev_req.response_text = req.response_text
    rev_req.response_timestamp = datetime.utcnow()
    rev_req.status = "responded"

    # 2. Advance case state to 'information_submitted'
    CaseWorkflowManager.validate_transition(case.status, "information_submitted")
    case.status = "information_submitted"

    # 3. Log cryptographic audit event
    AuditService.log_event(
        db=db,
        action="citizen_information_submitted",
        entity_type="case",
        entity_id=case.id,
        user_id=current_user.id,
        details={"request_id": str(request_id), "response_length": len(req.response_text)},
    )

    db.commit()
    return CaseReviewRequestResponse.model_validate(rev_req)
