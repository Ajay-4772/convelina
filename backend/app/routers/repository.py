import logging
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.models.official_form import OfficialForm, utc_now
from app.services.audit_service import AuditService
from app.services.repository_service import CitizenRepositoryService
from app.services.checklist_service import ChecklistService
from app.services.procedural_guidance_service import ProceduralGuidanceService
from app.rag.schemas import (
    RepositoryResourceItem,
    RepositoryResourceDetail,
    RepositoryResourceListResponse,
    ChecklistResponse,
    ChecklistItemProgressUpdate,
    ChecklistProgressResponse,
    ProceduralGuidanceRequest,
    ProceduralGuidanceResponse,
    PersonalizedGuidanceResponse,
    AdminResourceVerifyRequest,
    AdminResourceLifecycleRequest,
)

logger = logging.getLogger("convelina.repository.router")
router = APIRouter(prefix="/api/v1/repository", tags=["Citizen Document Repository"])


# ---------------------------------------------------------------------------
# 1. Citizen Document Repository Listing & Search
# ---------------------------------------------------------------------------

@router.get("/resources", response_model=RepositoryResourceListResponse)
def list_repository_resources(
    category: Optional[str] = Query(None, description="Identity category: aadhaar, pan, passport, class_10, class_12, epf, or all"),
    document_type: Optional[str] = Query(None, description="Document type filter: application_form, proof_matrix, correction_procedure, alternative_evidence, reference_circular"),
    provenance: Optional[str] = Query(None, description="Provenance: OFFICIAL_ORIGINAL, OFFICIAL_COPY, GOVERNMENT_REFERENCE, HISTORICAL_REFERENCE, APPLICATION_GENERATED, SYNTHETIC_DEVELOPMENT_SAMPLE, UNVERIFIED_SOURCE"),
    verification_status: Optional[str] = Query(None, description="Verification status: verified, needs_review, outdated, retired, source_metadata_conflict"),
    search: Optional[str] = Query(None, description="Search terms matching title, authority, purpose, or id"),
    sort_by: str = Query("relevance", description="Sort order: relevance, date_desc, title_asc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
):
    """
    Searchable, paginated citizen repository listing across the 6 supported identity categories:
    Aadhaar Card, PAN Card, Passport, Class 10 Certificate, Class 12 Certificate, and EPF/UAN Records.
    Enforces provenance classifications and verification states.
    """
    return CitizenRepositoryService.list_resources(
        category=category,
        document_type=document_type,
        provenance=provenance,
        verification_status=verification_status,
        search_query=search,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@router.get("/resources/{resource_id}", response_model=RepositoryResourceDetail)
def get_repository_resource_detail(
    resource_id: str,
):
    """
    Returns rich, dedicated document detail view:
    - Overview, purpose, authority, and provenance classification
    - Applicable cohorts (who should use it)
    - Related correction procedures
    - Supporting-document checklist
    - Preview & download paths
    - Source citations, page/section references, and statutory limitations
    """
    detail = CitizenRepositoryService.get_resource_detail(resource_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource '{resource_id}' was not found in the official repository catalog.",
        )
    return detail


@router.get("/categories")
def get_categories_summary():
    """
    Returns high-level summary and document counts across the 6 supported identity categories.
    """
    return CitizenRepositoryService.get_categories_summary()


# ---------------------------------------------------------------------------
# 2. Safe Preview & Download Endpoints
# ---------------------------------------------------------------------------

@router.get("/resources/{resource_id}/download")
def download_resource_file(
    resource_id: str,
):
    """
    Secure file download endpoint with path-traversal prevention.
    Streams official or synthetic sample PDF with attachment headers.
    """
    file_info = CitizenRepositoryService.resolve_file_path(resource_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical file for resource '{resource_id}' is unavailable or cannot be downloaded.",
        )

    abs_path, filename, mime_type = file_info
    return FileResponse(
        path=abs_path,
        media_type=mime_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/resources/{resource_id}/preview")
def preview_resource_file(
    resource_id: str,
):
    """
    Inline preview endpoint with path-traversal prevention.
    Streams PDF for browser rendering.
    """
    file_info = CitizenRepositoryService.resolve_file_path(resource_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Physical file for resource '{resource_id}' is unavailable for preview.",
        )

    abs_path, filename, mime_type = file_info
    return FileResponse(
        path=abs_path,
        media_type=mime_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# 3. Supporting-Document Checklist Engine Endpoints
# ---------------------------------------------------------------------------

@router.get("/checklists/{procedure_id}", response_model=ChecklistResponse)
def get_procedure_checklist(
    procedure_id: str,
):
    """
    Returns evidence-backed supporting document checklist for a procedure.
    Distinguishes:
    - VERIFIED_MANDATORY
    - VERIFIED_CONDITIONAL
    - RECOMMENDED
    - HUMAN_REVIEW_REQUIRED
    """
    checklist = ChecklistService.get_checklist_for_procedure(procedure_id)
    if not checklist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checklist for procedure '{procedure_id}' was not found.",
        )
    return checklist


@router.get("/checklists/category/{category}", response_model=List[ChecklistResponse])
def get_category_checklists(
    category: str,
):
    """
    Returns all standard checklists for a supported identity category.
    """
    return ChecklistService.get_checklists_for_category(category)


@router.get("/checklists/{procedure_id}/progress", response_model=ChecklistProgressResponse)
def get_user_checklist_progress(
    procedure_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns persistent citizen checklist preparation progress for the authenticated user.
    Enforces Row-Level Security isolation.
    """
    set_rls_context(db, current_user.id, current_user.role)
    return ChecklistService.get_user_progress(db=db, user_id=current_user.id, procedure_id=procedure_id)


@router.put("/checklists/{procedure_id}/progress", response_model=ChecklistProgressResponse)
def update_user_checklist_progress(
    procedure_id: str,
    update: ChecklistItemProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates completion state of a specific checklist item for the authenticated citizen.
    - Validates item against authoritative statutory checklist definitions
    - Citizens cannot modify statutory verification categories or criteria
    - Persists completion with timestamp in PostgreSQL under forced RLS
    - Emits immutable cryptographic audit record
    """
    set_rls_context(db, current_user.id, current_user.role)
    try:
        return ChecklistService.update_user_item_progress(
            db=db,
            user_id=current_user.id,
            procedure_id=procedure_id,
            item_id=update.item_id,
            is_completed=update.is_completed,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resources/{resource_id}/checklist-progress", response_model=ChecklistProgressResponse)
def get_resource_checklist_progress(
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns checklist progress for a given resource or its primary associated correction procedure.
    """
    set_rls_context(db, current_user.id, current_user.role)
    detail = CitizenRepositoryService.get_resource_detail(resource_id)
    procedure_id = resource_id
    if detail and detail.related_procedure_ids:
        procedure_id = detail.related_procedure_ids[0]
    return ChecklistService.get_user_progress(db=db, user_id=current_user.id, procedure_id=procedure_id)



# ---------------------------------------------------------------------------
# 4. Procedural Guidance Synthesis Endpoints
# ---------------------------------------------------------------------------

@router.post("/guidance/synthesize", response_model=ProceduralGuidanceResponse)
def synthesize_procedural_guidance(
    payload: ProceduralGuidanceRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Synthesizes grounded step-by-step procedural guidance for citizen questions.
    Enforces:
    - Statutory abstention on unverified or third-time exception claims
    - Preservation of DOC_043 restrictions (SOURCE_METADATA_CONFLICT, limitation notice)
    - Inclusion of relevant supporting document checklists and verified citations
    - Inclusion of mandatory comparison and synthetic disclaimers
    """
    if current_user:
        set_rls_context(db, current_user.id, current_user.role)
    return ProceduralGuidanceService.synthesize_guidance(payload=payload, current_user=current_user, db=db)


@router.get("/guidance/personalized", response_model=PersonalizedGuidanceResponse)
def get_personalized_guidance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves active discrepancies for the authenticated citizen from Module 5 (/api/v1/conflicts)
    and generates personalized, evidence-backed procedural guidance.
    Protected by PostgreSQL Row-Level Security: strictly scoped to current user.
    """
    set_rls_context(db, current_user.id, current_user.role)
    return ProceduralGuidanceService.get_personalized_guidance(current_user=current_user, db=db)


# ---------------------------------------------------------------------------
# 5. Administrative Repository Endpoints (Role: ADMIN only)
# ---------------------------------------------------------------------------

@router.put("/admin/resources/{resource_id}/verify", response_model=RepositoryResourceDetail)
def admin_verify_resource(
    resource_id: str,
    payload: AdminResourceVerifyRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin endpoint to verify or update provenance classification for a repository asset.
    Mandatory restrictions:
    - Requires explicit provenance evidence and review notes.
    - Application-generated or ReportLab PDFs can NEVER be marked as OFFICIAL_ORIGINAL or OFFICIAL_COPY.
    - Audited in tamper-evident audit log.
    """
    set_rls_context(db, current_user.id, current_user.role)

    detail = CitizenRepositoryService.get_resource_detail(resource_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource '{resource_id}' not found.",
        )

    target_prov = payload.provenance.upper()
    target_status = payload.verification_status.lower()

    # Reject attempt to mark synthetic / application-generated asset as OFFICIAL_ORIGINAL
    if target_prov in ("OFFICIAL_ORIGINAL", "OFFICIAL_COPY"):
        if detail.is_synthetic_sample or detail.provenance in ("SYNTHETIC_DEVELOPMENT_SAMPLE", "APPLICATION_GENERATED", "SYNTHETIC_TEST_ASSET"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot verify asset as OFFICIAL_ORIGINAL or OFFICIAL_COPY: the stored file is an application-generated ReportLab asset, not an authentic government publication."
            )
        file_info = CitizenRepositoryService.resolve_file_path(resource_id)
        if file_info:
            abs_path, _, _ = file_info
            try:
                with open(abs_path, "rb") as f:
                    header = f.read(2048)
                if b"ReportLab" in header:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot verify asset as OFFICIAL_ORIGINAL or OFFICIAL_COPY: the stored file is an application-generated ReportLab asset, not an authentic government publication."
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning("Could not read file header during verification check: %s", e)

    # If document exists in official_forms table, update database record
    form_record = db.query(OfficialForm).filter(OfficialForm.form_id == resource_id).first()
    if form_record:
        old_prov = form_record.provenance
        old_stat = form_record.verification_status
        form_record.provenance = target_prov
        form_record.verification_status = target_status
        form_record.last_verified_at = utc_now()
        form_record.verified_by_user_id = current_user.id
        if payload.review_notes:
            meta = dict(form_record.metadata_payload or {})
            meta["review_notes"] = payload.review_notes
            meta["provenance_evidence"] = payload.provenance_evidence
            form_record.metadata_payload = meta
        db.commit()

        entity_uuid = form_record.id if isinstance(form_record.id, UUID) else None
        try:
            if form_record.id and not entity_uuid:
                entity_uuid = UUID(str(form_record.id))
        except Exception:
            entity_uuid = None

        AuditService.log_event(
            db=db,
            action="admin_repository_resource_verified",
            entity_type="repository_resource",
            entity_id=entity_uuid,
            user_id=current_user.id,
            details={
                "resource_id": str(resource_id),
                "old_provenance": str(old_prov),
                "new_provenance": str(target_prov),
                "old_status": str(old_stat),
                "new_status": str(target_status),
                "evidence": str(payload.provenance_evidence),
            }
        )
    else:
        AuditService.log_event(
            db=db,
            action="admin_repository_resource_verified",
            entity_type="repository_resource",
            entity_id=None,
            user_id=current_user.id,
            details={
                "resource_id": str(resource_id),
                "new_provenance": str(target_prov),
                "new_status": str(target_status),
                "evidence": str(payload.provenance_evidence),
            }
        )

    # Return refreshed detail
    updated = CitizenRepositoryService.get_resource_detail(resource_id)
    return updated


@router.put("/admin/resources/{resource_id}/lifecycle", response_model=RepositoryResourceDetail)
def admin_transition_resource_lifecycle(
    resource_id: str,
    payload: AdminResourceLifecycleRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Transitions repository resource lifecycle status (outdated, retired, needs_review, verified).
    Audited in append-only audit log.
    """
    set_rls_context(db, current_user.id, current_user.role)

    detail = CitizenRepositoryService.get_resource_detail(resource_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource '{resource_id}' not found.",
        )

    form_record = db.query(OfficialForm).filter(OfficialForm.form_id == resource_id).first()
    if form_record:
        old_status = form_record.verification_status
        form_record.verification_status = payload.verification_status.lower()
        if payload.verification_status.lower() in ("retired", "outdated"):
            form_record.is_active = False
        db.commit()

        AuditService.log_event(
            db=db,
            action="admin_repository_resource_lifecycle_changed",
            entity_type="repository_resource",
            entity_id=form_record.id,
            user_id=current_user.id,
            details={
                "resource_id": resource_id,
                "old_status": old_status,
                "new_status": payload.verification_status.lower(),
                "reason": payload.reason,
            }
        )

    updated = CitizenRepositoryService.get_resource_detail(resource_id)
    return updated
