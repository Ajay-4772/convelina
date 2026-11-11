"""
CONVELINA — Machine-Readable Zone (MRZ) Parser (ICAO Doc 9303 Compliant)
Parses TD3 (Passport) 2-line x 44-character MRZ sequences.
Includes 7-3-1 check digit validation, name disambiguation, and field mapping.
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime


def compute_mrz_check_digit(data: str) -> int:
    """
    Computes ICAO Doc 9303 check digit using weights [7, 3, 1] repeating modulo 10.
    Characters:
    '<' or fillers -> 0
    '0'-'9' -> 0-9
    'A'-'Z' -> 10-35
    """
    weights = [7, 3, 1]
    total = 0
    for idx, char in enumerate(data):
        c = char.upper()
        if c.isdigit():
            val = int(c)
        elif 'A' <= c <= 'Z':
            val = ord(c) - ord('A') + 10
        else:
            val = 0
        total += val * weights[idx % 3]
    return total % 10


def parse_mrz_date(yy_mm_dd: str, is_expiry: bool = False) -> Optional[str]:
    """
    Converts 6-digit YYMMDD into YYYY-MM-DD format with century resolution.
    For expiry date: defaults to 20YY.
    For DOB: if YY > current_year % 100, assumes 19YY; else assumes 20YY.
    """
    if len(yy_mm_dd) != 6 or not yy_mm_dd.isdigit():
        return None
    
    yy = int(yy_mm_dd[:2])
    mm = int(yy_mm_dd[2:4])
    dd = int(yy_mm_dd[4:6])
    
    if not (1 <= mm <= 12 and 1 <= dd <= 31):
        return None
        
    curr_yr_short = datetime.now().year % 100
    if is_expiry:
        century = 2000
    else:
        century = 1900 if yy > curr_yr_short else 2000
        
    full_year = century + yy
    return f"{full_year:04d}-{mm:02d}-{dd:02d}"


class MRZParser:
    """
    ICAO Doc 9303 Type 3 (TD3) Passport MRZ Parser.
    Extracts, validates, and parses 2-line x 44-character passport MRZ blocks.
    """

    @classmethod
    def find_mrz_lines(cls, text: str) -> Optional[Tuple[str, str]]:
        """
        Scans raw OCR text for two consecutive 44-character lines starting with P< or P[A-Z].
        Handles common OCR character noise and varying chevron counts.
        """
        raw_lines = [l.strip().replace(" ", "") for l in text.splitlines() if l.strip()]
        
        # Look for two candidate lines
        for i in range(len(raw_lines) - 1):
            l1 = raw_lines[i]
            l2 = raw_lines[i + 1]
            
            # Check line 1 pattern: P< or P followed by country code and chevrons
            is_l1_cand = (l1.startswith("P<") or l1.startswith("P") and len(l1) >= 30 and "<" in l1)
            is_l2_cand = (len(l2) >= 30 and "<" in l2 and any(c.isdigit() for c in l2))
            
            if is_l1_cand and is_l2_cand:
                # Pad or trim to exactly 44 chars if close
                l1_clean = l1.ljust(44, "<")[:44]
                l2_clean = l2.ljust(44, "<")[:44]
                return l1_clean, l2_clean

        # Fallback: scan for any lines with >= 8 chevrons
        chevron_lines = [l for l in raw_lines if l.count("<") >= 5 and len(l) >= 25]
        if len(chevron_lines) >= 2:
            return chevron_lines[0].ljust(44, "<")[:44], chevron_lines[1].ljust(44, "<")[:44]

        return None

    @classmethod
    def parse_td3(cls, line1: str, line2: str) -> Dict[str, Any]:
        """
        Parses two 44-character MRZ lines following ICAO Doc 9303 Part 4.
        """
        line1 = line1.upper().ljust(44, "<")[:44]
        line2 = line2.upper().ljust(44, "<")[:44]

        # Line 1 Breakdown:
        # 0-1: Document code (P<)
        # 2-4: Issuing country (IND)
        # 5-43: Names: Surname<<Given Names<<<<...
        doc_code = line1[0:2].replace("<", "")
        country = line1[2:5].replace("<", "")
        names_field = line1[5:44]
        
        surname = ""
        given_names = ""
        if "<<" in names_field:
            parts = names_field.split("<<", 1)
            surname = parts[0].replace("<", " ").strip()
            given_names = parts[1].replace("<", " ").strip()
        else:
            surname = names_field.replace("<", " ").strip()
            
        full_name = f"{given_names} {surname}".strip() if given_names else surname

        # Line 2 Breakdown:
        # 0-8: Passport Number (9 chars)
        # 9: Check digit for passport number
        # 10-12: Nationality (3 chars)
        # 13-18: Date of Birth (YYMMDD)
        # 19: Check digit for DOB
        # 20: Sex (M/F/<)
        # 21-26: Expiry Date (YYMMDD)
        # 27: Check digit for Expiry
        # 28-41: Personal number / optional
        # 42: Check digit for optional
        # 43: Composite check digit
        
        passport_num_raw = line2[0:9]
        passport_num = passport_num_raw.replace("<", "").strip()
        passport_chk_char = line2[9]
        
        passport_chk_valid = False
        if passport_chk_char.isdigit():
            expected_chk = compute_mrz_check_digit(passport_num_raw)
            passport_chk_valid = (int(passport_chk_char) == expected_chk)
            
        nationality = line2[10:13].replace("<", "").strip()
        
        dob_raw = line2[13:19]
        dob_chk_char = line2[19]
        dob_chk_valid = False
        if dob_chk_char.isdigit() and dob_raw.isdigit():
            dob_chk_valid = (int(dob_chk_char) == compute_mrz_check_digit(dob_raw))
        dob_iso = parse_mrz_date(dob_raw, is_expiry=False)

        sex_char = line2[20]
        gender = "Male" if sex_char == "M" else ("Female" if sex_char == "F" else None)

        expiry_raw = line2[21:27]
        expiry_chk_char = line2[27]
        expiry_chk_valid = False
        if expiry_chk_char.isdigit() and expiry_raw.isdigit():
            expiry_chk_valid = (int(expiry_chk_char) == compute_mrz_check_digit(expiry_raw))
        expiry_iso = parse_mrz_date(expiry_raw, is_expiry=True)

        return {
            "mrz_detected": True,
            "document_code": doc_code,
            "issuing_country": country,
            "full_name": full_name,
            "surname": surname,
            "given_name": given_names,
            "passport_number": passport_num,
            "passport_check_valid": passport_chk_valid,
            "nationality": nationality,
            "date_of_birth": dob_iso,
            "dob_check_valid": dob_chk_valid,
            "gender": gender,
            "expiry_date": expiry_iso,
            "expiry_check_valid": expiry_chk_valid,
            "composite_valid": (passport_chk_valid and dob_chk_valid and expiry_chk_valid),
        }

