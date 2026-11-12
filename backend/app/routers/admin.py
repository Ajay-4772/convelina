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
from app.core.sanitizer import redact_address
from app.core.security_monitoring import get_security_telemetry
from app.dependencies.auth import require_admin
from app.models.user import User
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.assistant import AssistantMessage
from app.models.official_form import OfficialForm
from app.models.pki import DocumentAttestation, SigningKey
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService
from app.schemas.auth import AdminUpdateRoleRequest

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
        "security": get_security_telemetry(),
    }


def _mask_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = "".join(c for c in str(phone) if c.isdigit())
    if len(digits) <= 4:
        return "****"
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


def _mask_dob(dob: Optional[str]) -> Optional[str]:
    if not dob:
        return None
    s = str(dob).strip()
    if len(s) >= 4:
        return f"XX/XX/{s[-4:]}"
    return "[REDACTED_DOB]"


@router.get("/users")
def list_registered_users(
    query: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Allows administrators to search and inspect registered user accounts with minimized PII."""
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
            "phone_number": _mask_phone(u.phone_number),
            "date_of_birth": _mask_dob(u.date_of_birth),
            "address": redact_address(u.address) if u.address else None,
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


@router.post("/users/{user_id}/role")
def admin_update_user_role(
    user_id: UUID,
    req: AdminUpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Explicit, authenticated administrator endpoint to assign or modify user roles.
    Enforces strict two-role model: 'user' or 'admin'.
    Rejects self-demotion or self-escalation.
    Audits every role change into the immutable audit trail.
    """
    set_rls_context(db, current_user.id, current_user.role)

    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot modify their own role via this endpoint."
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found."
        )

    new_role = req.role.lower()
    if new_role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Permitted roles are strictly 'user' and 'admin'."
        )

    old_role = target_user.role

    # Audit the administrative role modification
    AuditService.log_event(
        db=db,
        action="admin_role_updated",
        entity_type="user",
        entity_id=target_user.id,
        user_id=current_user.id,
        details={
            "target_email": target_user.email,
            "previous_role": old_role,
            "new_role": new_role,
        },
    )

    target_user.role = new_role
    target_user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "success": True,
        "message": f"Role updated from '{old_role}' to '{new_role}' for user {target_user.email}.",
        "user_id": str(target_user.id),
        "role": target_user.role,
    }


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


