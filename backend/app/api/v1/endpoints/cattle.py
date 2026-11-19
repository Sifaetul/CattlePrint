"""
Cattle Profile API Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.cattle import Cattle
from backend.app.models.farm import Farm
from backend.app.schemas.cattle import CattleCreate, CattleResponse

router = APIRouter()


@router.post("/", response_model=CattleResponse)
async def register_cattle_profile(cattle_in: CattleCreate, db: AsyncSession = Depends(get_db)):
    # Verify farm exists
    farm = await db.get(Farm, cattle_in.farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm ID not found.")

    # Check unique tag number
    stmt = select(Cattle).where(Cattle.tag_number == cattle_in.tag_number)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Cattle with this tag number already exists.")

    cattle = Cattle(**cattle_in.model_dump())
    db.add(cattle)
    await db.commit()
    await db.refresh(cattle, attribute_names=["biometrics"])
    return cattle


@router.get("/", response_model=List[CattleResponse])
async def list_cattle(
    farm_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Cattle).options(selectinload(Cattle.biometrics)).order_by(Cattle.created_at.desc())
    if farm_id:
        stmt = stmt.where(Cattle.farm_id == farm_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{cattle_id}", response_model=CattleResponse)
async def get_cattle_profile(cattle_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Cattle).options(selectinload(Cattle.biometrics)).where(Cattle.id == cattle_id)
    result = await db.execute(stmt)
    cattle = result.scalars().first()
    if not cattle:
        raise HTTPException(status_code=404, detail="Cattle profile not found.")
    return cattle
