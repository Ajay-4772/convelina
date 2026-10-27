"""CONVELINA - Module 7 Correction Drafts Router

Provides secure endpoints for citizens to create, view, update, delete, regenerate,
and download (PDF/DOCX) correction application drafts.

Strictly enforces:
- Forced PostgreSQL RLS via transaction-scoped app user context.
- Gemini-only generation via CorrectionDocumentGenerator.
- Draft version history in correction_draft_versions.
- Citizen ownership and isolation.
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.conflict import Conflict
from app.models.correction_draft import CorrectionDraft, CorrectionDraftVersion
from app.schemas.correction_draft import (
    CorrectionDraftCreate,
    CorrectionDraftUpdate,
    CorrectionDraftResponse,
    CorrectionDraftListResponse,
    CorrectionDraftVersionResponse,
    CorrectionDraftRegenerateRequest,
)
from app.services.document_generator import CorrectionDocumentGenerator, DocumentValidator
from app.services.document_exporter import DocumentExporter
from app.rag.generation.llm_provider import GEMINI_UNAVAILABLE_MESSAGE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/correction-drafts", tags=["Correction Drafts"])
doc_generator = CorrectionDocumentGenerator()


@router.post("", response_model=CorrectionDraftResponse, status_code=status.HTTP_201_CREATED)
def create_correction_draft(
    req: CorrectionDraftCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates and saves a new correction draft for a selected conflict under RLS."""
    set_rls_context(db, current_user.id, current_user.role)

    # 1. Fetch Conflict to verify existence and extract context
    conflict = db.query(Conflict).filter(Conflict.id == req.conflict_id).first()
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced conflict not found or access denied.",
        )

    # Context values from conflict
    conflicting_field = conflict.field_name or "name"
    conflict_classification = conflict.conflict_type or "discrepancy"
    ocr_extracted = {
        conflicting_field: conflict.value_b or conflict.value_a,
        "doc_a_value": conflict.value_a,
        "doc_b_value": conflict.value_b,
    }

    # 2. Invoke Gemini generator
    success, content, source_refs, validation = doc_generator.generate_draft(
        document_type=req.document_type,
        document_category=req.document_category,
        conflicting_field=conflicting_field,
        confirmed_fields=req.confirmed_fields,
        ocr_extracted_values=ocr_extracted,
        conflict_classification=conflict_classification,
    )

    if not success or content == GEMINI_UNAVAILABLE_MESSAGE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=GEMINI_UNAVAILABLE_MESSAGE,
        )

    draft_title = (
        f"{req.document_category.upper()} {conflicting_field.replace('_', ' ').title()} Correction Application"
    )

    # 3. Persist Draft under forced RLS
    draft = CorrectionDraft(
        user_id=current_user.id,
        conflict_id=conflict.id,
        document_type=req.document_type,
        document_category=req.document_category,
        status="generated",
        title=draft_title,
        content=content,
        confirmed_fields=req.confirmed_fields,
        source_references=source_refs,
        version=1,
    )
    db.add(draft)
    db.flush()

    # 4. Save Version 1 record
    version_record = CorrectionDraftVersion(
        draft_id=draft.id,
        user_id=current_user.id,
        version_number=1,
        content=content,
        change_type="initial_generation",
    )
    db.add(version_record)
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
    """Retrieves all correction drafts created by the authenticated citizen (isolated via RLS)."""
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
    """Retrieves a single correction draft by ID (strictly isolated to owner)."""
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
    """Updates a draft's content, title, or status and creates a new version record."""
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

    content_changed = req.content is not None and req.content != draft.content

    if req.title is not None:
        draft.title = req.title
    if req.status is not None:
        draft.status = req.status
    if req.confirmed_fields is not None:
        draft.confirmed_fields = req.confirmed_fields
    if content_changed:
        draft.content = req.content
        draft.version += 1
        if draft.status == "generated":
            draft.status = "user_edited"

        # Log new version
        ver = CorrectionDraftVersion(
            draft_id=draft.id,
            user_id=current_user.id,
            version_number=draft.version,
            content=draft.content,
            change_type="manual_edit",
        )
        db.add(ver)

    db.commit()

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
    """Re-runs Gemini generation with updated confirmed fields and archives previous version."""
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

    conflict = db.query(Conflict).filter(Conflict.id == draft.conflict_id).first()
    conflicting_field = conflict.field_name if conflict else "name"
    conflict_type = conflict.conflict_type if conflict else "discrepancy"

    merged_fields = dict(draft.confirmed_fields or {})
    if req.confirmed_fields:
        merged_fields.update(req.confirmed_fields)

    ocr_extracted = {
        conflicting_field: conflict.value_b if conflict else "",
    }

    success, content, source_refs, validation = doc_generator.generate_draft(
        document_type=draft.document_type,
        document_category=draft.document_category,
        conflicting_field=conflicting_field,
        confirmed_fields=merged_fields,
        ocr_extracted_values=ocr_extracted,
        conflict_classification=conflict_type,
    )

    if not success or content == GEMINI_UNAVAILABLE_MESSAGE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=GEMINI_UNAVAILABLE_MESSAGE,
        )

    draft.content = content
    draft.confirmed_fields = merged_fields
    draft.source_references = source_refs
    draft.version += 1
    draft.status = "generated"

    ver = CorrectionDraftVersion(
        draft_id=draft.id,
        user_id=current_user.id,
        version_number=draft.version,
        content=draft.content,
        change_type="regenerated",
    )
    db.add(ver)

    db.commit()

    resp = CorrectionDraftResponse.model_validate(draft)
    resp.validation_status = validation
    return resp


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_correction_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes a draft and its version history without affecting original conflict."""
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

    safe_title = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in draft.title)[:40]

    if format == "pdf":
        file_bytes = DocumentExporter.export_pdf(
            title=draft.title,
            content=draft.content,
            draft_id=str(draft.id),
        )
        media_type = "application/pdf"
        filename = f"{safe_title}.pdf"
    else:
        file_bytes = DocumentExporter.export_docx(
            title=draft.title,
            content=draft.content,
            draft_id=str(draft.id),
        )
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"{safe_title}.docx"

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
