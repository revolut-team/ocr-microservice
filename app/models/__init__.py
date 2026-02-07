"""Models package initialization"""
from .requests import OCRImageRequest, OCRBase64Request
from .responses import (
    CedulaOCRResponse,
    VehicleOCRResponse,
    GenericOCRResponse,
    HealthResponse,
    ConfidenceScore,
    DetectedText
)

__all__ = [
    "OCRImageRequest",
    "OCRBase64Request",
    "CedulaOCRResponse",
    "VehicleOCRResponse",
    "GenericOCRResponse",
    "HealthResponse",
    "ConfidenceScore",
    "DetectedText"
]
