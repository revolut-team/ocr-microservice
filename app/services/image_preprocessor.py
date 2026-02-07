"""
Image Preprocessor - Pipeline for mobile camera images
Optimized for low light, angles, blur, and reflections
"""
import logging
import time
from typing import List, Tuple, Dict
import cv2
import numpy as np
from PIL import Image
from app.config import settings
from app.utils.image_utils import resize_image_if_needed, is_grayscale

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Image preprocessing pipeline for OCR optimization"""

    def __init__(self, custom_pipeline: str = None):
        """
        Initialize preprocessor with pipeline steps

        Args:
            custom_pipeline: Comma-separated list of steps (overrides config)
        """
        if custom_pipeline:
            self.pipeline = [s.strip() for s in custom_pipeline.split(',')]
        else:
            self.pipeline = settings.preprocessing_steps

        self.timings: Dict[str, float] = {}
        logger.info(f"Initialized preprocessor with pipeline: {self.pipeline}")

    def process(self, image: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """
        Process image through preprocessing pipeline

        Args:
            image: Input image (BGR or grayscale)

        Returns:
            Tuple of (processed_image, applied_steps)
        """
        self.timings = {}
        processed = image.copy()
        applied_steps = []

        total_start = time.time()

        for step in self.pipeline:
            step_start = time.time()

            try:
                if step == 'resize':
                    processed, was_resized = self._resize(processed)
                    if was_resized:
                        applied_steps.append('resize')

                elif step == 'exif_fix':
                    processed = self._fix_orientation(processed)
                    applied_steps.append('exif_fix')

                elif step == 'grayscale':
                    processed = self._to_grayscale(processed)
                    applied_steps.append('grayscale')

                elif step == 'denoise':
                    processed = self._denoise(processed)
                    applied_steps.append('denoise')

                elif step == 'perspective_correction':
                    processed, was_corrected = self._correct_perspective(processed)
                    if was_corrected:
                        applied_steps.append('perspective_correction')

                elif step == 'clahe':
                    processed = self._apply_clahe(processed)
                    applied_steps.append('clahe')

                elif step == 'adaptive_threshold':
                    processed = self._adaptive_threshold(processed)
                    applied_steps.append('adaptive_threshold')

                elif step == 'sharpen':
                    processed = self._sharpen(processed)
                    applied_steps.append('sharpen')

                elif step == 'morphology':
                    processed = self._morphological_operations(processed)
                    applied_steps.append('morphology')

                else:
                    logger.warning(f"Unknown preprocessing step: {step}")

                step_time = (time.time() - step_start) * 1000
                self.timings[step] = round(step_time, 2)
                logger.debug(f"Step '{step}' took {step_time:.2f}ms")

            except Exception as e:
                logger.error(f"Error in preprocessing step '{step}': {str(e)}")
                # Continue with next step

        total_time = (time.time() - total_start) * 1000
        self.timings['total'] = round(total_time, 2)
        logger.info(f"Total preprocessing time: {total_time:.2f}ms")

        return processed, applied_steps

    def _resize(self, image: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Step 1: Resize intelligently"""
        return resize_image_if_needed(
            image,
            max_dimension=settings.MAX_IMAGE_DIMENSION,
            optimal_width=settings.OPTIMAL_IMAGE_WIDTH
        )

    def _fix_orientation(self, image: np.ndarray) -> np.ndarray:
        """Step 2: Fix EXIF orientation (already handled in decode)"""
        # This is a placeholder - EXIF is handled during image decode
        return image

    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Step 3: Convert to grayscale"""
        if is_grayscale(image):
            return image

        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """Step 4: Reduce noise with fastNlMeansDenoising"""
        if is_grayscale(image):
            return cv2.fastNlMeansDenoising(
                image,
                h=settings.DENOISE_H,
                templateWindowSize=settings.DENOISE_TEMPLATE_WINDOW_SIZE,
                searchWindowSize=settings.DENOISE_SEARCH_WINDOW_SIZE
            )
        else:
            return cv2.fastNlMeansDenoisingColored(
                image,
                h=settings.DENOISE_H,
                hColor=settings.DENOISE_H,
                templateWindowSize=settings.DENOISE_TEMPLATE_WINDOW_SIZE,
                searchWindowSize=settings.DENOISE_SEARCH_WINDOW_SIZE
            )

    def _correct_perspective(self, image: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Step 5: Detect and correct perspective/skew"""
        try:
            # Convert to grayscale if needed
            gray = image if is_grayscale(image) else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect edges
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                return image, False

            # Find largest contour (assume it's the document)
            largest_contour = max(contours, key=cv2.contourArea)

            # Get bounding rectangle
            rect = cv2.minAreaRect(largest_contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box)

            # Check if significant rotation detected
            angle = rect[2]
            if abs(angle) < 2:  # Less than 2 degrees, no correction needed
                return image, False

            # Get rotation matrix
            center = rect[0]
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

            # Apply rotation
            height, width = image.shape[:2]
            rotated = cv2.warpAffine(image, rotation_matrix, (width, height),
                                     flags=cv2.INTER_CUBIC,
                                     borderMode=cv2.BORDER_REPLICATE)

            return rotated, True

        except Exception as e:
            logger.warning(f"Perspective correction failed: {str(e)}")
            return image, False

    def _apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """Step 6: Apply CLAHE for contrast enhancement"""
        # Convert to grayscale if needed
        gray = image if is_grayscale(image) else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Create CLAHE object
        clahe = cv2.createCLAHE(
            clipLimit=settings.CLAHE_CLIP_LIMIT,
            tileGridSize=(settings.CLAHE_TILE_GRID_SIZE, settings.CLAHE_TILE_GRID_SIZE)
        )

        # Apply CLAHE
        enhanced = clahe.apply(gray)

        return enhanced

    def _adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """Step 7: Apply adaptive thresholding"""
        # Convert to grayscale if needed
        gray = image if is_grayscale(image) else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply adaptive threshold
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            settings.ADAPTIVE_BLOCK_SIZE,
            settings.ADAPTIVE_C
        )

        return binary

    def _sharpen(self, image: np.ndarray) -> np.ndarray:
        """Step 8: Apply sharpening filter"""
        # Sharpening kernel
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])

        sharpened = cv2.filter2D(image, -1, kernel)

        return sharpened

    def _morphological_operations(self, image: np.ndarray) -> np.ndarray:
        """Step 9: Apply morphological operations (optional)"""
        # Remove small noise with opening
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

        # Close gaps with closing
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

        return closed

    def get_timings(self) -> Dict[str, float]:
        """Get timing information for last processed image"""
        return self.timings
