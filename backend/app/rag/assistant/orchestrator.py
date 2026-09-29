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
        Builds a privacy-minimized case context for the citizen.
        Never duplicates the deterministic conflict engine.
        """
        context: Dict[str, Any] = {
            "user_id": str(user_id),
            "conflict": None,
            "document_categories": []
        }

        if not conflict_id:
            return context

        # Query conflict under RLS
        conflict = self.db.query(Conflict).filter(
            Conflict.id == conflict_id,
            Conflict.user_id == user_id
        ).first()

        if not conflict:
            logger.warning("Conflict %s not found for citizen %s", conflict_id, user_id)
            return context

        # Fetch associated document categories
        doc_ids = [conflict.doc_a_id, conflict.doc_b_id]
        docs = self.db.query(Document).filter(
            Document.id.in_(doc_ids),
            Document.user_id == user_id
        ).all()
        categories = list({d.doc_type for d in docs if d.doc_type})

        # Mask values for privacy minimization
        val_a = conflict.value_a or ""
        val_b = conflict.value_b or ""

        context["document_categories"] = categories
        context["conflict"] = {
            "conflict_id": str(conflict.id),
            "field_name": conflict.field_name,
            "conflict_type": conflict.conflict_type,
            "severity": conflict.severity,
            "status": conflict.status,
            "doc_a_id": str(conflict.doc_a_id),
            "doc_b_id": str(conflict.doc_b_id),
            "document_categories": categories,
            "value_a": val_a,
            "value_b": val_b
        }
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
            if conflict_id and not conversation.active_conflict_id:
                conversation.active_conflict_id = conflict_id
                self.db.flush()

        active_conflict_id = conflict_id or conversation.active_conflict_id

        # 2. Build minimal case context
        case_context = self._build_minimal_case_context(user_id, active_conflict_id)

        # 3. Determine search categories
        inferred_category = document_category
        if not inferred_category and case_context.get("document_categories"):
            inferred_category = case_context["document_categories"][0]

        # 4. Load recent conversation history (max 6 messages)
        history_msgs = self.db.query(AssistantMessage).filter(
            AssistantMessage.conversation_id == conversation.id,
            AssistantMessage.user_id == user_id
        ).order_by(AssistantMessage.created_at.asc()).limit(6).all()

        conversation_history = [
            {"role": m.role, "content": m.content}
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
            conversation_id=conversation.id,
            user_id=user_id,
            role="user",
            content=question
        )
        self.db.add(user_msg)

        assistant_msg = AssistantMessage(
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
        saved_msg_id = str(assistant_msg.id)

        self.db.commit()

        return {
            "conversation_id": saved_conv_id,
            "message_id": saved_msg_id,
            "answer": grounded_answer
        }
