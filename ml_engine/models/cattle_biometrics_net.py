"""
Unified Cattle Biometrics Neural Network.
Combines Backbone + ArcMarginProduct Head for training,
and provides fast inference + ONNX export utility.
"""

from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
from ml_engine.config import model_config
from ml_engine.models.backbone import MuzzleFeatureBackbone
from ml_engine.models.arcface import ArcMarginProduct


class CattleBiometricsNet(nn.Module):
    def __init__(
        self,
        num_classes: int = 100,
        backbone_name: str = model_config.backbone_name,
        embedding_dim: int = model_config.embedding_dim,
        pretrained_backbone: bool = True,
    ):
        super(CattleBiometricsNet, self).__init__()
        self.num_classes = num_classes
        self.embedding_dim = embedding_dim
        self.backbone = MuzzleFeatureBackbone(
            backbone_name=backbone_name,
            embedding_dim=embedding_dim,
            pretrained=pretrained_backbone,
        )
        self.arcface_head = ArcMarginProduct(
            in_features=embedding_dim,
            out_features=num_classes,
            s=model_config.arcface_s,
            m=model_config.arcface_m,
        )

    def forward(
        self, x: torch.Tensor, labels: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        If labels is provided: returns ArcFace classification logits for cross-entropy training.
        If labels is None: returns normalized 512-dim embedding for biometric inference.
        """
        embeddings = self.backbone(x)
        if labels is not None:
            logits = self.arcface_head(embeddings, labels)
            return logits
        return embeddings

    def extract_embedding(self, x: torch.Tensor) -> np.ndarray:
        """
        Extracts L2-normalized numpy embedding for similarity matching.
        """
        self.eval()
        with torch.no_grad():
            emb = self.backbone(x)
            return emb.cpu().numpy()

    def export_onnx(
        self,
        output_path: Path,
        input_size: Tuple[int, int] = model_config.input_size,
    ) -> Path:
        """
        Exports only the backbone feature extractor to ONNX for ultra-low latency inference.
        """
        self.eval()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        dummy_input = torch.randn(1, 3, input_size[0], input_size[1], dtype=torch.float32)
        torch.onnx.export(
            self.backbone,
            dummy_input,
            str(output_path),
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=["input_image"],
            output_names=["embedding_512"],
            dynamic_axes={"input_image": {0: "batch_size"}, "embedding_512": {0: "batch_size"}},
        )
        return output_path
