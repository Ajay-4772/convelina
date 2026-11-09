import os
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.core.database import get_db, set_rls_context
from app.core.validator import validate_document_type, sanitize_filename, validate_file_content
from app.core.storage import save_temp_document, delete_temp_document
from app.core.encryption import encrypt_data
from app.core.sanitizer import sanitize_pii
from app.core.synthetic_documents import (
    generate_synthetic_document_pdf,
    generate_synthetic_document_image,
    SYNTHETIC_DATA_PROFILES,
)
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentFieldsUpdate,
    DocumentConfirmRequest,
)
from app.ocr.engine import default_ocr_engine
from app.ocr.field_extractor import FieldExtractor
from app.services.audit_service import AuditService
from app.services.identity_matching.models import DocumentIdentityProfile
from app.services.identity_matching.service import DocumentComparisonService

logger = logging.getLogger("convelina.documents")
router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.get("/synthetic-samples")
def list_synthetic_samples():
    """
    Returns the list of available synthetic development document profiles.
    These are fictional test samples used for development and verification.
    """
    samples = []
    for cat, profile in SYNTHETIC_DATA_PROFILES.items():
        samples.append({
            "category": cat,
            "title": profile.get("title", cat),
            "full_name": profile.get("full_name"),
            "provenance": "SYNTHETIC_TEST_ASSET",
            "formats": ["pdf", "png"],
            "disclaimer": "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM",
        })
    return {"samples": samples}


@router.get("/synthetic-samples/{category}")
def download_synthetic_sample(
    category: str,
    format: str = Query("pdf", pattern="^(pdf|png)$"),
):
    """
    Streams a generated synthetic test document (PDF or PNG) with prominent
    synthetic development sample banners and fictional demographic data.
    """
    cat = category.lower()
    if cat not in SYNTHETIC_DATA_PROFILES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown synthetic category '{category}'. Available: {list(SYNTHETIC_DATA_PROFILES.keys())}",
        )

    headers = {
        "X-Convelina-Provenance": "SYNTHETIC_TEST_ASSET",
        "X-Convelina-Disclaimer": "SYNTHETIC DEVELOPMENT SAMPLE - NOT AN OFFICIAL GOVERNMENT FORM",
    }

    if format == "png":
        img_bytes = generate_synthetic_document_image(cat)
        headers["Content-Disposition"] = f'attachment; filename="synthetic_{cat}_sample.png"'
        return Response(content=img_bytes, media_type="image/png", headers=headers)
    else:
        pdf_bytes = generate_synthetic_document_pdf(cat)
        headers["Content-Disposition"] = f'attachment; filename="synthetic_{cat}_sample.pdf"'
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Secure Document Upload & Synchronous Initial OCR Extraction.
    - Validates file size, magic bytes, and integrity.
    - Executes OCR extraction via Tesseract with confidence scoring.
    - Runs 14-step field-level schema extraction per category.
    - Enforces PostgreSQL RLS on storage.
    - Unlinks raw temporary image file per Aadhaar Act privacy guidelines.
    """
    # 1. Validate document type
    clean_doc_type = validate_document_type(document_type)

    # 2. Sanitize filename
    safe_filename = sanitize_filename(file.filename or "uploaded_document")

    # 3. Read uploaded bytes with bounded streaming to prevent memory-exhaustion DoS
    try:
        max_bytes = settings.MAX_UPLOAD_SIZE_BYTES
        chunk_size = 1024 * 1024  # 1 MB chunks
        content_buffer = bytearray()
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            content_buffer.extend(chunk)
            if len(content_buffer) > max_bytes:
                max_mb = max_bytes / (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File exceeds maximum allowed size of {max_mb:.1f} MB.",
                )
        content = bytes(content_buffer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file stream.",
        )

    # 4. Deep file validation: magic bytes, size, and corruption checks
    detected_format, ext = validate_file_content(content, safe_filename)

    # 5. Save to secure temporary directory
    temp_file_path, file_hash = save_temp_document(content, ext)

    # 6. OCR Text Extraction & Field-Level Schema Extraction
    ocr_status_val = "pending"
    extracted_fields = {}
    field_extractions_dict = {}
    masked_id = None
    encrypted_payload = None

    try:
        raw_text, ocr_conf = default_ocr_engine.extract_text_and_confidence(
            temp_file_path, is_pdf=(detected_format == "pdf")
        )

        extraction_result = FieldExtractor.extract_category_fields(
            document_type=clean_doc_type,
            raw_text=raw_text,
            overall_confidence=ocr_conf,
            page_number=1,
        )

        field_extractions_dict = {
            fname: res.model_dump()
            for fname, res in extraction_result.field_extractions.items()
        }
        extracted_fields = extraction_result.fields_flat
        masked_id = extraction_result.masked_id
        ocr_status_val = "needs_review" if extraction_result.requires_manual_review else "completed"

        # Encrypt sensitive full raw text at rest after pre-persistence PII sanitization
        if raw_text:
            sanitized_text, _, _ = sanitize_pii(raw_text)
            encrypted_payload = encrypt_data(sanitized_text)

    except Exception as e:
        logger.error("OCR extraction error for doc_type=%s: %s", clean_doc_type, str(e))
        ocr_status_val = "failed"
        extracted_fields = {"error": "OCR extraction failed or low confidence"}
        field_extractions_dict = {}
    finally:
        # 7. Privacy & Retention: cleanup temporary local file if configured
        final_file_path = temp_file_path
        if settings.STORAGE_RETENTION_POLICY == "delete_after_ocr":
            delete_temp_document(temp_file_path)
            final_file_path = f"ephemeral://redacted_{file_hash[:16]}"

    # 8. Database insertion under caller's transaction-local RLS context
    try:
        set_rls_context(db, current_user.id, current_user.role)
        new_doc = Document(
            user_id=current_user.id,
            document_type=clean_doc_type,
            file_path=final_file_path,
            file_hash=file_hash,
            ocr_status=ocr_status_val,
            extracted_fields=extracted_fields,
            field_extractions=field_extractions_dict,
            confirmed_fields={},
            is_user_confirmed=False,
            confirmed_at=None,
            masked_id=masked_id,
            encrypted_data=encrypted_payload,
        )
        db.add(new_doc)
        db.flush()

        response_payload = DocumentUploadResponse(
            id=str(new_doc.id),
            document_type=new_doc.document_type,
            file_hash=new_doc.file_hash,
            ocr_status=new_doc.ocr_status,
            masked_id=new_doc.masked_id,
            extracted_fields=new_doc.extracted_fields or {},
            field_extractions=new_doc.field_extractions or {},
            confirmed_fields=new_doc.confirmed_fields or {},
            is_user_confirmed=bool(new_doc.is_user_confirmed),
            confirmed_at=new_doc.confirmed_at.isoformat() if new_doc.confirmed_at else None,
            message=f"Document uploaded and OCR {ocr_status_val} successfully.",
            created_at=new_doc.created_at.isoformat() if new_doc.created_at else "",
        )
        db.commit()
    except Exception as e:
        db.rollback()
        # Clean up temp file on database failure if not already cleaned
        if os.path.exists(temp_file_path):
            delete_temp_document(temp_file_path)
        logger.error("Database error creating document record: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record document metadata in database."
        )

    return response_payload


@router.get("", response_model=DocumentListResponse)
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists documents visible to the current authenticated caller.
    Protected by PostgreSQL Row-Level Security:
    - Citizens see only their own documents.
    - Admins see all documents.
    """
    set_rls_context(db, current_user.id, current_user.role)
    docs = db.query(Document).order_by(Document.created_at.desc()).all()

    doc_responses = [
        DocumentResponse(
            id=str(d.id),
            user_id=str(d.user_id),
            document_type=d.document_type,
            file_hash=d.file_hash,
            ocr_status=d.ocr_status,
            masked_id=d.masked_id,
            extracted_fields=d.extracted_fields or {},
            field_extractions=d.field_extractions or {},
            confirmed_fields=d.confirmed_fields or {},
            is_user_confirmed=bool(d.is_user_confirmed),
            confirmed_at=d.confirmed_at.isoformat() if d.confirmed_at else None,
            created_at=d.created_at.isoformat() if d.created_at else "",
            updated_at=d.updated_at.isoformat() if d.updated_at else "",
        )
        for d in docs
    ]
    return DocumentListResponse(total=len(doc_responses), documents=doc_responses)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetches a specific document by ID.
    Enforces RLS: If caller is not authorized to view the document, returns 404.
    """
    set_rls_context(db, current_user.id, current_user.role)
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    return DocumentResponse(
        id=str(doc.id),
        user_id=str(doc.user_id),
        document_type=doc.document_type,
        file_hash=doc.file_hash,
        ocr_status=doc.ocr_status,
        masked_id=doc.masked_id,
        extracted_fields=doc.extracted_fields or {},
        field_extractions=doc.field_extractions or {},
        confirmed_fields=doc.confirmed_fields or {},
        is_user_confirmed=bool(doc.is_user_confirmed),
        confirmed_at=doc.confirmed_at.isoformat() if doc.confirmed_at else None,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
        updated_at=doc.updated_at.isoformat() if doc.updated_at else "",
    )


@router.get("/{document_id}/profile", response_model=DocumentIdentityProfile)
def get_document_identity_profile(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the canonical DocumentIdentityProfile for a specific document.
    Prioritizes user-confirmed values over machine OCR extractions while preserving
    confidence metrics and flags.
    Enforces PostgreSQL Row-Level Security.
    """
    set_rls_context(db, current_user.id, current_user.role)
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    return DocumentComparisonService.create_profile_from_document(doc)


@router.post("/{document_id}/confirm", response_model=DocumentResponse)
def confirm_document_fields(
    document_id: UUID,
    payload: DocumentConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Citizen confirms or corrects the demographic fields extracted from their document.
    Maintains clean separation between machine extraction (field_extractions) and
    user confirmation (confirmed_fields).
    Audit-logs the confirmation event.
    """
    set_rls_context(db, current_user.id, current_user.role)
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    # Sanitize and store confirmed fields
    confirmed = {}
    for k, v in payload.confirmed_fields.items():
        if v is not None:
            confirmed[k] = str(v).strip()

    doc.confirmed_fields = confirmed
    doc.is_user_confirmed = True
    now = datetime.now(timezone.utc)
    doc.confirmed_at = now

    # If document had "needs_review" status, user confirmation moves it to "completed"
    if doc.ocr_status == "needs_review":
        doc.ocr_status = "completed"

    # Audit log the user confirmation
    try:
        AuditService.log_event(
            db=db,
            action="document_fields_confirmed",
            entity_type="document",
            entity_id=doc.id,
            user_id=current_user.id,
            details={
                "document_type": doc.document_type,
                "confirmed_fields_count": len(confirmed),
                "is_user_confirmed": True,
            },
        )
    except Exception as e:
        logger.warning("Failed to record audit log for document confirmation: %s", str(e))

    db.commit()

    return DocumentResponse(
        id=str(doc.id),
        user_id=str(doc.user_id),
        document_type=doc.document_type,
        file_hash=doc.file_hash,
        ocr_status=doc.ocr_status,
        masked_id=doc.masked_id,
        extracted_fields=doc.extracted_fields or {},
        field_extractions=doc.field_extractions or {},
        confirmed_fields=doc.confirmed_fields or {},
        is_user_confirmed=bool(doc.is_user_confirmed),
        confirmed_at=doc.confirmed_at.isoformat() if doc.confirmed_at else None,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
        updated_at=doc.updated_at.isoformat() if doc.updated_at else "",
    )


@router.patch("/{document_id}/fields", response_model=DocumentResponse)
def update_document_fields(
    document_id: UUID,
    payload: DocumentFieldsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Allows a citizen to review, correct, or confirm extracted demographic fields
    (e.g., if OCR misread an initial, character, or format) under PostgreSQL RLS.
    """
    set_rls_context(db, current_user.id, current_user.role)
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    updated_fields = dict(doc.extracted_fields or {})
    for k, v in payload.extracted_fields.items():
        if v is not None:
            updated_fields[k] = str(v).strip()

    doc.extracted_fields = updated_fields

    # Changing underlying document fields invalidates previous confirmation
    was_confirmed = bool(doc.is_user_confirmed)
    if was_confirmed:
        doc.is_user_confirmed = False
        doc.confirmed_at = None
        try:
            AuditService.log_event(
                db=db,
                action="document_confirmation_invalidated",
                entity_type="document",
                entity_id=doc.id,
                user_id=current_user.id,
                details={
                    "document_type": doc.document_type,
                    "reason": "Document fields updated via PATCH /fields",
                },
            )
        except Exception as e:
            logger.warning("Failed to record audit log for document confirmation invalidation: %s", str(e))

    response = DocumentResponse(
        id=str(doc.id),
        user_id=str(doc.user_id),
        document_type=doc.document_type,
        file_hash=doc.file_hash,
        ocr_status=doc.ocr_status,
        masked_id=doc.masked_id,
        extracted_fields=updated_fields,
        field_extractions=doc.field_extractions or {},
        confirmed_fields=doc.confirmed_fields or {},
        is_user_confirmed=bool(doc.is_user_confirmed),
        confirmed_at=doc.confirmed_at.isoformat() if doc.confirmed_at else None,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
        updated_at=doc.updated_at.isoformat() if doc.updated_at else "",
    )
    db.commit()

    return response


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deletes a document record and purges any associated temporary files.
    Enforces RLS: Citizens can only delete their own documents.
    """
    set_rls_context(db, current_user.id, current_user.role)
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or unauthorized to delete."
        )

    # Unlink file if it exists on disk
    if doc.file_path and not doc.file_path.startswith("ephemeral://"):
        delete_temp_document(doc.file_path)

    db.delete(doc)
    db.commit()

    return {"message": "Document deleted successfully.", "id": str(document_id)}
