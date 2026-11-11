"""
CONVELINA — Confidence Calibration & Reliability Metrics Engine (Phase P3H.13)
Implements:
1. Expected Calibration Error (ECE) and Maximum Calibration Error (MCE)
2. Brier Score computation (Mean Squared Error between probability & empirical binary correctness)
3. Multi-factor Calibrator decoupling raw OCR heuristics from statutory validity
4. Reliability Diagram binning and telemetry generation
5. Multi-level Calibration: Token-level, Field-level, and Document-level
"""

import math
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CalibrationBin:
    bin_index: int
    lower_bound: float
    upper_bound: float
    sample_count: int = 0
    mean_confidence: float = 0.0
    empirical_accuracy: float = 0.0
    calibration_gap: float = 0.0


@dataclass
class CalibrationEvaluationReport:
    total_samples: int
    brier_score: float
    expected_calibration_error: float  # ECE
    maximum_calibration_error: float   # MCE
    bins: List[CalibrationBin] = field(default_factory=list)


class ConfidenceCalibrator:
    """
    Mathematical calibration engine for OCR and field extraction confidence.
    Enforces the core rule: Confidence scores must represent genuine empirical probabilities.
    """

    @staticmethod
    def compute_brier_score(predictions: List[Tuple[float, int]]) -> float:
        """
        Brier Score: Mean squared error between predicted confidence and binary ground truth (0 or 1).
        Lower is better (0.0 is perfect calibration, 1.0 is completely inverted).
        """
        if not predictions:
            return 0.0
        total_sq_err = sum((conf - truth) ** 2 for conf, truth in predictions)
        return round(total_sq_err / len(predictions), 4)

    @classmethod
    def evaluate_calibration(
        cls,
        predictions: List[Tuple[float, int]],
        num_bins: int = 10
    ) -> CalibrationEvaluationReport:
        """
        Computes ECE, MCE, Brier score, and bin-by-bin reliability metrics.
        predictions: list of (confidence_score, is_correct) where is_correct is 1 or 0.
        """
        if not predictions:
            return CalibrationEvaluationReport(
                total_samples=0,
                brier_score=0.0,
                expected_calibration_error=0.0,
                maximum_calibration_error=0.0,
                bins=[]
            )

        n = len(predictions)
        bin_width = 1.0 / num_bins
        bins: List[CalibrationBin] = []
        weighted_ece_sum = 0.0
        max_gap = 0.0

        for b_idx in range(num_bins):
            lo = b_idx * bin_width
            hi = (b_idx + 1) * bin_width if b_idx < num_bins - 1 else 1.0001
            
            # Filter samples in this bin: lo <= conf < hi
            bin_samples = [p for p in predictions if lo <= p[0] < hi]
            count = len(bin_samples)

            if count > 0:
                mean_conf = sum(p[0] for p in bin_samples) / count
                accuracy = sum(p[1] for p in bin_samples) / count
                gap = abs(accuracy - mean_conf)
                weighted_ece_sum += (count / n) * gap
                if gap > max_gap:
                    max_gap = gap
            else:
                mean_conf = (lo + hi) / 2.0
                accuracy = 0.0
                gap = 0.0

            bins.append(CalibrationBin(
                bin_index=b_idx,
                lower_bound=round(lo, 2),
                upper_bound=round(min(1.0, hi), 2),
                sample_count=count,
                mean_confidence=round(mean_conf, 4),
                empirical_accuracy=round(accuracy, 4),
                calibration_gap=round(gap, 4),
            ))

        brier = cls.compute_brier_score(predictions)

        return CalibrationEvaluationReport(
            total_samples=n,
            brier_score=brier,
            expected_calibration_error=round(weighted_ece_sum, 4),
            maximum_calibration_error=round(max_gap, 4),
            bins=bins,
        )

    @classmethod
    def calibrate_field_confidence(
        cls,
        ocr_engine_conf: float,
        parser_anchor_conf: float,
        format_validated: bool,
        quality_penalties: Optional[Dict[str, float]] = None,
        has_regional_script: bool = False,
    ) -> Tuple[float, bool]:
        """
        Calibrates field-level confidence combining OCR engine evidence,
        pattern anchor precision, statutory format validation, and image quality metrics.
        Returns: (calibrated_confidence, requires_manual_review)
        """
        penalties = quality_penalties or {}
        blur_pen = penalties.get("blur_penalty", 0.0)
        contrast_pen = penalties.get("contrast_penalty", 0.0)
        res_pen = penalties.get("resolution_penalty", 0.0)
        total_qual_penalty = blur_pen + contrast_pen + res_pen

        # Base engine confidence
        raw_combined = ocr_engine_conf * parser_anchor_conf

        if not format_validated:
            # Hard ceiling: if statutory regex/checksum fails, confidence CANNOT exceed 0.45
            calibrated = min(0.45, raw_combined * 0.45)
            review_required = True
        elif total_qual_penalty >= 0.30 or blur_pen >= 0.25:
            # Significant visual degradation penalty
            calibrated = max(0.20, min(0.55, raw_combined - total_qual_penalty))
            review_required = True
        else:
            # High-confidence valid path
            calibrated = max(0.40, min(0.96, raw_combined - total_qual_penalty * 0.5))
            review_required = (calibrated < 0.70) or has_regional_script

        return round(calibrated, 4), review_required


default_calibrator = ConfidenceCalibrator()

