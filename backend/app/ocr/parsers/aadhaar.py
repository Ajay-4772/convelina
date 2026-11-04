import re
from typing import Dict, Any, Optional
from app.ocr.parsers.base import BaseDocumentParser
from app.core.validator import validate_verhoeff

class AadhaarParser(BaseDocumentParser):
    """
    Parser for Aadhaar Cards following Aadhaar Act privacy standards:
    - Never retains plaintext 12-digit Aadhaar number.
    - Validates UIDAI Verhoeff checksum if unmasked 12 digits are visible.
    - Masks to XXXX-XXXX-1234.
    - Extracts Name, DOB, Gender, and relation fields.
    """
    def parse(self, raw_text: str) -> Dict[str, Any]:
        fields: Dict[str, Any] = {}
        masked_id: Optional[str] = None
        
        # 1. Masked Aadhaar Number extraction
        aadhaar_pattern = r"\b(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})\b"
        match = re.search(aadhaar_pattern, raw_text)
        if match:
            # Ephemeral checksum validation prior to discarding unmasked digits
            full_digits = match.group(1) + match.group(2) + match.group(3)
            fields["verhoeff_valid"] = validate_verhoeff(full_digits)
            # Mask first 8 digits, keep only last 4
            last_4 = match.group(3)
            masked_id = f"XXXX-XXXX-{last_4}"
            fields["aadhaar_last_4"] = last_4
        else:
            # Check for already masked patterns like XXXX XXXX 1234
            masked_pattern = r"\b[Xx]{4}[\s-]?[Xx]{4}[\s-]?(\d{4})\b"
            m_match = re.search(masked_pattern, raw_text)
            if m_match:
                last_4 = m_match.group(1)
                masked_id = f"XXXX-XXXX-{last_4}"
                fields["aadhaar_last_4"] = last_4
                fields["verhoeff_valid"] = None

        # 2. Date of Birth / Year of Birth extraction
        dob_match = re.search(r"(?:DOB|Date of Birth|जन्म तारीख)[:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if dob_match:
            fields["date_of_birth"] = dob_match.group(1).replace("-", "/")
        else:
            yob_match = re.search(r"(?:Year of Birth|जन्म वर्ष)[:\s]*(\d{4})", raw_text, re.IGNORECASE)
            if yob_match:
                fields["year_of_birth"] = yob_match.group(1)

        # 3. Gender extraction
        gender_match = re.search(r"\b(Male|Female|Transgender|पुरुष|महिला)\b", raw_text, re.IGNORECASE)
        if gender_match:
            g = gender_match.group(1).capitalize()
            if g in ("पुरुष", "Male"):
                fields["gender"] = "Male"
            elif g in ("महिला", "Female"):
                fields["gender"] = "Female"
            else:
                fields["gender"] = g

        # 4. Name extraction
        # Look for English name line above DOB or after header
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            if re.search(r"(?:DOB|Date of Birth|जन्म तारीख|Year of Birth)", line, re.IGNORECASE):
                # The line before DOB is commonly the English name in standard e-Aadhaar
                if i > 0:
                    candidate = lines[i - 1]
                    # Filter out institution header lines
                    if not any(header in candidate.lower() for header in ["government", "india", "authority", "unique", "enrollment"]):
                        cleaned_name = re.sub(r"[^a-zA-Z\s.]", "", candidate).strip()
                        if len(cleaned_name) >= 3 and not fields.get("full_name"):
                            fields["full_name"] = cleaned_name
                break

        return {
            "masked_id": masked_id,
            "fields": fields,
            "raw_text_summary": f"Aadhaar parsed. Found: {list(fields.keys())}"
        }
