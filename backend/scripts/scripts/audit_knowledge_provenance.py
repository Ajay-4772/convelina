"""
CONVELINA — Phase P3F.3
Part D: Knowledge Source Provenance Inventory & Verification Script

Inventories all knowledge sources in OFFICIAL_SOURCES_DATA:
- Original source identity (source_id)
- Official authority
- Original URL
- Source document title
- Publication / effective date
- Last verification date
- Verification status
- Content SHA-256 hash
- Document provenance (official statutory circular vs synthetic test asset)
- Applicable document category and correction type
- Chunk count and total character length
"""

import sys
import hashlib
from typing import Dict, Any, List

sys.path.insert(0, "/app")

from app.rag.ingestion.sources import OFFICIAL_SOURCES_DATA
from app.rag.ingestion.chunker import DocumentChunker


def run_provenance_audit():
    print("==================================================================")
    print("CONVELINA — Phase P3F.3: Knowledge Source Provenance Inventory")
    print("==================================================================")
    print(f"Total Sources Configured: {len(OFFICIAL_SOURCES_DATA)}\n")

    chunker = DocumentChunker()
    total_chunks = 0
    verified_sources = 0
    unverified_sources = 0

    for idx, src in enumerate(OFFICIAL_SOURCES_DATA, start=1):
        content = src.get("content", "").strip()
        c_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        chunks = chunker.chunk_source(src)
        n_chunks = len(chunks)
        total_chunks += n_chunks

        status = src.get("verification_status", "unverified")
        if status == "verified":
            verified_sources += 1
        else:
            unverified_sources += 1

        print(f"Source #{idx}: [{src.get('source_id')}]")
        print(f"  • Title             : {src.get('title')}")
        print(f"  • Issuing Authority : {src.get('issuing_authority')}")
        print(f"  • Official URL      : {src.get('source_url')}")
        print(f"  • Category / Type   : {src.get('document_category')} / {src.get('document_type')}")
        print(f"  • Version / Dates   : Version={src.get('version')} | Effective={src.get('effective_date')} | Last Verified={src.get('last_verified_at')}")
        print(f"  • Verification St.  : {status.upper()} (Active: {src.get('is_active')})")
        print(f"  • Provenance        : {src.get('provenance', 'STATUTORY_CIRCULAR')}")
        print(f"  • Content SHA-256   : {c_hash}")
        print(f"  • Chunks Generated  : {n_chunks} chunks ({len(content)} total characters)")
        print("")

    print("==================================================================")
    print("PROVENANCE SUMMARY")
    print("==================================================================")
    print(f"Total Knowledge Sources: {len(OFFICIAL_SOURCES_DATA)}")
    print(f"Verified Sources       : {verified_sources}")
    print(f"Unverified Sources     : {unverified_sources}")
    print(f"Total Chunks Generated : {total_chunks}")
    print("==================================================================")


if __name__ == "__main__":
    run_provenance_audit()

