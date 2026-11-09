"""
CONVELINA — Phase P3F.3
Part C: Corrected RAG Retrieval Evaluation & Tuning Suite

Addresses the P3F.2 contradiction where Lexical retrieval outperformed Hybrid retrieval.
Uses a separated Validation Set (for hybrid parameter tuning) and an Independent Holdout Test Set.

Includes:
- Exact official terminology
- Citizen-language paraphrases
- Pure synonyms (zero token overlap)
- Different word orderings
- Short keyword queries
- Long complex citizen inquiries
- Tamil queries (regional language retrieval)
- Irrelevant inquiries (abstention test)
- Conflicting statutory circular queries

Evaluates:
1. Deterministic Hash Retrieval
2. Lexical Token Retrieval
3. Neural Semantic Retrieval (FastEmbed BGE-small ONNX)
4. Hybrid Retrieval (with calibrated score normalization and Reciprocal Rank Fusion / linear tuning)
"""

import io
import os
import sys
import re
import math
import time
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

sys.path.insert(0, "/app")

from app.rag.ingestion.sources import OFFICIAL_SOURCES_DATA
from app.rag.ingestion.chunker import DocumentChunker
from app.rag.embeddings import DeterministicHashEmbeddingService, FastEmbedEmbeddingService
from app.rag.retrieval.retriever import STATUTORY_SYNONYMS


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


# 1. Chunk verified sources from knowledge corpus
chunker = DocumentChunker()
CORPUS_CHUNKS: List[Dict[str, Any]] = []
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

# 2. Embeddings initialization
hash_service = DeterministicHashEmbeddingService(dimension=1024)
fastembed_service = FastEmbedEmbeddingService("BAAI/bge-small-en-v1.5", dimension=384)

corpus_texts = [c["full_text"] for c in CORPUS_CHUNKS]
hash_embeddings = hash_service.embed_documents(corpus_texts)
fastembed_embeddings = fastembed_service.embed_documents(corpus_texts)


# ==============================================================================
# VALIDATION SET (For tuning hybrid weights only)
# ==============================================================================
VALIDATION_QUERIES = [
    {
        "query": "Aadhaar limit on name change lifetime",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "type": "short"
    },
    {
        "query": "Request For New PAN Card Or And Changes Or Correction in PAN Data",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "type": "exact"
    },
    {
        "query": "Alteration of female appellation post matrimonial ceremony",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "type": "synonym"
    },
    {
        "query": "EPFO Joint Declaration SOP Version 2 member profile correction",
        "target_source_ids": ["src_epfo_joint_declaration_2024"],
        "type": "exact"
    },
    {
        "query": "How do I correct my father's surname in CBSE Class 10 certificate?",
        "target_source_ids": ["src_cbse_name_correction_byelaws_2024"],
        "type": "paraphrase"
    },
    {
        "query": "What are the rules for adopting pet animals in municipal corporation?",
        "target_source_ids": [],
        "type": "irrelevant"
    },
    {
        "query": "Gazette notification deed poll affidavit passport change",
        "target_source_ids": ["src_passport_reissue_mea_2024"],
        "type": "word_order"
    },
    {
        "query": "EPF date of joining correction with employer digital signature",
        "target_source_ids": ["src_epfo_joint_declaration_2024"],
        "type": "paraphrase"
    },
]


# ==============================================================================
# INDEPENDENT HOLDOUT TEST SET (Completely unseen during hybrid tuning)
# ==============================================================================
HOLDOUT_TEST_QUERIES = [
    # 1. Exact official terminology
    {
        "query": "UIDAI circular maximum two updates for demographic name correction regional office exception",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "exact_wording"
    },
    {
        "query": "Joint Declaration by Member and Employer for Data Updation in Member Profile under EPF Scheme 1952",
        "target_source_ids": ["src_epfo_joint_declaration_2024"],
        "category": "exact_wording"
    },

    # 2. Citizen-language paraphrases
    {
        "query": "My spelling is wrong on my provident fund account how do I get my company to fix it?",
        "target_source_ids": ["src_epfo_joint_declaration_2024"],
        "category": "paraphrase"
    },
    {
        "query": "I got married and changed my last name. Which form do I need for updating my income tax PAN card?",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "paraphrase"
    },

    # 3. Pure synonyms (Zero token overlap with core statutory keywords)
    {
        "query": "Nomenclature modification protocol following matrimonial alliance for female taxpayers",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "pure_synonym"
    },
    {
        "query": "Chronological natal record chronological variance ceiling for biometric national identity register",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "pure_synonym"
    },

    # 4. Scrambled word order
    {
        "query": "reissue Form 1 Annexure E passport name change gazette",
        "target_source_ids": ["src_passport_reissue_mea_2024"],
        "category": "word_order"
    },
    {
        "query": "Class X five years limitation school records CBSE name change bye-laws",
        "target_source_ids": ["src_cbse_name_correction_byelaws_2024"],
        "category": "word_order"
    },

    # 5. Short keyword queries
    {
        "query": "Aadhaar DOB change proof",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "short_query"
    },
    {
        "query": "PAN surrender penalty 272B",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "short_query"
    },

    # 6. Long complex natural language inquiries
    {
        "query": "My Class 10 certificate was issued by CBSE in 2011 with my name as Kavita Devi, but my Aadhaar says Kavita Sharma. Can I request CBSE to amend my certificate after more than 5 years have passed?",
        "target_source_ids": ["src_cbse_name_correction_byelaws_2024"],
        "category": "long_query"
    },
    {
        "query": "My employer entered my date of joining as 01/01/2020 instead of 01/06/2019 in the EPFO portal. Is this classified as a major correction or minor correction under Joint Declaration SOP Version 2?",
        "target_source_ids": ["src_epfo_joint_declaration_2024"],
        "category": "long_query"
    },

    # 7. Regional language queries (Tamil)
    {
        "query": "ஆதார் அட்டையில் பெயர் திருத்தம் செய்ய எத்தனை முறை அனுமதிக்கப்படுகிறது?",
        "target_source_ids": ["src_uidai_update_policy_2024"],
        "category": "tamil_query"
    },
    {
        "query": "பான் கார்டு பெயர் மாற்றத்திற்கு என்ன ஆவணங்கள் தேவை?",
        "target_source_ids": ["src_pan_correction_nsdl_2024"],
        "category": "tamil_query"
    },

    # 8. Irrelevant queries (Must trigger NO_VERIFIED_PROCEDURE_AVAILABLE abstention)
    {
        "query": "How do I bake chocolate chip cookies in an air fryer at 180 degrees?",
        "target_source_ids": [],
        "category": "irrelevant"
    },
    {
        "query": "Current price of crude oil and stock market predictions for tomorrow",
        "target_source_ids": [],
        "category": "irrelevant"
    },
]


# ==============================================================================
# RETRIEVAL ALGORITHMS
# ==============================================================================

def retrieve_hash(query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    q_vec = hash_service.embed_query(query)
    scores = []
    for idx, c in enumerate(CORPUS_CHUNKS):
        c_vec = hash_embeddings[idx]
        sim = cosine_similarity(q_vec, c_vec)
        scores.append((c, sim))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def retrieve_lexical(query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    q_tokens = set(re.findall(r'[\w\u0B80-\u0BFF]+', query.lower()))
    stop_words = {"how", "do", "i", "my", "the", "in", "a", "an", "is", "for", "to", "what", "which", "and", "or", "of", "can"}
    tokens = q_tokens - stop_words
    if not tokens:
        tokens = q_tokens

    expanded_tokens = set(tokens)
    for t in tokens:
        if t in STATUTORY_SYNONYMS:
            expanded_tokens.update(STATUTORY_SYNONYMS[t])

    scores = []
    for c in CORPUS_CHUNKS:
        text = c["full_text"].lower()
        matched = sum(1 for t in expanded_tokens if t in text)
        score = min(1.0, matched / max(len(tokens), 1))
        scores.append((c, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def retrieve_semantic(query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
    q_vec = fastembed_service.embed_query(query)
    scores = []
    for idx, c in enumerate(CORPUS_CHUNKS):
        c_vec = fastembed_embeddings[idx]
        sim = cosine_similarity(q_vec, c_vec)
        scores.append((c, sim))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


def retrieve_rrf(query: str, top_k: int = 5, k_rrf: int = 60, relevance_floor: float = 0.55) -> List[Tuple[Dict[str, Any], float]]:
    """
    Reciprocal Rank Fusion (RRF) between Dense Neural and Lexical rankings.
    Score = 1/(k + rank_dense) + 1/(k + rank_lexical)
    """
    # 1. Dense ranking
    dense_scores = retrieve_semantic(query, top_k=len(CORPUS_CHUNKS))
    dense_rank = {c["chunk_id"]: r + 1 for r, (c, _) in enumerate(dense_scores)}
    dense_sim = {c["chunk_id"]: s for c, s in dense_scores}

    # 2. Lexical ranking
    lex_scores = retrieve_lexical(query, top_k=len(CORPUS_CHUNKS))
    lex_rank = {c["chunk_id"]: r + 1 for r, (c, _) in enumerate(lex_scores)}
    lex_ratio = {c["chunk_id"]: s for c, s in lex_scores}

    rrf_scores = []
    for c in CORPUS_CHUNKS:
        cid = c["chunk_id"]
        r_d = dense_rank.get(cid, len(CORPUS_CHUNKS))
        r_l = lex_rank.get(cid, len(CORPUS_CHUNKS))
        
        # Enforce relevance floor: query must have at least minimal semantic or lexical grounding
        sim_d = dense_sim.get(cid, 0.0)
        sim_l = lex_ratio.get(cid, 0.0)
        if sim_d < 0.40 and sim_l < 0.15:
            continue

        score = (1.0 / (k_rrf + r_d)) + (1.0 / (k_rrf + r_l))
        rrf_scores.append((c, score))

    rrf_scores.sort(key=lambda x: x[1], reverse=True)
    return rrf_scores[:top_k]


def retrieve_linear_hybrid(
    query: str,
    alpha: float = 0.50,
    top_k: int = 5,
    relevance_floor: float = 0.55
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Normalized Linear Combination: alpha * Dense + (1 - alpha) * Lexical
    With relevance floor abstention.
    """
    dense_res = retrieve_semantic(query, top_k=len(CORPUS_CHUNKS))
    dense_map = {c["chunk_id"]: s for c, s in dense_res}

    lex_res = retrieve_lexical(query, top_k=len(CORPUS_CHUNKS))
    lex_map = {c["chunk_id"]: s for c, s in lex_res}

    combined = []
    for c in CORPUS_CHUNKS:
        cid = c["chunk_id"]
        d_score = max(0.0, dense_map.get(cid, 0.0))
        l_score = max(0.0, lex_map.get(cid, 0.0))

        # Linear combination
        c_score = alpha * d_score + (1.0 - alpha) * l_score
        if c_score >= relevance_floor:
            combined.append((c, c_score))

    combined.sort(key=lambda x: x[1], reverse=True)
    return combined[:top_k]


# ==============================================================================
# BENCHMARK EVALUATOR
# ==============================================================================

def evaluate_method(queries: List[Dict[str, Any]], retrieve_fn, name: str) -> Dict[str, Any]:
    r1_list, r3_list, r5_list = [], [], []
    p1_list, p3_list, p5_list = [], [], []
    mrr_list = []
    ndcg5_list = []
    irrelevant_correct = 0
    irrelevant_total = 0
    latencies = []

    for q_item in queries:
        q = q_item["query"]
        target_ids = set(q_item["target_source_ids"])
        is_irrelevant = len(target_ids) == 0

        t0 = time.perf_counter()
        results = retrieve_fn(q, top_k=5)
        dt = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt)

        retrieved_sources = [r[0]["source_id"] for r in results]

        if is_irrelevant:
            irrelevant_total += 1
            # Abstention: no results returned, or all scores below threshold
            if not results or all(r[1] < 0.55 for r in results):
                irrelevant_correct += 1
            continue

        # Recall@K
        hit_1 = any(s in target_ids for s in retrieved_sources[:1])
        hit_3 = any(s in target_ids for s in retrieved_sources[:3])
        hit_5 = any(s in target_ids for s in retrieved_sources[:5])

        r1_list.append(1.0 if hit_1 else 0.0)
        r3_list.append(1.0 if hit_3 else 0.0)
        r5_list.append(1.0 if hit_5 else 0.0)

        # Precision@K
        p1 = sum(1 for s in retrieved_sources[:1] if s in target_ids) / 1.0
        p3 = sum(1 for s in retrieved_sources[:3] if s in target_ids) / 3.0
        p5 = sum(1 for s in retrieved_sources[:5] if s in target_ids) / 5.0
        p1_list.append(p1)
        p3_list.append(p3)
        p5_list.append(p5)

        # MRR
        rr = 0.0
        for rank, s in enumerate(retrieved_sources, start=1):
            if s in target_ids:
                rr = 1.0 / rank
                break
        mrr_list.append(rr)

        # nDCG@5
        ndcg = ndcg_at_k(retrieved_sources, list(target_ids), k=5)
        ndcg5_list.append(ndcg)

    abstention_rate = (irrelevant_correct / irrelevant_total * 100.0) if irrelevant_total else 100.0

    return {
        "name": name,
        "recall_1": np.mean(r1_list) * 100.0 if r1_list else 0.0,
        "recall_3": np.mean(r3_list) * 100.0 if r3_list else 0.0,
        "recall_5": np.mean(r5_list) * 100.0 if r5_list else 0.0,
        "precision_1": np.mean(p1_list) * 100.0 if p1_list else 0.0,
        "precision_3": np.mean(p3_list) * 100.0 if p3_list else 0.0,
        "precision_5": np.mean(p5_list) * 100.0 if p5_list else 0.0,
        "mrr": float(np.mean(mrr_list)) if mrr_list else 0.0,
        "ndcg_5": float(np.mean(ndcg5_list)) if ndcg5_list else 0.0,
        "abstention_rate": abstention_rate,
        "avg_latency_ms": float(np.mean(latencies)),
    }


def run_benchmark():
    print("==================================================================")
    print("CONVELINA — Phase P3F.3: Corrected RAG Retrieval Benchmark")
    print("==================================================================")

    # 1. Tuning Hybrid Weights on Validation Set
    print("\n--- PHASE 1: HYBRID WEIGHT TUNING ON VALIDATION SET (8 QUERIES) ---")
    print(f"{'Method / Alpha':<22} | {'Recall@1':<10} | {'Recall@3':<10} | {'MRR':<8} | {'nDCG@5':<8}")
    print("-" * 65)

    best_alpha = 0.50
    best_mrr = -1.0
    for a in [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]:
        fn = lambda q, top_k=5, alpha=a: retrieve_linear_hybrid(q, alpha=alpha, top_k=top_k, relevance_floor=0.50)
        res = evaluate_method(VALIDATION_QUERIES, fn, f"Hybrid (alpha={a:.1f})")
        print(f"Hybrid alpha={a:.1f}{' (Lexical)' if a==0.0 else (' (Dense)' if a==1.0 else ''):<10} | {res['recall_1']:6.2f}%   | {res['recall_3']:6.2f}%   | {res['mrr']:6.4f} | {res['ndcg_5']:6.4f}")
        if res['mrr'] > best_mrr:
            best_mrr = res['mrr']
            best_alpha = a

    # Also test RRF on validation
    rrf_res = evaluate_method(VALIDATION_QUERIES, retrieve_rrf, "Hybrid RRF")
    print(f"Hybrid RRF (k=60)      | {rrf_res['recall_1']:6.2f}%   | {rrf_res['recall_3']:6.2f}%   | {rrf_res['mrr']:6.4f} | {rrf_res['ndcg_5']:6.4f}")

    print(f"\n[Validation Tuning Result]: Optimal Linear Alpha = {best_alpha:.1f} (Validation MRR = {best_mrr:.4f})")

    # 2. Independent Holdout Evaluation (16 Queries)
    print("\n--- PHASE 2: INDEPENDENT HOLDOUT RETRIEVAL EVALUATION (16 QUERIES) ---")
    holdout_methods = [
        ("Deterministic Hash (1024-dim)", retrieve_hash),
        ("Lexical Token Overlap", retrieve_lexical),
        ("Neural Semantic (FastEmbed BGE-small)", retrieve_semantic),
        (f"Hybrid Linear (Tuned alpha={best_alpha:.1f})", lambda q, top_k=5: retrieve_linear_hybrid(q, alpha=best_alpha, top_k=top_k, relevance_floor=0.50)),
        ("Hybrid RRF (Reciprocal Rank Fusion)", retrieve_rrf),
    ]

    holdout_results = []
    for name, fn in holdout_methods:
        r = evaluate_method(HOLDOUT_TEST_QUERIES, fn, name)
        holdout_results.append(r)

    print(f"{'Retrieval Method':<38} | {'R@1':<7} | {'R@3':<7} | {'R@5':<7} | {'P@1':<7} | {'MRR':<7} | {'nDCG@5':<7} | {'Abstain':<8} | {'Lat(ms)':<7}")
    print("-" * 115)
    for r in holdout_results:
        print(f"{r['name']:<38} | {r['recall_1']:5.1f}% | {r['recall_3']:5.1f}% | {r['recall_5']:5.1f}% | {r['precision_1']:5.1f}% | {r['mrr']:6.4f} | {r['ndcg_5']:6.4f} | {r['abstention_rate']:6.1f}%  | {r['avg_latency_ms']:6.2f}")

    # 3. Category Breakdown on Holdout Set
    print("\n--- PHASE 3: HOLDOUT RETRIEVAL BREAKDOWN BY QUERY CATEGORY ---")
    cat_queries: Dict[str, List[Dict[str, Any]]] = {}
    for q in HOLDOUT_TEST_QUERIES:
        c = q["category"]
        cat_queries.setdefault(c, []).append(q)

    for cat_name, q_list in cat_queries.items():
        print(f"\n[Category: {cat_name.upper()} ({len(q_list)} queries)]")
        for m_name, fn in [
            ("Lexical", retrieve_lexical),
            ("Neural Semantic", retrieve_semantic),
            ("Hybrid Tuned", lambda q, top_k=5: retrieve_linear_hybrid(q, alpha=best_alpha, top_k=top_k, relevance_floor=0.50)),
        ]:
            c_res = evaluate_method(q_list, fn, m_name)
            if cat_name == "irrelevant":
                print(f"  {m_name:<18}: Abstention Rate = {c_res['abstention_rate']:.1f}%")
            else:
                print(f"  {m_name:<18}: R@1={c_res['recall_1']:5.1f}% | R@3={c_res['recall_3']:5.1f}% | MRR={c_res['mrr']:.4f}")

    print("\n==================================================================")
    print("CORRECTED RAG RETRIEVAL BENCHMARK COMPLETE")
    print("==================================================================")


if __name__ == "__main__":
    run_benchmark()

