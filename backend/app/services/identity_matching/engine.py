"""
CONVELINA - Multi-Field Identity Reconciliation Engine
Evaluates identity credentials holistically using multi-field corroborating evidence
(Full Name, Date of Birth, Father Name, Mother Name, Gender, Address).
Enforces fail-safe ambiguity logic and guarantees explainability.
"""

from typing import Dict, Any, List, Optional
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


class IdentityComparisonEngine:
    """
    Holistic cross-document reconciliation engine.
    Applies the multi-field evidence rule: independent corroborating fields
    (DOB, parent name) can resolve token-order and initial variations,
    while isolated ambiguous names are strictly held for manual review.
    """

    @classmethod
    def compare_profiles(
        cls,
        profile_a: DocumentIdentityProfile,
        profile_b: DocumentIdentityProfile,
    ) -> IdentityComparisonResult:
        field_results: Dict[str, FieldMatchResult] = {}
        matched_fields: List[str] = []
        conflicting_fields: List[str] = []
        ambiguous_fields: List[str] = []
        evidence: List[str] = []
        warnings: List[str] = []

        # 0. Global Fail-Safes: OCR Quality & Non-Latin Scripts
        min_ocr_conf = min(profile_a.overall_ocr_confidence, profile_b.overall_ocr_confidence)
        has_non_latin = profile_a.is_non_latin or profile_b.is_non_latin

        # 1. Primary Name Comparison
        name_res = NameMatcher.compare_names(
            name_a=profile_a.full_name_raw,
            name_b=profile_b.full_name_raw,
            field_name="full_name",
            ocr_confidence_a=profile_a.overall_ocr_confidence,
            ocr_confidence_b=profile_b.overall_ocr_confidence,
        )
        field_results["full_name"] = name_res
        if name_res.is_conflict and name_res.classification in (
            NameMatchClassification.MISMATCH,
            NameMatchClassification.GENDER_AWARE_SIMILAR_NAME,
        ):
            conflicting_fields.append("full_name")
            warnings.append(name_res.explanation)

        # 2. Date of Birth Comparison
        dob_res = cls._compare_dates_of_birth(profile_a, profile_b)
        if dob_res:
            field_results["date_of_birth"] = dob_res
            if dob_res.is_conflict:
                conflicting_fields.append("date_of_birth")
                warnings.append(dob_res.explanation)
            else:
                matched_fields.append("date_of_birth")
                evidence.append(dob_res.explanation)

        # 3. Father's Name Comparison
        if profile_a.father_name_raw and profile_b.father_name_raw:
            father_res = NameMatcher.compare_names(
                name_a=profile_a.father_name_raw,
                name_b=profile_b.father_name_raw,
                field_name="father_name",
                ocr_confidence_a=profile_a.overall_ocr_confidence,
                ocr_confidence_b=profile_b.overall_ocr_confidence,
            )
            field_results["father_name"] = father_res
            if father_res.is_conflict:
                if father_res.classification in (NameMatchClassification.MISMATCH, NameMatchClassification.GENDER_AWARE_SIMILAR_NAME):
                    conflicting_fields.append("father_name")
                    warnings.append(f"Father's name: {father_res.explanation}")
                else:
                    ambiguous_fields.append("father_name")
            else:
                matched_fields.append("father_name")
                evidence.append(f"Father's name matches ('{profile_a.father_name_raw}').")

        # 4. Mother's Name Comparison
        if profile_a.mother_name_raw and profile_b.mother_name_raw:
            mother_res = NameMatcher.compare_names(
                name_a=profile_a.mother_name_raw,
                name_b=profile_b.mother_name_raw,
                field_name="mother_name",
                ocr_confidence_a=profile_a.overall_ocr_confidence,
                ocr_confidence_b=profile_b.overall_ocr_confidence,
            )
            field_results["mother_name"] = mother_res
            if mother_res.is_conflict:
                conflicting_fields.append("mother_name")
            else:
                matched_fields.append("mother_name")
                evidence.append(f"Mother's name matches ('{profile_a.mother_name_raw}').")

        # 5. Gender Comparison
        if profile_a.gender_normalized and profile_b.gender_normalized:
            g_a = profile_a.gender_normalized
            g_b = profile_b.gender_normalized
            if g_a == g_b:
                matched_fields.append("gender")
                evidence.append(f"Gender declarations match ('{g_a}').")
            else:
                conflicting_fields.append("gender")
                gender_res = FieldMatchResult(
                    field_name="gender",
                    value_a_raw=profile_a.gender_raw,
                    value_b_raw=profile_b.gender_raw,
                    value_a_normalized=g_a,
                    value_b_normalized=g_b,
                    classification=NameMatchClassification.MISMATCH,
                    similarity_score=0.0,
                    confidence_score=1.0,
                    is_conflict=True,
                    severity=ConflictSeverity.HIGH,
                    requires_manual_review=True,
                    explanation=f"Gender declared differently: '{g_a}' vs '{g_b}'.",
                    possible_causes=["Clerical data entry discrepancy", "Gender transition record"],
                    recommended_action="Submit demographic correction request with supporting affidavit."
                )
                field_results["gender"] = gender_res
                warnings.append(gender_res.explanation)

        # 6. Address / Pincode Comparison
        if profile_a.pincode and profile_b.pincode:
            if profile_a.pincode == profile_b.pincode:
                matched_fields.append("pincode")
                evidence.append(f"Postal PIN code matches ({profile_a.pincode}).")
            else:
                # Differing PIN is not an identity conflict by itself (citizens move), but provides context
                evidence.append(f"Different postal PIN codes recorded ({profile_a.pincode} vs {profile_b.pincode}).")

        # -------------------------------------------------------------------------
        # MULTI-FIELD EVIDENCE SYNTHESIS
        # -------------------------------------------------------------------------

        # Check Fail-Safes First:
        if min_ocr_conf < 0.60:
            return IdentityComparisonResult(
                overall_classification=OverallIdentityClassification.LOW_CONFIDENCE_NEEDS_REVIEW,
                confidence_score=min_ocr_conf,
                requires_manual_review=True,
                matched_fields=matched_fields,
                conflicting_fields=conflicting_fields,
                ambiguous_fields=ambiguous_fields,
                field_results=field_results,
                evidence=evidence,
                explanation="Automated comparison halted: Document image quality or OCR extraction confidence is below safe operational threshold (60%).",
                warnings=["Low OCR confidence: manual verification of physical/original credential required."]
            )

        if has_non_latin and name_res.classification == NameMatchClassification.UNRESOLVABLE_NEEDS_MANUAL_REVIEW:
            return IdentityComparisonResult(
                overall_classification=OverallIdentityClassification.UNRESOLVABLE_NEEDS_MANUAL_REVIEW,
                confidence_score=0.50,
                requires_manual_review=True,
                matched_fields=matched_fields,
                conflicting_fields=conflicting_fields,
                ambiguous_fields=ambiguous_fields,
                field_results=field_results,
                evidence=evidence,
                explanation="One or more documents contain non-Latin native script without certified Romanized transliteration. Requires manual administrative review.",
                warnings=["Non-Latin script requires human review."]
            )

        # Severe Conflicting Fields (DOB or Gender mismatch)
        if "date_of_birth" in conflicting_fields or "gender" in conflicting_fields or name_res.classification in (NameMatchClassification.MISMATCH, NameMatchClassification.GENDER_AWARE_SIMILAR_NAME):
            return IdentityComparisonResult(
                overall_classification=OverallIdentityClassification.HIGH_RISK_GENUINE_MISMATCH if ("date_of_birth" in conflicting_fields or name_res.classification == NameMatchClassification.GENDER_AWARE_SIMILAR_NAME) else OverallIdentityClassification.MISMATCH,
                confidence_score=0.92,
                requires_manual_review=True,
                matched_fields=matched_fields,
                conflicting_fields=conflicting_fields,
                ambiguous_fields=ambiguous_fields,
                field_results=field_results,
                evidence=evidence,
                explanation="Substantive discrepancy detected across core identity attributes. Conflicting fields prevent automated identity reconciliation.",
                warnings=warnings
            )

        # Multi-Field Corroboration for Token Order Variation (e.g. M Ajay vs Ajay M)
        if name_res.classification == NameMatchClassification.TOKEN_ORDER_VARIATION:
            # Check if supporting evidence strongly corroborates identity
            has_dob_match = "date_of_birth" in matched_fields
            has_parent_match = "father_name" in matched_fields or "mother_name" in matched_fields

            if has_dob_match and has_parent_match:
                evidence.append("Token order variation in name is fully corroborated by identical Date of Birth and Parent Name.")
                return IdentityComparisonResult(
                    overall_classification=OverallIdentityClassification.LIKELY_SAME_PERSON,
                    confidence_score=0.95,
                    requires_manual_review=False,
                    matched_fields=["full_name"] + matched_fields,
                    conflicting_fields=conflicting_fields,
                    ambiguous_fields=ambiguous_fields,
                    field_results=field_results,
                    evidence=evidence,
                    explanation=f"Names differ in token ordering ('{profile_a.full_name_raw}' vs '{profile_b.full_name_raw}'), but independent corroborating evidence (matching Date of Birth and Father's Name) strongly confirms both records belong to the same citizen.",
                    warnings=[]
                )
            elif has_dob_match:
                evidence.append("Token order variation in name is supported by identical Date of Birth.")
                return IdentityComparisonResult(
                    overall_classification=OverallIdentityClassification.LIKELY_SAME_PERSON,
                    confidence_score=0.88,
                    requires_manual_review=False,
                    matched_fields=["full_name"] + matched_fields,
                    conflicting_fields=conflicting_fields,
                    ambiguous_fields=ambiguous_fields,
                    field_results=field_results,
                    evidence=evidence,
                    explanation=f"Name tokens match with transposed ordering ('{profile_a.full_name_raw}' vs '{profile_b.full_name_raw}'). Date of Birth matches identically.",
                    warnings=["Standardizing name word order before passport application recommended."]
                )
            else:
                # No independent corroboration -> Fail-safe: AMBIGUOUS_NEEDS_REVIEW
                ambiguous_fields.append("full_name")
                return IdentityComparisonResult(
                    overall_classification=OverallIdentityClassification.AMBIGUOUS_NEEDS_REVIEW,
                    confidence_score=0.70,
                    requires_manual_review=True,
                    matched_fields=matched_fields,
                    conflicting_fields=conflicting_fields,
                    ambiguous_fields=ambiguous_fields,
                    field_results=field_results,
                    evidence=evidence,
                    explanation=f"Names differ in token ordering ('{profile_a.full_name_raw}' vs '{profile_b.full_name_raw}') without independent demographic corroboration (DOB/Parent details missing). Cannot confirm identity with certainty.",
                    warnings=["Upload supporting document with Date of Birth or parent details to confirm identity."]
                )

        # Multi-Field Corroboration for Initial Ambiguity (e.g. R Karthik vs Karthik Raman)
        if name_res.classification == NameMatchClassification.INITIAL_AMBIGUITY:
            has_dob_match = "date_of_birth" in matched_fields
            has_parent_match = "father_name" in matched_fields

            # If father's name matches AND starts with the initial (e.g. Father is 'Raman'), that resolves the initial!
            if has_parent_match and profile_a.father_name_normalized and any(init in profile_a.father_name_normalized[:1] for init in profile_a.initials + profile_b.initials):
                evidence.append(f"Initial '{name_res.value_a_raw or name_res.value_b_raw}' corresponds directly to verified father's name ('{profile_a.father_name_raw}').")
                return IdentityComparisonResult(
                    overall_classification=OverallIdentityClassification.LIKELY_SAME_PERSON,
                    confidence_score=0.92,
                    requires_manual_review=False,
                    matched_fields=["full_name"] + matched_fields,
                    conflicting_fields=conflicting_fields,
                    ambiguous_fields=ambiguous_fields,
                    field_results=field_results,
                    evidence=evidence,
                    explanation="Initial expansion ambiguity resolved: Patronymic initial aligns with verified father's name in official records.",
                    warnings=[]
                )
            elif has_dob_match and has_parent_match:
                return IdentityComparisonResult(
                    overall_classification=OverallIdentityClassification.LIKELY_SAME_PERSON,
                    confidence_score=0.88,
                    requires_manual_review=False,
                    matched_fields=["full_name"] + matched_fields,
                    conflicting_fields=conflicting_fields,
                    ambiguous_fields=ambiguous_fields,
                    field_results=field_results,
                    evidence=evidence,
                    explanation=f"Initial expansion ('{profile_a.full_name_raw}' vs '{profile_b.full_name_raw}') is strongly corroborated by matching Date of Birth and Father's Name.",
                    warnings=["Submit initial expansion proof during passport reissue."]
                )
            else:
                # Strict Fail-Safe: Never automatically confirm initial expansion without proof!
                ambiguous_fields.append("full_name")
                return IdentityComparisonResult(
                    overall_classification=OverallIdentityClassification.AMBIGUOUS_NEEDS_REVIEW,
                    confidence_score=0.65,
                    requires_manual_review=True,
                    matched_fields=matched_fields,
                    conflicting_fields=conflicting_fields,
                    ambiguous_fields=ambiguous_fields,
                    field_results=field_results,
                    evidence=evidence,
                    explanation=f"Initial in '{profile_a.full_name_raw}' vs '{profile_b.full_name_raw}' could represent multiple expanded names. Lacking corroborating parental or civil records, manual review is required.",
                    warnings=["Initial ambiguity cannot be resolved automatically without supporting documents."]
                )

        # Truncation / Partial Match (e.g. Muthu vs Muthukumar)
        if name_res.classification == NameMatchClassification.TRUNCATION_OR_PARTIAL_MATCH:
            ambiguous_fields.append("full_name")
            return IdentityComparisonResult(
                overall_classification=OverallIdentityClassification.TRUNCATION_OR_PARTIAL_MATCH,
                confidence_score=0.74,
                requires_manual_review=True,
                matched_fields=matched_fields,
                conflicting_fields=conflicting_fields,
                ambiguous_fields=ambiguous_fields,
                field_results=field_results,
                evidence=evidence,
                explanation=name_res.explanation,
                warnings=["Truncation variation detected: Gazette notification or correction affidavit may be required."]
            )

        # Transliteration or Variant (e.g. Rajeev vs Rajiv, Lakshmi vs Laxmi)
        if name_res.classification == NameMatchClassification.TRANSLITERATION_OR_VARIANT:
            matched_fields.append("full_name")
            return IdentityComparisonResult(
                overall_classification=OverallIdentityClassification.LIKELY_SAME_PERSON,
                confidence_score=0.90,
                requires_manual_review=False,
                matched_fields=matched_fields,
                conflicting_fields=conflicting_fields,
                ambiguous_fields=ambiguous_fields,
                field_results=field_results,
                evidence=evidence + [name_res.explanation],
                explanation=f"Names differ only by common Indian regional/phonetic transliteration ('{profile_a.full_name_raw}' vs '{profile_b.full_name_raw}').",
                warnings=[]
            )

        # Format-Only Match (e.g. M Ajay vs M AJAY, M Ajay vs M. Ajay)
        if name_res.classification == NameMatchClassification.FORMAT_ONLY_MATCH:
            matched_fields.append("full_name")
            return IdentityComparisonResult(
                overall_classification=OverallIdentityClassification.FORMAT_ONLY_MATCH,
                confidence_score=0.98,
                requires_manual_review=False,
                matched_fields=matched_fields,
                conflicting_fields=conflicting_fields,
                ambiguous_fields=ambiguous_fields,
                field_results=field_results,
                evidence=evidence + [name_res.explanation],
                explanation="Identity attributes match across both documents. Differences are limited to formatting, case, and punctuation conventions.",
                warnings=[]
            )

        # Exact Match
        if name_res.classification == NameMatchClassification.EXACT_MATCH:
            matched_fields.append("full_name")
            return IdentityComparisonResult(
                overall_classification=OverallIdentityClassification.EXACT_MATCH,
                confidence_score=1.0,
                requires_manual_review=False,
                matched_fields=matched_fields,
                conflicting_fields=conflicting_fields,
                ambiguous_fields=ambiguous_fields,
                field_results=field_results,
                evidence=evidence + ["All evaluated identity attributes match identically."],
                explanation="Exact identity match across all compared attributes.",
                warnings=[]
            )

        # Default fallback
        return IdentityComparisonResult(
            overall_classification=OverallIdentityClassification.AMBIGUOUS_NEEDS_REVIEW,
            confidence_score=0.60,
            requires_manual_review=True,
            matched_fields=matched_fields,
            conflicting_fields=conflicting_fields,
            ambiguous_fields=ambiguous_fields,
            field_results=field_results,
            evidence=evidence,
            explanation="Unresolved identity variation: manual review recommended.",
            warnings=warnings
        )

    @classmethod
    def _compare_dates_of_birth(
        cls,
        profile_a: DocumentIdentityProfile,
        profile_b: DocumentIdentityProfile,
    ) -> Optional[FieldMatchResult]:
        """Compares dates of birth considering Year-Only compatibility and format variants."""
        dob_a_raw = profile_a.date_of_birth_raw
        dob_b_raw = profile_b.date_of_birth_raw

        if not dob_a_raw or not dob_b_raw:
            return None

        std_a = profile_a.date_of_birth_normalized
        std_b = profile_b.date_of_birth_normalized

        if not std_a or not std_b:
            return FieldMatchResult(
                field_name="date_of_birth",
                value_a_raw=dob_a_raw,
                value_b_raw=dob_b_raw,
                value_a_normalized=std_a,
                value_b_normalized=std_b,
                classification=NameMatchClassification.UNRESOLVABLE_NEEDS_MANUAL_REVIEW,
                similarity_score=0.0,
                confidence_score=0.5,
                is_conflict=True,
                severity=ConflictSeverity.MEDIUM,
                requires_manual_review=True,
                explanation=f"One or both dates could not be parsed as valid calendar dates ('{dob_a_raw}' vs '{dob_b_raw}').",
                possible_causes=["Non-standard date format", "Corrupted date field"],
                recommended_action="Manually verify date of birth in original document."
            )

        # Exact date match (YYYY-MM-DD == YYYY-MM-DD)
        if std_a == std_b:
            return FieldMatchResult(
                field_name="date_of_birth",
                value_a_raw=dob_a_raw,
                value_b_raw=dob_b_raw,
                value_a_normalized=std_a,
                value_b_normalized=std_b,
                classification=NameMatchClassification.EXACT_MATCH,
                similarity_score=1.0,
                confidence_score=1.0,
                is_conflict=False,
                severity=ConflictSeverity.LOW,
                requires_manual_review=False,
                explanation=f"Date of birth matches exactly ({std_a}).",
                possible_causes=[],
                recommended_action="No correction needed."
            )

        # Year-Only compatibility (e.g. Aadhaar Year 1995 vs Passport 1995-05-15)
        if profile_a.birth_year and profile_b.birth_year and profile_a.birth_year == profile_b.birth_year:
            # If one is year-only
            if (profile_a.birth_month is None or profile_b.birth_month is None):
                return FieldMatchResult(
                    field_name="date_of_birth",
                    value_a_raw=dob_a_raw,
                    value_b_raw=dob_b_raw,
                    value_a_normalized=std_a,
                    value_b_normalized=std_b,
                    classification=NameMatchClassification.FORMAT_ONLY_MATCH,
                    similarity_score=0.95,
                    confidence_score=0.95,
                    is_conflict=False,
                    severity=ConflictSeverity.LOW,
                    requires_manual_review=False,
                    explanation=f"Birth year matches ({profile_a.birth_year}). One record records full date while the other provides year only (standard on older e-Aadhaar cards).",
                    possible_causes=["Aadhaar Year of Birth (YOB) standard", "Older format civil records"],
                    recommended_action="Update Aadhaar with full DD/MM/YYYY date using 10th marksheet or birth certificate."
                )

        # Genuine Date of Birth Mismatch
        return FieldMatchResult(
            field_name="date_of_birth",
            value_a_raw=dob_a_raw,
            value_b_raw=dob_b_raw,
            value_a_normalized=std_a,
            value_b_normalized=std_b,
            classification=NameMatchClassification.MISMATCH,
            similarity_score=0.0,
            confidence_score=0.95,
            is_conflict=True,
            severity=ConflictSeverity.HIGH,
            requires_manual_review=True,
            explanation=f"Date of birth discrepancy: '{dob_a_raw}' ({std_a}) vs '{dob_b_raw}' ({std_b}).",
            possible_causes=["Clerical error in one of the documents", "Transposition of day and month (e.g. 05/10 vs 10/05)"],
            recommended_action="Submit statutory DOB correction request using Birth Certificate or Class 10 certificate as primary proof."
        )

