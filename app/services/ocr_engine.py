"""
OCR Engine - Singleton wrapper for PaddleOCR
"""
import logging
from typing import List, Tuple, Optional
import numpy as np
from paddleocr import PaddleOCR
from app.config import settings

logger = logging.getLogger(__name__)


class OCREngine:
    """Singleton OCR Engine using PaddleOCR"""

    _instance: Optional['OCREngine'] = None
    _ocr: Optional[PaddleOCR] = None
    _is_loaded: bool = False

    def __new__(cls):
        """Ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize OCR engine (only once)"""
        if not self._is_loaded:
            self._load_ocr()

    def _load_ocr(self):
        """Load PaddleOCR model"""
        try:
            logger.info("Loading PaddleOCR model...")
            logger.info(f"Config: lang={settings.OCR_LANG}, use_gpu={settings.OCR_USE_GPU}")

            self._ocr = PaddleOCR(
                use_angle_cls=True,  # Detect text orientation
                lang=settings.OCR_LANG,
                use_gpu=settings.OCR_USE_GPU,
                det_db_thresh=settings.OCR_DET_THRESHOLD,
                det_db_box_thresh=settings.OCR_DET_BOX_THRESHOLD,
                rec_batch_num=settings.OCR_REC_BATCH_NUM,
                max_text_length=settings.OCR_MAX_TEXT_LENGTH,
                use_space_char=True,
                show_log=False  # Disable internal Paddle logs
            )

            self._is_loaded = True
            logger.info("PaddleOCR model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load PaddleOCR model: {str(e)}")
            raise RuntimeError(f"OCR engine initialization failed: {str(e)}")

    def process_image(
        self,
        image: np.ndarray
    ) -> List[Tuple[List[List[float]], Tuple[str, float]]]:
        """
        Process image with OCR

        Args:
            image: OpenCV image array (BGR or grayscale)

        Returns:
            List of detected text with bounding boxes and confidence scores
            Format: [[[bbox_coords], (text, confidence)], ...]

        Raises:
            RuntimeError: If OCR processing fails
        """
        if not self._is_loaded or self._ocr is None:
            raise RuntimeError("OCR engine not loaded")

        try:
            logger.debug(f"Processing image of shape: {image.shape}")

            # PaddleOCR expects BGR or grayscale
            result = self._ocr.ocr(image, cls=True)

            # PaddleOCR returns [page_results]
            if not result or result[0] is None:
                logger.warning("No text detected in image")
                return []

            # result[0] is the list of detections for the page
            detections = result[0]

            logger.info(f"Detected {len(detections)} text regions")

            return detections

        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            raise RuntimeError(f"OCR processing error: {str(e)}")

    def extract_text_and_confidence(
        self,
        detections: List[Tuple[List[List[float]], Tuple[str, float]]]
    ) -> List[Tuple[str, float, List[List[float]]]]:
        """
        Extract text, confidence, and bounding boxes from detections

        Args:
            detections: Raw PaddleOCR output

        Returns:
            List of (text, confidence, bbox) tuples
        """
        results = []

        for detection in detections:
            bbox = detection[0]
            text_info = detection[1]
            text = text_info[0]
            confidence = text_info[1]

            results.append((text, confidence, bbox))

        return results

    def is_loaded(self) -> bool:
        """Check if OCR engine is loaded"""
        return self._is_loaded

    def get_average_confidence(
        self,
        detections: List[Tuple[List[List[float]], Tuple[str, float]]]
    ) -> float:
        """
        Calculate average confidence across all detections

        Args:
            detections: Raw PaddleOCR output

        Returns:
            Average confidence score (0.0-1.0)
        """
        if not detections:
            return 0.0

        confidences = [detection[1][1] for detection in detections]
        return sum(confidences) / len(confidences)

    def filter_by_confidence(
        self,
        detections: List[Tuple[List[List[float]], Tuple[str, float]]],
        min_confidence: float
    ) -> List[Tuple[List[List[float]], Tuple[str, float]]]:
        """
        Filter detections by minimum confidence threshold

        Args:
            detections: Raw PaddleOCR output
            min_confidence: Minimum confidence (0.0-1.0)

        Returns:
            Filtered detections
        """
        return [
            detection for detection in detections
            if detection[1][1] >= min_confidence
        ]


# Global singleton instance
_ocr_engine_instance: Optional[OCREngine] = None


def get_ocr_engine() -> OCREngine:
    """
    Get global OCR engine instance (singleton)

    Returns:
        OCREngine instance
    """
    global _ocr_engine_instance

    if _ocr_engine_instance is None:
        _ocr_engine_instance = OCREngine()

    return _ocr_engine_instance
