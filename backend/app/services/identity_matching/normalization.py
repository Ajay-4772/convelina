"""
CONVELINA - Deterministic Normalization Pipeline
Normalizes names, dates of birth, genders, and addresses while strictly preserving original values.
Follows conservative name token preservation rules (never strips Kumari, Devi, Selvi, etc.).
"""

import re
from datetime import datetime
from typing import Tuple, List, Optional

# Only strip purely transactional honorific titles at the start of a name.
# NEVER include 'kumari', 'devi', 'selvi', 'begum', 'master' as these are frequently genuine given/family names in India.
STRICT_TITLES = {
    "mr", "mrs", "ms", "shri", "shree", "sri", "smt", "dr", "prof"
}

# Non-Latin Indic and Arabic Unicode block ranges:
# Devanagari (0900-097F), Bengali (0980-09FF), Gurmukhi (0A00-0A7F), Gujarati (0A80-0AFF),
# Oriya (0B00-0B7F), Tamil (0B80-0BFF), Telugu (0C00-0C7F), Kannada (0C80-0CFF),
# Malayalam (0D00-0D7F), Arabic/Urdu (0600-06FF)
NON_LATIN_REGEX = re.compile(r"[\u0900-\u0D7F\u0600-\u06FF]")

# 6-digit Indian PIN Code pattern (First digit 1-9)
PINCODE_REGEX = re.compile(r"\b([1-9][0-9]{5})\b")

# Date pattern matchers
TEXTUAL_MONTH_FORMATS = [
    "%d %b %Y", "%d-%b-%Y", "%d %B %Y", "%d-%B-%Y",
    "%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y"
]
NUMERIC_DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
    "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%y", "%d-%m-%y"
]


def contains_unsupported_non_latin(text_val: Optional[str]) -> bool:
    """Returns True if the text contains non-Latin scripts requiring manual review."""
    if not text_val:
        return False
    return bool(NON_LATIN_REGEX.search(str(text_val)))


def normalize_person_name(raw_name: Optional[str]) -> Tuple[str, List[str], List[str]]:
    """
    Deterministically normalizes a person's name while preserving all substantive tokens.
    Returns:
        (normalized_string, list_of_tokens, list_of_initials)

    Safety Rules:
    - Never strips 'Kumari', 'Devi', 'Selvi', or other given-name words.
    - Strips only unambiguous professional/formal salutations (Mr, Shri, Dr) if at token 0.
    - Isolates single-letter initials (e.g. 'M.', 'M', 'R.') for ambiguity checking.
    """
    if not raw_name or not str(raw_name).strip():
        return "", [], []

    text_clean = str(raw_name).strip()

    # 1. Normalize punctuation: Replace dots, commas, hyphens, and slashes with space
    # (e.g. "M. Ajay" -> "M  Ajay", "Sharma-Verma" -> "Sharma Verma")
    cleaned_chars = re.sub(r"[.,\-/_()|:;]", " ", text_clean)

    # 2. Strip non-alphanumeric except spaces
    cleaned_chars = re.sub(r"[^a-zA-Z\s]", " ", cleaned_chars)

    # 3. Collapse multiple whitespace and lowercase
    tokens = [t.lower() for t in cleaned_chars.split() if t.strip()]

    if not tokens:
        return "", [], []

    # 4. Strip title prefix only from the first token if present
    if tokens[0] in STRICT_TITLES and len(tokens) > 1:
        tokens = tokens[1:]

    # 5. Extract single-letter initials
    initials = [t for t in tokens if len(t) == 1]

    normalized_string = " ".join(tokens)
    return normalized_string, tokens, initials


def normalize_date_of_birth(raw_date: Optional[str]) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[int]]:
    """
    Parses and standardizes date of birth strings across formats.
    Returns:
        (standardized_date_str, year, month, day)
        standardized_date_str is either "YYYY-MM-DD" or "YYYY" (for year-only records).
    """
    if not raw_date or not str(raw_date).strip():
        return None, None, None, None

    cleaned = str(raw_date).strip()

    # Check for Year only (e.g. 1990)
    year_match = re.match(r"^\b(19\d{2}|20\d{2})\b$", cleaned)
    if year_match:
        year = int(year_match.group(1))
        return f"{year}", year, None, None

    # Try numeric date formats
    for fmt in NUMERIC_DATE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if 1900 <= dt.year <= datetime.utcnow().year + 1:
                return dt.strftime("%Y-%m-%d"), dt.year, dt.month, dt.day
        except ValueError:
            continue

    # Try textual month formats (e.g. 15-Aug-1995, 15 August 1995)
    for fmt in TEXTUAL_MONTH_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            if 1900 <= dt.year <= datetime.utcnow().year + 1:
                return dt.strftime("%Y-%m-%d"), dt.year, dt.month, dt.day
        except ValueError:
            continue

    return None, None, None, None


def normalize_gender_value(raw_gender: Optional[str]) -> Optional[str]:
    """
    Standardizes gender strings across English and Hindi documents.
    Returns 'Male', 'Female', or 'Transgender'.
    """
    if not raw_gender or not str(raw_gender).strip():
        return None

    val = str(raw_gender).strip().lower()
    if val in ("m", "male", "पुरुष", "purush"):
        return "Male"
    elif val in ("f", "female", "महिला", "mahila"):
        return "Female"
    elif val in ("t", "transgender", "other"):
        return "Transgender"
    return val.capitalize()


def normalize_address_string(raw_address: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalizes postal addresses and extracts 6-digit Indian PIN code.
    Returns (normalized_address, pincode).
    """
    if not raw_address or not str(raw_address).strip():
        return None, None

    addr = str(raw_address).strip()

    # Extract 6-digit Indian PIN code
    pincode = None
    pin_match = PINCODE_REGEX.search(addr)
    if pin_match:
        pincode = pin_match.group(1)

    # Standardize whitespace and casing
    cleaned = re.sub(r"[^a-zA-Z0-9\s,.-]", " ", addr.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned, pincode

