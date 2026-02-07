"""
OCR Microservice Configuration
Uses Pydantic Settings for environment variable management
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # OCR Engine Settings
    OCR_LANG: str = "es"
    OCR_USE_GPU: bool = False
    OCR_DET_THRESHOLD: float = 0.3
    OCR_DET_BOX_THRESHOLD: float = 0.5
    OCR_REC_BATCH_NUM: int = 6
    OCR_MAX_TEXT_LENGTH: int = 50
    OCR_MIN_CONFIDENCE: float = 0.7

    # Image Processing Settings
    MAX_IMAGE_SIZE_MB: int = 10
    MAX_IMAGE_DIMENSION: int = 4096
    OPTIMAL_IMAGE_WIDTH: int = 1500

    # Preprocessing Pipeline Configuration
    PREPROCESSING_PIPELINE: str = "resize,exif_fix,grayscale,denoise,clahe,adaptive_threshold,sharpen"

    # CLAHE parameters
    CLAHE_CLIP_LIMIT: float = 2.0
    CLAHE_TILE_GRID_SIZE: int = 8

    # Denoising parameters
    DENOISE_H: int = 10
    DENOISE_TEMPLATE_WINDOW_SIZE: int = 7
    DENOISE_SEARCH_WINDOW_SIZE: int = 21

    # Adaptive threshold parameters
    ADAPTIVE_BLOCK_SIZE: int = 11
    ADAPTIVE_C: int = 2

    # Server Settings
    PORT: int = 8080
    WORKERS: int = 2
    LOG_LEVEL: str = "info"

    # CORS Settings
    CORS_ORIGINS: str = "*"

    # Rate Limiting
    RATE_LIMIT_PER_SECOND: int = 10

    # Request Timeout
    REQUEST_TIMEOUT_SECONDS: int = 30

    # Gemini Vision API Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"  # or gemini-2.5-pro for better accuracy

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def preprocessing_steps(self) -> List[str]:
        """Convert PREPROCESSING_PIPELINE string to list"""
        return [step.strip() for step in self.PREPROCESSING_PIPELINE.split(",")]


# Global settings instance
settings = Settings()
