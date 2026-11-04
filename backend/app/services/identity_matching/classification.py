"""
CONVELINA - Identity Matching Classification Taxonomy
Defines deterministic, explainable classification categories for individual fields
and multi-field identity comparisons across statutory documents.
"""

from enum import Enum


class NameMatchClassification(str, Enum):
    """Classifications for personal and familial name comparisons."""
    EXACT_MATCH = "EXACT_MATCH"
    FORMAT_ONLY_MATCH = "FORMAT_ONLY_MATCH"
    TOKEN_ORDER_VARIATION = "TOKEN_ORDER_VARIATION"
    INITIAL_AMBIGUITY = "INITIAL_AMBIGUITY"
    TRANSLITERATION_OR_VARIANT = "TRANSLITERATION_OR_VARIANT"
    TRUNCATION_OR_PARTIAL_MATCH = "TRUNCATION_OR_PARTIAL_MATCH"
    MISMATCH = "MISMATCH"
    GENDER_AWARE_SIMILAR_NAME = "GENDER_AWARE_SIMILAR_NAME"
    LOW_CONFIDENCE_NEEDS_REVIEW = "LOW_CONFIDENCE_NEEDS_REVIEW"
    UNRESOLVABLE_NEEDS_MANUAL_REVIEW = "UNRESOLVABLE_NEEDS_MANUAL_REVIEW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class OverallIdentityClassification(str, Enum):
    """Holistic classifications for cross-document identity reconciliation."""
    EXACT_MATCH = "EXACT_MATCH"
    FORMAT_ONLY_MATCH = "FORMAT_ONLY_MATCH"
    LIKELY_SAME_PERSON = "LIKELY_SAME_PERSON"
    AMBIGUOUS_NEEDS_REVIEW = "AMBIGUOUS_NEEDS_REVIEW"
    TRUNCATION_OR_PARTIAL_MATCH = "TRUNCATION_OR_PARTIAL_MATCH"
    LOW_CONFIDENCE_NEEDS_REVIEW = "LOW_CONFIDENCE_NEEDS_REVIEW"
    UNRESOLVABLE_NEEDS_MANUAL_REVIEW = "UNRESOLVABLE_NEEDS_MANUAL_REVIEW"
    MISMATCH = "MISMATCH"
    HIGH_RISK_GENUINE_MISMATCH = "HIGH_RISK_GENUINE_MISMATCH"


class ConflictSeverity(str, Enum):
    """Risk/severity indicator for statutory document discrepancies."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

