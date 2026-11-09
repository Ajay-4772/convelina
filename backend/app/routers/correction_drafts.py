"""CONVELINA - Module 7 / Phase P3G Correction Drafts Router

Provides secure endpoints for citizens to create, view, update, delete, regenerate,
confirm, and download (PDF/DOCX) administrative application drafts.

Strictly enforces:
- Forced PostgreSQL RLS via transaction-scoped app user context.
- Citizen confirmation safety gate: NO UNCONFIRMED IDENTITY FIELD MAY BE TREATED
  AS A VERIFIED FACT IN A PERSONALIZED DRAFT.
- Compatibility matrix check connecting 10 draft types to 6 document categories.
- Strict verified-source grounding and honest procedural abstention.
- Immutable version confirmation and invalidation lifecycle with SHA-256 hash tracking.
- Append-only cryptographic audit logging for every lifecycle event.
- Citizen ownership and tenant isolation.
"""

import hashlib
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.conflict import Conflict
from app.models.correction_draft import CorrectionDraft, CorrectionDraftVersion, MANDATORY_DRAFT_DISCLAIMER
from app.schemas.correction_draft import (
    CorrectionDraftCreate,
    CorrectionDraftUpdate,
    CorrectionDraftConfirmRequest,
    CorrectionDraftRegenerateRequest,
    CorrectionDraftTranslateRequest,
    CorrectionDraftResponse,
    CorrectionDraftListResponse,
    CorrectionDraftVersionResponse,
    DraftStatusEnum,
)
from app.services.draft_safety_service import DraftSafetyService, mask_identifier
from app.services.draft_translation_service import DraftTranslationService
from app.services.document_generator import CorrectionDocumentGenerator, DocumentValidator
from app.services.document_exporter import DocumentExporter
from app.services.audit_service import AuditService
from app.rag.generation.llm_provider import GEMINI_UNAVAILABLE_MESSAGE

logger = logging.getLogger("convelina.routers.drafts")

router = APIRouter(prefix="/api/v1/correction-drafts", tags=["Correction Drafts"])
doc_generator = CorrectionDocumentGenerator()


@router.post("", response_model=CorrectionDraftResponse, status_code=status.HTTP_201_CREATED)
def create_correction_draft(
    req: CorrectionDraftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates and saves a new administrative correction draft under Forced RLS.
    Enforces the citizen confirmation safety gate and category compatibility matrix.
    """
    set_rls_context(db, current_user.id, current_user.role)

    # 1. Compatibility matrix gate
    DraftSafetyService.validate_draft_compatibility(
        draft_type=req.document_type,
        document_category=req.document_category,
    )

    # 2. Citizen confirmation safety gate: reject missing or unconfirmed fields
    conflict, doc_a, doc_b, confirmed_fields = DraftSafetyService.validate_citizen_confirmation(
        db=db,
        user_id=current_user.id,
        conflict_id=req.conflict_id,
        confirmed_fields_override=req.confirmed_fields,
    )

    conflicting_field = conflict.field_name or "name"
    conflict_classification = conflict.conflict_type or "discrepancy"
    ocr_extracted = {
        conflicting_field: conflict.value_b or conflict.value_a,
        "doc_a_value": conflict.value_a,
        "doc_b_value": conflict.value_b,
    }

    # 3. Generate draft with verified grounding & offline fallback
    success, content, source_refs, validation = doc_generator.generate_draft(
        document_type=req.document_type,
        document_category=req.document_category,
        conflicting_field=conflicting_field,
        confirmed_fields=confirmed_fields,
        ocr_extracted_values=ocr_extracted,
        conflict_classification=conflict_classification,
        user_explanation=req.user_explanation,
        requested_action=req.requested_action,
        allow_fallback=True,
        conflict=conflict,
        language=req.language or "en",
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=content or GEMINI_UNAVAILABLE_MESSAGE,
        )

    # Deterministic metadata derivation
    cat_upper = req.document_category.upper()
    field_title = conflicting_field.replace("_", " ").title()
    draft_title = f"{cat_upper} {field_title} Correction Representation"
    subject = f"Representation for Correction of {field_title} in {cat_upper} Records"

    # 4. Persist Draft under Forced RLS
    draft = CorrectionDraft(
        user_id=current_user.id,
        conflict_id=conflict.id,
        document_type=req.document_type,
        document_category=req.document_category,
        status=DraftStatusEnum.AI_GENERATED.value,
        title=draft_title,
        content=content,
        subject=subject,
        user_explanation=req.user_explanation,
        requested_action=req.requested_action,
        confirmed_fields=confirmed_fields,
        source_references=source_refs,
        disclaimer=MANDATORY_DRAFT_DISCLAIMER,
        is_citizen_confirmed=False,
        language=req.language or "en",
        version=1,
    )
    db.add(draft)
    db.flush()

    # 5. Save Immutable Version 1 Record
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    draft.sha256_hash = content_hash
    version_record = CorrectionDraftVersion(
        draft_id=draft.id,
        user_id=current_user.id,
        version_number=1,
        content=content,
        change_type="initial_generation",
        subject=subject,
        confirmed_fields=confirmed_fields,
        source_references=source_refs,
        is_citizen_confirmed=False,
        sha256_hash=content_hash,
    )
    db.add(version_record)

    # 6. Cryptographic Audit Event
    try:
        AuditService.log_event(
            db=db,
            action="correction_draft_created",
            entity_type="correction_draft",
            entity_id=draft.id,
            user_id=current_user.id,
            details={
                "draft_id": str(draft.id),
                "conflict_id": str(conflict.id),
                "document_type": req.document_type,
                "document_category": req.document_category,
                "version": 1,
                "sha256_hash": content_hash,
            },
        )
    except Exception as e:
        logger.warning("Failed to log audit event for draft creation: %s", str(e))

    db.commit()

    resp = CorrectionDraftResponse.model_validate(draft)
    resp.validation_status = validation
    return resp


@router.get("", response_model=CorrectionDraftListResponse)
def list_correction_drafts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves all correction drafts created by the authenticated citizen (strictly isolated via RLS)."""
    set_rls_context(db, current_user.id, current_user.role)

    query = db.query(CorrectionDraft).filter(CorrectionDraft.user_id == current_user.id)
    total = query.count()
    drafts = (
        query.order_by(desc(CorrectionDraft.updated_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = []
    for d in drafts:
        val = DocumentValidator.validate(d.content)
        item = CorrectionDraftResponse.model_validate(d)
        item.validation_status = val
        items.append(item)

    return CorrectionDraftListResponse(total=total, items=items)


@router.get("/{draft_id}", response_model=CorrectionDraftResponse)
def get_correction_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves a single correction draft by ID (strictly isolated to owner via RLS)."""
    set_rls_context(db, current_user.id, current_user.role)

    draft = (
        db.query(CorrectionDraft)
        .filter(CorrectionDraft.id == draft_id, CorrectionDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction draft not found.",
        )

    resp = CorrectionDraftResponse.model_validate(draft)
    resp.validation_status = DocumentValidator.validate(draft.content)
    return resp


@router.patch("/{draft_id}", response_model=CorrectionDraftResponse)
def update_correction_draft(
    draft_id: UUID,
    req: CorrectionDraftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates draft content or metadata.
    Any content modification creates a new immutable version and invalidates confirmation.
    """
    set_rls_context(db, current_user.id, current_user.role)

    draft = (
        db.query(CorrectionDraft)
        .filter(CorrectionDraft.id == draft_id, CorrectionDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction draft not found.",
        )

    content_changed = req.content is not None and req.content.strip() != draft.content.strip()
    fields_changed = req.confirmed_fields is not None and req.confirmed_fields != draft.confirmed_fields

    if req.title is not None:
        draft.title = req.title
    if req.recipient_authority is not None:
        draft.recipient_authority = req.recipient_authority
    if req.subject is not None:
        draft.subject = req.subject
    if req.user_explanation is not None:
        draft.user_explanation = req.user_explanation
    if req.requested_action is not None:
        draft.requested_action = req.requested_action
    if req.confirmed_fields is not None:
        draft.confirmed_fields = req.confirmed_fields

    if content_changed or fields_changed:
        change_reason = "manual_edit" if content_changed else "confirmed_fields_update"
        # Invalidate confirmation for the new modified version
        DraftSafetyService.invalidate_confirmation_on_change(db, draft, current_user.id, change_reason)

        if content_changed:
            draft.content = req.content.strip()
        draft.version += 1
        draft.status = DraftStatusEnum.CITIZEN_EDITED.value
        content_hash = hashlib.sha256(draft.content.encode("utf-8")).hexdigest()
        draft.sha256_hash = content_hash

        # Persist new immutable version record
        ver = CorrectionDraftVersion(
            draft_id=draft.id,
            user_id=current_user.id,
            version_number=draft.version,
            content=draft.content,
            change_type=change_reason,
            subject=draft.subject,
            confirmed_fields=draft.confirmed_fields or {},
            source_references=draft.source_references or [],
            is_citizen_confirmed=False,
            sha256_hash=content_hash,
        )
        db.add(ver)

        try:
            AuditService.log_event(
                db=db,
                action="correction_draft_updated",
                entity_type="correction_draft",
                entity_id=draft.id,
                user_id=current_user.id,
                details={
                    "draft_id": str(draft.id),
                    "version_number": draft.version,
                    "change_type": change_reason,
                    "sha256_hash": content_hash,
                },
            )
        except Exception as e:
            logger.warning("Audit logging failed for draft edit: %s", str(e))

    db.commit()
    set_rls_context(db, current_user.id, current_user.role)
    db.refresh(draft)

    resp = CorrectionDraftResponse.model_validate(draft)
    resp.validation_status = DocumentValidator.validate(draft.content)
    return resp


@router.post("/{draft_id}/regenerate", response_model=CorrectionDraftResponse)
def regenerate_correction_draft(
    draft_id: UUID,
    req: CorrectionDraftRegenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Re-runs generation with updated confirmed fields.
    Archives previous version and invalidates confirmation for the new version.
    """
    set_rls_context(db, current_user.id, current_user.role)

    draft = (
        db.query(CorrectionDraft)
        .filter(CorrectionDraft.id == draft_id, CorrectionDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction draft not found.",
        )

    # Validate citizen confirmation for linked conflict
    conflict = db.query(Conflict).filter(Conflict.id == draft.conflict_id, Conflict.user_id == current_user.id).first()
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced conflict record not found.",
        )

    merged_fields = dict(draft.confirmed_fields or {})
    if req.confirmed_fields:
        merged_fields.update(req.confirmed_fields)

    # Enforce safety gate on regenerated fields
    _, _, _, sanitized_confirmed = DraftSafetyService.validate_citizen_confirmation(
        db=db,
        user_id=current_user.id,
        conflict_id=conflict.id,
        confirmed_fields_override=merged_fields,
    )

    conflicting_field = conflict.field_name or "name"
    conflict_type = conflict.conflict_type or "discrepancy"

    success, content, source_refs, validation = doc_generator.generate_draft(
        document_type=draft.document_type,
        document_category=draft.document_category,
        conflicting_field=conflicting_field,
        confirmed_fields=sanitized_confirmed,
        ocr_extracted_values={conflicting_field: conflict.value_b or conflict.value_a},
        conflict_classification=conflict_type,
        user_explanation=req.user_explanation or draft.user_explanation,
        requested_action=req.requested_action or draft.requested_action,
        allow_fallback=True,
        conflict=conflict,
        language=draft.language or "en",
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=content or GEMINI_UNAVAILABLE_MESSAGE,
        )

    # Invalidate confirmation for the new regenerated version
    DraftSafetyService.invalidate_confirmation_on_change(db, draft, current_user.id, "regeneration")

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    draft.content = content
    draft.confirmed_fields = sanitized_confirmed
    draft.source_references = source_refs
    draft.version += 1
    draft.status = DraftStatusEnum.AI_GENERATED.value
    draft.sha256_hash = content_hash

    ver = CorrectionDraftVersion(
        draft_id=draft.id,
        user_id=current_user.id,
        version_number=draft.version,
        content=draft.content,
        change_type="regenerated",
        subject=draft.subject,
        confirmed_fields=sanitized_confirmed,
        source_references=source_refs,
        is_citizen_confirmed=False,
        sha256_hash=content_hash,
    )
    db.add(ver)

    try:
        AuditService.log_event(
            db=db,
            action="correction_draft_regenerated",
            entity_type="correction_draft",
            entity_id=draft.id,
            user_id=current_user.id,
            details={
                "draft_id": str(draft.id),
                "version_number": draft.version,
                "sha256_hash": content_hash,
            },
        )
    except Exception as e:
        logger.warning("Audit logging failed for draft regeneration: %s", str(e))

    db.commit()
    set_rls_context(db, current_user.id, current_user.role)
    db.refresh(draft)

    resp = CorrectionDraftResponse.model_validate(draft)
    resp.validation_status = validation
    return resp


@router.post("/{draft_id}/translate", response_model=CorrectionDraftResponse)
def translate_correction_draft(
    draft_id: UUID,
    req: CorrectionDraftTranslateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Translates an administrative representation into the requested target language.
    Preserves all structured citizen identity fields, dates, numbers, statutory citations, and URLs.
    MANDATORY INVARIANT: Creates a new immutable version and INVALIDATES any prior
    citizen confirmation, requiring the citizen to review and confirm the translated draft independently.
    """
    set_rls_context(db, current_user.id, current_user.role)

    draft = (
        db.query(CorrectionDraft)
        .filter(CorrectionDraft.id == draft_id, CorrectionDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction draft not found.",
        )

    try:
        translated_content, trans_title, trans_subj, meta = DraftTranslationService.translate_draft(
            title=draft.title,
            content=draft.content,
            subject=draft.subject,
            recipient_authority=draft.recipient_authority,
            confirmed_fields=draft.confirmed_fields or {},
            document_category=draft.document_category,
            target_language=req.target_language,
            bilingual=req.bilingual,
            source_language=draft.language or "en",
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "unsupported_language", "message": str(ve)},
        )

    # Invalidate confirmation for the new translated version
    DraftSafetyService.invalidate_confirmation_on_change(
        db=db,
        draft=draft,
        user_id=current_user.id,
        change_type=f"translation_{req.target_language}",
    )

    content_hash = hashlib.sha256(translated_content.encode("utf-8")).hexdigest()
    draft.content = translated_content
    draft.title = trans_title
    draft.subject = trans_subj
    draft.language = meta.get("target_language", req.target_language)
    draft.version += 1
    draft.status = DraftStatusEnum.CITIZEN_EDITED.value
    draft.sha256_hash = content_hash

    # Persist new immutable version record
    ver = CorrectionDraftVersion(
        draft_id=draft.id,
        user_id=current_user.id,
        version_number=draft.version,
        content=draft.content,
        change_type=f"translation_{req.target_language}",
        subject=draft.subject,
        confirmed_fields=draft.confirmed_fields or {},
        supporting_documents=draft.supporting_documents or [],
        source_references=draft.source_references or [],
        is_citizen_confirmed=False,
        citizen_confirmed_at=None,
        sha256_hash=content_hash,
    )
    db.add(ver)

    try:
        AuditService.log_event(
            db=db,
            action="correction_draft_translated",
            entity_type="correction_draft",
            entity_id=draft.id,
            user_id=current_user.id,
            details={
                "draft_id": str(draft.id),
                "version_number": draft.version,
                "source_language": meta.get("source_language", "en"),
                "target_language": draft.language,
                "sha256_hash": content_hash,
                "provider_status": meta.get("provider_status"),
                "is_bilingual": req.bilingual,
            },
        )
    except Exception as e:
        logger.warning("Audit logging failed for draft translation: %s", str(e))

    db.commit()
    set_rls_context(db, current_user.id, current_user.role)
    db.refresh(draft)

    resp = CorrectionDraftResponse.model_validate(draft)
    resp.validation_status = DocumentValidator.validate(draft.content)
    return resp


@router.post("/{draft_id}/confirm", response_model=CorrectionDraftResponse)
def confirm_correction_draft(
    draft_id: UUID,
    req: CorrectionDraftConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Citizen explicitly reviews and confirms an administrative draft version.
    Binds confirmation to exact version number, content SHA-256 hash, and timestamp.
    """
    set_rls_context(db, current_user.id, current_user.role)

    draft = (
        db.query(CorrectionDraft)
        .filter(CorrectionDraft.id == draft_id, CorrectionDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction draft not found.",
        )

    confirmed_draft = DraftSafetyService.confirm_draft_version(
        db=db,
        draft=draft,
        user_id=current_user.id,
        confirmation_statement=req.confirmation_statement,
        version_number=req.version_number,
        expected_sha256_hash=req.expected_sha256_hash,
    )

    resp = CorrectionDraftResponse.model_validate(confirmed_draft)
    resp.validation_status = DocumentValidator.validate(confirmed_draft.content)
    return resp


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_correction_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes a draft and its version history. Records an audit event."""
    set_rls_context(db, current_user.id, current_user.role)

    draft = (
        db.query(CorrectionDraft)
        .filter(CorrectionDraft.id == draft_id, CorrectionDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction draft not found.",
        )

    try:
        AuditService.log_event(
            db=db,
            action="correction_draft_deleted",
            entity_type="correction_draft",
            entity_id=draft.id,
            user_id=current_user.id,
            details={
                "draft_id": str(draft.id),
                "document_type": draft.document_type,
                "document_category": draft.document_category,
                "final_version": draft.version,
            },
        )
    except Exception as e:
        logger.warning("Audit logging failed for draft deletion: %s", str(e))

    db.query(CorrectionDraftVersion).filter(CorrectionDraftVersion.draft_id == draft.id).delete()
    db.delete(draft)
    db.commit()
    return None


@router.get("/{draft_id}/download")
def download_correction_draft(
    draft_id: UUID,
    format: str = Query("pdf", pattern="^(pdf|docx)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Downloads the draft as a professionally styled PDF or DOCX file."""
    set_rls_context(db, current_user.id, current_user.role)

    draft = (
        db.query(CorrectionDraft)
        .filter(CorrectionDraft.id == draft_id, CorrectionDraft.user_id == current_user.id)
        .first()
    )
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Correction draft not found.",
        )

    raw_ascii = "".join(c if (c.isascii() and c.isalnum()) or c in ("-", "_") else "_" for c in (draft.title or "draft"))
    safe_title = raw_ascii[:40].strip("_")
    if not safe_title:
        safe_title = f"draft_{str(draft.id)[:8]}"

    # Audit log download request
    try:
        AuditService.log_event(
            db=db,
            action="correction_draft_downloaded",
            entity_type="correction_draft",
            entity_id=draft.id,
            user_id=current_user.id,
            details={
                "draft_id": str(draft.id),
                "format": format,
                "version": draft.version,
                "is_citizen_confirmed": draft.is_citizen_confirmed,
            },
        )
    except Exception as e:
        logger.warning("Audit logging failed for draft download: %s", str(e))

    if format == "pdf":
        file_bytes = DocumentExporter.export_pdf(
            title=draft.title,
            content=draft.content,
            draft_id=str(draft.id),
            language=draft.language or "en",
        )
        media_type = "application/pdf"
        filename = f"{safe_title}.pdf"
    else:
        file_bytes = DocumentExporter.export_docx(
            title=draft.title,
            content=draft.content,
            draft_id=str(draft.id),
            language=draft.language or "en",
        )
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{safe_title}.docx"

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
