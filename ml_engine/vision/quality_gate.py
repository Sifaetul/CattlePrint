"""
Quality Gate Module for Cattle Muzzle Biometrics.
Evaluates input imagery for motion blur, severe shadows, and specular glare
before passing to deep learning feature extractors.
"""

from dataclasses import dataclass
from typing import Tuple, Dict, Any
import numpy as np
import cv2
from ml_engine.config import quality_config


@dataclass
class QualityAssessmentResult:
    is_valid: bool
    blur_score: float
    brightness_score: float
    contrast_score: float
    reasons: list
    message: str


class MuzzleQualityGate:
    def __init__(
        self,
        min_blur_score: float = quality_config.min_laplacian_variance,
        min_brightness: float = quality_config.min_brightness,
        max_brightness: float = quality_config.max_brightness,
        min_resolution: Tuple[int, int] = quality_config.min_resolution,
    ):
        self.min_blur_score = min_blur_score
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.min_resolution = min_resolution

    def compute_blur_score(self, gray_image: np.ndarray) -> float:
        """
        Computes the variance of the Laplacian.
        Higher values indicate sharp edges (clear grooves and beads).
        Lower values indicate motion blur or out-of-focus capture.
        """
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        variance = laplacian.var()
        return float(variance)

    def compute_illumination_and_contrast(
        self, gray_image: np.ndarray
    ) -> Tuple[float, float]:
        """
        Calculates mean brightness (0-255) and RMS contrast (standard deviation).
        """
        mean_brightness = float(np.mean(gray_image))
        contrast = float(np.std(gray_image))
        return mean_brightness, contrast

    def assess_image(self, image_bgr: np.ndarray) -> QualityAssessmentResult:
        """
        Performs full quality assessment on an input BGR image.
        Returns a structured QualityAssessmentResult.
        """
        if image_bgr is None or image_bgr.size == 0:
            return QualityAssessmentResult(
                is_valid=False,
                blur_score=0.0,
                brightness_score=0.0,
                contrast_score=0.0,
                reasons=["EMPTY_IMAGE"],
                message="Image is empty or unreadable.",
            )

        h, w = image_bgr.shape[:2]
        reasons = []

        # Resolution check
        if h < self.min_resolution[0] or w < self.min_resolution[1]:
            reasons.append("LOW_RESOLUTION")

        # Convert to grayscale for biometric texture analysis
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Blur Detection
        blur_score = self.compute_blur_score(gray)
        if blur_score < self.min_blur_score:
            reasons.append("MOTION_BLUR")

        # 2. Illumination and Glare
        brightness_score, contrast_score = self.compute_illumination_and_contrast(gray)

        if brightness_score < self.min_brightness:
            reasons.append("UNDEREXPOSED_DARK")
        elif brightness_score > self.max_brightness:
            reasons.append("OVEREXPOSED_GLARE")

        # 3. Low contrast check (e.g. fog, extreme mud wash)
        if contrast_score < 20.0:
            reasons.append("LOW_CONTRAST")

        is_valid = len(reasons) == 0

        # Human-friendly feedback message in English & Bengali context
        if is_valid:
            message = "Quality Check Passed: Muzzle features are clear."
        else:
            feedback_map = {
                "LOW_RESOLUTION": "Resolution too low. Please move closer to the cattle muzzle.",
                "MOTION_BLUR": "Image is blurry. Please hold camera steady while cattle is calm.",
                "UNDEREXPOSED_DARK": "Too dark. Ensure adequate lighting in the farm/shed.",
                "OVEREXPOSED_GLARE": "Severe glare or reflection. Avoid direct flash on wet muzzle.",
                "LOW_CONTRAST": "Low contrast. Clean any heavy mud and re-focus.",
            }
            message = " | ".join([feedback_map.get(r, r) for r in reasons])

        return QualityAssessmentResult(
            is_valid=is_valid,
            blur_score=round(blur_score, 2),
            brightness_score=round(brightness_score, 2),
            contrast_score=round(contrast_score, 2),
            reasons=reasons,
            message=message,
        )
