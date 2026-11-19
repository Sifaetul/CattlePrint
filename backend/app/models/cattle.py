"""
Cattle Database Model.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Cattle(Base):
    __tablename__ = "cattle"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tag_number = Column(String(100), unique=True, index=True, nullable=False)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False)
    breed = Column(String(100), nullable=False)
    gender = Column(String(20), nullable=False)  # MALE, FEMALE
    date_of_birth = Column(Date, nullable=True)
    color = Column(String(50), nullable=True)
    insurance_policy_no = Column(String(100), nullable=True)
    status = Column(String(30), default="ACTIVE")  # ACTIVE, SOLD, DECEASED
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships with eager async loading
    farm = relationship("Farm", back_populates="cattle", lazy="selectin")
    biometrics = relationship("MuzzleBiometric", back_populates="cattle", cascade="all, delete-orphan", lazy="selectin")
