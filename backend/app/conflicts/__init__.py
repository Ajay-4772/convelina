from app.conflicts.engine import ConflictDetectionEngine
from app.conflicts.normalizer import (
    normalize_name,
    parse_and_normalize_date,
    normalize_gender,
)
from app.conflicts.matcher import (
    match_names,
    match_dates_of_birth,
    match_gender,
    NameMatchResult,
    DateMatchResult,
)
from app.conflicts.rules import evaluate_document_pair
from app.conflicts.schemas import (
    ConflictResponse,
    ConflictListResponse,
    ConflictReviewUpdate,
    ConflictDetectResponse,
)

# Alias for convenience
normalize_date = parse_and_normalize_date

__all__ = [
    "ConflictDetectionEngine",
    "normalize_name",
    "normalize_date",
    "parse_and_normalize_date",
    "normalize_gender",
    "match_names",
    "match_dates_of_birth",
    "match_gender",
    "NameMatchResult",
    "DateMatchResult",
    "evaluate_document_pair",
    "ConflictResponse",
    "ConflictListResponse",
    "ConflictReviewUpdate",
    "ConflictDetectResponse",
]
