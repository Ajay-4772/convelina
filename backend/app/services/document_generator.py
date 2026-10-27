"""CONVELINA - Module 7 Document Generator Service

Generates structured, professional correction drafts using Google Gemini, grounded in
Module 6 official government knowledge and verified forms.

Adheres strictly to the Gemini-Only architecture:
- If Gemini fails (API error, rate limit, quota, timeout, network error, or missing key),
  returns the exact required user-facing message:
  "Assistant service is not currently available. Please try again later."
- No alternative LLM providers or rule-based fallback draft generators are used.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings
from app.rag.generation.llm_provider import GoogleGeminiProvider, GEMINI_UNAVAILABLE_MESSAGE
from app.rag.retrieval.retriever import HybridRetriever

logger = logging.getLogger(__name__)

DRAFT_DISCLAIMER = (
    "AI-generated draft — review all information and verify the applicable official procedure before submission."
)

SUPPORTED_DOCUMENT_TYPES = {
    "correction_request_letter": "Formal Correction Request Letter",
    "supporting_document_checklist": "Supporting Document Checklist & Application Guide",
    "declaration_draft": "Self-Declaration / Affidavit Draft (Applicable official format)",
    "general_correction_application": "General Discrepancy Rectification Application",
}

SYSTEM_INSTRUCTION = f"""You are the CONVELINA Official Document Assistance Specialist.
Your responsibility is to draft professional, formally formatted correction request documents, checklists, or declarations for Indian citizens seeking identity document rectification.

MANDATORY RULES:
1. Ground every procedural claim in the provided verified government sources. Do NOT invent legal procedures, statutory sections, circulars, fees, or government office addresses.
2. If any citizen detail (such as full postal address, application number, or submission date) is not confirmed, insert a clear square-bracketed placeholder, for example: [Applicant Full Address], [Submission Date], [Application/URN Number].
3. For conflicting fields, clearly state the current incorrect recorded value and the requested corrected value as confirmed by the applicant.
4. DO NOT invent government seals, stamps, emblems, approval marks, or false signatures.
5. Emphasize that the document is a draft prepared for applicant submission and review.
6. The first line of the document output MUST be:
{DRAFT_DISCLAIMER}
7. Follow formal Indian government correspondence etiquette (To, Subject, Reference, Body, Enclosures, Signature block).
"""


class DocumentValidator:
    """Validates generated correction documents before making them available to users."""

    @staticmethod
    def validate(content: str) -> Dict[str, Any]:
        """Scans document content for unresolved placeholders, disclaimers, and warnings."""
        # Find placeholders like [Please confirm ...], [Applicant Address], etc.
        placeholder_pattern = re.compile(r"\[([A-Za-z0-9\s/_\-:,]+)\]")
        placeholders_found = placeholder_pattern.findall(content)

        # Filter out common markdown links or false positives
        unresolved_placeholders = [
            p.strip() for p in placeholders_found
            if not p.startswith("http") and len(p.strip()) > 1
        ]

        warnings: List[str] = []
        if DRAFT_DISCLAIMER not in content:
            warnings.append("Draft disclaimer was missing from generated content and was automatically appended.")

        if unresolved_placeholders:
            warnings.append(
                f"Document contains {len(unresolved_placeholders)} unresolved placeholder(s) that require user review: {', '.join(unresolved_placeholders[:5])}"
            )

        has_enclosures = bool(re.search(r"enclosure|annexure|documents attached", content, re.IGNORECASE))
        if not has_enclosures:
            warnings.append("No explicit enclosures list detected. Ensure supporting identity proofs are attached.")

        return {
            "is_valid": True,  # Valid for review/editing, but may contain warnings
            "unresolved_placeholders": list(set(unresolved_placeholders)),
            "warnings": warnings,
            "has_disclaimer": DRAFT_DISCLAIMER in content,
        }


class CorrectionDocumentGenerator:
    """Service to orchestrate case context, official RAG evidence retrieval,

    and Gemini generation for Module 7 correction documents.
    """

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
    ) -> Tuple[bool, str, List[Dict[str, Any]], Dict[str, Any]]:
        """Generates a correction draft.

        Returns:
            (success: bool, content: str, source_references: List[dict], validation: dict)
        """
        if document_type not in SUPPORTED_DOCUMENT_TYPES:
            document_type = "correction_request_letter"

        # 1. Retrieve official guidance & forms from Module 6 Knowledge Base
        query = f"Correction procedure and official forms for {conflicting_field} discrepancy in {document_category} document"
        try:
            rag_results = self.retriever.retrieve(query=query, top_k=4)
        except Exception as e:
            logger.warning(f"Error during RAG retrieval in document generator: {e}")
            rag_results = []

        sources: List[Dict[str, Any]] = []
        context_chunks: List[str] = []
        for r in rag_results:
            src_info = {
                "title": r.get("title", "Official Guideline"),
                "source_url": r.get("source_url", ""),
                "authority": r.get("issuing_authority", document_category.upper()),
                "doc_category": r.get("document_category", document_category),
                "relevance_score": round(float(r.get("score", 0.0)), 3),
            }
            sources.append(src_info)
            context_chunks.append(f"Source [{src_info['title']} - {src_info['authority']}]:\n{r.get('content', '')}")

        context_text = "\n\n---\n\n".join(context_chunks) if context_chunks else "No specific official guidance retrieved."

        # 2. Build structured user & case prompt
        doc_type_title = SUPPORTED_DOCUMENT_TYPES.get(document_type, "Correction Request")
        user_confirmed_name = confirmed_fields.get("applicant_name") or "[Applicant Full Name]"
        correct_value = confirmed_fields.get("requested_value") or confirmed_fields.get(conflicting_field) or f"[Please confirm correct {conflicting_field}]"
        incorrect_value = confirmed_fields.get("current_recorded_value") or (ocr_extracted_values.get(conflicting_field) if ocr_extracted_values else f"[Current recorded {conflicting_field}]")
        user_explanation = confirmed_fields.get("reason_for_discrepancy") or "Clerical recording error in historical records."

        prompt = f"""Generate a {doc_type_title} for correcting a {conflicting_field.replace('_', ' ')} inconsistency.

CASE DETAILS:
- Authority / Document Category: {document_category.upper()}
- Target Discrepancy Field: {conflicting_field}
- Conflict Classification: {conflict_classification or 'Identified Discrepancy'}
- Applicant Name: {user_confirmed_name}
- Current Incorrect Value in Records: {incorrect_value}
- Requested Corrected Value: {correct_value}
- Applicant Explanation: {user_explanation}
- Confirmed Additional Fields: {confirmed_fields}

VERIFIED OFFICIAL GUIDELINES & FORMS AVAILABLE:
{context_text}

DOCUMENT SPECIFICATIONS:
- If document_type is 'correction_request_letter': Produce a formal correction application letter addressed to the competent authority (e.g. Unique Identification Authority of India, Passport Seva Kendra / Regional Passport Office, Income Tax PAN Services Unit, or EPFO Regional Commissioner). Include To, From, Subject, Reference, Statement of Discrepancy, Requested Rectification, Enclosures checklist, and Signature line.
- If document_type is 'supporting_document_checklist': Detail the exact mandatory and acceptable list of identity proofs needed under verified official rules for {conflicting_field} correction in {document_category.upper()}.
- If document_type is 'declaration_draft': Draft a solemn self-declaration or affidavit format confirming the true particulars with clear bracketed placeholders for notarization or magistrate details if required.
- If document_type is 'general_correction_application': Provide a standardized representation format.

Do not invent facts. Use placeholders [like this] wherever specific details (e.g. Aadhaar Enrolment Number, Passport File Number, permanent address) are needed from the citizen.
"""

        # 3. Invoke Google Gemini
        if not self.llm_provider.is_configured:
            logger.error("Gemini API key is not configured. Failing safely.")
            return False, GEMINI_UNAVAILABLE_MESSAGE, [], {"is_valid": False, "warnings": [GEMINI_UNAVAILABLE_MESSAGE]}

        try:
            generated_text = self.llm_provider.generate(
                prompt=prompt,
                system_instruction=SYSTEM_INSTRUCTION,
            )
        except Exception as e:
            logger.error(f"Gemini generation call failed: {e}", exc_info=True)
            return False, GEMINI_UNAVAILABLE_MESSAGE, [], {"is_valid": False, "warnings": [GEMINI_UNAVAILABLE_MESSAGE]}

        # If LLM provider returned the unavailability message
        if generated_text.strip() == GEMINI_UNAVAILABLE_MESSAGE:
            return False, GEMINI_UNAVAILABLE_MESSAGE, [], {"is_valid": False, "warnings": [GEMINI_UNAVAILABLE_MESSAGE]}

        # Ensure disclaimer is at the beginning
        if DRAFT_DISCLAIMER not in generated_text:
            generated_text = f"{DRAFT_DISCLAIMER}\n\n{generated_text}"

        # 4. Validate output
        validation_result = DocumentValidator.validate(generated_text)

        return True, generated_text, sources, validation_result
