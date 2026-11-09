from typing import Dict, Any
from app.ocr.parsers.base import BaseDocumentParser
from app.ocr.parsers.aadhaar import AadhaarParser
from app.ocr.parsers.pan import PANParser
from app.ocr.parsers.passport import PassportParser
from app.ocr.parsers.education import EducationCertificateParser
from app.ocr.parsers.epf import EPFRecordParser

class GenericDocumentParser(BaseDocumentParser):
    def parse(self, raw_text: str) -> Dict[str, Any]:
        return {
            "masked_id": None,
            "fields": {"raw_snippet": raw_text[:200] if raw_text else ""},
            "raw_text_summary": f"Generic document processed ({len(raw_text)} chars)."
        }

def get_document_parser(document_type: str) -> BaseDocumentParser:
    """
    Returns dedicated parser instance for the specified document type.
    """
    normalized = document_type.strip().lower()
    if normalized == "aadhaar":
        return AadhaarParser()
    elif normalized == "pan":
        return PANParser()
    elif normalized == "passport":
        return PassportParser()
    elif normalized in ("education_10th", "education_12th"):
        return EducationCertificateParser(doc_type=normalized)
    elif normalized in ("epf", "epf_record", "epfo"):
        return EPFRecordParser()
    else:
        return GenericDocumentParser()
