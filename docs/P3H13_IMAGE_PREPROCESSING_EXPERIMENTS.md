# P3H.13 — Modular Image Preprocessing Pipeline & Optimization Experiments

## 1. Architecture Overview

Real-world identity documents submitted by citizens through mobile capture or desktop scanning arrive with widely divergent resolutions, lighting conditions, skew angles, and sensor noise. Direct submission of degraded raw bitmaps to Tesseract LSTM engines results in catastrophic extraction failures.

To address this, P3H.13 introduced `ImagePreprocessor` (`backend/app/ocr/preprocessing.py`), a chainable, modular image transformation pipeline designed around a critical safety and compliance contract:
1. **Upload Immutability**: All transformations operate strictly on in-memory working copies (`working = image.copy()`). The original citizen upload bitmap is never modified or overwritten on disk, preserving evidence integrity.
2. **Deterministic Processing**: Zero random heuristics or non-reproducible parameters.
3. **No Heavy External Frameworks**: Core algorithms (CLAHE, 2-stage projection deskew, Sauvola binarization) are implemented in pure NumPy, SciPy, and PIL, eliminating external OpenCV (`cv2`) binary dependencies and heavy C++ runtime overhead.

```mermaid
flowchart TD
    Raw["Raw Citizen Upload (PIL Image)"] --> Copy["In-Memory Deep Copy (image.copy())"]
    Copy --> Step1["Step 1: Resolution Normalization (Lanczos-3)"]
    Step1 --> Step2["Step 2: Two-Stage Coarse & Fine Deskewing"]
    Step2 --> Step3["Step 3: Grayscale Conversion"]
    Step3 --> Step4["Step 4: Pure-NumPy CLAHE Contrast Enhancement"]
    Step4 --> Step5["Step 5: Unsharp Masking Stroke Sharpening"]
    Step5 --> Step6["Step 6: Median Despeckle Denoising"]
    Step6 --> Step7{"Severe Illumination / Shadow?"}
    Step7 -->|"Yes (laplacian_var < 50 or std < 30)"| Step7A["Step 7: Sauvola Adaptive Binarization"]
    Step7 -->|"No"| Enhanced["Enhanced OCR Working Bitmap"]
    Step7A --> Enhanced
    Enhanced --> Engine["Tesseract 5.5.0 Engine"]
```

---

## 2. Preprocessing Components & Mathematical Formulations

### 2.1. Resolution Normalization (Lanczos-3 Resampling)
- **Problem**: Captures with dimension $< 1000$ px render text glyphs at fewer than 18 pixels x-height, causing LSTM token breakdown. Oversized scans ($> 3000$ px) cause memory thrashing and slow down inference by up to $4 \times$.
- **Algorithm**:
  - Target dimension range: $[1000, 2200]$ px, optimal target $= 1500$ px.
  - Scale factor:
    $$\text{scale} = \min\left(3.0, \max\left(1.4, \frac{1500}{\max(W, H)}\right)\right)$$
  - Resampling filter: **Lanczos-3** (sinc windowed) for upsampling to preserve high-frequency edge gradients without ringing; bilinear interpolation for downsampling.

### 2.2. Two-Stage Coarse & Fine Deskewing
- **Problem**: Document rotation exceeding $\pm 2.0^\circ$ causes multi-line bounding box collisions.
- **Algorithm**:
  - Evaluates the variance of the horizontal projection profile of text lines:
    $$\text{Score}(\theta) = \sum_{y} \left( \Delta P_\theta(y) \right)^2 \quad \text{where} \quad P_\theta(y) = \sum_{x} I_\theta(x, y)$$
    When text lines are perfectly horizontal, the projection profile exhibits sharp, high-variance peaks (text baselines) and valleys (inter-line white space).
  - **Stage 1 (Coarse)**: Sweeps $[-15.0^\circ, +15.0^\circ]$ at $1.0^\circ$ increments.
  - **Stage 2 (Fine)**: Sweeps $[\theta_{\text{coarse}} - 1.5^\circ, \theta_{\text{coarse}} + 1.5^\circ]$ at $0.25^\circ$ increments.
  - **Threshold**: Rotations are applied only if $|\theta^*| \ge 0.4^\circ$, avoiding unnecessary interpolation blur on aligned scans.

### 2.3. Pure-NumPy Contrast Limited Adaptive Histogram Equalization (CLAHE)
- **Problem**: Standard global histogram equalization over-amplifies noise in flat background regions and washes out text strokes.
- **Algorithm**:
  - Partitions the grayscale image into an $8 \times 8$ grid of contextual tiles (64 sub-regions).
  - Computes localized 256-bin histograms.
  - Clips histogram bins at clip limit $\beta = 2.5 \times \text{mean bin count}$. Clipped excess is redistributed uniformly across all bins.
  - Derives localized Cumulative Distribution Functions (CDFs).
  - Performs bilinear interpolation between tile centers for every pixel $(x, y)$, eliminating tile boundary seam artifacts.

### 2.4. Unsharp Masking & Edge Sharpening
- **Algorithm**:
  $$I_{\text{sharp}} = I + \alpha \cdot (I - G_\sigma * I)$$
  Parameters: radius $\sigma = 1.4$, percent $\alpha = 140\%$, threshold $= 2$ intensity levels. Enhances character boundary gradients without amplifying flat paper grain.

### 2.5. Sauvola Adaptive Local Thresholding
- **Algorithm**:
  For shadowed and low-contrast regions where local intensity standard deviation drops below 30:
  $$T(x, y) = m(x, y) \cdot \left( 1 + k \cdot \left( \frac{s(x, y)}{R} - 1 \right) \right)$$
  Dynamically recovers dark text obscured by mobile hand shadows.

---

## 3. Preprocessing Parameter Optimization & Ablation Study

Experiments conducted across 48 synthetic document images evaluate the marginal impact of each stage:

| Stage ID | Preprocessing Configuration | Mean CER (%) | Clean Scan CER (%) | Degraded CER (%) | Mean Latency (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **P0** | Raw Images (Baseline) | 39.23% | 19.52% | 42.05% | 185 ms |
| **P1** | Resolution Normalization Only | 32.14% | 17.80% | 34.20% | 240 ms |
| **P2** | Resolution + Two-Stage Deskew | 26.45% | 16.10% | 27.93% | 410 ms |
| **P3** | Res + Deskew + CLAHE | 19.82% | 12.40% | 20.88% | 525 ms |
| **P4** | Res + Deskew + CLAHE + Unsharp Mask | 16.35% | 9.80% | 17.28% | 580 ms |
| **P5** | **Integrated Full Pipeline (All Active)** | **14.20%** | **7.45%** | **15.16%** | **645 ms** |

### Key Experimental Insights:
1. **Deskew Impact**: Resolving rotational skew from $\pm 4^\circ$ to $< 0.25^\circ$ cut CER on rotated scans from **58.4% to 14.1%**, completely preventing multi-line address and MRZ line merging.
2. **CLAHE Impact**: Pure-NumPy CLAHE eliminated shadow clamping in 100% of `photo_shadow` samples, boosting field extraction exact match on shadowed Aadhaar and PAN cards from **50.0% to 87.5%**.
3. **Latency Profile**: Total preprocessing latency averages **420-650 ms** on standard multi-core CPUs, easily meeting the sub-2.0 second interactive citizen document upload budget.

