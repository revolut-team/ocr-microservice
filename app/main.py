"""
OCR Microservice - FastAPI Application
Specialized OCR for Venezuelan ID cards and vehicle documents
"""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.config import settings
from app.routes import health_router, ocr_router
from app.middleware import register_error_handlers
from app.services import get_ocr_engine

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app
    Handles startup and shutdown events
    """
    # Startup
    logger.info("=" * 60)
    logger.info("OCR Microservice Starting Up")
    logger.info("=" * 60)

    try:
        # Load OCR engine (singleton)
        logger.info("Loading PaddleOCR model...")
        ocr_engine = get_ocr_engine()

        if ocr_engine.is_loaded():
            logger.info("✓ PaddleOCR model loaded successfully")
        else:
            logger.error("✗ PaddleOCR model failed to load")
            raise RuntimeError("OCR engine initialization failed")

        # Log configuration
        logger.info(f"Configuration:")
        logger.info(f"  - OCR Language: {settings.OCR_LANG}")
        logger.info(f"  - OCR Use GPU: {settings.OCR_USE_GPU}")
        logger.info(f"  - Min Confidence: {settings.OCR_MIN_CONFIDENCE}")
        logger.info(f"  - Max Image Size: {settings.MAX_IMAGE_SIZE_MB}MB")
        logger.info(f"  - Preprocessing Pipeline: {settings.PREPROCESSING_PIPELINE}")
        logger.info(f"  - Port: {settings.PORT}")
        logger.info(f"  - Workers: {settings.WORKERS}")
        logger.info(f"  - CORS Origins: {settings.CORS_ORIGINS}")

        logger.info("=" * 60)
        logger.info("OCR Microservice Ready")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("OCR Microservice Shutting Down")


# Create FastAPI app
app = FastAPI(
    title="OCR Microservice",
    description="Specialized OCR for Venezuelan ID cards and vehicle documents using PaddleOCR",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Register error handlers
register_error_handlers(app)

# Include routers
app.include_router(health_router)
app.include_router(ocr_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ocr-microservice",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# For development
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
