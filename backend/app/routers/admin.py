"""CONVELINA - Admin Management & System Overview Router

Provides administrator endpoints to:
- Inspect system-wide real metrics and statistics.
- Manage user accounts (search, review, delete).
- Review immutable audit trail and security activities.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import require_admin
from app.models.user import User
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.assistant import AssistantMessage
from app.models.official_form import OfficialForm
from app.models.pki import DocumentAttestation, SigningKey
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Management"])


@router.get("/overview-stats")
def get_admin_overview_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Returns real operational metrics across all modules for the admin console."""
    set_rls_context(db, current_user.id, current_user.role)

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_platform_users = db.query(func.count(User.id)).filter(User.role.in_(["user", "citizen"])).scalar() or 0
    total_admins = db.query(func.count(User.id)).filter(User.role == "admin").scalar() or 0

    total_docs = db.query(func.count(Document.id)).scalar() or 0
    total_conflicts = db.query(func.count(Conflict.id)).scalar() or 0
    total_assistant_msgs = db.query(func.count(AssistantMessage.id)).scalar() or 0
    total_forms = db.query(func.count(OfficialForm.id)).scalar() or 0
    total_attestations = db.query(func.count(DocumentAttestation.id)).scalar() or 0
    active_keys = db.query(func.count(SigningKey.id)).filter(SigningKey.status == "active").scalar() or 0
    total_audit_events = db.query(func.count(AuditLog.id)).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "users": total_platform_users,
            "citizens": total_platform_users,
            "admins": total_admins,
        },
        "documents": {
            "total_uploaded": total_docs,
        },
        "conflicts": {
            "total_detected": total_conflicts,
        },
        "assistant": {
            "total_messages": total_assistant_msgs,
            "forms_available": total_forms,
        },
        "pki": {
            "total_attestations": total_attestations,
            "active_signing_keys": active_keys,
        },
        "audit": {
            "total_events": total_audit_events,
        },
    }


@router.get("/users")
def list_registered_users(
    query: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Allows administrators to search and inspect registered user accounts."""
    set_rls_context(db, current_user.id, current_user.role)

    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if query:
        search_pattern = f"%{query.strip()}%"
        q = q.filter((User.full_name.ilike(search_pattern)) | (User.email.ilike(search_pattern)))

    users = q.order_by(desc(User.created_at)).limit(limit).all()
    return [
        {
            "id": str(u.id),
            "firebase_uid": u.firebase_uid,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "phone_number": u.phone_number,
            "date_of_birth": u.date_of_birth,
            "address": u.address,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin securely removes a user account and records the action in the audit trail."""
    set_rls_context(db, current_user.id, current_user.role)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot self-delete from this console.")

    AuditService.log_event(
        db=db,
        action="admin_user_deleted",
        entity_type="user",
        entity_id=user.id,
        user_id=current_user.id,
        details={"deleted_email": user.email, "role": user.role},
    )

    db.delete(user)
    db.commit()
    return {"success": True, "message": f"User {user.email} removed successfully."}


@router.get("/system-activity")
def get_system_audit_activity(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Retrieves recent system-wide audit events with SHA-256 cryptographic chain proofs."""
    set_rls_context(db, current_user.id, current_user.role)

    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "details": log.details,
            "prev_hash": log.prev_hash,
            "current_hash": log.current_hash,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/conflicts")
def admin_list_conflicts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Allows administrators to monitor detected statutory discrepancies platform-wide."""
    set_rls_context(db, current_user.id, current_user.role)

    q = db.query(Conflict)
    if status_filter:
        q = q.filter(Conflict.status == status_filter)

    total = q.count()
    conflicts = q.order_by(desc(Conflict.created_at)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [c.to_dict() for c in conflicts],
    }


@router.get("/documents")
def admin_list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    doc_type: Optional[str] = Query(None, alias="document_type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Allows administrators to monitor document upload and OCR processing states platform-wide."""
    set_rls_context(db, current_user.id, current_user.role)

    q = db.query(Document)
    if doc_type:
        q = q.filter(Document.document_type == doc_type)

    total = q.count()
    docs = q.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [d.to_dict() for d in docs],
    }


