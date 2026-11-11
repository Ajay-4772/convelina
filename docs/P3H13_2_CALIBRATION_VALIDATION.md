# P3H.13.2 — Confidence Calibration Validation & Metric Reconciliation

## 1. Executive Summary

CONVELINA enforces a fail-safe confidence contract: confidence scores $p \in [0.0, 1.0]$ must reflect empirical correctness probabilities so degraded or misparsed extractions never bypass citizen review. Milestone P3H.13.2 validates `ConfidenceCalibrator` (`backend/app/ocr/calibrator.py`), isolates token-, document-, and field-level confidence definitions, audits dataset separation for zero leakage, and reconciles all previously reported calibration metrics under strictly identical evaluation formulas.

---

## 2. Granularity & Dataset Separation Definitions

A frequent source of confusion in OCR benchmarking is conflating confidence granularities or development/evaluation sets:

| Concept | Exact Mathematical Definition in CONVELINA | Origin / Dataset Scope |
| :--- | :--- | :--- |
| **Calibration / Heuristic Observation Set** | `benchmarks/p3h12/` (48 samples): Used during P3H.12 and P3H.13 failure analysis to determine objective degradation thresholds (`lap_var < 65`, `intensity_std < 38`, `min_dim < 600`, review cutoff `< 0.75`). | **Development Only**. Zero statistical regression/Platt/isotonic weights were fit on `p3h13`. |
| **Independent Evaluation Set** | `benchmarks/p3h13/` (48 unseen holdout images, 432 fields): Completely separated identities (`prof_h1`–`prof_h6`) evaluated strictly out-of-sample with frozen heuristic thresholds. | **Zero Leakage Confirmed**. |
| **Raw Token-Level Confidence** | Mean Tesseract per-word beam-search probability $\frac{1}{W} \sum_{w=1}^W c_w / 100$ directly from `pytesseract.image_to_data`. Unpenalized for blur/lighting. | Measured on preprocessed image ($N = 432$ field pairs). |
| **Document-Level Confidence** | `doc_ocr_confidence = max(0.30, raw_word_conf - quality_penalty)`. Penalizes raw input blur, low contrast STD, and low pixel resolution. | Matches historical P3H.12 (`0.2847`) and P3H.13.1 (`0.1888`) metric definition. |
| **Field-Level Confidence** | `FieldExtractionResult.confidence`: `0.0` if missing; otherwise `min(0.95, doc_conf * parser_conf)` if format passes, and hard-capped `<= 0.45` if statutory format validation fails (`pan_ocr_repaired` lowers `parser_conf` to `0.60`). | Evaluable across **All Fields** ($M = 432$) or **Extracted Non-Missing Fields Only** ($M = 236$). |

---

## 3. Reconciliation of All Reported Brier Scores & ECE Figures

Evaluating Pipeline A (P3H.12 baseline) and Pipeline B (P3H.13.2 hardened) across identical 48 holdout images ($M = 432$ fields) reconciles every previously reported figure transparently:

| Historical / Current Metric Reference | Underlying Dataset | Confidence Level Used | Brier Score | 10-Bin ECE | Explanation / Reconciliation |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **P3H.12 Preserved Baseline** | `p3h12` (48 samples, 453 fields) | Document-Level | `0.2847` | `0.2210` | Original P3H.12 baseline on dev set (exact match 37.09%). |
| **P3H.13.1 Baseline Re-run** | `p3h12` (48 samples, 453 fields) | Document-Level | `0.1877` | `0.1135` | Included P3H.13 hardcoded `issuing_authority` + `aadhaar[-4:]` inflation (exact match 54.53%). |
| **P3H.13.1 Holdout Reported** | `p3h13` (48 samples, 432 fields) | Document-Level | `0.1888` | `0.1100` | Included P3H.13 hardcoded `issuing_authority` + `aadhaar[-4:]` inflation (exact match 48.84%). |
| **P3H.13.2 Paired Raw Token (A $\to$ B)**| `p3h13` (48 samples, 432 fields) | **Raw Word-Level** | 0.4176 $\to$ **0.3744** | 0.4795 $\to$ **0.3691** | Unpenalized Tesseract confidence is severely overconfident ($\text{ECE} > 0.36$). |
| **P3H.13.2 Paired Doc-Level (A $\to$ B)** | `p3h13` (48 samples, 432 fields) | **Document-Level** | 0.2757 $\to$ **0.2344** | 0.3301 $\to$ **0.1946** | **True unbiased holdout comparison** under identical strict scoring (without fabrication/partial hacks). |
| **P3H.13.2 Field-Level (All 432)** | `p3h13` (48 samples, 432 fields) | **Field-Level** | **0.0828** | **0.0946** | Includes 196 missing fields properly scored `p = 0.0, y = 0`. |
| **P3H.13.2 Field-Level (Extracted 236)** | `p3h13` (48 samples, 236 fields) | **Field-Level (Non-Missing)** | **0.1516** | **0.1731** | Evaluates genuine predictive calibration strictly among populated extractions. |

### Key Analytical Reason for the `0.1888` $\to$ `0.2344` Holdout Difference:
In `2d2227b`, the Brier score measured `0.1888` because hardcoded `issuing_authority` and last-4 Aadhaar matching falsely flipped failing field outcomes from $y=0$ to $y=1$ while document confidence was $0.60$–$0.76$, shrinking squared residuals $(p - y)^2$. Removing those non-compliant rules during P3H.13.2 yields the true honest unbiased holdout Brier score (**0.2344** at document level, **0.1516** on extracted field level), still materially outperforming Pipeline A (**0.2757** document level) and raw Tesseract (**0.3744**).

---

## 4. Reproducible 10-Bin Reliability Diagrams (P3H.13 Holdout)

### 4.1. Document-Level Calibrated Confidence (`doc_ocr_confidence`, $M = 432$ fields)
**Brier Score**: `0.2344` | **ECE**: `0.1946` | **MCE**: `0.5598`

| Bin Interval | Count ($|B_m|$) | Mean Confidence | Empirical Accuracy | Gap $|\text{acc} - \text{conf}|$ | Diagnostic Observation |
| :---: | :---: | :---: | :---: | :---: | :--- |
| $[0.0, 0.2)$ | 0 | — | — | — | Empty (0.30 minimum engine confidence floor) |
| $[0.2, 0.3)$ | 40 | 0.3000 | 0.1250 | 0.1750 | Extreme `low_resolution` / degradation; 100% reviewed |
| $[0.3, 0.4)$ | 6 | 0.3129 | 0.1667 | 0.1462 | Sub-threshold low-res PAN; 100% reviewed |
| $[0.4, 0.5)$ | 17 | 0.4484 | 0.1765 | 0.2719 | Heavy compression/blur; 100% reviewed |
| $[0.5, 0.6)$ | 65 | 0.5598 | 0.0000 | **0.5598** | **Worst-Case Gap (MCE)**: CLAHE amplified blur speckles into contrast spikes rated 0.56 by Tesseract on unreadable docs |
| $[0.6, 0.7)$ | 89 | 0.6524 | 0.3258 | 0.3265 | Transitional shadow/compression border; 100% reviewed |
| $[0.7, 0.8)$ | **215** | **0.7633** | **0.7349** | **0.0285** | **Primary Operational Regime**: High precision — empirical accuracy aligns within **2.85%** |
| $[0.8, 1.0]$ | 0 | — | — | — | Empty due to conservative penalty & parser multiplier cap |

### 4.2. Field-Level Calibrated Confidence (`FieldExtractionResult.confidence`, Non-Missing $M = 236$ fields)
**Brier Score**: `0.1516` | **ECE**: `0.1731` | **MCE**: `0.3790`

| Bin Interval | Count ($|B_m|$) | Mean Confidence | Empirical Accuracy | Gap | Diagnostic Observation |
| :---: | :---: | :---: | :---: | :---: | :--- |
| $[0.1, 0.2)$ | 1 | 0.1880 | 0.0000 | 0.1880 | Sparse bin ($N=1$) |
| $[0.2, 0.3)$ | 9 | 0.2877 | 0.6667 | 0.3790 | Under-confident: regex rescued valid fields despite low image quality score (safely triggers review) |
| $[0.3, 0.4)$ | 10 | 0.3309 | 0.5000 | 0.1691 | Format-failure / severe-blur ceiling ($\le 0.45$) |
| $[0.4, 0.5)$ | 7 | 0.4541 | 0.4286 | 0.0256 | Repaired/compressed field extractions closely calibrated |
| $[0.5, 0.6)$ | 15 | 0.5717 | 0.5333 | 0.0383 | Near-calibrated borderline fields; review triggered ($<0.75$) |
| $[0.6, 0.7)$ | 37 | 0.6601 | 0.8649 | 0.2048 | Conservatively under-confident (+20.5% safer than stated confidence) |
| $[0.7, 0.8)$ | **157** | **0.7309** | **0.9045** | **0.1735** | Conservatively safe: 90.45% empirical accuracy at 0.73 mean confidence (0 dangerous overconfidence) |

*(Note: Adding the 196 missing fields scored $p=0.0, y=0$ in $[0.0, 0.1)$ reduces total field-level Brier across $M=432$ to `0.0828` and ECE to `0.0946`.)*

---

## 5. Calibration Limitations & Statistical Caveats
1. **Non-Uniform Bin Coverage**: Because `FieldExtractor` applies a $0.95$ parser multiplier and quality penalties, no predictions fall in $(0.80, 1.00]$. Four bins (`[0.1, 0.5)`) contain $\le 10$ samples each, yielding wide binomial uncertainty.
2. **Blur/CLAHE Overconfidence Artifact (`[0.5, 0.6)`)**: Notice in Doc-Level bin `[0.5, 0.6)` ($N=65$), CLAHE contrast enhancement artificially sharpened pure Gaussian blur artifacts, tricking Tesseract into emitting ~0.56 confidence where 0 fields succeeded (`acc=0.0000`). Because manual review intercepts all scores `< 0.75`, **zero** of those 65 cases escaped human inspection.
3. **No Live Production Isotonic Fit Yet**: Statistical probability calibration (`Platt Scaling` or `Isotonic Regression`) requires an empirical corpus of hundreds of real scanned citizen documents collected post-consent rather than 48 synthetic renders.

