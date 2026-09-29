import re
from datetime import datetime
from typing import Optional, Tuple, List

# Indian title/honorific prefixes to strip for name comparison
NAME_PREFIXES = {
    "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "shri", "shree", "sri", 
    "smt", "smt.", "kumari", "km", "km.", "dr", "dr.", "master"
}

def normalize_name(raw_name: Optional[str]) -> Tuple[str, List[str]]:
    """
    Normalizes a person's name for comparison while preserving structural tokens.
    Returns (normalized_full_string, list_of_tokens).
    Preserves original string untouched in caller.
    """
    if not raw_name:
        return "", []

    # 1. Lowercase and replace non-alphanumeric characters (except whitespace) with space
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", raw_name.lower())
    
    # 2. Tokenize and collapse whitespace
    raw_tokens = [t.strip() for t in cleaned.split() if t.strip()]
    
    # 3. Strip honorific prefixes (e.g. Shri, Smt, Mr, Dr)
    filtered_tokens = [t for t in raw_tokens if t not in NAME_PREFIXES]
    
    if not filtered_tokens:
        filtered_tokens = raw_tokens

    normalized_string = " ".join(filtered_tokens)
    return normalized_string, filtered_tokens

def parse_and_normalize_date(raw_date: Optional[str]) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[int], str]:
    """
    Parses and normalizes dates extracted from identity documents.
    Returns:
    (standardized_date_str: YYYY-MM-DD or YYYY, year, month, day, status)
    status can be: 'VALID', 'YEAR_ONLY', 'INVALID', 'MISSING'
    """
    if not raw_date or not str(raw_date).strip():
        return None, None, None, None, "MISSING"

    cleaned = str(raw_date).strip().replace(".", "/").replace("-", "/")

    # Check for Year only (e.g. 1988)
    if re.match(r"^\b(19\d{2}|20\d{2})\b$", cleaned):
        year = int(cleaned)
        return f"{year}", year, None, None, "YEAR_ONLY"

    # Match DD/MM/YYYY or YYYY/MM/DD
    formats = [
        ("%d/%m/%Y", False),
        ("%d/%m/%y", False),
        ("%Y/%m/%d", False),
    ]

    for fmt, _ in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            # Reasonable date range validation (1900 to current year)
            current_year = datetime.utcnow().year
            if 1900 <= dt.year <= current_year:
                std_str = dt.strftime("%Y-%m-%d")
                return std_str, dt.year, dt.month, dt.day, "VALID"
        except ValueError:
            continue

    return None, None, None, None, "INVALID"

def normalize_gender(raw_gender: Optional[str]) -> Optional[str]:
    """
    Normalizes gender strings across English and Hindi documents.
    """
    if not raw_gender:
        return None
    val = raw_gender.strip().lower()
    if val in ("m", "male", "पुरुष", "purush"):
        return "Male"
    elif val in ("f", "female", "महिला", "mahila"):
        return "Female"
    elif val in ("t", "transgender", "other"):
        return "Transgender"
    return val.capitalize()
