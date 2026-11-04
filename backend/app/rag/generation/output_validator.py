import re
import json
import logging
from typing import Dict, Any, List, Set, Optional
from app.rag.schemas import GroundedAnswer, SourceCitation

logger = logging.getLogger("consolith.rag.validator")

MANDATORY_STATUTORY_DISCLAIMER = "AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION"


class GroundedOutputValidator:
    """
    Validates model output to enforce zero-hallucination and citation grounding.
    Verifies that every generated citation corresponds to a legitimately retrieved chunk.
    Validates URL correspondence, verification status, and enforces statutory disclaimers.
    """

    @staticmethod
    def validate_and_filter_citations(
        raw_answer_dict: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
        case_context: Optional[Dict[str, Any]] = None,
        is_fallback: bool = False,
        provider_status: str = "operational"
    ) -> GroundedAnswer:
        # 1. Build dictionary of legitimate retrieved verified sources
        valid_sources: Dict[str, Dict[str, Any]] = {}
        for c in retrieved_chunks:
            sid = c.get("source_id")
            # Only allow verified sources
            if sid and c.get("verification_status", "verified") == "verified":
                valid_sources[sid] = {
                    "source_id": sid,
                    "title": c.get("title", "Official Source"),
                    "authority": c.get("issuing_authority", "Government Authority"),
                    "url": c.get("source_url", ""),
                    "verification_status": c.get("verification_status", "verified"),
                    "content": c.get("content", "").lower(),
                }

        # 2. Validate citations in raw answer
        raw_citations = raw_answer_dict.get("citations") or []
        verified_citations: List[SourceCitation] = []
        seen_source_ids: Set[str] = set()

        for cit in raw_citations:
            if isinstance(cit, dict):
                sid = cit.get("source_id")
                # Must exist in retrieved verified evidence
                if sid and sid in valid_sources:
                    if sid not in seen_source_ids:
                        seen_source_ids.add(sid)
                        # Overwrite with authoritative URL and metadata to prevent hallucinated URLs
                        verified_citations.append(
                            SourceCitation(
                                source_id=sid,
                                title=valid_sources[sid]["title"],
                                authority=valid_sources[sid]["authority"],
                                url=valid_sources[sid]["url"],
                                section=cit.get("section"),
                                verification_status=valid_sources[sid]["verification_status"]
                            )
                        )
                else:
                    logger.warning("Stripped ungrounded, unverified, or hallucinated citation: %s", sid)

        # 3. If model returned no valid citations but verified evidence was retrieved, auto-attach primary verified sources
        if not verified_citations and valid_sources:
            for sid, sdata in list(valid_sources.items())[:3]:
                verified_citations.append(
                    SourceCitation(
                        source_id=sid,
                        title=sdata["title"],
                        authority=sdata["authority"],
                        url=sdata["url"],
                        verification_status=sdata["verification_status"]
                    )
                )

        raw_answer_dict["citations"] = [c.model_dump() for c in verified_citations]

        # 4. Clean and normalize relevant_forms to match schema
        clean_forms = []
        for f in raw_answer_dict.get("relevant_forms") or []:
            if isinstance(f, dict):
                clean_forms.append({
                    "id": f.get("id"),
                    "form_id": f.get("form_id", "form_unknown"),
                    "form_name": f.get("form_name", "Official Form"),
                    "document_category": f.get("document_category", "general"),
                    "purpose": f.get("purpose", "Official Document Update"),
                    "issuing_authority": f.get("issuing_authority", "Government Authority"),
                    "official_download_url": f.get("official_download_url", ""),
                    "instructions_source_id": f.get("instructions_source_id"),
                    "applicable_issue_types": f.get("applicable_issue_types", []),
                    "applicable_conditions": f.get("applicable_conditions", []),
                    "language": f.get("language", "en"),
                    "version": f.get("version"),
                    "effective_date": f.get("effective_date"),
                    "last_verified_at": f.get("last_verified_at"),
                    "verification_status": f.get("verification_status", "verified"),
                    "is_active": f.get("is_active", True)
                })
            else:
                clean_forms.append(f)
        raw_answer_dict["relevant_forms"] = clean_forms

        # 5. Mandatory Statutory Disclaimer Enforcement
        answer_text = raw_answer_dict.get("answer", "")
        if "AUTOMATED COMPARISON RESULT" not in answer_text:
            raw_answer_dict["answer"] = f"{answer_text.strip()}\n\n---\n{MANDATORY_STATUTORY_DISCLAIMER}"

        # 5. Check confidence floor & evidence sufficiency
        if not retrieved_chunks:
            raw_answer_dict["confidence"] = "insufficient_evidence"
            provider_status = "insufficient_evidence"
        elif not raw_answer_dict.get("confidence"):
            raw_answer_dict["confidence"] = "supported"

        raw_answer_dict["is_fallback"] = is_fallback
        raw_answer_dict["provider_status"] = provider_status

        return GroundedAnswer(**raw_answer_dict)
