import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db, set_rls_context
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.conflict import Conflict
from app.rag.assistant.orchestrator import RAGOrchestrator
from app.rag.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationResponse,
    ConversationListResponse,
    MessageHistoryItem,
    MessageListResponse,
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
            document_category=req.document_category
        )
        return ChatMessageResponse(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            response=result["answer"]
        )
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

@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists conversations belonging to the authenticated citizen."""
    set_rls_context(db, current_user.id, current_user.role)
    convs = db.query(AssistantConversation).filter(
        AssistantConversation.user_id == current_user.id
    ).order_by(AssistantConversation.updated_at.desc()).all()

    return ConversationListResponse(
        total=len(convs),
        conversations=[ConversationResponse(**c.to_dict()) for c in convs]
    )

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
    """Deletes a conversation and its messages belonging to the authenticated citizen."""
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

    db.query(AssistantMessage).filter(AssistantMessage.conversation_id == conv_uuid).delete()
    db.delete(conv)
    db.commit()
    return None
