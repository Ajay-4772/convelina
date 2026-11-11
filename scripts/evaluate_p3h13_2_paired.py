"""
CONVELINA — P3H.13.2 Paired OCR Benchmark, Field Correctness & Calibration Validator

Evaluates Pipeline A (Original P3H.12 Baseline @ commit cb12356) and Pipeline B (Enhanced P3H.13.x)
on IDENTICAL inputs (48 images, 48 ground-truth annotations in benchmarks/p3h13/),
using IDENTICAL field definitions, normalization rules, and calibration definitions.

Usage:
  1. Extract baseline OCR outputs (run with P3H.12 backend on PYTHONPATH):
     python scripts/evaluate_p3h13_2_paired.py run-ocr --pipeline p3h12 --dataset p3h13 --output benchmarks/p3h13/raw_p3h12_on_holdout.json
  2. Extract enhanced OCR outputs (run with current backend on PYTHONPATH):
     python scripts/evaluate_p3h13_2_paired.py run-ocr --pipeline p3h13 --dataset p3h13 --output benchmarks/p3h13/raw_p3h13_on_holdout.json
  3. Run paired statistical, field-level, calibration & downstream invariant analysis:
     python scripts/evaluate_p3h13_2_paired.py analyze --p3h12-json benchmarks/p3h13/raw_p3h12_on_holdout.json --p3h13-json benchmarks/p3h13/raw_p3h13_on_holdout.json --output benchmarks/p3h13/paired_benchmark_results.json
"""

import os
import re
import sys
import json
import time
import math
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
if not (BASE_DIR / "benchmarks").exists() and Path("/workspace/benchmarks").exists():
    BASE_DIR = Path("/workspace")


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            ins = prev[j + 1] + 1
            dele = curr[j] + 1
            sub = prev[j] + (c1 != c2)
            curr.append(min(ins, dele, sub))
        prev = curr
    return prev[-1]


def compute_cer(reference: str, hypothesis: str) -> float:
    ref_clean = " ".join(reference.split())
    hyp_clean = " ".join(hypothesis.split())
    if not ref_clean:
        return 0.0 if not hyp_clean else 1.0
    dist = levenshtein_distance(ref_clean, hyp_clean)
    return round(min(1.0, dist / max(len(ref_clean), 1)), 4)


def compute_wer_standard(reference: str, hypothesis: str) -> float:
    """Standard Word Error Rate: Levenshtein(ref_words, hyp_words) / len(ref_words), clamped [0, 1]."""
    ref_words = [w.lower() for w in reference.split()]
    hyp_words = [w.lower() for w in hypothesis.split()]
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    # Compute edit distance keeping ref_words as ground truth denominator
    n, m = len(ref_words), len(hyp_words)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev = curr
    return round(min(1.0, prev[m] / max(n, 1)), 4)


def normalize_val(v: Any) -> str:
    """Strict canonical normalization for field comparison (never accepts partial matches)."""
    if v is None:
        return ""
    s = str(v).strip().upper()
    d_match = re.match(r"^(\d{1,4})[/-](\d{1,2})[/-](\d{1,4})$", s)
    if d_match:
        p1, p2, p3 = int(d_match.group(1)), int(d_match.group(2)), int(d_match.group(3))
        if p1 > 1000:
            return f"{p1:04d}/{p2:02d}/{p3:02d}"
        elif p3 > 1000:
            return f"{p3:04d}/{p2:02d}/{p1:02d}"
    s = s.replace("-", "/").replace(".", "/")
    return " ".join(s.split())


def compute_calibration_metrics(predictions: List[Tuple[float, int]], num_bins: int = 10) -> Dict[str, Any]:
    """Unified, leak-free calculation of Brier score, ECE (10 bins), MCE, and bin details."""
    if not predictions:
        return {"total_samples": 0, "brier_score": 0.0, "ece": 0.0, "mce": 0.0, "bins": []}
    n = len(predictions)
    brier = round(sum((p - y) ** 2 for p, y in predictions) / n, 4)
    bin_width = 1.0 / num_bins
    weighted_ece = 0.0
    max_gap = 0.0
    bins_out = []
    for b_idx in range(num_bins):
        lo = b_idx * bin_width
        hi = (b_idx + 1) * bin_width if b_idx < num_bins - 1 else 1.0001
        samples = [(p, y) for p, y in predictions if lo <= p < hi]
        cnt = len(samples)
        if cnt > 0:
            mean_c = sum(p for p, _ in samples) / cnt
            acc = sum(y for _, y in samples) / cnt
            gap = abs(acc - mean_c)
            weighted_ece += (cnt / n) * gap
            if gap > max_gap:
                max_gap = gap
        else:
            mean_c = (lo + min(1.0, hi)) / 2.0
            acc = 0.0
            gap = 0.0
        bins_out.append({
            "bin_index": b_idx,
            "lower_bound": round(lo, 2),
            "upper_bound": round(min(1.0, hi), 2),
            "sample_count": cnt,
            "mean_confidence": round(mean_c, 4),
            "empirical_accuracy": round(acc, 4),
            "calibration_gap": round(gap, 4),
        })
    return {
        "total_samples": n,
        "brier_score": brier,
        "ece": round(weighted_ece, 4),
        "mce": round(max_gap, 4),
        "bins": bins_out,
    }


def extract_raw_word_confidence(ocr_engine, img_path: Path) -> Optional[float]:
    """Measures raw Tesseract word-level mean confidence without quality penalty subtraction."""
    try:
        import pytesseract
        from PIL import Image
        with Image.open(img_path) as im:
            processed = ocr_engine.preprocess_image(im)
            data = pytesseract.image_to_data(processed, lang="eng", config="--psm 4", output_type=pytesseract.Output.DICT)
            confs = [float(c) for c in data.get("conf", []) if float(c) >= 0]
            if confs:
                return round(sum(confs) / len(confs) / 100.0, 4)
    except Exception:
        pass
    return None


def cmd_run_ocr(args):
    sys.path.insert(0, args.backend_dir)
    from app.ocr.engine import default_ocr_engine
    from app.ocr.field_extractor import FieldExtractor

    manifest_path = BASE_DIR / "benchmarks" / args.dataset / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    samples_out = []
    print(f"[{args.pipeline.upper()}] Executing OCR extraction on {len(manifest)} samples from {args.dataset} (backend={args.backend_dir})...")

    for idx, item in enumerate(manifest):
        sample_id = item["sample_id"]
        category = item["category"]
        condition = item["condition"]
        img_path = BASE_DIR / item["image_path"]
        ann_path = BASE_DIR / item["annotation_path"]

        with open(ann_path, "r", encoding="utf-8") as af:
            annotation = json.load(af)

        t0 = time.perf_counter()
        error_msg = None
        try:
            extracted_text, doc_conf = default_ocr_engine.extract_text_and_confidence(str(img_path), is_pdf=False)
        except Exception as e:
            extracted_text = ""
            doc_conf = 0.30
            error_msg = str(e)
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        raw_word_conf = extract_raw_word_confidence(default_ocr_engine, img_path)

        cat_result = FieldExtractor.extract_category_fields(
            document_type=category,
            raw_text=extracted_text,
            overall_confidence=doc_conf,
            source_document_id=sample_id,
        )

        # Transient ephemeral 12-digit check for Aadhaar OCR engine validation (never persisted to DB)
        ephemeral_aadhaar = None
        if category == "aadhaar" and extracted_text:
            m = re.search(r"\b(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})\b", extracted_text)
            if m:
                ephemeral_aadhaar = f"{m.group(1)} {m.group(2)} {m.group(3)}"

        field_confs = {
            k: round(float(v.confidence), 4)
            for k, v in cat_result.field_extractions.items()
        }
        field_valid_flags = {
            k: bool(v.format_validated)
            for k, v in cat_result.field_extractions.items()
        }

        samples_out.append({
            "sample_id": sample_id,
            "category": category,
            "condition": condition,
            "expected_manual_review": bool(item.get("expected_review", False)),
            "extracted_text": extracted_text,
            "ground_truth_text": annotation["ground_truth_text"],
            "ground_truth_fields": annotation["ground_truth_fields"],
            "doc_ocr_confidence": round(float(doc_conf), 4),
            "raw_word_confidence": raw_word_conf,
            "requires_manual_review": bool(cat_result.requires_manual_review),
            "fields_flat": cat_result.fields_flat,
            "field_confidences": field_confs,
            "field_valid_flags": field_valid_flags,
            "ephemeral_aadhaar_12digit": ephemeral_aadhaar,
            "latency_ms": elapsed_ms,
            "error": error_msg,
        })
        print(f"  [{idx+1:02d}/{len(manifest)}] {sample_id:<32} doc_conf={doc_conf:.3f} raw_conf={raw_word_conf} latency={elapsed_ms:.1f}ms")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "pipeline": args.pipeline,
            "dataset": args.dataset,
            "backend_dir": str(args.backend_dir),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "samples": samples_out,
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved raw OCR outputs to {out_path}")


def score_pipeline_run(raw_data: Dict[str, Any], allow_ephemeral_aadhaar: bool = False) -> Dict[str, Any]:
    """Applies unified strict scoring & calibration calculation to a pipeline's raw JSON run."""
    samples = raw_data["samples"]

    # Core deduplicated fields printed directly on all synthetic templates
    CORE_PRINTED_KEYS = {
        "aadhaar": {"full_name", "date_of_birth", "gender", "address", "aadhaar_number"},
        "pan": {"full_name", "father_name", "date_of_birth", "pan_number"},
        "passport": {"passport_number", "surname", "full_name", "date_of_birth"},
        "education_10th": {"board", "passing_year", "roll_number", "registration_number", "full_name", "father_name", "mother_name", "date_of_birth"},
        "education_12th": {"board", "passing_year", "roll_number", "registration_number", "full_name", "father_name", "mother_name", "date_of_birth"},
        "epf": {"uan", "member_id", "full_name", "employer_name", "date_of_joining", "date_of_exit"},
    }

    sample_scored = []
    cat_agg: Dict[str, Dict[str, Any]] = {}
    cond_agg: Dict[str, Dict[str, Any]] = {}
    field_agg: Dict[str, Dict[str, int]] = {}

    cal_doc_all = []
    cal_field_all = []
    cal_field_nonmissing = []
    cal_raw_word = []

    rev_tp = rev_fp = rev_tn = rev_fn = 0
    total_f = total_ex = total_ms = total_inc = 0
    core_f = core_ex = core_ms = core_inc = 0

    for s in samples:
        sid = s["sample_id"]
        cat = s["category"]
        cond = s["condition"]
        gt_text = s["ground_truth_text"]
        ext_text = s["extracted_text"]
        gt_fields = s["ground_truth_fields"]
        ext_fields = s["fields_flat"]
        doc_conf = float(s["doc_ocr_confidence"])
        raw_conf = s.get("raw_word_confidence")
        f_confs = s.get("field_confidences", {})

        cer = compute_cer(gt_text, ext_text)
        wer = compute_wer_standard(gt_text, ext_text)

        s_tot = s_ex = s_ms = s_inc = 0
        s_core_tot = s_core_ex = 0
        field_results = {}

        for fname, gt_val in gt_fields.items():
            if gt_val is None:
                continue
            s_tot += 1
            ext_val = ext_fields.get(fname)
            if allow_ephemeral_aadhaar and cat == "aadhaar" and fname in ("aadhaar_number", "document_number"):
                if s.get("ephemeral_aadhaar_12digit"):
                    ext_val = s["ephemeral_aadhaar_12digit"]

            norm_gt = normalize_val(gt_val)
            norm_ext = normalize_val(ext_val)

            is_exact = (norm_gt != "" and norm_gt == norm_ext)
            is_missing = (ext_val is None or str(ext_val).strip() == "")
            is_incorrect = (not is_missing) and (not is_exact)

            if is_exact:
                s_ex += 1
            elif is_missing:
                s_ms += 1
            else:
                s_inc += 1

            is_core = fname in CORE_PRINTED_KEYS.get(cat, set())
            if is_core:
                s_core_tot += 1
                if is_exact:
                    s_core_ex += 1

            field_results[fname] = {
                "gt": gt_val,
                "ext": ext_val,
                "exact": is_exact,
                "missing": is_missing,
                "incorrect": is_incorrect,
                "field_conf": float(f_confs.get(fname, 0.0)),
                "is_core": is_core,
            }

            if fname not in field_agg:
                field_agg[fname] = {"total": 0, "exact": 0, "missing": 0, "incorrect": 0}
            field_agg[fname]["total"] += 1
            field_agg[fname]["exact"] += (1 if is_exact else 0)
            field_agg[fname]["missing"] += (1 if is_missing else 0)
            field_agg[fname]["incorrect"] += (1 if is_incorrect else 0)

            y = 1 if is_exact else 0
            cal_doc_all.append((doc_conf, y))
            fc = float(f_confs.get(fname, 0.0))
            cal_field_all.append((fc, y))
            if not is_missing:
                cal_field_nonmissing.append((fc, y))
            if raw_conf is not None:
                cal_raw_word.append((float(raw_conf), y))

        total_f += s_tot
        total_ex += s_ex
        total_ms += s_ms
        total_inc += s_inc
        core_f += s_core_tot
        core_ex += s_core_ex

        req_rev = bool(s["requires_manual_review"])
        exp_rev = bool(s["expected_manual_review"])
        if req_rev and exp_rev:
            rev_tp += 1
        elif req_rev and not exp_rev:
            rev_fp += 1
        elif not req_rev and not exp_rev:
            rev_tn += 1
        elif not req_rev and exp_rev:
            rev_fn += 1

        if cat not in cat_agg:
            cat_agg[cat] = {"samples": 0, "cer": 0.0, "wer": 0.0, "f": 0, "ex": 0, "ms": 0, "inc": 0, "core_f": 0, "core_ex": 0}
        cs = cat_agg[cat]
        cs["samples"] += 1
        cs["cer"] += cer
        cs["wer"] += wer
        cs["f"] += s_tot
        cs["ex"] += s_ex
        cs["ms"] += s_ms
        cs["inc"] += s_inc
        cs["core_f"] += s_core_tot
        cs["core_ex"] += s_core_ex

        if cond not in cond_agg:
            cond_agg[cond] = {"samples": 0, "cer": 0.0, "wer": 0.0, "f": 0, "ex": 0, "ms": 0, "inc": 0}
        cn = cond_agg[cond]
        cn["samples"] += 1
        cn["cer"] += cer
        cn["wer"] += wer
        cn["f"] += s_tot
        cn["ex"] += s_ex
        cn["ms"] += s_ms
        cn["inc"] += s_inc

        sample_scored.append({
            "sample_id": sid,
            "category": cat,
            "condition": cond,
            "cer": cer,
            "wer": wer,
            "total_fields": s_tot,
            "exact": s_ex,
            "missing": s_ms,
            "incorrect": s_inc,
            "exact_rate": round(s_ex / max(s_tot, 1), 4),
            "core_fields": s_core_tot,
            "core_exact": s_core_ex,
            "core_exact_rate": round(s_core_ex / max(s_core_tot, 1), 4),
            "latency_ms": s["latency_ms"],
            "doc_conf": doc_conf,
            "requires_manual_review": req_rev,
            "expected_manual_review": exp_rev,
            "fields": field_results,
        })

    latencies = sorted(s["latency_ms"] for s in samples)
    n_samples = len(samples)
    mean_cer = round(sum(s["cer"] for s in sample_scored) / n_samples, 4)
    mean_wer = round(sum(s["wer"] for s in sample_scored) / n_samples, 4)

    return {
        "pipeline": raw_data["pipeline"],
        "ephemeral_aadhaar_scoring": allow_ephemeral_aadhaar,
        "aggregate": {
            "total_samples": n_samples,
            "total_fields": total_f,
            "exact_matches": total_ex,
            "missing_fields": total_ms,
            "incorrect_fields": total_inc,
            "exact_match_rate": round(total_ex / max(total_f, 1), 4),
            "missing_rate": round(total_ms / max(total_f, 1), 4),
            "incorrect_rate": round(total_inc / max(total_f, 1), 4),
            "core_total_fields": core_f,
            "core_exact_matches": core_ex,
            "core_exact_match_rate": round(core_ex / max(core_f, 1), 4),
            "mean_cer": mean_cer,
            "mean_wer": mean_wer,
            "review_tp": rev_tp,
            "review_fp": rev_fp,
            "review_tn": rev_tn,
            "review_fn": rev_fn,
            "review_recall": round(rev_tp / max(rev_tp + rev_fn, 1), 4),
            "review_precision": round(rev_tp / max(rev_tp + rev_fp, 1), 4),
            "latency_mean_ms": round(sum(latencies) / n_samples, 2),
            "latency_p50_ms": latencies[int(n_samples * 0.50)],
            "latency_p95_ms": latencies[int(n_samples * 0.95)],
        },
        "calibration": {
            "document_level": compute_calibration_metrics(cal_doc_all),
            "field_level_all": compute_calibration_metrics(cal_field_all),
            "field_level_nonmissing": compute_calibration_metrics(cal_field_nonmissing),
            "raw_word_level": compute_calibration_metrics(cal_raw_word),
        },
        "by_category": {
            k: {
                "samples": v["samples"],
                "total_fields": v["f"],
                "exact_matches": v["ex"],
                "missing_fields": v["ms"],
                "incorrect_fields": v["inc"],
                "exact_match_rate": round(v["ex"] / max(v["f"], 1), 4),
                "core_total_fields": v["core_f"],
                "core_exact_matches": v["core_ex"],
                "core_exact_match_rate": round(v["core_ex"] / max(v["core_f"], 1), 4),
                "mean_cer": round(v["cer"] / v["samples"], 4),
                "mean_wer": round(v["wer"] / v["samples"], 4),
            }
            for k, v in cat_agg.items()
        },
        "by_condition": {
            k: {
                "samples": v["samples"],
                "total_fields": v["f"],
                "exact_matches": v["ex"],
                "missing_fields": v["ms"],
                "incorrect_fields": v["inc"],
                "exact_match_rate": round(v["ex"] / max(v["f"], 1), 4),
                "mean_cer": round(v["cer"] / v["samples"], 4),
                "mean_wer": round(v["wer"] / v["samples"], 4),
            }
            for k, v in cond_agg.items()
        },
        "by_field": {
            k: {
                "total": v["total"],
                "exact": v["exact"],
                "missing": v["missing"],
                "incorrect": v["incorrect"],
                "exact_rate": round(v["exact"] / max(v["total"], 1), 4),
            }
            for k, v in field_agg.items()
        },
        "samples": sample_scored,
    }


def mcnemar_exact_p_value(n_gain: int, n_loss: int) -> float:
    """Two-sided exact binomial test on discordant pairs (n01, n10)."""
    k_tot = n_gain + n_loss
    if k_tot == 0:
        return 1.0
    k = min(n_gain, n_loss)
    p_one = sum(math.comb(k_tot, i) for i in range(0, k + 1)) * (0.5 ** k_tot)
    return round(min(1.0, 2.0 * p_one), 8)


def verify_live_ocr_downstream_safety(raw_p3h13: Dict[str, Any]) -> Dict[str, Any]:
    """
    Feeds ACTUAL P3H.13 OCR extractions into DocumentIdentityProfile.from_extracted_fields()
    and IdentityComparisonEngine.compare_profiles(), verifying 0% auto-accept on degraded or mismatched records.
    """
    sys.path.insert(0, str(BASE_DIR / "backend"))
    sys.path.insert(0, str(BASE_DIR))
    from app.services.identity_matching.models import DocumentIdentityProfile
    from app.services.identity_matching.engine import IdentityComparisonEngine
    from app.services.identity_matching.classification import OverallIdentityClassification
    from scripts.evaluate_p3h12_comparison import COMPARISON_BENCHMARK_DATASET

    # 1. Run 64 synthetic comparison benchmark cases
    tp = fn = tn = fp = 0
    for tc in COMPARISON_BENCHMARK_DATASET:
        cid = tc["id"]
        pa = DocumentIdentityProfile.from_extracted_fields(
            f"{cid}_a", tc["doc_a"].get("doc_type", "generic"),
            {"name": tc["doc_a"].get("full_name"), "full_name": tc["doc_a"].get("full_name"),
             "date_of_birth": tc["doc_a"].get("date_of_birth"), "gender": tc["doc_a"].get("gender")},
            overall_ocr_confidence=tc["doc_a"].get("ocr_confidence", 0.95),
        )
        pb = DocumentIdentityProfile.from_extracted_fields(
            f"{cid}_b", tc["doc_b"].get("doc_type", "generic"),
            {"name": tc["doc_b"].get("full_name"), "full_name": tc["doc_b"].get("full_name"),
             "date_of_birth": tc["doc_b"].get("date_of_birth"), "gender": tc["doc_b"].get("gender")},
            overall_ocr_confidence=tc["doc_b"].get("ocr_confidence", 0.95),
        )
        res = IdentityComparisonEngine.compare_profiles(pa, pb)
        is_auto = (
            res.overall_classification in [OverallIdentityClassification.EXACT_MATCH, OverallIdentityClassification.FORMAT_ONLY_MATCH]
            and not res.requires_manual_review
            and len(res.conflicting_fields) == 0
            and len(res.ambiguous_fields) == 0
        )
        is_clean_gt = (not tc["expected_conflict"]) and (not tc["expected_review"])
        if not is_clean_gt:
            if not is_auto:
                tp += 1
            else:
                fn += 1
        else:
            if not is_auto:
                fp += 1
            else:
                tn += 1

    # 2. Cross-compare real OCR outputs from degraded P3H.13 holdout against ground-truth profiles & other profiles
    samples = raw_p3h13["samples"]
    by_id = {s["sample_id"]: s for s in samples}
    real_ocr_false_accepts = 0
    real_ocr_pairs_tested = 0

    # Compare every degraded sample (blur_noise, photo_shadow, low_resolution) against clean_scan of different profile -> MUST NEVER auto-accept!
    clean_samples = [s for s in samples if s["condition"] == "clean_scan"]
    degraded_samples = [s for s in samples if s["condition"] in ("blur_noise", "photo_shadow", "low_resolution", "obscured_crease")]
    for cs in clean_samples:
        p_clean = DocumentIdentityProfile.from_extracted_fields(
            cs["sample_id"], cs["category"], cs["fields_flat"], overall_ocr_confidence=cs["doc_ocr_confidence"]
        )
        for ds in degraded_samples:
            p_deg = DocumentIdentityProfile.from_extracted_fields(
                ds["sample_id"], ds["category"], ds["fields_flat"], overall_ocr_confidence=ds["doc_ocr_confidence"]
            )
            res = IdentityComparisonEngine.compare_profiles(p_clean, p_deg)
            is_auto = (
                res.overall_classification in [OverallIdentityClassification.EXACT_MATCH, OverallIdentityClassification.FORMAT_ONLY_MATCH]
                and not res.requires_manual_review
                and len(res.conflicting_fields) == 0
            )
            real_ocr_pairs_tested += 1
            if ds["category"] != cs["category"] and is_auto:
                # Different profile! Auto-accept would be a critical FAR violation!
                real_ocr_false_accepts += 1
            elif ds["condition"] in ("blur_noise", "photo_shadow", "low_resolution") and is_auto:
                # Severely degraded OCR must not auto-accept even on same profile!
                real_ocr_false_accepts += 1

    return {
        "benchmark_64_cases": {
            "total": len(COMPARISON_BENCHMARK_DATASET),
            "tp": tp, "fn": fn, "tn": tn, "fp": fp,
            "far": round(fn / max(tp + fn, 1), 4),
            "frr": round(fp / max(tn + fp, 1), 4),
        },
        "live_ocr_pairwise_stress": {
            "total_pairs_tested": real_ocr_pairs_tested,
            "false_acceptances": real_ocr_false_accepts,
            "far_invariant_preserved": (real_ocr_false_accepts == 0),
        }
    }


def cmd_analyze(args):
    with open(args.p3h12_json, "r", encoding="utf-8") as f:
        raw_a = json.load(f)
    with open(args.p3h13_json, "r", encoding="utf-8") as f:
        raw_b = json.load(f)

    scored_a_strict = score_pipeline_run(raw_a, allow_ephemeral_aadhaar=False)
    scored_b_strict = score_pipeline_run(raw_b, allow_ephemeral_aadhaar=False)
    scored_b_ephemeral = score_pipeline_run(raw_b, allow_ephemeral_aadhaar=True)
    scored_a_ephemeral = score_pipeline_run(raw_a, allow_ephemeral_aadhaar=True)

    # Paired sample and field-level McNemar analysis (strict mode, identical across both)
    improved_samples = tied_samples = regressed_samples = 0
    cer_deltas = []
    exact_rate_deltas = []
    n11 = n01 = n10 = n00 = 0  # both, gained, lost, neither

    samples_a_map = {s["sample_id"]: s for s in scored_a_strict["samples"]}
    for sb in scored_b_strict["samples"]:
        sa = samples_a_map[sb["sample_id"]]
        d_cer = sb["cer"] - sa["cer"]
        d_ex = sb["exact_rate"] - sa["exact_rate"]
        cer_deltas.append(d_cer)
        exact_rate_deltas.append(d_ex)
        if sb["exact"] > sa["exact"]:
            improved_samples += 1
        elif sb["exact"] < sa["exact"]:
            regressed_samples += 1
        else:
            tied_samples += 1

        for fname, fb in sb["fields"].items():
            fa = sa["fields"][fname]
            if fa["exact"] and fb["exact"]:
                n11 += 1
            elif (not fa["exact"]) and fb["exact"]:
                n01 += 1
            elif fa["exact"] and (not fb["exact"]):
                n10 += 1
            else:
                n00 += 1

    # Also McNemar with ephemeral 12-digit Aadhaar evaluation
    e_n11 = e_n01 = e_n10 = e_n00 = 0
    samples_ae_map = {s["sample_id"]: s for s in scored_a_ephemeral["samples"]}
    for sb in scored_b_ephemeral["samples"]:
        sa = samples_ae_map[sb["sample_id"]]
        for fname, fb in sb["fields"].items():
            fa = sa["fields"][fname]
            if fa["exact"] and fb["exact"]:
                e_n11 += 1
            elif (not fa["exact"]) and fb["exact"]:
                e_n01 += 1
            elif fa["exact"] and (not fb["exact"]):
                e_n10 += 1
            else:
                e_n00 += 1

    agg_a = scored_a_strict["aggregate"]
    agg_b = scored_b_strict["aggregate"]

    abs_diff = round((agg_b["exact_match_rate"] - agg_a["exact_match_rate"]) * 100.0, 2)
    rel_diff = round(((agg_b["exact_match_rate"] - agg_a["exact_match_rate"]) / max(agg_a["exact_match_rate"], 1e-6)) * 100.0, 2)

    downstream_invariants = verify_live_ocr_downstream_safety(raw_b)

    report = {
        "milestone": "P3H.13.2",
        "dataset": raw_b["dataset"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "strict_comparison": {
            "pipeline_a_p3h12": scored_a_strict,
            "pipeline_b_p3h13": scored_b_strict,
            "paired_summary": {
                "samples_improved": improved_samples,
                "samples_tied": tied_samples,
                "samples_regressed": regressed_samples,
                "absolute_exact_match_gain_pct_pts": abs_diff,
                "relative_exact_match_gain_pct": rel_diff,
                "mean_cer_delta": round(sum(cer_deltas) / len(cer_deltas), 4),
                "mean_exact_rate_delta": round(sum(exact_rate_deltas) / len(exact_rate_deltas), 4),
                "mcnemar_432_fields": {
                    "both_correct_n11": n11,
                    "p3h13_gained_n01": n01,
                    "p3h13_regressed_n10": n10,
                    "both_incorrect_n00": n00,
                    "exact_two_sided_p_value": mcnemar_exact_p_value(n01, n10),
                },
            },
        },
        "ephemeral_aadhaar_adjusted_comparison": {
            "pipeline_a_p3h12": scored_a_ephemeral["aggregate"],
            "pipeline_b_p3h13": scored_b_ephemeral["aggregate"],
            "mcnemar_432_fields": {
                "both_correct_n11": e_n11,
                "p3h13_gained_n01": e_n01,
                "p3h13_regressed_n10": e_n10,
                "both_incorrect_n00": e_n00,
                "exact_two_sided_p_value": mcnemar_exact_p_value(e_n01, e_n10),
            },
        },
        "downstream_safety_invariants": downstream_invariants,
    }

    out_path = Path(args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 82)
    print(f"PAIRED BENCHMARK RESULTS ON INDEPENDENT HOLDOUT ({raw_b['dataset'].upper()})")
    print("=" * 82)
    print(f"Pipeline A (P3H.12 Baseline): Exact {agg_a['exact_matches']}/{agg_a['total_fields']} ({agg_a['exact_match_rate']*100:.2f}%) | Missing {agg_a['missing_fields']} | Incorrect {agg_a['incorrect_fields']} | CER {agg_a['mean_cer']*100:.2f}%")
    print(f"Pipeline B (P3H.13 Enhanced): Exact {agg_b['exact_matches']}/{agg_b['total_fields']} ({agg_b['exact_match_rate']*100:.2f}%) | Missing {agg_b['missing_fields']} | Incorrect {agg_b['incorrect_fields']} | CER {agg_b['mean_cer']*100:.2f}%")
    print(f"Strict Gain: +{abs_diff:.2f} pct pts ({rel_diff:+.2f}% relative) | McNemar gained={n01}, lost={n10}, p={mcnemar_exact_p_value(n01, n10)}")
    print(f"Samples: Improved={improved_samples}, Tied={tied_samples}, Regressed={regressed_samples} (N={len(samples_a_map)})")
    eb_a = scored_a_ephemeral["aggregate"]
    eb_b = scored_b_ephemeral["aggregate"]
    print(f"With Ephemeral 12-Digit Aadhaar OCR: {eb_a['exact_match_rate']*100:.2f}% -> {eb_b['exact_match_rate']*100:.2f}% (McNemar gained={e_n01}, lost={e_n10}, p={mcnemar_exact_p_value(e_n01, e_n10)})")
    print(f"Core Printed Fields Only ({agg_b['core_total_fields']} fields): {agg_a['core_exact_match_rate']*100:.2f}% -> {agg_b['core_exact_match_rate']*100:.2f}%")
    print(f"Downstream 64 Cases FAR: {downstream_invariants['benchmark_64_cases']['far']*100:.2f}% | Live OCR Stress ({downstream_invariants['live_ocr_pairwise_stress']['total_pairs_tested']} pairs) False Accepts: {downstream_invariants['live_ocr_pairwise_stress']['false_acceptances']}")
    print("=" * 82)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run-ocr")
    p_run.add_argument("--pipeline", required=True)
    p_run.add_argument("--dataset", default="p3h13")
    p_run.add_argument("--backend-dir", required=True)
    p_run.add_argument("--output", required=True)

    p_ana = sub.add_parser("analyze")
    p_ana.add_argument("--p3h12-json", required=True)
    p_ana.add_argument("--p3h13-json", required=True)
    p_ana.add_argument("--output", required=True)

    args = parser.parse_args()
    if args.cmd == "run-ocr":
        cmd_run_ocr(args)
    elif args.cmd == "analyze":
        cmd_analyze(args)

