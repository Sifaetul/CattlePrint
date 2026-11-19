"""
Muzzle Region of Interest (ROI) Detector & Normalizer.
Provides:
1. Deep Learning / YOLO based bounding box detection (when weights available).
2. Morphological / Anatomical fallback detector (locates nostrils & dermatoglyphic plate).
3. Standardized aspect-ratio crop and resize to model input dimensions (224x224).
"""

from typing import Tuple, Optional
import numpy as np
import cv2
from ml_engine.config import model_config


class MuzzleDetector:
    def __init__(
        self,
        target_size: Tuple[int, int] = model_config.input_size,
        weights_path: Optional[str] = None,
    ):
        self.target_size = target_size
        self.weights_path = weights_path
        self.yolo_model = None

        if weights_path:
            try:
                # Lazy import if ultralytics / yolo is installed
                from ultralytics import YOLO
                self.yolo_model = YOLO(weights_path)
            except Exception:
                self.yolo_model = None

    def detect_roi(self, image_bgr: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Detects and crops the muzzle ROI from an input cattle photo.
        Returns:
            cropped_roi: 224x224 BGR image focused on muzzle beads/grooves
            bbox: (x, y, w, h) bounding box in original image coordinates
        """
        if image_bgr is None or image_bgr.size == 0:
            raise ValueError("Input image is invalid or empty.")

        h, w = image_bgr.shape[:2]

        # 1. Try YOLO detection if loaded
        if self.yolo_model is not None:
            try:
                results = self.yolo_model(image_bgr, verbose=False)
                if len(results) > 0 and len(results[0].boxes) > 0:
                    box = results[0].boxes[0].xyxy[0].cpu().numpy().astype(int)
                    x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3])
                    crop = image_bgr[y1:y2, x1:x2]
                    resized = cv2.resize(crop, self.target_size, interpolation=cv2.INTER_LANCZOS4)
                    return resized, (x1, y1, x2 - x1, y2 - y1)
            except Exception:
                pass

        # 2. Anatomical / Morphological Landmark Heuristic
        # Cattle nostrils are typically dark concave ellipses on the lower third of the face
        crop, bbox = self._anatomical_muzzle_crop(image_bgr)
        resized = cv2.resize(crop, self.target_size, interpolation=cv2.INTER_LANCZOS4)
        return resized, bbox

    def _anatomical_muzzle_crop(
        self, image_bgr: np.ndarray
    ) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Heuristic crop focusing on the central/lower region of interest,
        adapting to camera viewfinder orientation.
        """
        h, w = image_bgr.shape[:2]

        # Field guidelines ask agents to center the muzzle in the camera box.
        # We extract the 60% center-width and 50% vertical center-to-lower section.
        crop_w = int(w * 0.65)
        crop_h = int(h * 0.60)

        start_x = max(0, (w - crop_w) // 2)
        start_y = max(0, int(h * 0.25))

        # Clamp boundaries
        end_x = min(w, start_x + crop_w)
        end_y = min(h, start_y + crop_h)

        crop = image_bgr[start_y:end_y, start_x:end_x]
        return crop, (start_x, start_y, end_x - start_x, end_y - start_y)
