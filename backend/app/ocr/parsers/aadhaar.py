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
        dob_match = re.search(r"(?:DOB|Date of Birth|जन्म तारीख|பிறந்த தேதி)[:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if dob_match:
            fields["date_of_birth"] = dob_match.group(1).replace("-", "/")
        else:
            yob_match = re.search(r"(?:Year of Birth|जन्म वर्ष)[:\s]*(\d{4})", raw_text, re.IGNORECASE)
            if yob_match:
                fields["year_of_birth"] = yob_match.group(1)

        # 3. Gender extraction
        gender_match = re.search(r"\b(Male|Female|Transgender|पुरुष|महिला|ஆண்|பெண்)\b", raw_text, re.IGNORECASE)
        if gender_match:
            g = gender_match.group(1).capitalize()
            if g in ("पुरुष", "Male", "ஆண்"):
                fields["gender"] = "Male"
            elif g in ("महिला", "Female", "பெண்"):
                fields["gender"] = "Female"
            else:
                fields["gender"] = g

        # 4. Name extraction
        # Look for English name line above DOB or after header
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            if re.search(r"(?:DOB|Date of Birth|जन्म तारीख|Year of Birth|பிறந்த தேதி)", line, re.IGNORECASE):
                # The line before DOB is commonly the English name in standard e-Aadhaar
                if i > 0:
                    candidate = lines[i - 1]
                    # Filter out institution header lines
                    if not any(header in candidate.lower() for header in ["government", "india", "authority", "unique", "enrollment", "helpdesk"]):
                        cleaned_name = re.sub(r'^(?:(?:Full\s*)?Name|Candidate(?:\s*Name)?|Student(?:\s*Name)?|Applicant(?:\s*Name)?|பெயர்)[.:\s]+', '', candidate, flags=re.IGNORECASE).strip()
                        cleaned_name = re.sub(r"[^a-zA-Z\s.]", "", cleaned_name).strip()
                        if len(cleaned_name) >= 3 and not fields.get("full_name"):
                            fields["full_name"] = cleaned_name
                break

        # Fallback Name extraction if not caught above
        if not fields.get("full_name"):
            name_kw = re.search(r"(?:Name|Full Name)[.:\s]+([A-Za-z .]{3,40})", raw_text, re.IGNORECASE)
            if name_kw:
                raw_cand = name_kw.group(1).strip()
                cleaned = re.sub(r'^(?:(?:Full\s*)?Name|Candidate(?:\s*Name)?|Student(?:\s*Name)?|Applicant(?:\s*Name)?)[.:\s]+', '', raw_cand, flags=re.IGNORECASE).strip()
                if cleaned and not any(h in cleaned.lower() for h in ["government", "india", "authority", "unique", "enrollment", "helpdesk"]):
                    fields["full_name"] = cleaned

        # Ensure label prefix is stripped from full_name if present
        if fields.get("full_name"):
            fields["full_name"] = re.sub(r'^(?:(?:Full\s*)?Name|Candidate(?:\s*Name)?|Student(?:\s*Name)?|Applicant(?:\s*Name)?)[.:\s]+', '', fields["full_name"], flags=re.IGNORECASE).strip()

        # Regional / Tamil Name extraction (Unicode preservation)
        tamil_match = re.search(r"(?:Regional\s*Name\s*(?:Tamil)?|பெயர்)[.:\s]+([\u0B80-\u0BFF\s.]{2,40})", raw_text)
        if tamil_match:
            cand_tamil = re.sub(r"^(?:பெயர்)[.:\s]*", "", tamil_match.group(1)).strip()
            if cand_tamil and not any(hw in cand_tamil for hw in ["இந்தியா", "அடையாள", "ஆணையம்", "அரசு"]):
                fields["tamil_name"] = cand_tamil

        if not fields.get("tamil_name"):
            # Search line-by-line for standalone Tamil name line, excluding official institutional headers
            tamil_header_words = ["இந்திய", "தனித்துவ", "அடையாள", "ஆணையம்", "அரசு", "ஆதார்", "மையம்", "மத்திய", "பதிவு", "பிறந்த", "தேதி", "முகவரி", "ஆண்", "பெண்", "உதவி"]
            for line in lines:
                if re.search(r"[\u0B80-\u0BFF]{2,}", line) and not re.search(r"[a-zA-Z0-9]", line):
                    if not any(hw in line for hw in tamil_header_words):
                        t_tokens = re.findall(r"[\u0B80-\u0BFF.]+", line)
                        if 1 <= len(t_tokens) <= 4:
                            cand_t = " ".join(t_tokens).strip()
                            if len(cand_t) >= 3:
                                fields["tamil_name"] = cand_t
                                break

        # 5. PIN Code extraction (6 digits)
        pin_match = re.search(r"\b([1-9][0-9]{5})\b", raw_text)
        if pin_match:
            fields["pincode"] = pin_match.group(1)

        # 6. Address extraction
        addr_match = re.search(r"(?:Address|पता)[:\s]+(.*?)(?=\b\d{4}\b|\bUnique\b|\bHelpdesk\b|\n\n|$)", raw_text, re.DOTALL | re.IGNORECASE)
        if addr_match:
            raw_addr = addr_match.group(1).replace("\n", " ").strip()
            # Clean up redundant spaces
            fields["address"] = re.sub(r"\s+", " ", raw_addr)[:200].strip()

        return {
            "masked_id": masked_id,
            "fields": fields,
            "raw_text_summary": f"Aadhaar parsed. Found: {list(fields.keys())}"
        }
