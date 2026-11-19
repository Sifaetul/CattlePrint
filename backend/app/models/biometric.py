"""
Biometric Database Models for Cattle Muzzle Prints & Identification Audit.
"""

import uuid
import json
from datetime import datetime
from typing import List
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class MuzzleBiometric(Base):
    __tablename__ = "muzzle_biometrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cattle_id = Column(String(36), ForeignKey("cattle.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_image_path = Column(Text, nullable=False)
    cropped_image_path = Column(Text, nullable=False)
    quality_score = Column(Float, default=1.0)
    is_primary = Column(Boolean, default=True)

    # Serialized 512-dimensional vector stored as JSON text for cross-database portability
    embedding_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cattle = relationship("Cattle", back_populates="biometrics", lazy="selectin")

    @property
    def embedding(self) -> List[float]:
        return json.loads(self.embedding_json)

    @embedding.setter
    def embedding(self, vector_list: List[float]):
        self.embedding_json = json.dumps(vector_list)


class IdentificationLog(Base):
    __tablename__ = "identification_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    probe_image_path = Column(Text, nullable=False)
    matched_cattle_id = Column(String(36), nullable=True, index=True)
    similarity_score = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)  # MATCH_CONFIRMED, BORDERLINE, UNKNOWN_ANIMAL
    timestamp = Column(DateTime, default=datetime.utcnow)
