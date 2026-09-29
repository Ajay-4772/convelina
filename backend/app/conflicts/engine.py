import re
import logging
from typing import List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models.document import Document
from app.models.conflict import Conflict
from app.conflicts.rules import evaluate_document_pair

logger = logging.getLogger("consolith.conflicts.engine")

AADHAAR_REGEX = re.compile(r'\b\d{4}\s?\d{4}\s?(\d{4})\b')

def mask_sensitive_content(text_val: Any) -> str:
    """
    Defense-in-depth masking to ensure no raw 12-digit Aadhaar numbers ever persist
    or leak into conflict logs, values, or explanations.
    """
    if text_val is None:
        return ""
    s = str(text_val)
    return AADHAAR_REGEX.sub(r'XXXX-XXXX-\1', s)


class ConflictDetectionEngine:
    """
    Deterministic, explainable, and secure Conflict Detection Engine.
    Executes pairwise cross-document evaluations under authenticated citizen RLS scope.
    """

    def __init__(self, db: Session):
        self.db = db

    def run_detection_for_user(self, user_id: UUID) -> Dict[str, Any]:
        """
        Runs comprehensive conflict detection across all completed documents for user_id.
        Enforces canonical pair ordering (doc_a_id < doc_b_id) and idempotent upserts.
        """
        # 1. Fetch all completed documents belonging to this user
        docs: List[Document] = (
            self.db.query(Document)
            .filter(Document.user_id == user_id, Document.ocr_status == "completed")
            .order_by(Document.created_at.asc())
            .all()
        )

        total_docs = len(docs)
        if total_docs < 2:
            existing_conflicts = (
                self.db.query(Conflict)
                .filter(Conflict.user_id == user_id)
                .order_by(Conflict.created_at.desc())
                .all()
            )
            return {
                "total_documents_analyzed": total_docs,
                "total_conflicts_detected": len(existing_conflicts),
                "new_conflicts_created": 0,
                "conflicts": [c.to_dict() for c in existing_conflicts],
                "message": (
                    "At least 2 processed documents are required to detect cross-document conflicts."
                    if total_docs < 2
                    else "Analysis completed."
                ),
            }

        # 2. Pairwise evaluation with canonical ordering (doc_a_id < doc_b_id)
        new_conflicts_count = 0
        detected_items = []

        for i in range(total_docs):
            for j in range(i + 1, total_docs):
                doc_1 = docs[i]
                doc_2 = docs[j]

                # Canonical ordering by UUID string representation
                if str(doc_1.id) < str(doc_2.id):
                    doc_a, doc_b = doc_1, doc_2
                else:
                    doc_a, doc_b = doc_2, doc_1

                dict_a = {
                    "id": str(doc_a.id),
                    "document_type": doc_a.document_type,
                    "masked_id": doc_a.masked_id,
                    "extracted_fields": doc_a.extracted_fields or {},
                }
                dict_b = {
                    "id": str(doc_b.id),
                    "document_type": doc_b.document_type,
                    "masked_id": doc_b.masked_id,
                    "extracted_fields": doc_b.extracted_fields or {},
                }

                pair_conflicts = evaluate_document_pair(dict_a, dict_b)
                for item in pair_conflicts:
                    detected_items.append((doc_a, doc_b, item))

        # 3. Idempotent upsert into conflicts table
        for doc_a, doc_b, item in detected_items:
            field_name = item["field_name"]
            val_a = mask_sensitive_content(item["value_a"])
            val_b = mask_sensitive_content(item["value_b"])
            explanation = mask_sensitive_content(item["description"])
            conflict_type = item["conflict_type"]
            severity = item["severity"]
            comp_method = item.get("comparison_method", "exact")
            sim_score = item.get("similarity_score")

            # Check for existing record
            existing = (
                self.db.query(Conflict)
                .filter(
                    Conflict.user_id == user_id,
                    Conflict.doc_a_id == doc_a.id,
                    Conflict.doc_b_id == doc_b.id,
                    Conflict.field_name == field_name,
                )
                .first()
            )

            if existing:
                # Update comparison data while preserving review status if already changed by user
                existing.value_a = val_a
                existing.value_b = val_b
                existing.description = explanation
                existing.conflict_type = conflict_type
                existing.severity = severity
                existing.comparison_method = comp_method
                existing.similarity_score = sim_score
            else:
                new_conflict = Conflict(
                    user_id=user_id,
                    doc_a_id=doc_a.id,
                    doc_b_id=doc_b.id,
                    conflict_type=conflict_type,
                    severity=severity,
                    field_name=field_name,
                    value_a=val_a,
                    value_b=val_b,
                    description=explanation,
                    status="detected",
                    comparison_method=comp_method,
                    similarity_score=sim_score,
                )
                self.db.add(new_conflict)
                new_conflicts_count += 1

        self.db.flush()

        # 4. Fetch all active conflicts for user
        all_conflicts = (
            self.db.query(Conflict)
            .filter(Conflict.user_id == user_id)
            .order_by(Conflict.created_at.desc())
            .all()
        )

        return {
            "total_documents_analyzed": total_docs,
            "total_conflicts_detected": len(all_conflicts),
            "new_conflicts_created": new_conflicts_count,
            "conflicts": [c.to_dict() for c in all_conflicts],
            "message": f"Analyzed {total_docs} documents across {len(detected_items)} potential discrepancies. {new_conflicts_count} new conflict records created.",
        }
