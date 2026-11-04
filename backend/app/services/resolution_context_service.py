"""
CONVELINA - Resolution Context Service (Phase P2A)
Server-side reconstruction of verified discrepancy context for RAG and AI Assistant.
Enforces strict user ownership, PostgreSQL RLS boundaries, privacy minimization,
OCR quality evaluation, and tamper-evident audit logging.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import set_rls_context
from app.models.conflict import Conflict
from app.models.document import Document
from app.rag.schemas import ResolutionContext
from app.conflicts.engine import mask_sensitive_content
from app.services.audit_service import AuditService
from app.services.resolution_mapping_service import ResolutionMappingService

logger = logging.getLogger("convelina.resolution_context")


class ResolutionContextService:
    """
    Constructs a verified, server-side ResolutionContext for a detected conflict.
    Never trusts client-provided diagnosis, classification, or identity data.
    """

    @classmethod
    def get_resolution_context(
        cls,
        db: Session,
        user_id: UUID,
        conflict_id: UUID,
        log_audit: bool = True,
    ) -> ResolutionContext:
        """
        Loads the requested conflict and associated documents under authenticated user scope.
        Validates ownership, derives OCR quality flags, and constructs a strongly typed
        ResolutionContext.
        """
        # Ensure RLS tenant isolation context is armed for this transaction
        set_rls_context(db, user_id, "user")

        # 1. Query conflict under caller's tenant scope
        conflict = (
            db.query(Conflict)
            .filter(Conflict.id == conflict_id)
            .first()
        )

        if not conflict:
            logger.warning("Resolution context query failed: Conflict %s not found", conflict_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discrepancy record not found.",
            )

        # Enforce strict ownership
        if conflict.user_id != user_id:
            logger.warning(
                "Security alert: User %s attempted cross-tenant access to conflict %s belonging to %s",
                user_id,
                conflict_id,
                conflict.user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access discrepancy record belonging to another user.",
            )

        # 2. Query and validate associated documents
        doc_ids = [conflict.doc_a_id, conflict.doc_b_id]
        docs = (
            db.query(Document)
            .filter(Document.id.in_(doc_ids))
            .all()
        )
        doc_map = {d.id: d for d in docs}

        for d_id in doc_ids:
            if d_id not in doc_map:
                logger.warning("Associated document %s missing for conflict %s", d_id, conflict_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Associated document '{d_id}' not found.",
                )
            if doc_map[d_id].user_id != user_id:
                logger.warning(
                    "Security alert: Document %s belongs to another user %s",
                    d_id,
                    doc_map[d_id].user_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Document belongs to another user.",
                )

        doc_a = doc_map[conflict.doc_a_id]
        doc_b = doc_map[conflict.doc_b_id]
        doc_types = [doc_a.document_type, doc_b.document_type]

        # 3. OCR Quality and Script Verification
        ocr_quality_warning: Optional[str] = None
        non_latin_warning: Optional[str] = None

        extracted_a = doc_a.extracted_fields or {}
        extracted_b = doc_b.extracted_fields or {}

        def _get_ocr_conf(extr: Dict[str, Any]) -> float:
            for k in ("overall_ocr_confidence", "ocr_confidence", "confidence"):
                if k in extr and extr[k] is not None:
                    try:
                        return float(extr[k])
                    except (ValueError, TypeError):
                        pass
            return 1.0

        ocr_a = _get_ocr_conf(extracted_a)
        ocr_b = _get_ocr_conf(extracted_b)
        min_ocr = min(ocr_a, ocr_b)

        meta = conflict.metadata_ or {}
        det_cls = meta.get("classification") or conflict.conflict_type
        overall_cls = meta.get("overall_classification") or conflict.conflict_type

        if min_ocr < 0.60 or det_cls == "LOW_CONFIDENCE_NEEDS_REVIEW" or overall_cls == "LOW_CONFIDENCE_NEEDS_REVIEW":
            ocr_quality_warning = (
                f"One or more documents had OCR confidence below 60% (detected: {round(min_ocr * 100)}%). "
                "Some extracted information could not be verified with high certainty. "
                "Manual review of document scan is strongly recommended."
            )

        if (
            extracted_a.get("non_latin_detected")
            or extracted_b.get("non_latin_detected")
            or det_cls == "UNRESOLVABLE_NON_LATIN_SCRIPT"
        ):
            non_latin_warning = (
                "Non-Latin or Indic regional script detected in source document. "
                "Transliteration could not be deterministically confirmed without certified translation."
            )

        # 4. Extract and normalize deterministic metadata
        raw_conf_score = meta.get("confidence_score")
        if raw_conf_score is not None:
            confidence_score = float(raw_conf_score)
        elif conflict.similarity_score is not None:
            confidence_score = float(conflict.similarity_score) / 100.0
        else:
            confidence_score = 0.70

        req_manual = meta.get("requires_manual_review")
        if req_manual is None:
            req_manual = conflict.severity in ("high", "critical") or conflict.conflict_type == "unresolvable-needs-evidence"

        possible_causes = meta.get("possible_causes") or []
        if not possible_causes and conflict.description:
            possible_causes = [conflict.description]

        recommended_action = meta.get("recommended_action")
        evidence = meta.get("evidence") or []

        # 5. Privacy minimization: Mask sensitive values
        val_a_masked = mask_sensitive_content(conflict.value_a or "")
        val_b_masked = mask_sensitive_content(conflict.value_b or "")

        # 6. Deterministic Statutory Resolution Mapping (Phase P2B)
        resolution_mapping = ResolutionMappingService.map_conflict(
            field_name=conflict.field_name,
            deterministic_classification=str(det_cls),
            document_types=doc_types,
            ocr_quality_warning=ocr_quality_warning,
            non_latin_warning=non_latin_warning,
            requires_manual_review=bool(req_manual),
        )

        res_context = ResolutionContext(
            conflict_id=str(conflict.id),
            user_id=str(user_id),
            field_name=conflict.field_name,
            conflict_type=conflict.conflict_type,
            severity=conflict.severity,
            status=conflict.status,
            document_types=doc_types,
            document_ids=[str(doc_a.id), str(doc_b.id)],
            value_a=val_a_masked,
            value_b=val_b_masked,
            deterministic_classification=str(det_cls),
            overall_classification=str(overall_cls),
            confidence_score=round(confidence_score, 2),
            requires_manual_review=bool(req_manual),
            possible_causes=possible_causes,
            recommended_action=recommended_action,
            evidence=evidence,
            ocr_quality_warning=ocr_quality_warning,
            non_latin_warning=non_latin_warning,
            statutory_disclaimer="AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION",
            resolution_mapping=resolution_mapping,
        )

        # 7. Audit Logging (privacy-safe metadata only)
        if log_audit:
            try:
                AuditService.log_event(
                    db=db,
                    action="resolution_context_generated",
                    entity_type="conflict_resolution",
                    entity_id=conflict.id,
                    user_id=user_id,
                    details={
                        "conflict_id": str(conflict.id),
                        "field_name": conflict.field_name,
                        "conflict_type": conflict.conflict_type,
                        "severity": conflict.severity,
                        "deterministic_classification": str(det_cls),
                        "requires_manual_review": bool(req_manual),
                        "has_ocr_warning": bool(ocr_quality_warning),
                        "has_non_latin_warning": bool(non_latin_warning),
                        "mapped_procedure": resolution_mapping.procedure_name if resolution_mapping else None,
                        "mapped_authority": resolution_mapping.authority_name if resolution_mapping else None,
                    },
                )
                db.commit()
            except Exception as e:
                logger.error("Audit log failed for resolution context generation: %s", str(e), exc_info=True)

        return res_context
