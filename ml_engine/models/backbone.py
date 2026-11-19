"""
Feature Extractor Backbone for Cattle Muzzle Biometrics.
Maps preprocessed 224x224 muzzle images into a 512-dimensional hyperspherical embedding.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models
from ml_engine.config import model_config


class MuzzleFeatureBackbone(nn.Module):
    def __init__(
        self,
        backbone_name: str = model_config.backbone_name,
        embedding_dim: int = model_config.embedding_dim,
        pretrained: bool = True,
        dropout_rate: float = 0.3,
    ):
        super(MuzzleFeatureBackbone, self).__init__()
        self.backbone_name = backbone_name
        self.embedding_dim = embedding_dim

        if backbone_name == "resnet50":
            weights = models.ResNet50_Weights.DEFAULT if pretrained else None
            base = models.resnet50(weights=weights)
            in_features = base.fc.in_features
            # Replace final classification head with identity
            base.fc = nn.Identity()
            self.feature_extractor = base
        elif backbone_name == "efficientnet_b0":
            weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
            base = models.efficientnet_b0(weights=weights)
            in_features = base.classifier[1].in_features
            base.classifier = nn.Identity()
            self.feature_extractor = base
        else:
            # Custom lightweight residual convolutional network
            in_features = 512
            self.feature_extractor = nn.Sequential(
                nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(kernel_size=3, stride=2, padding=1),
                nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
                nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm2d(256),
                nn.ReLU(inplace=True),
                nn.Conv2d(256, 512, kernel_size=3, stride=2, padding=1),
                nn.BatchNorm2d(512),
                nn.ReLU(inplace=True),
                nn.AdaptiveAvgPool2d((1, 1)),
                nn.Flatten(),
            )

        # Projection head to embedding space
        self.embedding_head = nn.Sequential(
            nn.Linear(in_features, embedding_dim, bias=False),
            nn.BatchNorm1d(embedding_dim),
            nn.Dropout(p=dropout_rate),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Returns: L2-normalized 512-dimensional embedding vector (||v|| = 1.0)
        """
        features = self.feature_extractor(x)
        embeddings = self.embedding_head(features)
        normalized_embeddings = F.normalize(embeddings, p=2, dim=1)
        return normalized_embeddings
