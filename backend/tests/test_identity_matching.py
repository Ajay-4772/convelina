"""
CONVELINA - Phase P0 Identity Conflict Detection Regression Battery
Exhaustively tests:
1. Exact identical names
2. Case-only differences
3. Punctuation-only differences
4. Whitespace-only differences
5. Initial format variations (A.K. Sharma vs AK Sharma)
6. Initial vs expanded name ambiguity (R Karthik vs Karthik Raman)
7. Token-order variations (M Ajay vs Ajay M)
8. Transliteration variants (Rajeev vs Rajiv)
9. Transliteration variants (Lakshmi vs Laxmi)
10. Truncation / partial matches (Muthu vs Muthukumar)
11. Gender-aware distinction 1 (Deepak vs Deepika)
12. Gender-aware distinction 2 (Kumar vs Kumari)
13. Gender-aware distinction 3 (Sunil vs Sunita)
14. Low OCR confidence fail-safe (< 60%)
15. Non-Latin unsupported script fail-safe
16. Multi-field corroboration (Name variation + DOB + Father -> LIKELY_SAME_PERSON)
17. Multi-field initial expansion resolved by father's name
18. Conflicting Date of Birth -> HIGH_RISK_GENUINE_MISMATCH
19. Aadhaar Year-of-Birth compatibility (1995 vs 15/05/1995)
20. Preservation of raw OCR values and given-name honorific retention (Kumari, Devi, Selvi)
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
from app.services.identity_matching.name_matcher import (
    NameMatcher,
    is_gender_differentiated_pair,
)
from app.services.identity_matching.engine import IdentityComparisonEngine
from app.services.identity_matching.normalization import (
    normalize_person_name,
    normalize_date_of_birth,
    contains_unsupported_non_latin,
)


class TestIdentityMatchingP0Battery:
    """Rigorous 20-case regression battery for Phase P0 identity intelligence."""

    def test_case_01_exact_identical_names(self):
        """Case 1: Exact identical strings must return EXACT_MATCH with no review."""
        res = NameMatcher.compare_names("Ajay Kumar", "Ajay Kumar")
        assert res.classification == NameMatchClassification.EXACT_MATCH
        assert res.similarity_score == 1.0
        assert res.confidence_score == 1.0
        assert res.is_conflict is False
        assert res.requires_manual_review is False
        assert res.severity == ConflictSeverity.LOW

    def test_case_02_case_only_difference(self):
        """Case 2: Case differences (e.g. PAN uppercase) must return FORMAT_ONLY_MATCH."""
        res = NameMatcher.compare_names("M Ajay", "M AJAY")
        assert res.classification == NameMatchClassification.FORMAT_ONLY_MATCH
        assert res.similarity_score == 1.0
        assert res.is_conflict is False
        assert res.requires_manual_review is False

    def test_case_03_punctuation_only_difference(self):
        """Case 3: Punctuation differences on initials must return FORMAT_ONLY_MATCH."""
        res = NameMatcher.compare_names("M. Ajay", "M Ajay")
        assert res.classification == NameMatchClassification.FORMAT_ONLY_MATCH
        assert res.similarity_score == 1.0
        assert res.is_conflict is False
        assert res.requires_manual_review is False

    def test_case_04_whitespace_only_difference(self):
        """Case 4: Spacing and indentation differences must return FORMAT_ONLY_MATCH."""
        res = NameMatcher.compare_names("Ajay   Kumar", "Ajay Kumar")
        assert res.classification == NameMatchClassification.FORMAT_ONLY_MATCH
        assert res.similarity_score == 1.0
        assert res.is_conflict is False
        assert res.requires_manual_review is False

    def test_case_05_initial_format_variation(self):
        """Case 5: Initial format variations (e.g. A.K. Sharma vs AK Sharma) must return FORMAT_ONLY_MATCH."""
        res = NameMatcher.compare_names("A.K. Sharma", "AK Sharma")
        assert res.classification == NameMatchClassification.FORMAT_ONLY_MATCH
        assert res.similarity_score == 1.0
        assert res.is_conflict is False
        assert res.requires_manual_review is False

    def test_case_06_initial_vs_expanded_ambiguity(self):
        """Case 6: Initial vs expanded name in isolation must return INITIAL_AMBIGUITY and require review."""
        res = NameMatcher.compare_names("R Karthik", "Karthik Raman")
        assert res.classification == NameMatchClassification.INITIAL_AMBIGUITY
        assert res.is_conflict is True
        assert res.requires_manual_review is True
        assert res.severity == ConflictSeverity.MEDIUM
        assert "Initial" in res.explanation
        assert "corroborating" in res.explanation.lower() or "expansion" in res.explanation.lower()

    def test_case_07_token_order_variation_isolated(self):
        """Case 7: Token order variations (e.g. South Indian conventions) in isolation flag variation."""
        res = NameMatcher.compare_names("M Ajay", "Ajay M")
        assert res.classification == NameMatchClassification.TOKEN_ORDER_VARIATION
        assert res.is_conflict is True
        assert res.requires_manual_review is True
        assert res.similarity_score >= 0.90

    def test_case_08_transliteration_variant_eev_iv(self):
        """Case 8: Indian transliteration variation (Rajeev vs Rajiv) must be recognized."""
        res = NameMatcher.compare_names("Rajeev", "Rajiv")
        assert res.classification == NameMatchClassification.TRANSLITERATION_OR_VARIANT
        assert res.is_conflict is True
        assert res.severity == ConflictSeverity.LOW
        assert res.requires_manual_review is False

    def test_case_09_transliteration_variant_ksh_x(self):
        """Case 9: Orthographic variation (Lakshmi vs Laxmi) must be recognized."""
        res = NameMatcher.compare_names("Lakshmi", "Laxmi")
        assert res.classification == NameMatchClassification.TRANSLITERATION_OR_VARIANT
        assert res.is_conflict is True
        assert res.severity == ConflictSeverity.LOW
        assert res.requires_manual_review is False

    def test_case_10_truncation_or_partial_match(self):
        """Case 10: Name truncation (Muthu vs Muthukumar) must be flagged as partial match requiring review."""
        res = NameMatcher.compare_names("Muthu", "Muthukumar")
        assert res.classification == NameMatchClassification.TRUNCATION_OR_PARTIAL_MATCH
        assert res.is_conflict is True
        assert res.severity == ConflictSeverity.MEDIUM
        assert res.requires_manual_review is True
        assert "truncated" in res.explanation.lower() or "partial" in res.explanation.lower()

    def test_case_11_gender_aware_protection_deepak_deepika(self):
        """Case 11: Gender-differentiated pair (Deepak vs Deepika) MUST NOT be treated as a typo."""
        assert is_gender_differentiated_pair("deepak", "deepika") is True
        res = NameMatcher.compare_names("Deepak", "Deepika")
        assert res.classification == NameMatchClassification.MISMATCH
        assert res.is_conflict is True
        assert res.severity == ConflictSeverity.CRITICAL
        assert res.requires_manual_review is True
        assert "gender" in res.explanation.lower()

    def test_case_12_gender_aware_protection_kumar_kumari(self):
        """Case 12: Gender-differentiated pair (Kumar vs Kumari) must trigger CRITICAL mismatch."""
        assert is_gender_differentiated_pair("kumar", "kumari") is True
        res = NameMatcher.compare_names("Ajay Kumar", "Ajay Kumari")
        assert res.classification == NameMatchClassification.MISMATCH
        assert res.is_conflict is True
        assert res.severity == ConflictSeverity.CRITICAL
        assert res.requires_manual_review is True

    def test_case_13_gender_aware_protection_sunil_sunita(self):
        """Case 13: Gender-differentiated pair (Sunil vs Sunita) must trigger CRITICAL mismatch."""
        assert is_gender_differentiated_pair("sunil", "sunita") is True
        res = NameMatcher.compare_names("Sunil", "Sunita")
        assert res.classification == NameMatchClassification.MISMATCH
        assert res.is_conflict is True
        assert res.severity == ConflictSeverity.CRITICAL
        assert res.requires_manual_review is True

    def test_case_14_low_ocr_confidence_fail_safe(self):
        """Case 14: When OCR confidence < 60%, match must halt with LOW_CONFIDENCE_NEEDS_REVIEW."""
        res = NameMatcher.compare_names(
            name_a="Ajay Kumar",
            name_b="Ajay Kumar",
            ocr_confidence_a=0.52,  # Below 60%
            ocr_confidence_b=0.98,
        )
        assert res.classification == NameMatchClassification.LOW_CONFIDENCE_NEEDS_REVIEW
        assert res.is_conflict is True
        assert res.requires_manual_review is True
        assert "below the safe threshold" in res.explanation

    def test_case_15_non_latin_unsupported_script(self):
        """Case 15: Non-Latin Indic script without Romanized certified counterpart flags manual review."""
        assert contains_unsupported_non_latin("அஜய் குமார்") is True
        res = NameMatcher.compare_names("அஜய் குமார்", "Ajay Kumar")
        assert res.classification == NameMatchClassification.UNRESOLVABLE_NEEDS_MANUAL_REVIEW
        assert res.is_conflict is True
        assert res.requires_manual_review is True
        assert "non-latin" in res.explanation.lower() or "script" in res.explanation.lower()

    def test_case_16_multi_field_corroboration_resolves_token_order(self):
        """
        Case 16: Multi-field evidence reconciliation.
        Token order difference (M Ajay vs Ajay M) is resolved to LIKELY_SAME_PERSON
        when supported by matching Date of Birth and Father's Name.
        """
        doc1 = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc1",
            document_type="passport",
            extracted_fields={
                "full_name": "M Ajay",
                "date_of_birth": "1995-05-15",
                "father_name": "Muthukumar",
                "gender": "M",
            },
            overall_ocr_confidence=0.95,
        )
        doc2 = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc2",
            document_type="aadhaar",
            extracted_fields={
                "full_name": "Ajay M",
                "date_of_birth": "15/05/1995",
                "father_name": "Muthukumar",
                "gender": "Male",
            },
            overall_ocr_confidence=0.94,
        )

        comparison = IdentityComparisonEngine.compare_profiles(doc1, doc2)
        assert comparison.overall_classification == OverallIdentityClassification.LIKELY_SAME_PERSON
        assert comparison.requires_manual_review is False
        assert comparison.confidence_score >= 0.90
        assert "full_name" in comparison.matched_fields
        assert "date_of_birth" in comparison.matched_fields
        assert "father_name" in comparison.matched_fields

    def test_case_17_multi_field_initial_expansion_resolved_by_father_name(self):
        """
        Case 17: Initial expansion (R Karthik vs Karthik Raman) is resolved when
        the initial aligns with the verified father's name ('Raman').
        """
        doc1 = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc1",
            document_type="pan",
            extracted_fields={
                "full_name": "R Karthik",
                "father_name": "Raman",
                "date_of_birth": "1998-10-20",
            },
            overall_ocr_confidence=0.95,
        )
        doc2 = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc2",
            document_type="passport",
            extracted_fields={
                "full_name": "Karthik Raman",
                "father_name": "Raman",
                "date_of_birth": "20/10/1998",
            },
            overall_ocr_confidence=0.96,
        )

        comparison = IdentityComparisonEngine.compare_profiles(doc1, doc2)
        assert comparison.overall_classification == OverallIdentityClassification.LIKELY_SAME_PERSON
        assert comparison.requires_manual_review is False
        assert any("father" in ev.lower() for ev in comparison.evidence)

    def test_case_18_conflicting_dates_of_birth_high_risk(self):
        """Case 18: Conflicting Dates of Birth must flag HIGH_RISK_GENUINE_MISMATCH."""
        doc1 = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc1",
            document_type="aadhaar",
            extracted_fields={
                "full_name": "Ajay Kumar",
                "date_of_birth": "15/05/1995",
            },
        )
        doc2 = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc2",
            document_type="pan",
            extracted_fields={
                "full_name": "Ajay Kumar",
                "date_of_birth": "20/10/1998",
            },
        )

        comparison = IdentityComparisonEngine.compare_profiles(doc1, doc2)
        assert comparison.overall_classification == OverallIdentityClassification.HIGH_RISK_GENUINE_MISMATCH
        assert comparison.requires_manual_review is True
        assert "date_of_birth" in comparison.conflicting_fields

    def test_case_19_aadhaar_yob_only_compatibility(self):
        """Case 19: Aadhaar year-only records (1995) vs full date (15/05/1995) are compatible."""
        doc1 = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc1",
            document_type="aadhaar",
            extracted_fields={
                "full_name": "Ajay Kumar",
                "year_of_birth": "1995",
            },
        )
        doc2 = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc2",
            document_type="passport",
            extracted_fields={
                "full_name": "Ajay Kumar",
                "date_of_birth": "15/05/1995",
            },
        )

        comparison = IdentityComparisonEngine.compare_profiles(doc1, doc2)
        assert comparison.overall_classification in (
            OverallIdentityClassification.EXACT_MATCH,
            OverallIdentityClassification.FORMAT_ONLY_MATCH,
        )
        assert comparison.requires_manual_review is False
        dob_res = comparison.field_results.get("date_of_birth")
        assert dob_res is not None
        assert dob_res.is_conflict is False

    def test_case_20_raw_preservation_and_honorific_safety(self):
        """
        Case 20: Canonical DocumentIdentityProfile preserves raw OCR values untouched,
        and never strips genuine given-name components like Kumari, Devi, or Selvi.
        """
        raw_name = "Kumari Selvi M"
        profile = DocumentIdentityProfile.from_extracted_fields(
            document_id="doc1",
            document_type="marksheet",
            extracted_fields={
                "full_name": raw_name,
                "gender": "Female",
            },
        )

        # Raw value is preserved exactly
        assert profile.full_name_raw == raw_name

        # Given-name words are preserved in tokens
        norm_name, tokens, inits = normalize_person_name(raw_name)
        assert "kumari" in tokens
        assert "selvi" in tokens
        assert "m" in inits

        # Only transactional honorifics like 'Mr', 'Shri', 'Dr' are stripped from token 0
        norm_mr, tokens_mr, _ = normalize_person_name("Mr. Ajay Kumar")
        assert tokens_mr == ["ajay", "kumar"]
        assert "mr" not in tokens_mr

