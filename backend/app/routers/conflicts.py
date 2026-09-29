import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.conflict import Conflict
from app.conflicts.engine import ConflictDetectionEngine
from app.conflicts.schemas import (
    ConflictResponse,
    ConflictListResponse,
    ConflictReviewUpdate,
    ConflictDetectResponse,
)

logger = logging.getLogger("consolith.conflicts.router")
router = APIRouter(prefix="/api/v1/conflicts", tags=["Conflicts"])

VALID_STATUSES = {"detected", "in_review", "resolved", "ignored"}


@router.post("/detect", response_model=ConflictDetectResponse, status_code=status.HTTP_200_OK)
def detect_conflicts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Triggers conflict detection across all completed documents belonging to the authenticated citizen.
    Protected by PostgreSQL Row-Level Security: operates strictly within citizen data scope.
    """
    try:
        set_rls_context(db, current_user.id, current_user.role)
        engine = ConflictDetectionEngine(db)
        result = engine.run_detection_for_user(current_user.id)
        db.commit()

        return ConflictDetectResponse(
            total_documents_analyzed=result["total_documents_analyzed"],
            total_conflicts_detected=result["total_conflicts_detected"],
            new_conflicts_created=result["new_conflicts_created"],
            conflicts=[ConflictResponse(**c) for c in result["conflicts"]],
            message=result["message"],
        )
    except Exception as e:
        db.rollback()
        logger.error("Conflict detection failed for user %s: %s", current_user.id, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete conflict detection analysis.",
        )


@router.get("", response_model=ConflictListResponse)
def list_conflicts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by conflict status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Lists conflicts visible to the current authenticated caller.
    Protected by PostgreSQL Row-Level Security:
    - Citizens see only conflicts derived from their own documents.
    - Admins see all conflicts.
    - Officers see conflicts within their assigned citizen scope.
    """
    set_rls_context(db, current_user.id, current_user.role)
    query = db.query(Conflict)

    if status_filter:
        clean_status = status_filter.strip().lower()
        if clean_status in VALID_STATUSES:
            query = query.filter(Conflict.status == clean_status)

    total = query.count()
    records = query.order_by(Conflict.created_at.desc()).offset(skip).limit(limit).all()

    conflicts_data = [ConflictResponse(**r.to_dict()) for r in records]
    return ConflictListResponse(total=total, conflicts=conflicts_data)


@router.get("/{conflict_id}", response_model=ConflictResponse)
def get_conflict(
    conflict_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a single conflict record by ID with ownership enforcement via RLS.
    """
    set_rls_context(db, current_user.id, current_user.role)
    record = db.query(Conflict).filter(Conflict.id == conflict_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict record not found or access denied.",
        )

    return ConflictResponse(**record.to_dict())


@router.patch("/{conflict_id}/review", response_model=ConflictResponse)
def update_conflict_review(
    conflict_id: UUID,
    payload: ConflictReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the review status of a conflict record.
    Allowed statuses: detected, in_review, resolved, ignored.
    Enforces RLS: callers can only review conflicts they own or are assigned to oversee.
    """
    new_status = payload.status.strip().lower()
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    set_rls_context(db, current_user.id, current_user.role)
    record = db.query(Conflict).filter(Conflict.id == conflict_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict record not found or unauthorized to update.",
        )

    record.status = new_status
    db.flush()

    response_data = ConflictResponse(**record.to_dict())
    db.commit()

    return response_data
