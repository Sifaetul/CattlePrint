"""
Unit & Integration Tests for CattlePrint ML Engine.
Verifies Quality Gate, CLAHE, Detector, ArcFace Embedding, and Metrics.
"""

import numpy as np
import torch
import pytest
from ml_engine.vision.quality_gate import MuzzleQualityGate
from ml_engine.vision.clahe_enhancer import CLAHEEnhancer
from ml_engine.vision.detector import MuzzleDetector
from ml_engine.models.cattle_biometrics_net import CattleBiometricsNet
from ml_engine.evaluation.metrics import BiometricEvaluator
from ml_engine.datasets.downloader import generate_synthetic_muzzle_sample


def test_quality_gate_clean_vs_blurry():
    gate = MuzzleQualityGate()

    # Generate a sharp synthetic muzzle
    sharp_img = generate_synthetic_muzzle_sample(cattle_id=1, session=0, size=(250, 250))
    res_sharp = gate.assess_image(sharp_img)
    assert res_sharp.is_valid is True
    assert res_sharp.blur_score > gate.min_blur_score

    # Simulate heavy motion blur with severe Gaussian blur
    import cv2
    blurred_img = cv2.GaussianBlur(sharp_img, (35, 35), 0)
    res_blur = gate.assess_image(blurred_img)
    assert res_blur.is_valid is False
    assert "MOTION_BLUR" in res_blur.reasons


def test_quality_gate_dark_exposure():
    gate = MuzzleQualityGate()
    dark_img = np.zeros((250, 250, 3), dtype=np.uint8)  # pitch black
    res = gate.assess_image(dark_img)
    assert res.is_valid is False
    assert "UNDEREXPOSED_DARK" in res.reasons


def test_clahe_enhancer():
    enhancer = CLAHEEnhancer(clip_limit=2.0)
    img = generate_synthetic_muzzle_sample(cattle_id=2, session=0)
    enhanced = enhancer.enhance(img)
    assert enhanced.shape == img.shape
    assert enhanced.dtype == np.uint8


def test_muzzle_detector_crop_and_resize():
    detector = MuzzleDetector(target_size=(224, 224))
    raw_img = generate_synthetic_muzzle_sample(cattle_id=3, session=0, size=(400, 400))
    roi, bbox = detector.detect_roi(raw_img)
    assert roi.shape == (224, 224, 3)
    assert bbox[2] > 0 and bbox[3] > 0


def test_arcface_and_embedding_normalization():
    model = CattleBiometricsNet(
        num_classes=5,
        backbone_name="mobile_convnet",
        embedding_dim=512,
        pretrained_backbone=False,
    )
    model.eval()

    # Input batch of 2 synthetic muzzle crops
    dummy_input = torch.randn(2, 3, 224, 224)
    with torch.no_grad():
        embeddings = model(dummy_input)

    assert embeddings.shape == (2, 512)
    # Norm of L2-normalized vectors must be 1.0 (within float tolerance)
    norms = torch.norm(embeddings, p=2, dim=1).numpy()
    np.testing.assert_allclose(norms, [1.0, 1.0], rtol=1e-4)


def test_biometric_evaluator_metrics():
    # Synthetic genuine scores (high similarity, mean ~ 0.85)
    genuine = np.random.normal(0.85, 0.05, 50)
    # Synthetic impostor scores (low similarity, mean ~ 0.35)
    impostor = np.random.normal(0.35, 0.08, 100)

    results = BiometricEvaluator.calculate_far_frr_eer(genuine, impostor)
    assert "eer" in results
    assert "optimal_threshold" in results
    assert "precision" in results
    assert "recall" in results
    assert "f1_score" in results
    assert "identification_accuracy" in results
    assert results["roc_auc"] > 0.90  # Well-separated distributions
