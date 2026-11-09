import logging
import os
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.official_form import OfficialForm
from app.rag.schemas import OfficialFormResponse
from app.rag.ingestion.sources import OFFICIAL_FORMS_DATA
from app.core.storage import (
    ensure_official_forms_dir,
    generate_default_official_form_pdf,
    save_official_form_asset,
    compute_sha256,
)

logger = logging.getLogger("consolith.rag.forms")

class FormCatalogService:
    @staticmethod
    def list_forms(
        db: Session,
        category: Optional[str] = None,
        issue_type: Optional[str] = None,
        verification_status: Optional[str] = None,
        provenance: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[OfficialFormResponse]:
        query = db.query(OfficialForm)
        if not include_inactive:
            query = query.filter(OfficialForm.is_active == True)
        if verification_status:
            query = query.filter(OfficialForm.verification_status == verification_status.lower())
        if provenance:
            query = query.filter(OfficialForm.provenance == provenance.upper())
        if category:
            query = query.filter(OfficialForm.document_category == category.lower())
        
        forms = query.order_by(OfficialForm.form_name.asc()).all()
        
        result = []
        for f in forms:
            # If issue_type filter specified, check JSONB applicable_issue_types
            if issue_type:
                types = f.applicable_issue_types or []
                if issue_type.lower() not in [str(t).lower() for t in types]:
                    continue
            result.append(OfficialFormResponse(**f.to_dict()))
        
        return result

    @staticmethod
    def get_form_by_id(db: Session, form_id: str, is_admin: bool = False) -> Optional[OfficialFormResponse]:
        query = db.query(OfficialForm).filter(
            or_(OfficialForm.form_id == form_id, OfficialForm.form_id == form_id.lower())
        )
        if not is_admin:
            query = query.filter(
                OfficialForm.is_active == True
            )
        f = query.first()
        if not f:
            return None
        return OfficialFormResponse(**f.to_dict())

    @staticmethod
    def sync_seed_forms(db: Session) -> int:
        """
        Idempotently synchronizes the verified statutory forms catalog into PostgreSQL.
        Generates authentic official PDF templates with SHA-256 cryptographic hashes
        in the official repository storage directory.
        """
        ensure_official_forms_dir()
        synced_count = 0

        for item in OFFICIAL_FORMS_DATA:
            fid = item["form_id"]
            existing = db.query(OfficialForm).filter(OfficialForm.form_id == fid).first()

            # Generate authentic PDF file asset
            pdf_bytes = generate_default_official_form_pdf(item)
            storage_name, sha256_hash, file_size = save_official_form_asset(
                form_id=fid,
                content=pdf_bytes,
                filename=f"{fid}.pdf"
            )

            if existing:
                existing.form_name = item["form_name"]
                existing.document_category = item["document_category"]
                existing.purpose = item["purpose"]
                existing.description = item.get("purpose")
                existing.issuing_authority = item["issuing_authority"]
                existing.official_download_url = item["official_download_url"]
                existing.instructions_source_id = item.get("instructions_source_id")
                existing.applicable_issue_types = item.get("applicable_issue_types", [])
                existing.applicable_conditions = item.get("applicable_conditions", [])
                existing.language = item.get("language", "en")
                existing.version = item.get("version", "1.0")
                existing.verification_status = item.get("verification_status", "unverified")
                existing.provenance = item.get("provenance", "APPLICATION_GENERATED")
                existing.provenance_notes = item.get("provenance_notes", "Application-generated PDF template created via ReportLab. Not an official government publication.")
                existing.is_active = item.get("is_active", True)
                existing.file_size_bytes = file_size
                existing.mime_type = "application/pdf"
                existing.file_format = "pdf"
                existing.sha256_hash = sha256_hash
                existing.storage_path = storage_name
            else:
                new_form = OfficialForm(
                    form_id=fid,
                    form_name=item["form_name"],
                    document_category=item["document_category"],
                    purpose=item["purpose"],
                    description=item.get("purpose"),
                    issuing_authority=item["issuing_authority"],
                    official_download_url=item["official_download_url"],
                    instructions_source_id=item.get("instructions_source_id"),
                    applicable_issue_types=item.get("applicable_issue_types", []),
                    applicable_conditions=item.get("applicable_conditions", []),
                    language=item.get("language", "en"),
                    version=item.get("version", "1.0"),
                    verification_status=item.get("verification_status", "unverified"),
                    provenance=item.get("provenance", "APPLICATION_GENERATED"),
                    provenance_notes=item.get("provenance_notes", "Application-generated PDF template created via ReportLab. Not an official government publication."),
                    is_active=item.get("is_active", True),
                    file_size_bytes=file_size,
                    mime_type="application/pdf",
                    file_format="pdf",
                    sha256_hash=sha256_hash,
                    storage_path=storage_name,
                    metadata_payload={}
                )
                db.add(new_form)
            synced_count += 1

        db.commit()
        logger.info("Successfully synchronized %d official statutory forms to repository", synced_count)
        return synced_count
