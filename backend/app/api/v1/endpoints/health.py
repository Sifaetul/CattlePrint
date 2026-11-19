"""
Health & Diagnostics Endpoint.
"""

from fastapi import APIRouter
import torch
from backend.app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "similarity_threshold": settings.SIMILARITY_THRESHOLD,
        "cuda_available": torch.cuda.is_available(),
        "storage_ready": settings.UPLOAD_DIR.exists() and settings.CROPPED_DIR.exists(),
    }
