"""
OCR endpoints
"""
import logging
import time
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from app.models.requests import OCRBase64Request
from app.models.responses import (
    CedulaOCRResponse,
    VehicleOCRResponse,
    GenericOCRResponse,
    GenericOCRData,
    DetectedText,
    BoundingBox
)
from app.services import get_ocr_engine, ImagePreprocessor, CedulaParser, VehicleDocParser
from app.services.gemini_vision_service import get_gemini_vision_service
from app.utils.image_utils import decode_base64_image, get_image_size_mb
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])


@router.post("/cedula-vision")
async def process_cedula_vision(request: OCRBase64Request):
    """
    Process Venezuelan cedula (ID card) using Gemini Vision AI

    Uses Google Gemini Pro Vision to extract structured data from cedula images.
    More accurate than traditional OCR but requires API key.

    Extracts:
    - Document type (V, E, J, G, P)
    - Cedula number (formatted)
    - First name and last name
    - Birth date
    - Civil status
    - Nationality
    - Expedition and expiration dates
    - Director name

    Args:
        request: Base64 encoded image

    Returns:
        Structured cedula data with high accuracy
    """
    start_time = time.time()

    try:
        logger.info("Processing cedula image with Gemini Vision")

        # Decode image
        image = decode_base64_image(request.image)
        logger.debug(f"Image decoded: shape={image.shape}")

        # Check image size
        image_size_mb = get_image_size_mb(image)
        if image_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise ValueError(f"Image too large: {image_size_mb:.2f}MB (max: {settings.MAX_IMAGE_SIZE_MB}MB)")

        # Get Gemini Vision service
        gemini_service = get_gemini_vision_service()

        # Process with Gemini Vision
        result = gemini_service.process_cedula_image(image)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Gemini Vision processing completed in {processing_time_ms}ms")

        # Map to CedulaOCRResponse format
        cedula_data = result["data"]

        return {
            "success": True,
            "data": {
                "tipo_documento": cedula_data.get("tipo_documento"),
                "numero_cedula": cedula_data.get("numero_cedula"),
                "apellidos": cedula_data.get("apellidos"),
                "nombres": cedula_data.get("nombres"),
                "fecha_nacimiento": cedula_data.get("fecha_nacimiento"),
                "estado_civil": cedula_data.get("estado_civil"),
                "nacionalidad": cedula_data.get("nacionalidad"),
                "fecha_expedicion": cedula_data.get("fecha_expedicion"),
                "fecha_vencimiento": cedula_data.get("fecha_vencimiento"),
                "director": cedula_data.get("director"),
                "cedula_formateada": cedula_data.get("cedula_formateada"),
                "confidence": cedula_data.get("confidence"),
                "raw_text": result.get("raw_response", "")
            },
            "processing_time_ms": processing_time_ms,
            "preprocessing_applied": ["ocr"],
            "engine": "ocr",
            "model": "standard"
        }

    except Exception as e:
        logger.error(f"Gemini Vision processing failed: {str(e)}")
        raise


@router.post("/carnet-vision")
async def process_carnet_vision(request: OCRBase64Request):
    """
    Process Venezuelan carnet de circulación using Gemini Vision AI

    Uses Google Gemini Vision to extract structured vehicle registration data.
    More accurate than traditional OCR for Venezuelan INTT certificates.

    Extracts:
    - Plate number
    - Vehicle brand and model
    - Year and color
    - Serial number (N.I.V.)
    - Owner name and cedula
    - Vehicle use and type

    Args:
        request: Base64 encoded image

    Returns:
        Structured vehicle registration data with high accuracy
    """
    start_time = time.time()

    try:
        logger.info("Processing carnet image with Gemini Vision")

        # Decode image
        image = decode_base64_image(request.image)
        logger.debug(f"Image decoded: shape={image.shape}")

        # Check image size
        image_size_mb = get_image_size_mb(image)
        if image_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise ValueError(f"Image too large: {image_size_mb:.2f}MB (max: {settings.MAX_IMAGE_SIZE_MB}MB)")

        # Get Gemini Vision service
        gemini_service = get_gemini_vision_service()

        # Process with Gemini Vision
        result = gemini_service.process_carnet_image(image)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Gemini Vision carnet processing completed in {processing_time_ms}ms")

        # Map to VehicleOCRResponse format
        carnet_data = result["data"]

        return {
            "success": True,
            "data": {
                "plate": carnet_data.get("placa"),
                "vehicle_brand": carnet_data.get("marca"),
                "vehicle_model": carnet_data.get("modelo"),
                "vehicle_year": carnet_data.get("año"),
                "vehicle_color": carnet_data.get("color"),
                "vehicle_serial": carnet_data.get("serial"),
                "owner_name": carnet_data.get("propietario"),
                "owner_cedula": carnet_data.get("cedula_propietario"),
                "vehicle_use": carnet_data.get("uso"),
                "vehicle_type": carnet_data.get("tipo"),
                "vehicle_peso": carnet_data.get("peso"),
                "vehicle_ejes": carnet_data.get("numero_ejes"),
                "vehicle_puestos": carnet_data.get("cantidad_puestos"),
                "confidence": carnet_data.get("confidence"),
                "raw_text": result.get("raw_response", "")
            },
            "processing_time_ms": processing_time_ms,
            "preprocessing_applied": ["ocr"],
            "engine": "ocr",
            "model": "standard"
        }

    except Exception as e:
        logger.error(f"Gemini Vision carnet processing failed: {str(e)}")
        raise


@router.post("/cedula", response_model=CedulaOCRResponse)
async def process_cedula(request: OCRBase64Request):
    """
    Process Venezuelan cedula (ID card) image using PaddleOCR

    Extracts:
    - Document type (V, E, J, G, P)
    - Cedula number
    - First name
    - Last name
    - Birth date
    - Raw text

    Args:
        request: Base64 encoded image

    Returns:
        CedulaOCRResponse with extracted data
    """
    start_time = time.time()

    try:
        logger.info("Processing cedula image with PaddleOCR")

        # Decode image
        image = decode_base64_image(request.image)
        logger.debug(f"Image decoded: shape={image.shape}")

        # Check image size
        image_size_mb = get_image_size_mb(image)
        if image_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise ValueError(f"Image too large: {image_size_mb:.2f}MB (max: {settings.MAX_IMAGE_SIZE_MB}MB)")

        # Preprocess image
        custom_pipeline = request.preprocessing_steps
        preprocessor = ImagePreprocessor(custom_pipeline=custom_pipeline)
        processed_image, applied_steps = preprocessor.process(image)

        logger.info(f"Preprocessing applied: {applied_steps}")

        # Get OCR engine
        ocr_engine = get_ocr_engine()

        # Process with OCR
        detections = ocr_engine.process_image(processed_image)

        if not detections:
            raise ValueError("No text detected in image")

        # Filter by confidence if specified
        min_conf = request.min_confidence or settings.OCR_MIN_CONFIDENCE
        detections = ocr_engine.filter_by_confidence(detections, min_conf)

        logger.info(f"Filtered detections: {len(detections)} (min_confidence={min_conf})")

        # Parse cedula data
        parser = CedulaParser()
        cedula_data = parser.parse(detections)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"PaddleOCR processing completed in {processing_time_ms}ms")

        return CedulaOCRResponse(
            success=True,
            data=cedula_data,
            processing_time_ms=processing_time_ms,
            preprocessing_applied=applied_steps
        )

    except Exception as e:
        logger.error(f"PaddleOCR processing failed: {str(e)}")
        raise


@router.post("/vehicle", response_model=VehicleOCRResponse)
async def process_vehicle(request: OCRBase64Request):
    """
    Process Venezuelan vehicle document (Carnet de Circulación)

    Extracts:
    - License plate
    - Vehicle brand
    - Vehicle model
    - Vehicle year
    - Chassis serial number
    - Color
    - Raw text

    Args:
        request: Base64 encoded image

    Returns:
        VehicleOCRResponse with extracted data
    """
    start_time = time.time()

    try:
        logger.info("Processing vehicle document image")

        # Decode image
        image = decode_base64_image(request.image)
        logger.debug(f"Image decoded: shape={image.shape}")

        # Check image size
        image_size_mb = get_image_size_mb(image)
        if image_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise ValueError(f"Image too large: {image_size_mb:.2f}MB (max: {settings.MAX_IMAGE_SIZE_MB}MB)")

        # Preprocess image
        custom_pipeline = request.preprocessing_steps
        preprocessor = ImagePreprocessor(custom_pipeline=custom_pipeline)
        processed_image, applied_steps = preprocessor.process(image)

        logger.info(f"Preprocessing applied: {applied_steps}")

        # Get OCR engine
        ocr_engine = get_ocr_engine()

        # Process with OCR
        detections = ocr_engine.process_image(processed_image)

        if not detections:
            raise ValueError("No text detected in image")

        # Filter by confidence if specified
        min_conf = request.min_confidence or settings.OCR_MIN_CONFIDENCE
        detections = ocr_engine.filter_by_confidence(detections, min_conf)

        logger.info(f"Filtered detections: {len(detections)} (min_confidence={min_conf})")

        # Parse vehicle data
        parser = VehicleDocParser()
        vehicle_data = parser.parse(detections)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Vehicle processing completed in {processing_time_ms}ms")

        return VehicleOCRResponse(
            success=True,
            data=vehicle_data,
            processing_time_ms=processing_time_ms,
            preprocessing_applied=applied_steps
        )

    except Exception as e:
        logger.error(f"Vehicle processing failed: {str(e)}")
        raise


@router.post("/generic", response_model=GenericOCRResponse)
async def process_generic(request: OCRBase64Request):
    """
    Process any image with generic OCR

    Returns all detected text with bounding boxes and confidence scores

    Args:
        request: Base64 encoded image

    Returns:
        GenericOCRResponse with all detected text
    """
    start_time = time.time()

    try:
        logger.info("Processing generic image")

        # Decode image
        image = decode_base64_image(request.image)
        logger.debug(f"Image decoded: shape={image.shape}")

        # Check image size
        image_size_mb = get_image_size_mb(image)
        if image_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise ValueError(f"Image too large: {image_size_mb:.2f}MB (max: {settings.MAX_IMAGE_SIZE_MB}MB)")

        # Preprocess image
        custom_pipeline = request.preprocessing_steps
        preprocessor = ImagePreprocessor(custom_pipeline=custom_pipeline)
        processed_image, applied_steps = preprocessor.process(image)

        logger.info(f"Preprocessing applied: {applied_steps}")

        # Get OCR engine
        ocr_engine = get_ocr_engine()

        # Process with OCR
        detections = ocr_engine.process_image(processed_image)

        if not detections:
            raise ValueError("No text detected in image")

        # Filter by confidence if specified
        min_conf = request.min_confidence or settings.OCR_MIN_CONFIDENCE
        detections = ocr_engine.filter_by_confidence(detections, min_conf)

        logger.info(f"Filtered detections: {len(detections)} (min_confidence={min_conf})")

        # Build response
        detected_texts = []
        raw_text_lines = []

        for idx, detection in enumerate(detections):
            bbox = detection[0]
            text = detection[1][0]
            confidence = detection[1][1]

            # Create bounding box
            bbox_obj = BoundingBox(
                x1=bbox[0][0], y1=bbox[0][1],
                x2=bbox[1][0], y2=bbox[1][1],
                x3=bbox[2][0], y3=bbox[2][1],
                x4=bbox[3][0], y4=bbox[3][1]
            )

            # Create detected text
            detected_text = DetectedText(
                text=text,
                confidence=confidence,
                bbox=bbox_obj,
                position_index=idx
            )

            detected_texts.append(detected_text)
            raw_text_lines.append(text)

        # Calculate average confidence
        avg_confidence = ocr_engine.get_average_confidence(detections)

        # Build data
        generic_data = GenericOCRData(
            detected_texts=detected_texts,
            total_texts=len(detected_texts),
            average_confidence=round(avg_confidence, 3),
            raw_text_lines=raw_text_lines
        )

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(f"Generic processing completed in {processing_time_ms}ms")

        return GenericOCRResponse(
            success=True,
            data=generic_data,
            processing_time_ms=processing_time_ms,
            preprocessing_applied=applied_steps
        )

    except Exception as e:
        logger.error(f"Generic processing failed: {str(e)}")
        raise
