"""
CONVELINA - Deterministic, Explainable & Gender-Aware Name Matcher
Implements conservative, ambiguity-aware identity name comparison.
Guarantees gender-pair false positive protection, initial ambiguity detection,
transliteration recognition, truncation classification, and OCR fail-safes.
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Set
from rapidfuzz import fuzz
import jellyfish

from app.services.identity_matching.classification import NameMatchClassification, ConflictSeverity
from app.services.identity_matching.models import FieldMatchResult
from app.services.identity_matching.normalization import (
    normalize_person_name,
    contains_unsupported_non_latin,
)

# Explicit gendered name pairs that must NEVER be treated as typos or matches
GENDERED_DISTINCT_PAIRS: Set[Tuple[str, str]] = {
    ("deepak", "deepika"),
    ("deepika", "deepak"),
    ("kumar", "kumari"),
    ("kumari", "kumar"),
    ("sunil", "sunita"),
    ("sunita", "sunil"),
    ("anil", "anita"),
    ("anita", "anil"),
    ("amit", "amita"),
    ("amita", "amit"),
    ("suresh", "suresha"),
    ("suresha", "suresh"),
    ("ramesh", "rameshwari"),
    ("rameshwari", "ramesh"),
    ("vijay", "vijaya"),
    ("vijaya", "vijay"),
    ("ajay", "ajaya"),
    ("ajaya", "ajay"),
}

# Common Indic transliteration / spelling equivalence rules
TRANSLITERATION_MAP = [
    (r"eev\b", "iv"),
    (r"ee", "i"),
    (r"oo", "u"),
    (r"x", "ksh"),
    (r"dhary\b", "dhury"),
    (r"dhury\b", "dhary"),
    (r"sh", "s"),
    (r"th", "t"),
    (r"bh", "b"),
    (r"dh", "d"),
    (r"gh", "g"),
    (r"kh", "k"),
    (r"ph", "f"),
    (r"^b", "v"),
    (r"v", "w"),
]


def apply_indic_transliteration_folding(token: str) -> str:
    """Folds common Indian phonetic and regional transliteration variations to a canonical token."""
    res = token.lower()
    for pattern, replacement in TRANSLITERATION_MAP:
        res = re.sub(pattern, replacement, res)
    return res


def is_gender_differentiated_pair(token_a: str, token_b: str) -> bool:
    """
    Detects if two tokens represent gender-differentiated names that must be protected
    against fuzzy matching false positives.
    """
    t_a, t_b = token_a.lower(), token_b.lower()

    if (t_a, t_b) in GENDERED_DISTINCT_PAIRS:
        return True

    # Suffix-based gender inflection detection:
    # 1. -ak vs -ika (e.g. Deepak / Deepika, Tilak / Tilika)
    if (t_a.endswith("ak") and t_b == t_a[:-2] + "ika") or (t_b.endswith("ak") and t_a == t_b[:-2] + "ika"):
        return True

    # 2. -il vs -ita (e.g. Sunil / Sunita, Anil / Anita)
    if (t_a.endswith("il") and t_b == t_a[:-2] + "ita") or (t_b.endswith("il") and t_a == t_b[:-2] + "ita"):
        return True

    # 3. -ar vs -ari (e.g. Kumar / Kumari)
    if (t_a.endswith("ar") and t_b == t_a + "i") or (t_b.endswith("ar") and t_a == t_b + "i"):
        return True

    # 4. -esh vs -eshwari (e.g. Ramesh / Rameshwari, Suresh / Sureshwari)
    if (t_a.endswith("esh") and t_b == t_a + "wari") or (t_b.endswith("esh") and t_a == t_b + "wari"):
        return True

    return False


def is_transliteration_variant(token_a: str, token_b: str) -> bool:
    """Checks if two tokens match under Indic transliteration folding."""
    folded_a = apply_indic_transliteration_folding(token_a)
    folded_b = apply_indic_transliteration_folding(token_b)
    if folded_a == folded_b and len(folded_a) > 2:
        return True

    # Metaphone check for transliterations
    meta_a = jellyfish.metaphone(token_a)
    meta_b = jellyfish.metaphone(token_b)
    if meta_a == meta_b and len(meta_a) >= 3:
        # Rapidfuzz check to prevent phonetically similar but different words
        ratio = fuzz.ratio(token_a, token_b)
        if ratio >= 70.0:
            return True

    return False


def is_truncation_or_prefix(token_a: str, token_b: str) -> Tuple[bool, Optional[str]]:
    """
    Detects if one token is an exact prefix truncation of the other (e.g. 'Muthu' vs 'Muthukumar').
    Returns (is_truncation, suffix_diff).
    """
    t_a, t_b = token_a.lower(), token_b.lower()
    if t_a == t_b:
        return False, None

    if len(t_a) >= 3 and t_b.startswith(t_a):
        suffix = t_b[len(t_a):]
        if len(suffix) >= 2:
            return True, suffix
    elif len(t_b) >= 3 and t_a.startswith(t_b):
        suffix = t_a[len(t_b):]
        if len(suffix) >= 2:
            return True, suffix

    return False, None


class NameMatcher:
    """
    Deterministic Ambiguity and Gender-Aware Name Matcher.
    Executes layered comparison and returns an explainable FieldMatchResult.
    """

    @classmethod
    def compare_names(
        cls,
        name_a: Optional[str],
        name_b: Optional[str],
        field_name: str = "full_name",
        ocr_confidence_a: float = 1.0,
        ocr_confidence_b: float = 1.0,
    ) -> FieldMatchResult:
        """
        Compares two personal names deterministically and produces an explainable classification.
        """
        raw_a = name_a.strip() if name_a else None
        raw_b = name_b.strip() if name_b else None

        # Fail-Safe 1: Missing or Empty Input
        if not raw_a or not raw_b:
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized="",
                value_b_normalized="",
                classification=NameMatchClassification.INSUFFICIENT_DATA,
                similarity_score=0.0,
                confidence_score=0.0,
                is_conflict=False,
                severity=ConflictSeverity.LOW,
                requires_manual_review=False,
                explanation="One or both records are missing name values.",
                possible_causes=["Incomplete document extraction", "Field not present on credential"],
                recommended_action="Ensure credentials containing legal name are uploaded."
            )

        # Fail-Safe 2: OCR Quality Threshold (Threshold: 60%)
        min_ocr_conf = min(ocr_confidence_a, ocr_confidence_b)
        if min_ocr_conf < 0.60:
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=raw_a,
                value_b_normalized=raw_b,
                classification=NameMatchClassification.LOW_CONFIDENCE_NEEDS_REVIEW,
                similarity_score=0.0,
                confidence_score=min_ocr_conf,
                is_conflict=True,
                severity=ConflictSeverity.MEDIUM,
                requires_manual_review=True,
                explanation=f"OCR extraction confidence ({min_ocr_conf * 100:.1f}%) is below the safe threshold (60%). Image quality or blurriness prevents reliable automated matching.",
                possible_causes=["Blurry scan", "Low resolution photo", "Glare or watermarking on credential"],
                recommended_action="Re-upload a high-resolution, clear color scan or photograph."
            )

        # Fail-Safe 3: Non-Latin Script Detection
        if contains_unsupported_non_latin(raw_a) or contains_unsupported_non_latin(raw_b):
            # If both are exactly identical strings in native script, allow format match
            if raw_a == raw_b:
                return FieldMatchResult(
                    field_name=field_name,
                    value_a_raw=raw_a,
                    value_b_raw=raw_b,
                    value_a_normalized=raw_a,
                    value_b_normalized=raw_b,
                    classification=NameMatchClassification.EXACT_MATCH,
                    similarity_score=1.0,
                    confidence_score=1.0,
                    is_conflict=False,
                    severity=ConflictSeverity.LOW,
                    requires_manual_review=False,
                    explanation="Names match identically in native script."
                )

            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=raw_a,
                value_b_normalized=raw_b,
                classification=NameMatchClassification.UNRESOLVABLE_NEEDS_MANUAL_REVIEW,
                similarity_score=0.0,
                confidence_score=0.5,
                is_conflict=True,
                severity=ConflictSeverity.HIGH,
                requires_manual_review=True,
                explanation="Document contains non-Latin (Indic or regional) script without verified Romanized counterpart. Automated cross-script reconciliation cannot safely infer identity without risk of error.",
                possible_causes=["Regional language credential", "Bilingual identity card"],
                recommended_action="Manual administrative inspection required to verify phonetic spelling in official records."
            )

        # Normalization
        norm_a, tokens_a, inits_a = normalize_person_name(raw_a)
        norm_b, tokens_b, inits_b = normalize_person_name(raw_b)

        if not norm_a or not norm_b:
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=norm_a,
                value_b_normalized=norm_b,
                classification=NameMatchClassification.INSUFFICIENT_DATA,
                similarity_score=0.0,
                confidence_score=0.0,
                is_conflict=False,
                severity=ConflictSeverity.LOW,
                requires_manual_review=False,
                explanation="Name fields contain no comparable alphabetic characters."
            )

        # Layer 1: Raw Exact Match
        if raw_a == raw_b:
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=norm_a,
                value_b_normalized=norm_b,
                classification=NameMatchClassification.EXACT_MATCH,
                similarity_score=1.0,
                confidence_score=1.0,
                is_conflict=False,
                severity=ConflictSeverity.LOW,
                requires_manual_review=False,
                explanation=f"Names are an exact identical match ('{raw_a}').",
                possible_causes=[],
                recommended_action="No correction needed."
            )

        # Layer 2: Format-Only Match (Differ only by case, spacing, punctuation, or fused initials)
        # e.g. "M Ajay" vs "M AJAY", "M. Ajay" vs "M Ajay", "Ajay   Kumar" vs "Ajay Kumar", "A.K. Sharma" vs "AK Sharma"
        if norm_a == norm_b or norm_a.replace(" ", "") == norm_b.replace(" ", ""):
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=norm_a,
                value_b_normalized=norm_b,
                classification=NameMatchClassification.FORMAT_ONLY_MATCH,
                similarity_score=1.0,
                confidence_score=0.98,
                is_conflict=False,
                severity=ConflictSeverity.LOW,
                requires_manual_review=False,
                explanation=f"Values differ only in capitalization, punctuation, spacing, or initial formatting ('{raw_a}' vs '{raw_b}'). Does not indicate a substantive identity discrepancy.",
                possible_causes=["Document-specific formatting conventions (e.g. PAN uppercase standards)", "Punctuation placement on initials", "Initial concatenation conventions"],
                recommended_action="Formatting difference only. Standardizing spelling format across all records before passport application is recommended but not mandatory."
            )

        # Layer 3: Gender-Aware Protection Check
        # CRITICAL SAFETY RULE: Never allow high fuzzy scores to treat gender-differentiated names as typos
        for t_a in tokens_a:
            for t_b in tokens_b:
                if is_gender_differentiated_pair(t_a, t_b):
                    return FieldMatchResult(
                        field_name=field_name,
                        value_a_raw=raw_a,
                        value_b_raw=raw_b,
                        value_a_normalized=norm_a,
                        value_b_normalized=norm_b,
                        classification=NameMatchClassification.MISMATCH,
                        similarity_score=0.25,
                        confidence_score=0.95,
                        is_conflict=True,
                        severity=ConflictSeverity.CRITICAL,
                        requires_manual_review=True,
                        explanation=f"Names differ by gender-differentiated forms ('{t_a.capitalize()}' vs '{t_b.capitalize()}'). Despite high textual similarity, these represent distinct individuals under statutory identification rules.",
                        possible_causes=["Different persons (e.g. brother/sister records uploaded together)", "Substantive clerical error during enrollment"],
                        recommended_action="Confirm that documents belong to the same citizen. If an error occurred, submit a formal statutory name correction affidavit."
                    )

        # Layer 4: Token-Order Variation (Exact token sets with different ordering)
        # e.g. "M Ajay" vs "Ajay M", "Sharma Rohan" vs "Rohan Sharma"
        if set(tokens_a) == set(tokens_b) and len(tokens_a) == len(tokens_b):
            is_initial_order = (len(inits_a) > 0 and len(inits_b) > 0)
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=norm_a,
                value_b_normalized=norm_b,
                classification=NameMatchClassification.TOKEN_ORDER_VARIATION,
                similarity_score=0.92,
                confidence_score=0.85 if is_initial_order else 0.75,
                is_conflict=True,
                severity=ConflictSeverity.LOW,
                requires_manual_review=True,  # Conservative: requires multi-field confirmation or review
                explanation=f"Name contains the identical tokens but in reversed/transposed order ('{raw_a}' vs '{raw_b}').",
                possible_causes=["South Indian initial-first vs initial-last convention", "Surname-first institutional ordering (e.g. CBSE / Board certificates)"],
                recommended_action="Check whether institutional guidelines require family name or initial first."
            )

        # Layer 5: Initial Ambiguity (Single-letter initial vs expanded full word)
        # e.g. "R Karthik" vs "Karthik Raman", "M Ajay" vs "Ajay Mohan"
        # Check if one name has an initial that matches the first letter of an extra word in the other name
        initial_expansion_detected, ambig_init, ambig_expanded = cls._check_initial_expansion(tokens_a, tokens_b)
        if initial_expansion_detected:
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=norm_a,
                value_b_normalized=norm_b,
                classification=NameMatchClassification.INITIAL_AMBIGUITY,
                similarity_score=0.68,
                confidence_score=0.65,
                is_conflict=True,
                severity=ConflictSeverity.MEDIUM,
                requires_manual_review=True,
                explanation=f"Initial '{ambig_init.upper()}' in one record could represent '{ambig_expanded.capitalize()}' in the other, but could also expand to an entirely different name. Cannot be confirmed without corroborating evidence.",
                possible_causes=["Initial expansion during passport or KYC registration", "Patronymic initial vs expanded father's name"],
                recommended_action="Submit supporting document showing full expansion of initials (e.g. birth certificate or 10th marksheet)."
            )

        # Layer 6: Truncation or Partial Name Match
        # e.g. "Muthu" vs "Muthukumar"
        trunc_detected, trunc_stem, trunc_full = cls._check_truncation(tokens_a, tokens_b)
        if trunc_detected:
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=norm_a,
                value_b_normalized=norm_b,
                classification=NameMatchClassification.TRUNCATION_OR_PARTIAL_MATCH,
                similarity_score=0.74,
                confidence_score=0.72,
                is_conflict=True,
                severity=ConflictSeverity.MEDIUM,
                requires_manual_review=True,
                explanation=f"Name appears as a truncated or partial stem ('{trunc_stem.capitalize()}' vs '{trunc_full.capitalize()}'). This represents a partial name variation rather than a typographical misspelling.",
                possible_causes=["Character limit truncation in employer or banking systems", "Colloquial shortened name used in enrollment"],
                recommended_action="Align truncated credential with primary identity document via Gazette notification or official change form."
            )

        # Layer 7: Transliteration / Regional Phonetic Variant
        # e.g. "Rajeev" vs "Rajiv", "Lakshmi" vs "Laxmi"
        if cls._check_transliteration(tokens_a, tokens_b):
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=norm_a,
                value_b_normalized=norm_b,
                classification=NameMatchClassification.TRANSLITERATION_OR_VARIANT,
                similarity_score=0.88,
                confidence_score=0.85,
                is_conflict=True,
                severity=ConflictSeverity.LOW,
                requires_manual_review=False,
                explanation=f"Names differ by standard Indian transliteration or phonetic spelling variation ('{raw_a}' vs '{raw_b}').",
                possible_causes=["Vowel length transliteration differences (ee/i, oo/u)", "Orthographic simplification (ksh/x)"],
                recommended_action="Acceptable under common procedural KYC standards. Align spelling during routine passport or Aadhaar updates."
            )

        # Layer 8: RapidFuzz Fuzzy String & Token Ratio Analysis
        sort_ratio = fuzz.token_sort_ratio(norm_a, norm_b)
        std_ratio = fuzz.ratio(norm_a, norm_b)
        best_ratio = max(sort_ratio, std_ratio)

        # If high similarity (>= 88%) without matching earlier rules, it is a minor typo
        if best_ratio >= 88.0:
            return FieldMatchResult(
                field_name=field_name,
                value_a_raw=raw_a,
                value_b_raw=raw_b,
                value_a_normalized=norm_a,
                value_b_normalized=norm_b,
                classification=NameMatchClassification.FORMAT_ONLY_MATCH if best_ratio >= 95.0 else NameMatchClassification.TRANSLITERATION_OR_VARIANT,
                similarity_score=float(best_ratio) / 100.0,
                confidence_score=0.80,
                is_conflict=True,
                severity=ConflictSeverity.LOW,
                requires_manual_review=False,
                explanation=f"Close textual similarity ({best_ratio:.1f}%): likely minor typographical error or OCR artifact ('{raw_a}' vs '{raw_b}').",
                possible_causes=["Single character OCR confusion (e.g. 1/I, 0/O)", "Typographical error during data entry"],
                recommended_action="Review and update clerical record."
            )

        # Layer 9: Confirmed Genuine Mismatch
        return FieldMatchResult(
            field_name=field_name,
            value_a_raw=raw_a,
            value_b_raw=raw_b,
            value_a_normalized=norm_a,
            value_b_normalized=norm_b,
            classification=NameMatchClassification.MISMATCH,
            similarity_score=float(best_ratio) / 100.0,
            confidence_score=0.92,
            is_conflict=True,
            severity=ConflictSeverity.CRITICAL,
            requires_manual_review=True,
            explanation=f"Substantial name mismatch ({best_ratio:.1f}% similarity): '{raw_a}' vs '{raw_b}'. Represents completely different identities.",
            possible_causes=["Documents belonging to different individuals", "Incorrect document uploaded"],
            recommended_action="Ensure documents uploaded belong strictly to the same individual."
        )

    @classmethod
    def _check_initial_expansion(cls, tokens_a: List[str], tokens_b: List[str]) -> Tuple[bool, str, str]:
        """
        Detects initial vs expanded word relationship between two token lists.
        e.g. ['r', 'karthik'] vs ['karthik', 'raman'] -> returns (True, 'r', 'raman')
        """
        inits_a = [t for t in tokens_a if len(t) == 1]
        inits_b = [t for t in tokens_b if len(t) == 1]

        # Case 1: tokens_a has an initial that tokens_b expands
        for init in inits_a:
            for full_tok in tokens_b:
                if len(full_tok) > 1 and full_tok.startswith(init):
                    # Check that common shared tokens exist (e.g. "karthik" is in both)
                    shared = set(tokens_a).intersection(set(tokens_b))
                    if len(shared) >= 1 and any(len(s) > 1 for s in shared):
                        return True, init, full_tok

        # Case 2: tokens_b has an initial that tokens_a expands
        for init in inits_b:
            for full_tok in tokens_a:
                if len(full_tok) > 1 and full_tok.startswith(init):
                    shared = set(tokens_a).intersection(set(tokens_b))
                    if len(shared) >= 1 and any(len(s) > 1 for s in shared):
                        return True, init, full_tok

        return False, "", ""

    @classmethod
    def _check_truncation(cls, tokens_a: List[str], tokens_b: List[str]) -> Tuple[bool, str, str]:
        """Detects if one non-initial token is an exact prefix of another."""
        for t_a in tokens_a:
            if len(t_a) <= 1:
                continue
            for t_b in tokens_b:
                if len(t_b) <= 1 or t_a == t_b:
                    continue
                is_trunc, _ = is_truncation_or_prefix(t_a, t_b)
                if is_trunc:
                    stem = t_a if len(t_a) < len(t_b) else t_b
                    full = t_b if len(t_b) > len(t_a) else t_a
                    return True, stem, full
        return False, "", ""

    @classmethod
    def _check_transliteration(cls, tokens_a: List[str], tokens_b: List[str]) -> bool:
        """Checks if tokens match under Indic transliteration folding."""
        if len(tokens_a) != len(tokens_b):
            return False

        # Sort tokens to handle arbitrary order
        sorted_a = sorted(tokens_a)
        sorted_b = sorted(tokens_b)

        all_match = True
        has_variant = False
        for a, b in zip(sorted_a, sorted_b):
            if a == b:
                continue
            if is_transliteration_variant(a, b):
                has_variant = True
            else:
                all_match = False
                break

        return all_match and has_variant
