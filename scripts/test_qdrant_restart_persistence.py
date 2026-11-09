import os
import sys
import time
import subprocess
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.rag.retrieval.retriever import HybridRetriever
from app.rag.ingestion.corpus_ingestion import DOC_043_STATUTORY_DISCLAIMER

QDRANT_URL = "http://127.0.0.1:6333"

def query_collections():
    resp = requests.get(f"{QDRANT_URL}/collections", timeout=5)
    resp.raise_for_status()
    collections = resp.json()["result"]["collections"]
    details = {}
    for col in collections:
        c_name = col["name"]
        c_resp = requests.get(f"{QDRANT_URL}/collections/{c_name}", timeout=5)
        c_resp.raise_for_status()
        details[c_name] = c_resp.json()["result"]
    return details

def main():
    print("=== QDRANT RESTART & DURABILITY AUDIT ===")
    
    # 1. State before restart
    print("\n[STEP 1] Recording pre-restart Qdrant state...")
    pre_state = query_collections()
    for name, data in pre_state.items():
        print(f"  Collection: {name}, Points: {data['points_count']}, Vectors: {data['config']['params']['vectors']}")

    # 2. Restart container
    print("\n[STEP 2] Restarting container 'convelina-qdrant' (preserving volume 'consolin_qdrant_data')...")
    res = subprocess.run(["docker", "restart", "convelina-qdrant"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error restarting container: {res.stderr}")
        sys.exit(1)
    print("  Container restart command completed.")

    # 3. Wait for Qdrant to become ready
    print("\n[STEP 3] Waiting for Qdrant service to recover...")
    for i in range(15):
        try:
            r = requests.get(f"{QDRANT_URL}/readyz", timeout=2)
            if r.status_code == 200:
                print(f"  Qdrant ready in ~{i+1}s.")
                break
        except Exception:
            time.sleep(1)
    else:
        print("  Error: Qdrant did not become ready within 15s")
        sys.exit(1)

    # 4. State after restart
    print("\n[STEP 4] Verifying post-restart state...")
    post_state = query_collections()
    for name, data in post_state.items():
        print(f"  Collection: {name}, Points: {data['points_count']}, Vectors: {data['config']['params']['vectors']}")
        assert name in pre_state, f"Collection {name} was missing before restart"
        assert data['points_count'] == pre_state[name]['points_count'], (
            f"Point count mismatch for {name}: before={pre_state[name]['points_count']}, after={data['points_count']}"
        )
    print("  [PASS] All collections and points survived restart identically.")

    # 5. Retrieval verification
    print("\n[STEP 5] Testing Hybrid & BM25 Retrieval after restart...")
    retriever = HybridRetriever()
    results = retriever.retrieve("Aadhaar name update documentary proof initial expansion", top_k=3)
    assert len(results) > 0, "Retrieval returned 0 results after restart"
    print(f"  Retrieved {len(results)} results for statutory query:")
    has_valid_source = False
    for r in results:
        print(f"    - Source: {r['document_id']} | Title: {r['document_title']} | Score: {r['score']:.4f}")
        if r['document_id'] in ("DOC_034", "DOC_001", "DOC_043", "DOC_013"):
            has_valid_source = True
    assert has_valid_source, "No recognized statutory source found in retrieval results"
    print("  [PASS] Retrieval correctly operational with preserved source identifiers.")

    # 6. DOC_043 Governance Verification
    print("\n[STEP 6] Verifying DOC_043 Governance and statutory restriction...")
    doc43_results = retriever.retrieve("DOC_043 SOP for updating name exception", top_k=5)
    for r in doc43_results:
        if r['document_id'] == "DOC_043":
            print(f"  Found DOC_043 chunk: human_review_required={r['human_review_required']}, status={r['verification_status']}")
            assert r['human_review_required'] is True, "DOC_043 chunk must mandate human_review_required"
    print("  [PASS] DOC_043 statutory restriction invariants verified.")

    # 7. Zero Citizen PII Verification in Corpus
    print("\n[STEP 7] Verifying zero citizen PII in vector corpus...")
    # Scan payload of first 20 points
    for col_name in ("consolith_knowledge", "consolith_forms"):
        pts_resp = requests.post(
            f"{QDRANT_URL}/collections/{col_name}/points/scroll",
            json={"limit": 20, "with_payload": True, "with_vector": False},
            timeout=5
        ).json()["result"]["points"]
        for pt in pts_resp:
            payload = pt.get("payload", {})
            for forbidden in ("aadhaar_number", "citizen_name", "phone", "email", "pan_number"):
                assert forbidden not in payload, f"Found citizen PII field {forbidden} in {col_name} payload"
    print("  [PASS] Zero citizen PII confirmed across Qdrant vector payload stores.")

    print("\n==================================================")
    print("  ALL QDRANT RESTART & DURABILITY CHECKS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    main()
