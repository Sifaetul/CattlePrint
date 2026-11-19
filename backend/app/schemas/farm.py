"""
Pydantic Schemas for Farms.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class FarmBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Bengal Green Dairy Farm"})
    owner_name: str = Field(..., json_schema_extra={"example": "Md. Rahim Uddin"})
    phone: str = Field(..., json_schema_extra={"example": "01712345678"})
    district: Optional[str] = Field("Sirajganj", json_schema_extra={"example": "Sirajganj"})
    upazila: Optional[str] = Field("Shahjadpur", json_schema_extra={"example": "Shahjadpur"})


class FarmCreate(FarmBase):
    pass


class FarmResponse(FarmBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
