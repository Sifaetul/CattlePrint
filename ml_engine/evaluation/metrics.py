"""
Biometric Evaluation Suite for Cattle Muzzle Recognition.
Calculates FAR (False Acceptance Rate), FRR (False Rejection Rate),
EER (Equal Error Rate), ROC-AUC, and Rank-1/Rank-5 Identification Accuracy.
"""

from typing import List, Tuple, Dict, Any
import numpy as np
from sklearn.metrics import roc_curve, auc


class BiometricEvaluator:
    @staticmethod
    def calculate_far_frr_eer(
        genuine_scores: np.ndarray, impostor_scores: np.ndarray, num_thresholds: int = 1000
    ) -> Dict[str, Any]:
        """
        Genuine scores: cosine similarity between images of the SAME cattle.
        Impostor scores: cosine similarity between images of DIFFERENT cattle.

        FAR = False Positives / Total Impostors (impostor score >= threshold)
        FRR = False Negatives / Total Genuine (genuine score < threshold)
        EER = Threshold where |FAR - FRR| is minimized.
        """
        thresholds = np.linspace(0.0, 1.0, num_thresholds)
        far_list = []
        frr_list = []

        total_genuine = len(genuine_scores)
        total_impostor = len(impostor_scores)

        if total_genuine == 0 or total_impostor == 0:
            raise ValueError("Genuine and impostor score lists must not be empty.")

        min_diff = float("inf")
        eer = 0.0
        optimal_threshold = 0.5

        for th in thresholds:
            # Impostors falsely accepted as genuine
            fa = np.sum(impostor_scores >= th)
            far = fa / total_impostor

            # Genuine falsely rejected
            fr = np.sum(genuine_scores < th)
            frr = fr / total_genuine

            far_list.append(far)
            frr_list.append(frr)

            diff = abs(far - frr)
            if diff < min_diff:
                min_diff = diff
                eer = (far + frr) / 2.0
                optimal_threshold = th

        # ROC & AUC
        labels = np.concatenate([np.ones_like(genuine_scores), np.zeros_like(impostor_scores)])
        scores = np.concatenate([genuine_scores, impostor_scores])
        fpr, tpr, _ = roc_curve(labels, scores)
        roc_auc = auc(fpr, tpr)

        # Classification metrics at optimal threshold
        tp = np.sum(genuine_scores >= optimal_threshold)
        fn = np.sum(genuine_scores < optimal_threshold)
        fp = np.sum(impostor_scores >= optimal_threshold)
        tn = np.sum(impostor_scores < optimal_threshold)

        accuracy = (tp + tn) / (total_genuine + total_impostor)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = (2.0 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        far_at_opt = fp / total_impostor
        frr_at_opt = fn / total_genuine

        return {
            "identification_accuracy": float(round(accuracy * 100.0, 2)),
            "precision": float(round(precision * 100.0, 2)),
            "recall": float(round(recall * 100.0, 2)),
            "f1_score": float(round(f1_score * 100.0, 2)),
            "far": float(round(far_at_opt * 100.0, 4)),
            "frr": float(round(frr_at_opt * 100.0, 4)),
            "eer": float(round(eer * 100.0, 4)),
            "optimal_threshold": float(round(optimal_threshold, 4)),
            "roc_auc": float(round(roc_auc, 4)),
            "mean_genuine_similarity": float(round(np.mean(genuine_scores), 4)),
            "mean_impostor_similarity": float(round(np.mean(impostor_scores), 4)),
            "total_genuine_pairs": total_genuine,
            "total_impostor_pairs": total_impostor,
        }

    @staticmethod
    def calculate_rank_k_accuracy(
        probe_embeddings: np.ndarray,
        gallery_embeddings: np.ndarray,
        probe_labels: np.ndarray,
        gallery_labels: np.ndarray,
        top_k: List[int] = [1, 5],
    ) -> Dict[str, float]:
        """
        Computes Rank-K 1:N Identification Accuracy.
        For each probe cattle, finds the closest matches in the gallery.
        """
        # probe_embeddings: (N_probe, 512), gallery_embeddings: (N_gallery, 512)
        # Cosine similarity matrix = probe @ gallery.T
        similarity_matrix = np.dot(probe_embeddings, gallery_embeddings.T)

        results = {}
        total_probes = len(probe_labels)

        for k in top_k:
            correct = 0
            for i in range(total_probes):
                top_indices = np.argsort(similarity_matrix[i])[::-1][:k]
                predicted_labels = gallery_labels[top_indices]
                if probe_labels[i] in predicted_labels:
                    correct += 1
            results[f"rank_{k}_accuracy"] = round((correct / total_probes) * 100.0, 2)

        return results
