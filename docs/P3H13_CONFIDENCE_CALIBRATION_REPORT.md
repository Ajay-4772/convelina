# P3H.13 — Confidence Calibration & Reliability Metrics Report

## 1. Executive Summary & Calibration Mandate

In safety-critical identity verification systems, uncalibrated confidence scores create dangerous failure modes. If an OCR system reports 95% confidence on an erroneous name or date of birth, downstream processes may auto-accept a corrupted record, causing false acceptance (FAR > 0) or citizen identity misattribution.

The CONVELINA operating contract enforces an empirical rule:
> **Confidence Calibration Mandate**: A confidence score $p \in [0.0, 1.0]$ must represent a genuine empirical probability. That is, across all extractions assigned confidence $p$, approximately $100 \times p\%$ must be ground-truth correct.

In P3H.12, raw Tesseract engine confidence exhibited severe overconfidence on corrupted text (Brier score $= 0.3347$). P3H.13 implements `ConfidenceCalibrator` (`backend/app/ocr/calibrator.py`), formalizing mathematical calibration across token, field, and document levels.

---

## 2. Mathematical Framework

```mermaid
flowchart LR
    Token["Token Level<br/>Tesseract LSTM Logits & Char Heights"] --> Field["Field Level<br/>Multi-Factor Calibration Engine"]
    Format["Format Validation<br/>(Verhoeff, ICAO 7-3-1, Regex)"] --> Field
    Quality["Image Quality Penalties<br/>(Blur, Contrast, Resolution)"] --> Field
    Field --> Doc["Document Level<br/>Harmonic / Min Aggregate"]
    Doc --> ECE["Reliability Assessment<br/>(Brier Score, 10-Bin ECE, MCE)"]
```

### 2.1. Multi-Level Calibration Hierarchy

1. **Character & Token Level**: Raw character log-odds and token bounds produced by Tesseract 5.5.0 LSTM beam search.
2. **Field Level**: Calibrated score $C_{\text{field}} \in [0.0, 1.0]$ evaluating:
   - Token OCR confidence ($c_{\text{ocr}}$).
   - Parser anchor precision ($c_{\text{anchor}}$: $1.0$ for exact statutory label, $0.75$ for heuristic proximity).
   - Format validity ($\phi \in \{0, 1\}$: statutory regex, Verhoeff, ICAO Doc 9303 checksums).
   - Image degradation penalties ($P_{\text{qual}} = P_{\text{blur}} + P_{\text{contrast}} + P_{\text{res}}$).
3. **Document Level**: Joint document confidence:
   $$C_{\text{doc}} = \min_{f \in \text{critical}} C_f \cdot \left( \frac{1}{N} \sum_{i=1}^N C_i \right)^{1/2}$$
   Guarantees that a single failing critical field (e.g. invalid name or DOB) bounds the entire document's confidence.

### 2.2. Mathematical Calibration Metrics

#### Brier Score
The mean squared difference between predicted confidence $p_i$ and binary ground truth outcome $y_i \in \{0, 1\}$:
$$\text{BS} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$
Lower is better: $\text{BS} = 0.0$ indicates perfect prediction; $\text{BS} = 0.25$ indicates an uninformative random guess ($p=0.5$).

#### Expected Calibration Error (ECE)
Partitions predicted probabilities into $M = 10$ uniform intervals $B_m = (\frac{m-1}{M}, \frac{m}{M}]$:
$$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
where $\text{acc}(B_m) = \frac{1}{|B_m|} \sum_{i \in B_m} y_i$ and $\text{conf}(B_m) = \frac{1}{|B_m|} \sum_{i \in B_m} p_i$.

#### Maximum Calibration Error (MCE)
Measures the worst-case divergence between confidence and accuracy across all bins:
$$\text{MCE} = \max_{m \in \{1, \dots, M\}} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$

---

## 3. Decoupling Rules & Mathematical Penalties

The P3H.13 calibrator enforces two strict decoupling invariants:
1. **Format Validation Cannot Inflate Low OCR Evidence**: Validating against a regex cannot transform a garbled scan ($c_{\text{ocr}} = 0.30$) into a high-confidence record.
2. **Format Failure Imposes a Hard Ceiling**: If statutory validation fails (e.g. invalid Verhoeff checksum or malformed PAN syntax), calibrated confidence is strictly capped:
   $$C_{\text{field}} \le 0.45 \quad \text{when} \quad \phi = 0$$
   and human review is irrevocably triggered (`review_required = True`).

---

## 4. Empirical Evaluation Results

Evaluated across both the 48-sample P3H.12 baseline (453 fields) and the 48-sample P3H.13 independent holdout (432 fields across 6 unseen profiles):

| Calibration Metric | Raw Tesseract Engine | P3H.12 Calibrated Baseline | P3H.13 Enhanced (Baseline) | P3H.13 Enhanced (Holdout) | Overall Gain vs Raw |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Brier Score** | **0.3347** | 0.2847 | **0.1877** | **0.1888** | **$-43.6\%$** |
| **Expected Calibration Error (ECE)** | **0.2814** | 0.2210 | **0.1135** | **0.1100** | **$-60.9\%$** |
| **Maximum Calibration Error (MCE)** | **0.4920** | 0.3850 | **0.2252** | **0.3849** | **$-21.8\%$** |

### 10-Bin Reliability Table (P3H.13 Holdout Dataset: 432 Evaluated Fields)

| Bin Range | Sample Count ($|B_m|$) | Mean Confidence | Empirical Accuracy | Calibration Gap ($|\text{acc} - \text{conf}|$) | Operational Interpretation |
| :---: | :---: | :---: | :---: | :---: | :--- |
| $[0.0, 0.2)$ | 0 | — | — | — | Empty (Calibrator enforces 0.20 minimum floor) |
| $[0.2, 0.3)$ | 111 | 0.3000 | 0.0991 | 0.2009 | Degraded/blurred scans; 100% routed to manual review |
| $[0.3, 0.4)$ | 6 | 0.3129 | 0.1667 | 0.1462 | Sub-threshold extractions; routed to manual review |
| $[0.4, 0.5)$ | 17 | 0.4484 | 0.2353 | 0.2131 | Severe noise/shadow; routed to manual review |
| $[0.5, 0.6)$ | 19 | 0.5428 | 0.1579 | 0.3849 | Truncated/ambiguous fields; routed to manual review |
| $[0.6, 0.7)$ | 64 | 0.6453 | 0.4844 | 0.1610 | Moderate confidence border; flagged for review |
| $[0.7, 0.8)$ | 215 | 0.7633 | 0.7488 | **0.0145** | **High-validity structured fields; gap is only 1.45%** |
| $[0.8, 1.0]$ | 0 | — | — | — | Conservative calibration ceiling caps raw OCR at 0.77 |

### Statistical Reliability & Sample Size Limitations:
1. **Sample Clustering**: Because CONVELINA's calibrator caps raw OCR scores to $\le 0.77$ to prevent overconfidence and enforces a 0.20 floor for severely degraded inputs, predictions cluster in the $[0.2, 0.3)$ and $[0.7, 0.8)$ bins.
2. **Decisive Operational Discrimination**: The $[0.7, 0.8)$ bin contains 215 field extractions where mean confidence (0.7633) almost identically matches empirical ground-truth accuracy (0.7488), achieving an exceptional calibration gap of only **0.0145 (1.45%)**.
3. **Fail-Safe Lower Deciles**: Fields with confidence $< 0.70$ (217 total fields) are 100% intercepted by automated manual-review triggers, preventing any uncalibrated machine decision from reaching the citizen.

