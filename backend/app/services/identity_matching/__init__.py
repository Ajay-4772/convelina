"""
CONVELINA - Identity Matching & Cross-Document Reconciliation Package
"""

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
from app.services.identity_matching.normalization import (
    normalize_person_name,
    normalize_date_of_birth,
    normalize_gender_value,
    normalize_address_string,
    contains_unsupported_non_latin,
)
from app.services.identity_matching.name_matcher import (
    NameMatcher,
    is_gender_differentiated_pair,
    is_transliteration_variant,
    is_truncation_or_prefix,
)
from app.services.identity_matching.engine import IdentityComparisonEngine
from app.services.identity_matching.service import (
    DocumentComparisonService,
    map_p0_classification_to_conflict_db,
)

__all__ = [
    "NameMatchClassification",
    "OverallIdentityClassification",
    "ConflictSeverity",
    "DocumentIdentityProfile",
    "FieldMatchResult",
    "IdentityComparisonResult",
    "NameMatcher",
    "IdentityComparisonEngine",
    "DocumentComparisonService",
    "map_p0_classification_to_conflict_db",
    "normalize_person_name",
    "normalize_date_of_birth",
    "normalize_gender_value",
    "normalize_address_string",
    "contains_unsupported_non_latin",
    "is_gender_differentiated_pair",
    "is_transliteration_variant",
    "is_truncation_or_prefix",
]

