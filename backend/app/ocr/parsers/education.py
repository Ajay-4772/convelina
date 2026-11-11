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
        roll_match = re.search(r"(?:Roll\s*(?:No|Number|No\.)?|Enrollment\s*No|Registration\s*/\s*Roll|Unique\s*ID\s*/\s*Roll\s*No)[:\s]*([A-Za-z0-9/-]{4,20})", raw_text, re.IGNORECASE)
        if roll_match:
            roll_no = roll_match.group(1).strip()
            fields["roll_number"] = roll_no
            masked_id = f"ROLL-{roll_no}"

        # Registration Number
        reg_match = re.search(r"(?:Registration\s*(?:No|Number)|Reg\s*No)[:\s]*([A-Za-z0-9/-]{4,25})", raw_text, re.IGNORECASE)
        if reg_match:
            fields["registration_number"] = reg_match.group(1).strip()

        # 2. Date of Birth (standard on 10th certificates)
        dob_match = re.search(r"(?:Date\s*of\s*Birth|DOB|Born\s*on)[:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if dob_match:
            fields["date_of_birth"] = dob_match.group(1).replace("-", "/")

        # 3. Year of Examination / Passing
        exam_match = re.search(r"(?:held\s*in|Examination|Passing\s*Year|Session|Year)[:\s]*\b(19\d{2}|20\d{2})\b", raw_text, re.IGNORECASE)
        if exam_match:
            fields["examination_year"] = exam_match.group(1)
            fields["passing_year"] = exam_match.group(1)
        else:
            # Strip full date patterns first so DOB year is not grabbed
            text_without_dates = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b", "", raw_text)
            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text_without_dates)
            if year_match:
                fields["examination_year"] = year_match.group(1)
                fields["passing_year"] = year_match.group(1)

        # 4. Educational Board detection (including multi-line board headers)
        flat_text = " ".join(raw_text.split()).upper()
        if "CENTRAL BOARD OF SECONDARY EDUCATION" in flat_text:
            fields["board"] = "CENTRAL BOARD OF SECONDARY EDUCATION"
            fields["issuing_authority"] = "CBSE"
        elif "CENTRAL BOARD" in flat_text or "CBSE" in flat_text:
            fields["board"] = "CBSE"
            fields["issuing_authority"] = "CBSE"
        elif "COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS" in flat_text:
            fields["board"] = "COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS"
            fields["issuing_authority"] = "ICSE"
        elif "COUNCIL FOR THE INDIAN SCHOOL" in flat_text or "CISCE" in flat_text or "ICSE" in flat_text:
            fields["board"] = "ICSE"
            fields["issuing_authority"] = "ICSE"
        elif "MAHARASHTRA STATE BOARD" in flat_text:
            fields["board"] = "MAHARASHTRA STATE BOARD"
            fields["issuing_authority"] = "State Board"
        elif "STATE BOARD" in flat_text or "SECONDARY EDUCATION" in flat_text:
            fields["board"] = "State Board"
            fields["issuing_authority"] = "State Board"

        # 5. Candidate Name extraction
        name_match = re.search(r"(?:This\s+is\s+to\s+certify\s+that|Candidate\s*Name|Name\s*of\s*(?:Student|Candidate)|Student\s*Name|Candidate|\bName)[:=\-\s]+([A-Za-z .]{3,40})", raw_text, re.IGNORECASE)
        if name_match:
            candidate_raw = name_match.group(1).splitlines()[0]
            # Strip trailing indicators like "Born on", "Son of", "Father"
            candidate_clean = re.split(r"\b(?:Born|Son|Daughter|has|passed|Father|Mother|DOB|Roll|Reg|Unique)\b", candidate_raw, flags=re.IGNORECASE)[0]
            cleaned = re.sub(r"[^a-zA-Z .]", "", candidate_clean).strip()
            cleaned = re.sub(r'^(?:(?:Candidate|Student|Name|Shri|Kumari|Master)(?:\s*Name)?|Name\s*of\s*(?:Candidate|Student))[.:\s]+', '', cleaned, flags=re.IGNORECASE).strip()
            if len(cleaned) >= 3 and cleaned.lower() not in ("name", "candidate", "student", "candidate name"):
                fields["full_name"] = cleaned
        else:
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            for l in lines:
                if re.match(r"^[A-Z .]{4,30}$", l) and not any(k in l.lower() for k in ["board", "secondary", "examination", "certificate", "marks"]):
                    cleaned = re.sub(r'^(?:(?:Candidate|Student|Name|Shri|Kumari|Master)(?:\s*Name)?)[.:\s]+', '', l, flags=re.IGNORECASE).strip()
                    fields["full_name"] = cleaned
                    break

        # 6. Father's Name
        father_match = re.search(r"(?:Father'?s?\s*Name|Father\s*Name)[:\s]+([A-Za-z .]{3,35})", raw_text, re.IGNORECASE)
        if father_match:
            cand_f = father_match.group(1).splitlines()[0]
            cand_f = re.split(r"\b(?:Mother|DOB|Roll|Date|Born)\b", cand_f, flags=re.IGNORECASE)[0]
            cleaned_f = re.sub(r"[^a-zA-Z .]", "", cand_f).strip()
            cleaned_f = re.sub(r'^(?:Father\'?s?\s*Name|Father\s*Name|Father)[.:\s]+', '', cleaned_f, flags=re.IGNORECASE).strip()
            if len(cleaned_f) >= 3:
                fields["father_name"] = cleaned_f

        # 7. Mother's Name
        mother_match = re.search(r"(?:Mother'?s?\s*Name|Mother\s*Name)[:\s]+([A-Za-z .]{3,35})", raw_text, re.IGNORECASE)
        if mother_match:
            cand_m = mother_match.group(1).splitlines()[0]
            cand_m = re.split(r"\b(?:Father|DOB|Roll|Date|Born)\b", cand_m, flags=re.IGNORECASE)[0]
            cleaned_m = re.sub(r"[^a-zA-Z .]", "", cand_m).strip()
            cleaned_m = re.sub(r'^(?:Mother\'?s?\s*Name|Mother\s*Name|Mother)[.:\s]+', '', cleaned_m, flags=re.IGNORECASE).strip()
            if len(cleaned_m) >= 3:
                fields["mother_name"] = cleaned_m



        return {
            "masked_id": masked_id,
            "fields": fields,
            "raw_text_summary": f"{self.doc_type} parsed. Found: {list(fields.keys())}"
        }
