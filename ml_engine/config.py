"""
CattlePrint ML Engine Configuration
Defines hyperparameters, dimensions, thresholds, and quality gate boundaries.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class QualityGateConfig:
    min_laplacian_variance: float = 85.0  # Threshold for motion blur detection
    min_brightness: float = 35.0          # Below this is underexposed / dark barn
    max_brightness: float = 230.0         # Above this is specular reflection / flash glare
    min_resolution: tuple = (200, 200)    # Minimum acceptable input resolution


@dataclass
class ModelConfig:
    input_size: tuple = (224, 224)        # Standard input tensor (3, 224, 224)
    embedding_dim: int = 512              # 512-dimensional L2-normalized vector
    backbone_name: str = "resnet50"       # Options: resnet50, efficientnet_b0, mobile_convnet
    arcface_s: float = 64.0               # ArcFace radius scale
    arcface_m: float = 0.50               # ArcFace angular margin
    default_similarity_threshold: float = 0.72  # Cosine similarity matching threshold


@dataclass
class PathConfig:
    root_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = root_dir / "data"
    raw_images_dir: Path = data_dir / "raw"
    cropped_muzzle_dir: Path = data_dir / "cropped"
    weights_dir: Path = root_dir / "ml_engine" / "weights"
    exports_dir: Path = root_dir / "ml_engine" / "exports"


quality_config = QualityGateConfig()
model_config = ModelConfig()
path_config = PathConfig()
