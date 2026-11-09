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
        # Standard: 1 uppercase letter followed by 7 digits (e.g. Z1234567)
        exact_p = re.search(r"\b([A-Z][0-9]{7})\b", raw_text)
        if exact_p:
            p_no = exact_p.group(1)
            fields["passport_number"] = p_no
            masked_id = f"{p_no[0]}*****{p_no[-2:]}"
        else:
            passport_match = re.search(r"(?:Passport\s*(?:No|Number|No\.)?[.:\s]*)([A-Z0-9]{8})\b", raw_text, re.IGNORECASE)
            if passport_match:
                candidate = passport_match.group(1).upper()
                if not re.match(r"^[A-Z][0-9]{7}$", candidate):
                    # Only apply character fix if format failed
                    first_char = candidate[0]
                    if first_char in "01278":
                        letter_fix = {"7": "Z", "1": "I", "0": "O", "8": "B", "2": "Z"}.get(first_char, "Z")
                        candidate = letter_fix + candidate[1:]
                if re.match(r"^[A-Z][0-9]{7}$", candidate):
                    fields["passport_number"] = candidate
                    masked_id = f"{candidate[0]}*****{candidate[-2:]}"

        # 2. Dates (DOB, Issue, Expiry) - Prioritize explicit label matching
        dob_match = re.search(r"(?:Date\s*of\s*Birth|DOB|Birth\s*Date)[.:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if dob_match:
            fields["date_of_birth"] = dob_match.group(1).replace("-", "/")

        doi_match = re.search(r"(?:Date\s*of\s*Issue|DOI|Issue\s*Date)[.:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if doi_match:
            fields["date_of_issue"] = doi_match.group(1).replace("-", "/")

        doe_match = re.search(r"(?:Date\s*of\s*Expiry|DOE|Expiry\s*Date)[.:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if doe_match:
            fields["expiry_date"] = doe_match.group(1).replace("-", "/")

        # Fallback date extraction if explicit labels were missed
        if not fields.get("date_of_birth"):
            dates = re.findall(r"\b([0-3]?\d[/-][0-1]?\d[/-]\d{4})\b", raw_text)
            if dates:
                fields["date_of_birth"] = dates[0].replace("-", "/")
                if len(dates) > 1 and not fields.get("expiry_date"):
                    fields["expiry_date"] = dates[-1].replace("-", "/")

        # 3. Nationality
        if re.search(r"(?:Nationality[.:\s]*)?\b(INDIAN|REPUBLIC OF INDIA)\b", raw_text, re.IGNORECASE):
            fields["nationality"] = "INDIAN"

        # 4. Gender
        gender_match = re.search(r"\b(?:Sex|Gender)[.:\s]*([MF]|Male|Female)\b", raw_text, re.IGNORECASE)
        if gender_match:
            g = gender_match.group(1).upper()
            fields["gender"] = "Male" if g in ("M", "MALE") else "Female"

        # 5. Names (Surname, Given Name, Full Name)
        inline_surname = re.search(r"(?:Surname(?:\(s\))?|1\.\s*Surname(?:\(s\))?)(?:\s*/\s*Nom)?[.:\s/]+([A-Za-z ]{2,35})", raw_text, re.IGNORECASE)
        if inline_surname and not fields.get("surname"):
            cand_s = inline_surname.group(1).strip()
            cand_s = re.split(r"\b(?:Given|Prenom|DOB|Date|Sex|Nationality)\b", cand_s, flags=re.IGNORECASE)[0].strip()
            if cand_s and not any(k in cand_s.lower() for k in ["passport", "republic", "india", "given", "prenom"]):
                fields["surname"] = cand_s

        inline_given = re.search(r"(?:Given\s*Names?(?:\(s\))?|2\.\s*Given\s*Names?(?:\(s\))?)(?:\s*/\s*Prenom(?:s)?)?[.:\s/]+([A-Za-z ]{2,35})", raw_text, re.IGNORECASE)
        if inline_given and not fields.get("given_name"):
            cand_g = inline_given.group(1).strip()
            cand_g = re.split(r"\b(?:Surname|Nom|DOB|Date|Sex|Nationality)\b", cand_g, flags=re.IGNORECASE)[0].strip()
            if cand_g and not any(k in cand_g.lower() for k in ["passport", "republic", "india", "surname", "nom"]):
                fields["given_name"] = cand_g

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            if re.search(r"^(?:Surname|1\.\s*Surname)(?:\s*/\s*Nom)?[:\s]*$", line, re.IGNORECASE) and i + 1 < len(lines):
                cand_s = re.sub(r"[^a-zA-Z\s]", "", lines[i + 1]).strip()
                if cand_s and not any(k in cand_s.lower() for k in ["given", "prenom", "passport"]):
                    fields["surname"] = cand_s
            elif re.search(r"^(?:Given\s*Names?|2\.\s*Given\s*Names?)(?:\s*/\s*Prenom(?:s)?)?[:\s]*$", line, re.IGNORECASE) and i + 1 < len(lines):
                cand_g = re.sub(r"[^a-zA-Z\s]", "", lines[i + 1]).strip()
                if cand_g and not any(k in cand_g.lower() for k in ["surname", "nom", "passport"]):
                    fields["given_name"] = cand_g

        # Strip prefixes
        if fields.get("surname"):
            fields["surname"] = re.sub(r"^(?:Surname|Nom|1\.\s*Surname)[.:\s/]+", "", fields["surname"], flags=re.IGNORECASE).strip()
        if fields.get("given_name"):
            fields["given_name"] = re.sub(r"^(?:Given\s*Names?|Prenom|2\.\s*Given\s*Names?)[.:\s/]+", "", fields["given_name"], flags=re.IGNORECASE).strip()

        # Combine full name if components found
        if fields.get("given_name") and fields.get("surname"):
            fields["full_name"] = f"{fields['given_name']} {fields['surname']}"
        elif fields.get("given_name") and not fields.get("full_name"):
            fields["full_name"] = fields["given_name"]
        elif fields.get("surname") and not fields.get("full_name"):
            fields["full_name"] = fields["surname"]
        elif not fields.get("full_name"):
            full_match = re.search(r"\bFull\s*Name[.:\s]+([A-Za-z ]{3,35})", raw_text, re.IGNORECASE)
            if full_match:
                candidate_full = full_match.group(1).strip()
                if not any(k in candidate_full.lower() for k in ["passport", "republic", "india", "office", "sample"]):
                    fields["full_name"] = candidate_full

        if fields.get("full_name"):
            fields["full_name"] = re.sub(r'^(?:(?:Full\s*)?Name|Candidate(?:\s*Name)?)[.:\s]+', '', fields["full_name"], flags=re.IGNORECASE).strip()

        # 6. Place of Birth
        pob_match = re.search(r"(?:Place\s*of\s*Birth|POB)[.:\s]+([A-Za-z\s,.-]{3,35})", raw_text, re.IGNORECASE)
        if pob_match:
            cand_pob = pob_match.group(1).splitlines()[0]
            cand_pob = re.split(r"\b(?:Date|DOI|Father|Mother)\b", cand_pob, flags=re.IGNORECASE)[0]
            fields["place_of_birth"] = cand_pob.strip()

        # 7. Date of Issue
        doi_match = re.search(r"(?:Date\s*of\s*Issue|DOI|Issue\s*Date)[.:\s]*([0-3]?\d[/-][0-1]?\d[/-]\d{4})", raw_text, re.IGNORECASE)
        if doi_match:
            fields["date_of_issue"] = doi_match.group(1).replace("-", "/")

        # 8. Father's / Legal Guardian Name
        father_match = re.search(r"(?:Father\'?s?\s*Name|Father|Name\s*of\s*Father|Legal\s*Guardian)[.:\s]+([A-Za-z .]{3,35})", raw_text, re.IGNORECASE)
        if father_match:
            cand = father_match.group(1).splitlines()[0]
            cand = re.split(r"\b(?:Mother|DOB|Date|DOI)\b", cand, flags=re.IGNORECASE)[0]
            fields["father_name"] = re.sub(r"[^a-zA-Z .]", "", cand).strip()

        # 9. Mother's Name
        mother_match = re.search(r"(?:Mother\'?s?\s*Name|Mother|Name\s*of\s*Mother)[.:\s]+([A-Za-z .]{3,35})", raw_text, re.IGNORECASE)
        if mother_match:
            cand_m = mother_match.group(1).splitlines()[0]
            cand_m = re.split(r"\b(?:Father|DOB|Date|DOI)\b", cand_m, flags=re.IGNORECASE)[0]
            fields["mother_name"] = re.sub(r"[^a-zA-Z .]", "", cand_m).strip()

        # 10. Address
        addr_match = re.search(r"(?:Address)[:\s]+(.*?)(?=\bPIN\b|\bFile\b|\n\n|$)", raw_text, re.DOTALL | re.IGNORECASE)
        if addr_match:
            raw_addr = addr_match.group(1).replace("\n", " ").strip()
            fields["address"] = re.sub(r"\s+", " ", raw_addr)[:200].strip()

        return {
            "masked_id": masked_id,
            "fields": fields,
            "raw_text_summary": f"Passport parsed. Found: {list(fields.keys())}"
        }
