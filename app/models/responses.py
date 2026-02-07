"""
Response models for OCR endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ConfidenceScore(BaseModel):
    """Individual field confidence scores"""

    overall: float = Field(..., ge=0.0, le=1.0)
    numero_cedula: Optional[float] = Field(None, ge=0.0, le=1.0)
    nombres: Optional[float] = Field(None, ge=0.0, le=1.0)
    apellidos: Optional[float] = Field(None, ge=0.0, le=1.0)
    fecha_nacimiento: Optional[float] = Field(None, ge=0.0, le=1.0)
    placa: Optional[float] = Field(None, ge=0.0, le=1.0)
    marca: Optional[float] = Field(None, ge=0.0, le=1.0)
    modelo: Optional[float] = Field(None, ge=0.0, le=1.0)
    año: Optional[float] = Field(None, ge=0.0, le=1.0)
    serial: Optional[float] = Field(None, ge=0.0, le=1.0)
    color: Optional[float] = Field(None, ge=0.0, le=1.0)


class CedulaData(BaseModel):
    """Parsed cedula data"""

    tipo_documento: Optional[str] = Field(None, description="V, E, J, G, P")
    numero_cedula: Optional[str] = Field(None, description="8-digit cedula number")
    cedula_formateada: Optional[str] = Field(None, description="Formatted as V-12.345.678")
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    fecha_nacimiento: Optional[str] = Field(None, description="DD/MM/YYYY format")
    estado_civil: Optional[str] = None
    raw_text: List[str] = Field(default_factory=list, description="All detected text lines")
    confidence: ConfidenceScore
    low_confidence_fields: List[str] = Field(default_factory=list)


class CedulaOCRResponse(BaseModel):
    """Response for cedula OCR endpoint"""

    success: bool = True
    data: CedulaData
    processing_time_ms: int
    preprocessing_applied: List[str]
    message: Optional[str] = None


class VehicleData(BaseModel):
    """Parsed vehicle document data"""

    placa: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    año: Optional[str] = None
    serial_carroceria: Optional[str] = None
    serial_motor: Optional[str] = None
    color: Optional[str] = None
    clase: Optional[str] = None
    tipo: Optional[str] = None
    uso: Optional[str] = None
    raw_text: List[str] = Field(default_factory=list)
    confidence: ConfidenceScore
    low_confidence_fields: List[str] = Field(default_factory=list)


class VehicleOCRResponse(BaseModel):
    """Response for vehicle document OCR endpoint"""

    success: bool = True
    data: VehicleData
    processing_time_ms: int
    preprocessing_applied: List[str]
    message: Optional[str] = None


class BoundingBox(BaseModel):
    """Bounding box coordinates"""

    x1: float
    y1: float
    x2: float
    y2: float
    x3: float
    y3: float
    x4: float
    y4: float


class DetectedText(BaseModel):
    """Individual detected text with metadata"""

    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    position_index: int


class GenericOCRData(BaseModel):
    """Generic OCR results"""

    detected_texts: List[DetectedText]
    total_texts: int
    average_confidence: float
    raw_text_lines: List[str]


class GenericOCRResponse(BaseModel):
    """Response for generic OCR endpoint"""

    success: bool = True
    data: GenericOCRData
    processing_time_ms: int
    preprocessing_applied: List[str]
    message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = "healthy"
    service: str = "ocr-microservice"
    version: str = "1.0.0"
    paddle_ocr_loaded: bool
    uptime_seconds: float
    timestamp: datetime = Field(default_factory=datetime.now)
    config: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response"""

    success: bool = False
    message: str
    error_type: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
