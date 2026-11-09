import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db, set_rls_context
from app.core.storage import delete_temp_attachment
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.models.assistant import AssistantConversation, AssistantMessage, MessageAttachment
from app.models.conflict import Conflict
from app.rag.assistant.orchestrator import RAGOrchestrator
from app.services.attachment_service import AttachmentService, utc_now
from app.rag.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    ConversationUpdateRequest,
    ConversationSearchMatch,
    ConversationSearchResponse,
    MessageHistoryItem,
    MessageListResponse,
    MessageAttachmentResponse,
    AttachmentUploadResponse,
    AttachmentUpdateRequest,
    GroundedAnswer,
    ResolutionContext,
)
from app.services.resolution_context_service import ResolutionContextService

logger = logging.getLogger("convelina.assistant.router")
router = APIRouter(prefix="/api/v1/assistant", tags=["AI Resolution Assistant"])

@router.post("/chat", response_model=ChatMessageResponse)
def chat_with_assistant(
    req: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Context-aware conversational endpoint.
    Maintains citizen RLS boundary, pulls active conflict metadata if provided,
    retrieves official evidence, and generates verified guidance.
    """
    set_rls_context(db, current_user.id, current_user.role)
    orchestrator = RAGOrchestrator(db)

    try:
        conv_uuid = uuid.UUID(req.conversation_id) if req.conversation_id else None
        conflict_uuid = uuid.UUID(req.conflict_id) if req.conflict_id else None
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format")

    try:
        result = orchestrator.answer_question(
            user_id=current_user.id,
            question=req.message,
            conversation_id=conv_uuid,
            conflict_id=conflict_uuid,
            document_category=req.document_category,
            message_type=req.message_type or "chat",
            language=req.language or "en",
            attachment_ids=req.attachment_ids
        )
        return ChatMessageResponse(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            response=result["answer"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat failure for citizen %s: %s", current_user.id, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate grounded resolution guidance."
        )

@router.get("/resolution-context/{conflict_id}", response_model=ResolutionContext)
def get_resolution_context_endpoint(
    conflict_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the verified, privacy-minimized ResolutionContext for a conflict belonging to the citizen.
    Reconstructed purely server-side from database records under forced RLS.
    """
    set_rls_context(db, current_user.id, current_user.role)
    try:
        c_uuid = uuid.UUID(conflict_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conflict ID format")

    return ResolutionContextService.get_resolution_context(
        db=db,
        user_id=current_user.id,
        conflict_id=c_uuid,
        log_audit=True
    )

@router.post("/explain-conflict/{conflict_id}", response_model=ChatMessageResponse)
def explain_conflict(
    conflict_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the citizen's actual detected conflict under RLS and generates an evidence-backed explanation.
    """
    set_rls_context(db, current_user.id, current_user.role)
    try:
        c_uuid = uuid.UUID(conflict_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conflict ID")

    conflict = db.query(Conflict).filter(
        Conflict.id == c_uuid,
        Conflict.user_id == current_user.id
    ).first()
    if not conflict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found")

    prompt = (
        f"Explain why this discrepancy was detected in my {conflict.field_name}: "
        f"Document A has '{conflict.value_a}' while Document B has '{conflict.value_b}'. "
        f"What does this mismatch mean and what official procedure applies?"
    )

    try:
        orchestrator = RAGOrchestrator(db)
        result = orchestrator.answer_question(
            user_id=current_user.id,
            question=prompt,
            conflict_id=c_uuid
        )
        return ChatMessageResponse(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            response=result["answer"]
        )
    except Exception as e:
        logger.error("Failed to explain conflict %s for user %s: %s", conflict_id, current_user.id, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate grounded conflict explanation."
        )

@router.post("/resolve-conflict/{conflict_id}", response_model=ChatMessageResponse)
def resolve_conflict(
    conflict_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the citizen's actual conflict and generates step-by-step resolution instructions and official forms.
    """
    set_rls_context(db, current_user.id, current_user.role)
    try:
        c_uuid = uuid.UUID(conflict_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conflict ID")

    conflict = db.query(Conflict).filter(
        Conflict.id == c_uuid,
        Conflict.user_id == current_user.id
    ).first()
    if not conflict:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found")

    prompt = (
        f"How can I resolve the discrepancy in my {conflict.field_name}? "
        f"Provide the exact step-by-step correction procedure, required supporting documents, "
        f"and the verified official form or portal."
    )

    try:
        orchestrator = RAGOrchestrator(db)
        result = orchestrator.answer_question(
            user_id=current_user.id,
            question=prompt,
            conflict_id=c_uuid
        )
        return ChatMessageResponse(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            response=result["answer"]
        )
    except Exception as e:
        logger.error("Failed to explain conflict %s for user %s: %s", conflict_id, current_user.id, str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate grounded conflict explanation."
        )

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    req: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Explicitly initializes an assistant conversation, optionally linked to an authorized conflict."""
    set_rls_context(db, current_user.id, current_user.role)
    conflict_uuid = None
    if req.active_conflict_id:
        try:
            conflict_uuid = uuid.UUID(req.active_conflict_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conflict ID format")

        # Validate ownership of conflict
        conflict = db.query(Conflict).filter(
            Conflict.id == conflict_uuid,
            Conflict.user_id == current_user.id
        ).first()
        if not conflict:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discrepancy record not found or access denied")

    conv = AssistantConversation(
        user_id=current_user.id,
        title=req.title.strip() if (req.title and req.title.strip()) else "New Inquiry",
        active_conflict_id=conflict_uuid,
        response_language=req.response_language or "en"
    )
    db.add(conv)
    db.flush()

    try:
        from app.services.audit_service import AuditService
        AuditService.log_event(
            db=db,
            action="conversation_created",
            entity_type="conversation",
            entity_id=conv.id,
            user_id=current_user.id,
            details={
                "conflict_id": str(conflict_uuid) if conflict_uuid else None,
                "title": conv.title
            }
        )
    except Exception as e:
        logger.warning("Failed to log conversation creation audit: %s", str(e))

    res = ConversationResponse(**conv.to_dict())
    db.commit()
    return res

@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    conflict_id: Optional[str] = Query(None, description="Filter by linked conflict ID"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status")
):
    """Lists conversations belonging to the authenticated citizen, ordered by pin and updated_at."""
    set_rls_context(db, current_user.id, current_user.role)
    query = db.query(AssistantConversation).filter(
        AssistantConversation.user_id == current_user.id
    )
    if conflict_id is not None and isinstance(conflict_id, str) and conflict_id.strip():
        try:
            c_uuid = uuid.UUID(conflict_id.strip())
            query = query.filter(AssistantConversation.active_conflict_id == c_uuid)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conflict ID format")

    if is_pinned is not None and isinstance(is_pinned, bool):
        query = query.filter(AssistantConversation.is_pinned == is_pinned)
    if is_archived is not None and isinstance(is_archived, bool):
        query = query.filter(AssistantConversation.is_archived == is_archived)

    convs = query.order_by(
        AssistantConversation.is_pinned.desc(),
        AssistantConversation.updated_at.desc()
    ).all()

    return ConversationListResponse(
        total=len(convs),
        conversations=[ConversationResponse(**c.to_dict()) for c in convs]
    )

@router.get("/conversations/search", response_model=ConversationSearchResponse)
def search_conversations(
    q: str = Query(..., min_length=1, max_length=100, description="Search term for conversations or messages"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Searches conversations and message contents belonging to the authenticated citizen."""
    set_rls_context(db, current_user.id, current_user.role)
    search_pattern = f"%{q.strip()}%"

    # 1. Matching by conversation title
    convs_by_title = db.query(AssistantConversation).filter(
        AssistantConversation.user_id == current_user.id,
        AssistantConversation.title.ilike(search_pattern)
    ).all()

    # 2. Matching by message content
    matching_messages = db.query(AssistantMessage).filter(
        AssistantMessage.user_id == current_user.id,
        AssistantMessage.content.ilike(search_pattern)
    ).order_by(AssistantMessage.created_at.desc()).limit(50).all()

    # Aggregate matched conversation IDs
    conv_ids_from_messages = {m.conversation_id for m in matching_messages}
    all_conv_ids = {c.id for c in convs_by_title}.union(conv_ids_from_messages)

    all_convs = db.query(AssistantConversation).filter(
        AssistantConversation.id.in_(all_conv_ids),
        AssistantConversation.user_id == current_user.id
    ).order_by(
        AssistantConversation.is_pinned.desc(),
        AssistantConversation.updated_at.desc()
    ).all() if all_conv_ids else []

    results = []
    for c in all_convs:
        c_msgs = [m for m in matching_messages if m.conversation_id == c.id]
        results.append(
            ConversationSearchMatch(
                conversation=ConversationResponse(**c.to_dict()),
                matched_messages=[MessageHistoryItem(**m.to_dict()) for m in c_msgs]
            )
        )

    return ConversationSearchResponse(
        query=q,
        total=len(results),
        results=results
    )

@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    req: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates conversation properties: title, is_pinned, is_archived, response_language."""
    set_rls_context(db, current_user.id, current_user.role)
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conversation ID")

    conv = db.query(AssistantConversation).filter(
        AssistantConversation.id == conv_uuid,
        AssistantConversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    updated_fields = []
    if req.title is not None and req.title.strip():
        setattr(conv, "title", req.title.strip())
        updated_fields.append("title")
    if req.is_pinned is not None:
        setattr(conv, "is_pinned", req.is_pinned)
        updated_fields.append("is_pinned")
    if req.is_archived is not None:
        setattr(conv, "is_archived", req.is_archived)
        updated_fields.append("is_archived")
    if req.response_language is not None and req.response_language.strip():
        setattr(conv, "response_language", req.response_language.strip())
        updated_fields.append("response_language")
    if req.active_conflict_id is not None:
        val = req.active_conflict_id.strip()
        if not val or val.lower() == "none" or val.lower() == "null":
            setattr(conv, "active_conflict_id", None)
            updated_fields.append("active_conflict_id_removed")
        else:
            try:
                new_c_uuid = uuid.UUID(val)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conflict ID format")

            # Validate conflict ownership
            target_conflict = db.query(Conflict).filter(
                Conflict.id == new_c_uuid,
                Conflict.user_id == current_user.id
            ).first()
            if not target_conflict:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discrepancy record not found or access denied")

            setattr(conv, "active_conflict_id", new_c_uuid)
            updated_fields.append("active_conflict_id_linked")

    if updated_fields:
        try:
            from app.services.audit_service import AuditService
            AuditService.log_event(
                db=db,
                action="conversation_updated",
                entity_type="conversation",
                entity_id=conv.id,
                user_id=current_user.id,
                details={"updated_fields": updated_fields}
            )
        except Exception as e:
            logger.warning("Failed to log conversation update audit: %s", str(e))

    res = ConversationResponse(**conv.to_dict())
    db.commit()
    return res

@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all messages for a specific conversation belonging to the citizen."""
    set_rls_context(db, current_user.id, current_user.role)
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conversation ID")

    conv = db.query(AssistantConversation).filter(
        AssistantConversation.id == conv_uuid,
        AssistantConversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = db.query(AssistantMessage).filter(
        AssistantMessage.conversation_id == conv_uuid,
        AssistantMessage.user_id == current_user.id
    ).order_by(AssistantMessage.created_at.asc()).all()

    return MessageListResponse(
        total=len(messages),
        messages=[MessageHistoryItem(**m.to_dict()) for m in messages]
    )

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a conversation and its messages belonging to the authenticated citizen.
    Cleans up associated confidential temporary attachment files from disk.
    """
    set_rls_context(db, current_user.id, current_user.role)
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid conversation ID")

    conv = db.query(AssistantConversation).filter(
        AssistantConversation.id == conv_uuid,
        AssistantConversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Clean up attachment files on disk
    attachments = db.query(MessageAttachment).filter(
        MessageAttachment.conversation_id == conv_uuid
    ).all()
    for att in attachments:
        if att.storage_ref:
            delete_temp_attachment(att.storage_ref)

    db.query(MessageAttachment).filter(MessageAttachment.conversation_id == conv_uuid).delete()
    db.query(AssistantMessage).filter(AssistantMessage.conversation_id == conv_uuid).delete()
    db.delete(conv)
    db.commit()
    return None

# ===========================================================================
# Multimodal Attachments & Document Processing Endpoints (Phase P3E)
# ===========================================================================

@router.post("/attachments/upload", response_model=AttachmentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment_endpoint(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    conflict_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Secure In-Chat Multimodal Document Upload & OCR Processing Endpoint.
    - Inspects magic bytes and rejects unsupported extensions or MIME spoofing.
    - Enforces max upload size (10 MB).
    - Stores file in private temporary storage with 24h retention.
    - Runs OCR extraction and document type detection.
    - Pre-sanitizes extracted text against PII leakage.
    - Links to conversation and optional conflict under forced RLS.
    """
    attachment = await AttachmentService.upload_attachment(
        db=db,
        current_user=current_user,
        file=file,
        conversation_id=conversation_id,
        conflict_id=conflict_id,
    )
    return AttachmentUploadResponse(
        attachment=MessageAttachmentResponse(**attachment.to_dict()),
        message="Attachment uploaded and processed successfully."
    )

@router.get("/attachments/{attachment_id}", response_model=MessageAttachmentResponse)
def get_attachment_metadata_endpoint(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves metadata and OCR results for a specific attachment owned by citizen."""
    try:
        att_uuid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attachment ID format.")

    attachment = AttachmentService.get_attachment_for_user(db, att_uuid, current_user)
    return MessageAttachmentResponse(**attachment.to_dict())

@router.get("/attachments/{attachment_id}/preview")
def preview_attachment_endpoint(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Streams authenticated inline preview for citizen's uploaded document.
    Enforces user ownership, magic byte re-validation, nosniff headers, and path traversal protection.
    """
    try:
        att_uuid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attachment ID format.")

    attachment, file_path = AttachmentService.get_attachment_file_path(db, att_uuid, current_user)

    headers = {
        "X-Content-Type-Options": "nosniff",
        "Content-Disposition": f'inline; filename="{attachment.file_name}"',
        "X-Convelina-Attachment-ID": str(attachment.id),
        "X-Convelina-OCR-Status": attachment.ocr_status,
    }

    return FileResponse(
        path=file_path,
        media_type=attachment.mime_type,
        headers=headers
    )

@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment_endpoint(
    attachment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Explicitly deletes an attachment and unlinks its temporary file from disk."""
    try:
        att_uuid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attachment ID format.")

    AttachmentService.delete_attachment(db, att_uuid, current_user)
    return None

@router.patch("/attachments/{attachment_id}", response_model=MessageAttachmentResponse)
def update_attachment_association_endpoint(
    attachment_id: str,
    req: AttachmentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Links or unlinks an uploaded attachment with an existing discrepancy conflict."""
    try:
        att_uuid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid attachment ID format.")

    updated = AttachmentService.link_conflict(
        db=db,
        attachment_id=att_uuid,
        conflict_id=req.conflict_id,
        current_user=current_user
    )
    return MessageAttachmentResponse(**updated.to_dict())

@router.post("/attachments/cleanup")
def cleanup_expired_attachments_endpoint(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-only triggered cleanup for expired temporary chat attachments."""
    count = AttachmentService.cleanup_expired_attachments(db)
    return {
        "message": f"Successfully cleaned up {count} expired attachments.",
        "cleaned_count": count
    }
