"""
CattlePrint Backend Configuration (Pydantic Settings).
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "CattlePrint AI Biometric Service"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database: Supports SQLite (for zero-setup dev & automated testing) and PostgreSQL with pgvector
    DATABASE_URL: str = "sqlite+aiosqlite:///./cattleprint.db"

    # Biometric Matching Threshold (0.0 to 1.0)
    # Cosine Similarity >= 0.72 indicates genuine cattle match
    SIMILARITY_THRESHOLD: float = 0.72
    BORDERLINE_THRESHOLD: float = 0.60

    # Storage paths
    STORAGE_DIR: Path = Path("./storage")
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    CROPPED_DIR: Path = STORAGE_DIR / "cropped"

    # Model settings
    MODEL_WEIGHTS_PATH: Optional[str] = None
    USE_GPU: bool = False

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()

# Ensure storage directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CROPPED_DIR.mkdir(parents=True, exist_ok=True)
