import re
from typing import Dict, Any, Optional
from app.ocr.parsers.base import BaseDocumentParser

class PassportParser(BaseDocumentParser):
    """
    Parser for Indian Passports.
    Passport Number format: 1 letter followed by 7 digits (e.g. Z1234567).
    """
    def parse(self, raw_text: str) -> Dict[str, Any]:
        fields: Dict[str, Any] = {}
        masked_id: Optional[str] = None

        # 1. Passport Number
        passport_match = re.search(r"\b([A-Z][0-9]{7})\b", raw_text)
        if passport_match:
            p_no = passport_match.group(1)
            fields["passport_number"] = p_no
            masked_id = f"{p_no[0]}*****{p_no[-2:]}"

        # 2. Dates (DOB and Expiry)
        # Indian passports typically have "Date of Birth" and "Date of Expiry"
        dates = re.findall(r"\b([0-3]?\d[/-][0-1]?\d[/-]\d{4})\b", raw_text)
        if dates:
            fields["date_of_birth"] = dates[0].replace("-", "/")
            if len(dates) > 1:
                fields["expiry_date"] = dates[-1].replace("-", "/")

        # 3. Nationality
        if re.search(r"\b(INDIAN|REPUBLIC OF INDIA)\b", raw_text, re.IGNORECASE):
            fields["nationality"] = "INDIAN"

        # 4. Gender
        gender_match = re.search(r"\bSex[:\s]*([MF])\b", raw_text, re.IGNORECASE)
        if gender_match:
            fields["gender"] = "Male" if gender_match.group(1).upper() == "M" else "Female"

        # 5. Names (Surname, Given Name)
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            if re.search(r"Surname", line, re.IGNORECASE) and i + 1 < len(lines):
                fields["surname"] = re.sub(r"[^a-zA-Z\s]", "", lines[i + 1]).strip()
            elif re.search(r"Given\s*Name", line, re.IGNORECASE) and i + 1 < len(lines):
                fields["given_name"] = re.sub(r"[^a-zA-Z\s]", "", lines[i + 1]).strip()

        # Combine full name if components found
        if fields.get("given_name") and fields.get("surname"):
            fields["full_name"] = f"{fields['given_name']} {fields['surname']}"
        elif fields.get("given_name"):
            fields["full_name"] = fields["given_name"]

        return {
            "masked_id": masked_id,
            "fields": fields,
            "raw_text_summary": f"Passport parsed. Found: {list(fields.keys())}"
        }
