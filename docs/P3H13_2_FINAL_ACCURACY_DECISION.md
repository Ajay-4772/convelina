# P3H.13.2 — Final OCR Accuracy Decision & Milestone Acceptance

## 1. Final Verdict

**Decision**: **ACCEPTED FOR LOCAL DEVELOPMENT** *(Cleanly validated on local Docker + synthetic benchmarks; NOT cleared for unattended real-world production automation without human-in-the-loop review and real-camera validation).*

---

## 2. Synthetic vs. Real-World OCR Performance Distinction

| Property | Synthetic Benchmark Evidence (`p3h12` / `p3h13`) | Real-World Citizen Document Conditions (Production Reality) |
| :--- | :--- | :--- |
| **Input Provenance** | 48 synthetic PNG/JPEG images rendered via Python PIL from 6 standardized templates (`prof_h1`–`prof_h6`). | Diverse mobile camera captures, flatbed PDFs, WhatsApp forwards, stamps, signatures, watermarks, laminates, holograms, and physical wear. |
| **Observed Accuracy** | Strict exact field match rate jumped **27.55% $\to$ 45.37%** (+17.82 pct pts; $p < 10^{-10}$); **47.69%** when accounting for ephemeral 12-digit Aadhaar reading; **77.78%** on `clean_scan`; **79.63%** on `skewed_rot`. | Expected real-world raw extraction accuracy on wrinkled, shadowed, multi-lingual citizen IDs will vary widely below clean synthetic scans — making CONVELINA's manual-review gate mandatory rather than optional. |
| **Known Shadow Limit** | `photo_shadow` on Tesseract + CLAHE scored only **11.11%**, compared to **68.52%** achieved by `RapidOCR` (PP-OCR ONNX). | Real mobile camera lighting shadows on glossy laminated PAN/Aadhaar cards will frequently route through CONVELINA's `< 0.75` review boundary until adaptive thresholding or ONNX DBNet detection is integrated. |
| **Safety Guarantee** | **0.00% FAR** across 64 deterministic identity cases AND **0 false acceptances** across 144 live degraded OCR cross-comparisons. | Because deterministic comparison enforces citizen confirmation (`is_user_confirmed=True`), OCR errors **never** generate automated false matches or erroneous correction drafts. |

---

## 3. Compliance Against All Nine P3H.13.2 Acceptance Criteria

| Criterion | Status | Verification Evidence |
| :--- | :---: | :--- |
| 1. Both OCR pipelines run on the exact same independent holdout | **PASS** | `evaluate_p3h13_2_paired.py` executed verbatim `cb12356` (`p3h12`) vs current `p3h13` inside `convelina-backend:latest` on all 48 images in `benchmarks/p3h13/`. |
| 2. Baseline and enhanced results independently reproducible | **PASS** | All commands, snapshots, container recipes, and output JSON artifacts (`raw_p3h12_on_holdout.json`, `raw_p3h13_on_holdout.json`, `paired_benchmark_results.json`) preserved in repository. |
| 3. Every reported metric includes explicit denominators | **PASS** | Every aggregate, category, condition, and field metric reports `n / M` ($N=48$ images, $M=432$ fields, $M_{\text{core}}=280$ core printed fields). |
| 4. All six Tier 1 categories represented | **PASS** | Aadhaar (64 fields), PAN (48 fields), Passport (72 fields), Class 10 (88 fields), Class 12 (88 fields), EPFO/UAN (72 fields). |
| 5. Alternative engines accurately labelled (Executed vs. Researched) | **PASS** | `RapidOCR 1.2.3` and `EasyOCR 1.7.2` executed empirically across all 48 holdout images; native `paddleocr 3.7.0` documented as dry-run audited; PyPI Apache-2.0 licenses verified. |
| 6. Calibration methodology transparent & zero leakage | **PASS** | Separated raw word-, document-, and field-level metrics; verified heuristic thresholds originated from `p3h12` with zero fitting on `p3h13` holdout labels; reconciled all historical Brier/ECE numbers. |
| 7. All seven downstream invariants intact | **PASS** | Verified via 7 explicit tests in `test_p3h13_ocr_engineering.py`, 64-case comparison benchmark (FAR 0.00%, FRR 0.00%), and 144 live OCR stress pairs (0 false acceptances). |
| 8. Zero security, Aadhaar Act, or tenant-isolation regressions | **PASS** | Remediated `aadhaar.py` unmasked leakage (`test_aadhaar_parser_masking` passes); restored `engine.py` fallback `_extract_from_image`; removed fabricated `issuing_authority`; **10/10** PostgreSQL 16 forced RLS tests passed; OpenQodex clean. |
| 9. Remaining accuracy limitations honestly documented | **PASS** | Documented unconditional `MedianFilter(3)` stroke erosion on thin fonts, `photo_shadow` vulnerability (`11.11%`), unpadded synthetic passport MRZ formatting, and sparse calibration bins. |

---

## 4. Field Correctness & Safety Fixes Completed in P3H.13.2

In resolving P3H.13.2 audit checks, six real correctness and compliance defects were fixed in production code:
1. **Aadhaar Act Privacy Masking Restored (`backend/app/ocr/parsers/aadhaar.py`)**: Never exposes first 8 digits in `parsed["fields"]` (`XXXX-XXXX-1234` only); added transient in-memory `extract_ephemeral_full_number()` helper purely for unstored Verhoeff/benchmark validation (`test_upload_ocr.py::test_aadhaar_parser_masking` fixed).
2. **Engine Fallback Method Restored (`backend/app/ocr/engine.py`)**: Restored missing `_extract_from_image()` accidentally removed during P3H.13 refactor (`test_field_level_ocr_and_user_confirmation.py::test_document_user_confirmation_lifecycle` fixed).
3. **Eliminated Unconditional `issuing_authority` Fabrication (`aadhaar.py`, `pan.py`, `passport.py`, `epf.py`, `field_extractor.py`)**: Issuing authority is now emitted **only** when textual evidence exists in OCR output (`0%` fabrication on unreadable blur noise).
4. **Passport MRZ Check-Digit Overwrite Guard (`backend/app/ocr/parsers/passport.py`)**: Prevents failed-checksum / shifted MRZ sequences (`N67890120`) from overwriting clean VIZ passport numbers (`N6789012`).
5. **PAN Character Substitution Review Flagging (`pan.py`, `field_extractor.py`)**: Fallback confusion substitutions (`0->O`, `O->0`) explicitly mark `pan_ocr_repaired = True` and lower `parser_confidence = 0.60` (`val_status = "repaired_needs_review"`), mandating citizen confirmation instead of silent acceptance (`CVBMS9012Q -> CVBMS9012O`).
6. **Education Board & Name Boundary Fixes (`education.py`)**: Restored full raw matched board title for `EducationCertificateParser.parse()` (`test_upload_ocr.py::test_education_certificate_parser` fixed while keeping `FieldExtractor` normalized `"CBSE"`/`"ICSE"`) and prevented `Candidate Name: = ...` thresholding artifacts from capturing literal `"name"`.

---

## 5. Production Readiness Roadmap (Post-P3H.13 Local Milestone)
Before promoting OCR workflows beyond local development into live production:
1. Replace global median filtering on clean sharp scans with noise-gated despeckling + conditional Sauvola adaptive binarization (or benchmark hybrid **Deskew + `RapidOCR` PP-OCR ONNX** integration targeting >65% accuracy on camera shadow conditions without PyTorch bloat).
2. Validate against an ethics-approved, consented multi-template dataset of physical photographed ID documents (including holographic reflections and bilingual stamps).
3. Refit empirical confidence calibration (temperature/isotonic scaling) on out-of-sample live camera telemetry once $N > 500$ anonymized field extractions are accumulated cleanly.

