import json
import logging
from typing import Dict, Any, List, Optional

from app.config import settings
from app.rag.generation.prompt_templates import format_rag_prompt
from app.rag.generation.output_validator import GroundedOutputValidator
from app.rag.schemas import GroundedAnswer

logger = logging.getLogger("consolith.rag.llm")

SERVICE_UNAVAILABLE_MESSAGE = "Assistant service is not currently available. Please try again later."
GEMINI_UNAVAILABLE_MESSAGE = SERVICE_UNAVAILABLE_MESSAGE


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
    - Never uses a rule-based generator as an alternative when Gemini fails.
    - If Gemini fails (API error, timeout, quota, invalid JSON, or missing key),
      returns exactly: "Assistant service is not currently available. Please try again later."
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        self.client = None
        self.raw_client = None

        if self.api_key:
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

    def generate_answer(
        self,
        question: str,
        case_context: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
        relevant_forms: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> GroundedAnswer:
        # 1. First check relevance floor on retrieved evidence
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

        # 2. If Gemini is unconfigured or failed initialization, fail safely with the exact required message
        if not self.client:
            logger.error("Google Gemini client unavailable or unconfigured.")
            return GroundedAnswer(
                answer=SERVICE_UNAVAILABLE_MESSAGE,
                issue_summary=None,
                resolution_steps=[],
                relevant_forms=[],
                potential_future_implications=[],
                uncertainties=["AI assistant service currently unavailable."],
                citations=[],
                requires_clarification=False,
                confidence="insufficient_evidence"
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

        # 3. Invoke Google Gemini API
        try:
            response = self.client.generate_content(prompt)
            raw_text = response.text if response else ""

            if not raw_text or not raw_text.strip():
                logger.error("Google Gemini returned empty response.")
                return GroundedAnswer(
                    answer=SERVICE_UNAVAILABLE_MESSAGE,
                    confidence="insufficient_evidence"
                )

            # Parse JSON block
            if "{" in raw_text and "}" in raw_text:
                json_start = raw_text.find("{")
                json_end = raw_text.rfind("}") + 1
                parsed = json.loads(raw_text[json_start:json_end])
                parsed["relevant_forms"] = relevant_forms
                return GroundedOutputValidator.validate_and_filter_citations(parsed, retrieved_chunks)
            else:
                logger.error("Google Gemini response did not contain valid JSON.")
                return GroundedAnswer(
                    answer=SERVICE_UNAVAILABLE_MESSAGE,
                    confidence="insufficient_evidence"
                )

        except Exception as e:
            logger.error("Google Gemini API call failed: %s", str(e), exc_info=True)
            return GroundedAnswer(
                answer=SERVICE_UNAVAILABLE_MESSAGE,
                issue_summary=None,
                resolution_steps=[],
                relevant_forms=[],
                potential_future_implications=[],
                uncertainties=["Upstream LLM request failed."],
                citations=[],
                requires_clarification=False,
                confidence="insufficient_evidence"
            )


def get_llm_provider() -> BaseLLMProvider:
    """Returns Google Gemini provider ONLY. No other LLM providers allowed."""
    return GoogleGeminiProvider(
        api_key=settings.GEMINI_API_KEY,
        model=settings.GEMINI_MODEL
    )
