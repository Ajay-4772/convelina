import re
from typing import Dict, Any, Optional
from app.ocr.parsers.base import BaseDocumentParser

class EPFRecordParser(BaseDocumentParser):
    """
    Parser for Employees' Provident Fund (EPFO / UAN) passbooks and records.
    Key identifiers: 12-digit UAN (Universal Account Number) and Member ID.
    """
    def parse(self, raw_text: str) -> Dict[str, Any]:
        fields: Dict[str, Any] = {}
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
        name_match = re.search(r"(?:Member\s*Name|Name\s*of\s*Member|Employee\s*Name)[:\s]*([A-Za-z .]{3,40})", raw_text, re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).splitlines()[0]
            fields["full_name"] = re.sub(r"[^a-zA-Z .]", "", candidate).strip()

        # 4. Establishment / Employer Name
        est_match = re.search(r"(?:Establishment\s*Name|Employer\s*Name)[:\s]*([A-Za-z0-9 .,&-]{4,50})", raw_text, re.IGNORECASE)
        if est_match:
            candidate_est = est_match.group(1).splitlines()[0]
            fields["establishment_name"] = candidate_est.strip()


        # 5. Date of Birth if present
        dob_match = re.search(r"(?:Date\s*of\s*Birth|DOB)[:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if dob_match:
            fields["date_of_birth"] = dob_match.group(1).replace("-", "/")

        return {
            "masked_id": masked_id,
            "fields": fields,
            "raw_text_summary": f"EPF record parsed. Found: {list(fields.keys())}"
        }
