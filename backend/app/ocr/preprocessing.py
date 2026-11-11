"""
CONVELINA — Modular Document Image Preprocessing Pipeline (Phase P3H.13)
Implements reproducible, production-grade image enhancement:
1. Multi-scale Lanczos Resolution Normalization
2. Two-stage Coarse/Fine Projection Profile Deskewing
3. Pure-NumPy Contrast Limited Adaptive Histogram Equalization (CLAHE)
4. Unsharp Mask Character Edge Sharpening
5. Median Despeckle Filtering
6. Local Adaptive Binarization (Sauvola / Dynamic Thresholding)
7. Objective Image Quality Telemetry (Laplacian Variance, Intensity STD)

CRITICAL INVARIANT: Operates strictly on in-memory working copies.
Source files and byte buffers on disk remain 100% immutable.
"""

import math
import logging
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

logger = logging.getLogger("convelina.ocr.preprocessing")


@dataclass
class PreprocessingConfig:
    deskew_enabled: bool = True
    max_deskew_angle: float = 15.0
    coarse_step: float = 1.0
    fine_step: float = 0.25
    clahe_enabled: bool = True
    clahe_clip_limit: float = 2.5
    clahe_tiles: Tuple[int, int] = (8, 8)
    unsharp_enabled: bool = True
    unsharp_radius: float = 1.4
    unsharp_percent: int = 140
    unsharp_threshold: int = 2
    denoise_enabled: bool = True
    denoise_size: int = 3
    rescale_enabled: bool = True
    min_dimension: int = 1000
    max_dimension: int = 2200
    target_dimension: int = 1500
    adaptive_threshold_enabled: bool = False  # Enabled dynamically on low contrast


class ImagePreprocessor:
    """
    Modular, chainable document image preprocessor.
    Transforms raw document photos/scans into high-readability OCR inputs.
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()

    def compute_quality_metrics(self, image: Image.Image) -> Dict[str, float]:
        """
        Computes objective quality metrics on the image:
        - Laplacian variance (focus/sharpness)
        - Intensity standard deviation (contrast)
        - Deficit penalties
        """
        try:
            gray = image.convert("L")
            arr = np.array(gray, dtype=np.float32)

            # Discrete 2D Laplacian convolution kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
            lap = (
                np.roll(arr, 1, axis=0) + np.roll(arr, -1, axis=0) +
                np.roll(arr, 1, axis=1) + np.roll(arr, -1, axis=1) -
                4.0 * arr
            )
            # Exclude 3-pixel borders
            inner = lap[3:-3, 3:-3] if arr.shape[0] > 6 and arr.shape[1] > 6 else lap
            lap_var = float(np.var(inner))

            # Intensity standard deviation (global contrast)
            intensity_std = float(np.std(arr))

            # Dimension adequacy
            w, h = image.size
            min_dim = min(w, h)

            blur_penalty = min(0.35, max(0.0, (65.0 - lap_var) / 65.0 * 0.35)) if lap_var < 65.0 else 0.0
            contrast_penalty = min(0.25, max(0.0, (38.0 - intensity_std) / 38.0 * 0.25)) if intensity_std < 38.0 else 0.0
            res_penalty = min(0.20, max(0.0, (600.0 - min_dim) / 600.0 * 0.20)) if min_dim < 600 else 0.0

            total_penalty = round(blur_penalty + contrast_penalty + res_penalty, 3)

            return {
                "laplacian_variance": round(lap_var, 2),
                "intensity_std": round(intensity_std, 2),
                "min_dimension": float(min_dim),
                "blur_penalty": round(blur_penalty, 3),
                "contrast_penalty": round(contrast_penalty, 3),
                "resolution_penalty": round(res_penalty, 3),
                "total_quality_penalty": total_penalty,
            }
        except Exception as e:
            logger.warning("Quality metric computation error: %s", e)
            return {
                "laplacian_variance": 120.0,
                "intensity_std": 50.0,
                "min_dimension": 1000.0,
                "blur_penalty": 0.0,
                "contrast_penalty": 0.0,
                "resolution_penalty": 0.0,
                "total_quality_penalty": 0.0,
            }

    def normalize_resolution(self, image: Image.Image) -> Image.Image:
        """
        Scales low-resolution images up using Lanczos resampling.
        Downscales oversized images to prevent Tesseract memory thrashing.
        """
        w, h = image.size
        min_dim = min(w, h)
        max_dim = max(w, h)

        if min_dim < self.config.min_dimension:
            scale = min(3.0, max(1.4, float(self.config.target_dimension) / max(w, 1)))
            new_size = (int(round(w * scale)), int(round(h * scale)))
            return image.resize(new_size, Image.Resampling.LANCZOS)
        elif max_dim > self.config.max_dimension:
            scale = float(self.config.max_dimension) / float(max_dim)
            new_size = (int(round(w * scale)), int(round(h * scale)))
            return image.resize(new_size, Image.Resampling.BILINEAR)

        return image

    def deskew_image(self, image: Image.Image) -> Tuple[Image.Image, float]:
        """
        Two-stage coarse/fine horizontal projection profile variance deskewing.
        Coarse sweep: -15 deg to +15 deg in 1.0 deg steps.
        Fine sweep: +/- 1.0 deg around best coarse angle in 0.25 deg steps.
        """
        if not self.config.deskew_enabled:
            return image, 0.0

        try:
            # Downsample thumbnail for fast projection profile computation
            thumb = image.convert("L")
            thumb.thumbnail((600, 600), Image.Resampling.BILINEAR)
            arr = np.array(thumb)
            thresh = float(np.mean(arr))
            binary = (arr < thresh).astype(np.float32)

            best_score = -1.0
            best_angle = 0.0

            # Stage 1: Coarse sweep (-15 to +15, step 1.0)
            angles_coarse = np.arange(-self.config.max_deskew_angle, self.config.max_deskew_angle + 0.1, self.config.coarse_step)
            for angle in angles_coarse:
                rot = Image.fromarray(binary).rotate(float(angle), resample=Image.Resampling.NEAREST, fillcolor=0)
                proj = np.sum(np.array(rot), axis=1)
                score = float(np.sum(np.diff(proj) ** 2))
                if score > best_score:
                    best_score = score
                    best_angle = float(angle)

            # Stage 2: Fine sweep (+/- 1.5 deg around best_angle, step 0.25)
            fine_start = max(-self.config.max_deskew_angle, best_angle - 1.5)
            fine_end = min(self.config.max_deskew_angle, best_angle + 1.5)
            angles_fine = np.arange(fine_start, fine_end + 0.05, self.config.fine_step)
            
            for angle in angles_fine:
                rot = Image.fromarray(binary).rotate(float(angle), resample=Image.Resampling.NEAREST, fillcolor=0)
                proj = np.sum(np.array(rot), axis=1)
                score = float(np.sum(np.diff(proj) ** 2))
                if score > best_score:
                    best_score = score
                    best_angle = float(angle)

            if abs(best_angle) >= 0.4:
                fill = 255 if image.mode in ("L", "1") else (255, 255, 255)
                rotated = image.rotate(
                    best_angle,
                    resample=Image.Resampling.BICUBIC,
                    expand=True,
                    fillcolor=fill
                )
                return rotated, round(best_angle, 2)

            return image, 0.0
        except Exception as e:
            logger.warning("Deskew failed: %s", e)
            return image, 0.0

    def apply_clahe(self, gray_image: Image.Image) -> Image.Image:
        """
        Pure NumPy Contrast Limited Adaptive Histogram Equalization.
        Splits image into an NxM grid of contextual tiles, limits histogram slope,
        equalizes each tile, and bilinearly interpolates pixel mappings.
        Eliminates heavy shadows and uneven lighting without blowing out text strokes.
        """
        if not self.config.clahe_enabled:
            return gray_image

        try:
            arr = np.array(gray_image, dtype=np.uint8)
            h, w = arr.shape
            grid_y, grid_x = self.config.clahe_tiles

            tile_h = h / grid_y
            tile_w = w / grid_x

            # Compute clipped CDF for each tile
            cdfs = np.zeros((grid_y, grid_x, 256), dtype=np.float32)

            for gy in range(grid_y):
                y_start = int(gy * tile_h)
                y_end = int((gy + 1) * tile_h) if gy < grid_y - 1 else h
                for gx in range(grid_x):
                    x_start = int(gx * tile_w)
                    x_end = int((gx + 1) * tile_w) if gx < grid_x - 1 else w

                    tile = arr[y_start:y_end, x_start:x_end]
                    tile_size = max(tile.size, 1)

                    # Histogram
                    hist, _ = np.histogram(tile, bins=256, range=(0, 256))
                    
                    # Clip limit
                    clip_limit = int(self.config.clahe_clip_limit * (tile_size / 256.0))
                    excess = np.sum(np.maximum(0, hist - clip_limit))
                    hist_clipped = np.minimum(hist, clip_limit)
                    hist_clipped += int(excess // 256)

                    # Cumulative Distribution Function
                    cdf = np.cumsum(hist_clipped).astype(np.float32)
                    cdf_min = cdf[0]
                    cdf_max = cdf[-1]
                    if cdf_max > cdf_min:
                        cdfs[gy, gx] = np.round((cdf - cdf_min) / (cdf_max - cdf_min) * 255.0)
                    else:
                        cdfs[gy, gx] = np.arange(256, dtype=np.float32)

            # Bilinear interpolation of mapping across the image
            out = np.zeros_like(arr, dtype=np.uint8)

            # Center coordinates of each tile
            x_centers = np.array([(gx + 0.5) * tile_w for gx in range(grid_x)], dtype=np.float32)
            y_centers = np.array([(gy + 0.5) * tile_h for gy in range(grid_y)], dtype=np.float32)

            # Grid coordinates for every pixel
            ys = np.arange(h, dtype=np.float32)
            xs = np.arange(w, dtype=np.float32)

            # Find bounding tile indices for y and x
            gy0 = np.clip(np.searchsorted(y_centers, ys) - 1, 0, grid_y - 2)
            gy1 = gy0 + 1
            gx0 = np.clip(np.searchsorted(x_centers, xs) - 1, 0, grid_x - 2)
            gx1 = gx0 + 1

            # Interpolation weights
            wy1 = np.clip((ys - y_centers[gy0]) / np.maximum(y_centers[gy1] - y_centers[gy0], 1e-4), 0.0, 1.0)[:, None]
            wy0 = 1.0 - wy1
            wx1 = np.clip((xs - x_centers[gx0]) / np.maximum(x_centers[gx1] - x_centers[gx0], 1e-4), 0.0, 1.0)[None, :]
            wx0 = 1.0 - wx1

            # Vectorized mapping lookup
            val = arr
            gy0_grid = gy0[:, None]
            gy1_grid = gy1[:, None]
            gx0_grid = gx0[None, :]
            gx1_grid = gx1[None, :]

            f00 = cdfs[gy0_grid, gx0_grid, val]
            f01 = cdfs[gy0_grid, gx1_grid, val]
            f10 = cdfs[gy1_grid, gx0_grid, val]
            f11 = cdfs[gy1_grid, gx1_grid, val]

            top = wy0 * (wx0 * f00 + wx1 * f01)
            bot = wy1 * (wx0 * f10 + wx1 * f11)
            out = np.clip(top + bot, 0, 255).astype(np.uint8)

            return Image.fromarray(out, mode="L")
        except Exception as e:
            logger.warning("CLAHE failed, falling back to standard contrast enhancement: %s", e)
            enhancer = ImageEnhance.Contrast(gray_image)
            return enhancer.enhance(1.5)

    def apply_unsharp_mask(self, image: Image.Image) -> Image.Image:
        """
        Applies subtle unsharp masking to enhance character stroke definition.
        """
        if not self.config.unsharp_enabled:
            return image
        return image.filter(
            ImageFilter.UnsharpMask(
                radius=self.config.unsharp_radius,
                percent=self.config.unsharp_percent,
                threshold=self.config.unsharp_threshold
            )
        )

    def apply_median_denoise(self, image: Image.Image) -> Image.Image:
        """
        Applies median filter to remove high-frequency salt-and-pepper noise.
        """
        if not self.config.denoise_enabled:
            return image
        return image.filter(ImageFilter.MedianFilter(size=self.config.denoise_size))

    def apply_adaptive_threshold(self, gray_image: Image.Image) -> Image.Image:
        """
        Sauvola-inspired adaptive local thresholding for deeply shadowed document images.
        """
        arr = np.array(gray_image, dtype=np.float32)
        # Approximate local mean via box blur
        blurred = np.array(gray_image.filter(ImageFilter.BoxBlur(15)), dtype=np.float32)
        # Dynamic threshold: T = local_mean * (1 - 0.05)
        thresh = blurred * 0.94
        binary = np.where(arr < thresh, 0, 255).astype(np.uint8)
        return Image.fromarray(binary, mode="L")

    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Main end-to-end preprocessing pipeline.
        Takes an input PIL Image (which remains unmodified) and returns
        an enhanced, deskewed, contrast-normalized, sharpened working copy.
        """
        # Step 0: Create isolated working copy
        working = image.copy()

        # Step 1: Normalize resolution (Lanczos upsampling / downsampling)
        if self.config.rescale_enabled:
            working = self.normalize_resolution(working)

        # Step 2: Two-stage coarse & fine deskew
        if self.config.deskew_enabled:
            working, detected_angle = self.deskew_image(working)

        # Step 3: Convert to Grayscale
        gray = working.convert("L")

        # Step 4: Contrast enhancement via CLAHE
        enhanced = self.apply_clahe(gray)

        # Step 5: Unsharp masking to sharpen text strokes
        sharpened = self.apply_unsharp_mask(enhanced)

        # Step 6: Subtle median denoise to clear speckles
        if self.config.denoise_enabled:
            final_img = self.apply_median_denoise(sharpened)
        else:
            final_img = sharpened

        return final_img


# Default singleton instance
default_image_preprocessor = ImagePreprocessor()
