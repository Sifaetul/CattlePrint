"""
Farms API Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.models.farm import Farm
from backend.app.schemas.farm import FarmCreate, FarmResponse

router = APIRouter()


@router.post("/", response_model=FarmResponse)
async def create_farm(farm_in: FarmCreate, db: AsyncSession = Depends(get_db)):
    # Check if phone already registered
    stmt = select(Farm).where(Farm.phone == farm_in.phone)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Farm with this phone number already registered.")

    farm = Farm(**farm_in.model_dump())
    db.add(farm)
    await db.commit()
    await db.refresh(farm)
    return farm


@router.get("/", response_model=List[FarmResponse])
async def list_farms(db: AsyncSession = Depends(get_db)):
    stmt = select(Farm).order_by(Farm.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
