import re
from typing import Dict, Any, Optional
from app.ocr.parsers.base import BaseDocumentParser

class PANParser(BaseDocumentParser):
    """
    Parser for Indian Permanent Account Number (PAN) cards.
    Format: 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F).
    """
    def parse(self, raw_text: str) -> Dict[str, Any]:
        fields: Dict[str, Any] = {}
        masked_id: Optional[str] = None

        # 1. PAN Number extraction with OCR character disambiguation
        # Standard: 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F)
        # Handles frequent OCR confusions: S/5, O/0, I/1, Z/2, B/8
        digit_replacements = {'S': '5', 's': '5', 'O': '0', 'o': '0', 'I': '1', 'i': '1', 'Z': '2', 'z': '2', 'B': '8'}
        letter_replacements = {'5': 'S', '0': 'O', '1': 'I', '2': 'Z', '8': 'B'}

        # First try exact regex
        pan_match = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b", raw_text)
        if pan_match:
            pan_no = pan_match.group(1)
            fields["pan_number"] = pan_no
            masked_id = f"{pan_no[:2]}***{pan_no[5:]}"
        else:
            # Fall back to 10-char alphanumeric candidates and normalize positions
            for candidate in re.findall(r"\b([A-Za-z0-9]{10})\b", raw_text):
                p_letters = ''.join(letter_replacements.get(c, c) for c in candidate[:5].upper())
                p_digits = ''.join(digit_replacements.get(c, c) for c in candidate[5:9])
                p_last = letter_replacements.get(candidate[9], candidate[9]).upper()
                normalized_pan = f"{p_letters}{p_digits}{p_last}"
                if re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", normalized_pan):
                    fields["pan_number"] = normalized_pan
                    masked_id = f"{normalized_pan[:2]}***{normalized_pan[5:]}"
                    break



        # 2. Date of Birth extraction (DD/MM/YYYY)
        dob_match = re.search(r"\b([0-3]?\d[/-][0-1]?\d[/-]\d{4})\b", raw_text)
        if dob_match:
            fields["date_of_birth"] = dob_match.group(1).replace("-", "/")

        # 3. Name & Father's Name parsing
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            # Check for Father's Name indicator
            if re.search(r"(?:Father'?s?\s*Name|पिता का नाम)", line, re.IGNORECASE):
                # The line before "Father's Name" is usually the holder's Name
                if i > 0 and not fields.get("full_name"):
                    candidate = lines[i - 1]
                    if not any(k in candidate.lower() for k in ["income", "tax", "department", "govt", "india"]):
                        cleaned = re.sub(r"[^a-zA-Z\s.]", "", candidate).strip()
                        if len(cleaned) >= 3:
                            fields["full_name"] = cleaned
                # The line after "Father's Name" is the father's name
                if i + 1 < len(lines):
                    candidate_father = lines[i + 1]
                    cleaned_father = re.sub(r"[^a-zA-Z\s.]", "", candidate_father).strip()
                    if len(cleaned_father) >= 3 and not re.search(r"\d", candidate_father):
                        fields["father_name"] = cleaned_father

        # Fallback name search if not found
        if not fields.get("full_name"):
            for line in lines:
                if re.match(r"^[A-Z\s.]{4,35}$", line) and not any(k in line.lower() for k in ["income", "tax", "department", "india", "permanent", "account"]):
                    fields["full_name"] = line.strip()
                    break

        return {
            "masked_id": masked_id,
            "fields": fields,
            "raw_text_summary": f"PAN parsed. Found: {list(fields.keys())}"
        }
