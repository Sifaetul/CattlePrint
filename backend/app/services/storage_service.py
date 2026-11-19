"""
Storage Service for securely persisting raw and cropped muzzle images.
"""

import uuid
from pathlib import Path
import cv2
import numpy as np
import aiofiles
from backend.app.core.config import settings


class StorageService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.cropped_dir = settings.CROPPED_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.cropped_dir.mkdir(parents=True, exist_ok=True)

    async def save_raw_image(self, file_bytes: bytes, filename_prefix: str = "raw") -> Path:
        """Saves raw uploaded image bytes to storage."""
        unique_name = f"{filename_prefix}_{uuid.uuid4().hex[:12]}.jpg"
        file_path = self.upload_dir / unique_name
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)
        return file_path

    def save_cropped_muzzle(self, cropped_bgr: np.ndarray, filename_prefix: str = "muzzle") -> Path:
        """Saves processed 224x224 muzzle crop image to storage."""
        unique_name = f"{filename_prefix}_{uuid.uuid4().hex[:12]}.jpg"
        file_path = self.cropped_dir / unique_name
        cv2.imwrite(str(file_path), cropped_bgr)
        return file_path


storage_service = StorageService()
