"""
CONVELINA — RAG Retrieval Evaluation Benchmark (Phase P3F.2)
Compares 4 retrieval architectures against an authoritative Indian statutory procedural dataset:
1. Deterministic Hash Embedding Retrieval (Current CPU baseline)
2. Lexical Token Overlap Retrieval (BM25 / Token matching)
3. Genuine Semantic Neural Retrieval (FastEmbed ONNX)
4. Hybrid Retrieval (Neural Dense + Lexical Overlap + Metadata Filter + Relevance Floor)

Evaluates:
- Exact wording queries
- Paraphrased queries
- Synonyms (zero token overlap)
- Different word order
- Short questions
- Long natural language questions
- Irrelevant queries (abstention test)
- Conflicting-source queries

Metrics:
- Recall@1, Recall@3, Recall@5
- Precision@1, Precision@3, Precision@5
- Mean Reciprocal Rank (MRR)
- nDCG@5
- Irrelevant Query Rejection Rate (%)
"""

import math
import time
import json
import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

import sys
sys.path.insert(0, "/app")

from app.rag.ingestion.sources import OFFICIAL_SOURCES_DATA
from app.rag.ingestion.chunker import DocumentChunker
from app.rag.embeddings import DeterministicHashEmbeddingService, FastEmbedEmbeddingService


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def dcg_at_k(relevances: List[int], k: int = 5) -> float:
    dcg = 0.0
    for i in range(min(len(relevances), k)):
        rel = relevances[i]
        dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg


def ndcg_at_k(retrieved_ids: List[str], target_ids: List[str], k: int = 5) -> float:
    relevances = [1 if r_id in target_ids else 0 for r_id in retrieved_ids[:k]]
    actual_dcg = dcg_at_k(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    ideal_dcg = dcg_at_k(ideal_relevances, k)
    if ideal_dcg <= 1e-9:
        return 1.0 if not target_ids else 0.0
    return actual_dcg / ideal_dcg


# Chunk the authoritative knowledge corpus
chunker = DocumentChunker()
CORPUS_CHUNKS = []
for src in OFFICIAL_SOURCES_DATA:
    if src.get("is_active", True) and src.get("verification_status") == "verified":
        chunks = chunker.chunk_source(src)
        for c in chunks:
            CORPUS_CHUNKS.append({
                "chunk_id": c["chunk_id"],
                "source_id": c["source_id"],
                "title": c["title"],
                "heading": c.get("heading", ""),
                "content": c["content"],
                "full_text": f"{c['title']} {c.get('heading', '')} {c['content']}".strip()
            })

# Precompute embeddings
hash_service = DeterministicHashEmbeddingService(dimension=1024)
fastembed_service = FastEmbedEmbeddingService("BAAI/bge-small-en-v1.5", dimension=384)

corpus_texts = [c["full_text"] for c in CORPUS_CHUNKS]
hash_embeddings = hash_service.embed_documents(corpus_texts)
fastembed_embeddings = fastembed_service.embed_documents(corpus_texts)


RETRIEVAL_TEST_QUERIES = [
    # 1. Exact wording queries
    {
        "query": "A resident can update their name in Aadhaar up to a maximum of two times in their entire lifetime",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "exact_wording"
    },
    {
        "query": "Request For New PAN Card Or And Changes Or Correction in PAN Data commonly referred to as CSF Form",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "exact_wording"
    },

    # 2. Paraphrased queries
    {
        "query": "How many times am I allowed to modify my recorded name on my Aadhaar identity card?",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "paraphrased"
    },
    {
        "query": "What is the penalty for possessing two active PAN cards under Section 272B?",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "paraphrased"
    },

    # 3. Synonyms (zero token overlap with core heading)
    {
        "query": "Alteration of nomenclature or patronymic appellation following nuptials for women",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "synonyms"
    },
    {
        "query": "Permitted variance window for date of nativity documentation discrepancy UIDAI",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "synonyms"
    },

    # 4. Different word order
    {
        "query": "lifetime once update birth of date municipal certificate UIDAI",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "word_order"
    },
    {
        "query": "Marriage certificate husband passport female surname change PAN card",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "word_order"
    },

    # 5. Short questions
    {
        "query": "Aadhaar DOB update limit",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "short_query"
    },
    {
        "query": "PAN father name correction documents",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "short_query"
    },

    # 6. Long natural-language questions
    {
        "query": "I noticed an inconsistency where my Class 10 school certificate shows my surname as Kumar but my Aadhaar card omits it entirely. Can I update my Aadhaar using my Class 10 marksheet as proof of identity?",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "long_natural_language"
    },
    {
        "query": "My father's name on my PAN card has a typographical spelling mistake compared to my municipal birth certificate. Do I need to submit an affidavit or does the CSF form accept the birth certificate?",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "long_natural_language"
    },

    # 7. Irrelevant queries (Must abstain / return no confident results)
    {
        "query": "What is the best recipe for baking chocolate brownies with walnuts?",
        "target_source_ids": [],
        "category": "irrelevant"
    },
    {
        "query": "Tomorrow's weather forecast and rainfall probability in Bengaluru",
        "target_source_ids": [],
        "category": "irrelevant"
    },

    # 8. Conflicting-source queries
    {
        "query": "Official Gazette publication requirement for major name change across Aadhaar and PAN",
        "target_source_ids": ["src_uidai_update_policy_2024", "src_pan_correction_nsdl_2024"],
        "category": "conflicting_sources"
    }
]


def retrieve_deterministic_hash(query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    q_vec = hash_service.embed_query(query)
    scores = []
    for idx, c in enumerate(CORPUS_CHUNKS):
        c_vec = hash_embeddings[idx]
        sim = cosine_similarity(q_vec, c_vec)
        scores.append((c, sim))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def retrieve_lexical(query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    q_tokens = set(re.findall(r'\w+', query.lower()))
    stop_words = {"how", "do", "i", "my", "the", "in", "a", "an", "is", "for", "to", "what", "which", "and", "or"}
    tokens = q_tokens - stop_words
    if not tokens:
        tokens = q_tokens

    scores = []
    for c in CORPUS_CHUNKS:
        text = c["full_text"].lower()
        matched = sum(1 for t in tokens if t in text)
        score = matched / max(len(tokens), 1)
        scores.append((c, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def retrieve_semantic_neural(query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    q_vec = fastembed_service.embed_query(query)
    scores = []
    for idx, c in enumerate(CORPUS_CHUNKS):
        c_vec = fastembed_embeddings[idx]
        sim = cosine_similarity(q_vec, c_vec)
        scores.append((c, sim))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def retrieve_hybrid(query: str, top_k: int = 5, relevance_floor: float = 0.55) -> List[Tuple[Dict[str, Any], float]]:
    q_vec = fastembed_service.embed_query(query)
    q_tokens = set(re.findall(r'\w+', query.lower()))
    stop_words = {"how", "do", "i", "my", "the", "in", "a", "an", "is", "for", "to", "what", "which", "and", "or"}
    tokens = q_tokens - stop_words
    if not tokens:
        tokens = q_tokens

    scored = []
    for idx, c in enumerate(CORPUS_CHUNKS):
        c_vec = fastembed_embeddings[idx]
        dense_sim = max(0.0, cosine_similarity(q_vec, c_vec))
        text = c["full_text"].lower()
        lexical_ratio = sum(1 for t in tokens if t in text) / max(len(tokens), 1)

        combined = 0.60 * dense_sim + 0.40 * lexical_ratio
        if combined >= relevance_floor:
            scored.append((c, combined))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def evaluate_retrieval_system(system_name: str, retrieval_fn) -> Dict[str, Any]:
    queries_evaluated = 0
    recalls_1 = []
    recalls_3 = []
    recalls_5 = []
    precisions_1 = []
    precisions_3 = []
    precisions_5 = []
    mrr_list = []
    ndcg_list = []
    irrelevant_rejected = 0
    irrelevant_total = 0

    for item in RETRIEVAL_TEST_QUERIES:
        q = item["query"]
        targets = item["target_source_ids"]
        is_irrelevant = (len(targets) == 0)

        results = retrieval_fn(q, top_k=5)
        retrieved_source_ids = [r[0]["source_id"] for r in results]

        if is_irrelevant:
            irrelevant_total += 1
            # If no results returned or all results below 0.55 floor
            if not results or (results and results[0][1] < 0.55):
                irrelevant_rejected += 1
            continue

        queries_evaluated += 1

        # Recall & Precision at K
        for k, r_list, p_list in [
            (1, recalls_1, precisions_1),
            (3, recalls_3, precisions_3),
            (5, recalls_5, precisions_5),
        ]:
            top_k_sources = retrieved_source_ids[:k]
            matched = sum(1 for s in targets if s in top_k_sources)
            recall = matched / len(targets)
            precision = matched / max(k, 1)
            r_list.append(recall)
            p_list.append(precision)

        # MRR
        first_rank = 0
        for rank, s_id in enumerate(retrieved_source_ids, start=1):
            if s_id in targets:
                first_rank = rank
                break
        mrr_list.append(1.0 / first_rank if first_rank > 0 else 0.0)

        # nDCG@5
        ndcg_list.append(ndcg_at_k(retrieved_source_ids, targets, k=5))

    return {
        "system": system_name,
        "queries_count": queries_evaluated,
        "recall_at_1": round(float(np.mean(recalls_1)) * 100, 2),
        "recall_at_3": round(float(np.mean(recalls_3)) * 100, 2),
        "recall_at_5": round(float(np.mean(recalls_5)) * 100, 2),
        "precision_at_1": round(float(np.mean(precisions_1)) * 100, 2),
        "precision_at_3": round(float(np.mean(precisions_3)) * 100, 2),
        "precision_at_5": round(float(np.mean(precisions_5)) * 100, 2),
        "mrr": round(float(np.mean(mrr_list)), 4),
        "ndcg_at_5": round(float(np.mean(ndcg_list)), 4),
        "irrelevant_abstention_pct": round((irrelevant_rejected / irrelevant_total) * 100, 2) if irrelevant_total else 100.0
    }


def run_all_retrieval_benchmarks():
    print("\n" + "="*80)
    print("CONVELINA — RAG RETRIEVAL ARCHITECTURE BENCHMARK")
    print("Corpus Chunks:", len(CORPUS_CHUNKS))
    print("="*80)

    systems = [
        ("Deterministic Hash (Current Baseline)", retrieve_deterministic_hash),
        ("Lexical Retrieval (Token Overlap)", retrieve_lexical),
        ("Semantic Neural (FastEmbed BGE-small)", retrieve_semantic_neural),
        ("Hybrid (Neural Dense + Lexical + Floor)", retrieve_hybrid),
    ]

    results = []
    for name, fn in systems:
        res = evaluate_retrieval_system(name, fn)
        results.append(res)
        print(f"\n--- {name} ---")
        print(f"  Recall@1: {res['recall_at_1']}% | Recall@3: {res['recall_at_3']}% | Recall@5: {res['recall_at_5']}%")
        print(f"  Precision@1: {res['precision_at_1']}% | Precision@3: {res['precision_at_3']}% | Precision@5: {res['precision_at_5']}%")
        print(f"  MRR: {res['mrr']} | nDCG@5: {res['ndcg_at_5']}")
        print(f"  Irrelevant Query Abstention: {res['irrelevant_abstention_pct']}%")

    with open("/tmp/rag_benchmark_p3f2.json", "w") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    run_all_retrieval_benchmarks()
