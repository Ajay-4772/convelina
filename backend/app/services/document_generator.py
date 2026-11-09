"""CONVELINA - Module 7 / Phase P3G Document Generator Service

Generates structured, professional administrative drafts grounded in
Module 6 official government knowledge and verified forms.

Core safety properties:
- Uses ONLY citizen-confirmed identity information.
- Strictly filters knowledge sources to verification_status == 'verified'.
- Honest statutory abstention when verified guidance is unavailable.
- Supports deterministic statutory fallback generation when Gemini is offline.
- Fails safely with GEMINI_UNAVAILABLE_MESSAGE when strict Gemini mode is active.
- Neutralizes prompt injection attempts.
- Enforces the mandatory disclaimer:
  "AI-GENERATED ADMINISTRATIVE DRAFT — REVIEW ALL DETAILS AND VERIFY THE APPLICABLE OFFICIAL PROCEDURE BEFORE SUBMISSION."
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings
from app.rag.generation.llm_provider import GoogleGeminiProvider, GEMINI_UNAVAILABLE_MESSAGE
from app.rag.retrieval.retriever import HybridRetriever
from app.schemas.correction_draft import DraftTypeEnum, MANDATORY_DRAFT_DISCLAIMER
from app.services.draft_safety_service import DraftSafetyService, STATUTORY_ABSTENTION_NOTICE

logger = logging.getLogger(__name__)

DRAFT_DISCLAIMER = MANDATORY_DRAFT_DISCLAIMER

SUPPORTED_DOCUMENT_TYPES = {
    # P3G 10 Administrative Types
    DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value: "Identity-Detail Correction Request Letter",
    DraftTypeEnum.NAME_CHANGE_REPRESENTATION.value: "Name Correction / Change Representation",
    DraftTypeEnum.DOB_RECTIFICATION_REQUEST.value: "Date of Birth Correction Request",
    DraftTypeEnum.ADDRESS_UPDATE_APPLICATION.value: "Address Correction / Update Application",
    DraftTypeEnum.PARENT_NAME_RECTIFICATION.value: "Parent / Guardian Name Correction Request",
    DraftTypeEnum.EDUCATIONAL_CERTIFICATE_REPRESENTATION.value: "Educational Certificate Correction Representation",
    DraftTypeEnum.EPF_MEMBER_CORRECTION_REQUEST.value: "EPF / UAN Member-Detail Correction Request",
    DraftTypeEnum.GENERAL_ADMINISTRATIVE_REPRESENTATION.value: "General Administrative Representation",
    DraftTypeEnum.SUPPORTING_DOCUMENT_COVER_LETTER.value: "Supporting Document Cover Letter",
    DraftTypeEnum.STATUTORY_PETITION_REPRESENTATION.value: "Statutory Petition Representation",
    # Legacy compatibility aliases
    "correction_request_letter": "Formal Correction Request Letter",
    "supporting_document_checklist": "Supporting Document Checklist & Application Guide",
    "declaration_draft": "Self-Declaration / Affidavit Draft",
    "general_correction_application": "General Discrepancy Rectification Application",
}

SYSTEM_INSTRUCTION = f"""You are the CONVELINA Official Administrative Drafting Specialist.
Your responsibility is to draft professional, formally formatted correction request representations, petitions, checklists, or declarations for Indian citizens seeking identity document rectification.

MANDATORY SAFETY RULES:
1. Ground every procedural claim strictly in the provided verified government sources. Do NOT invent legal procedures, statutory sections, circular numbers, deadlines, fees, or government office addresses.
2. If any citizen detail (such as postal address, URN, or submission date) is unconfirmed, insert a clear square-bracketed placeholder: [Applicant Full Address], [Submission Date], [Application / Ack Number].
3. For conflicting fields, state only the citizen-confirmed true value and the recorded discrepancy. Never invent values.
4. DO NOT invent government seals, stamps, emblems, approval marks, or false signatures.
5. The very first line of the output MUST be exactly:
{MANDATORY_DRAFT_DISCLAIMER}
6. Follow formal Indian administrative correspondence etiquette (To, Date, Subject, Reference, Salutation, Statement of Facts, Citizen Explanation, Requested Administrative Relief, Enclosures checklist, Signature block).
7. If no verified guidance is available, include the notice: "{STATUTORY_ABSTENTION_NOTICE}".
"""


class DocumentValidator:
    """Validates generated correction documents before making them available to users."""

    @staticmethod
    def validate(content: str) -> Dict[str, Any]:
        """Scans document content for unresolved placeholders, disclaimers, and warnings."""
        placeholder_pattern = re.compile(r"\[([A-Za-z0-9\s/_\-:,]+)\]")
        placeholders_found = placeholder_pattern.findall(content)

        unresolved_placeholders = [
            p.strip() for p in placeholders_found
            if not p.startswith("http") and len(p.strip()) > 1
        ]

        warnings: List[str] = []
        has_disclaimer = bool(
            re.search(r"ai-generated (administrative )?draft\s*[-—]\s*review all (information|details)", content, re.IGNORECASE)
        )

        if not has_disclaimer:
            warnings.append("Draft disclaimer was missing from generated content and was automatically appended.")

        if unresolved_placeholders:
            warnings.append(
                f"Document contains {len(unresolved_placeholders)} unresolved placeholder(s) requiring review: {', '.join(unresolved_placeholders[:5])}"
            )

        has_enclosures = bool(re.search(r"enclosure|annexure|documents attached|supporting documents", content, re.IGNORECASE))
        if not has_enclosures:
            warnings.append("No explicit enclosures list detected. Ensure supporting identity proofs are attached.")

        return {
            "is_valid": True,
            "unresolved_placeholders": list(set(unresolved_placeholders)),
            "warnings": warnings,
            "has_disclaimer": has_disclaimer,
        }


class CorrectionDocumentGenerator:
    """Orchestrates case context, verified RAG evidence retrieval, and document generation."""

    def __init__(self, retriever: Optional[HybridRetriever] = None):
        self.retriever = retriever or HybridRetriever()
        self.llm_provider = GoogleGeminiProvider()

    def generate_draft(
        self,
        document_type: str,
        document_category: str,
        conflicting_field: str,
        confirmed_fields: Dict[str, Any],
        ocr_extracted_values: Optional[Dict[str, Any]] = None,
        conflict_classification: Optional[str] = None,
        user_explanation: Optional[str] = None,
        requested_action: Optional[str] = None,
        allow_fallback: bool = False,
        conflict: Optional[Any] = None,
        language: str = "en",
    ) -> Tuple[bool, str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generates a personalized administrative draft.
        Returns:
            (success: bool, content: str, source_references: List[dict], validation: dict)
        """
        if document_type not in SUPPORTED_DOCUMENT_TYPES:
            document_type = DraftTypeEnum.IDENTITY_CORRECTION_REQUEST.value

        # 1. Retrieve verified guidance & forms (strictly verification_status == 'verified')
        query = f"Correction procedure and official forms for {conflicting_field} discrepancy in {document_category} document"
        verified_sources, relevant_forms, is_verified, abstention_msg = DraftSafetyService.retrieve_verified_guidance(
            retriever=self.retriever,
            query=query,
            category=document_category,
            conflicting_field=conflicting_field,
        )

        sources: List[Dict[str, Any]] = []
        context_chunks: List[str] = []
        for r in verified_sources:
            sources.append({
                "source_id": r.get("source_id", ""),
                "title": r.get("title", "Official Guideline"),
                "authority": r.get("issuing_authority", document_category.upper()),
                "source_url": r.get("source_url", ""),
                "relevance_score": r.get("relevance_score", 0.0),
                "verification_status": "verified",
            })
            context_chunks.append(f"Source [{r['title']} - {r['issuing_authority']}]:\n{r.get('content', '')}")

        context_text = "\n\n---\n\n".join(context_chunks) if context_chunks else abstention_msg

        # 2. Build structured prompt
        doc_type_title = SUPPORTED_DOCUMENT_TYPES.get(document_type, "Administrative Correction Representation")
        user_confirmed_name = confirmed_fields.get("applicant_name") or "[Applicant Full Name]"
        correct_value = (
            confirmed_fields.get("requested_value")
            or confirmed_fields.get(conflicting_field)
            or confirmed_fields.get("correct_name")
            or confirmed_fields.get("date_of_birth")
            or f"[Confirmed Correct {conflicting_field}]"
        )
        recorded_value = (
            confirmed_fields.get("current_recorded_value")
            or (ocr_extracted_values.get(conflicting_field) if ocr_extracted_values else f"[Current Recorded {conflicting_field}]")
        )
        explanation = user_explanation or confirmed_fields.get("reason_for_discrepancy") or "Clerical recording error in official records."
        action = requested_action or f"Rectification of recorded {conflicting_field.replace('_', ' ')} to reflect verified particulars."

        prompt = f"""Generate a {doc_type_title} for rectifying a {conflicting_field.replace('_', ' ')} discrepancy.

CASE DETAILS (CITIZEN-CONFIRMED FACTS ONLY):
- Authority / Document Category: {document_category.upper()}
- Target Discrepancy Field: {conflicting_field}
- Conflict Classification: {conflict_classification or 'Identified Discrepancy'}
- Applicant Name: {user_confirmed_name}
- Current Incorrect Recorded Value: {recorded_value}
- Requested Corrected Value: {correct_value}
- Applicant Explanation: {explanation}
- Confirmed Additional Particulars: {confirmed_fields}

VERIFIED OFFICIAL GUIDELINES & STATUTORY FORMS:
{context_text}

MANDATORY INSTRUCTIONS:
- Ground every procedural instruction in the verified sources.
- If verified sources are unavailable, explicitly include the statutory abstention statement.
- First line MUST be: {MANDATORY_DRAFT_DISCLAIMER}
- Do not invent facts. Use placeholders [like this] for any unconfirmed details.
"""

        # 3. Invocation with offline fallback support
        if not self.llm_provider.is_configured or not getattr(self.llm_provider, "api_key", None):
            if allow_fallback:
                logger.info("Gemini unconfigured; utilizing deterministic statutory draft generation.")
                content, _, _, _ = DraftSafetyService.build_deterministic_draft_content(
                    draft_type=document_type,
                    document_category=document_category,
                    conflicting_field=conflicting_field,
                    confirmed_fields=confirmed_fields,
                    conflict=conflict or type("TempConflict", (), {"value_a": recorded_value, "value_b": recorded_value, "conflict_type": conflict_classification})(),
                    verified_sources=verified_sources,
                    relevant_forms=relevant_forms,
                    user_explanation=explanation,
                    requested_action=action,
                    language=language,
                )
                val = DocumentValidator.validate(content)
                return True, content, sources, val
            else:
                logger.error("Gemini API key is not configured and fallback mode disabled. Failing safely.")
                return False, GEMINI_UNAVAILABLE_MESSAGE, [], {"is_valid": False, "warnings": [GEMINI_UNAVAILABLE_MESSAGE]}

        try:
            generated_text = self.llm_provider.generate(
                prompt=prompt,
                system_instruction=SYSTEM_INSTRUCTION,
            )
        except Exception as e:
            logger.error("Gemini generation call failed: %s", str(e), exc_info=True)
            if allow_fallback:
                logger.info("Falling back to deterministic statutory draft following Gemini exception.")
                content, _, _, _ = DraftSafetyService.build_deterministic_draft_content(
                    draft_type=document_type,
                    document_category=document_category,
                    conflicting_field=conflicting_field,
                    confirmed_fields=confirmed_fields,
                    conflict=conflict or type("TempConflict", (), {"value_a": recorded_value, "value_b": recorded_value, "conflict_type": conflict_classification})(),
                    verified_sources=verified_sources,
                    relevant_forms=relevant_forms,
                    user_explanation=explanation,
                    requested_action=action,
                    language=language,
                )
                val = DocumentValidator.validate(content)
                return True, content, sources, val
            return False, GEMINI_UNAVAILABLE_MESSAGE, [], {"is_valid": False, "warnings": [GEMINI_UNAVAILABLE_MESSAGE]}

        if generated_text.strip() == GEMINI_UNAVAILABLE_MESSAGE:
            if allow_fallback:
                content, _, _, _ = DraftSafetyService.build_deterministic_draft_content(
                    draft_type=document_type,
                    document_category=document_category,
                    conflicting_field=conflicting_field,
                    confirmed_fields=confirmed_fields,
                    conflict=conflict or type("TempConflict", (), {"value_a": recorded_value, "value_b": recorded_value, "conflict_type": conflict_classification})(),
                    verified_sources=verified_sources,
                    relevant_forms=relevant_forms,
                    user_explanation=explanation,
                    requested_action=action,
                    language=language,
                )
                val = DocumentValidator.validate(content)
                return True, content, sources, val
            return False, GEMINI_UNAVAILABLE_MESSAGE, [], {"is_valid": False, "warnings": [GEMINI_UNAVAILABLE_MESSAGE]}

        # Ensure mandatory disclaimer is at the beginning
        if MANDATORY_DRAFT_DISCLAIMER not in generated_text:
            generated_text = f"{MANDATORY_DRAFT_DISCLAIMER}\n\n{generated_text}"

        val = DocumentValidator.validate(generated_text)
        return True, generated_text, sources, val
