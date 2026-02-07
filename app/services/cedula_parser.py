"""
Venezuelan Cedula Parser
Specialized parser for extracting data from Venezuelan ID cards
"""
import logging
import re
from typing import List, Tuple, Optional, Dict
from app.utils.validators import (
    validate_cedula,
    format_cedula,
    validate_fecha,
    extract_cedula_number
)
from app.models.responses import CedulaData, ConfidenceScore
from app.config import settings

logger = logging.getLogger(__name__)


class CedulaParser:
    """Parser for Venezuelan cedula documents"""

    # Keywords to identify cedula documents
    CEDULA_KEYWORDS = [
        'REPUBLICA', 'REPÚBLICA', 'BOLIVARIANA', 'VENEZUELA',
        'CEDULA', 'CÉDULA', 'IDENTIDAD', 'ELECTORAL'
    ]

    # Document type patterns
    DOC_TYPES = ['V', 'E', 'J', 'G', 'P']

    # Name keywords (usually appear near names)
    NAME_KEYWORDS = ['NOMBRES', 'APELLIDOS', 'NOMBRE', 'APELLIDO']

    def __init__(self):
        """Initialize parser"""
        self.min_confidence = settings.OCR_MIN_CONFIDENCE
        logger.info(f"Initialized CedulaParser with min_confidence={self.min_confidence}")

    def parse(
        self,
        detections: List[Tuple[List[List[float]], Tuple[str, float]]]
    ) -> CedulaData:
        """
        Parse cedula data from OCR detections

        Args:
            detections: Raw PaddleOCR detections

        Returns:
            CedulaData with extracted information
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
        tipo_documento = None
        numero_cedula = None
        cedula_formateada = None
        nombres = None
        apellidos = None
        fecha_nacimiento = None
        estado_civil = None

        # Confidence tracking
        field_confidences = {}

        # 1. Extract cedula number and type
        cedula_result = self._extract_cedula(texts_with_confidence)
        if cedula_result:
            tipo_documento = cedula_result['tipo']
            numero_cedula = cedula_result['numero']
            cedula_formateada = cedula_result['formateada']
            field_confidences['numero_cedula'] = cedula_result['confidence']

        # 2. Extract names
        nombres_result = self._extract_nombres(texts_with_confidence)
        if nombres_result:
            nombres = nombres_result['nombres']
            field_confidences['nombres'] = nombres_result['confidence']

        # 3. Extract surnames
        apellidos_result = self._extract_apellidos(texts_with_confidence)
        if apellidos_result:
            apellidos = apellidos_result['apellidos']
            field_confidences['apellidos'] = apellidos_result['confidence']

        # 4. Extract birth date
        fecha_result = self._extract_fecha_nacimiento(texts_with_confidence)
        if fecha_result:
            fecha_nacimiento = fecha_result['fecha']
            field_confidences['fecha_nacimiento'] = fecha_result['confidence']

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
            numero_cedula=field_confidences.get('numero_cedula'),
            nombres=field_confidences.get('nombres'),
            apellidos=field_confidences.get('apellidos'),
            fecha_nacimiento=field_confidences.get('fecha_nacimiento')
        )

        return CedulaData(
            tipo_documento=tipo_documento,
            numero_cedula=numero_cedula,
            cedula_formateada=cedula_formateada,
            nombres=nombres,
            apellidos=apellidos,
            fecha_nacimiento=fecha_nacimiento,
            estado_civil=estado_civil,
            raw_text=raw_text,
            confidence=confidence,
            low_confidence_fields=low_confidence_fields
        )

    def _extract_cedula(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract cedula number and type"""
        # Pattern for cedula: [V|E|J|G|P]-XX.XXX.XXX or similar
        cedula_pattern = r'[VvEeJjGgPp][-.\s]?\d{1,2}[.\s]?\d{3}[.\s]?\d{3}'

        best_match = None
        best_confidence = 0.0

        for text, confidence, bbox in texts_with_confidence:
            # Try to find cedula pattern
            match = re.search(cedula_pattern, text)

            if match:
                cedula_str = match.group(0)

                # Extract type and number
                tipo = cedula_str[0].upper()
                numero = re.sub(r'[^0-9]', '', cedula_str)

                # Validate
                if validate_cedula(numero):
                    if confidence > best_confidence:
                        best_match = {
                            'tipo': tipo,
                            'numero': numero,
                            'formateada': format_cedula(tipo, numero),
                            'confidence': confidence
                        }
                        best_confidence = confidence

        # If no pattern match, try to find just numbers
        if not best_match:
            for text, confidence, bbox in texts_with_confidence:
                # Extract numbers
                numbers = re.sub(r'[^0-9]', '', text)

                if len(numbers) >= 6 and len(numbers) <= 8:
                    if validate_cedula(numbers):
                        # Assume V type
                        best_match = {
                            'tipo': 'V',
                            'numero': numbers,
                            'formateada': format_cedula('V', numbers),
                            'confidence': confidence * 0.8  # Lower confidence
                        }
                        break

        return best_match

    def _extract_nombres(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract first names"""
        # Look for name keywords
        name_index = -1

        for i, (text, confidence, bbox) in enumerate(texts_with_confidence):
            text_upper = text.upper()
            if 'NOMBRE' in text_upper or 'NOMBRES' in text_upper:
                name_index = i
                break

        if name_index >= 0 and name_index + 1 < len(texts_with_confidence):
            # Next line after keyword
            nombres_text, confidence, bbox = texts_with_confidence[name_index + 1]

            # Clean and validate
            nombres_clean = self._clean_name(nombres_text)

            if nombres_clean:
                return {
                    'nombres': nombres_clean,
                    'confidence': confidence
                }

        # Fallback: look for capitalized words
        for text, confidence, bbox in texts_with_confidence:
            if self._looks_like_name(text):
                return {
                    'nombres': self._clean_name(text),
                    'confidence': confidence * 0.7
                }

        return None

    def _extract_apellidos(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract last names"""
        # Look for surname keywords
        surname_index = -1

        for i, (text, confidence, bbox) in enumerate(texts_with_confidence):
            text_upper = text.upper()
            if 'APELLIDO' in text_upper or 'APELLIDOS' in text_upper:
                surname_index = i
                break

        if surname_index >= 0 and surname_index + 1 < len(texts_with_confidence):
            # Next line after keyword
            apellidos_text, confidence, bbox = texts_with_confidence[surname_index + 1]

            # Clean and validate
            apellidos_clean = self._clean_name(apellidos_text)

            if apellidos_clean:
                return {
                    'apellidos': apellidos_clean,
                    'confidence': confidence
                }

        return None

    def _extract_fecha_nacimiento(
        self,
        texts_with_confidence: List[Tuple[str, float, List[List[float]]]]
    ) -> Optional[Dict[str, any]]:
        """Extract birth date"""
        # Look for date patterns
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'

        for text, confidence, bbox in texts_with_confidence:
            match = re.search(date_pattern, text)

            if match:
                fecha_str = match.group(0)

                # Validate date
                is_valid, dt = validate_fecha(fecha_str)

                if is_valid and dt:
                    # Format as DD/MM/YYYY
                    formatted = dt.strftime('%d/%m/%Y')

                    return {
                        'fecha': formatted,
                        'confidence': confidence
                    }

        return None

    def _clean_name(self, text: str) -> str:
        """Clean and normalize name text"""
        # Remove special characters except spaces
        text = re.sub(r'[^A-Za-zÀ-ÿ\s]', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Capitalize properly
        text = text.upper()

        return text.strip()

    def _looks_like_name(self, text: str) -> bool:
        """Check if text looks like a name"""
        # Should be mostly letters
        if not text:
            return False

        letters = sum(c.isalpha() for c in text)
        total = len(text)

        return letters / total > 0.7 and len(text) > 3
