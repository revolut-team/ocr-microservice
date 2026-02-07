"""
Vehicle Document Parser
Specialized parser for Venezuelan vehicle circulation permits (Carnet de Circulación)
"""
import logging
import re
from typing import List, Tuple, Optional, Dict
from app.utils.validators import validate_placa_venezuela, extract_placa
from app.models.responses import VehicleData, ConfidenceScore
from app.config import settings

logger = logging.getLogger(__name__)


class VehicleDocParser:
    """Parser for Venezuelan vehicle documents"""

    # Keywords to identify vehicle documents
    VEHICLE_KEYWORDS = [
        'CARNET', 'CIRCULACION', 'CIRCULACIÓN', 'VEHICULO', 'VEHÍCULO',
        'PLACA', 'MARCA', 'MODELO', 'AÑO', 'SERIAL', 'COLOR', 'CLASE', 'TIPO', 'USO'
    ]

    # Common vehicle brands in Venezuela
    BRANDS = [
        'TOYOTA', 'FORD', 'CHEVROLET', 'NISSAN', 'HYUNDAI', 'KIA',
        'VOLKSWAGEN', 'MAZDA', 'HONDA', 'SUZUKI', 'MITSUBISHI',
        'RENAULT', 'PEUGEOT', 'CHERY', 'GEELY', 'JAC', 'CHANGAN'
    ]

    # Common colors
    COLORS = [
        'BLANCO', 'NEGRO', 'GRIS', 'AZUL', 'ROJO', 'VERDE',
        'AMARILLO', 'PLATEADO', 'DORADO', 'MARRON', 'MARRÓN',
        'BEIGE', 'NARANJA', 'MORADO', 'ROSADO'
    ]

    # Vehicle classes
    CLASSES = [
        'AUTOMOVIL', 'AUTOMÓVIL', 'CAMIONETA', 'PICKUP', 'PICK-UP',
        'MOTOCICLETA', 'MOTO', 'AUTOBUS', 'AUTOBÚS', 'CAMION', 'CAMIÓN',
        'RUSTICO', 'RÚSTICO', 'PARTICULAR'
    ]

    def __init__(self):
        """Initialize parser"""
        self.min_confidence = settings.OCR_MIN_CONFIDENCE
        logger.info(f"Initialized VehicleDocParser with min_confidence={self.min_confidence}")

    def parse(
        self,
        detections: List[Tuple[List[List[float]], Tuple[str, float]]]
    ) -> VehicleData:
        """
        Parse vehicle document data from OCR detections

        Args:
            detections: Raw PaddleOCR detections

        Returns:
            VehicleData with extracted information
        """
        # Extract text and confidence
        texts_with_confidence = []
        raw_text = []

        for detection in detections:
            bbox = detection[0]
            text = detection[1][0]
            confidence = detection[1][1]

            texts_with_confidence.append((text, confidence, bbox))
            raw_text.append(text)

        logger.info(f"Parsing {len(texts_with_confidence)} text detections")
        logger.debug(f"Raw text: {raw_text}")

        # Extract fields
        placa = None
        marca = None
        modelo = None
        año = None
        serial_carroceria = None
        serial_motor = None
        color = None
        clase = None
        tipo = None
        uso = None

        # Confidence tracking
        field_confidences = {}

        # 1. Extract placa
        placa_result = self._extract_placa(texts_with_confidence)
        if placa_result:
            placa = placa_result['placa']
            field_confidences['placa'] = placa_result['confidence']

        # 2. Extract marca (brand)
        marca_result = self._extract_marca(texts_with_confidence)
        if marca_result:
            marca = marca_result['marca']
            field_confidences['marca'] = marca_result['confidence']

        # 3. Extract modelo
        modelo_result = self._extract_modelo(texts_with_confidence)
        if modelo_result:
            modelo = modelo_result['modelo']
            field_confidences['modelo'] = modelo_result['confidence']

        # 4. Extract año (year)
        año_result = self._extract_año(texts_with_confidence)
        if año_result:
            año = año_result['año']
            field_confidences['año'] = año_result['confidence']

        # 5. Extract serial de carrocería
        serial_result = self._extract_serial(texts_with_confidence)
        if serial_result:
            serial_carroceria = serial_result['serial']
            field_confidences['serial'] = serial_result['confidence']

        # 6. Extract color
        color_result = self._extract_color(texts_with_confidence)
        if color_result:
            color = color_result['color']
            field_confidences['color'] = color_result['confidence']

        # Calculate overall confidence
        overall_confidence = sum(field_confidences.values()) / len(field_confidences) if field_confidences else 0.0

        # Identify low confidence fields
        low_confidence_fields = [
            field for field, conf in field_confidences.items()
            if conf < self.min_confidence
        ]

        # Build confidence score
        confidence = ConfidenceScore(
            overall=round(overall_confidence, 3),
            placa=field_confidences.get('placa'),
            marca=field_confidences.get('marca'),
            modelo=field_confidences.get('modelo'),
            año=field_confidences.get('año'),
            serial=field_confidences.get('serial'),
            color=field_confidences.get('color')
        )

        return VehicleData(
            placa=placa,
            marca=marca,
            modelo=modelo,
            año=año,
            serial_carroceria=serial_carroceria,
            serial_motor=serial_motor,
            color=color,
            clase=clase,
            tipo=tipo,
            uso=uso,
            raw_text=raw_text,
            confidence=confidence,
            low_confidence_fields=low_confidence_fields
        )

    def _extract_placa(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract license plate"""
        # Look for placa keyword
        placa_index = -1

        for i, (text, confidence, bbox) in enumerate(texts_with_confidence):
            text_upper = text.upper()
            if 'PLACA' in text_upper:
                placa_index = i
                break

        # Check next line after keyword
        if placa_index >= 0 and placa_index + 1 < len(texts_with_confidence):
            placa_text, confidence, bbox = texts_with_confidence[placa_index + 1]

            placa_extracted = extract_placa(placa_text)

            if placa_extracted and validate_placa_venezuela(placa_extracted):
                return {
                    'placa': placa_extracted,
                    'confidence': confidence
                }

        # Fallback: search all text
        for text, confidence, bbox in texts_with_confidence:
            placa_extracted = extract_placa(text)

            if placa_extracted and validate_placa_venezuela(placa_extracted):
                return {
                    'placa': placa_extracted,
                    'confidence': confidence * 0.8
                }

        return None

    def _extract_marca(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract vehicle brand"""
        # Look for marca keyword
        marca_index = -1

        for i, (text, confidence, bbox) in enumerate(texts_with_confidence):
            text_upper = text.upper()
            if 'MARCA' in text_upper:
                marca_index = i
                break

        # Check next line
        if marca_index >= 0 and marca_index + 1 < len(texts_with_confidence):
            marca_text, confidence, bbox = texts_with_confidence[marca_index + 1]
            marca_upper = marca_text.upper()

            # Check if it's a known brand
            for brand in self.BRANDS:
                if brand in marca_upper:
                    return {
                        'marca': brand,
                        'confidence': confidence
                    }

            # Return text even if not recognized
            return {
                'marca': marca_upper.strip(),
                'confidence': confidence * 0.7
            }

        # Fallback: search for known brands
        for text, confidence, bbox in texts_with_confidence:
            text_upper = text.upper()
            for brand in self.BRANDS:
                if brand in text_upper:
                    return {
                        'marca': brand,
                        'confidence': confidence * 0.8
                    }

        return None

    def _extract_modelo(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract vehicle model"""
        # Look for modelo keyword
        modelo_index = -1

        for i, (text, confidence, bbox) in enumerate(texts_with_confidence):
            text_upper = text.upper()
            if 'MODELO' in text_upper and 'AÑO' not in text_upper:
                modelo_index = i
                break

        # Check next line
        if modelo_index >= 0 and modelo_index + 1 < len(texts_with_confidence):
            modelo_text, confidence, bbox = texts_with_confidence[modelo_index + 1]

            # Clean and return
            modelo_clean = self._clean_text(modelo_text)

            return {
                'modelo': modelo_clean,
                'confidence': confidence
            }

        return None

    def _extract_año(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract vehicle year"""
        # Pattern for year (1900-2099)
        year_pattern = r'(19|20)\d{2}'

        # Look for año keyword first
        año_index = -1

        for i, (text, confidence, bbox) in enumerate(texts_with_confidence):
            text_upper = text.upper()
            if 'AÑO' in text_upper or 'ANO' in text_upper:
                año_index = i
                break

        # Check next line
        if año_index >= 0 and año_index + 1 < len(texts_with_confidence):
            año_text, confidence, bbox = texts_with_confidence[año_index + 1]

            match = re.search(year_pattern, año_text)
            if match:
                return {
                    'año': match.group(0),
                    'confidence': confidence
                }

        # Fallback: search all text
        for text, confidence, bbox in texts_with_confidence:
            match = re.search(year_pattern, text)
            if match:
                year = match.group(0)
                # Validate reasonable year range
                if 1980 <= int(year) <= 2030:
                    return {
                        'año': year,
                        'confidence': confidence * 0.8
                    }

        return None

    def _extract_serial(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract chassis serial number"""
        # Look for serial keyword
        serial_index = -1

        for i, (text, confidence, bbox) in enumerate(texts_with_confidence):
            text_upper = text.upper()
            if 'SERIAL' in text_upper or 'CARROCERIA' in text_upper or 'CARROCERÍA' in text_upper:
                serial_index = i
                break

        # Check next line
        if serial_index >= 0 and serial_index + 1 < len(texts_with_confidence):
            serial_text, confidence, bbox = texts_with_confidence[serial_index + 1]

            # Serial is usually alphanumeric, 10-17 characters
            serial_clean = re.sub(r'[^A-Z0-9]', '', serial_text.upper())

            if 10 <= len(serial_clean) <= 17:
                return {
                    'serial': serial_clean,
                    'confidence': confidence
                }

        return None

    def _extract_color(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract vehicle color"""
        # Look for color keyword
        color_index = -1

        for i, (text, confidence, bbox) in enumerate(texts_with_confidence):
            text_upper = text.upper()
            if 'COLOR' in text_upper:
                color_index = i
                break

        # Check next line
        if color_index >= 0 and color_index + 1 < len(texts_with_confidence):
            color_text, confidence, bbox = texts_with_confidence[color_index + 1]
            color_upper = color_text.upper()

            # Check if it's a known color
            for known_color in self.COLORS:
                if known_color in color_upper:
                    return {
                        'color': known_color,
                        'confidence': confidence
                    }

            # Return text even if not recognized
            return {
                'color': color_upper.strip(),
                'confidence': confidence * 0.7
            }

        # Fallback: search for known colors
        for text, confidence, bbox in texts_with_confidence:
            text_upper = text.upper()
            for known_color in self.COLORS:
                if known_color in text_upper:
                    return {
                        'color': known_color,
                        'confidence': confidence * 0.8
                    }

        return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = ' '.join(text.split())

        # Convert to uppercase
        text = text.upper()

        return text.strip()
