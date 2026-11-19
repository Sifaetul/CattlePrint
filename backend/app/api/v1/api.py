"""
API v1 Router Aggregator.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, farms, cattle, biometrics

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(farms.router, prefix="/farms", tags=["Farms"])
api_router.include_router(cattle.router, prefix="/cattle", tags=["Cattle"])
api_router.include_router(biometrics.router, prefix="/biometrics", tags=["Biometrics"])
