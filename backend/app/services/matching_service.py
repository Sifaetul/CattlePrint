"""
1:N Biometric Matching Service.
Performs hyperspherical cosine similarity comparison, applies confidence thresholds,
and triggers open-set unknown animal rejection.
"""

from typing import List, Tuple, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.models.biometric import MuzzleBiometric, IdentificationLog
from backend.app.models.cattle import Cattle
from backend.app.schemas.biometric import CandidateMatch


class BiometricMatchingService:
    @staticmethod
    def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Computes dot product of two L2-normalized 512-dim vectors.
        For unit vectors, dot product equals cosine similarity.
        """
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        score = float(np.dot(v1, v2))
        return max(0.0, min(1.0, score))

    async def search_1_to_n(
        self,
        db: AsyncSession,
        probe_vector: List[float],
        top_k: int = 3,
    ) -> Tuple[str, float, Optional[Cattle], List[CandidateMatch]]:
        """
        Searches entire database of registered muzzle biometrics.
        Returns:
            status: MATCH_CONFIRMED | BORDERLINE | UNKNOWN_ANIMAL
            best_score: float (0.0 to 1.0)
            best_cattle: Matched Cattle entity or None
            top_candidates: List of top matching candidates
        """
        stmt = (
            select(MuzzleBiometric)
            .options(
                selectinload(MuzzleBiometric.cattle).selectinload(Cattle.farm),
                selectinload(MuzzleBiometric.cattle).selectinload(Cattle.biometrics),
            )
            .order_by(MuzzleBiometric.created_at.desc())
        )
        result = await db.execute(stmt)
        gallery_biometrics = result.scalars().all()

        if not gallery_biometrics:
            return "UNKNOWN_ANIMAL", 0.0, None, []

        candidate_scores: List[Tuple[float, MuzzleBiometric]] = []

        for bio in gallery_biometrics:
            sim = self.calculate_cosine_similarity(probe_vector, bio.embedding)
            candidate_scores.append((sim, bio))

        # Sort descending by similarity score
        candidate_scores.sort(key=lambda x: x[0], reverse=True)

        best_score, best_bio = candidate_scores[0]
        best_cattle = best_bio.cattle

        # Prepare top candidate summaries
        top_candidates = []
        for score, bio in candidate_scores[:top_k]:
            c = bio.cattle
            farm_name = c.farm.name if c.farm else None
            top_candidates.append(
                CandidateMatch(
                    cattle_id=c.id,
                    tag_number=c.tag_number,
                    breed=c.breed,
                    farm_name=farm_name,
                    similarity_score=round(score, 4),
                )
            )

        # Apply Threshold Logic
        if best_score >= settings.SIMILARITY_THRESHOLD:
            status = "MATCH_CONFIRMED"
        elif best_score >= settings.BORDERLINE_THRESHOLD:
            status = "BORDERLINE"
        else:
            status = "UNKNOWN_ANIMAL"
            best_cattle = None

        return status, round(best_score, 4), best_cattle, top_candidates

    async def log_identification_attempt(
        self,
        db: AsyncSession,
        probe_path: str,
        matched_cattle_id: Optional[str],
        similarity_score: float,
        status: str,
    ):
        """Audit logging for field tracking and insurance claim verification."""
        log_entry = IdentificationLog(
            probe_image_path=probe_path,
            matched_cattle_id=matched_cattle_id,
            similarity_score=similarity_score,
            status=status,
        )
        db.add(log_entry)
        await db.commit()


matching_service = BiometricMatchingService()
