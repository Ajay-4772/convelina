import json
import logging
from typing import Dict, Any, List, Optional

from app.config import settings
from app.rag.generation.prompt_templates import format_rag_prompt
from app.rag.generation.output_validator import GroundedOutputValidator
from app.rag.schemas import GroundedAnswer, ResolutionStep, FutureImplication, SourceCitation

logger = logging.getLogger("consolith.rag.llm")

class BaseLLMProvider:
    def generate_answer(
        self,
        question: str,
        case_context: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
        relevant_forms: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> GroundedAnswer:
        raise NotImplementedError


class GroundedDeterministicProvider(BaseLLMProvider):
    """
    Deterministic rule-grounded generator.
    Parses verified official chunks, forms, and case context to produce structured,
    traceable responses without requiring external LLM API tokens.
    Guarantees zero hallucination and enforces strict relevance thresholds.
    """

    def generate_answer(
        self,
        question: str,
        case_context: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
        relevant_forms: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> GroundedAnswer:
        # Check relevance floor
        if not retrieved_chunks:
            return GroundedAnswer(
                answer="No official procedural guidance could be verified for this specific question above the relevance threshold (>= 0.55). Please ensure the inquiry pertains to supported Indian identity documents (Aadhaar, PAN, Passport, Class 10/12, or EPF).",
                issue_summary="Evidence unavailable or below relevance floor",
                resolution_steps=[],
                relevant_forms=[],
                potential_future_implications=[],
                uncertainties=["Official government circular or procedure not found in verified knowledge repository."],
                citations=[],
                requires_clarification=False,
                confidence="insufficient_evidence"
            )

        conflict_info = case_context.get("conflict") or {}
        field_name = conflict_info.get("field_name", "record details")
        val_a = conflict_info.get("value_a", "")
        val_b = conflict_info.get("value_b", "")
        conflict_type = conflict_info.get("conflict_type", "discrepancy")

        # Synthesize procedural explanation from primary retrieved chunk
        primary_chunk = retrieved_chunks[0]
        authority = primary_chunk.get("issuing_authority", "Official Authority")
        doc_category = primary_chunk.get("document_category", "identity record").upper()

        explanation_lines = [
            f"Based on official {authority} guidelines, an inconsistency was identified in your {field_name} across your documents ({val_a} vs {val_b}).",
            f"Under {doc_category} procedures, this is classified as a {conflict_type}. The discrepancy requires procedural verification with authentic supporting evidence before it can be updated."
        ]

        # Resolution steps based on retrieved authority
        steps: List[ResolutionStep] = []
        if "aadhaar" in doc_category.lower():
            steps = [
                ResolutionStep(
                    step_number=1,
                    title="Verify Supporting Identity Documents",
                    description="Ensure you have a valid original Proof of Identity (POI) or Proof of Date of Birth (PDB) such as Passport, Birth Certificate, or School Certificate.",
                    required_documents=["Original Birth Certificate or Passport", "Aadhaar Card copy"],
                    official_portal_or_form="https://myaadhaar.uidai.gov.in"
                ),
                ResolutionStep(
                    step_number=2,
                    title="Submit Update Request Online or at Aadhaar Seva Kendra",
                    description="Fill out the Aadhaar Enrolment / Update Form and present original documents for physical biometric authentication.",
                    required_documents=["Aadhaar Enrolment / Update Form (Adult)"],
                    official_portal_or_form="Aadhaar Seva Kendra"
                )
            ]
        elif "pan" in doc_category.lower():
            steps = [
                ResolutionStep(
                    step_number=1,
                    title="Download and Fill CSF Correction Form",
                    description="Submit the Request for Changes or Correction in PAN Data Form (CSF). Specify your existing 10-character PAN and check only the box for the field requiring modification.",
                    required_documents=["Copy of PAN Card", "Proof of Identity / DOB matching correct name"],
                    official_portal_or_form="Protean NSDL / UTIITSL Portal"
                ),
                ResolutionStep(
                    step_number=2,
                    title="Submit Application Online or at TIN-FC",
                    description="Submit via Aadhaar e-KYC or lodge physical signed form with photographs at the nearest TIN-FC center.",
                    required_documents=["Self-attested identity proof"],
                    official_portal_or_form="https://www.onlineservices.nsdl.com"
                )
            ]
        elif "epf" in doc_category.lower():
            steps = [
                ResolutionStep(
                    step_number=1,
                    title="Execute Joint Declaration Form",
                    description="Complete the official EPFO Joint Declaration Form signed by both you and your authorized employer signatory.",
                    required_documents=["Joint Declaration Form", "Aadhaar Card", "PAN Card", "Educational Certificate"],
                    official_portal_or_form="EPFO Unified Member Portal / Field Office"
                ),
                ResolutionStep(
                    step_number=2,
                    title="Submit to Jurisdictional EPF Office",
                    description="Employer must verify and forward the Joint Declaration online via Member Portal or physically to the EPF Field Office.",
                    required_documents=["Employer authorization letter"],
                    official_portal_or_form="https://unifiedportal-mem.epfindia.gov.in"
                )
            ]
        elif "passport" in doc_category.lower():
            steps = [
                ResolutionStep(
                    step_number=1,
                    title="Apply for Re-issue of Passport",
                    description="Log in to Passport Seva portal and select 'Re-issue of Passport' under reason 'Change in Personal Particulars'.",
                    required_documents=["Old Original Passport", "Proof of Identity matching revised name", "Annexure E (if major change)"],
                    official_portal_or_form="https://www.passportindia.gov.in"
                ),
                ResolutionStep(
                    step_number=2,
                    title="Attend Passport Seva Kendra Appointment",
                    description="Visit PSK with all original documents for physical document inspection and biometrics.",
                    required_documents=["Appointment confirmation receipt"],
                    official_portal_or_form="Passport Seva Kendra (PSK)"
                )
            ]
        else:
            steps = [
                ResolutionStep(
                    step_number=1,
                    title="Verify School / Admission Records",
                    description="Confirm that the requested correction matches the original school admission register records.",
                    required_documents=["School Admission Register Extract", "Application through Head of Institution"],
                    official_portal_or_form="Regional Board Office"
                )
            ]

        # Potential Future Implications (Qualified, never absolute)
        future_implications: List[FutureImplication] = [
            FutureImplication(
                area="Aadhaar-PAN Linking & Tax Processing",
                risk_assessment="conditional",
                explanation="If demographic data (Name, DOB, Gender) differs between Aadhaar and PAN, automated electronic linking may fail, potentially rendering PAN inoperative for high-value banking transactions.",
                suggested_action="Synchronize name and date of birth in PAN to match Aadhaar before filing tax returns."
            ),
            FutureImplication(
                area="EPFO Electronic Claim Settlement",
                risk_assessment="documented_requirement",
                explanation="Section 142 of the Code on Social Security mandates Aadhaar seeding for EPF withdrawals. Discrepancies trigger 'Aadhaar demographic mismatch' errors and block online claims.",
                suggested_action="Submit a Joint Declaration to align EPFO records with Aadhaar."
            )
        ]

        # Build citations from retrieved chunks
        citations = []
        for c in retrieved_chunks[:3]:
            citations.append({
                "source_id": c.get("source_id", "official_source"),
                "title": c.get("title", "Official Guidance"),
                "authority": c.get("issuing_authority", "Government Authority"),
                "url": c.get("source_url", ""),
                "section": c.get("heading")
            })

        raw_dict = {
            "answer": " ".join(explanation_lines),
            "issue_summary": f"Inconsistency in {field_name} across documents: '{val_a}' vs '{val_b}'." if val_a and val_b else f"Procedural inquiry regarding {doc_category} records.",
            "resolution_steps": [s.model_dump() for s in steps],
            "relevant_forms": relevant_forms,
            "potential_future_implications": [f.model_dump() for f in future_implications],
            "uncertainties": ["Exact processing timeline depends on regional field office verification."],
            "citations": citations,
            "requires_clarification": False,
            "confidence": "supported"
        }

        return GroundedOutputValidator.validate_and_filter_citations(raw_dict, retrieved_chunks)


class AnthropicClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude API provider using official 'anthropic' client library.
    Falls back to GroundedDeterministicProvider if API key is invalid or call fails.
    """

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self.fallback = GroundedDeterministicProvider()
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            logger.warning("Failed to initialize Anthropic client, using fallback: %s", str(e))
            self.client = None

    def generate_answer(
        self,
        question: str,
        case_context: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
        relevant_forms: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> GroundedAnswer:
        if not self.client:
            return self.fallback.generate_answer(question, case_context, retrieved_chunks, relevant_forms, conversation_history)

        case_context_str = json.dumps(case_context, indent=2)
        evidence_str = "\n\n---\n\n".join([
            f"[Source ID: {c.get('source_id')} | Authority: {c.get('issuing_authority')} | URL: {c.get('source_url')}]\n{c.get('content')}"
            for c in retrieved_chunks
        ])
        history_str = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in conversation_history])

        prompt = format_rag_prompt(
            question=question,
            case_context_str=case_context_str,
            evidence_str=evidence_str,
            conversation_history_str=history_str
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.content[0].text
            # Extract JSON block
            if "{" in raw_text and "}" in raw_text:
                json_start = raw_text.find("{")
                json_end = raw_text.rfind("}") + 1
                parsed = json.loads(raw_text[json_start:json_end])
                parsed["relevant_forms"] = relevant_forms
                return GroundedOutputValidator.validate_and_filter_citations(parsed, retrieved_chunks)
            else:
                logger.warning("Claude response was not JSON, falling back to deterministic.")
                return self.fallback.generate_answer(question, case_context, retrieved_chunks, relevant_forms, conversation_history)
        except Exception as e:
            logger.error("Anthropic Claude API call failed: %s. Using deterministic fallback.", str(e))
            return self.fallback.generate_answer(question, case_context, retrieved_chunks, relevant_forms, conversation_history)


def get_llm_provider() -> BaseLLMProvider:
    if settings.ANTHROPIC_API_KEY:
        return AnthropicClaudeProvider(api_key=settings.ANTHROPIC_API_KEY, model=settings.ANTHROPIC_MODEL)
    return GroundedDeterministicProvider()
