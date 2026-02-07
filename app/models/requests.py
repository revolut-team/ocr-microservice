"""
Request models for OCR endpoints
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import base64


class OCRBase64Request(BaseModel):
    """Request model for base64 encoded image"""

    image: str = Field(
        ...,
        description="Base64 encoded image string (with or without data URI prefix)"
    )
    min_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold (0.0-1.0)"
    )
    preprocessing_steps: Optional[str] = Field(
        None,
        description="Custom preprocessing pipeline (comma-separated)"
    )

    @field_validator("image")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """Validate and clean base64 string"""
        # Remove data URI prefix if present
        if v.startswith("data:"):
            try:
                v = v.split(",", 1)[1]
            except IndexError:
                raise ValueError("Invalid data URI format")

        # Validate base64
        try:
            base64.b64decode(v, validate=True)
        except Exception as e:
            raise ValueError(f"Invalid base64 string: {str(e)}")

        return v


class OCRImageRequest(BaseModel):
    """Request model for multipart file upload"""

    min_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold (0.0-1.0)"
    )
    preprocessing_steps: Optional[str] = Field(
        None,
        description="Custom preprocessing pipeline (comma-separated)"
    )
