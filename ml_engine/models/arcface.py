"""
ArcMarginProduct (ArcFace: Additive Angular Margin Loss).
Ref: Deng et al. "ArcFace: Additive Angular Margin Loss for Deep Face Recognition" (CVPR 2019).
Adapted for Bovine Muzzle Dermatoglyphic Biometrics.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from ml_engine.config import model_config


class ArcMarginProduct(nn.Module):
    def __init__(
        self,
        in_features: int = model_config.embedding_dim,
        out_features: int = 100,  # Number of cattle classes in training set
        s: float = model_config.arcface_s,
        m: float = model_config.arcface_m,
        easy_margin: bool = False,
    ):
        super(ArcMarginProduct, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.s = s
        self.m = m
        self.weight = nn.Parameter(torch.FloatTensor(out_features, in_features))
        nn.init.xavier_uniform_(self.weight)

        self.easy_margin = easy_margin
        self.cos_m = math.cos(m)
        self.sin_m = math.sin(m)
        self.th = math.cos(math.pi - m)
        self.mm = math.sin(math.pi - m) * m

    def forward(self, input_features: torch.Tensor, label: torch.Tensor) -> torch.Tensor:
        """
        Args:
            input_features: (batch_size, in_features)
            label: (batch_size,) ground truth cattle ID indices
        Returns:
            output logits: (batch_size, out_features)
        """
        # 1. Cosine similarity = W^T * X (normalized)
        cosine = F.linear(F.normalize(input_features), F.normalize(self.weight))
        sine = torch.sqrt(1.0 - torch.clamp(cosine ** 2, 0.0, 1.0))

        # 2. Additive angular margin: cos(theta + m) = cos(theta)cos(m) - sin(theta)sin(m)
        phi = cosine * self.cos_m - sine * self.sin_m

        if self.easy_margin:
            phi = torch.where(cosine > 0, phi, cosine)
        else:
            phi = torch.where(cosine > self.th, phi, cosine - self.mm)

        # 3. One-hot mask for ground truth cattle class
        one_hot = torch.zeros(cosine.size(), device=input_features.device)
        one_hot.scatter_(1, label.view(-1, 1).long(), 1.0)

        # 4. Multiply by feature scale s
        output = (one_hot * phi) + ((1.0 - one_hot) * cosine)
        output *= self.s
        return output
