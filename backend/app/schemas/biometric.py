"""
Pydantic Schemas for Biometric Registration and 1:N Identification.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.cattle import CattleResponse


class QualityCheckResponse(BaseModel):
    is_valid: bool
    blur_score: float
    brightness_score: float
    contrast_score: float
    reasons: List[str]
    message: str


class BiometricRegistrationResponse(BaseModel):
    success: bool
    cattle_id: str
    biometric_id: str
    raw_image_url: str
    cropped_image_url: str
    quality_assessment: QualityCheckResponse
    message: str


class CandidateMatch(BaseModel):
    cattle_id: str
    tag_number: str
    breed: str
    farm_name: Optional[str] = None
    similarity_score: float


class IdentificationResult(BaseModel):
    matched: bool
    status: str  # MATCH_CONFIRMED, BORDERLINE, UNKNOWN_ANIMAL, QUALITY_REJECTED
    similarity_score: float
    cattle: Optional[CattleResponse] = None
    top_candidates: List[CandidateMatch] = []
    quality_assessment: QualityCheckResponse
    processing_time_ms: float
    message: str
