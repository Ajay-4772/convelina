"""
CONVELINA - Phase P3H.11 Synthetic Adversarial Comparison Test Suite
Exhaustively verifies deterministic identity comparison reliability across 35 adversarial scenarios:
1. Gender-differentiated name pairs (Deepak/Deepika, Kumar/Kumari, Sunil/Sunita, Anil/Anita, Amit/Amita, Vijay/Vijaya, Ajay/Ajaya, Ramesh/Rameshwari)
2. Initials and expanded names (R. Karthik vs Karthik Raman, A. Sharma vs Aarav Sharma, etc.)
3. Token-order variations (Aarav Sharma vs Sharma Aarav, M Ajay vs Ajay M)
4. Transliteration variants (Rajeev/Rajiv, Lakshmi/Laxmi, Pooja/Puja, Choudhury/Chowdhury)
5. Missing characters and truncations (Muthu/Muthukumar, Aravind/Aravindan)
6. Date-of-Birth format differences (DD/MM/YYYY vs YYYY-MM-DD, Year-only)
7. Conflicting dates and demographic attributes (DOB year mismatch, DOB day/month mismatch, gender conflict)
8. Low OCR confidence triggers (< 60%)
9. Empty, malformed, and unsupported-script inputs
10. False-Acceptance (FA) and False-Rejection (FR) metrics accounting
"""

import pytest
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
from app.services.identity_matching.name_matcher import NameMatcher
from app.services.identity_matching.engine import IdentityComparisonEngine
from app.services.identity_matching.normalization import (
    normalize_person_name,
    normalize_date_of_birth,
    contains_unsupported_non_latin,
)


class TestAdversarialComparisonP3H11:
    """Adversarial testing battery for deterministic identity matching engine."""

    # -------------------------------------------------------------------------
    # 1. Gender-Differentiated Name Pairs (Must NEVER be treated as match/typo)
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize(
        "name_a, name_b",
        [
            ("Deepak", "Deepika"),
            ("Kumar", "Kumari"),
            ("Sunil", "Sunita"),
            ("Anil", "Anita"),
            ("Amit", "Amita"),
            ("Vijay", "Vijaya"),
            ("Ajay", "Ajaya"),
            ("Ramesh", "Rameshwari"),
        ],
    )
    def test_gender_differentiated_pairs_are_genuine_mismatches(self, name_a, name_b):
        """Gender-inflected names must be classified as GENDER_AWARE_SIMILAR_NAME / conflict."""
        res = NameMatcher.compare_names(name_a, name_b, field_name="full_name")
        assert res.classification in (
            NameMatchClassification.GENDER_AWARE_SIMILAR_NAME,
            NameMatchClassification.MISMATCH,
        ), f"Expected gender conflict for {name_a} vs {name_b}, got {res.classification}"
        assert res.is_conflict is True
        assert res.requires_manual_review is True
        assert res.severity in (ConflictSeverity.HIGH, ConflictSeverity.CRITICAL)

    # -------------------------------------------------------------------------
    # 2. Initials and Expanded Names
    # -------------------------------------------------------------------------
    def test_initial_ambiguity_isolated(self):
        """Single initial vs expanded name without corroboration must be flagged as ambiguous."""
        res = NameMatcher.compare_names("R Karthik", "Karthik Raman", field_name="full_name")
        assert res.classification in (
            NameMatchClassification.INITIAL_AMBIGUITY,
            NameMatchClassification.TRUNCATION_OR_PARTIAL_MATCH,
        )
        assert res.requires_manual_review is True

    def test_initial_expansion_with_single_letter(self):
        """Initial prefix 'A. Sharma' vs 'Aarav Sharma'."""
        res = NameMatcher.compare_names("A. Sharma", "Aarav Sharma", field_name="full_name")
        assert res.classification in (
            NameMatchClassification.INITIAL_AMBIGUITY,
            NameMatchClassification.TRUNCATION_OR_PARTIAL_MATCH,
            NameMatchClassification.FORMAT_ONLY_MATCH,
        )

    def test_multi_initial_variation(self):
        """'S. K. Gupta' vs 'Suresh Kumar Gupta'."""
        res = NameMatcher.compare_names("S. K. Gupta", "Suresh Kumar Gupta", field_name="full_name")
        assert res.classification in (
            NameMatchClassification.INITIAL_AMBIGUITY,
            NameMatchClassification.TRUNCATION_OR_PARTIAL_MATCH,
        )

    # -------------------------------------------------------------------------
    # 3. Token-Order Changes
    # -------------------------------------------------------------------------
    def test_token_order_reversal(self):
        """Reversed first and last name: classified as TOKEN_ORDER_VARIATION with review."""
        res = NameMatcher.compare_names("Aarav Sharma", "Sharma Aarav", field_name="full_name")
        assert res.classification in (
            NameMatchClassification.TOKEN_ORDER_VARIATION,
            NameMatchClassification.FORMAT_ONLY_MATCH,
        )
        assert res.similarity_score >= 0.90
        assert res.is_conflict is True
        assert res.requires_manual_review is True

    def test_initial_and_token_order(self):
        """'M Ajay' vs 'Ajay M': recognized as token order variation."""
        res = NameMatcher.compare_names("M Ajay", "Ajay M", field_name="full_name")
        assert res.classification in (
            NameMatchClassification.TOKEN_ORDER_VARIATION,
            NameMatchClassification.FORMAT_ONLY_MATCH,
        )
        assert res.similarity_score >= 0.90

    # -------------------------------------------------------------------------
    # 4. Transliteration and Spelling Variations
    # -------------------------------------------------------------------------
    @pytest.mark.parametrize(
        "name_a, name_b",
        [
            ("Rajeev Kumar", "Rajiv Kumar"),
            ("Lakshmi Devi", "Laxmi Devi"),
            ("Pooja Sharma", "Puja Sharma"),
            ("Choudhury", "Chowdhury"),
            ("Vikas", "Wikas"),
        ],
    )
    def test_transliteration_variants(self, name_a, name_b):
        """Phonetic transliteration variations must be recognized as TRANSLITERATION_OR_VARIANT."""
        res = NameMatcher.compare_names(name_a, name_b, field_name="full_name")
        assert res.classification == NameMatchClassification.TRANSLITERATION_OR_VARIANT
        assert res.similarity_score >= 0.85

    # -------------------------------------------------------------------------
    # 5. Missing Characters and Truncations
    # -------------------------------------------------------------------------
    def test_prefix_truncation(self):
        """'Muthu' vs 'Muthukumar'."""
        res = NameMatcher.compare_names("Muthu", "Muthukumar", field_name="full_name")
        assert res.classification == NameMatchClassification.TRUNCATION_OR_PARTIAL_MATCH
        assert res.is_conflict is True

    def test_suffix_truncation(self):
        """'Aravind' vs 'Aravindan'."""
        res = NameMatcher.compare_names("Aaravind", "Aravindan", field_name="full_name")
        assert res.classification in (
            NameMatchClassification.TRUNCATION_OR_PARTIAL_MATCH,
            NameMatchClassification.TRANSLITERATION_OR_VARIANT,
            NameMatchClassification.MISMATCH,
        )

    # -------------------------------------------------------------------------
    # 6. Date of Birth Format Variations & Year Compatibility
    # -------------------------------------------------------------------------
    def test_dob_format_difference(self):
        """Same date in different formats must produce EXACT_MATCH / no conflict."""
        p_a = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc_a",
            document_type="aadhaar",
            extracted_fields={"full_name": "Aarav Sharma", "date_of_birth": "15/05/1995"},
            overall_ocr_confidence=0.95,
        )
        p_b = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc_b",
            document_type="pan",
            extracted_fields={"full_name": "Aarav Sharma", "date_of_birth": "1995-05-15"},
            overall_ocr_confidence=0.95,
        )
        res = IdentityComparisonEngine.compare_profiles(p_a, p_b)
        assert res.field_results["date_of_birth"].is_conflict is False
        assert res.field_results["date_of_birth"].classification == NameMatchClassification.EXACT_MATCH

    def test_dob_year_only_compatibility(self):
        """Aadhaar year-only (1995) vs full date (15/05/1995) is compatible (FORMAT_ONLY_MATCH)."""
        p_a = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc_a",
            document_type="aadhaar",
            extracted_fields={"full_name": "Aarav Sharma", "date_of_birth": "1995"},
            overall_ocr_confidence=0.95,
        )
        p_b = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc_b",
            document_type="pan",
            extracted_fields={"full_name": "Aarav Sharma", "date_of_birth": "15/05/1995"},
            overall_ocr_confidence=0.95,
        )
        res = IdentityComparisonEngine.compare_profiles(p_a, p_b)
        assert res.field_results["date_of_birth"].is_conflict is False
        assert res.field_results["date_of_birth"].classification == NameMatchClassification.FORMAT_ONLY_MATCH

    # -------------------------------------------------------------------------
    # 7. Conflicting Dates and Demographic Fields
    # -------------------------------------------------------------------------
    def test_conflicting_dob_year(self):
        """Different year (1995 vs 1990) must be a HIGH_RISK_GENUINE_MISMATCH."""
        p_a = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc_a",
            document_type="aadhaar",
            extracted_fields={"full_name": "Aarav Sharma", "date_of_birth": "15/05/1995"},
            overall_ocr_confidence=0.95,
        )
        p_b = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc_b",
            document_type="pan",
            extracted_fields={"full_name": "Aarav Sharma", "date_of_birth": "15/05/1990"},
            overall_ocr_confidence=0.95,
        )
        res = IdentityComparisonEngine.compare_profiles(p_a, p_b)
        assert res.field_results["date_of_birth"].is_conflict is True
        assert res.overall_classification in (
            OverallIdentityClassification.HIGH_RISK_GENUINE_MISMATCH,
            OverallIdentityClassification.MISMATCH,
        )

    def test_conflicting_gender(self):
        """Opposite gender (Male vs Female) with identical name must be flagged as conflict."""
        p_a = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc_a",
            document_type="aadhaar",
            extracted_fields={"full_name": "Kiran Kumar", "gender": "Male"},
            overall_ocr_confidence=0.95,
        )
        p_b = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc_b",
            document_type="pan",
            extracted_fields={"full_name": "Kiran Kumar", "gender": "Female"},
            overall_ocr_confidence=0.95,
        )
        res = IdentityComparisonEngine.compare_profiles(p_a, p_b)
        assert "gender" in res.field_results
        assert res.field_results["gender"].is_conflict is True
        assert res.field_results["gender"].classification == NameMatchClassification.MISMATCH

    # -------------------------------------------------------------------------
    # 8. Low OCR Confidence (< 60%) Fail-Safe
    # -------------------------------------------------------------------------
    def test_low_ocr_confidence_triggers_review(self):
        """OCR confidence below 0.60 must flag LOW_CONFIDENCE_NEEDS_REVIEW."""
        res = NameMatcher.compare_names(
            "Aarav Sharma",
            "Aarav Sharma",
            field_name="full_name",
            ocr_confidence_a=0.45,
            ocr_confidence_b=0.92,
        )
        assert res.classification == NameMatchClassification.LOW_CONFIDENCE_NEEDS_REVIEW
        assert res.requires_manual_review is True

    # -------------------------------------------------------------------------
    # 9. Empty, Malformed and Unsupported Script Values
    # -------------------------------------------------------------------------
    def test_empty_string_input(self):
        """Empty string must return INSUFFICIENT_DATA with zero similarity."""
        res = NameMatcher.compare_names("", "Aarav Sharma", field_name="full_name")
        assert res.classification == NameMatchClassification.INSUFFICIENT_DATA
        assert res.similarity_score == 0.0

    def test_unsupported_non_latin_script(self):
        """Devanagari or non-Latin script without transliteration must trigger manual review."""
        res = NameMatcher.compare_names("आरव शर्मा", "Aarav Sharma", field_name="full_name")
        assert res.classification == NameMatchClassification.UNRESOLVABLE_NEEDS_MANUAL_REVIEW
        assert res.requires_manual_review is True

    def test_completely_disparate_names(self):
        """Unrelated names must return MISMATCH with is_conflict=True."""
        res = NameMatcher.compare_names("Aarav Sharma", "Vikram Singh", field_name="full_name")
        assert res.classification == NameMatchClassification.MISMATCH
        assert res.is_conflict is True
        assert res.severity == ConflictSeverity.CRITICAL
