"""
CONVELINA — P3H.12 Benchmark Test Suite
Validates:
1. Synthetic benchmark integrity (48 images, 48 annotations, 6 categories, 8 visual conditions).
2. OCR benchmark evaluation output metrics and calibration.
3. Deterministic comparison benchmark safety invariants:
   - Critical invariant: FAR == 0.00% (Zero false acceptance on conflicting/ambiguous identities)
   - 100% rejection/review of gender-differentiated lookalikes
   - 100% manual review trigger on low-confidence OCR inputs
   - 100% manual review trigger on unsupported non-Latin scripts
"""

import json
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_DIR = REPO_ROOT / "benchmarks" / "p3h12"


def test_synthetic_benchmark_dataset_integrity():
    manifest_path = BENCHMARK_DIR / "manifest.json"
    assert manifest_path.exists(), "Manifest file must exist"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    samples = manifest if isinstance(manifest, list) else manifest.get("samples", [])
    assert len(samples) == 48, f"Expected 48 benchmark samples, found {len(samples)}"
    
    expected_categories = {"aadhaar", "pan", "passport", "education_10th", "education_12th", "epf"}
    expected_conditions = {
        "clean_scan", "photo_shadow", "skewed_rot", "low_resolution",
        "blur_noise", "compression", "obscured_crease", "bilingual_script"
    }
    
    cat_counts = {}
    cond_counts = {}
    
    for s in samples:
        cat = s["category"]
        cond = s["condition"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        cond_counts[cond] = cond_counts.get(cond, 0) + 1
        
        # Verify image existence
        img_path = REPO_ROOT / s["image_path"]
        assert img_path.exists(), f"Image not found: {img_path}"
        assert img_path.stat().st_size > 0, f"Image is empty: {img_path}"
        
        # Verify annotation existence and schema
        ann_path = REPO_ROOT / s["annotation_path"]
        assert ann_path.exists(), f"Annotation not found: {ann_path}"
        
        with open(ann_path, "r", encoding="utf-8") as af:
            ann = json.load(af)
        
        assert "sample_id" in ann, f"Missing sample_id in {ann_path}"
        assert "category" in ann, f"Missing category in {ann_path}"
        assert "condition" in ann, f"Missing condition in {ann_path}"
        assert "ground_truth_text" in ann, f"Missing ground_truth_text in {ann_path}"
        assert "ground_truth_fields" in ann, f"Missing ground_truth_fields in {ann_path}"
        
        fields = ann["ground_truth_fields"]
        assert "full_name" in fields, f"Missing full_name in {ann_path}"
        assert len(fields["full_name"]) > 0, f"Empty full_name in {ann_path}"
        if cat != "epf":
            assert "date_of_birth" in fields, f"Missing date_of_birth in {ann_path}"
        else:
            assert "uan" in fields or "member_id" in fields, f"Missing UAN/member_id in {ann_path}"
    
    for cat in expected_categories:
        assert cat_counts.get(cat) == 8, f"Category {cat} should have 8 samples, got {cat_counts.get(cat)}"
    for cond in expected_conditions:
        assert cond_counts.get(cond) == 6, f"Condition {cond} should have 6 samples, got {cond_counts.get(cond)}"


def test_ocr_evaluation_results_validity():
    results_path = BENCHMARK_DIR / "ocr_evaluation_results.json"
    assert results_path.exists(), "OCR evaluation results file must exist"
    
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    meta = data.get("benchmark_metadata", {})
    assert meta.get("total_samples") == 48, f"Expected 48 samples in metadata, got {meta.get('total_samples')}"
    
    agg = data.get("aggregate_metrics", {})
    cer = agg.get("mean_cer", 0.0)
    wer = agg.get("mean_wer", 0.0)
    exact_match = agg.get("overall_field_exact_match_rate", 0.0)
    missing_rate = agg.get("overall_missing_field_rate", 0.0)
    
    assert 0.0 < cer < 1.0, f"CER must be valid fraction, got {cer}"
    assert 0.0 < wer < 1.0, f"WER must be valid fraction, got {wer}"
    assert 0.0 < exact_match < 1.0, f"Exact match must be valid fraction, got {exact_match}"
    assert 0.0 < missing_rate < 1.0, f"Missing rate must be valid fraction, got {missing_rate}"
    
    # Verify confidence calibration: Calibrated confidence Brier score must be lower than raw
    brier_raw = agg.get("calibration_brier_score_raw_tesseract", 1.0)
    brier_cal = agg.get("calibration_brier_score_calibrated", 1.0)
    assert brier_cal < brier_raw, (
        f"Calibrated confidence ({brier_cal}) must exhibit better calibration (lower Brier score) than raw ({brier_raw})"
    )
    
    # Review trigger recall must be high (fail-safe trigger on degraded documents)
    recall = agg.get("manual_review_trigger_recall", 0.0)
    assert recall >= 0.70, f"Review trigger recall must be at least 70%, got {recall*100:.1f}%"


def test_comparison_benchmark_safety_invariants():
    results_path = BENCHMARK_DIR / "comparison_evaluation_results.json"
    assert results_path.exists(), "Comparison evaluation results file must exist"
    
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    agg = data.get("aggregate_metrics", {})
    far = agg.get("false_acceptance_rate", 1.0)
    frr = agg.get("false_rejection_rate", 1.0)
    precision = agg.get("precision", 0.0)
    recall = agg.get("recall", 0.0)
    f1 = agg.get("f1_score", 0.0)
    
    # CRITICAL ARCHITECTURAL SAFETY INVARIANT: FAR MUST BE 0.00%
    assert far == 0.00, f"CRITICAL SAFETY VIOLATION: False Acceptance Rate must be 0.00%, got {far*100:.2f}%"
    assert frr == 0.00, f"False Rejection Rate should be minimal, got {frr*100:.2f}%"
    assert precision >= 0.95, f"Conflict precision must be >= 0.95, got {precision}"
    assert recall >= 0.95, f"Conflict recall must be >= 0.95, got {recall}"
    assert f1 >= 0.95, f"Conflict F1 score must be >= 0.95, got {f1}"
    
    # Phenomenon-specific checks
    cases = data.get("cases", [])
    case_map = {c["id"]: c for c in cases}
    
    # 1. Gender-differentiated pairs must NEVER be auto-accepted
    gender_cases = [f"similar_gender_{i:02d}" for i in range(1, 9)]
    for gid in gender_cases:
        c = case_map.get(gid)
        assert c is not None, f"Missing case {gid}"
        assert not c["is_auto_accepted"], f"Gender-differentiated case {gid} was auto-accepted!"
        assert c["detected_conflict"], f"Gender-differentiated case {gid} must be detected as conflict"
    
    # 2. Low-confidence OCR inputs must trigger manual review
    low_conf_cases = ["low_conf_01", "low_conf_02", "low_conf_03"]
    for lcid in low_conf_cases:
        c = case_map.get(lcid)
        assert c is not None, f"Missing case {lcid}"
        assert not c["is_auto_accepted"], f"Low confidence case {lcid} was auto-accepted!"
        assert c["requires_manual_review"], f"Low confidence case {lcid} must require manual review"
    
    # 3. Unsupported non-Latin scripts must trigger manual review
    script_cases = ["script_01", "script_02"]
    for scid in script_cases:
        c = case_map.get(scid)
        assert c is not None, f"Missing case {scid}"
        assert not c["is_auto_accepted"], f"Unsupported script case {scid} was auto-accepted!"
        assert c["requires_manual_review"], f"Unsupported script case {scid} must require manual review"
    
    # 4. Conflicting dates must be detected as conflicts
    date_cases = [f"date_{i:02d}" for i in range(1, 5)]
    for dcid in date_cases:
        c = case_map.get(dcid)
        assert c is not None, f"Missing case {dcid}"
        assert not c["is_auto_accepted"], f"Conflicting date case {dcid} was auto-accepted!"
        assert "date_of_birth" in c["conflicting_fields"], f"Date conflict not registered in conflicting_fields for {dcid}"
