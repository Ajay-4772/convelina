import re
from typing import Dict, Any, Optional
from app.ocr.parsers.base import BaseDocumentParser

class EPFRecordParser(BaseDocumentParser):
    """
    Parser for Employees' Provident Fund (EPFO / UAN) passbooks and records.
    Key identifiers: 12-digit UAN (Universal Account Number) and Member ID.
    """
    def parse(self, raw_text: str) -> Dict[str, Any]:
        fields: Dict[str, Any] = {
            "issuing_authority": "EPFO"
        }
        masked_id: Optional[str] = None

        # 1. UAN (12 digits)
        uan_match = re.search(r"(?:UAN|Universal\s*Account\s*Number)[:\s]*(\d{12})\b", raw_text, re.IGNORECASE)
        if not uan_match:
            uan_match = re.search(r"\b(\d{12})\b", raw_text)
            
        if uan_match:
            uan_no = uan_match.group(1)
            fields["uan"] = uan_no
            # Mask middle digits for privacy: e.g. 1004****5678
            masked_id = f"UAN-{uan_no[:4]}****{uan_no[-4:]}"

        # 2. Member ID / PF Account No
        member_match = re.search(r"(?:Member\s*ID|PF\s*Account\s*No)[:\s]*([A-Za-z0-9/-]{10,30})", raw_text, re.IGNORECASE)
        if member_match:
            fields["member_id"] = member_match.group(1).strip()

        # 3. Member Name
        name_match = re.search(r"(?:Full\s*Name|Member\s*Name|Name\s*of\s*Member|Employee\s*Name|\bMember(?!\s*(?:Passbook|ID|Profile)))[.:\s]+([A-Za-z .]{3,40})", raw_text, re.IGNORECASE)
        if not name_match:
            name_match = re.search(r"\bName[.:\s]+([A-Za-z .]{3,40})", raw_text, re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).splitlines()[0]
            candidate = re.split(r"\b(?:UAN|Member\s*ID|PF|Establishment|Employer|Date|DOJ|DOE|Exit|Joining)\b", candidate, flags=re.IGNORECASE)[0]
            cleaned = re.sub(r"[^a-zA-Z .]", "", candidate).strip()
            cleaned = re.sub(r'^(?:(?:Member|Employee|Full)?\s*Name)[.:\s]+', '', cleaned, flags=re.IGNORECASE).strip()
            if len(cleaned) >= 3 and not any(k in cleaned.lower() for k in ["provident", "organisation", "epfo", "india"]):
                fields["full_name"] = cleaned
                fields["member_name"] = cleaned

        # 4. Establishment / Employer Name
        est_match = re.search(r"(?:Establishment\s*Name|Employer\s*Name|Establishment)[:\s]*([A-Za-z0-9 .,&-]{4,50})", raw_text, re.IGNORECASE)
        if est_match:
            candidate_est = est_match.group(1).splitlines()[0]
            candidate_est = re.split(r"\b(?:Date|DOJ|DOE|Establishment\s*ID|Est\s*ID|UAN)\b", candidate_est, flags=re.IGNORECASE)[0]
            cleaned_est = candidate_est.strip()
            fields["establishment_name"] = cleaned_est
            fields["employer_name"] = cleaned_est

        # Establishment ID
        est_id_match = re.search(r"(?:Establishment\s*ID|Est\s*ID)[:\s]*([A-Za-z0-9]{5,20})", raw_text, re.IGNORECASE)
        if est_id_match:
            fields["establishment_id"] = est_id_match.group(1).strip()

        # 5. Date of Birth if present
        dob_match = re.search(r"(?:Date\s*of\s*Birth|DOB)[:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if dob_match:
            fields["date_of_birth"] = dob_match.group(1).replace("-", "/")

        # 6. Date of Joining
        doj_match = re.search(r"(?:Date\s*of\s*Joining|DOJ)[:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if doj_match:
            fields["date_of_joining"] = doj_match.group(1).replace("-", "/")

        # 7. Date of Exit (Optional: can be None / NA if currently employed)
        doe_match = re.search(r"(?:Date\s*of\s*Exit|DOE)[:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4}|NA|N\.A\.|N/A|-)", raw_text, re.IGNORECASE)
        if doe_match:
            val_doe = doe_match.group(1).strip()
            if val_doe.upper() in ("NA", "N.A.", "N/A", "-", "NONE", "NIL"):
                fields["date_of_exit"] = None
            else:
                fields["date_of_exit"] = val_doe.replace("-", "/")
        else:
            fields["date_of_exit"] = None

        return {
            "masked_id": masked_id,
            "fields": fields,
            "raw_text_summary": f"EPF record parsed. Found: {list(fields.keys())}"
        }
