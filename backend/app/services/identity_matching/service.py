"""
CONVELINA - Document Comparison & Conflict Persistence Service (Phase P1)
Integrates canonical DocumentIdentityProfile extraction, deterministic P0 comparison,
tamper-evident audit logging, and idempotent conflict persistence under PostgreSQL RLS.
"""

import logging
from typing import List, Dict, Any, Tuple
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.conflict import Conflict
from app.services.audit_service import AuditService
from app.services.identity_matching.classification import (
    NameMatchClassification,
    OverallIdentityClassification,
    ConflictSeverity,
)
from app.services.identity_matching.models import (
    DocumentIdentityProfile,
    FieldMatchResult,
    IdentityComparisonResult,
)
from app.services.identity_matching.engine import IdentityComparisonEngine
from app.conflicts.schemas import (
    DocumentCompareResponse,
    DocumentMetadataSummary,
)
from app.conflicts.engine import mask_sensitive_content

logger = logging.getLogger("convelina.conflicts.service")


def map_p0_classification_to_conflict_db(field_res: FieldMatchResult) -> Tuple[str, str]:
    """
    Deterministically maps granular P0 classification into the database
    check-constraint valid conflict_type and severity.
    Database check constraints:
      conflict_type: ['format-only', 'genuine-mismatch', 'unresolvable-needs-evidence']
      severity: ['low', 'medium', 'high', 'critical']
    """
    cls_name = field_res.classification

    if cls_name in (
        NameMatchClassification.MISMATCH,
        NameMatchClassification.GENDER_AWARE_SIMILAR_NAME,
    ):
        return "genuine-mismatch", "critical"

    if cls_name in (
        NameMatchClassification.FORMAT_ONLY_MATCH,
        NameMatchClassification.TRANSLITERATION_OR_VARIANT,
    ):
        return "format-only", "low"

    if cls_name == NameMatchClassification.TOKEN_ORDER_VARIATION:
        return "format-only", "low"

    if cls_name == NameMatchClassification.INITIAL_AMBIGUITY:
        return "unresolvable-needs-evidence", "medium"

    if cls_name == NameMatchClassification.TRUNCATION_OR_PARTIAL_MATCH:
        return "unresolvable-needs-evidence", "medium"

    if cls_name == NameMatchClassification.LOW_CONFIDENCE_NEEDS_REVIEW:
        return "unresolvable-needs-evidence", "medium"

    if cls_name == NameMatchClassification.UNRESOLVABLE_NEEDS_MANUAL_REVIEW:
        return "unresolvable-needs-evidence", "high"

    if field_res.is_conflict:
        return "unresolvable-needs-evidence", field_res.severity or "medium"

    return "format-only", "low"


class DocumentComparisonService:
    """
    Phase P1 Document Comparison Service.
    Coordinates document ownership validation, canonical profile extraction,
    multi-field P0 engine execution, audit logging, and idempotent conflict storage.
    """

    @classmethod
    def create_profile_from_document(cls, doc: Document) -> DocumentIdentityProfile:
        """Derives a canonical DocumentIdentityProfile directly from Document record."""
        extracted = doc.extracted_fields or {}
        ocr_conf = float(extracted.get("overall_ocr_confidence", 1.0))

        return DocumentIdentityProfile.from_extracted_fields(
            document_id=str(doc.id),
            document_type=doc.document_type,
            extracted_fields=extracted,
            overall_ocr_confidence=ocr_conf,
            source_ref=doc.masked_id,
        )

    @classmethod
    def compare_documents_for_user(
        cls,
        db: Session,
        user_id: UUID,
        document_ids: List[UUID],
    ) -> DocumentCompareResponse:
        """
        Executes comparison across specified documents for user_id.
        Enforces:
        - Authenticated ownership of every document.
        - Document readiness check (OCR completed).
        - Multi-field deterministic P0 evaluation.
        - Idempotent upsert into conflicts table.
        - Cryptographic audit event logging.
        """
        # 1. Fetch requested documents under caller's RLS context
        docs: List[Document] = (
            db.query(Document)
            .filter(Document.id.in_(document_ids))
            .all()
        )

        doc_map = {d.id: d for d in docs}

        # 2. Strict Ownership & Existence Verification
        for req_id in document_ids:
            if req_id not in doc_map:
                logger.warning(
                    "Security alert: User %s attempted to compare missing/unauthorized document %s",
                    user_id,
                    req_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document '{req_id}' not found or access denied.",
                )
            doc = doc_map[req_id]
            if doc.user_id != user_id:
                logger.warning(
                    "Security violation: User %s attempted cross-tenant comparison of document %s belonging to user %s",
                    user_id,
                    req_id,
                    doc.user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Cannot compare documents belonging to another user.",
                )

        # 3. Document Readiness Check
        for doc in docs:
            if doc.ocr_status != "completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document '{doc.id}' ({doc.document_type}) is not ready for comparison. Current OCR status: '{doc.ocr_status}'.",
                )

        # Maintain request order
        ordered_docs = [doc_map[req_id] for req_id in document_ids]

        # 4. Generate Canonical Profiles
        profiles = [cls.create_profile_from_document(d) for d in ordered_docs]

        # 5. Execute Deterministic P0 Comparison
        # For pair: direct evaluation
        # For >2 docs: pairwise evaluation + holistic synthesis
        new_conflicts_created = 0
        total_discrepancies = 0

        if len(profiles) == 2:
            comparison_result = IdentityComparisonEngine.compare_profiles(profiles[0], profiles[1])
            pairwise_evals = [(ordered_docs[0], ordered_docs[1], comparison_result)]
        else:
            # Multi-document comparison: evaluate all distinct pairs
            pairwise_evals = []
            worst_overall = OverallIdentityClassification.EXACT_MATCH
            combined_matched: set = set()
            combined_conflicts: set = set()
            combined_ambiguous: set = set()
            combined_evidence: List[str] = []
            combined_warnings: List[str] = []
            min_conf = 1.0

            # Priority order for worst-case synthesis
            severity_order = [
                OverallIdentityClassification.HIGH_RISK_GENUINE_MISMATCH,
                OverallIdentityClassification.MISMATCH,
                OverallIdentityClassification.UNRESOLVABLE_NEEDS_MANUAL_REVIEW,
                OverallIdentityClassification.LOW_CONFIDENCE_NEEDS_REVIEW,
                OverallIdentityClassification.AMBIGUOUS_NEEDS_REVIEW,
                OverallIdentityClassification.TRUNCATION_OR_PARTIAL_MATCH,
                OverallIdentityClassification.LIKELY_SAME_PERSON,
                OverallIdentityClassification.FORMAT_ONLY_MATCH,
                OverallIdentityClassification.EXACT_MATCH,
            ]

            for i in range(len(profiles)):
                for j in range(i + 1, len(profiles)):
                    pair_res = IdentityComparisonEngine.compare_profiles(profiles[i], profiles[j])
                    pairwise_evals.append((ordered_docs[i], ordered_docs[j], pair_res))
                    combined_matched.update(pair_res.matched_fields)
                    combined_conflicts.update(pair_res.conflicting_fields)
                    combined_ambiguous.update(pair_res.ambiguous_fields)
                    combined_evidence.extend(pair_res.evidence)
                    combined_warnings.extend(pair_res.warnings)
                    min_conf = min(min_conf, pair_res.confidence_score)

                    # Update worst overall classification
                    if severity_order.index(pair_res.overall_classification) < severity_order.index(worst_overall):
                        worst_overall = pair_res.overall_classification

            # Synthesize overall result
            comparison_result = IdentityComparisonResult(
                overall_classification=worst_overall,
                confidence_score=min_conf,
                requires_manual_review=(
                    worst_overall not in (
                        OverallIdentityClassification.EXACT_MATCH,
                        OverallIdentityClassification.FORMAT_ONLY_MATCH,
                        OverallIdentityClassification.LIKELY_SAME_PERSON,
                    )
                ),
                matched_fields=sorted(list(combined_matched)),
                conflicting_fields=sorted(list(combined_conflicts)),
                ambiguous_fields=sorted(list(combined_ambiguous)),
                field_results=pairwise_evals[0][2].field_results,  # Reference field results from primary pair
                evidence=list(dict.fromkeys(combined_evidence)),
                explanation=f"Evaluated {len(ordered_docs)} documents across {len(pairwise_evals)} pairs. Overall status: {worst_overall.value}.",
                warnings=list(dict.fromkeys(combined_warnings)),
            )

        # 6. Idempotent Conflict Persistence in Database
        for d_1, d_2, pair_res in pairwise_evals:
            # Canonical ordering by UUID string
            if str(d_1.id) < str(d_2.id):
                doc_a, doc_b = d_1, d_2
            else:
                doc_a, doc_b = d_2, d_1

            for field_name, field_res in pair_res.field_results.items():
                if not field_res.is_conflict:
                    continue

                total_discrepancies += 1
                db_conflict_type, db_severity = map_p0_classification_to_conflict_db(field_res)
                val_a = mask_sensitive_content(field_res.value_a_raw or "")
                val_b = mask_sensitive_content(field_res.value_b_raw or "")
                desc = mask_sensitive_content(field_res.explanation)
                sim_score = round(field_res.similarity_score * 100.0, 2)

                meta_payload = {
                    "classification": field_res.classification,
                    "confidence_score": field_res.confidence_score,
                    "requires_manual_review": field_res.requires_manual_review,
                    "possible_causes": field_res.possible_causes,
                    "recommended_action": field_res.recommended_action,
                    "overall_classification": pair_res.overall_classification,
                    "evidence": pair_res.evidence,
                }

                existing = (
                    db.query(Conflict)
                    .filter(
                        Conflict.user_id == user_id,
                        Conflict.doc_a_id == doc_a.id,
                        Conflict.doc_b_id == doc_b.id,
                        Conflict.field_name == field_name,
                    )
                    .first()
                )

                if existing:
                    existing.value_a = val_a
                    existing.value_b = val_b
                    existing.description = desc
                    existing.conflict_type = db_conflict_type
                    existing.severity = db_severity
                    existing.comparison_method = "deterministic_p0_engine"
                    existing.similarity_score = sim_score
                    existing.metadata_ = meta_payload
                else:
                    new_conf = Conflict(
                        user_id=user_id,
                        doc_a_id=doc_a.id,
                        doc_b_id=doc_b.id,
                        conflict_type=db_conflict_type,
                        severity=db_severity,
                        field_name=field_name,
                        value_a=val_a,
                        value_b=val_b,
                        description=desc,
                        status="detected",
                        comparison_method="deterministic_p0_engine",
                        similarity_score=sim_score,
                        metadata_=meta_payload,
                    )
                    db.add(new_conf)
                    new_conflicts_created += 1

        db.flush()

        # 7. Cryptographic Audit Event Logging
        try:
            AuditService.log_event(
                db=db,
                action="document_comparison_executed",
                entity_type="document_comparison",
                entity_id=ordered_docs[0].id,
                user_id=user_id,
                details={
                    "document_ids": [str(d.id) for d in ordered_docs],
                    "document_types": [d.document_type for d in ordered_docs],
                    "overall_classification": comparison_result.overall_classification,
                    "requires_manual_review": comparison_result.requires_manual_review,
                    "matched_fields": comparison_result.matched_fields,
                    "conflicting_fields": comparison_result.conflicting_fields,
                    "ambiguous_fields": comparison_result.ambiguous_fields,
                },
            )
            db.flush()
        except Exception as audit_err:
            logger.warning("Audit logging non-fatal failure: %s", str(audit_err))

        db.commit()

        # 8. Build and Return Structured Response
        action_needed = comparison_result.requires_manual_review or (
            comparison_result.overall_classification in (
                OverallIdentityClassification.MISMATCH,
                OverallIdentityClassification.HIGH_RISK_GENUINE_MISMATCH,
                OverallIdentityClassification.AMBIGUOUS_NEEDS_REVIEW,
                OverallIdentityClassification.LOW_CONFIDENCE_NEEDS_REVIEW,
                OverallIdentityClassification.UNRESOLVABLE_NEEDS_MANUAL_REVIEW,
            )
        )

        doc_summaries = [
            DocumentMetadataSummary(
                id=str(d.id),
                document_type=d.document_type,
                masked_id=d.masked_id,
                ocr_status=d.ocr_status,
                created_at=d.created_at.isoformat() if d.created_at else "",
            )
            for d in ordered_docs
        ]

        return DocumentCompareResponse(
            overall_classification=comparison_result.overall_classification,
            confidence_score=round(comparison_result.confidence_score, 2),
            requires_manual_review=comparison_result.requires_manual_review,
            action_recommended=action_needed,
            matched_fields=comparison_result.matched_fields,
            conflicting_fields=comparison_result.conflicting_fields,
            ambiguous_fields=comparison_result.ambiguous_fields,
            field_results={k: v.to_dict() for k, v in comparison_result.field_results.items()},
            evidence=comparison_result.evidence,
            explanation=comparison_result.explanation,
            warnings=comparison_result.warnings,
            documents_compared=doc_summaries,
            discrepancies_count=total_discrepancies,
            conflicts_created=new_conflicts_created,
        )

