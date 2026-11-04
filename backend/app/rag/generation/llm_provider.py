import json
import time
import logging
from typing import Dict, Any, List, Optional

from app.config import settings
from app.rag.generation.prompt_templates import format_rag_prompt
from app.rag.generation.output_validator import GroundedOutputValidator
from app.rag.schemas import GroundedAnswer, SourceCitation, OfficialFormResponse

logger = logging.getLogger("consolith.rag.llm")

SERVICE_UNAVAILABLE_MESSAGE = "Assistant service is not currently available. Please try again later."
GEMINI_UNAVAILABLE_MESSAGE = SERVICE_UNAVAILABLE_MESSAGE
MANDATORY_STATUTORY_DISCLAIMER = "AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION"


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


class GoogleGeminiProvider(BaseLLMProvider):
    """
    Google Gemini ONLY LLM Provider.
    Adheres strictly to the single-provider mandate:
    - Never falls back to Anthropic, OpenAI, Groq, or Hugging Face.
    - Uses Google Gemini for live AI reasoning when configured.
    - Implements retry with exponential backoff for transient 429 / 503 / network errors.
    - Distinguishes live generation (is_fallback=False, provider_status="operational")
      from safe offline statutory fallback (is_fallback=True, provider_status="fallback_offline").
    - If evidence is below relevance floor (>= 0.55), abstains with confidence="insufficient_evidence".
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
        backoff_factor: Optional[float] = None
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        self.timeout_seconds = timeout_seconds or getattr(settings, "GEMINI_TIMEOUT_SECONDS", 15)
        self.max_retries = max_retries if max_retries is not None else getattr(settings, "GEMINI_MAX_RETRIES", 2)
        self.backoff_factor = backoff_factor if backoff_factor is not None else getattr(settings, "GEMINI_BACKOFF_FACTOR", 2.0)
        self.client = None
        self.raw_client = None

        if settings.GEMINI_ENABLED and self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={"response_mime_type": "application/json"}
                )
                self.raw_client = genai.GenerativeModel(
                    model_name=self.model_name
                )
            except Exception as e:
                logger.error("Failed to initialize Google Gemini client: %s", str(e), exc_info=True)
                self.client = None
                self.raw_client = None
        else:
            if not settings.GEMINI_ENABLED:
                logger.info("GEMINI_ENABLED is False. GoogleGeminiProvider running in offline statutory fallback mode.")
            else:
                logger.warning("GEMINI_API_KEY is not configured. Google Gemini cannot generate live responses.")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.client)

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generates plain text / markdown output (used by Document Generator)."""
        if not self.raw_client:
            return GEMINI_UNAVAILABLE_MESSAGE
        try:
            full_prompt = f"System Instruction: {system_instruction}\n\nPrompt:\n{prompt}" if system_instruction else prompt
            response = self.raw_client.generate_content(full_prompt)
            if response and response.text and response.text.strip():
                return response.text.strip()
            return GEMINI_UNAVAILABLE_MESSAGE
        except Exception as e:
            logger.error("Gemini text generation failed: %s", str(e), exc_info=True)
            return GEMINI_UNAVAILABLE_MESSAGE

    def _generate_offline_fallback(
        self,
        question: str,
        case_context: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
        relevant_forms: List[Dict[str, Any]]
    ) -> GroundedAnswer:
        """
        Generates a deterministic statutory resolution answer when live Gemini is disabled,
        offline, or encounters upstream API errors. Grounded purely in verified database
        mapping and official statutory circulars.
        """
        res_mapping = case_context.get("resolution_mapping")
        findings = case_context.get("deterministic_findings") or {}

        # 1. Build verified citations from retrieved chunks
        citations: List[SourceCitation] = []
        for c in retrieved_chunks:
            sid = c.get("source_id")
            if sid and str(c.get("verification_status", "verified")).lower() == "verified":
                citations.append(
                    SourceCitation(
                        source_id=sid,
                        title=c.get("title", "Official Guidance"),
                        authority=c.get("issuing_authority", "Government Authority"),
                        url=c.get("source_url", ""),
                        verification_status=c.get("verification_status", "verified")
                    )
                )

        # 2. Case with active conflict and resolution mapping
        if res_mapping:
            field_name = findings.get("field_name", "identity field")
            classification = findings.get("classification", "Discrepancy detected")
            conf_score = int(findings.get("confidence_score", 1.0) * 100)

            # Layer A: Deterministic Identity Finding
            layer_a = (
                f"**[Layer A: Deterministic Identity Finding]**\n"
                f"CONVELINA automated comparison identified an inconsistency in '{field_name}' "
                f"classified as '{classification}' (Engine Confidence: {conf_score}%)."
            )
            if findings.get("requires_manual_review"):
                layer_a += "\n⚠️ Caution: Ambiguous identity variations detected. Manual official review is required."
            if findings.get("ocr_quality_warning"):
                layer_a += f"\n⚠️ OCR Notice: {findings['ocr_quality_warning']}"
            if findings.get("non_latin_warning"):
                layer_a += f"\n⚠️ Script Notice: {findings['non_latin_warning']}"

            # Layer B: Statutory Guidance
            proc_name = res_mapping.get("procedure_name", "Official Correction Procedure")
            authority = res_mapping.get("authority_name", "Competent Authority")
            portal = res_mapping.get("authority_portal", "")
            channel = res_mapping.get("submission_channel", "official portal").replace("_", " ")
            rules = res_mapping.get("statutory_rules", [])

            layer_b = (
                f"**[Layer B: Verified Statutory Guidance]**\n"
                f"According to verified {authority} procedures, this inconsistency must be addressed via the '{proc_name}'.\n"
                f"• Official Authority: {authority}\n"
                f"• Submission Channel: {channel.title()}\n"
                f"• Official Portal: {portal}"
            )
            if rules:
                layer_b += "\n• Statutory Guidelines:\n  - " + "\n  - ".join(rules[:3])

            # Layer C: Manual Review & Statutory Boundary
            layer_c = (
                f"**[Layer C: Manual Review & Statutory Boundaries]**\n"
                f"Statutory Notice: This offline guidance is synthesized directly from verified statutory circulars and prescribed forms. "
                f"All corrections are subject to official verification by {authority} officers. "
                f"CONVELINA does not perform direct government filing."
            )

            full_answer = f"{layer_a}\n\n{layer_b}\n\n{layer_c}\n\n---\n{MANDATORY_STATUTORY_DISCLAIMER}"

            # Build resolution steps
            resolution_steps = []
            checklist = res_mapping.get("document_checklist", [])
            prescribed_forms = res_mapping.get("prescribed_forms", [])

            if checklist:
                resolution_steps.append({
                    "step_number": 1,
                    "title": "Assemble Required Supporting Documentation",
                    "description": "Gather verified proof documents before initiating correction.",
                    "required_documents": checklist,
                    "official_portal_or_form": portal
                })
            if prescribed_forms:
                form_names = [f.get("form_name", "Prescribed Form") for f in prescribed_forms]
                resolution_steps.append({
                    "step_number": len(resolution_steps) + 1,
                    "title": "Complete Prescribed Statutory Forms",
                    "description": f"Download and fill out the designated official form(s): {', '.join(form_names)}.",
                    "required_documents": [],
                    "official_portal_or_form": prescribed_forms[0].get("official_download_url")
                })
            resolution_steps.append({
                "step_number": len(resolution_steps) + 1,
                "title": f"Submit via {channel.title()}",
                "description": f"Submit documentation to {authority} through the verified {channel} channel.",
                "required_documents": [],
                "official_portal_or_form": portal
            })

            # Format forms
            mapped_forms = []
            for pf in prescribed_forms:
                mapped_forms.append({
                    "form_id": pf.get("form_id", ""),
                    "form_name": pf.get("form_name", ""),
                    "document_category": res_mapping.get("target_document_category", "general"),
                    "purpose": pf.get("purpose", ""),
                    "issuing_authority": pf.get("issuing_authority", authority),
                    "official_download_url": pf.get("official_download_url", ""),
                    "verification_status": "verified",
                    "is_active": True
                })

            return GroundedAnswer(
                answer=full_answer,
                issue_summary=f"Discrepancy in {field_name}: {classification}",
                resolution_steps=resolution_steps,
                relevant_forms=mapped_forms or relevant_forms,
                potential_future_implications=[
                    {
                        "area": "Identity Verification",
                        "risk_assessment": "conditional",
                        "explanation": "Uncorrected discrepancies between records may lead to administrative delays during verification.",
                        "suggested_action": f"Resolve via {proc_name} prior to high-stakes filings."
                    }
                ],
                uncertainties=[] if not findings.get("requires_manual_review") else ["Manual official verification required."],
                citations=citations[:3],
                requires_clarification=bool(findings.get("requires_manual_review")),
                confidence="supported" if citations else "partially_supported",
                is_fallback=True,
                provider_status="fallback_offline"
            )

        # 3. Generic question with retrieved chunks
        top_chunk = retrieved_chunks[0] if retrieved_chunks else {}
        authority = top_chunk.get("issuing_authority", "Official Authority")
        title = top_chunk.get("title", "Official Guidance")
        content = top_chunk.get("content", "")

        answer_text = (
            f"**[Verified Statutory Guidance — {authority}]**\n\n"
            f"Based on official documentation for *{title}*:\n\n"
            f"{content[:500]}...\n\n"
            f"For complete official procedures, consult the verified source at {top_chunk.get('source_url')}.\n\n"
            f"---\n{MANDATORY_STATUTORY_DISCLAIMER}"
        )

        return GroundedAnswer(
            answer=answer_text,
            issue_summary=title,
            resolution_steps=[],
            relevant_forms=relevant_forms,
            potential_future_implications=[],
            uncertainties=["Live AI synthesis offline; response presented from verified statutory circular."],
            citations=citations[:3],
            requires_clarification=False,
            confidence="supported" if citations else "partially_supported",
            is_fallback=True,
            provider_status="fallback_offline"
        )

    def generate_answer(
        self,
        question: str,
        case_context: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
        relevant_forms: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> GroundedAnswer:
        # 1. First check relevance floor on retrieved evidence: explicit abstention if empty AND no deterministic mapping
        if not retrieved_chunks and not case_context.get("resolution_mapping"):
            return GroundedAnswer(
                answer=(
                    "No official procedural guidance could be verified for this specific question above "
                    "the relevance threshold (>= 0.55). Please ensure the inquiry pertains to supported Indian "
                    f"identity documents (Aadhaar, PAN, Passport, Class 10/12, or EPF).\n\n---\n{MANDATORY_STATUTORY_DISCLAIMER}"
                ),
                issue_summary="Evidence unavailable or below relevance floor",
                resolution_steps=[],
                relevant_forms=[],
                potential_future_implications=[],
                uncertainties=["Official government circular or procedure not found in verified knowledge repository."],
                citations=[],
                requires_clarification=False,
                confidence="insufficient_evidence",
                is_fallback=not settings.GEMINI_ENABLED,
                provider_status="insufficient_evidence"
            )

        # 2. If Gemini is unconfigured or disabled, generate safe statutory fallback
        if not settings.GEMINI_ENABLED or not self.client:
            logger.info("Google Gemini is unconfigured or disabled. Returning grounded offline statutory fallback.")
            return self._generate_offline_fallback(
                question=question,
                case_context=case_context,
                retrieved_chunks=retrieved_chunks,
                relevant_forms=relevant_forms
            )

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

        # 3. Invoke Google Gemini API with retry loop and backoff
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.generate_content(prompt)
                raw_text = response.text if response else ""

                if not raw_text or not raw_text.strip():
                    raise ValueError("Google Gemini returned empty response.")

                # Parse JSON block
                if "{" in raw_text and "}" in raw_text:
                    json_start = raw_text.find("{")
                    json_end = raw_text.rfind("}") + 1
                    parsed = json.loads(raw_text[json_start:json_end])
                    parsed["relevant_forms"] = relevant_forms
                    return GroundedOutputValidator.validate_and_filter_citations(
                        raw_answer_dict=parsed,
                        retrieved_chunks=retrieved_chunks,
                        case_context=case_context,
                        is_fallback=False,
                        provider_status="operational"
                    )
                else:
                    raise ValueError("Google Gemini response did not contain valid JSON.")

            except Exception as e:
                err_msg = str(e).lower()
                # Non-retryable authentication / permissions errors: fail to fallback immediately
                if any(err_token in err_msg for err_token in ["401", "403", "unauthenticated", "permission_denied", "api_key", "invalid api key"]):
                    logger.error("Google Gemini authentication/permission error: %s. Reverting to statutory fallback.", str(e))
                    return self._generate_offline_fallback(
                        question=question,
                        case_context=case_context,
                        retrieved_chunks=retrieved_chunks,
                        relevant_forms=relevant_forms
                    )

                # Transient errors (429 rate limit, 503 service unavailable, timeouts)
                if attempt < self.max_retries:
                    delay = (self.backoff_factor ** attempt) * 0.5
                    logger.warning("Gemini transient failure (attempt %d/%d): %s. Retrying in %.1fs...", attempt + 1, self.max_retries, str(e), delay)
                    time.sleep(delay)
                else:
                    logger.error("Google Gemini exhausted %d retries: %s. Falling back to offline statutory resolution.", self.max_retries, str(e))
                    return self._generate_offline_fallback(
                        question=question,
                        case_context=case_context,
                        retrieved_chunks=retrieved_chunks,
                        relevant_forms=relevant_forms
                    )

        # Fallback if loop exits without returning
        return self._generate_offline_fallback(
            question=question,
            case_context=case_context,
            retrieved_chunks=retrieved_chunks,
            relevant_forms=relevant_forms
        )


def get_llm_provider() -> BaseLLMProvider:
    """Returns Google Gemini provider ONLY. No other LLM providers allowed."""
    return GoogleGeminiProvider(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL
    )
