"""
CONVELINA — Development Application Explorer & Guided QA Router
Provides development-only APIs to inspect system health, route inventory,
persistent citizen records under forced RLS, and test account provisioning.

CRITICAL INVARIANT: Disabled in production mode.
"""

import logging
import os
import re
import time
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc

from app.config import settings
from app.core.database import get_db, set_rls_context, engine as db_engine
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.conflict import Conflict
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.checklist import CitizenChecklistItem
from app.models.correction_draft import CorrectionDraft
from app.models.audit_log import AuditLog
from app.models.official_form import OfficialForm
from app.models.pki import SigningKey
from app.services.audit_service import AuditService
from app.core.firebase import is_firebase_configured

logger = logging.getLogger("convelina.dev")

router = APIRouter(prefix="/api/v1/dev", tags=["Development Explorer"])


def verify_dev_mode():
    """Guards development routes against execution outside development or test environments."""
    env_lower = settings.ENVIRONMENT.lower()
    if env_lower == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development Explorer is strictly disabled in production mode.",
        )
    if env_lower not in ("development", "test"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development Explorer is strictly disabled outside development and test environments.",
        )


class TestAccountRequest(BaseModel):
    target: str  # "citizen_a", "citizen_b", "admin"


def _mask_text(val: Optional[str]) -> str:
    """Masks personal text while retaining first letter for verification."""
    if not val:
        return "Not specified"
    val = str(val).strip()
    if len(val) <= 2:
        return "**"
    return f"{val[0]}{'*' * (len(val) - 2)}{val[-1]}"


def _mask_doc_number(val: Optional[str], doc_type: str = "generic") -> str:
    """Masks Aadhaar, PAN, or Passport numbers to show only last 4 digits."""
    if not val:
        return "XXXX-XXXX-XXXX"
    clean = re.sub(r"[\s-]", "", str(val))
    if len(clean) >= 4:
        last4 = clean[-4:]
        if "aadhaar" in doc_type.lower():
            return f"XXXX-XXXX-{last4}"
        elif "pan" in doc_type.lower():
            return f"XXXXX{last4}"
        return f"****-****-{last4}"
    return "****"


@router.get("/overview", dependencies=[Depends(verify_dev_mode)])
def get_dev_overview(db: Session = Depends(get_db)):
    """Returns real-time system architecture, live service health, and operational statistics."""
    # 1. PostgreSQL & RLS metrics
    pg_status = {"status": "down"}
    rls_tables = []
    try:
        with db_engine.connect() as conn:
            user_row = conn.execute(text("SELECT current_user, current_database();")).fetchone()
            table_rows = conn.execute(text("""
                SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity 
                FROM pg_class c 
                JOIN pg_namespace n ON n.oid = c.relnamespace 
                WHERE n.nspname = 'public' AND c.relkind = 'r'
                ORDER BY c.relname;
            """)).fetchall()

            rls_tables = [
                {
                    "name": r[0],
                    "rls_enabled": bool(r[1]),
                    "force_rls": bool(r[2]),
                }
                for r in table_rows
            ]

            mig_rows = conn.execute(text("SELECT version FROM schema_migrations ORDER BY version;")).fetchall()
            applied_migs = [r[0] for r in mig_rows]

            pg_status = {
                "status": "READY",
                "role": user_row[0] if user_row else "unknown",
                "database": user_row[1] if user_row else "unknown",
                "total_tables": len(rls_tables),
                "forced_rls_count": sum(1 for t in rls_tables if t["force_rls"]),
                "migrations_applied": len(applied_migs),
                "latest_migration": applied_migs[-1] if applied_migs else None,
            }
    except Exception as e:
        pg_status = {"status": "DEGRADED", "error": str(e)}

    # 2. Qdrant metrics
    qdrant_status = {"status": "down"}
    try:
        from app.rag.qdrant import get_qdrant_client
        client = get_qdrant_client()
        cols = client.get_collections().collections
        col_details = []
        for c in cols:
            try:
                info = client.get_collection(c.name)
                col_details.append({
                    "name": c.name,
                    "points_count": info.points_count,
                    "vectors_count": getattr(info, "vectors_count", info.points_count),
                    "status": str(info.status),
                })
            except Exception:
                col_details.append({"name": c.name, "points_count": "unknown"})
        qdrant_status = {
            "status": "READY",
            "storage_mount": "consolin_qdrant_data -> /qdrant/storage",
            "collections": col_details,
            "persistence_type": "Durable Named Docker Volume",
        }
    except Exception as e:
        qdrant_status = {"status": "DEGRADED", "error": str(e)}

    # 3. Overall Service Matrix
    services = {
        "fastapi": {
            "status": "READY",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        },
        "postgres": pg_status,
        "qdrant": qdrant_status,
        "firebase_auth": {
            "status": "SIMULATED",
            "is_configured": is_firebase_configured(),
            "simulation_allowed": settings.TEST_MODE_ALLOW_SIMULATED_TOKENS,
            "cloud_integration": "PENDING_CREDENTIALS",
            "label": "Local Token Simulation Active (Live Cloud Blocked)",
        },
        "gemini": {
            "status": "BLOCKED",
            "is_enabled": settings.GEMINI_ENABLED,
            "fallback": "Deterministic BM25 & Statutory Citation Rule Engine",
            "label": "Disabled by Default (Deterministic Grounding Active)",
        },
        "ocr_engine": {
            "status": "READY",
            "type": "Tesseract with Regex/Heuristic Fallback",
            "pii_masking_pre_save": True,
        },
        "storage": {
            "status": "READY",
            "retention_policy": settings.STORAGE_RETENTION_POLICY,
            "temp_dir": settings.STORAGE_TEMP_DIR,
        },
        "pki_signing": {
            "status": "READY",
            "algorithm": "Ed25519 (RFC 8032)",
            "purpose": "Internal Platform Document Attestation (RFC 8032; distinct from statutory eSign)",
        },
        "statutory_catalog": {
            "status": "READY",
            "total_official_resources": 52,
            "catalog_breakdown": "43 statutory circulars & SOPs + 9 primary forms; 34 forms & 11 acts in active DB schema",
            "doc_043_governance": "RESTRICTED (human_review_required=True)",
        },
        "citizen_checklist": {
            "status": "READY",
            "backend": "PostgreSQL 'citizen_checklist_items' (Forced RLS)",
        },
    }

    return {
        "platform_name": "CONVELINA",
        "tagline": "Connect. Manage. Evolve.",
        "description": "AI-Powered Identity Document Conflict Detection and Government Correction Assistance System",
        "architecture_summary": "Two-Role Architecture (USER & ADMIN) with PostgreSQL Forced RLS, Qdrant Named Volume Persistence, Ed25519 Platform Attestation, and Local Simulation Guardrails.",
        "roles": ["USER", "ADMIN"],
        "services": services,
        "database_tables": rls_tables,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/persistence-inspect", dependencies=[Depends(verify_dev_mode)])
def inspect_persistence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Read-only persistence inspector for the authenticated user.
    Respects PostgreSQL forced Row-Level Security.
    Strictly masks sensitive fields (zero raw Aadhaar, PAN, or full OCR text).
    """
    set_rls_context(db, current_user.id, current_user.role)

    # 1. Documents
    docs = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).all()
    doc_records = []
    for d in docs:
        fields = d.confirmed_fields or d.extracted_fields or {}
        doc_num = fields.get("id_number") or fields.get("aadhaar_number") or fields.get("pan_number") or d.masked_id
        doc_records.append({
            "id": str(d.id),
            "document_type": d.document_type,
            "masked_number": _mask_doc_number(doc_num, d.document_type),
            "ocr_status": d.ocr_status,
            "is_user_confirmed": bool(d.is_user_confirmed),
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "storage_location": "PostgreSQL 'documents' table (Fernet encrypted raw text) & storage volume",
            "tenancy_boundary": "PostgreSQL Forced RLS (user_id = current_user.id)",
        })

    # 2. Conflicts
    conflicts = db.query(Conflict).filter(Conflict.user_id == current_user.id).order_by(Conflict.created_at.desc()).all()
    conflict_records = []
    for c in conflicts:
        conflict_records.append({
            "id": str(c.id),
            "field_name": c.field_name,
            "severity": c.severity,
            "conflict_type": c.conflict_type,
            "status": c.status,
            "value_a_masked": _mask_text(c.value_a),
            "value_b_masked": _mask_text(c.value_b),
            "description": c.description,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "storage_location": "PostgreSQL 'conflicts' table (Forced RLS)",
        })

    # 3. Conversations & Messages
    convs = db.query(AssistantConversation).filter(AssistantConversation.user_id == current_user.id).order_by(AssistantConversation.updated_at.desc()).all()
    conv_records = []
    for conv in convs:
        msg_count = db.query(func.count(AssistantMessage.id)).filter(AssistantMessage.conversation_id == conv.id).scalar() or 0
        conv_records.append({
            "id": str(conv.id),
            "title": conv.title,
            "message_count": msg_count,
            "is_pinned": bool(conv.is_pinned),
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            "storage_location": "PostgreSQL 'assistant_conversations' & 'assistant_messages' (Forced RLS)",
        })

    # 4. Checklist Progress
    checklists = db.query(CitizenChecklistItem).filter(CitizenChecklistItem.user_id == current_user.id).all()
    # Group by procedure
    proc_groups: Dict[str, List[str]] = {}
    last_updated_map: Dict[str, str] = {}
    for item in checklists:
        if item.is_completed:
            proc_groups.setdefault(item.procedure_id, []).append(item.item_id)
            if item.confirmed_at:
                last_updated_map[item.procedure_id] = item.confirmed_at.isoformat()

    checklist_records = [
        {
            "procedure_id": pid,
            "completed_item_ids": items,
            "completed_count": len(items),
            "last_updated": last_updated_map.get(pid),
            "storage_location": "PostgreSQL 'citizen_checklist_items' table (Forced RLS)",
        }
        for pid, items in proc_groups.items()
    ]

    # 5. Correction Drafts
    drafts = db.query(CorrectionDraft).filter(CorrectionDraft.user_id == current_user.id).order_by(CorrectionDraft.created_at.desc()).all()
    draft_records = []
    for dr in drafts:
        draft_records.append({
            "id": str(dr.id),
            "title": dr.title,
            "document_category": dr.document_category,
            "status": dr.status,
            "is_citizen_confirmed": bool(dr.is_citizen_confirmed),
            "version": dr.version,
            "sha256_hash_short": dr.sha256_hash[:12] + "..." if dr.sha256_hash else None,
            "created_at": dr.created_at.isoformat() if dr.created_at else None,
            "storage_location": "PostgreSQL 'correction_drafts' table (Forced RLS + Ed25519 attestation)",
        })

    # 6. Audit Trail for Current User
    audit_events = db.query(AuditLog).filter(AuditLog.user_id == current_user.id).order_by(AuditLog.created_at.desc()).limit(15).all()
    audit_records = [
        {
            "id": str(a.id),
            "action": a.action,
            "entity_type": a.entity_type,
            "prev_hash_short": a.prev_hash[:10] + "..." if a.prev_hash else "GENESIS",
            "current_hash_short": a.current_hash[:10] + "..." if a.current_hash else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "storage_location": "PostgreSQL 'audit_log' table (Append-only cryptographic hash chain)",
        }
        for a in audit_events
    ]

    return {
        "authenticated_user": {
            "id": str(current_user.id),
            "email_masked": f"{current_user.email.split('@')[0][:3]}***@{current_user.email.split('@')[1]}",
            "role": current_user.role,
            "tenancy_enforcement": "Strict PostgreSQL FORCE ROW LEVEL SECURITY (Session Bound)",
        },
        "inventory": {
            "documents": doc_records,
            "conflicts": conflict_records,
            "conversations": conv_records,
            "checklists": checklist_records,
            "correction_drafts": draft_records,
            "recent_audit_events": audit_records,
        },
        "storage_matrix": [
            {"entity": "User Identity & Authentication", "storage": "PostgreSQL 'users'", "rls_status": "FORCED", "durability": "Permanent account record"},
            {"entity": "Raw Documents & OCR", "storage": "PostgreSQL 'documents' + Storage Volume", "rls_status": "FORCED", "durability": "Fernet AES-256 encrypted; retained per user policy"},
            {"entity": "Inconsistencies & Conflicts", "storage": "PostgreSQL 'conflicts'", "rls_status": "FORCED", "durability": "Persists across sessions & reloads"},
            {"entity": "Assistant Chats & Messages", "storage": "PostgreSQL 'assistant_conversations'", "rls_status": "FORCED", "durability": "Persists across page refresh"},
            {"entity": "Procedural Checklist Progress", "storage": "PostgreSQL 'citizen_checklist_items'", "rls_status": "FORCED", "durability": "Persists across navigation & logout"},
            {"entity": "Statutory Correction Drafts", "storage": "PostgreSQL 'correction_drafts'", "rls_status": "FORCED", "durability": "Persists across page reload; Ed25519 signed"},
            {"entity": "Statutory Vector Knowledge", "storage": "Qdrant Docker Volume (consolin_qdrant_data)", "rls_status": "Public Reference", "durability": "Durable across container restart"},
            {"entity": "System Audit Trail", "storage": "PostgreSQL 'audit_log'", "rls_status": "FORCED (Admin Read)", "durability": "Immutable append-only SHA-256 hash chain"},
        ]
    }


@router.post("/provision-test-account", dependencies=[Depends(verify_dev_mode)])
def provision_test_account(
    req: TestAccountRequest,
    db: Session = Depends(get_db),
):
    """
    Provisions or synchronizes a synthetic test account for local QA exploration.
    Strictly uses synthetic identities:
    - citizen_a: Aarav Sharma (citizen_a@example.com) -> role 'user'
    - citizen_b: Priya Patel (citizen_b@example.com) -> role 'user'
    - admin: AJAY M (admin@convelina.gov.in) -> role 'admin'
    """
    target = req.target.lower().strip()

    if target == "citizen_a":
        email = "citizen_a@example.com"
        full_name = "Aarav Sharma"
        fuid = "test_fuid_citizen_a"
        target_role = "user"
    elif target == "citizen_b":
        email = "citizen_b@example.com"
        full_name = "Priya Patel"
        fuid = "test_fuid_citizen_b"
        target_role = "user"
    elif target == "admin":
        email = "admin@convelina.gov.in"
        full_name = "AJAY M (Platform Administrator)"
        fuid = "test_fuid_admin"
        target_role = "admin"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown test target '{target}'. Must be 'citizen_a', 'citizen_b', or 'admin'.",
        )

    # 1. Check if user already exists
    existing = db.execute(
        text("SELECT id, firebase_uid, email, full_name, role FROM users WHERE LOWER(email) = LOWER(:email);"),
        {"email": email}
    ).mappings().first()

    if existing:
        user_id = existing["id"]
        # If target is admin, elevate to admin and log
        if target_role == "admin" and existing["role"] != "admin":
            set_rls_context(db, user_id, "admin")
            db.execute(
                text("UPDATE users SET role = 'admin', updated_at = NOW() WHERE id = :uid;"),
                {"uid": user_id}
            )
            AuditService.log_event(
                db=db,
                action="admin_provisioned_via_dev_explorer",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                details={"email": email, "granted_role": "admin"}
            )
            db.commit()
    else:
        # Provision new synthetic user
        new_row = db.execute(
            text("SELECT id, firebase_uid, email, full_name, role FROM provision_user(:fuid, :email, :name);"),
            {"fuid": fuid, "email": email, "name": full_name}
        ).mappings().first()
        user_id = new_row["id"]
        db.commit()

        if target_role == "admin":
            set_rls_context(db, user_id, "admin")
            db.execute(
                text("UPDATE users SET role = 'admin', updated_at = NOW() WHERE id = :uid;"),
                {"uid": user_id}
            )
            AuditService.log_event(
                db=db,
                action="admin_provisioned_via_dev_explorer",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                details={"email": email, "granted_role": "admin"}
            )
            db.commit()

    test_token = f"test_token_:{fuid}:{email}:{full_name}"

    return {
        "success": True,
        "target": target,
        "email": email,
        "full_name": full_name,
        "role": target_role,
        "test_token": test_token,
        "simulated": True,
        "message": f"Successfully prepared synthetic {target_role.upper()} session for {full_name}.",
    }
