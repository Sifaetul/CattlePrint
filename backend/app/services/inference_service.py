"""
AI Biometric Inference Service.
Integrates Quality Gate, ROI Detector, CLAHE Enhancer, and Deep Metric ArcFace Net.
"""

from typing import Tuple, List, Optional
import cv2
import numpy as np
import torch
from torchvision import transforms
from PIL import Image

from ml_engine.config import model_config
from ml_engine.vision.quality_gate import MuzzleQualityGate, QualityAssessmentResult
from ml_engine.vision.detector import MuzzleDetector
from ml_engine.vision.clahe_enhancer import CLAHEEnhancer
from ml_engine.models.cattle_biometrics_net import CattleBiometricsNet
from backend.app.core.config import settings


class BiometricInferenceService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BiometricInferenceService, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        """Initializes computer vision pipelines and deep learning network."""
        self.quality_gate = MuzzleQualityGate()
        self.detector = MuzzleDetector(target_size=model_config.input_size)
        self.clahe = CLAHEEnhancer(clip_limit=2.5)

        self.device = "cuda" if torch.cuda.is_available() and settings.USE_GPU else "cpu"

        # Initialize network
        self.net = CattleBiometricsNet(
            num_classes=100,
            backbone_name="mobile_convnet",
            embedding_dim=model_config.embedding_dim,
            pretrained_backbone=False,
        ).to(self.device)

        # Load trained weights if checkpoint exists
        from ml_engine.config import path_config
        weights_file = path_config.weights_dir / "cattleprint_arcface_best.pt"
        if weights_file.exists():
            try:
                state_dict = torch.load(weights_file, map_location=self.device)
                self.net.load_state_dict(state_dict, strict=False)
            except Exception:
                pass

        self.net.eval()

        # Image preprocessing transform
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def assess_quality(self, image_bgr: np.ndarray) -> QualityAssessmentResult:
        """Evaluates image sharpness and exposure."""
        return self.quality_gate.assess_image(image_bgr)

    def process_and_extract_embedding(
        self, image_bytes: bytes, strict_quality: bool = False
    ) -> Tuple[QualityAssessmentResult, Optional[np.ndarray], Optional[List[float]]]:
        """
        Full End-to-End Processing:
        1. Decode image bytes.
        2. Assess Quality (Blur / Glare / Illumination).
        3. Detect and Crop Muzzle ROI.
        4. Enhance Ridge/Groove Contrast with CLAHE.
        5. Extract 512-dim Unit-Normalized Embedding.
        """
        # Decode byte buffer to BGR array
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image_bgr is None:
            empty_res = QualityAssessmentResult(
                is_valid=False,
                blur_score=0.0,
                brightness_score=0.0,
                contrast_score=0.0,
                reasons=["CORRUPT_OR_UNREADABLE_IMAGE"],
                message="Could not decode image bytes.",
            )
            return empty_res, None, None

        # 1. Quality Assessment
        quality_res = self.assess_quality(image_bgr)
        if strict_quality and not quality_res.is_valid:
            return quality_res, None, None

        # 2. Muzzle Detection & Crop
        cropped_roi, _ = self.detector.detect_roi(image_bgr)

        # 3. CLAHE Texture Enhancement
        enhanced_crop = self.clahe.enhance(cropped_roi)

        # 4. Neural Network Embedding Extraction
        # Convert BGR to RGB for PyTorch model
        rgb_crop = cv2.cvtColor(enhanced_crop, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_crop)
        tensor_img = self.transform(pil_img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            emb_tensor = self.net(tensor_img)
            # Embedding is already L2-normalized: ||v|| = 1.0
            vector = emb_tensor.cpu().numpy()[0].tolist()

        return quality_res, cropped_roi, vector


inference_service = BiometricInferenceService()
