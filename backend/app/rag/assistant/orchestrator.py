import logging
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.assistant import AssistantConversation, AssistantMessage, MessageAttachment
from app.models.conflict import Conflict
from app.models.document import Document
from app.core.sanitizer import sanitize_pii
from app.rag.retrieval.retriever import HybridRetriever
from app.rag.generation.llm_provider import get_llm_provider
from app.rag.schemas import GroundedAnswer, OfficialFormResponse
from app.services.form_retrieval_service import FormRetrievalService

logger = logging.getLogger("consolith.rag.orchestrator")

class RAGOrchestrator:
    """
    Context-aware RAG orchestrator:
    1. Loads authenticated user's case and conflict records under forced RLS.
    2. Builds a minimal, masked context (no unmasked raw IDs/PII).
    3. Executes hybrid retrieval against official knowledge base and forms catalog.
    4. Generates an evidence-grounded answer with zero hallucination.
    5. Persists conversational turns in PostgreSQL under citizen RLS scoping.
    """

    def __init__(self, db: Session):
        self.db = db
        self.retriever = HybridRetriever()
        self.provider = get_llm_provider()

    def _build_minimal_case_context(
        self,
        user_id: uuid.UUID,
        conflict_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Builds a privacy-minimized case context for the citizen grounded in verified
        deterministic findings from ResolutionContextService.
        """
        context: Dict[str, Any] = {
            "user_id": str(user_id),
            "conflict": None,
            "document_categories": [],
            "deterministic_findings": None,
        }

        if not conflict_id:
            return context

        from app.core.database import set_rls_context
        from app.services.resolution_context_service import ResolutionContextService
        from fastapi import HTTPException

        set_rls_context(self.db, user_id, "user")
        try:
            res_ctx = ResolutionContextService.get_resolution_context(
                db=self.db,
                user_id=user_id,
                conflict_id=conflict_id,
                log_audit=False,
            )
            context["document_categories"] = res_ctx.document_types
            context["conflict"] = res_ctx.model_dump()
            context["resolution_context"] = res_ctx.model_dump()
            context["resolution_mapping"] = res_ctx.resolution_mapping.model_dump() if res_ctx.resolution_mapping else None
            context["deterministic_findings"] = {
                "field_name": res_ctx.field_name,
                "classification": res_ctx.deterministic_classification,
                "overall_classification": res_ctx.overall_classification,
                "confidence_score": res_ctx.confidence_score,
                "requires_manual_review": res_ctx.requires_manual_review,
                "possible_causes": res_ctx.possible_causes,
                "recommended_action": res_ctx.recommended_action,
                "evidence": res_ctx.evidence,
                "ocr_quality_warning": res_ctx.ocr_quality_warning,
                "non_latin_warning": res_ctx.non_latin_warning,
                "statutory_disclaimer": res_ctx.statutory_disclaimer,
            }
        except HTTPException as he:
            logger.warning("Conflict %s could not be loaded via ResolutionContextService: %s", conflict_id, he.detail)
        except Exception as e:
            logger.error("Error building resolution context for %s: %s", conflict_id, str(e), exc_info=True)

        return context

    def answer_question(
        self,
        user_id: uuid.UUID,
        question: str,
        conversation_id: Optional[uuid.UUID] = None,
        conflict_id: Optional[uuid.UUID] = None,
        document_category: Optional[str] = None,
        message_type: Optional[str] = "chat",
        language: Optional[str] = None,
        attachment_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline for citizen conversation with pre-persistence PII sanitization.
        """
        # 0. Pre-sanitize question to prevent raw PII in database, prompts, and logs
        clean_question, was_redacted, pii_summary = sanitize_pii(question)

        # 1. Resolve or create conversation
        conversation = None
        if conversation_id:
            conversation = self.db.query(AssistantConversation).filter(
                AssistantConversation.id == conversation_id,
                AssistantConversation.user_id == user_id
            ).first()

        if not conversation:
            conv_title = clean_question[:50] + ("..." if len(clean_question) > 50 else "")
            conversation = AssistantConversation(
                user_id=user_id,
                title=conv_title,
                active_case_id=None,
                active_conflict_id=conflict_id,
                response_language=language or "en"
            )
            self.db.add(conversation)
            self.db.flush()
        else:
            if conflict_id and not getattr(conversation, "active_conflict_id", None):
                setattr(conversation, "active_conflict_id", conflict_id)
                self.db.flush()
            if language and getattr(conversation, "response_language", None) != language:
                setattr(conversation, "response_language", language)
                self.db.flush()

        active_conflict_id: Optional[uuid.UUID] = conflict_id
        if not active_conflict_id:
            raw_cid = getattr(conversation, "active_conflict_id", None)
            if raw_cid:
                active_conflict_id = uuid.UUID(str(raw_cid))

        # 2. Build minimal case context
        case_context = self._build_minimal_case_context(user_id, active_conflict_id)

        # Resolve attachments if attachment_ids provided
        attachments = []
        if attachment_ids:
            parsed_ids = []
            for a in attachment_ids:
                try:
                    parsed_ids.append(uuid.UUID(str(a)))
                except (ValueError, TypeError):
                    pass
            if parsed_ids:
                attachments = self.db.query(MessageAttachment).filter(
                    MessageAttachment.id.in_(parsed_ids),
                    MessageAttachment.user_id == user_id,
                    MessageAttachment.deleted_at.is_(None)
                ).all()

        attachment_contexts = []
        for att in attachments:
            attachment_contexts.append({
                "id": str(att.id),
                "file_name": att.file_name,
                "mime_type": att.mime_type,
                "status": att.status,
                "ocr_status": att.ocr_status,
                "ocr_confidence": float(att.ocr_confidence) if att.ocr_confidence is not None else None,
                "detected_type": (att.extracted_fields or {}).get("document_type_indicator", "supporting_document"),
                "dates_found": (att.extracted_fields or {}).get("dates_found", []),
                "rejection_reasons": (att.extracted_fields or {}).get("rejection_reasons", []),
                "masked_identifiers": (att.extracted_fields or {}).get("masked_identifiers", {}),
                "extracted_text": att.extracted_text or "",
            })

        case_context["attachments"] = attachment_contexts
        case_context["language"] = language or getattr(conversation, "response_language", "en")

        # Log resolution guidance audit event if active discrepancy is addressed
        if active_conflict_id:
            try:
                from app.services.audit_service import AuditService
                AuditService.log_event(
                    db=self.db,
                    action="resolution_guidance_requested",
                    entity_type="conflict_resolution",
                    entity_id=active_conflict_id,
                    user_id=user_id,
                    details={
                        "conflict_id": str(active_conflict_id),
                        "conversation_id": str(conversation.id),
                        "is_grounded": bool(case_context.get("deterministic_findings")),
                    },
                )
            except Exception as e:
                logger.error("Audit logging failed for resolution guidance request: %s", str(e))

        # 3. Determine search categories
        inferred_category = document_category
        if not inferred_category and case_context.get("resolution_mapping"):
            inferred_category = case_context["resolution_mapping"].get("target_document_category")
        if not inferred_category and case_context.get("document_categories"):
            inferred_category = case_context["document_categories"][0]

        # 4. Load recent conversation history (max 6 messages)
        history_msgs = self.db.query(AssistantMessage).filter(
            AssistantMessage.conversation_id == conversation.id,
            AssistantMessage.user_id == user_id
        ).order_by(AssistantMessage.created_at.asc()).limit(6).all()

        conversation_history: List[Dict[str, str]] = [
            {"role": str(m.role), "content": str(m.content)}
            for m in history_msgs
        ]

        # 5. Hybrid Retrieval from Qdrant Knowledge & Deterministic Forms Repository
        retrieved_chunks = self.retriever.retrieve(
            query=clean_question,
            document_category=inferred_category,
            top_k=5
        )

        form_retrieval_res = FormRetrievalService.retrieve_applicable_forms(
            db=self.db,
            query=clean_question,
            document_category=inferred_category,
            issue_type=case_context.get("field_name"),
            conflict_context=case_context,
            top_k=4
        )
        relevant_forms_payload = [f.model_dump() for f in form_retrieval_res.forms]

        # 6. Generate Grounded Answer
        grounded_answer: GroundedAnswer = self.provider.generate_answer(
            question=clean_question,
            case_context=case_context,
            retrieved_chunks=retrieved_chunks,
            relevant_forms=relevant_forms_payload,
            conversation_history=conversation_history
        )

        # Enforce verified forms and no_verified_form_available flag
        if form_retrieval_res.forms:
            grounded_answer.relevant_forms = form_retrieval_res.forms
        if form_retrieval_res.no_verified_form_available:
            grounded_answer.no_verified_form_available = True
            notice_text = (
                f"\n\n> ⚠️ **Statutory Notice:** No verified official government form is currently registered "
                f"in the repository for this specific category or correction requirement. "
                f"Please consult the {form_retrieval_res.suggested_authority or 'competent authority'} portal directly."
            )
            if "no verified" not in grounded_answer.answer.lower():
                grounded_answer.answer += notice_text

        # 7. Persist turn in PostgreSQL with sanitized content and message_type
        user_msg = AssistantMessage(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            user_id=user_id,
            role="user",
            content=clean_question,
            message_type=message_type or "chat"
        )
        self.db.add(user_msg)
        self.db.flush()

        # Link attachments to user message and conversation
        for att in attachments:
            att.message_id = user_msg.id
            att.conversation_id = conversation.id

        if was_redacted:
            try:
                from app.services.audit_service import AuditService
                AuditService.log_event(
                    db=self.db,
                    action="pii_masked_in_chat",
                    entity_type="chat_message",
                    entity_id=user_msg.id,
                    user_id=user_id,
                    details=pii_summary
                )
            except Exception as e:
                logger.warning("Failed to log PII redaction audit event: %s", str(e))

        assistant_msg_id = uuid.uuid4()
        assistant_msg = AssistantMessage(
            id=assistant_msg_id,
            conversation_id=conversation.id,
            user_id=user_id,
            role="assistant",
            content=grounded_answer.answer,
            message_type=message_type or "chat",
            structured_response=grounded_answer.model_dump(),
            citations=[c.model_dump() for c in grounded_answer.citations],
            tokens_used=0
        )
        self.db.add(assistant_msg)
        
        # Save IDs before committing so subsequent access doesn't trigger expired attribute load
        saved_conv_id = str(conversation.id)
        saved_msg_id = str(assistant_msg_id)

        self.db.commit()

        return {
            "conversation_id": saved_conv_id,
            "message_id": saved_msg_id,
            "answer": grounded_answer
        }
