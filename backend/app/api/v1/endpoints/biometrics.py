"""
Biometric Registration and 1:N Identification API Endpoints.
"""

import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.database import get_db
from backend.app.models.cattle import Cattle
from backend.app.models.biometric import MuzzleBiometric
from backend.app.schemas.cattle import CattleResponse
from backend.app.schemas.biometric import (
    QualityCheckResponse,
    BiometricRegistrationResponse,
    IdentificationResult,
)
from backend.app.services.inference_service import inference_service
from backend.app.services.storage_service import storage_service
from backend.app.services.matching_service import matching_service

router = APIRouter()


@router.post("/quality-check", response_model=QualityCheckResponse)
async def check_muzzle_quality(file: UploadFile = File(...)):
    """
    Rapid edge quality evaluation.
    Inspects image for motion blur, darkness, or specular flash reflections.
    """
    image_bytes = await file.read()
    quality_res, _, _ = inference_service.process_and_extract_embedding(image_bytes, strict_quality=False)

    return QualityCheckResponse(
        is_valid=quality_res.is_valid,
        blur_score=quality_res.blur_score,
        brightness_score=quality_res.brightness_score,
        contrast_score=quality_res.contrast_score,
        reasons=quality_res.reasons,
        message=quality_res.message,
    )


@router.post("/register-muzzle", response_model=BiometricRegistrationResponse)
async def register_cattle_muzzle(
    cattle_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Registers biometric muzzle print for an existing cattle profile.
    Extracts 512-dim ArcFace embedding and persists to database.
    """
    cattle = await db.get(Cattle, cattle_id)
    if not cattle:
        raise HTTPException(status_code=404, detail="Cattle ID not found.")

    image_bytes = await file.read()
    quality_res, cropped_bgr, embedding = inference_service.process_and_extract_embedding(
        image_bytes, strict_quality=False
    )

    if cropped_bgr is None or embedding is None:
        raise HTTPException(status_code=400, detail=f"Image processing failed: {quality_res.message}")

    # Persist images
    raw_path = await storage_service.save_raw_image(image_bytes, filename_prefix=f"cattle_{cattle.tag_number}")
    cropped_path = storage_service.save_cropped_muzzle(cropped_bgr, filename_prefix=f"crop_{cattle.tag_number}")

    # Store biometric record
    biometric = MuzzleBiometric(
        cattle_id=cattle.id,
        raw_image_path=str(raw_path),
        cropped_image_path=str(cropped_path),
        quality_score=quality_res.blur_score,
        is_primary=True,
    )
    biometric.embedding = embedding

    db.add(biometric)
    await db.commit()
    await db.refresh(biometric)

    return BiometricRegistrationResponse(
        success=True,
        cattle_id=cattle.id,
        biometric_id=biometric.id,
        raw_image_url=str(raw_path),
        cropped_image_url=str(cropped_path),
        quality_assessment=QualityCheckResponse(
            is_valid=quality_res.is_valid,
            blur_score=quality_res.blur_score,
            brightness_score=quality_res.brightness_score,
            contrast_score=quality_res.contrast_score,
            reasons=quality_res.reasons,
            message=quality_res.message,
        ),
        message="Muzzle print successfully registered with 512-dim biometric embedding.",
    )


@router.post("/identify", response_model=IdentificationResult)
async def identify_cattle_1_to_n(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Core 1:N Biometric Identification.
    Accepts field photograph of cattle muzzle, extracts embedding,
    and searches the entire registered gallery for matching cattle.
    """
    start_time = time.time()
    image_bytes = await file.read()

    # 1. AI Inference Pipeline
    quality_res, cropped_bgr, probe_embedding = inference_service.process_and_extract_embedding(
        image_bytes, strict_quality=False
    )

    if probe_embedding is None:
        raise HTTPException(status_code=400, detail=f"Invalid image: {quality_res.message}")

    # Save probe image for audit logging
    probe_path = await storage_service.save_raw_image(image_bytes, filename_prefix="probe")

    # 2. 1:N Search against Gallery
    status, best_score, best_cattle, top_candidates = await matching_service.search_1_to_n(
        db=db, probe_vector=probe_embedding, top_k=3
    )

    elapsed_ms = round((time.time() - start_time) * 1000.0, 2)

    # 3. Audit Log
    matched_id = best_cattle.id if best_cattle else None
    await matching_service.log_identification_attempt(
        db=db,
        probe_path=str(probe_path),
        matched_cattle_id=matched_id,
        similarity_score=best_score,
        status=status,
    )

    matched = status == "MATCH_CONFIRMED"
    cattle_response = CattleResponse.model_validate(best_cattle) if best_cattle else None

    if matched:
        msg = f"Match Confirmed: Cattle identified as Tag #{best_cattle.tag_number} ({best_cattle.breed}) with {best_score * 100:.1f}% confidence."
    elif status == "BORDERLINE":
        msg = f"Borderline Match: Confidence ({best_score * 100:.1f}%) is below 72% confirmation threshold. Please recapture with steady lighting."
    else:
        msg = f"Unknown Animal: Highest similarity ({best_score * 100:.1f}%) is below threshold. Animal is not in the registered database."

    return IdentificationResult(
        matched=matched,
        status=status,
        similarity_score=best_score,
        cattle=cattle_response,
        top_candidates=top_candidates,
        quality_assessment=QualityCheckResponse(
            is_valid=quality_res.is_valid,
            blur_score=quality_res.blur_score,
            brightness_score=quality_res.brightness_score,
            contrast_score=quality_res.contrast_score,
            reasons=quality_res.reasons,
            message=quality_res.message,
        ),
        processing_time_ms=elapsed_ms,
        message=msg,
    )
