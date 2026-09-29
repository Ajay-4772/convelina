import re
import hashlib
from typing import List, Dict, Any

class DocumentChunker:
    """
    Semantic chunker designed for official government procedural guides and circulars.
    Splits by hierarchical Markdown headings (H1, H2, H3) and paragraphs while
    preserving source provenance, section context, and metadata on every chunk.
    """

    def __init__(self, max_chunk_chars: int = 1200, chunk_overlap: int = 150):
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap = chunk_overlap

    def chunk_source(self, source_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        raw_text = source_dict.get("content", "").strip()
        if not raw_text:
            return []

        source_id = source_dict["source_id"]
        title = source_dict["title"]
        authority = source_dict["issuing_authority"]
        category = source_dict["document_category"]
        url = source_dict["source_url"]
        status = source_dict.get("verification_status", "verified")

        # Split on markdown headers: #, ##, ###
        sections = re.split(r'\n(?=#{1,3}\s)', raw_text)
        chunks: List[Dict[str, Any]] = []
        chunk_idx = 0

        for section in sections:
            sec_clean = section.strip()
            if not sec_clean:
                continue

            # Extract heading if present
            lines = sec_clean.split("\n")
            heading = ""
            if lines[0].startswith("#"):
                heading = lines[0].lstrip("#").strip()

            # If section is small enough, make it a chunk
            if len(sec_clean) <= self.max_chunk_chars:
                chunk_id = f"{source_id}_c{chunk_idx:03d}"
                content_payload = f"[{title} | {heading}]\n{sec_clean}" if heading else f"[{title}]\n{sec_clean}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "source_id": source_id,
                    "title": title,
                    "issuing_authority": authority,
                    "document_category": category,
                    "source_url": url,
                    "heading": heading,
                    "content": content_payload,
                    "verification_status": status,
                    "chunk_hash": hashlib.sha256(content_payload.encode("utf-8")).hexdigest()
                })
                chunk_idx += 1
            else:
                # Sub-split into paragraphs
                paragraphs = sec_clean.split("\n\n")
                buf = ""
                for p in paragraphs:
                    p_str = p.strip()
                    if not p_str:
                        continue
                    if len(buf) + len(p_str) < self.max_chunk_chars:
                        buf += ("\n\n" + p_str if buf else p_str)
                    else:
                        if buf:
                            chunk_id = f"{source_id}_c{chunk_idx:03d}"
                            content_payload = f"[{title} | {heading}]\n{buf}" if heading else f"[{title}]\n{buf}"
                            chunks.append({
                                "chunk_id": chunk_id,
                                "source_id": source_id,
                                "title": title,
                                "issuing_authority": authority,
                                "document_category": category,
                                "source_url": url,
                                "heading": heading,
                                "content": content_payload,
                                "verification_status": status,
                                "chunk_hash": hashlib.sha256(content_payload.encode("utf-8")).hexdigest()
                            })
                            chunk_idx += 1
                        buf = p_str

                if buf:
                    chunk_id = f"{source_id}_c{chunk_idx:03d}"
                    content_payload = f"[{title} | {heading}]\n{buf}" if heading else f"[{title}]\n{buf}"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "source_id": source_id,
                        "title": title,
                        "issuing_authority": authority,
                        "document_category": category,
                        "source_url": url,
                        "heading": heading,
                        "content": content_payload,
                        "verification_status": status,
                        "chunk_hash": hashlib.sha256(content_payload.encode("utf-8")).hexdigest()
                    })
                    chunk_idx += 1

        return chunks
