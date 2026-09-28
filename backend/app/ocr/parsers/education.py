import re
from typing import Dict, Any, Optional
from app.ocr.parsers.base import BaseDocumentParser

class EducationCertificateParser(BaseDocumentParser):
    """
    Parser for Class 10 (Secondary) and Class 12 (Higher Secondary) educational certificates.
    Commonly used as primary proof of Date of Birth and Name in India.
    """
    def __init__(self, doc_type: str = "education_10th"):
        self.doc_type = doc_type

    def parse(self, raw_text: str) -> Dict[str, Any]:
        fields: Dict[str, Any] = {
            "certificate_tier": "Class 10" if self.doc_type == "education_10th" else "Class 12"
        }
        masked_id: Optional[str] = None

        # 1. Roll Number / Registration Number
        roll_match = re.search(r"(?:Roll\s*(?:No|Number)|Registration\s*(?:No|Number)|Enrollment\s*No)[:\s]*([A-Za-z0-9/-]{5,20})", raw_text, re.IGNORECASE)
        if roll_match:
            roll_no = roll_match.group(1).strip()
            fields["roll_number"] = roll_no
            masked_id = f"ROLL-{roll_no}"

        # 2. Date of Birth (standard on 10th certificates)
        dob_match = re.search(r"(?:Date\s*of\s*Birth|DOB|Born\s*on)[:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if dob_match:
            fields["date_of_birth"] = dob_match.group(1).replace("-", "/")

        # 3. Year of Examination / Passing
        exam_match = re.search(r"(?:held\s*in|Examination|Passing\s*Year|Session|Year)[:\s]*\b(19\d{2}|20\d{2})\b", raw_text, re.IGNORECASE)
        if exam_match:
            fields["examination_year"] = exam_match.group(1)
        else:
            # Strip full date patterns first so DOB year is not grabbed
            text_without_dates = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b", "", raw_text)
            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text_without_dates)
            if year_match:
                fields["examination_year"] = year_match.group(1)


        # 4. Educational Board detection
        boards = ["CBSE", "CENTRAL BOARD OF SECONDARY EDUCATION", "ICSE", "CISCE", "STATE BOARD", "SECONDARY EDUCATION", "HIGHER SECONDARY"]
        for b in boards:
            if re.search(r"\b" + re.escape(b) + r"\b", raw_text, re.IGNORECASE):
                fields["board"] = b
                break

        # 5. Candidate Name extraction
        name_match = re.search(r"(?:This\s+is\s+to\s+certify\s+that|Candidate\s*Name|Name\s*of\s*Student|Name)[:\s]+([A-Za-z .]{3,35})", raw_text, re.IGNORECASE)
        if name_match:
            candidate_raw = name_match.group(1).splitlines()[0]
            # Strip trailing indicators like "Born on", "Son of"
            candidate_clean = re.split(r"\b(?:Born|Son|Daughter|has|passed)\b", candidate_raw, flags=re.IGNORECASE)[0]
            fields["full_name"] = re.sub(r"[^a-zA-Z .]", "", candidate_clean).strip()
        else:
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            for l in lines:
                if re.match(r"^[A-Z .]{4,30}$", l) and not any(k in l.lower() for k in ["board", "secondary", "examination", "certificate", "marks"]):
                    fields["full_name"] = l
                    break


        return {
            "masked_id": masked_id,
            "fields": fields,
            "raw_text_summary": f"{self.doc_type} parsed. Found: {list(fields.keys())}"
        }
