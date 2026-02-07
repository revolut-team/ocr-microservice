"""
Health check endpoint
"""
import logging
import time
from fastapi import APIRouter
from app.models.responses import HealthResponse
from app.services import get_ocr_engine
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["health"])

# Track service start time
SERVICE_START_TIME = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns service status, OCR model status, uptime, and configuration
    """
    try:
        # Check if OCR engine is loaded
        ocr_engine = get_ocr_engine()
        ocr_loaded = ocr_engine.is_loaded()

        # Calculate uptime
        uptime = time.time() - SERVICE_START_TIME

        # Build config summary
        config_summary = {
            "ocr_lang": settings.OCR_LANG,
            "ocr_use_gpu": settings.OCR_USE_GPU,
            "ocr_min_confidence": settings.OCR_MIN_CONFIDENCE,
            "max_image_size_mb": settings.MAX_IMAGE_SIZE_MB,
            "preprocessing_pipeline": settings.PREPROCESSING_PIPELINE,
            "port": settings.PORT,
            "workers": settings.WORKERS
        }

        return HealthResponse(
            status="healthy" if ocr_loaded else "degraded",
            service="ocr-microservice",
            version="1.0.0",
            paddle_ocr_loaded=ocr_loaded,
            uptime_seconds=round(uptime, 2),
            config=config_summary
        )

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            service="ocr-microservice",
            version="1.0.0",
            paddle_ocr_loaded=False,
            uptime_seconds=0.0,
            config={}
        )
