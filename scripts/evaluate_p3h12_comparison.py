"""
CONVELINA — P3H.12 Deterministic Identity Comparison & Normalization Benchmark
Evaluates the deterministic comparison engine across 60 ground-truth pairwise test cases.

Phenomena Evaluated:
1. Exact matches
2. Formatting differences (case, spaces, separators)
3. Transliteration variations (soundex/metaphone equivalents)
4. Initial expansion (single, multi, prefix/suffix initials)
5. Token reordering (surname transpositions)
6. Similar but different names (gender-differentiated pairs, phonetic lookalikes)
7. Truncated values (prefix and suffix truncation)
8. Conflicting dates (different year, month, day, year-only compatibility)
9. Missing values (insufficient data, empty fields)
10. Unsupported non-Latin scripts
11. Low-confidence OCR inputs (< 0.60 threshold)
12. Contradictory documents (conflicting gender, mismatched credentials)

Metrics Reported:
- False Acceptance Rate (FAR): Critical invariant: must be 0.00%
- False Rejection Rate (FRR)
- Precision, Recall, F1 for conflict detection
- Confusion Matrix across all 7 classification categories
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.identity_matching.classification import (
    NameMatchClassification,
    OverallIdentityClassification,
    ConflictSeverity,
)
from app.services.identity_matching.models import (
    DocumentIdentityProfile,
    FieldMatchResult,
    IdentityComparisonResult,
)
from app.services.identity_matching.engine import IdentityComparisonEngine


# 60 Ground-Truth Pairwise Test Cases
COMPARISON_BENCHMARK_DATASET = [
    # -------------------------------------------------------------
    # 1. Exact Matches (10 cases) - Expected: EXACT_MATCH, is_conflict=False
    # -------------------------------------------------------------
    {
        "id": "exact_01",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "pan"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "exact_02",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-08-25", "gender": "female", "doc_type": "passport"},
        "doc_b": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-08-25", "gender": "female", "doc_type": "aadhaar"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "exact_03",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "education_10th"},
        "doc_b": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "education_12th"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "exact_04",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "NEHA PATEL", "date_of_birth": "1992-02-03", "gender": "female", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "NEHA PATEL", "date_of_birth": "1992-02-03", "gender": "female", "doc_type": "pan"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "exact_05",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "LAKSHMI SUNDARAM", "date_of_birth": "1996-06-30", "gender": "female", "doc_type": "epf"},
        "doc_b": {"full_name": "LAKSHMI SUNDARAM", "date_of_birth": "1996-06-30", "gender": "female", "doc_type": "aadhaar"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "exact_06",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "VIKRAMADITYA SINGH", "date_of_birth": "1980-05-15", "gender": "male", "doc_type": "passport"},
        "doc_b": {"full_name": "VIKRAMADITYA SINGH", "date_of_birth": "1980-05-15", "gender": "male", "doc_type": "pan"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "exact_07",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "DEEPAK JOSHI", "date_of_birth": "1989-10-10", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "DEEPAK JOSHI", "date_of_birth": "1989-10-10", "gender": "male", "doc_type": "education_10th"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "exact_08",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "SUNITA SHARMA", "date_of_birth": "1975-03-22", "gender": "female", "doc_type": "pan"},
        "doc_b": {"full_name": "SUNITA SHARMA", "date_of_birth": "1975-03-22", "gender": "female", "doc_type": "aadhaar"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "exact_09",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "MOHAMMED ARIF", "date_of_birth": "1993-07-07", "gender": "male", "doc_type": "passport"},
        "doc_b": {"full_name": "MOHAMMED ARIF", "date_of_birth": "1993-07-07", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "exact_10",
        "phenomenon": "exact_match",
        "doc_a": {"full_name": "SURESH BABU", "date_of_birth": "1982-12-01", "gender": "male", "doc_type": "epf"},
        "doc_b": {"full_name": "SURESH BABU", "date_of_birth": "1982-12-01", "gender": "male", "doc_type": "pan"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },

    # -------------------------------------------------------------
    # 2. Formatting Differences (6 cases) - Expected: FORMATTING_DIFFERENCE, is_conflict=False
    # -------------------------------------------------------------
    {
        "id": "format_01",
        "phenomenon": "formatting_difference",
        "doc_a": {"full_name": "rajesh kumar verma", "date_of_birth": "12/04/1988", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "MALE", "doc_type": "pan"},
        "expected_conflict": False,
        "expected_classification": "FORMATTING_DIFFERENCE",
        "expected_review": False,
    },
    {
        "id": "format_02",
        "phenomenon": "formatting_difference",
        "doc_a": {"full_name": "  Priya   Ramanathan  ", "date_of_birth": "25-08-1994", "gender": "Female", "doc_type": "passport"},
        "doc_b": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994/08/25", "gender": "female", "doc_type": "aadhaar"},
        "expected_conflict": False,
        "expected_classification": "FORMATTING_DIFFERENCE",
        "expected_review": False,
    },
    {
        "id": "format_03",
        "phenomenon": "formatting_difference",
        "doc_a": {"full_name": "Anirban Banerjee.", "date_of_birth": "14.11.1985", "gender": "Male", "doc_type": "education_10th"},
        "doc_b": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "education_12th"},
        "expected_conflict": False,
        "expected_classification": "FORMATTING_DIFFERENCE",
        "expected_review": False,
    },
    {
        "id": "format_04",
        "phenomenon": "formatting_difference",
        "doc_a": {"full_name": "PATEL, NEHA", "date_of_birth": "03/02/1992", "gender": "FEMALE", "doc_type": "passport"},
        "doc_b": {"full_name": "NEHA PATEL", "date_of_birth": "1992-02-03", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "TOKEN_ORDER_VARIATION",
        "expected_review": True,
    },
    {
        "id": "format_05",
        "phenomenon": "formatting_difference",
        "doc_a": {"full_name": "K. RAMANATHAN", "date_of_birth": "1960", "gender": "male", "doc_type": "pan"},
        "doc_b": {"full_name": "K RAMANATHAN", "date_of_birth": "01/01/1960", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": False,
        "expected_classification": "FORMATTING_DIFFERENCE",
        "expected_review": False,
    },
    {
        "id": "format_06",
        "phenomenon": "formatting_difference",
        "doc_a": {"full_name": "SURESH CHANDRA-VERMA", "date_of_birth": "1958-09-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "SURESH CHANDRA VERMA", "date_of_birth": "12/09/1958", "gender": "male", "doc_type": "pan"},
        "expected_conflict": False,
        "expected_classification": "FORMATTING_DIFFERENCE",
        "expected_review": False,
    },

    # -------------------------------------------------------------
    # 3. Transliteration Variations (6 cases) - Expected: TRANSLITERATION_OR_VARIANT, is_conflict=True, review=False
    # -------------------------------------------------------------
    {
        "id": "translit_01",
        "phenomenon": "transliteration_variation",
        "doc_a": {"full_name": "RAJEEV KUMAR", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAJIV KUMAR", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "TRANSLITERATION_OR_VARIANT",
        "expected_review": False,
    },
    {
        "id": "translit_02",
        "phenomenon": "transliteration_variation",
        "doc_a": {"full_name": "LAKSHMI DEVI", "date_of_birth": "1975-06-15", "gender": "female", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "LAXMI DEVI", "date_of_birth": "1975-06-15", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "TRANSLITERATION_OR_VARIANT",
        "expected_review": False,
    },
    {
        "id": "translit_03",
        "phenomenon": "transliteration_variation",
        "doc_a": {"full_name": "POOJA SHARMA", "date_of_birth": "1993-11-20", "gender": "female", "doc_type": "education_10th"},
        "doc_b": {"full_name": "PUJA SHARMA", "date_of_birth": "1993-11-20", "gender": "female", "doc_type": "passport"},
        "expected_conflict": True,
        "expected_classification": "TRANSLITERATION_OR_VARIANT",
        "expected_review": False,
    },
    {
        "id": "translit_04",
        "phenomenon": "transliteration_variation",
        "doc_a": {"full_name": "ANIRBAN CHOUDHURY", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "ANIRBAN CHOWDHURY", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "epf"},
        "expected_conflict": True,
        "expected_classification": "TRANSLITERATION_OR_VARIANT",
        "expected_review": False,
    },
    {
        "id": "translit_05",
        "phenomenon": "transliteration_variation",
        "doc_a": {"full_name": "VIKAS YADAV", "date_of_birth": "1990-01-01", "gender": "male", "doc_type": "pan"},
        "doc_b": {"full_name": "WIKAS YADAV", "date_of_birth": "1990-01-01", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "TRANSLITERATION_OR_VARIANT",
        "expected_review": False,
    },
    {
        "id": "translit_06",
        "phenomenon": "transliteration_variation",
        "doc_a": {"full_name": "BHAVANA PATEL", "date_of_birth": "1992-02-03", "gender": "female", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "BHAWANA PATEL", "date_of_birth": "1992-02-03", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "TRANSLITERATION_OR_VARIANT",
        "expected_review": False,
    },

    # -------------------------------------------------------------
    # 4. Initial Expansion (6 cases) - Expected: INITIAL_AMBIGUITY, is_conflict=True, review=True
    # -------------------------------------------------------------
    {
        "id": "initial_01",
        "phenomenon": "initial_expansion",
        "doc_a": {"full_name": "K. RAMANATHAN", "date_of_birth": "1960-01-01", "gender": "male", "doc_type": "pan"},
        "doc_b": {"full_name": "KUMAR RAMANATHAN", "date_of_birth": "1960-01-01", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "INITIAL_AMBIGUITY",
        "expected_review": True,
    },
    {
        "id": "initial_02",
        "phenomenon": "initial_expansion",
        "doc_a": {"full_name": "S. K. VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "SURESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "passport"},
        "expected_conflict": True,
        "expected_classification": "INITIAL_AMBIGUITY",
        "expected_review": True,
    },
    {
        "id": "initial_03",
        "phenomenon": "initial_expansion",
        "doc_a": {"full_name": "RAMANATHAN K.", "date_of_birth": "1960-01-01", "gender": "male", "doc_type": "education_10th"},
        "doc_b": {"full_name": "RAMANATHAN KUMAR", "date_of_birth": "1960-01-01", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "INITIAL_AMBIGUITY",
        "expected_review": True,
    },
    {
        "id": "initial_04",
        "phenomenon": "initial_expansion",
        "doc_a": {"full_name": "A. SHARMA", "date_of_birth": "1990-09-19", "gender": "male", "doc_type": "pan"},
        "doc_b": {"full_name": "AARAV SHARMA", "date_of_birth": "1990-09-19", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "INITIAL_AMBIGUITY",
        "expected_review": True,
    },
    {
        "id": "initial_05",
        "phenomenon": "initial_expansion",
        "doc_a": {"full_name": "M. AJAY", "date_of_birth": "1995-12-12", "gender": "male", "doc_type": "education_12th"},
        "doc_b": {"full_name": "MUTHU AJAY", "date_of_birth": "1995-12-12", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "INITIAL_AMBIGUITY",
        "expected_review": True,
    },
    {
        "id": "initial_06",
        "phenomenon": "initial_expansion",
        "doc_a": {"full_name": "P. MEENAKSHI", "date_of_birth": "1994-08-25", "gender": "female", "doc_type": "passport"},
        "doc_b": {"full_name": "PRIYA MEENAKSHI", "date_of_birth": "1994-08-25", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "INITIAL_AMBIGUITY",
        "expected_review": True,
    },

    # -------------------------------------------------------------
    # 5. Token Reordering (4 cases) - Expected: TOKEN_ORDER_VARIATION, is_conflict=True, review=True
    # -------------------------------------------------------------
    {
        "id": "reorder_01",
        "phenomenon": "token_reordering",
        "doc_a": {"full_name": "VERMA RAJESH KUMAR", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "education_10th"},
        "doc_b": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "TOKEN_ORDER_VARIATION",
        "expected_review": True,
    },
    {
        "id": "reorder_02",
        "phenomenon": "token_reordering",
        "doc_a": {"full_name": "BANERJEE ANIRBAN", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "epf"},
        "doc_b": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "TOKEN_ORDER_VARIATION",
        "expected_review": True,
    },
    {
        "id": "reorder_03",
        "phenomenon": "token_reordering",
        "doc_a": {"full_name": "PATEL NEHA BHAVESH", "date_of_birth": "1992-02-03", "gender": "female", "doc_type": "passport"},
        "doc_b": {"full_name": "NEHA BHAVESH PATEL", "date_of_birth": "1992-02-03", "gender": "female", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "TOKEN_ORDER_VARIATION",
        "expected_review": True,
    },
    {
        "id": "reorder_04",
        "phenomenon": "token_reordering",
        "doc_a": {"full_name": "SHARMA S K", "date_of_birth": "1990-09-19", "gender": "male", "doc_type": "pan"},
        "doc_b": {"full_name": "S K SHARMA", "date_of_birth": "1990-09-19", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "TOKEN_ORDER_VARIATION",
        "expected_review": True,
    },

    # -------------------------------------------------------------
    # 6. Similar but Different Names (12 cases) - MUST NEVER AUTO-ACCEPT! FAR=0.00%
    # 8 Gender-differentiated pairs + 4 Phonetic lookalikes
    # -------------------------------------------------------------
    {
        "id": "similar_gender_01",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "DEEPAK", "date_of_birth": "1989-10-10", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "DEEPIKA", "date_of_birth": "1989-10-10", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,  # Definite mismatch
    },
    {
        "id": "similar_gender_02",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "KUMAR", "date_of_birth": "1991-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "KUMARI", "date_of_birth": "1991-04-12", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_gender_03",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "SUNIL", "date_of_birth": "1985-05-20", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "SUNITA", "date_of_birth": "1985-05-20", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_gender_04",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "ANIL", "date_of_birth": "1982-08-14", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "ANITA", "date_of_birth": "1982-08-14", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_gender_05",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "AMIT", "date_of_birth": "1993-01-11", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "AMITA", "date_of_birth": "1993-01-11", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_gender_06",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "VIJAY", "date_of_birth": "1987-03-30", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "VIJAYA", "date_of_birth": "1987-03-30", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_gender_07",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "AJAY", "date_of_birth": "1995-12-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "AJAYA", "date_of_birth": "1995-12-12", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_gender_08",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "RAMESH", "date_of_birth": "1978-07-25", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAMESHWARI", "date_of_birth": "1978-07-25", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_lookalike_09",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "RAJESH SHARMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAKESH SHARMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_lookalike_10",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "SURESH VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "NARESH VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_lookalike_11",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "DINESH PATEL", "date_of_birth": "1992-02-03", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "GANESH PATEL", "date_of_birth": "1992-02-03", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "similar_lookalike_12",
        "phenomenon": "similar_different_names",
        "doc_a": {"full_name": "K. SHARMA", "date_of_birth": "1990-09-19", "gender": "male", "doc_type": "pan"},
        "doc_b": {"full_name": "R. SHARMA", "date_of_birth": "1990-09-19", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },

    # -------------------------------------------------------------
    # 7. Truncated Values (4 cases) - Expected: POSSIBLE_TRUNCATION, is_conflict=True, review=True
    # -------------------------------------------------------------
    {
        "id": "trunc_01",
        "phenomenon": "truncated_values",
        "doc_a": {"full_name": "NARAYANASWAMY", "date_of_birth": "1970-01-01", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "NARAYANA", "date_of_birth": "1970-01-01", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "POSSIBLE_TRUNCATION",
        "expected_review": True,
    },
    {
        "id": "trunc_02",
        "phenomenon": "truncated_values",
        "doc_a": {"full_name": "MUTHUKUMAR", "date_of_birth": "1984-06-18", "gender": "male", "doc_type": "passport"},
        "doc_b": {"full_name": "MUTHU", "date_of_birth": "1984-06-18", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "POSSIBLE_TRUNCATION",
        "expected_review": True,
    },
    {
        "id": "trunc_03",
        "phenomenon": "truncated_values",
        "doc_a": {"full_name": "ARAVINDAN", "date_of_birth": "1991-03-24", "gender": "male", "doc_type": "education_10th"},
        "doc_b": {"full_name": "ARAVIND", "date_of_birth": "1991-03-24", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "POSSIBLE_TRUNCATION",
        "expected_review": True,
    },
    {
        "id": "trunc_04",
        "phenomenon": "truncated_values",
        "doc_a": {"full_name": "SWAMY", "date_of_birth": "1970-01-01", "gender": "male", "doc_type": "pan"},
        "doc_b": {"full_name": "NARAYANASWAMY", "date_of_birth": "1970-01-01", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "POSSIBLE_TRUNCATION",
        "expected_review": True,
    },

    # -------------------------------------------------------------
    # 8. Conflicting Dates (4 cases) - Expected: MISMATCH, is_conflict=True
    # -------------------------------------------------------------
    {
        "id": "date_01",
        "phenomenon": "conflicting_dates",
        "doc_a": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1990-04-12", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,  # Critical mismatch
    },
    {
        "id": "date_02",
        "phenomenon": "conflicting_dates",
        "doc_a": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-08-25", "gender": "female", "doc_type": "passport"},
        "doc_b": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-05-25", "gender": "female", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "date_03",
        "phenomenon": "conflicting_dates",
        "doc_a": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "education_10th"},
        "doc_b": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-20", "gender": "male", "doc_type": "education_12th"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "date_04",
        "phenomenon": "conflicting_dates",
        "doc_a": {"full_name": "NEHA PATEL", "date_of_birth": "1992-02-03", "gender": "female", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "NEHA PATEL", "date_of_birth": "1993-02-03", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },

    # -------------------------------------------------------------
    # 9. Missing Values (4 cases) - Expected: INSUFFICIENT_DATA / MANUAL_REVIEW
    # -------------------------------------------------------------
    {
        "id": "missing_01",
        "phenomenon": "missing_values",
        "doc_a": {"full_name": "", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "INSUFFICIENT_DATA",
        "expected_review": False,
    },
    {
        "id": "missing_02",
        "phenomenon": "missing_values",
        "doc_a": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": None, "gender": "female", "doc_type": "passport"},
        "doc_b": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-08-25", "gender": "female", "doc_type": "aadhaar"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "missing_03",
        "phenomenon": "missing_values",
        "doc_a": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-14", "gender": None, "doc_type": "education_10th"},
        "doc_b": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "education_12th"},
        "expected_conflict": False,
        "expected_classification": "EXACT_MATCH",
        "expected_review": False,
    },
    {
        "id": "missing_04",
        "phenomenon": "missing_values",
        "doc_a": {"full_name": "   ", "date_of_birth": None, "gender": None, "doc_type": "aadhaar"},
        "doc_b": {"full_name": "   ", "date_of_birth": None, "gender": None, "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "INSUFFICIENT_DATA",
        "expected_review": False,
    },

    # -------------------------------------------------------------
    # 10. Unsupported Non-Latin Scripts (2 cases) - Expected: UNRESOLVABLE_NEEDS_MANUAL_REVIEW
    # -------------------------------------------------------------
    {
        "id": "script_01",
        "phenomenon": "unsupported_scripts",
        "doc_a": {"full_name": "राजेश कुमार", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAJESH KUMAR", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "UNRESOLVABLE_NEEDS_MANUAL_REVIEW",
        "expected_review": True,
    },
    {
        "id": "script_02",
        "phenomenon": "unsupported_scripts",
        "doc_a": {"full_name": "ராஜேஷ் குமார்", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAJESH KUMAR", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "UNRESOLVABLE_NEEDS_MANUAL_REVIEW",
        "expected_review": True,
    },

    # -------------------------------------------------------------
    # 11. Low-Confidence OCR Inputs (3 cases) - Expected: LOW_CONFIDENCE_NEEDS_REVIEW
    # -------------------------------------------------------------
    {
        "id": "low_conf_01",
        "phenomenon": "low_confidence_ocr",
        "doc_a": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar", "ocr_confidence": 0.45},
        "doc_b": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "pan", "ocr_confidence": 0.90},
        "expected_conflict": True,
        "expected_classification": "LOW_CONFIDENCE_NEEDS_REVIEW",
        "expected_review": True,
    },
    {
        "id": "low_conf_02",
        "phenomenon": "low_confidence_ocr",
        "doc_a": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-08-25", "gender": "female", "doc_type": "passport", "ocr_confidence": 0.35},
        "doc_b": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-08-25", "gender": "female", "doc_type": "aadhaar", "ocr_confidence": 0.88},
        "expected_conflict": True,
        "expected_classification": "LOW_CONFIDENCE_NEEDS_REVIEW",
        "expected_review": True,
    },
    {
        "id": "low_conf_03",
        "phenomenon": "low_confidence_ocr",
        "doc_a": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "education_10th", "ocr_confidence": 0.52},
        "doc_b": {"full_name": "ANIRBAN BANERJEE", "date_of_birth": "1985-11-14", "gender": "male", "doc_type": "education_12th", "ocr_confidence": 0.55},
        "expected_conflict": True,
        "expected_classification": "LOW_CONFIDENCE_NEEDS_REVIEW",
        "expected_review": True,
    },

    # -------------------------------------------------------------
    # 12. Contradictory Documents (3 cases) - Expected: MISMATCH, is_conflict=True
    # -------------------------------------------------------------
    {
        "id": "contra_01",
        "phenomenon": "contradictory_documents",
        "doc_a": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "RAJESH KUMAR VERMA", "date_of_birth": "1988-04-12", "gender": "female", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "contra_02",
        "phenomenon": "contradictory_documents",
        "doc_a": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-08-25", "gender": "female", "doc_type": "passport"},
        "doc_b": {"full_name": "PRIYA RAMANATHAN", "date_of_birth": "1994-08-25", "gender": "male", "doc_type": "aadhaar"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
    {
        "id": "contra_03",
        "phenomenon": "contradictory_documents",
        "doc_a": {"full_name": "RAJESH SHARMA", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "aadhaar"},
        "doc_b": {"full_name": "MOHAMMED ALI", "date_of_birth": "1988-04-12", "gender": "male", "doc_type": "pan"},
        "expected_conflict": True,
        "expected_classification": "MISMATCH",
        "expected_review": False,
    },
]


def map_to_7_categories(classification: str) -> str:
    c = str(classification).upper()
    if "EXACT" in c:
        return "Exact match"
    elif "FORMAT" in c:
        return "Format-only difference"
    elif "TRANSLIT" in c or "LIKELY_SAME" in c:
        return "Transliteration variation"
    elif "INITIAL" in c or "TOKEN_ORDER" in c or "TRUNCATION" in c or "AMBIGUOUS" in c:
        return "Ambiguous match (requires review)"
    elif "MISMATCH" in c or "GENDER_AWARE" in c or "HIGH_RISK" in c:
        return "Conflict (different person)"
    elif "LOW_CONFIDENCE" in c:
        return "Low confidence (requires review)"
    elif "INSUFFICIENT" in c or "UNRESOLVABLE" in c:
        return "Insufficient data"
    return "Conflict (different person)"


def run_comparison_evaluation():
    print(f"Loaded {len(COMPARISON_BENCHMARK_DATASET)} ground-truth pairwise test cases.")
    print("Running Deterministic Identity Comparison Benchmark...")

    SEVEN_CLASSES = [
        "Exact match",
        "Format-only difference",
        "Transliteration variation",
        "Ambiguous match (requires review)",
        "Conflict (different person)",
        "Low confidence (requires review)",
        "Insufficient data",
    ]

    confusion_7x7 = {exp: {det: 0 for det in SEVEN_CLASSES} for exp in SEVEN_CLASSES}

    # Binary Conflict / Auto-Match Detection Metrics:
    # A pair is "Genuine Match" if expected_conflict is False and expected_review is False (exact match or format only)
    # A pair is "Genuine Conflict / Non-Match" if expected_conflict is True or expected_review is True
    # "Positive" = System detects conflict or requires review (blocks auto-acceptance)
    # "Negative" = System auto-accepts as verified match without review
    #
    # False Acceptance (FA) = System auto-accepts (verified_match=True, review=False) when it should NOT have.
    # False Rejection (FR) = System blocks / flags review when it is a genuine exact/format match.
    tp = 0  # Expected non-match/review, system blocked/flagged
    fp = 0  # Expected clean match, system blocked/flagged (False Rejection)
    tn = 0  # Expected clean match, system auto-accepted (verified match)
    fn = 0  # Expected non-match/review, system auto-accepted (FALSE ACCEPTANCE - CRITICAL SAFETY RISK!)

    results = []
    phenomenon_stats = {}

    for idx, test_case in enumerate(COMPARISON_BENCHMARK_DATASET):
        c_id = test_case["id"]
        phenomenon = test_case["phenomenon"]
        exp_conflict = test_case["expected_conflict"]
        exp_class = test_case["expected_classification"]
        exp_review = test_case["expected_review"]

        # Build DocumentIdentityProfile instances
        prof_a = DocumentIdentityProfile.from_extracted_fields(
            document_id=f"{c_id}_doc_a",
            document_type=test_case["doc_a"]["doc_type"],
            extracted_fields={
                "name": test_case["doc_a"]["full_name"],
                "full_name": test_case["doc_a"]["full_name"],
                "date_of_birth": test_case["doc_a"]["date_of_birth"],
                "gender": test_case["doc_a"]["gender"],
            },
            overall_ocr_confidence=test_case["doc_a"].get("ocr_confidence", 0.95),
        )

        prof_b = DocumentIdentityProfile.from_extracted_fields(
            document_id=f"{c_id}_doc_b",
            document_type=test_case["doc_b"]["doc_type"],
            extracted_fields={
                "name": test_case["doc_b"]["full_name"],
                "full_name": test_case["doc_b"]["full_name"],
                "date_of_birth": test_case["doc_b"]["date_of_birth"],
                "gender": test_case["doc_b"]["gender"],
            },
            overall_ocr_confidence=test_case["doc_b"].get("ocr_confidence", 0.95),
        )

        comparison_result = IdentityComparisonEngine.compare_profiles(prof_a, prof_b)
        name_match = comparison_result.field_results.get("full_name")
        dob_match = comparison_result.field_results.get("date_of_birth")
        gender_match = comparison_result.field_results.get("gender")

        # Determine effective detected classification for the primary phenomenon under test
        if phenomenon == "conflicting_dates" and dob_match:
            raw_det_class = dob_match.classification.upper()
        elif phenomenon == "contradictory_documents" and gender_match and gender_match.is_conflict:
            raw_det_class = gender_match.classification.upper()
        elif name_match:
            raw_det_class = name_match.classification.upper()
        else:
            raw_det_class = comparison_result.overall_classification.value.upper()

        mapped_exp_class = map_to_7_categories(exp_class)
        mapped_det_class = map_to_7_categories(raw_det_class)
        confusion_7x7[mapped_exp_class][mapped_det_class] += 1

        # Determine system decision
        # Clean auto-acceptance: overall is EXACT_MATCH or FORMAT_ONLY_MATCH,
        # not requiring manual review, and having zero conflicting or ambiguous fields
        is_auto_accepted = (
            comparison_result.overall_classification in ["EXACT_MATCH", "FORMAT_ONLY_MATCH"]
            and not comparison_result.requires_manual_review
            and len(comparison_result.conflicting_fields) == 0
            and len(comparison_result.ambiguous_fields) == 0
        )
        is_blocked_or_flagged = not is_auto_accepted

        # Ground-truth expectation:
        # A pair is a "Clean Match" if exp_conflict is False and exp_review is False
        is_expected_clean_match = (not exp_conflict) and (not exp_review)

        if not is_expected_clean_match:
            if is_blocked_or_flagged:
                tp += 1
            else:
                fn += 1  # FALSE ACCEPTANCE! Auto-accepted an ambiguous or conflicting identity!
        else:
            if not is_blocked_or_flagged:
                tn += 1
            else:
                fp += 1  # FALSE REJECTION! Blocked or flagged a clean match!

        # Phenomenon Stats
        if phenomenon not in phenomenon_stats:
            phenomenon_stats[phenomenon] = {"total": 0, "correct_category": 0, "false_accept": 0, "false_reject": 0}
        p_stat = phenomenon_stats[phenomenon]
        p_stat["total"] += 1

        if mapped_det_class == mapped_exp_class:
            p_stat["correct_category"] += 1
        if (not is_expected_clean_match) and is_auto_accepted:
            p_stat["false_accept"] += 1
        if is_expected_clean_match and is_blocked_or_flagged:
            p_stat["false_reject"] += 1

        results.append({
            "id": c_id,
            "phenomenon": phenomenon,
            "expected_conflict": exp_conflict,
            "detected_conflict": not is_auto_accepted,
            "expected_classification": exp_class,
            "detected_classification": raw_det_class,
            "mapped_expected_7class": mapped_exp_class,
            "mapped_detected_7class": mapped_det_class,
            "is_auto_accepted": is_auto_accepted,
            "overall_classification": comparison_result.overall_classification,
            "requires_manual_review": comparison_result.requires_manual_review,
            "conflicting_fields": comparison_result.conflicting_fields,
            "ambiguous_fields": comparison_result.ambiguous_fields,
            "similarity": name_match.similarity_score if name_match else 1.0,
        })

    # Summary Metrics
    total = len(COMPARISON_BENCHMARK_DATASET)
    total_non_matches = sum(1 for c in COMPARISON_BENCHMARK_DATASET if c["expected_conflict"] or c["expected_review"])
    total_clean_matches = total - total_non_matches

    far = fn / max(total_non_matches, 1)  # False Acceptance Rate: Non-matches erroneously auto-accepted
    frr = fp / max(total_clean_matches, 1)  # False Rejection Rate: Clean matches erroneously rejected/flagged
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = (2 * precision * recall) / max(precision + recall, 1e-6)

    # Phenomenon breakdown
    p_summary = {}
    for p_name, st in phenomenon_stats.items():
        p_summary[p_name] = {
            "total_cases": st["total"],
            "category_accuracy": round(st["correct_category"] / st["total"], 4),
            "false_accepts": st["false_accept"],
            "false_rejects": st["false_reject"],
        }

    output_data = {
        "benchmark_metadata": {
            "version": "P3H.12",
            "total_cases": total,
            "clean_matches": total_clean_matches,
            "discrepancies_and_variations": total_non_matches,
            "phenomena_count": len(phenomenon_stats),
            "target_far": "0.00%",
        },
        "aggregate_metrics": {
            "total_evaluated": total,
            "false_acceptance_rate": round(far, 4),
            "false_rejection_rate": round(frr, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": {
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn,
            }
        },
        "seven_class_confusion_matrix": confusion_7x7,
        "by_phenomenon": p_summary,
        "cases": results,
    }

    out_path = Path(__file__).resolve().parent.parent / "benchmarks" / "p3h12" / "comparison_evaluation_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print("\n" + "=" * 82)
    print("CONVELINA P3H.12 DETERMINISTIC IDENTITY COMPARISON BENCHMARK RESULTS")
    print("=" * 82)
    print(f"Total Pairwise Cases Evaluated:   {total}")
    print(f"  - Genuine Matches:              {total_clean_matches}")
    print(f"  - Discrepancies / Ambiguities:  {total_non_matches}")
    print(f"False Acceptance Rate (FAR):      {far*100:.2f}%  (Must be 0.00% - Critical Safety Invariant)")
    print(f"False Rejection Rate (FRR):       {frr*100:.2f}%")
    print(f"Conflict Detection Precision:     {precision*100:.2f}%")
    print(f"Conflict Detection Recall:        {recall*100:.2f}%")
    print(f"Conflict Detection F1 Score:      {f1:.4f}")
    print("\nPhenomenon Breakdown:")
    for p_name, p_stat in p_summary.items():
        print(f"  - {p_name:<26}: 7-Class Match: {p_stat['category_accuracy']*100:5.1f}% | FA: {p_stat['false_accepts']} | FR: {p_stat['false_rejects']}")
    print("\n7-Class Confusion Matrix (Rows=Expected, Cols=Detected):")
    header = f"{'Expected \\ Detected':<34}" + "".join(f"{c[:10]:>11}" for c in SEVEN_CLASSES)
    print(header)
    print("-" * len(header))
    for exp_c in SEVEN_CLASSES:
        row = f"{exp_c:<34}" + "".join(f"{confusion_7x7[exp_c][det_c]:>11}" for det_c in SEVEN_CLASSES)
        print(row)
    print("=" * 82)
    print(f"Detailed comparison evaluation written to {out_path}")


if __name__ == "__main__":
    run_comparison_evaluation()
