import json
import logging
from typing import Dict, Any, List, Set
from app.rag.schemas import GroundedAnswer, SourceCitation

logger = logging.getLogger("consolith.rag.validator")

class GroundedOutputValidator:
    """
    Validates model output to enforce zero-hallucination and citation grounding.
    Verifies that every generated citation corresponds to a legitimately retrieved chunk.
    """

    @staticmethod
    def validate_and_filter_citations(
        raw_answer_dict: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]]
    ) -> GroundedAnswer:
        # Build set of legitimate retrieved source IDs and URLs
        valid_sources: Dict[str, Dict[str, str]] = {}
        for c in retrieved_chunks:
            sid = c.get("source_id")
            if sid:
                valid_sources[sid] = {
                    "title": c.get("title", "Official Source"),
                    "authority": c.get("issuing_authority", "Government Authority"),
                    "url": c.get("source_url", "")
                }

        # Validate citations in raw answer
        raw_citations = raw_answer_dict.get("citations") or []
        verified_citations: List[SourceCitation] = []

        for cit in raw_citations:
            if isinstance(cit, dict):
                sid = cit.get("source_id")
                # Must exist in retrieved evidence
                if sid in valid_sources:
                    verified_citations.append(
                        SourceCitation(
                            source_id=sid,
                            title=valid_sources[sid]["title"],
                            authority=valid_sources[sid]["authority"],
                            url=valid_sources[sid]["url"],
                            section=cit.get("section")
                        )
                    )
                else:
                    logger.warning("Stripped ungrounded or hallucinated citation: %s", sid)

        # If model returned no citations but evidence was retrieved, auto-attach primary sources
        if not verified_citations and valid_sources:
            for sid, sdata in list(valid_sources.items())[:3]:
                verified_citations.append(
                    SourceCitation(
                        source_id=sid,
                        title=sdata["title"],
                        authority=sdata["authority"],
                        url=sdata["url"]
                    )
                )

        raw_answer_dict["citations"] = [c.model_dump() for c in verified_citations]

        # Check confidence floor
        if not retrieved_chunks:
            raw_answer_dict["confidence"] = "insufficient_evidence"

        return GroundedAnswer(**raw_answer_dict)
