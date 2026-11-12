import json
import time
import logging
from typing import Dict, Any, List, Optional

from app.config import settings
from app.core.sanitizer import sanitize_pii
from app.core.security_monitoring import record_security_event
from app.rag.generation.prompt_templates import (
    SYSTEM_PROMPT,
    detect_prompt_injection,
    format_rag_prompt,
    sanitize_untrusted_text,
)
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
                    system_instruction=SYSTEM_PROMPT,
                    generation_config={"response_mime_type": "application/json"}
                )
                self.raw_client = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=SYSTEM_PROMPT,
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
            if detect_prompt_injection(prompt):
                record_security_event("prompt_injection_detected", component="ai", outcome="flagged")
            sanitized_prompt, _, _ = sanitize_pii(prompt, include_address=True)
            safe_prompt = sanitize_untrusted_text(sanitized_prompt)
            if system_instruction:
                client = self.raw_client
                try:
                    import google.generativeai as genai
                    client = genai.GenerativeModel(
                        model_name=self.model_name,
                        system_instruction=system_instruction,
                    )
                except Exception:
                    safe_prompt = f"<system_instruction>{system_instruction}</system_instruction>\n\n<user_prompt>{safe_prompt}</user_prompt>"
                response = client.generate_content(
                    safe_prompt,
                    request_options={"timeout": float(self.timeout_seconds)}
                )
            else:
                response = self.raw_client.generate_content(
                    safe_prompt,
                    request_options={"timeout": float(self.timeout_seconds)}
                )
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
            sid = c.get("source_id") or c.get("document_id")
            title = c.get("document_title") or c.get("title", "Official Guidance")
            if sid and str(c.get("verification_status", "verified")).lower() in ("verified", "needs_review"):
                citations.append(
                    SourceCitation(
                        source_id=sid,
                        title=title,
                        authority=c.get("issuing_authority", "Government Authority"),
                        url=c.get("source_url", ""),
                        verification_status=c.get("verification_status", "verified")
                    )
                )

        attachments = case_context.get("attachments") or []
        for att in attachments:
            fname = att.get("file_name", "Uploaded Document")
            citations.append(
                SourceCitation(
                    source_id=f"attachment_{att.get('id', '')}",
                    title=f"Uploaded Evidence: {fname}",
                    authority="Citizen Submitted Document",
                    url="",
                    verification_status="unverified"
                )
            )

        # 2. Build Document Analysis Section if attachments are present
        att_section = ""
        has_low_confidence = False
        if attachments:
            att_blocks = []
            for att in attachments:
                fname = att.get("file_name", "Uploaded Document")
                dtype = att.get("detected_type", "supporting_document").replace("_", " ").title()
                conf = att.get("ocr_confidence")
                conf_pct = f"{int(conf * 100)}%" if conf is not None else "N/A"
                ocr_st = att.get("ocr_status", "completed")

                block = [
                    f"### [Document Evidence: {fname}]",
                    f"• **Detected Document Category**: {dtype}",
                    f"• **OCR Recognition Quality**: {conf_pct} ({ocr_st.replace('_', ' ').title()})"
                ]

                if ocr_st == "low_confidence" or (conf is not None and conf < 0.60):
                    has_low_confidence = True
                    block.append("⚠️ **OCR Quality Warning**: Recognition confidence is below 60%. Certain characters, numerals, or stamps may be degraded. Official manual verification is required.")

                dates = att.get("dates_found", [])
                if dates:
                    block.append(f"• **Relevant Dates Identified**: {', '.join(dates)}")

                reasons = att.get("rejection_reasons", [])
                if reasons:
                    block.append(f"• **Stated Rejection / Deficiency Observations**:\n  - " + "\n  - ".join(reasons))

                masked_ids = att.get("masked_identifiers", {})
                if masked_ids:
                    id_strs = [f"{k.replace('_', ' ').title()}: {v}" for k, v in masked_ids.items()]
                    block.append(f"• **Protected Identifiers Detected**: {', '.join(id_strs)}")

                txt = (att.get("extracted_text") or "").strip()
                if txt:
                    snip = txt[:350].replace("\n", " ").strip()
                    if len(txt) > 350:
                        snip += "..."
                    block.append(f"• **Extracted Content Excerpt**:\n  > \"{snip}\"")

                att_blocks.append("\n".join(block))

            att_section = "\n\n".join(att_blocks)

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

            if att_section:
                full_answer = f"{att_section}\n\n---\n\n{layer_a}\n\n{layer_b}\n\n{layer_c}\n\n---\n{MANDATORY_STATUTORY_DISCLAIMER}"
            else:
                full_answer = f"{layer_a}\n\n{layer_b}\n\n{layer_c}\n\n---\n{MANDATORY_STATUTORY_DISCLAIMER}"

            # Check for Tamil or Hindi translation request
            q_lower = question.lower()
            if "tamil" in q_lower or "தமிழ்" in q_lower or case_context.get("language") == "ta":
                full_answer += (
                    f"\n\n**[தமிழ் மொழிபெயர்ப்பு / Tamil Summary]**\n"
                    f"அடையாள ஆவண முரண்பாடு: '{field_name}' விவரத்தில் முரண்பாடு கண்டறியப்பட்டுள்ளது. "
                    f"சம்பந்தப்பட்ட {authority} துறையின் '{proc_name}' நடைமுறை மூலம் சரிபார்க்கப்பட்ட படிவத்தை சமர்ப்பித்து திருத்தம் செய்யவும்."
                )
            elif "hindi" in q_lower or "हिन्दी" in q_lower or case_context.get("language") == "hi":
                full_answer += (
                    f"\n\n**[हिन्दी अनुवाद / Hindi Summary]**\n"
                    f"पहचान दस्तावेज़ विसंगति: '{field_name}' में विसंगति पाई गई है। "
                    f"कृपया {authority} के आधिकारिक पोर्टल पर '{proc_name}' के माध्यम से सुधार हेतु आवेदन करें।"
                )

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
        title = top_chunk.get("document_title") or top_chunk.get("title", "Official Guidance")
        content = top_chunk.get("chunk_text") or top_chunk.get("content", "")
        doc043_disclaimer = top_chunk.get("disclaimer")

        # 3. Document Attachment question or generic question
        q_lower = question.lower()
        if att_section:
            answer_text = (
                f"**[Citizen Document Analysis & Evidence Review]**\n\n"
                f"{att_section}\n\n"
            )
            if top_chunk and content:
                answer_text += (
                    f"**[Statutory Cross-Reference — {authority}]**\n"
                    f"Based on official documentation for *{title}*:\n"
                    f"{content[:400]}...\n\n"
                    f"Verified source portal: {top_chunk.get('source_url')}\n\n"
                )

            # Multilingual response
            if "tamil" in q_lower or "தமிழ்" in q_lower or case_context.get("language") == "ta":
                answer_text += (
                    f"**[தமிழ் வழிகாட்டல் / Tamil Guidance]**\n"
                    f"நீங்கள் பதிவேற்றிய ஆவணம் பகுப்பாய்வு செய்யப்பட்டது. "
                    f"அதில் உள்ள தகவல்களை சரிபார்த்து அதிகாரப்பூர்வ நடைமுறைப்படி விண்ணப்பிக்கவும்.\n\n"
                )
            elif "hindi" in q_lower or "हिन्दी" in q_lower or case_context.get("language") == "hi":
                answer_text += (
                    f"**[हिन्दी मार्गदर्शन / Hindi Guidance]**\n"
                    f"आपके द्वारा अपलोड किए गए दस्तावेज़ का विश्लेषण किया गया है। "
                    f"कृपया आधिकारिक प्रक्रिया के अनुसार उचित कदम उठाएं।\n\n"
                )

            answer_text += f"---\n{MANDATORY_STATUTORY_DISCLAIMER}"
            issue_title = "Document Analysis & Evidence Review"
        else:
            disclaimer_block = f"\n\n> ⚠️ **{doc043_disclaimer}**\n\n" if doc043_disclaimer else ""
            answer_text = (
                f"**[Verified Statutory Guidance — {authority}]**\n\n"
                f"Based on official documentation for *{title}*:\n\n"
                f"{content[:500]}...\n\n"
                f"{disclaimer_block}"
                f"For complete official procedures, consult the verified source at {top_chunk.get('source_url', 'official portal')}.\n\n"
                f"---\n{MANDATORY_STATUTORY_DISCLAIMER}"
            )
            issue_title = title

        return GroundedAnswer(
            answer=answer_text,
            issue_summary=issue_title,
            resolution_steps=[],
            relevant_forms=relevant_forms,
            potential_future_implications=[],
            uncertainties=["Live AI synthesis offline; response presented from verified statutory circular."] if not att_section else ([] if not has_low_confidence else ["OCR confidence below 60%; manual review required."]),
            citations=citations[:3],
            requires_clarification=has_low_confidence,
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
        # 1. First check relevance floor on retrieved evidence: explicit abstention if empty AND no deterministic mapping AND no attachments
        if not retrieved_chunks and not case_context.get("resolution_mapping") and not case_context.get("attachments"):
            return GroundedAnswer(
                answer=(
                    "NO_VERIFIED_PROCEDURE_AVAILABLE: No official procedural guidance could be verified for this specific question above "
                    "the relevance threshold (>= 0.55). Please ensure the inquiry pertains to supported Indian "
                    f"identity documents (Aadhaar, PAN, Passport, Class 10/12, or EPF).\n\n---\n{MANDATORY_STATUTORY_DISCLAIMER}"
                ),
                issue_summary="Evidence unavailable or below relevance floor",
                resolution_steps=[],
                relevant_forms=[],
                potential_future_implications=[],
                uncertainties=["NO_VERIFIED_PROCEDURE_AVAILABLE", "Official government circular or procedure not found in verified knowledge repository."],
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

        if detect_prompt_injection(question) or any(
            detect_prompt_injection(m.get("content", "")) for m in conversation_history
        ):
            record_security_event("prompt_injection_detected", component="ai", outcome="flagged")

        sanitized_question, _, _ = sanitize_pii(question, include_address=True)
        case_context_raw = json.dumps(case_context, indent=2)
        sanitized_case_context, _, _ = sanitize_pii(case_context_raw, include_address=True)
        evidence_str = "\n\n---\n\n".join([
            f"[Source ID: {c.get('source_id')} | Authority: {c.get('issuing_authority')} | URL: {c.get('source_url')}]\n{c.get('content')}"
            for c in retrieved_chunks
        ])
        history_raw = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in conversation_history])
        sanitized_history, _, _ = sanitize_pii(history_raw, include_address=True)

        prompt = format_rag_prompt(
            question=sanitized_question,
            case_context_str=sanitized_case_context,
            evidence_str=evidence_str,
            conversation_history_str=sanitized_history,
            include_system_prompt=False,
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
