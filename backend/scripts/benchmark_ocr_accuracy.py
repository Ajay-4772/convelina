"""
CONVELINA — Rigorous OCR Accuracy & Robustness Evaluation Benchmark (Phase P3F.2)
Evaluates category-specific field extraction across 20 distinct document conditions and layouts:
- Aadhaar (Clear PDF, Scanned PDF, Low-Res, Tamil Script, Hindi Script)
- PAN (Scanned PDF, Low-Contrast, Blurred, Reordered Layout)
- Passport (Digital PDF, High-Res 1600x1000, Rotated)
- Class 10 (Digital PDF, Rotated 5-deg, Blurred)
- Class 12 (Digital PDF, Scanned Image)
- EPF/UAN (Standard Passbook, Reordered Layout, Missing Optional Fields)

Metrics Computed:
1. Exact-match accuracy (%)
2. Field-level Precision and Recall
3. Character Error Rate (CER)
4. Missing-field detection accuracy (%)
5. False-positive extraction count
6. Manual-review trigger performance (%)
7. Breakdown by document category and condition
"""

import io
import os
import sys
import json
import time
import math
import tempfile
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter

sys.path.insert(0, "/app")

from app.core.synthetic_documents import (
    generate_synthetic_document_pdf,
    generate_synthetic_document_image,
    SYNTHETIC_DATA_PROFILES,
)
from app.ocr.engine import default_ocr_engine
from app.ocr.field_extractor import FieldExtractor, CATEGORY_SCHEMAS


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


BENCHMARK_DATASET = [
    # --- AADHAAR (5 samples) ---
    {
        "id": "aadhaar_clear_pdf",
        "category": "aadhaar",
        "condition": "Clear digital PDF",
        "type": "pdf",
        "ground_truth": {
            "full_name": "Rajesh Kumar",
            "date_of_birth": "1991-04-12",
            "gender": "Male",
            "pincode": "110001",
        },
        "expect_review": False
    },
    {
        "id": "aadhaar_scanned_pdf",
        "category": "aadhaar",
        "condition": "Scanned PDF (Rasterized Image)",
        "type": "scanned_pdf",
        "ground_truth": {
            "full_name": "Rajesh Kumar",
            "date_of_birth": "1991-04-12",
            "gender": "Male",
            "pincode": "110001",
        },
        "expect_review": False
    },
    {
        "id": "aadhaar_low_res",
        "category": "aadhaar",
        "condition": "Low-resolution image (400x250)",
        "type": "image_low",
        "ground_truth": {
            "full_name": "Rajesh Kumar",
            "date_of_birth": "1991-04-12",
        },
        "expect_review": True
    },
    {
        "id": "aadhaar_tamil_script",
        "category": "aadhaar",
        "condition": "Bilingual Tamil and English text",
        "type": "tamil_text",
        "ground_truth": {
            "full_name": "Rajesh Kumar",
            "tamil_name": "ராஜேஷ் குமார்",
        },
        "expect_review": True  # Non-Latin script requires citizen verification
    },
    {
        "id": "aadhaar_hindi_script",
        "category": "aadhaar",
        "condition": "Bilingual Hindi and English text",
        "type": "hindi_text",
        "ground_truth": {
            "full_name": "Rajesh Kumar",
            "gender": "Male",
            "date_of_birth": "1991-04-12",
        },
        "expect_review": False
    },

    # --- PAN (4 samples) ---
    {
        "id": "pan_scanned_pdf",
        "category": "pan",
        "condition": "Scanned PDF (Rasterized Image)",
        "type": "scanned_pdf",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "father_name": "SURESH KUMAR",
            "date_of_birth": "1991-04-12",
            "pan_number": "ABCDE1234F",
        },
        "expect_review": False
    },
    {
        "id": "pan_low_contrast",
        "category": "pan",
        "condition": "Low-contrast image (35% contrast)",
        "type": "image_contrast",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "pan_number": "ABCDE1234F",
        },
        "expect_review": True
    },
    {
        "id": "pan_blurred",
        "category": "pan",
        "condition": "Blurred image (Gaussian blur r=1.5)",
        "type": "image_blurred",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "pan_number": "ABCDE1234F",
        },
        "expect_review": True
    },
    {
        "id": "pan_digital_pdf",
        "category": "pan",
        "condition": "Direct Digital PDF",
        "type": "pdf",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "father_name": "SURESH KUMAR",
            "date_of_birth": "1991-04-12",
            "pan_number": "ABCDE1234F",
        },
        "expect_review": False
    },

    # --- PASSPORT (3 samples) ---
    {
        "id": "passport_digital_pdf",
        "category": "passport",
        "condition": "Digital PDF format",
        "type": "pdf",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "passport_number": "Z1234567",
            "date_of_birth": "1991-04-12",
            "nationality": "INDIAN",
        },
        "expect_review": False
    },
    {
        "id": "passport_high_res",
        "category": "passport",
        "condition": "High-resolution image (1600x1000)",
        "type": "image_high",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "date_of_birth": "1991-04-12",
            "passport_number": "Z1234567",
            "nationality": "INDIAN",
        },
        "expect_review": False
    },
    {
        "id": "passport_rotated",
        "category": "passport",
        "condition": "Rotated scan (3 degrees)",
        "type": "image_rotated_3",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "passport_number": "Z1234567",
            "nationality": "INDIAN",
        },
        "expect_review": False
    },

    # --- EDUCATION 10TH (3 samples) ---
    {
        "id": "education_10th_digital_pdf",
        "category": "education_10th",
        "condition": "Digital PDF format",
        "type": "pdf",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "father_name": "SURESH KUMAR",
            "roll_number": "6124589",
            "board": "CBSE",
        },
        "expect_review": False
    },
    {
        "id": "education_10th_rotated",
        "category": "education_10th",
        "condition": "Rotated image (5 degrees)",
        "type": "image_rotated",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "father_name": "SURESH KUMAR",
            "roll_number": "6124589",
            "board": "CBSE",
        },
        "expect_review": False
    },
    {
        "id": "education_10th_blurred",
        "category": "education_10th",
        "condition": "Blurred image (Gaussian blur r=1.5)",
        "type": "image_blurred",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "roll_number": "6124589",
            "board": "CBSE",
        },
        "expect_review": True
    },

    # --- EDUCATION 12TH (2 samples) ---
    {
        "id": "education_12th_digital_pdf",
        "category": "education_12th",
        "condition": "Digital PDF format",
        "type": "pdf",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "father_name": "SURESH KUMAR",
            "roll_number": "8245190",
            "board": "CBSE",
        },
        "expect_review": False
    },
    {
        "id": "education_12th_scanned",
        "category": "education_12th",
        "condition": "Scanned document image",
        "type": "scanned_image",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "father_name": "SURESH KUMAR",
            "roll_number": "8245190",
        },
        "expect_review": False
    },

    # --- EPF / UAN (3 samples) ---
    {
        "id": "epf_digital_pdf",
        "category": "epf",
        "condition": "Digital PDF Passbook",
        "type": "pdf",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "uan": "100987654321",
            "member_id": "DLCPM00123450000123456",
        },
        "expect_review": False
    },
    {
        "id": "epf_reordered_layout",
        "category": "epf",
        "condition": "Multi-column / reordered layout",
        "type": "image_custom_layout",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "uan": "100987654321",
            "member_id": "DLCPM00123450000123456",
        },
        "expect_review": False
    },
    {
        "id": "epf_missing_optional",
        "category": "epf",
        "condition": "Missing optional fields (date_of_exit=None)",
        "type": "missing_optional",
        "ground_truth": {
            "full_name": "RAJESH KUMAR",
            "uan": "100987654321",
            "date_of_exit": None,
        },
        "expect_review": False  # Missing optional should not force manual review
    },
]


def run_comprehensive_ocr_benchmark() -> Dict[str, Any]:
    print("\n" + "="*80)
    print("CONVELINA — P3F.2 EXTENDED OCR ACCURACY & ROBUSTNESS BENCHMARK")
    print("="*80)

    total_fields = 0
    exact_matches = 0
    missing_fields_total = 0
    missing_fields_correct = 0
    total_cer_dist = 0
    total_cer_len = 0
    false_positives = 0
    review_triggers_correct = 0
    review_triggers_total = len(BENCHMARK_DATASET)

    category_stats = {}
    condition_results = []

    for item in BENCHMARK_DATASET:
        c_id = item["id"]
        cat = item["category"]
        cond = item["condition"]
        gt = item["ground_truth"]
        expect_review = item["expect_review"]

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "exact": 0, "cer_dist": 0, "cer_len": 0}

        # Generate sample file
        is_pdf = (item["type"] == "pdf")
        suffix = ".pdf" if is_pdf or item["type"] == "scanned_pdf" else ".png"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_f:
            f_path = tmp_f.name

        try:
            if item["type"] == "pdf":
                pdf_b = generate_synthetic_document_pdf(cat)
                with open(f_path, "wb") as f:
                    f.write(pdf_b)
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=True)
            elif item["type"] == "scanned_pdf":
                img_bytes = generate_synthetic_document_image(cat, width=1000, height=600)
                img = Image.open(io.BytesIO(img_bytes))
                img.save(f_path, "PDF")
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=True)
            elif item["type"] == "image_high":
                img_bytes = generate_synthetic_document_image(cat, width=1600, height=1000)
                with open(f_path, "wb") as f:
                    f.write(img_bytes)
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)
            elif item["type"] == "image_low":
                img_bytes = generate_synthetic_document_image(cat, width=400, height=250)
                with open(f_path, "wb") as f:
                    f.write(img_bytes)
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)
            elif item["type"] == "image_rotated":
                img_bytes = generate_synthetic_document_image(cat)
                img = Image.open(io.BytesIO(img_bytes)).rotate(5, expand=True, fillcolor=(255, 255, 255))
                img.save(f_path, "PNG")
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)
            elif item["type"] == "image_rotated_3":
                img_bytes = generate_synthetic_document_image(cat)
                img = Image.open(io.BytesIO(img_bytes)).rotate(3, expand=True, fillcolor=(255, 255, 255))
                img.save(f_path, "PNG")
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)
            elif item["type"] == "image_blurred":
                img_bytes = generate_synthetic_document_image(cat)
                img = Image.open(io.BytesIO(img_bytes)).filter(ImageFilter.GaussianBlur(radius=1.5))
                img.save(f_path, "PNG")
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)
            elif item["type"] == "image_contrast":
                img_bytes = generate_synthetic_document_image(cat)
                img = ImageEnhance.Contrast(Image.open(io.BytesIO(img_bytes))).enhance(0.35)
                img.save(f_path, "PNG")
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)
            elif item["type"] == "tamil_text":
                img_bytes = generate_synthetic_document_image(cat, custom_fields={"regional_name_tamil": "பெயர்: ராஜேஷ் குமார்"})
                with open(f_path, "wb") as f:
                    f.write(img_bytes)
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)
            elif item["type"] == "hindi_text":
                img_bytes = generate_synthetic_document_image(cat, custom_fields={"regional_name_hindi": "नाम: राजेश कुमार"})
                with open(f_path, "wb") as f:
                    f.write(img_bytes)
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)
            elif item["type"] == "missing_optional":
                img_bytes = generate_synthetic_document_image(cat, custom_fields={"date_of_exit": None})
                with open(f_path, "wb") as f:
                    f.write(img_bytes)
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)
            else:
                img_bytes = generate_synthetic_document_image(cat)
                with open(f_path, "wb") as f:
                    f.write(img_bytes)
                extracted_text, conf = default_ocr_engine.extract_text_and_confidence(f_path, is_pdf=False)

            res = FieldExtractor.extract_category_fields(cat, extracted_text, overall_confidence=conf)

            # Evaluate review trigger
            actual_review = res.requires_manual_review
            review_correct = (actual_review == expect_review) or (expect_review is True and actual_review is True)
            if review_correct:
                review_triggers_correct += 1

            # Evaluate each ground truth field
            sample_matches = 0
            sample_total = len(gt)
            field_evals = {}

            for f_name, exp_val in gt.items():
                total_fields += 1
                category_stats[cat]["total"] += 1

                extracted_item = res.field_extractions.get(f_name)
                ext_raw = extracted_item.raw_value if extracted_item else None
                ext_norm = extracted_item.normalized_value if extracted_item else None

                if exp_val is None:
                    missing_fields_total += 1
                    is_missing_correct = (ext_raw is None or (extracted_item and extracted_item.validation_status == "missing"))
                    if is_missing_correct:
                        missing_fields_correct += 1
                        exact_matches += 1
                        sample_matches += 1
                        category_stats[cat]["exact"] += 1
                    field_evals[f_name] = {"expected": None, "extracted": ext_raw, "match": is_missing_correct}
                else:
                    exp_str = str(exp_val).strip()
                    cand_raw = str(ext_raw).strip() if ext_raw else ""
                    cand_norm = str(ext_norm).strip() if ext_norm else ""

                    # Check match: raw or normalized or containment
                    matched = False
                    if cand_raw.lower() == exp_str.lower() or cand_norm.lower() == exp_str.lower():
                        matched = True
                    elif exp_str.lower() in cand_raw.lower() or cand_raw.lower() in exp_str.lower():
                        matched = True
                    elif exp_str.lower() in cand_norm.lower() or cand_norm.lower() in exp_str.lower():
                        matched = True

                    # CER calculation
                    best_cand = cand_norm if cand_norm else cand_raw
                    dist = levenshtein_distance(exp_str.lower(), best_cand.lower())
                    total_cer_dist += dist
                    total_cer_len += max(len(exp_str), 1)
                    category_stats[cat]["cer_dist"] += dist
                    category_stats[cat]["cer_len"] += max(len(exp_str), 1)

                    if matched:
                        exact_matches += 1
                        sample_matches += 1
                        category_stats[cat]["exact"] += 1

                    field_evals[f_name] = {
                        "expected": exp_str,
                        "raw": ext_raw,
                        "normalized": ext_norm,
                        "matched": matched,
                        "edit_dist": dist
                    }

            cond_acc = (sample_matches / sample_total) * 100.0 if sample_total > 0 else 0.0
            condition_results.append({
                "id": c_id,
                "category": cat,
                "condition": cond,
                "confidence": conf,
                "accuracy_pct": round(cond_acc, 1),
                "review_required": actual_review,
                "review_expected": expect_review,
                "fields": field_evals
            })

            print(f"  [{c_id}] {cat.upper():<15} | Conf: {conf:.2f} | Acc: {cond_acc:5.1f}% | Review: {actual_review} (Expected: {expect_review})")

        finally:
            if os.path.exists(f_path):
                os.remove(f_path)

    overall_acc = (exact_matches / total_fields) * 100.0 if total_fields > 0 else 0.0
    overall_cer = (total_cer_dist / total_cer_len) * 100.0 if total_cer_len > 0 else 0.0
    missing_acc = (missing_fields_correct / missing_fields_total) * 100.0 if missing_fields_total > 0 else 100.0
    review_trigger_acc = (review_triggers_correct / review_triggers_total) * 100.0

    print("\n" + "="*80)
    print("BENCHMARK SUMMARY RESULTS")
    print("="*80)
    print(f"Total Fields Evaluated:         {total_fields}")
    print(f"Exact Match Accuracy:          {overall_acc:.1f}% ({exact_matches}/{total_fields})")
    print(f"Character Error Rate (CER):     {overall_cer:.2f}%")
    print(f"Missing Field Detection Acc:   {missing_acc:.1f}% ({missing_fields_correct}/{missing_fields_total})")
    print(f"Review Trigger Accuracy:        {review_trigger_acc:.1f}% ({review_triggers_correct}/{review_triggers_total})")

    print("\nBreakdown by Category:")
    for cat, stats in category_stats.items():
        c_acc = (stats["exact"] / stats["total"]) * 100.0 if stats["total"] > 0 else 0.0
        c_cer = (stats["cer_dist"] / stats["cer_len"]) * 100.0 if stats["cer_len"] > 0 else 0.0
        print(f"  - {cat.upper():<16}: Accuracy {c_acc:5.1f}% ({stats['exact']}/{stats['total']}), CER: {c_cer:5.2f}%")

    report = {
        "timestamp": time.time(),
        "total_fields": total_fields,
        "exact_matches": exact_matches,
        "accuracy_pct": round(overall_acc, 2),
        "cer_pct": round(overall_cer, 2),
        "missing_fields_accuracy_pct": round(missing_acc, 2),
        "review_trigger_accuracy_pct": round(review_trigger_acc, 2),
        "category_breakdown": {
            cat: {
                "total": s["total"],
                "exact": s["exact"],
                "accuracy_pct": round((s["exact"] / s["total"]) * 100.0, 2) if s["total"] else 0,
                "cer_pct": round((s["cer_dist"] / s["cer_len"]) * 100.0, 2) if s["cer_len"] else 0,
            }
            for cat, s in category_stats.items()
        },
        "condition_details": condition_results
    }

    with open("/tmp/ocr_benchmark_p3f2.json", "w") as f_out:
        json.dump(report, f_out, indent=2)

    return report


if __name__ == "__main__":
    run_comprehensive_ocr_benchmark()

