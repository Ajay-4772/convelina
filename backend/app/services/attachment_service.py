import os
import re
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile

from app.config import settings
from app.core.database import set_rls_context
from app.core.validator import validate_file_content, sanitize_filename
from app.core.storage import (
    save_temp_attachment,
    delete_temp_attachment,
    get_temp_attachment_path,
    compute_sha256,
)
from app.core.sanitizer import sanitize_pii
from app.models.assistant import MessageAttachment, AssistantConversation
from app.models.conflict import Conflict
from app.models.user import User
from app.ocr.engine import default_ocr_engine
from app.services.audit_service import AuditService

logger = logging.getLogger("consolith.services.attachment")

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AttachmentService:
    """
    Confidential Multimodal Attachment Lifecycle & Document Processing Service (Phase P3E).
    Enforces:
    - Lifecycle: UPLOADED -> VALIDATING -> PROCESSING -> READY -> EXPIRED / DELETED
    - Magic byte inspection and MIME-type spoofing rejection
    - Automatic document-type indicator detection (Identity docs, Rejection notices, Affidavits)
    - OCR confidence calculation (< 60% flagged as low_confidence)
    - Pre-persistence PII sanitization for all extracted text and structured fields
    - Private temporary storage with configurable retention (default 24h)
    - Automatic expiry cleanup and explicit deletion
    - Full cryptographic audit logging
    """

    @staticmethod
    def detect_document_type(raw_text: str) -> str:
        """
        Infers document type from textual indicators and statutory markers.
        """
        if not raw_text:
            return "supporting_document"

        lower = raw_text.lower()

        # 1. Rejection or Deficiency Notice
        rejection_markers = [
            "rejected", "rejection", "application rejected", "deficiency",
            "objection", "disapproved", "clarification requested",
            "reason for rejection", "documents required", "action required",
            "discrepancy noticed", "rejection reason"
        ]
        if any(m in lower for m in rejection_markers):
            return "rejection_notice"

        # 2. Aadhaar Document
        if any(m in lower for m in ["aadhaar", "uidai", "unique identification", "enrolment no", "mera aadhaar"]):
            return "aadhaar"

        # 3. PAN Card
        if "permanent account number" in lower or "income tax department" in lower:
            return "pan"
        if re.search(r"\b[a-z]{5}[0-9]{4}[a-z]\b", lower):
            return "pan"

        # 4. Passport
        if "passport" in lower or "republic of india" in lower or "p<ind" in lower:
            return "passport"

        # 5. EPF / EPFO Record
        if any(m in lower for m in ["epfo", "provident fund", "uan", "universal account number", "member id"]):
            return "epf_record"

        # 6. Educational Certificate
        if any(m in lower for m in ["board of secondary", "cbse", "marksheet", "matriculation", "higher secondary"]):
            return "education_certificate"

        # 7. Official Gazette / Deed Poll Affidavit
        if any(m in lower for m in ["deed poll", "gazette notification", "affidavit", "notary public", "first class magistrate"]):
            return "statutory_affidavit_or_gazette"

        return "supporting_document"

    @classmethod
    def extract_document_fields(cls, raw_text: str, doc_type: str) -> Dict[str, Any]:
        """
        Extracts structured fields, dates, masked identifiers, and rejection reasons.
        """
        if not raw_text:
            return {
                "document_type_indicator": doc_type,
                "dates_found": [],
                "rejection_reasons": [],
                "masked_identifiers": {},
                "summary": "No text detected in document.",
            }

        # 1. Detect Dates (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, or Month DD, YYYY)
        date_pattern = re.compile(
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b"
        )
        dates = list(set(date_pattern.findall(raw_text)))[:5]

        # 2. Extract and mask identifiers via PII sanitizer
        sanitized_text, was_redacted, pii_summary = sanitize_pii(raw_text)

        masked_identifiers = {}
        # Find any masked Aadhaar numbers
        masked_aadhars = re.findall(r"XXXX-XXXX-\d{4}", sanitized_text)
        if masked_aadhars:
            masked_identifiers["aadhaar_masked"] = masked_aadhars[0]

        # Find any masked PAN numbers
        masked_pans = re.findall(r"XXXXX\d{4}[A-Z]", sanitized_text)
        if masked_pans:
            masked_identifiers["pan_masked"] = masked_pans[0]

        # 3. Detect Rejection Reasons
        rejection_reasons = []
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        rejection_keywords = ["reason", "rejected", "deficiency", "mismatch", "because", "due to", "clarification"]

        for line in lines:
            line_lower = line.lower()
            if any(k in line_lower for k in rejection_keywords):
                clean_line, _, _ = sanitize_pii(line)
                if len(clean_line) < 200 and clean_line not in rejection_reasons:
                    rejection_reasons.append(clean_line)
                if len(rejection_reasons) >= 3:
                    break

        summary_snip = sanitized_text[:280].replace("\n", " ").strip()
        if len(sanitized_text) > 280:
            summary_snip += "..."

        return {
            "document_type_indicator": doc_type,
            "dates_found": dates,
            "rejection_reasons": rejection_reasons,
            "masked_identifiers": masked_identifiers,
            "has_pii_redacted": was_redacted,
            "summary": summary_snip,
        }

    @classmethod
    async def upload_attachment(
        cls,
        db: Session,
        current_user: User,
        file: UploadFile,
        conversation_id: Optional[str] = None,
        conflict_id: Optional[str] = None,
    ) -> MessageAttachment:
        """
        Stages and validates a confidential chat attachment.
        Executes OCR extraction and stores masked fields under forced RLS.
        """
        set_rls_context(db, current_user.id, current_user.role)

        # 1. Validate conversation_id if provided
        conv_uuid = None
        if conversation_id:
            try:
                conv_uuid = uuid.UUID(conversation_id)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conversation ID format.")
            conv = db.query(AssistantConversation).filter(
                AssistantConversation.id == conv_uuid,
                AssistantConversation.user_id == current_user.id
            ).first()
            if not conv:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or unauthorized.")

        # 2. Validate conflict_id if provided
        conflict_uuid = None
        if conflict_id:
            try:
                conflict_uuid = uuid.UUID(conflict_id)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conflict ID format.")
            conf = db.query(Conflict).filter(
                Conflict.id == conflict_uuid,
                Conflict.user_id == current_user.id
            ).first()
            if not conf:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated conflict not found or unauthorized.")

        # 3. Check attachment count limit for the conversation
        if conv_uuid:
            active_count = db.query(MessageAttachment).filter(
                MessageAttachment.conversation_id == conv_uuid,
                MessageAttachment.user_id == current_user.id,
                MessageAttachment.deleted_at.is_(None)
            ).count()
            max_limit = getattr(settings, "MAX_ATTACHMENTS_PER_MESSAGE", 5) * 4 # Max 20 attachments per conversation
            if active_count >= max_limit:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Attachment limit reached ({max_limit} active attachments for this conversation)."
                )

        # 4. Sanitize filename
        safe_filename = sanitize_filename(file.filename or "uploaded_attachment")

        # 5. Read upload stream with bounded memory protection
        max_bytes = getattr(settings, "MAX_UPLOAD_SIZE_BYTES", 10 * 1024 * 1024)
        chunk_size = 1024 * 1024
        content_buffer = bytearray()
        try:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                content_buffer.extend(chunk)
                if len(content_buffer) > max_bytes:
                    max_mb = max_bytes / (1024 * 1024)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File exceeds maximum allowed size of {max_mb:.1f} MB."
                    )
            content = bytes(content_buffer)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to read uploaded file stream."
            )

        # 6. Deep file inspection: magic bytes, MIME spoofing denial, and image/pdf verification
        detected_format, ext = validate_file_content(content, safe_filename)
        mime_map = {
            "pdf": "application/pdf",
            "jpeg": "image/jpeg",
            "png": "image/png"
        }
        effective_mime = mime_map.get(detected_format, "application/octet-stream")

        # 7. Save to confidential temporary storage
        temp_path, file_hash = save_temp_attachment(content, ext, user_id=str(current_user.id))

        retention_hours = getattr(settings, "ATTACHMENT_RETENTION_HOURS", 24)
        expires_at = utc_now() + timedelta(hours=retention_hours)

        attachment = MessageAttachment(
            id=uuid.uuid4(),
            message_id=None,
            conversation_id=conv_uuid,
            conflict_id=conflict_uuid,
            user_id=current_user.id,
            file_name=safe_filename,
            mime_type=effective_mime,
            file_size_bytes=len(content),
            storage_ref=temp_path,
            sha256_hash=file_hash,
            extracted_text=None,
            extracted_fields={},
            ocr_confidence=None,
            ocr_status="pending",
            status="PROCESSING",
            is_temporary=True,
            expires_at=expires_at,
            deleted_at=None,
            error_message=None
        )
        db.add(attachment)
        db.flush()

        # 8. Synchronous OCR Text Extraction & Analysis
        try:
            is_pdf = (detected_format == "pdf")
            raw_text, ocr_confidence = default_ocr_engine.extract_text_and_confidence(temp_path, is_pdf=is_pdf)

            # Auto-detect document type
            doc_type = cls.detect_document_type(raw_text)

            # Extract structured fields and dates
            fields = cls.extract_document_fields(raw_text, doc_type)

            # Pre-sanitize raw text before persistence
            clean_text, _, _ = sanitize_pii(raw_text)

            attachment.extracted_text = clean_text
            attachment.extracted_fields = fields
            attachment.ocr_confidence = ocr_confidence
            attachment.ocr_status = "low_confidence" if ocr_confidence < 0.60 else "completed"
            attachment.status = "READY"

            logger.info(
                "Attachment %s processed: type=%s, confidence=%.2f, ocr_status=%s",
                attachment.id, doc_type, ocr_confidence, attachment.ocr_status
            )
        except Exception as e:
            logger.error("OCR extraction error for attachment %s: %s", attachment.id, str(e), exc_info=True)
            attachment.status = "FAILED"
            attachment.ocr_status = "failed"
            attachment.error_message = f"Document processing failed: {str(e)[:150]}"

        # 9. Audit event
        try:
            AuditService.log_event(
                db=db,
                action="attachment_uploaded",
                entity_type="message_attachment",
                entity_id=attachment.id,
                user_id=current_user.id,
                details={
                    "file_name": safe_filename,
                    "mime_type": effective_mime,
                    "file_size": len(content),
                    "status": attachment.status,
                    "ocr_status": attachment.ocr_status,
                    "ocr_confidence": attachment.ocr_confidence,
                    "sha256": file_hash[:16],
                    "conversation_id": str(conv_uuid) if conv_uuid else None,
                    "conflict_id": str(conflict_uuid) if conflict_uuid else None,
                }
            )
        except Exception as ae:
            logger.warning("Failed to log attachment upload audit event: %s", str(ae))

        db.commit()

        return attachment

    @staticmethod
    def get_attachment_for_user(
        db: Session,
        attachment_id: uuid.UUID,
        current_user: User
    ) -> MessageAttachment:
        """
        Retrieves attachment verifying user ownership, expiry, and deletion status.
        """
        set_rls_context(db, current_user.id, current_user.role)

        attachment = db.query(MessageAttachment).filter(
            MessageAttachment.id == attachment_id,
            MessageAttachment.user_id == current_user.id
        ).first()

        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found or access denied.")

        if attachment.deleted_at is not None or attachment.status == "DELETED":
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Attachment has been deleted.")

        if attachment.is_temporary and attachment.expires_at and attachment.expires_at < utc_now():
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Attachment has expired.")

        return attachment

    @classmethod
    def get_attachment_file_path(
        cls,
        db: Session,
        attachment_id: uuid.UUID,
        current_user: User
    ) -> Tuple[MessageAttachment, str]:
        """
        Validates access and returns validated physical file path on disk.
        """
        attachment = cls.get_attachment_for_user(db, attachment_id, current_user)
        target_path = get_temp_attachment_path(attachment.storage_ref)

        if not target_path or not os.path.exists(target_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file not found on disk.")

        # Re-verify magic bytes before streaming
        try:
            with open(target_path, "rb") as f:
                header = f.read(16)
            valid = False
            if attachment.mime_type == "application/pdf" and header.startswith(b"%PDF-"):
                valid = True
            elif attachment.mime_type == "image/jpeg" and header.startswith(b"\xff\xd8\xff"):
                valid = True
            elif attachment.mime_type == "image/png" and header.startswith(b"\x89PNG\r\n\x1a\n"):
                valid = True

            if not valid:
                logger.error("Magic bytes mismatch for attachment %s (mime=%s)", attachment.id, attachment.mime_type)
                raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Attachment file signature invalid.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to read attachment header: %s", str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not read attachment file.")

        return attachment, target_path

    @classmethod
    def delete_attachment(
        cls,
        db: Session,
        attachment_id: uuid.UUID,
        current_user: User
    ) -> bool:
        """
        Explicit deletion endpoint: removes temporary file from disk and marks status DELETED.
        """
        set_rls_context(db, current_user.id, current_user.role)

        attachment = db.query(MessageAttachment).filter(
            MessageAttachment.id == attachment_id,
            MessageAttachment.user_id == current_user.id
        ).first()

        if not attachment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found or access denied.")

        if attachment.status == "DELETED":
            return True

        # Delete physical file from disk
        if attachment.storage_ref:
            delete_temp_attachment(attachment.storage_ref)

        attachment.status = "DELETED"
        attachment.deleted_at = utc_now()
        attachment.extracted_text = None
        attachment.extracted_fields = {"deleted": True}

        # Audit log event
        try:
            AuditService.log_event(
                db=db,
                action="attachment_deleted",
                entity_type="message_attachment",
                entity_id=attachment.id,
                user_id=current_user.id,
                details={
                    "file_name": attachment.file_name,
                    "sha256": (attachment.sha256_hash or "")[:16],
                }
            )
        except Exception as ae:
            logger.warning("Failed to log attachment deletion audit event: %s", str(ae))

        db.commit()

        return True

    @classmethod
    def link_conflict(
        cls,
        db: Session,
        attachment_id: uuid.UUID,
        conflict_id: Optional[str],
        current_user: User
    ) -> MessageAttachment:
        """
        Explicitly links or unlinks an attachment with an existing conflict.
        """
        set_rls_context(db, current_user.id, current_user.role)
        attachment = cls.get_attachment_for_user(db, attachment_id, current_user)

        if not conflict_id:
            # Unlink
            attachment.conflict_id = None
        else:
            try:
                c_uuid = uuid.UUID(conflict_id)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conflict ID format.")

            conf = db.query(Conflict).filter(
                Conflict.id == c_uuid,
                Conflict.user_id == current_user.id
            ).first()
            if not conf:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found or access denied.")

            attachment.conflict_id = c_uuid

        db.commit()
        return attachment

    @classmethod
    def cleanup_expired_attachments(cls, db: Session) -> int:
        """
        Scheduled / triggered cleanup of expired temporary chat attachments.
        Deletes files from disk, wipes extracted text, and updates status to EXPIRED.
        """
        now = utc_now()
        expired_attachments = db.query(MessageAttachment).filter(
            MessageAttachment.is_temporary == True,
            MessageAttachment.expires_at < now,
            MessageAttachment.deleted_at.is_(None),
            MessageAttachment.status != "EXPIRED"
        ).all()

        cleaned_count = 0
        for att in expired_attachments:
            try:
                if att.storage_ref:
                    delete_temp_attachment(att.storage_ref)
                att.status = "EXPIRED"
                att.deleted_at = now
                att.extracted_text = None
                att.extracted_fields = {"expired": True}
                cleaned_count += 1
            except Exception as e:
                logger.error("Error expiring attachment %s: %s", att.id, str(e))

        if cleaned_count > 0:
            db.commit()
            logger.info("Cleaned up %d expired chat attachments", cleaned_count)

        return cleaned_count
