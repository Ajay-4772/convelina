import logging
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.conflict import Conflict
from app.models.document import Document
from app.rag.retrieval.retriever import HybridRetriever
from app.rag.generation.llm_provider import get_llm_provider
from app.rag.schemas import GroundedAnswer, OfficialFormResponse

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
        document_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline for citizen conversation.
        """
        # 1. Resolve or create conversation
        conversation = None
        if conversation_id:
            conversation = self.db.query(AssistantConversation).filter(
                AssistantConversation.id == conversation_id,
                AssistantConversation.user_id == user_id
            ).first()

        if not conversation:
            conv_title = question[:50] + ("..." if len(question) > 50 else "")
            conversation = AssistantConversation(
                user_id=user_id,
                title=conv_title,
                active_case_id=None,
                active_conflict_id=conflict_id
            )
            self.db.add(conversation)
            self.db.flush()
        else:
            if conflict_id and not getattr(conversation, "active_conflict_id", None):
                setattr(conversation, "active_conflict_id", conflict_id)
                self.db.flush()

        active_conflict_id: Optional[uuid.UUID] = conflict_id
        if not active_conflict_id:
            raw_cid = getattr(conversation, "active_conflict_id", None)
            if raw_cid:
                active_conflict_id = uuid.UUID(str(raw_cid))

        # 2. Build minimal case context
        case_context = self._build_minimal_case_context(user_id, active_conflict_id)

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

        # 5. Hybrid Retrieval from Qdrant
        retrieved_chunks = self.retriever.retrieve(
            query=question,
            document_category=inferred_category,
            top_k=5
        )

        relevant_forms = self.retriever.retrieve_forms(
            query=question,
            document_category=inferred_category,
            top_k=3
        )

        # 6. Generate Grounded Answer
        grounded_answer: GroundedAnswer = self.provider.generate_answer(
            question=question,
            case_context=case_context,
            retrieved_chunks=retrieved_chunks,
            relevant_forms=relevant_forms,
            conversation_history=conversation_history
        )

        # 7. Persist turn in PostgreSQL
        user_msg = AssistantMessage(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            user_id=user_id,
            role="user",
            content=question
        )
        self.db.add(user_msg)

        assistant_msg_id = uuid.uuid4()
        assistant_msg = AssistantMessage(
            id=assistant_msg_id,
            conversation_id=conversation.id,
            user_id=user_id,
            role="assistant",
            content=grounded_answer.answer,
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
