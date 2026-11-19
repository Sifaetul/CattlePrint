"""
CattlePrint Deep Metric Learning Training Pipeline.
Trains ArcFace + Backbone on Cattle Muzzle Prints,
Evaluates EER & Rank-1 Accuracy, and Exports to ONNX.
"""

import os
from pathlib import Path
from typing import Tuple, List
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

from ml_engine.config import model_config, path_config
from ml_engine.models.cattle_biometrics_net import CattleBiometricsNet
from ml_engine.vision.clahe_enhancer import CLAHEEnhancer
from ml_engine.evaluation.metrics import BiometricEvaluator
from ml_engine.datasets.downloader import setup_local_benchmark_dataset


class CattleMuzzleDataset(Dataset):
    def __init__(self, samples: List[Tuple[str, int]], transform=None, apply_clahe: bool = True):
        self.samples = samples
        self.transform = transform
        self.apply_clahe = apply_clahe
        self.clahe = CLAHEEnhancer() if apply_clahe else None

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image_bgr = Image.open(img_path).convert("RGB")
        img_np = np.array(image_bgr)[:, :, ::-1]  # RGB to BGR for cv2

        if self.apply_clahe and self.clahe:
            img_np = self.clahe.enhance(img_np)

        img_rgb = Image.fromarray(img_np[:, :, ::-1])

        if self.transform:
            img_tensor = self.transform(img_rgb)
        else:
            img_tensor = transforms.ToTensor()(img_rgb)

        return img_tensor, torch.tensor(label, dtype=torch.long)


def build_samples_list(data_dir: Path) -> Tuple[List[Tuple[str, int]], int]:
    samples = []
    classes = sorted([d.name for d in data_dir.iterdir() if d.is_dir()])
    class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}

    for cls_name in classes:
        cls_dir = data_dir / cls_name
        for img_file in cls_dir.glob("*.jpg"):
            samples.append((str(img_file), class_to_idx[cls_name]))

    return samples, len(classes)


def train_cattle_model(
    data_dir: Path,
    num_epochs: int = 5,
    batch_size: int = 8,
    learning_rate: float = 1e-4,
    device: str = "cpu",
) -> Tuple[CattleBiometricsNet, dict]:
    """
    Executes training loop and produces trained model + performance metrics.
    """
    samples, num_classes = build_samples_list(data_dir)
    if num_classes < 2:
        raise ValueError("At least 2 cattle classes are required for metric learning.")

    # Data augmentation tailored for muzzle recognition
    train_transform = transforms.Compose([
        transforms.Resize(model_config.input_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=10),
        transforms.ColorJitter(brightness=0.1, contrast=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(model_config.input_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    dataset = CattleMuzzleDataset(samples, transform=train_transform, apply_clahe=True)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Initialize Model with lightweight Mobile ConvNet for fast testing
    model = CattleBiometricsNet(
        num_classes=num_classes,
        backbone_name="mobile_convnet",  # Lightweight, CPU-friendly for local test
        embedding_dim=model_config.embedding_dim,
        pretrained_backbone=False,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

    print(f"Starting CattlePrint ArcFace training for {num_classes} cattle identities...")
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()

            logits = model(images, labels)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            preds = torch.argmax(logits, dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        epoch_loss = running_loss / total
        epoch_acc = (correct / total) * 100.0
        print(f"Epoch [{epoch + 1}/{num_epochs}] - Loss: {epoch_loss:.4f} | Margin-Accuracy: {epoch_acc:.2f}%")

    # Evaluation on the dataset: extract all embeddings
    model.eval()
    val_dataset = CattleMuzzleDataset(samples, transform=val_transform, apply_clahe=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    all_embeddings = []
    all_labels = []
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            emb = model(images)  # returns normalized 512-dim embedding
            all_embeddings.append(emb.cpu().numpy())
            all_labels.append(labels.numpy())

    all_embeddings = np.concatenate(all_embeddings, axis=0)
    all_labels = np.concatenate(all_labels, axis=0)

    # Compute Genuine and Impostor pair cosine similarities
    genuine_scores = []
    impostor_scores = []
    n = len(all_labels)

    for i in range(n):
        for j in range(i + 1, n):
            sim = float(np.dot(all_embeddings[i], all_embeddings[j]))
            if all_labels[i] == all_labels[j]:
                genuine_scores.append(sim)
            else:
                impostor_scores.append(sim)

    metrics = BiometricEvaluator.calculate_far_frr_eer(
        np.array(genuine_scores), np.array(impostor_scores)
    )

    rank_metrics = BiometricEvaluator.calculate_rank_k_accuracy(
        all_embeddings, all_embeddings, all_labels, all_labels, top_k=[1, 3]
    )
    metrics.update(rank_metrics)

    # Export ONNX and PyTorch checkpoints
    path_config.weights_dir.mkdir(parents=True, exist_ok=True)
    path_config.exports_dir.mkdir(parents=True, exist_ok=True)

    weights_file = path_config.weights_dir / "cattleprint_arcface_best.pt"
    torch.save(model.state_dict(), weights_file)

    onnx_file = path_config.exports_dir / "cattleprint_backbone.onnx"
    try:
        model.export_onnx(onnx_file)
        metrics["onnx_exported"] = str(onnx_file)
    except Exception as e:
        metrics["onnx_export_error"] = str(e)

    print("\nBiometric Evaluation Report:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    return model, metrics


if __name__ == "__main__":
    test_data_dir = setup_local_benchmark_dataset(num_cattle=5, samples_per_cattle=3)
    train_cattle_model(test_data_dir, num_epochs=3)
