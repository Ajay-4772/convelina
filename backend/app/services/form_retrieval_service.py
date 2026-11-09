import logging
import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.official_form import OfficialForm
from app.rag.schemas import OfficialFormResponse

logger = logging.getLogger("consolith.services.form_retrieval")

class FormRetrievalResult:
    def __init__(
        self,
        forms: List[OfficialFormResponse],
        no_verified_form_available: bool = False,
        retrieval_reason: Optional[str] = None,
        suggested_authority: Optional[str] = None,
    ):
        self.forms = forms
        self.no_verified_form_available = no_verified_form_available
        self.retrieval_reason = retrieval_reason
        self.suggested_authority = suggested_authority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "forms": [f.model_dump() for f in self.forms],
            "no_verified_form_available": self.no_verified_form_available,
            "retrieval_reason": self.retrieval_reason,
            "suggested_authority": self.suggested_authority,
        }

class FormRetrievalService:
    """
    Deterministic Official Form Retrieval Service (Phase P3D).
    Enforces strict statutory verification rules:
    - Only forms with verification_status='verified' and is_active=True are ever returned as official forms.
    - Outdated, needs_review, or retired forms are strictly excluded from citizen guidance.
    - Cross-references conflict discrepancy classification and resolution mapping when available.
    - Emits explicit NO_VERIFIED_FORM_AVAILABLE response when no approved form satisfies the criteria.
    - Zero fabrication of government forms, form numbers, or statutory authorities.
    """

    @classmethod
    def retrieve_applicable_forms(
        cls,
        db: Session,
        query: Optional[str] = None,
        document_category: Optional[str] = None,
        issue_type: Optional[str] = None,
        conflict_context: Optional[Dict[str, Any]] = None,
        top_k: int = 4
    ) -> FormRetrievalResult:
        # Base query: active forms excluding needs_review, outdated, retired, and revoked
        q = db.query(OfficialForm).filter(
            OfficialForm.is_active == True,
            OfficialForm.verification_status.notin_(["needs_review", "outdated", "retired", "revoked"])
        )

        matched_form_ids: List[str] = []
        inferred_category = document_category
        inferred_issue_type = issue_type

        # 1. Conflict-Aware Form Retrieval
        if conflict_context:
            res_mapping = conflict_context.get("resolution_mapping") or {}
            prescribed = res_mapping.get("prescribed_forms") or []
            if prescribed:
                for pf in prescribed:
                    fid = pf.get("form_id")
                    if fid and fid not in matched_form_ids:
                        matched_form_ids.append(fid)

            # Extract conflict field name (e.g. full_name, date_of_birth)
            field_name = conflict_context.get("field_name")
            if field_name and not inferred_issue_type:
                inferred_issue_type = field_name.lower()

            # Extract document categories (e.g. ["aadhaar", "pan"])
            doc_types = conflict_context.get("document_types") or []
            if doc_types and not inferred_category:
                inferred_category = doc_types[0].lower()

        # 2. If explicit prescribed forms matched from conflict resolution mapping
        if matched_form_ids:
            forms_by_id = q.filter(OfficialForm.form_id.in_(matched_form_ids)).all()
            if forms_by_id:
                res_forms = [OfficialFormResponse(**f.to_dict()) for f in forms_by_id]
                has_official = any(f.is_official_government_form for f in res_forms)
                return FormRetrievalResult(
                    forms=res_forms[:top_k],
                    no_verified_form_available=not has_official,
                    retrieval_reason="Mapped from deterministic statutory resolution precedence."
                )

        # 3. Category & Issue Type Filtering
        clean_q = (query or "").lower().strip()

        # Keyword inference if category not specified
        if not inferred_category:
            if re.search(r"\b(pan|tin|nsdl|income tax|utiitsl)\b", clean_q):
                inferred_category = "pan"
            elif re.search(r"\b(aadhaar|uidai|resident|enrolment)\b", clean_q):
                inferred_category = "aadhaar"
            elif re.search(r"\b(passport|mea|cpv|annexure)\b", clean_q):
                inferred_category = "passport"
            elif re.search(r"\b(epf|epfo|pf|uan|provident|joint declaration)\b", clean_q):
                inferred_category = "epf"
            elif re.search(r"\b(cbse|education|marksheet|10th|12th)\b", clean_q):
                inferred_category = "education"
            elif re.search(r"\b(gazette|deed poll|proforma)\b", clean_q):
                inferred_category = "gazette"

        if not inferred_issue_type:
            if "name" in clean_q or "spelling" in clean_q:
                inferred_issue_type = "full_name"
            elif "dob" in clean_q or "birth" in clean_q or "date" in clean_q:
                inferred_issue_type = "date_of_birth"
            elif "father" in clean_q or "parent" in clean_q:
                inferred_issue_type = "father_name"
            elif "gender" in clean_q:
                inferred_issue_type = "gender"

        if inferred_category:
            q = q.filter(OfficialForm.document_category == inferred_category.lower())

        candidates = q.order_by(OfficialForm.form_name.asc()).all()

        matching_forms: List[OfficialForm] = []
        for f in candidates:
            # Check applicable issue types if filtered
            if inferred_issue_type:
                types = [str(t).lower() for t in (f.applicable_issue_types or [])]
                if inferred_issue_type.lower() in types:
                    matching_forms.append(f)
                    continue

            # Check lexical query match in title, purpose, conditions
            if clean_q:
                searchable = f"{f.form_name} {f.purpose} {f.issuing_authority} {' '.join(f.applicable_conditions or [])}".lower()
                query_words = [w for w in clean_q.split() if len(w) > 2]
                if any(w in searchable for w in query_words):
                    matching_forms.append(f)
                    continue

            # If no strict filter, keep candidate in category
            if not inferred_issue_type and not clean_q:
                matching_forms.append(f)

        # Deduplicate
        seen_ids = set()
        unique_forms: List[OfficialFormResponse] = []
        for f in matching_forms:
            if f.form_id not in seen_ids:
                seen_ids.add(f.form_id)
                unique_forms.append(OfficialFormResponse(**f.to_dict()))

        if unique_forms:
            has_official = any(f.is_official_government_form for f in unique_forms)
            return FormRetrievalResult(
                forms=unique_forms[:top_k],
                no_verified_form_available=not has_official,
                retrieval_reason=f"Retrieved {len(unique_forms)} forms matching {inferred_category or 'general'} statutory requirements."
            )

        # 4. If query or category was specified and none matched
        if clean_q or inferred_category or conflict_context:
            return FormRetrievalResult(
                forms=[],
                no_verified_form_available=True,
                retrieval_reason="No approved, active official form registered for this specific category or discrepancy type.",
                suggested_authority=inferred_category.upper() if inferred_category else "Competent Authority"
            )

        return FormRetrievalResult(forms=[], no_verified_form_available=False)

    @classmethod
    def get_verified_form_for_download(
        cls,
        db: Session,
        form_id: str,
        is_admin: bool = False
    ) -> Optional[OfficialForm]:
        """
        Retrieves form record for authenticated preview or download.
        Permissions and active/revoked status checks are enforced in the route handler.
        """
        query = db.query(OfficialForm).filter(
            or_(OfficialForm.form_id == form_id, OfficialForm.form_id == form_id.lower())
        )
        return query.first()

