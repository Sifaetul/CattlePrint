"""
Muzzle Ridge & Groove Contrast Enhancement using CLAHE.
(Contrast Limited Adaptive Histogram Equalization on CIELAB L-channel)
"""

import cv2
import numpy as np


class CLAHEEnhancer:
    def __init__(self, clip_limit: float = 2.5, tile_grid_size: tuple = (8, 8)):
        """
        Args:
            clip_limit: Threshold for contrast limiting. Higher values increase contrast.
            tile_grid_size: Size of grid for histogram equalization.
        """
        self.clahe = cv2.createCLAHE(
            clipLimit=clip_limit, tileGridSize=tile_grid_size
        )

    def enhance(self, image_bgr: np.ndarray) -> np.ndarray:
        """
        Enhances muzzle grooves and ridges by applying CLAHE to the L (luminance) channel
        in the CIELAB color space, preserving natural chrominance.
        """
        if image_bgr is None or image_bgr.size == 0:
            return image_bgr

        # Convert BGR to LAB color space
        lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Apply CLAHE to luminance
        enhanced_l = self.clahe.apply(l_channel)

        # Merge back and convert to BGR
        enhanced_lab = cv2.merge((enhanced_l, a_channel, b_channel))
        enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        return enhanced_bgr

    def enhance_grayscale(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Applies CLAHE directly to a 2D grayscale array.
        """
        if gray_image is None or gray_image.size == 0:
            return gray_image
        return self.clahe.apply(gray_image)
