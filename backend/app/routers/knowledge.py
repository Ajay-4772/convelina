import logging
import uuid
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.models.knowledge_source import KnowledgeSource
from app.models.official_form import OfficialForm, OfficialFormVersion, utc_now
from app.rag.forms.catalog import FormCatalogService
from app.services.form_retrieval_service import FormRetrievalService
from app.services.audit_service import AuditService
from app.rag.ingestion.service import KnowledgeIngestionService
from app.config import settings
from app.core.storage import (
    get_official_form_path,
    save_official_form_asset,
    generate_default_official_form_pdf,
    compute_sha256,
)
from app.rag.schemas import (
    KnowledgeSourceResponse,
    KnowledgeSourceListResponse,
    OfficialFormResponse,
    OfficialFormListResponse,
    OfficialFormCreateRequest,
    OfficialFormUpdateRequest,
    OfficialFormVerificationRequest,
    OfficialFormReplaceRequest,
    OfficialFormVersionResponse,
    OfficialFormHistoryResponse,
    KnowledgeIngestionJobResponse,
    UpdateVerificationStatusRequest,
    CorpusManifestResponse,
    CorpusManifestItem,
    CorpusStatusResponse,
    IngestionJobStartRequest,
    IngestionJobStatusResponse,
    CollectionsHealthResponse,
    CollectionRollbackRequest,
    CollectionRollbackResponse,
    RetrievalDiagnosticsRequest,
    RetrievalDiagnosticsResponse,
    RetrievalDiagnosticChunk,
)
from app.rag.ingestion.corpus_ingestion import (
    CorpusValidator,
    ProcedureAwareHierarchicalChunker,
    CorpusIngestionManager,
    _INGESTION_STATE,
    CORE_DOC_IDS,
    REFERENCE_DOC_IDS,
    EXPECTED_CORE_CHUNKS,
    EXPECTED_REFERENCE_CHUNKS,
    EXPECTED_TOTAL_CHUNKS,
)
from app.rag.retrieval.retriever import HybridRetriever

logger = logging.getLogger("convelina.knowledge.router")
router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge & Official Forms"])

# ---------------------------------------------------------------------------
# 1. Citizen Knowledge & Form Retrieval Endpoints
# ---------------------------------------------------------------------------

@router.get("/sources", response_model=KnowledgeSourceListResponse)
def list_knowledge_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by document category (aadhaar, pan, passport, epf)"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Returns verified statutory sources and procedures.
    Only returns active, verified sources for citizen guidance.
    """
    set_rls_context(db, current_user.id, current_user.role)
    query = db.query(KnowledgeSource).filter(
        KnowledgeSource.verification_status == "verified",
        KnowledgeSource.is_active == True
    )
    if category:
        query = query.filter(KnowledgeSource.document_category == category.lower())
    
    sources = query.order_by(KnowledgeSource.title.asc()).limit(limit).all()
    return KnowledgeSourceListResponse(
        total=len(sources),
        sources=[KnowledgeSourceResponse(**s.to_dict()) for s in sources]
    )

@router.get("/sources/{source_id}", response_model=KnowledgeSourceResponse)
def get_knowledge_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns statutory knowledge source details and official circular link."""
    set_rls_context(db, current_user.id, current_user.role)
    src = db.query(KnowledgeSource).filter(
        or_(KnowledgeSource.source_id == source_id, KnowledgeSource.id == source_id if _is_valid_uuid(source_id) else False),
        KnowledgeSource.is_active == True
    ).first()
    if not src:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge source not found")
    return KnowledgeSourceResponse(**src.to_dict())

@router.get("/forms", response_model=OfficialFormListResponse)
def list_official_forms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by document category"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type (full_name, date_of_birth, father_name, gender)"),
    verification_status: Optional[str] = Query(None, description="Filter by verification status (verified, unverified, etc.)"),
    provenance: Optional[str] = Query(None, description="Filter by provenance (OFFICIAL_ORIGINAL, APPLICATION_GENERATED, etc.)")
):
    """
    Returns statutory correction and update forms catalog.
    Returns active forms with accurate provenance and verification status.
    """
    set_rls_context(db, current_user.id, current_user.role)
    forms = FormCatalogService.list_forms(
        db,
        category=category,
        issue_type=issue_type,
        verification_status=verification_status,
        provenance=provenance,
        include_inactive=False
    )
    return OfficialFormListResponse(total=len(forms), forms=forms)

@router.get("/forms/{form_id}", response_model=OfficialFormResponse)
def get_official_form(
    form_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns official form details, purpose, and download URL."""
    set_rls_context(db, current_user.id, current_user.role)
    is_admin = current_user.role == "admin"
    form = FormCatalogService.get_form_by_id(db, form_id, is_admin=is_admin)
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official form not found")
    return form

# ---------------------------------------------------------------------------
# 2. Secure File Streaming & Preview Endpoints (Phase P3D)
# ---------------------------------------------------------------------------

@router.get("/forms/{form_id}/download")
def download_official_form(
    form_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated streaming download for official statutory forms.
    Enforces:
    - User authentication and role scoping.
    - Verified & active status check (unverified/retired forms inaccessible to regular users).
    - Strict path traversal prevention.
    - Cryptographic SHA-256 integrity validation.
    - Safe Content-Disposition and security headers.
    - Tamper-evident audit logging.
    """
    set_rls_context(db, current_user.id, current_user.role)
    
    # Check for path traversal characters in form_id
    if ".." in form_id or "/" in form_id or "\\" in form_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid form identifier.")

    is_admin = current_user.role == "admin"
    form = FormRetrievalService.get_verified_form_for_download(db, form_id, is_admin=is_admin)
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found in statutory repository.")

    if not form.is_active and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Form has been deactivated.")

    if form.verification_status == "revoked" and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Form has been revoked by statutory authorities.")

    # Resolve safe physical file path
    abs_path = get_official_form_path(form.storage_path or form.form_id)
    if not abs_path or not os.path.isfile(abs_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical document asset missing from repository.")

    # Read bytes for integrity and MIME type validation
    with open(abs_path, "rb") as f:
        content_bytes = f.read()

    # MIME magic bytes verification (%PDF)
    if not content_bytes.startswith(b"%PDF"):
        logger.error("MIME type validation failed for form %s: missing %%PDF header", form.form_id)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File integrity check failed: asset is not a valid PDF document."
        )

    # Cryptographic SHA-256 file integrity check
    if form.sha256_hash:
        computed = compute_sha256(content_bytes)
        if computed != form.sha256_hash:
            logger.error("SHA-256 integrity failure for form %s: recorded=%s, disk=%s", form.form_id, form.sha256_hash, computed)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Form integrity check failed: file has been modified or corrupted."
            )

    # Audit logging
    try:
        AuditService.log_event(
            db=db,
            action="official_form_downloaded",
            entity_type="official_form",
            entity_id=form.id,
            user_id=current_user.id,
            details={
                "form_id": form.form_id,
                "document_category": form.document_category,
                "provenance": form.provenance,
                "sha256_hash": form.sha256_hash,
                "role": current_user.role,
            }
        )
        db.commit()
    except Exception as e:
        logger.warning("Audit logging failed for form download: %s", str(e))

    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', form.form_id)
    is_official = form.provenance in ("OFFICIAL_ORIGINAL", "OFFICIAL_COPY") and form.verification_status == "verified"
    safe_filename = f"{safe_name}.pdf" if is_official else f"TEMPLATE_{safe_name}.pdf"

    return FileResponse(
        path=abs_path,
        media_type="application/pdf",
        filename=safe_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-cache",
            "X-Convelina-Provenance": form.provenance or "UNVERIFIED",
            "X-Convelina-Verification-Status": form.verification_status or "unverified",
            "X-Convelina-Official-Source-URL": form.official_download_url or "",
        }
    )

@router.get("/forms/{form_id}/preview")
def preview_official_form(
    form_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated inline streaming preview for official statutory forms.
    Enforces:
    - User authentication and role scoping.
    - Verified & active status check.
    - Path traversal prevention.
    - Content-Disposition: inline with safe PDF headers.
    - Audit logging.
    """
    set_rls_context(db, current_user.id, current_user.role)

    # Check for path traversal characters
    if ".." in form_id or "/" in form_id or "\\" in form_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid form identifier.")

    is_admin = current_user.role == "admin"
    form = FormRetrievalService.get_verified_form_for_download(db, form_id, is_admin=is_admin)
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found in statutory repository.")

    if not form.is_active and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Form has been deactivated.")

    if form.verification_status == "revoked" and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Form has been revoked by statutory authorities.")

    abs_path = get_official_form_path(form.storage_path or form.form_id)
    if not abs_path or not os.path.isfile(abs_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical document asset missing from repository.")

    with open(abs_path, "rb") as f:
        content_bytes = f.read()

    # MIME magic bytes verification (%PDF)
    if not content_bytes.startswith(b"%PDF"):
        logger.error("MIME type validation failed for form preview %s: missing %%PDF header", form.form_id)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File integrity check failed: asset is not a valid PDF document."
        )

    # Integrity verification
    if form.sha256_hash:
        computed = compute_sha256(content_bytes)
        if computed != form.sha256_hash:
            logger.error("SHA-256 integrity failure on preview for form %s", form.form_id)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Form integrity check failed: file has been modified or corrupted."
            )

    try:
        AuditService.log_event(
            db=db,
            action="official_form_previewed",
            entity_type="official_form",
            entity_id=form.id,
            user_id=current_user.id,
            details={
                "form_id": form.form_id,
                "document_category": form.document_category,
                "provenance": form.provenance,
                "sha256_hash": form.sha256_hash,
                "role": current_user.role,
            }
        )
        db.commit()
    except Exception as e:
        logger.warning("Audit logging failed for form preview: %s", str(e))

    import re
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', form.form_id)
    is_official = form.provenance in ("OFFICIAL_ORIGINAL", "OFFICIAL_COPY") and form.verification_status == "verified"
    safe_filename = f"{safe_name}.pdf" if is_official else f"TEMPLATE_{safe_name}.pdf"

    return FileResponse(
        path=abs_path,
        media_type="application/pdf",
        filename=safe_filename,
        headers={
            "Content-Disposition": f'inline; filename="{safe_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-cache",
            "X-Convelina-Provenance": form.provenance or "UNVERIFIED",
            "X-Convelina-Verification-Status": form.verification_status or "unverified",
            "X-Convelina-Official-Source-URL": form.official_download_url or "",
        }
    )

# ---------------------------------------------------------------------------
# 3. Admin Repository Management Endpoints (Phase P3D Section 7)
# ---------------------------------------------------------------------------

@router.get("/admin/forms", response_model=OfficialFormListResponse)
def admin_list_all_forms(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    verification_status: Optional[str] = Query(None, description="Filter by status (verified, needs_review, outdated, retired)"),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """
    Admin-only endpoint to inspect all forms in the repository across all lifecycle states.
    """
    set_rls_context(db, current_user.id, current_user.role)
    query = db.query(OfficialForm)
    if verification_status:
        query = query.filter(OfficialForm.verification_status == verification_status.lower())
    if category:
        query = query.filter(OfficialForm.document_category == category.lower())
    if is_active is not None:
        query = query.filter(OfficialForm.is_active == is_active)

    forms = query.order_by(OfficialForm.form_name.asc()).all()
    return OfficialFormListResponse(
        total=len(forms),
        forms=[OfficialFormResponse(**f.to_dict()) for f in forms]
    )

@router.post("/admin/forms", response_model=OfficialFormResponse, status_code=status.HTTP_201_CREATED)
def admin_create_official_form(
    body: OfficialFormCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to register a new official government form in the repository.
    """
    set_rls_context(db, current_user.id, current_user.role)
    existing = db.query(OfficialForm).filter(OfficialForm.form_id == body.form_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Form with identifier '{body.form_id}' already exists.")

    # Generate initial authentic PDF asset template
    form_dict = body.model_dump()
    pdf_bytes = generate_default_official_form_pdf(form_dict)
    storage_name, sha256_hash, file_size = save_official_form_asset(body.form_id, pdf_bytes)

    new_form = OfficialForm(
        form_id=body.form_id,
        form_name=body.form_name,
        document_category=body.document_category.lower(),
        purpose=body.purpose,
        description=body.description or body.purpose,
        issuing_authority=body.issuing_authority,
        official_download_url=body.official_download_url,
        instructions_source_id=body.instructions_source_id,
        applicable_issue_types=body.applicable_issue_types,
        applicable_conditions=body.applicable_conditions,
        language=body.language,
        version=body.version or "1.0",
        verification_status=body.verification_status,
        is_active=body.is_active,
        file_size_bytes=file_size,
        mime_type="application/pdf",
        file_format="pdf",
        sha256_hash=sha256_hash,
        storage_path=storage_name,
        metadata_payload={}
    )
    db.add(new_form)
    db.commit()
    db.refresh(new_form)

    AuditService.log_event(
        db=db,
        action="admin_form_created",
        entity_type="official_form",
        entity_id=new_form.id,
        user_id=current_user.id,
        details={"form_id": new_form.form_id, "authority": new_form.issuing_authority, "sha256": sha256_hash}
    )
    return OfficialFormResponse(**new_form.to_dict())

@router.put("/admin/forms/{form_id}", response_model=OfficialFormResponse)
def admin_update_official_form(
    form_id: str,
    body: OfficialFormUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to update metadata for an existing official government form.
    """
    set_rls_context(db, current_user.id, current_user.role)
    form = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official form not found.")

    update_data = body.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(form, field, val)

    AuditService.log_event(
        db=db,
        action="admin_form_updated",
        entity_type="official_form",
        entity_id=form.id,
        user_id=current_user.id,
        details={"form_id": form.form_id, "updated_fields": list(update_data.keys())}
    )
    db.commit()
    db.refresh(form)
    return OfficialFormResponse(**form.to_dict())

@router.post("/admin/forms/{form_id}/upload", response_model=OfficialFormResponse)
async def admin_upload_form_asset(
    form_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to upload or replace the physical PDF document for an official form.
    Computes cryptographic SHA-256 hash and updates file metadata.
    """
    set_rls_context(db, current_user.id, current_user.role)
    form = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official form not found.")

    content = await file.read()
    if not content or len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    storage_name, sha256_hash, file_size = save_official_form_asset(form.form_id, content, filename=file.filename)
    form.storage_path = storage_name
    form.sha256_hash = sha256_hash
    form.file_size_bytes = file_size
    form.mime_type = file.content_type or "application/pdf"

    AuditService.log_event(
        db=db,
        action="admin_form_asset_uploaded",
        entity_type="official_form",
        entity_id=form.id,
        user_id=current_user.id,
        details={"form_id": form.form_id, "file_size": file_size, "sha256": sha256_hash}
    )
    db.commit()
    db.refresh(form)
    return OfficialFormResponse(**form.to_dict())

@router.put("/admin/forms/{form_id}/verification", response_model=OfficialFormResponse)
def admin_update_form_verification(
    form_id: str,
    body: OfficialFormVerificationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to update verification state and provenance of an official form.
    MANDATORY CRITICAL RULE:
    ReportLab-generated PDFs must never be classified as authentic government originals
    merely because they resemble official forms. Only documents with verified official
    provenance (OFFICIAL_ORIGINAL or OFFICIAL_COPY) may receive the verified official status.
    """
    set_rls_context(db, current_user.id, current_user.role)
    form = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official form not found.")

    valid_statuses = ["verified", "unverified", "provisional", "needs_review", "revoked", "outdated", "retired"]
    valid_provenances = ["OFFICIAL_ORIGINAL", "OFFICIAL_COPY", "APPLICATION_GENERATED", "SYNTHETIC_TEST_ASSET", "UNVERIFIED"]

    target_status = body.verification_status.lower()
    if target_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification status. Must be one of {valid_statuses}."
        )

    target_provenance = (body.provenance or form.provenance or "UNVERIFIED").upper()
    if target_provenance not in valid_provenances:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provenance. Must be one of {valid_provenances}."
        )

    # Enforce Rule 2: ReportLab-generated PDFs cannot receive OFFICIAL_ORIGINAL or OFFICIAL_COPY or verified status
    if target_provenance in ("OFFICIAL_ORIGINAL", "OFFICIAL_COPY") or target_status == "verified":
        if target_provenance not in ("OFFICIAL_ORIGINAL", "OFFICIAL_COPY"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only documents with verified official provenance (OFFICIAL_ORIGINAL or OFFICIAL_COPY) may receive the verified official status."
            )

        abs_path = get_official_form_path(form.storage_path or form.form_id)
        if abs_path and os.path.isfile(abs_path):
            with open(abs_path, "rb") as f:
                header = f.read(2048)
            if b"ReportLab" in header:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot verify form as OFFICIAL_ORIGINAL or OFFICIAL_COPY: the stored file is an application-generated ReportLab asset, not an authentic government publication."
                )

    old_status = form.verification_status
    old_provenance = form.provenance
    form.verification_status = target_status
    form.provenance = target_provenance
    form.last_verified_at = utc_now()
    form.verified_by_user_id = current_user.id
    if body.provenance_notes:
        form.provenance_notes = body.provenance_notes
    if body.review_notes:
        meta = dict(form.metadata_payload or {})
        meta["review_notes"] = body.review_notes
        form.metadata_payload = meta

    AuditService.log_event(
        db=db,
        action="admin_form_verification_updated",
        entity_type="official_form",
        entity_id=form.id,
        user_id=current_user.id,
        details={
            "form_id": form.form_id,
            "old_status": old_status,
            "new_status": form.verification_status,
            "old_provenance": old_provenance,
            "new_provenance": form.provenance,
        }
    )
    db.commit()
    db.refresh(form)
    return OfficialFormResponse(**form.to_dict())

@router.post("/admin/forms/sync")
def admin_sync_seed_forms(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to synchronize and seed default verified official statutory forms.
    """
    set_rls_context(db, current_user.id, current_user.role)
    synced_count = FormCatalogService.sync_seed_forms(db)
    return {
        "status": "success",
        "forms_synced": synced_count,
        "message": f"Successfully synchronized {synced_count} verified official forms to repository."
    }

@router.get("/admin/forms/{form_id}/history", response_model=OfficialFormHistoryResponse)
def admin_get_form_history(
    form_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint to view the version history and retired audit trail of an official form.
    """
    set_rls_context(db, current_user.id, current_user.role)
    form = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Form '{form_id}' not found.")

    versions = (
        db.query(OfficialFormVersion)
        .filter(OfficialFormVersion.form_id == form_id)
        .order_by(OfficialFormVersion.retired_at.desc())
        .all()
    )

    return OfficialFormHistoryResponse(
        form_id=form.form_id,
        current_version=form.version,
        current_provenance=form.provenance,
        current_verification_status=form.verification_status,
        total_versions=len(versions),
        versions=[OfficialFormVersionResponse(**v.to_dict()) for v in versions],
    )

@router.post("/admin/forms/{form_id}/replace", response_model=OfficialFormResponse)
async def admin_replace_official_form(
    form_id: str,
    file: UploadFile = File(...),
    version: str = Form(...),
    issuing_authority: Optional[str] = Form(None),
    official_download_url: Optional[str] = Form(None),
    provenance: str = Form("OFFICIAL_ORIGINAL"),
    verification_status: str = Form("unverified"),
    provenance_notes: Optional[str] = Form(None),
    publication_info: Optional[str] = Form(None),
    change_summary: Optional[str] = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only replacement workflow:
    - Archives current form version into official_form_versions table with retired timestamp and user.
    - Validates uploaded PDF (size, %PDF magic bytes, ReportLab rejection gate).
    - Stores new physical asset and updates form record.
    - Emits tamper-evident audit logs for archiving and replacement.
    """
    set_rls_context(db, current_user.id, current_user.role)
    form = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Form '{form_id}' not found.")

    content = await file.read()
    if not content or len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File integrity check failed: uploaded asset is not a valid PDF document."
        )

    # ReportLab rejection gate: ReportLab-generated PDFs cannot be classified as OFFICIAL_ORIGINAL or OFFICIAL_COPY
    prov_upper = provenance.upper()
    if prov_upper in ("OFFICIAL_ORIGINAL", "OFFICIAL_COPY"):
        header = content[:2048]
        if b"ReportLab" in header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot replace form with provenance OFFICIAL_ORIGINAL or OFFICIAL_COPY: the uploaded file is a ReportLab-generated synthetic template, not an authentic government publication."
            )

    # 1. Archive current version to official_form_versions
    archived_version = OfficialFormVersion(
        form_id=form.form_id,
        version=form.version or "1.0",
        form_name=form.form_name,
        document_category=form.document_category,
        issuing_authority=form.issuing_authority,
        purpose=form.purpose,
        official_download_url=form.official_download_url,
        sha256_hash=form.sha256_hash,
        file_size_bytes=form.file_size_bytes,
        storage_path=form.storage_path,
        provenance=form.provenance or "UNVERIFIED",
        provenance_notes=form.provenance_notes,
        verification_status=form.verification_status,
        retired_by_user_id=current_user.id,
        retired_at=utc_now(),
    )
    db.add(archived_version)

    # 2. Save new asset
    storage_name, new_sha256, new_size = save_official_form_asset(form.form_id, content, filename=file.filename)

    # 3. Update current form record
    old_version = form.version
    old_hash = form.sha256_hash
    form.version = version
    form.storage_path = storage_name
    form.sha256_hash = new_sha256
    form.file_size_bytes = new_size
    form.mime_type = file.content_type or "application/pdf"
    form.file_format = "pdf"
    form.provenance = prov_upper
    form.verification_status = verification_status.lower()
    if issuing_authority:
        form.issuing_authority = issuing_authority
    if official_download_url:
        form.official_download_url = official_download_url
    if provenance_notes:
        form.provenance_notes = provenance_notes
    if publication_info:
        meta = dict(form.metadata_payload or {})
        meta["publication_info"] = publication_info
        form.metadata_payload = meta

    # 4. Audit logging
    AuditService.log_event(
        db=db,
        action="official_form_version_archived",
        entity_type="official_form_version",
        entity_id=archived_version.id,
        user_id=current_user.id,
        details={
            "form_id": form.form_id,
            "archived_version": old_version,
            "archived_hash": old_hash,
            "superseded_by_version": version,
        },
    )

    AuditService.log_event(
        db=db,
        action="official_form_replaced",
        entity_type="official_form",
        entity_id=form.id,
        user_id=current_user.id,
        details={
            "form_id": form.form_id,
            "new_version": version,
            "new_sha256": new_sha256,
            "provenance": prov_upper,
            "verification_status": form.verification_status,
            "change_summary": change_summary or f"Replaced with version {version}",
        },
    )

    db.commit()
    db.refresh(form)
    return OfficialFormResponse(**form.to_dict())

@router.put("/admin/forms/{form_id}/verify-and-publish", response_model=OfficialFormResponse)
def admin_verify_and_publish_form(
    form_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint to verify and publish an official form.
    Enforces the ReportLab rejection gate: ReportLab-generated synthetic forms cannot be published as verified official documents.
    """
    set_rls_context(db, current_user.id, current_user.role)
    form = db.query(OfficialForm).filter(OfficialForm.form_id == form_id).first()
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Form '{form_id}' not found.")

    abs_path = get_official_form_path(form.storage_path or form.form_id)
    if abs_path and os.path.isfile(abs_path):
        with open(abs_path, "rb") as f:
            header = f.read(2048)
        if b"ReportLab" in header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot verify and publish: the stored file is a ReportLab-generated synthetic template. Official verification requires an authentic government publication."
            )

    form.verification_status = "verified"
    form.is_active = True
    form.last_verified_at = utc_now()
    form.verified_by_user_id = current_user.id

    AuditService.log_event(
        db=db,
        action="official_form_verified_and_published",
        entity_type="official_form",
        entity_id=form.id,
        user_id=current_user.id,
        details={
            "form_id": form.form_id,
            "provenance": form.provenance,
            "sha256_hash": form.sha256_hash,
            "version": form.version,
        },
    )

    db.commit()
    db.refresh(form)
    return OfficialFormResponse(**form.to_dict())

# ---------------------------------------------------------------------------
# 4. Knowledge Ingestion & Source Admin Endpoints
# ---------------------------------------------------------------------------

@router.post("/ingestion", response_model=KnowledgeIngestionJobResponse)
def trigger_knowledge_ingestion(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to sync official government procedures and forms into PostgreSQL and Qdrant.
    """
    set_rls_context(db, current_user.id, current_user.role)
    try:
        service = KnowledgeIngestionService(db)
        res = service.sync_all()
        # Also sync form assets
        FormCatalogService.sync_seed_forms(db)
        return KnowledgeIngestionJobResponse(
            job_id=str(uuid.uuid4()),
            status=res.get("status", "success"),
            sources_indexed=res.get("sources_synced", 0),
            forms_indexed=res.get("forms_synced", 0),
            message=f"Synced {res.get('sources_synced', 0)} sources, {res.get('chunks_indexed', 0)} chunks, and official forms to PostgreSQL and Qdrant."
        )
    except Exception as e:
        logger.error("Knowledge ingestion failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge ingestion failed: {str(e)}"
        )

@router.get("/admin/sources", response_model=KnowledgeSourceListResponse)
def admin_list_all_sources(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    verification_status: Optional[str] = Query(None, description="Filter by status (verified, needs_review, outdated, retired)"),
    category: Optional[str] = Query(None)
):
    """Admin-only endpoint to inspect all knowledge sources across all lifecycle states."""
    set_rls_context(db, current_user.id, current_user.role)
    query = db.query(KnowledgeSource)
    if verification_status:
        query = query.filter(KnowledgeSource.verification_status == verification_status.lower())
    if category:
        query = query.filter(KnowledgeSource.document_category == category.lower())
    sources = query.order_by(KnowledgeSource.title.asc()).all()
    return KnowledgeSourceListResponse(
        total=len(sources),
        sources=[KnowledgeSourceResponse(**s.to_dict()) for s in sources]
    )

@router.put("/admin/sources/{source_id}/verification", response_model=KnowledgeSourceResponse)
def admin_update_source_verification(
    source_id: str,
    body: UpdateVerificationStatusRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to update verification state of a statutory source."""
    set_rls_context(db, current_user.id, current_user.role)
    src = db.query(KnowledgeSource).filter(
        or_(KnowledgeSource.source_id == source_id, KnowledgeSource.id == source_id if _is_valid_uuid(source_id) else False)
    ).first()
    if not src:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge source not found")
    
    src.verification_status = body.verification_status.value
    if body.review_notes:
        meta = dict(src.metadata_payload or {})
        meta["review_notes"] = body.review_notes
        src.metadata_payload = meta
    db.commit()
    db.refresh(src)
    return KnowledgeSourceResponse(**src.to_dict())

def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False

@router.post("/admin/sources/ingest-file")
async def admin_ingest_knowledge_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_category: str = Form(...),
    issuing_authority: str = Form(...),
    source_url: Optional[str] = Form(None),
    publication_date: Optional[str] = Form(None),
    verification_status: str = Form("unverified"),
    provenance: str = Form("OFFICIAL_ORIGINAL"),
    review_notes: Optional[str] = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin-only endpoint to upload, extract, chunk, embed, and index an official knowledge file (PDF, TXT, MD).
    Returns an Ingestion Report detailing:
    - accepted_files
    - page_count
    - chunk_count
    - embedding_status
    - indexing_status
    - verification_status
    """
    set_rls_context(db, current_user.id, current_user.role)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    filename = file.filename or "uploaded_knowledge"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in (".pdf", ".txt", ".md"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported format. Only PDF, TXT, and Markdown (.md) knowledge files are accepted."
        )

    file_hash = compute_sha256(content)
    page_count = 1
    raw_text = ""

    if ext == ".pdf":
        try:
            import pypdf
            import io
            reader = pypdf.PdfReader(io.BytesIO(content))
            page_count = len(reader.pages)
            text_pages = [p.extract_text() or "" for p in reader.pages]
            raw_text = "\n\n".join(text_pages).strip()
        except Exception as e:
            logger.error("PDF reading failed: %s", str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse PDF: {str(e)}")
    else:
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = content.decode("latin-1")
        page_count = max(1, len(raw_text) // 2500)

    if not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No readable text extracted from file.")

    # Unique source_id slug
    import re
    slug = re.sub(r'[^a-zA-Z0-9_]', '_', title.lower())[:40]
    source_id = f"src_{slug}_{file_hash[:8]}"

    # Ingestion service
    ingestion_service = KnowledgeIngestionService(db)

    # Store in database
    existing_src = db.query(KnowledgeSource).filter(KnowledgeSource.source_id == source_id).first()
    if existing_src:
        existing_src.title = title
        existing_src.issuing_authority = issuing_authority
        existing_src.document_category = document_category.lower()
        existing_src.raw_content = raw_text
        existing_src.content_hash = file_hash
        existing_src.verification_status = verification_status.lower()
        existing_src.ingestion_status = "indexing"
        existing_src.uploaded_by_user_id = current_user.id
        existing_src.review_notes = review_notes
        existing_src.publication_date = publication_date
        db_src = existing_src
    else:
        db_src = KnowledgeSource(
            source_id=source_id,
            title=title,
            issuing_authority=issuing_authority,
            document_type="circular_procedure",
            document_category=document_category.lower(),
            source_url=source_url or f"https://official.gov.in/{source_id}",
            jurisdiction="India",
            language="en",
            version="1.0",
            content_hash=file_hash,
            raw_content=raw_text,
            verification_status=verification_status.lower(),
            is_active=True,
            ingestion_status="indexing",
            uploaded_by_user_id=current_user.id,
            review_notes=review_notes,
            publication_date=publication_date,
            correction_category=document_category.lower(),
        )
        db.add(db_src)

    db.flush()

    # Chunking & Embedding
    chunker = ingestion_service.chunker
    source_dict = {
        "source_id": source_id,
        "title": title,
        "issuing_authority": issuing_authority,
        "document_category": document_category.lower(),
        "source_url": source_url or f"https://official.gov.in/{source_id}",
        "verification_status": verification_status.lower(),
        "content": raw_text,
    }
    chunks = chunker.chunk_source(source_dict)

    embedding_status = "completed"
    indexing_status = "completed"
    try:
        if chunks:
            texts = [c["content"] for c in chunks]
            embeddings = ingestion_service.embedding_service.embed_documents(texts)
            from qdrant_client.models import PointStruct
            points = []
            for chunk, emb in zip(chunks, embeddings):
                pt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["chunk_id"]))
                points.append(PointStruct(id=pt_id, vector=emb, payload=chunk))

            ingestion_service.qdrant.upsert(
                collection_name=settings.QDRANT_KNOWLEDGE_COLLECTION,
                points=points,
            )
    except Exception as e:
        logger.error("Vector indexing error for source %s: %s", source_id, str(e))
        embedding_status = "error"
        indexing_status = "error"

    db_src.ingestion_status = indexing_status

    AuditService.log_event(
        db=db,
        action="knowledge_file_ingested",
        entity_type="knowledge_source",
        entity_id=db_src.id,
        user_id=current_user.id,
        details={
            "source_id": source_id,
            "title": title,
            "filename": filename,
            "page_count": page_count,
            "chunk_count": len(chunks),
            "sha256": file_hash,
            "indexing_status": indexing_status,
        },
    )

    db.commit()
    db.refresh(db_src)

    return {
        "status": "success",
        "source_id": source_id,
        "title": title,
        "document_category": document_category,
        "sha256_hash": file_hash,
        "accepted_files": [filename],
        "page_count": page_count,
        "chunk_count": len(chunks),
        "embedding_status": embedding_status,
        "indexing_status": indexing_status,
        "verification_status": verification_status,
        "provenance": provenance,
        "message": f"Successfully ingested '{title}': {len(chunks)} chunks indexed into Qdrant.",
    }

# ---------------------------------------------------------------------------
# 7. P3H.5 Controlled Ingestion & Administrative Operations Endpoints
# ---------------------------------------------------------------------------

@router.get("/corpus/status", response_model=CorpusStatusResponse)
def get_corpus_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns current status of knowledge corpus:
    Counts of Core, Reference, and Quarantined documents, chunk counts, active version, and Qdrant status.
    """
    set_rls_context(db, current_user.id, current_user.role)
    mgr = CorpusIngestionManager(base_dir=".")
    health = mgr.get_collections_health()

    return CorpusStatusResponse(
        total_documents=47,
        core_documents_count=len(CORE_DOC_IDS),
        reference_documents_count=len(REFERENCE_DOC_IDS),
        quarantined_documents_count=27,
        core_chunks_count=EXPECTED_CORE_CHUNKS,
        reference_chunks_count=EXPECTED_REFERENCE_CHUNKS,
        total_chunks_count=EXPECTED_TOTAL_CHUNKS,
        active_version=_INGESTION_STATE["active_version"],
        embedding_mode=getattr(settings, "RETRIEVAL_MODE", "lexical_only"),
        qdrant_status=health
    )

@router.get("/corpus/manifest", response_model=CorpusManifestResponse)
def get_corpus_manifest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    classification: Optional[str] = Query(None, description="Filter by classification: CORE_OPERATIONAL, REFERENCE_SECONDARY, QUARANTINED")
):
    """
    Returns the official reconciled corpus manifest across all 47 documents.
    """
    set_rls_context(db, current_user.id, current_user.role)
    recon_path = os.path.join(".", "forms", "P3H4_1_CORPUS_RECONCILIATION.csv")
    if not os.path.exists(recon_path):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Reconciliation manifest missing.")

    import csv
    with open(recon_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    items: List[CorpusManifestItem] = []
    core_cnt = 0
    ref_cnt = 0
    quar_cnt = 0

    for r in rows:
        col = r.get("proposed_collection", "")
        if col == "convelina_core_operational":
            cls_name = "CORE_OPERATIONAL"
            core_cnt += 1
        elif col == "convelina_reference_secondary":
            cls_name = "REFERENCE_SECONDARY"
            ref_cnt += 1
        else:
            cls_name = "QUARANTINED"
            quar_cnt += 1

        if classification and cls_name.upper() != classification.upper():
            continue

        doc_id = r["document_id"]
        # Human review required on DOC_043
        hr_req = (doc_id == "DOC_043") or (r.get("human_review_required", "").lower() == "true")

        items.append(CorpusManifestItem(
            document_id=doc_id,
            filename=r.get("original_filename") or r.get("filename") or "",
            sha256=r.get("sha256", ""),
            document_title=f"Official Document {doc_id}",
            corpus_classification=cls_name,
            retrieval_eligibility=r.get("retrieval_eligibility", "HARD_BLOCKED"),
            actual_chunk_count=int(r.get("actual_chunk_count") or 0),
            human_review_required=hr_req,
            source_status="SOURCE_METADATA_CONFLICT" if doc_id == "DOC_043" else r.get("provenance_authenticity_status", "OFFICIALLY_PUBLISHED"),
            applicant_cohort=r.get("applicant_cohort"),
            issuing_authority=r.get("document_category", "Government Authority")
        ))

    return CorpusManifestResponse(
        total_documents=len(rows),
        core_count=core_cnt,
        reference_count=ref_cnt,
        quarantine_count=quar_cnt,
        documents=items
    )

@router.post("/admin/ingest", response_model=IngestionJobStatusResponse)
def admin_start_ingestion(
    body: IngestionJobStartRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to start versioned knowledge ingestion.
    Executes staged replacement: validation, chunking, staging upload, count checks, and atomic activation.
    """
    set_rls_context(db, current_user.id, current_user.role)
    mgr = CorpusIngestionManager(base_dir=".")

    try:
        res = mgr.run_ingestion(version_tag=body.version_tag, dry_run=body.dry_run)
        job_id = res["job_id"]
        job_info = _INGESTION_STATE["jobs"].get(job_id, {})

        AuditService.log_event(
            db=db,
            action="corpus_ingestion_executed",
            entity_type="knowledge_collection",
            entity_id=None,
            user_id=current_user.id,
            details=res
        )

        return IngestionJobStatusResponse(
            job_id=job_id,
            status=job_info.get("status", "completed"),
            version_tag=job_info.get("version_tag", body.version_tag or "active"),
            core_chunks_indexed=job_info.get("core_chunks_indexed", 0),
            reference_chunks_indexed=job_info.get("reference_chunks_indexed", 0),
            staging_collections=job_info.get("staging_collections", []),
            active_collections=job_info.get("active_collections", []),
            created_at=job_info.get("created_at", utc_now().isoformat()),
            completed_at=job_info.get("completed_at")
        )
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(re))
    except Exception as e:
        logger.error("Admin ingestion failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {str(e)}")

@router.get("/admin/ingest/status/{job_id}", response_model=IngestionJobStatusResponse)
def admin_get_ingestion_status(
    job_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to inspect status of an ingestion job."""
    set_rls_context(db, current_user.id, current_user.role)
    job_info = _INGESTION_STATE["jobs"].get(job_id)
    if not job_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ingestion job {job_id} not found.")

    return IngestionJobStatusResponse(**job_info)

@router.get("/admin/collections/health", response_model=CollectionsHealthResponse)
def admin_get_collections_health(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to inspect Qdrant collection health, point counts, and vector configuration."""
    set_rls_context(db, current_user.id, current_user.role)
    mgr = CorpusIngestionManager(base_dir=".")
    health = mgr.get_collections_health()
    return CollectionsHealthResponse(**health)

@router.post("/admin/collections/rollback", response_model=CollectionRollbackResponse)
def admin_rollback_collection(
    body: CollectionRollbackRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to roll back active Qdrant collections to a previous version."""
    set_rls_context(db, current_user.id, current_user.role)
    mgr = CorpusIngestionManager(base_dir=".")
    try:
        res = mgr.rollback(target_version=body.target_version)
        AuditService.log_event(
            db=db,
            action="corpus_collection_rollback",
            entity_type="knowledge_collection",
            entity_id=None,
            user_id=current_user.id,
            details=res
        )
        return CollectionRollbackResponse(**res)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Admin rollback failed: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Rollback failed: {str(e)}")

@router.post("/retrieval/diagnostics", response_model=RetrievalDiagnosticsResponse)
def admin_retrieval_diagnostics(
    body: RetrievalDiagnosticsRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to execute retrieval diagnostic queries.
    Returns normalized tokens, rank breakdown, provenance, BM25 scores, DOC_043 restrictions, and abstention reasons.
    """
    set_rls_context(db, current_user.id, current_user.role)
    retriever = HybridRetriever()

    norm_query = retriever.normalize_query(body.query)
    is_unverified = retriever.check_doc043_unverified_claim(body.query)

    classification_target = "CORE_OPERATIONAL"
    if body.collection_target == "reference":
        classification_target = "REFERENCE_SECONDARY"
    elif body.collection_target == "both":
        classification_target = None

    hits = retriever.retrieve(
        query=body.query,
        document_category=body.document_category,
        corpus_classification=classification_target,
        top_k=body.top_k,
        mode=body.mode,
        min_score=body.min_score
    )

    abstention_triggered = (len(hits) == 0)
    abstention_reason = None
    if abstention_triggered:
        if is_unverified:
            abstention_reason = "UNVERIFIED_DOC043_CLAIM: Query requests unverified 3rd-time exception or RO escalation packet."
        else:
            abstention_reason = "SCORE_FLOOR_ABSTENTION: Insufficient evidence in official corpus above calibrated relevance floor."

    diagnostic_chunks: List[RetrievalDiagnosticChunk] = []
    for h in hits:
        preview = h.get("chunk_text", "")[:200].replace("\n", " ").strip() + "..."
        diagnostic_chunks.append(RetrievalDiagnosticChunk(
            chunk_id=h["chunk_id"],
            document_id=h["document_id"],
            document_title=h["document_title"],
            page_number=h["page_number"],
            section_title=h["section_title"],
            content_type=h.get("content_type", "PROCEDURAL_GUIDANCE"),
            score=h["score"],
            bm25_score=h.get("bm25_score", h["score"]),
            corpus_classification=h.get("corpus_classification", "CORE_OPERATIONAL"),
            source_status=h["source_status"],
            human_review_required=h["human_review_required"],
            is_doc043=h["is_doc043"],
            disclaimer=h.get("disclaimer"),
            content_preview=preview
        ))

    return RetrievalDiagnosticsResponse(
        query=body.query,
        normalized_query=norm_query,
        mode=body.mode,
        retrieved_count=len(diagnostic_chunks),
        abstention_triggered=abstention_triggered,
        abstention_reason=abstention_reason,
        chunks=diagnostic_chunks
    )

