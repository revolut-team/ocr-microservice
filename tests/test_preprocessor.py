"""
Tests for image preprocessor
"""
import pytest
import numpy as np
from app.services.image_preprocessor import ImagePreprocessor


class TestImagePreprocessor:
    """Test image preprocessing pipeline"""

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image (BGR)"""
        # Create a simple 800x600 BGR image
        return np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

    @pytest.fixture
    def sample_grayscale(self):
        """Create a sample grayscale image"""
        return np.random.randint(0, 255, (600, 800), dtype=np.uint8)

    def test_preprocessor_initialization(self):
        """Test preprocessor initialization"""
        preprocessor = ImagePreprocessor()
        assert preprocessor is not None
        assert len(preprocessor.pipeline) > 0

    def test_custom_pipeline(self):
        """Test custom preprocessing pipeline"""
        custom_steps = "resize,grayscale"
        preprocessor = ImagePreprocessor(custom_pipeline=custom_steps)
        assert preprocessor.pipeline == ["resize", "grayscale"]

    def test_resize_step(self, sample_image):
        """Test resize preprocessing step"""
        preprocessor = ImagePreprocessor(custom_pipeline="resize")
        processed, applied = preprocessor.process(sample_image)

        assert processed is not None
        assert "resize" in applied or len(applied) == 0  # May not resize if already optimal

    def test_grayscale_step(self, sample_image):
        """Test grayscale conversion"""
        preprocessor = ImagePreprocessor(custom_pipeline="grayscale")
        processed, applied = preprocessor.process(sample_image)

        assert processed is not None
        assert len(processed.shape) == 2  # Grayscale has 2 dimensions
        assert "grayscale" in applied

    def test_full_pipeline(self, sample_image):
        """Test full preprocessing pipeline"""
        preprocessor = ImagePreprocessor(
            custom_pipeline="resize,grayscale,denoise,clahe"
        )
        processed, applied = preprocessor.process(sample_image)

        assert processed is not None
        assert len(applied) > 0
        assert "grayscale" in applied

    def test_timings(self, sample_image):
        """Test that timings are recorded"""
        preprocessor = ImagePreprocessor(custom_pipeline="resize,grayscale")
        processed, applied = preprocessor.process(sample_image)

        timings = preprocessor.get_timings()
        assert "total" in timings
        assert timings["total"] > 0

    def test_invalid_step(self, sample_image):
        """Test handling of invalid preprocessing step"""
        preprocessor = ImagePreprocessor(custom_pipeline="resize,invalid_step,grayscale")
        processed, applied = preprocessor.process(sample_image)

        # Should continue processing despite invalid step
        assert processed is not None
        assert "invalid_step" not in applied
