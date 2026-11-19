"""
Pydantic Schemas for Cattle Profiles.
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class CattleBase(BaseModel):
    tag_number: str = Field(..., json_schema_extra={"example": "COW-BD-1092"})
    breed: str = Field(..., json_schema_extra={"example": "Red Chittagong"})
    gender: str = Field("FEMALE", json_schema_extra={"example": "FEMALE"})
    date_of_birth: Optional[date] = None
    color: Optional[str] = Field("Reddish Brown", json_schema_extra={"example": "Reddish Brown"})
    insurance_policy_no: Optional[str] = Field(None, json_schema_extra={"example": "INS-2026-9921"})
    status: str = Field("ACTIVE", json_schema_extra={"example": "ACTIVE"})


class CattleCreate(CattleBase):
    farm_id: str


class BiometricSummary(BaseModel):
    id: str
    raw_image_path: str
    cropped_image_path: str
    quality_score: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CattleResponse(CattleBase):
    id: str
    farm_id: str
    created_at: datetime
    biometrics: List[BiometricSummary] = []
    model_config = ConfigDict(from_attributes=True)
