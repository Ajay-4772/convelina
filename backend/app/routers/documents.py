import os
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.core.database import get_db, set_rls_context
from app.core.validator import validate_document_type, sanitize_filename, validate_file_content
from app.core.storage import save_temp_document, delete_temp_document
from app.core.encryption import encrypt_data
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentUploadResponse, DocumentResponse, DocumentListResponse
from app.ocr.engine import default_ocr_engine
from app.ocr.parsers.factory import get_document_parser

logger = logging.getLogger("convelina.documents")
router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

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
    - Executes OCR extraction via Tesseract.
    - Extracts structured fields & masks identifiers (e.g. Aadhaar XXXX-XXXX-1234).
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

    # 6. OCR Text Extraction & Document-specific parsing
    ocr_status_val = "pending"
    extracted_fields = {}
    masked_id = None
    encrypted_payload = None

    try:
        raw_text = default_ocr_engine.extract_text(temp_file_path, is_pdf=(detected_format == "pdf"))
        # Parse fields with dedicated parser
        parser = get_document_parser(clean_doc_type)
        parsed_result = parser.parse(raw_text)
        
        extracted_fields = parsed_result.get("fields", {})
        masked_id = parsed_result.get("masked_id")
        ocr_status_val = "completed"
        
        # Encrypt sensitive full raw text at rest
        if raw_text:
            encrypted_payload = encrypt_data(raw_text)
            
    except Exception as e:
        logger.error("OCR extraction error for doc_type=%s: %s", clean_doc_type, str(e))
        ocr_status_val = "failed"
        extracted_fields = {"error": "OCR extraction failed or low confidence"}
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
            extracted_fields=new_doc.extracted_fields,
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
    - Officers see assigned citizen documents.
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
        created_at=doc.created_at.isoformat() if doc.created_at else "",
        updated_at=doc.updated_at.isoformat() if doc.updated_at else "",
    )

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
