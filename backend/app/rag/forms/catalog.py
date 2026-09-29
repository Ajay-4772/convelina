import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.official_form import OfficialForm
from app.rag.schemas import OfficialFormResponse

logger = logging.getLogger("consolith.rag.forms")

class FormCatalogService:
    @staticmethod
    def list_forms(
        db: Session,
        category: Optional[str] = None,
        issue_type: Optional[str] = None
    ) -> List[OfficialFormResponse]:
        query = db.query(OfficialForm).filter(OfficialForm.is_active == True)
        if category:
            query = query.filter(OfficialForm.document_category == category.lower())
        
        forms = query.order_by(OfficialForm.form_name.asc()).all()
        
        result = []
        for f in forms:
            # If issue_type filter specified, check JSONB applicable_issue_types
            if issue_type:
                types = f.applicable_issue_types or []
                if issue_type.lower() not in [t.lower() for t in types]:
                    continue
            result.append(OfficialFormResponse(**f.to_dict()))
        
        return result

    @staticmethod
    def get_form_by_id(db: Session, form_id: str) -> Optional[OfficialFormResponse]:
        f = db.query(OfficialForm).filter(
            or_(OfficialForm.form_id == form_id, OfficialForm.form_id == form_id.lower()),
            OfficialForm.is_active == True
        ).first()
        if not f:
            return None
        return OfficialFormResponse(**f.to_dict())
