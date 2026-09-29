import logging
from typing import Dict, Any, List, Optional
from app.conflicts.matcher import match_names, match_dates_of_birth, match_gender

logger = logging.getLogger("consolith.conflicts.rules")

# Documents with full_name field
NAME_CAPABLE_DOCS = {"aadhaar", "pan", "passport", "education_10th", "education_12th", "epf_record"}

# Documents with date_of_birth field
DOB_CAPABLE_DOCS = {"aadhaar", "pan", "passport", "education_10th", "epf_record"}

# Documents with gender field
GENDER_CAPABLE_DOCS = {"aadhaar", "passport"}

# Documents with father_name field
FATHER_NAME_CAPABLE_DOCS = {"pan", "passport", "education_10th", "education_12th"}

def evaluate_document_pair(
    doc_a: Dict[str, Any],
    doc_b: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Evaluates two documents belonging to the same citizen and returns any detected discrepancies.
    Only compares mutually applicable, comparable fields.
    doc_a and doc_b are dictionaries containing:
    {
        'id': str,
        'document_type': str,
        'masked_id': str,
        'extracted_fields': dict
    }
    """
    detected_conflicts: List[Dict[str, Any]] = []

    type_a = doc_a.get("document_type", "").lower()
    type_b = doc_b.get("document_type", "").lower()
    fields_a = doc_a.get("extracted_fields") or {}
    fields_b = doc_b.get("extracted_fields") or {}

    # 1. Name Comparison
    if type_a in NAME_CAPABLE_DOCS and type_b in NAME_CAPABLE_DOCS:
        name_a = fields_a.get("full_name")
        name_b = fields_b.get("full_name")

        if name_a and name_b:
            name_result = match_names(name_a, name_b)
            if name_result.is_conflict:
                detected_conflicts.append({
                    "field_name": "full_name",
                    "value_a": name_a,
                    "value_b": name_b,
                    "conflict_type": name_result.conflict_type or "unresolvable-needs-evidence",
                    "severity": name_result.severity or "medium",
                    "comparison_method": "rapidfuzz_token_phonetic",
                    "similarity_score": name_result.similarity_score,
                    "description": name_result.explanation,
                })

    # 2. Date of Birth Comparison
    if type_a in DOB_CAPABLE_DOCS and type_b in DOB_CAPABLE_DOCS:
        # Check date_of_birth or year_of_birth
        dob_a = fields_a.get("date_of_birth") or fields_a.get("year_of_birth")
        dob_b = fields_b.get("date_of_birth") or fields_b.get("year_of_birth")

        if dob_a and dob_b:
            dob_result = match_dates_of_birth(dob_a, dob_b)
            if dob_result.is_conflict:
                detected_conflicts.append({
                    "field_name": "date_of_birth",
                    "value_a": str(dob_a),
                    "value_b": str(dob_b),
                    "conflict_type": dob_result.conflict_type or "genuine-mismatch",
                    "severity": dob_result.severity or "high",
                    "comparison_method": "date_normalization",
                    "similarity_score": 100.0 if dob_result.category == "COMPATIBLE_YEAR" else 0.0,
                    "description": dob_result.explanation,
                })

    # 3. Gender Comparison
    if type_a in GENDER_CAPABLE_DOCS and type_b in GENDER_CAPABLE_DOCS:
        gender_a = fields_a.get("gender")
        gender_b = fields_b.get("gender")

        if gender_a and gender_b:
            gender_result = match_gender(gender_a, gender_b)
            if gender_result and gender_result.get("is_conflict"):
                detected_conflicts.append({
                    "field_name": "gender",
                    "value_a": gender_a,
                    "value_b": gender_b,
                    "conflict_type": gender_result["conflict_type"],
                    "severity": gender_result["severity"],
                    "comparison_method": "categorical_gender",
                    "similarity_score": 0.0,
                    "description": gender_result["explanation"],
                })

    # 4. Father's Name Comparison
    if type_a in FATHER_NAME_CAPABLE_DOCS and type_b in FATHER_NAME_CAPABLE_DOCS:
        father_a = fields_a.get("father_name")
        father_b = fields_b.get("father_name")

        if father_a and father_b:
            father_result = match_names(father_a, father_b)
            if father_result.is_conflict:
                detected_conflicts.append({
                    "field_name": "father_name",
                    "value_a": father_a,
                    "value_b": father_b,
                    "conflict_type": father_result.conflict_type or "unresolvable-needs-evidence",
                    "severity": father_result.severity or "medium",
                    "comparison_method": "rapidfuzz_token_phonetic",
                    "similarity_score": father_result.similarity_score,
                    "description": f"Father's name: {father_result.explanation}",
                })

    # 5. Same-Document-Type Duplicate Identifier Conflict
    # e.g. User uploads two PAN cards or two Passports with different numbers
    if type_a == type_b and type_a not in ("education_10th", "education_12th", "other"):
        id_a = doc_a.get("masked_id")
        id_b = doc_b.get("masked_id")
        if id_a and id_b and id_a != id_b:
            detected_conflicts.append({
                "field_name": f"{type_a}_number",
                "value_a": id_a,
                "value_b": id_b,
                "conflict_type": "genuine-mismatch",
                "severity": "critical",
                "comparison_method": "identifier_exact",
                "similarity_score": 0.0,
                "description": f"Discrepancy in {type_a.upper()} identifier between two uploaded records ({id_a} vs {id_b}).",
            })

    return detected_conflicts
