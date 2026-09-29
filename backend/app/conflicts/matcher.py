import logging
from typing import Dict, Any, Optional, List
from rapidfuzz import fuzz
import jellyfish

from app.conflicts.normalizer import normalize_name, parse_and_normalize_date, normalize_gender

logger = logging.getLogger("consolith.conflicts.matcher")

class NameMatchResult:
    def __init__(
        self,
        category: str,
        similarity_score: float,
        explanation: str,
        is_conflict: bool,
        severity: Optional[str] = None,
        conflict_type: Optional[str] = None
    ):
        self.category = category  # EXACT_MATCH, TOKEN_REORDER, INITIALS_EXPANSION, MINOR_TYPO, POTENTIAL_MISMATCH, CONFIRMED_MISMATCH
        self.similarity_score = similarity_score
        self.explanation = explanation
        self.is_conflict = is_conflict
        self.severity = severity
        self.conflict_type = conflict_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "similarity_score": round(self.similarity_score, 2),
            "explanation": self.explanation,
            "is_conflict": self.is_conflict,
            "severity": self.severity,
            "conflict_type": self.conflict_type,
        }

def match_names(name_a: Optional[str], name_b: Optional[str]) -> NameMatchResult:
    """
    Executes layered comparison between two names:
    1. Exact string match
    2. Token set / permutation match
    3. Initials / abbreviation match
    4. Fuzzy string similarity (RapidFuzz token_sort_ratio)
    5. Phonetic analysis (Jellyfish Metaphone / Soundex)
    """
    if not name_a or not name_b:
        return NameMatchResult(
            category="INSUFFICIENT_DATA",
            similarity_score=0.0,
            explanation="One or both document records are missing name values.",
            is_conflict=False
        )

    norm_a, tokens_a = normalize_name(name_a)
    norm_b, tokens_b = normalize_name(name_b)

    if not norm_a or not norm_b:
        return NameMatchResult(
            category="INSUFFICIENT_DATA",
            similarity_score=0.0,
            explanation="Name values contain no comparable alphabetic characters.",
            is_conflict=False
        )

    # 1. Exact Normalized Match
    if norm_a == norm_b:
        return NameMatchResult(
            category="EXACT_MATCH",
            similarity_score=100.0,
            explanation=f"Names are an exact match ('{name_a}').",
            is_conflict=False
        )

    # 2. Token Set Permutation Match (e.g. 'Sharma Rohan' vs 'Rohan Sharma')
    if set(tokens_a) == set(tokens_b):
        return NameMatchResult(
            category="TOKEN_REORDER",
            similarity_score=98.0,
            explanation=f"Name tokens match exactly with transposed word order ('{name_a}' vs '{name_b}').",
            is_conflict=True,
            severity="low",
            conflict_type="format-only"
        )

    # 3. Initials / Abbreviation Match (e.g. 'A. Sharma' vs 'Ajay Sharma')
    # Check if surname matches and one name has single-character initials for given name
    if len(tokens_a) > 0 and len(tokens_b) > 0:
        # Compare last token (family name / surname)
        surname_match = (tokens_a[-1] == tokens_b[-1])
        if surname_match:
            # Check if remaining tokens are initials
            first_a = tokens_a[0]
            first_b = tokens_b[0]
            if (len(first_a) == 1 and first_b.startswith(first_a)) or (len(first_b) == 1 and first_a.startswith(first_b)):
                return NameMatchResult(
                    category="INITIALS_EXPANSION",
                    similarity_score=85.0,
                    explanation=f"Name uses initials vs expanded given name ('{name_a}' vs '{name_b}'). Manual evidence review recommended.",
                    is_conflict=True,
                    severity="medium",
                    conflict_type="unresolvable-needs-evidence"
                )

    # 4. RapidFuzz String & Token Similarity
    sort_ratio = fuzz.token_sort_ratio(norm_a, norm_b)
    std_ratio = fuzz.ratio(norm_a, norm_b)
    best_score = max(sort_ratio, std_ratio)

    # 5. Phonetic Metaphone analysis
    meta_a = jellyfish.metaphone(norm_a)
    meta_b = jellyfish.metaphone(norm_b)
    phonetic_match = (meta_a == meta_b and len(meta_a) > 2)

    # Classify based on score thresholds
    if best_score >= 90.0:
        # High similarity typo or OCR artifact (e.g. 'Vikram' vs 'Vikramm')
        return NameMatchResult(
            category="MINOR_TYPO",
            similarity_score=float(best_score),
            explanation=f"High string similarity ({best_score:.1f}%), likely minor typo or OCR character artifact ('{name_a}' vs '{name_b}').",
            is_conflict=True,
            severity="low",
            conflict_type="format-only"
        )
    elif phonetic_match or best_score >= 75.0:
        # Potential phonetic variant (e.g. 'Choudhary' vs 'Chowdhury')
        desc = f"Phonetic match with {best_score:.1f}% string similarity ('{name_a}' vs '{name_b}')."
        if phonetic_match:
            desc += " Sounds phonetically identical under Metaphone encoding."
        return NameMatchResult(
            category="POTENTIAL_MISMATCH",
            similarity_score=float(best_score),
            explanation=desc,
            is_conflict=True,
            severity="medium",
            conflict_type="unresolvable-needs-evidence"
        )
    else:
        # Genuine name discrepancy
        return NameMatchResult(
            category="CONFIRMED_MISMATCH",
            similarity_score=float(best_score),
            explanation=f"Substantial name discrepancy ({best_score:.1f}% similarity): '{name_a}' vs '{name_b}'.",
            is_conflict=True,
            severity="critical",
            conflict_type="genuine-mismatch"
        )

class DateMatchResult:
    def __init__(
        self,
        category: str,
        explanation: str,
        is_conflict: bool,
        severity: Optional[str] = None,
        conflict_type: Optional[str] = None
    ):
        self.category = category
        self.explanation = explanation
        self.is_conflict = is_conflict
        self.severity = severity
        self.conflict_type = conflict_type

def match_dates_of_birth(date_a: Optional[str], date_b: Optional[str]) -> DateMatchResult:
    """
    Compares two dates of birth:
    - Validates standard DD/MM/YYYY dates
    - Handles Year-only records (common in older Aadhaar cards)
    - Distinguishes missing/invalid from conflicts
    """
    std_a, y_a, m_a, d_a, status_a = parse_and_normalize_date(date_a)
    std_b, y_b, m_b, d_b, status_b = parse_and_normalize_date(date_b)

    # Missing or invalid checks
    if status_a == "MISSING" or status_b == "MISSING":
        return DateMatchResult(
            category="MISSING_DATA",
            explanation="Date of birth is not recorded in one of the documents.",
            is_conflict=False
        )

    if status_a == "INVALID" or status_b == "INVALID":
        return DateMatchResult(
            category="INVALID_DATE",
            explanation=f"One of the dates could not be parsed as a valid calendar date ('{date_a}' vs '{date_b}').",
            is_conflict=True,
            severity="medium",
            conflict_type="unresolvable-needs-evidence"
        )

    # Year only compatibility (e.g. Aadhaar Year of Birth 1988 vs Passport 12/03/1988)
    if status_a == "YEAR_ONLY" or status_b == "YEAR_ONLY":
        if y_a == y_b:
            return DateMatchResult(
                category="COMPATIBLE_YEAR",
                explanation=f"Birth year matches ({y_a}). One document provides year-only while the other includes day and month.",
                is_conflict=True,
                severity="low",
                conflict_type="format-only"
            )
        else:
            return DateMatchResult(
                category="YEAR_MISMATCH",
                explanation=f"Birth year mismatch: {y_a} vs {y_b}.",
                is_conflict=True,
                severity="critical",
                conflict_type="genuine-mismatch"
            )

    # Full dates comparison
    if std_a == std_b:
        return DateMatchResult(
            category="EXACT_MATCH",
            explanation=f"Date of birth matches exactly ({std_a}).",
            is_conflict=False
        )

    # Same year and month, different day
    if y_a == y_b and m_a == m_b and d_a != d_b:
        return DateMatchResult(
            category="DAY_MISMATCH",
            explanation=f"Date of birth differs by day in the same month/year: '{date_a}' vs '{date_b}'.",
            is_conflict=True,
            severity="high",
            conflict_type="genuine-mismatch"
        )

    # Same year, different month/day
    if y_a == y_b:
        return DateMatchResult(
            category="MONTH_DAY_MISMATCH",
            explanation=f"Date of birth differs in day/month within year {y_a}: '{date_a}' vs '{date_b}'.",
            is_conflict=True,
            severity="high",
            conflict_type="genuine-mismatch"
        )

    # Complete mismatch (different years)
    return DateMatchResult(
        category="FULL_MISMATCH",
        explanation=f"Date of birth discrepancy: '{date_a}' ({std_a}) vs '{date_b}' ({std_b}).",
        is_conflict=True,
        severity="critical",
        conflict_type="genuine-mismatch"
    )

def match_gender(gender_a: Optional[str], gender_b: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Compares gender declarations across documents.
    """
    g_a = normalize_gender(gender_a)
    g_b = normalize_gender(gender_b)

    if not g_a or not g_b:
        return None

    if g_a == g_b:
        return None  # No conflict

    return {
        "is_conflict": True,
        "conflict_type": "genuine-mismatch",
        "severity": "high",
        "category": "GENDER_MISMATCH",
        "similarity_score": 0.0,
        "explanation": f"Gender declared as '{g_a}' in one document and '{g_b}' in another."
    }
