# P3H.13.2 — Paired OCR Benchmark Report (Independent Holdout Dataset)

## 1. Executive Summary & Experimental Design

Previous P3H.13 evaluations compared P3H.12 baseline metrics measured on `benchmarks/p3h12/` against P3H.13 enhanced metrics measured on `benchmarks/p3h13/`. Milestone P3H.13.2 eliminates dataset mismatch by running a strictly **paired, controlled benchmark** on the exact same **48 images and 48 ground-truth annotations in `benchmarks/p3h13/`** (6 Tier 1 categories $\times$ 8 environmental conditions across 6 unseen fictional profiles `prof_h1`–`prof_h6`):

- **Pipeline A (Original P3H.12 Baseline)**: Exact verbatim codebase extracted from Git commit [`cb12356`](https://github.com/Ajay-4772/convelina/commit/cb12356) (`backend/app/ocr/engine.py`, `field_extractor.py`, and original 5 parsers). Executed inside `convelina-backend:latest` (Tesseract 5.5.0 + Leptonica 1.84.1).
- **Pipeline B (Enhanced P3H.13.x Pipeline)**: Current `HEAD` pipeline featuring modular image preprocessing (`ImagePreprocessor`), ICAO Doc 9303 Part 4 MRZ parsing with 7-3-1 check-digit gating (`MRZParser`), hardened parsers with Aadhaar Act masking, and evidence-gated extraction. Executed inside the identical `convelina-backend:latest` container under identical scoring rules.

> [!IMPORTANT]
> **Methodological Integrity Rules Enforced**:
> - **Identical Normalization & Ground Truth**: Both pipelines are scored using identical date canonicalization (`YYYY/MM/DD`) and strict normalized equality (`norm_gt == norm_ext`).
> - **Zero Anti-Masking or Partial-Match Hacks**: Partial last-4 Aadhaar matching is prohibited. Hardcoded `issuing_authority` fabrication on empty/noisy text is disabled. Repaired PAN values (`0->O`) are flagged as `repaired_needs_review` for mandatory citizen review.

---

## 2. Headline Paired Results ($N = 48$ Images, $M = 432$ Ground-Truth Fields)

| Evaluation Metric | Pipeline A (`cb12356` P3H.12 Baseline) | Pipeline B (P3H.13.x Enhanced) | Absolute Change | Relative Change | Denominator |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Strict Exact Field Match Rate** | **27.55%** (119 / 432) | **45.37%** (196 / 432) | **+17.82 pct pts** | **+64.68%** | 432 annotated fields |
| **Missing Field Rate** | 64.35% (278 / 432) | **45.37%** (196 / 432) | **-18.98 pct pts** | **-29.50%** | 432 annotated fields |
| **Incorrect Field Rate** | 8.10% (35 / 432) | 9.26% (40 / 432) | +1.16 pct pts | +14.32% | 432 annotated fields |
| **Ephemeral 12-Digit Aadhaar Adjusted** | 29.40% (127 / 432) | **47.69%** (206 / 432) | **+18.29 pct pts** | **+62.21%** | 432 fields (transient raw digits) |
| **Core Deduplicated Printed Fields** | 38.57% (108 / 280) | **45.71%** (128 / 280) | **+7.14 pct pts** | **+18.51%** | 280 non-redundant printed fields |
| **Overall Mean CER** | 53.59% | 54.52% | +0.93 pct pts | +1.74% | 48 full-document transcripts |
| **Overall Mean WER (Standard)** | 66.70% | 66.71% | +0.01 pct pts | +0.01% | 48 full-document transcripts |
| **Manual Review Recall (Degraded Scans)** | 100.0% (18 / 18) | **100.0%** (18 / 18) | — | — | 18 expected-review samples |
| **Processing Latency (p50)** | 3,762.64 ms | 6,442.72 ms | +2,680.08 ms | +71.23% | 48 CPU executions |
| **Processing Latency (p95)** | 13,886.69 ms | 15,571.60 ms | +1,684.91 ms | +12.13% | 48 CPU executions |

### Paired Sample & McNemar Statistical Analysis
- **Per-Image Paired Direction ($N = 48$ images)**:
  - **Improved (`B > A`)**: **31 images** (64.6%)
  - **Tied (`B = A`)**: **16 images** (33.3%)
  - **Regressed (`B < A`)**: **1 image** (`pan_blur_noise`: Pipeline A randomly matched on degraded text whereas Pipeline B cleanly abstained as missing).
- **Per-Field $2 \times 2$ McNemar Contingency Table ($M = 432$ paired field outcomes)**:
  - Both exact ($n_{11}$): **106 fields**
  - P3H.13 gained ($n_{01}: A=0, B=1$): **90 fields**
  - P3H.13 regressed ($n_{10}: A=1, B=0$): **13 fields**
  - Both missing/incorrect ($n_{00}$): **223 fields**
  - Exact two-sided binomial $p$-value: **$p < 10^{-10}$** (statistically decisive net gain).
  - With ephemeral 12-digit Aadhaar evaluation: $n_{11} = 112$, $n_{01} = 94$, $n_{10} = 15$, $p < 10^{-10}$.

---

## 3. Category-by-Category Breakdown ($N = 8$ Images per Category)

| Document Category | Total Fields ($M_c$) | Core Printed Fields | Pipeline A Exact (%) | Pipeline B Exact (%) | Gain ($\Delta$ pts) | Core Exact (A $\to$ B) | CER (A $\to$ B) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Aadhaar Card** | 64 | 40 | 15.62% (10/64) | **21.88%** (14/64) | +6.26 pts | 25.00% $\to$ 22.50%* | 43.95% $\to$ 53.27% |
| **PAN Card** | 48 | 32 | 10.42% (5/48) | **27.08%** (13/48) | +16.66 pts | 15.62% $\to$ 21.88% | 57.81% $\to$ 59.26% |
| **Passport** | 72 | 32 | 26.39% (19/72) | **44.44%** (32/72) | +18.05 pts | 25.00% $\to$ 43.75% | 74.96% $\to$ 75.65% |
| **Class 10 Certificate** | 88 | 64 | 36.36% (32/88) | **55.68%** (49/88) | +19.32 pts | 50.00% $\to$ 54.69% | 49.73% $\to$ 47.05% |
| **Class 12 Certificate** | 88 | 64 | 35.23% (31/88) | **59.09%** (52/88) | +23.86 pts | 48.44% $\to$ 57.81% | 51.43% $\to$ 46.35% |
| **EPFO / UAN Records** | 72 | 48 | 30.56% (22/72) | **50.00%** (36/72) | +19.44 pts | 45.83% $\to$ 54.17% | 43.66% $\to$ 45.55% |

*\*Note on Aadhaar strict score*: Persisted `aadhaar_number` is strictly masked to `XXXX-XXXX-6789` (Aadhaar Act privacy enforcement), scoring 0/8 against plaintext 12-digit ground truth `8901 2345 6789` under strict schema matching. Under transient ephemeral 12-digit extraction evaluation prior to masking, Aadhaar 12-digit accuracy rose from **4/8 (50.0%)** in Pipeline A to **5/8 (62.5%)** in Pipeline B.

---

## 4. Image Condition Breakdown ($N = 6$ Images, $M = 54$ Fields per Condition)

| Capture Condition | Pipeline A Exact (%) | Pipeline B Exact (%) | Gain ($\Delta$ pts) | CER (A $\to$ B) | Review Triggered (B) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `clean_scan` | 53.70% (29/54) | **77.78%** (42/54) | **+24.08 pts** | 32.51% $\to$ 33.55% | 100.0% (schema gaps + threshold) |
| `skewed_rot` | 48.15% (26/54) | **79.63%** (43/54) | **+31.48 pts** | 32.63% $\to$ 33.36% | 100.0% |
| `bilingual_script` | 53.70% (29/54) | **74.07%** (40/54) | **+20.37 pts** | 32.45% $\to$ 34.73% | 100.0% |
| `obscured_crease` | 35.19% (19/54) | **64.81%** (35/54) | **+29.62 pts** | 37.33% $\to$ 35.82% | 100.0% |
| `compression` | 24.07% (13/54) | **44.44%** (24/54) | **+20.37 pts** | 40.35% $\to$ 37.83% | 100.0% |
| `low_resolution` | 0.00% (0/54) | **11.11%** (6/54) | **+11.11 pts** | 74.03% $\to$ 67.63% | 100.0% |
| `photo_shadow` | 3.70% (2/54) | **11.11%** (6/54) | **+7.41 pts** | 88.16% $\to$ 94.25% | 100.0% |
| `blur_noise` | 1.85% (1/54) | 0.00% (0/54) | -1.85 pts | 91.28% $\to$ 99.00% | 100.0% |

---

## 5. Field-Level Correctness Audit & Regression Root Causes

### 5.1. Detailed Identifier Performance Across Both Pipelines ($A \to B$)
| Field Name | Denominator ($M_f$) | Pipeline A Exact | Pipeline B Exact | Engineering Audit Findings |
| :--- | :---: | :---: | :---: | :--- |
| `full_name` | 48 | 14 (29.2%) | **20 (41.7%)** | Education & Aadhaar multi-line capture gains |
| `date_of_birth` | 40 | 12 (30.0%) | **18 (45.0%)** | PAN slashes & date anchor stabilization |
| `surname` | 8 | 0 (0.0%) | **6 (75.0%)** | MRZ line-1 `GREWAL<<...` & VIZ extraction |
| `parent_guardian_name` | 16 | 0 (0.0%) | **9 (56.2%)** | Schema unification with education certificates |
| `issuing_authority` | 48 | 0 (0.0%) | **35 (72.9%)** | Extracted strictly from OCR agency tokens (`0%` on noise) |
| `document_number` | 48 | 0 (0.0%) | **14 (29.2%)** | Cross-category canonical identifier aliasing |
| `aadhaar_number` (12d ephem) | 8 | 4 (50.0%) | **5 (62.5%)** | Lanczos upscaling rescued `low_resolution` & `compression` |
| `pan_number` | 8 | 2 (25.0%) | **0 (0.0%)** | Tesseract misread `CVBMS9012Q` as `...0`; repaired to `...O` & flagged |
| `passport_number` | 8 | 4 (50.0%) | 2 (25.0%) | Median filter degraded VIZ number; check-digit rejected shifted MRZ |
| `uan` (EPFO) | 8 | 4 (50.0%) | 4 (50.0%) | Eliminated P3H.12 false substring grab on `epf_compression` |

### 5.2. Root Cause Analysis of All 13 Field Regressions ($A=1, B=0$)
Inspection of the raw OCR transcripts revealed three concrete, instructive mechanisms behind the 13 field losses:
1. **`MedianFilter(size=3)` Stroke Erosion on Clean Thin Fonts (9 regressions)**:
   In `backend/app/ocr/preprocessing.py`, unconditional 3x3 median despeckling thinned 1–2 px colons and curved tails. On `aadhaar_bilingual_script`, labels `Name:`, `DOB:`, `Gender:` vanished completely (`full_name` lost label anchor $\to$ `None`). On `pan_clean_scan`, `CVBMS9012Q` lost the tail of `Q`, becoming `CVBMS90120` (repaired to wrong `CVBMS9012O` rather than `Q`). On `passport_clean_scan`, `Passport No: N6789012` dropped `N6789012` and `Sex F`.
2. **Strict Check-Digit Gating & Non-Padded Synthetic MRZ (3 passport regressions)**:
   In `benchmarks/p3h13/annotations/passport_*.json`, the synthetic generator produced unpadded 8-char line-2 MRZ strings (`N67890120IND9105050F2805090<<<<<<<<<<<<<<<00`) omitting position-8 filler `<` and using `'0'` check digits. `MRZParser` rightly rejected invalid checksums (`passport_check_valid=False`), and `PassportParser` refused to pass corrupted `N67890120`, returning `None` when VIZ `N6789012` was erased by median filtering.
3. **Compression Digit Confusion (`2` $\to$ `7`) & Missing Label (2 education regressions)**:
   On `education_10th_compression`, `passing_year` `2002` read as `2007`.

---

## 6. Dataset Scope & Limitations
1. **Small Synthetic Sample Size**: $N = 48$ images across 6 static synthetic templates (`prof_h1`–`prof_h6`, 1 template per category). Synthetic PIL renders have sharp vector anti-aliased fonts rather than real paper textures, glare, holograms, or mobile camera perspective warp.
2. **Fields Absent on Visual Templates**: Ground-truth annotations include `aadhaar.pincode` (8 instances) and `epf.establishment_id` label (8 instances) even though those labels were not rendered onto the synthetic image text, bounding maximum possible strict schema accuracy to $< 100\%$.
3. **CPU Shadow Weakness**: `photo_shadow` achieved only **11.11%** on Tesseract + CLAHE because local Sauvola thresholding was disabled by default (`adaptive_threshold_enabled=False`).

*Artifacts generated*: [`paired_benchmark_results.json`](file:///c:/Users/ajaya/Desktop/consolin/benchmarks/p3h13/paired_benchmark_results.json), [`raw_p3h12_on_holdout.json`](file:///c:/Users/ajaya/Desktop/consolin/benchmarks/p3h13/raw_p3h12_on_holdout.json), [`raw_p3h13_on_holdout.json`](file:///c:/Users/ajaya/Desktop/consolin/benchmarks/p3h13/raw_p3h13_on_holdout.json).

