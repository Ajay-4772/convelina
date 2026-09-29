import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.models.knowledge_source import KnowledgeSource
from app.models.official_form import OfficialForm
from app.rag.forms.catalog import FormCatalogService
from app.rag.ingestion.service import KnowledgeIngestionService
from app.rag.schemas import (
    KnowledgeSourceResponse,
    KnowledgeSourceListResponse,
    OfficialFormResponse,
    OfficialFormListResponse,
    KnowledgeIngestionJobResponse
)

logger = logging.getLogger("consolith.knowledge.router")
router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge & Official Forms"])

@router.get("/sources", response_model=KnowledgeSourceListResponse)
def list_knowledge_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None, description="Filter by document category (aadhaar, pan, passport, epf, education)"),
    document_type: Optional[str] = Query(None, description="Filter by document type")
):
    """
    Returns verified official government knowledge sources.
    Open to all authenticated citizens and officers.
    """
    set_rls_context(db, current_user.id, current_user.role)
    query = db.query(KnowledgeSource).filter(
        KnowledgeSource.is_active == True,
        KnowledgeSource.verification_status == "verified"
    )
    if category:
        query = query.filter(KnowledgeSource.document_category == category.lower())
    if document_type:
        query = query.filter(KnowledgeSource.document_type == document_type.lower())

    sources = query.order_by(KnowledgeSource.title.asc()).all()
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
    """Returns metadata and text for a specific verified government knowledge source."""
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
    issue_type: Optional[str] = Query(None, description="Filter by issue type (full_name, date_of_birth, father_name, gender)")
):
    """
    Returns official government correction and update forms catalog.
    Only returns verified, active official forms.
    """
    set_rls_context(db, current_user.id, current_user.role)
    forms = FormCatalogService.list_forms(db, category=category, issue_type=issue_type)
    return OfficialFormListResponse(total=len(forms), forms=forms)

@router.get("/forms/{form_id}", response_model=OfficialFormResponse)
def get_official_form(
    form_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns official form details, purpose, and download URL."""
    set_rls_context(db, current_user.id, current_user.role)
    form = FormCatalogService.get_form_by_id(db, form_id)
    if not form:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official form not found")
    return form

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
        return KnowledgeIngestionJobResponse(
            job_id=str(uuid.uuid4()),
            status=res.get("status", "success"),
            sources_indexed=res.get("sources_synced", 0),
            forms_indexed=res.get("forms_synced", 0),
            message=f"Synced {res.get('sources_synced', 0)} sources, {res.get('chunks_indexed', 0)} chunks, and {res.get('forms_synced', 0)} forms to PostgreSQL and Qdrant."
        )
    except Exception as e:
        logger.error("Knowledge ingestion failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge ingestion failed: {str(e)}"
        )

def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False
