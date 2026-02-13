"""
Gemini Vision Service for Document OCR
Uses Google Gemini Pro Vision to extract structured data from Venezuelan documents
"""
import logging
import re
import google.generativeai as genai
from typing import Dict, Any, Optional
from PIL import Image
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiVisionService:
    """Service to process documents using Gemini Pro Vision"""

    def __init__(self):
        """Initialize Gemini Vision API client"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        logger.info(f"Gemini Vision Service initialized with model: {settings.GEMINI_MODEL}")

    def process_cedula_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Process Venezuelan cedula (ID card) using Gemini Vision

        Args:
            image: Image as numpy array (BGR format from OpenCV)

        Returns:
            Dictionary with extracted cedula data
        """
        try:
            # Convert BGR to RGB for PIL
            import cv2
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)

            # First validate that this is a Venezuelan cedula
            logger.info("Validating that image is a Venezuelan cedula...")
            validation_prompt = self._get_cedula_validation_prompt()
            validation_response = self.model.generate_content([validation_prompt, pil_image])

            logger.info(f"Cedula validation raw response: {validation_response.text}")

            if not self._is_valid_cedula(validation_response.text):
                logger.warning(f"Image validation failed: Not a Venezuelan cedula. Response: {validation_response.text}")
                raise ValueError("La imagen no corresponde a una cédula de identidad venezolana válida. Por favor, cargue una imagen de su cédula.")

            # Craft prompt for Gemini
            prompt = self._get_cedula_prompt()

            logger.info("Sending image to Gemini Vision API...")

            # Generate response
            response = self.model.generate_content([prompt, pil_image])

            logger.info("Received response from Gemini Vision API")
            logger.debug(f"Raw response: {response.text}")

            # Parse response
            extracted_data = self._parse_cedula_response(response.text)

            return {
                "success": True,
                "data": extracted_data,
                "raw_response": response.text
            }

        except Exception as e:
            logger.error(f"Gemini Vision processing failed: {str(e)}")
            raise

    def process_carnet_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Process Venezuelan carnet de circulación (vehicle registration) using Gemini Vision

        Args:
            image: Image as numpy array (BGR format from OpenCV)

        Returns:
            Dictionary with extracted carnet data
        """
        try:
            # Convert BGR to RGB for PIL
            import cv2
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)

            # First validate that this is a Venezuelan carnet de circulación
            logger.info("Validating that image is a Venezuelan carnet de circulación...")
            validation_prompt = self._get_carnet_validation_prompt()
            validation_response = self.model.generate_content([validation_prompt, pil_image])

            logger.info(f"Carnet validation raw response: {validation_response.text}")

            if not self._is_valid_carnet(validation_response.text):
                logger.warning(f"Image validation failed: Not a Venezuelan carnet. Response: {validation_response.text}")
                raise ValueError("La imagen no corresponde a un certificado de circulación venezolano válido. Por favor, cargue una imagen de su carnet de circulación.")

            # Craft prompt for Gemini
            prompt = self._get_carnet_prompt()

            logger.info("Sending carnet image to Gemini Vision API...")

            # Generate response
            response = self.model.generate_content([prompt, pil_image])

            logger.info("Received carnet response from Gemini Vision API")
            logger.debug(f"Raw response: {response.text}")

            # Parse response
            extracted_data = self._parse_carnet_response(response.text)

            return {
                "success": True,
                "data": extracted_data,
                "raw_response": response.text
            }

        except Exception as e:
            logger.error(f"Gemini Vision carnet processing failed: {str(e)}")
            raise

    def _get_cedula_prompt(self) -> str:
        """
        Get optimized prompt for Venezuelan cedula extraction

        Returns:
            Prompt string for Gemini
        """
        return """Analiza esta imagen de una CÉDULA DE IDENTIDAD VENEZOLANA y extrae EXACTAMENTE los siguientes datos estructurados.

IMPORTANTE: Devuelve SOLO un JSON válido con los datos extraídos, SIN texto adicional antes o después del JSON.

Campos a extraer:

1. **numero_cedula**: El número de cédula completo (ejemplo: "24757906" sin puntos)
2. **tipo_documento**: La letra antes del número (V, E, J, G, o P)
3. **apellidos**: Los apellidos de la persona (campo APELLIDOS)
4. **nombres**: Los nombres de la persona (campo NOMBRES)
5. **fecha_nacimiento**: Fecha de nacimiento en formato DD/MM/YYYY
6. **estado_civil**: Estado civil (CASADO, SOLTERO, DIVORCIADO, VIUDO)
7. **nacionalidad**: Nacionalidad (VENEZOLANO, VENEZOLANA, etc.)
8. **fecha_expedicion**: Fecha de expedición en formato DD/MM/YYYY
9. **fecha_vencimiento**: Fecha de vencimiento en formato MM/YYYY
10. **director**: Nombre del director que expidió la cédula

FORMATO DE RESPUESTA (JSON):
```json
{
  "numero_cedula": "24757906",
  "tipo_documento": "V",
  "apellidos": "HERNANDEZ RIVERO",
  "nombres": "LUIGY ANTONI",
  "fecha_nacimiento": "13/08/1994",
  "estado_civil": "CASADO",
  "nacionalidad": "VENEZOLANO",
  "fecha_expedicion": "04/04/2025",
  "fecha_vencimiento": "04/2035",
  "director": "Dr. Giuson Flores"
}
```

NOTAS:
- Si un campo no es visible o no se puede leer, usa `null`
- Los nombres y apellidos deben estar en MAYÚSCULAS
- El número de cédula NO debe incluir puntos ni el prefijo V/E/J/G/P
- Las fechas deben estar en el formato exacto especificado
- NO inventes datos, si no puedes leerlo con confianza, usa `null`

Responde ÚNICAMENTE con el JSON, sin explicaciones."""

    def _get_carnet_prompt(self) -> str:
        """
        Get optimized prompt for Venezuelan carnet de circulación extraction

        Returns:
            Prompt string for Gemini
        """
        return """Analiza esta imagen de un CERTIFICADO DE CIRCULACIÓN venezolano (INTT) y extrae EXACTAMENTE los siguientes datos estructurados.

IMPORTANTE: Devuelve SOLO un JSON válido con los datos extraídos, SIN texto adicional antes o después del JSON.

Campos a extraer:

1. **placa**: Número de placa del vehículo (ejemplo: "AL5I77K")
2. **marca**: Marca del vehículo (ejemplo: "KEEWAY", "TOYOTA", "FORD")
3. **modelo**: Modelo del vehículo (ejemplo: "RK 250", "COROLLA", "F-150")
4. **año**: Año del vehículo (ejemplo: "2025")
5. **color**: Color del vehículo (ejemplo: "NEGRO", "BLANCO", "AZUL")
6. **serial**: Serial de carrocería o N.I.V. (ejemplo: "8123NBN12SM588128")
7. **propietario**: Nombre completo del propietario (ejemplo: "LUIGY ANTONI HERNANDEZ RIVERO")
8. **cedula_propietario**: Cédula del propietario con letra (ejemplo: "V24757906")
9. **uso**: Uso del vehículo (ejemplo: "MOTO PARTICULAR", "PARTICULAR", "PUBLICO")
10. **tipo**: Tipo de vehículo (ejemplo: "MOTOCICLETA", "AUTOMOVIL", "CAMIONETA")
11. **peso**: Peso del vehículo con unidad (ejemplo: "150 KGS", "1200 KGS"). Puede aparecer como "TARA", "PESO BRUTO" o "PESO". Si no aparece, usa null.
12. **numero_ejes**: Número de ejes con descripción (ejemplo: "2 EJES", "3 EJES"). Si no aparece, usa null.
13. **cantidad_puestos**: Cantidad de puestos o asientos con unidad (ejemplo: "2 PTOS.", "5 PTOS.", "2 PERSONAS"). Si no aparece, usa null.

FORMATO DE RESPUESTA (JSON):
```json
{
  "placa": "AL5I77K",
  "marca": "KEEWAY",
  "modelo": "RK 250",
  "año": "2025",
  "color": "NEGRO",
  "serial": "8123NBN12SM588128",
  "propietario": "LUIGY ANTONI HERNANDEZ RIVERO",
  "cedula_propietario": "V24757906",
  "uso": "MOTO PARTICULAR",
  "tipo": "MOTOCICLETA",
  "peso": "150 KGS",
  "numero_ejes": "2 EJES",
  "cantidad_puestos": "2 PTOS."
}
```

NOTAS IMPORTANTES:
- Si un campo no es visible o no se puede leer, usa `null`
- TODOS los textos deben estar en MAYÚSCULAS
- La placa puede contener números y letras (lee con cuidado, la "I" y "1" son confusas)
- El serial N.I.V. es un número largo alfanumérico
- La cédula del propietario debe incluir la letra (V, E, J, G) seguida del número SIN puntos
- NO inventes datos, si no puedes leerlo con confianza, usa `null`
- El año puede estar en formato "2025/2025" o "2025", devuelve solo "2025"

Responde ÚNICAMENTE con el JSON, sin explicaciones."""

    def _get_cedula_validation_prompt(self) -> str:
        """
        Get prompt to validate if image is a Venezuelan cedula

        Returns:
            Validation prompt string
        """
        return """Tu única tarea es determinar si esta imagen es una CÉDULA DE IDENTIDAD VENEZOLANA oficial.

Una cédula venezolana VÁLIDA debe tener TODOS estos elementos:
- Encabezado "REPÚBLICA BOLIVARIANA DE VENEZUELA" o "CÉDULA DE IDENTIDAD"
- Un número de cédula con prefijo V, E, J, G, o P
- Campos claramente visibles: APELLIDOS, NOMBRES, FECHA DE NACIMIENTO
- Logo o escudo de Venezuela
- Puede ser verde (nueva) o laminada (antigua)

IMPORTANTE:
- Si es una cédula venezolana → responde EXACTAMENTE: SI
- Si NO es una cédula venezolana (foto de persona, pasaporte, carnet de circulación, cualquier otro documento, imagen random, etc.) → responde EXACTAMENTE: NO - [describe qué es la imagen]

RESPONDE ÚNICAMENTE LA PALABRA:
SI
o
NO - [descripción breve]"""

    def _get_carnet_validation_prompt(self) -> str:
        """
        Get prompt to validate if image is a Venezuelan carnet de circulación

        Returns:
            Validation prompt string
        """
        return """Tu única tarea es determinar si esta imagen es un CERTIFICADO DE CIRCULACIÓN venezolano oficial del INTT.

Un certificado de circulación venezolano VÁLIDO debe tener TODOS estos elementos:
- Encabezado "INSTITUTO NACIONAL DE TRANSPORTE TERRESTRE" o logo "INTT"
- La palabra "CERTIFICADO" o "CIRCULACIÓN"
- Campos del vehículo: PLACA, MARCA, MODELO, AÑO, COLOR, SERIAL (N.I.V.)
- Información del propietario con cédula
- Puede ser digital (con código QR) o impreso

IMPORTANTE:
- Si es un certificado de circulación venezolano → responde EXACTAMENTE: SI
- Si NO es un certificado de circulación (cédula, licencia de conducir, foto, cualquier otro documento, imagen random, etc.) → responde EXACTAMENTE: NO - [describe qué es la imagen]

RESPONDE ÚNICAMENTE LA PALABRA:
SI
o
NO - [descripción breve]"""

    def _is_valid_cedula(self, validation_response: str) -> bool:
        """
        Check if validation response indicates a valid Venezuelan cedula

        Args:
            validation_response: Response from validation prompt

        Returns:
            True if valid cedula, False otherwise
        """
        response_upper = validation_response.strip().upper()
        logger.info(f"Cedula validation response (uppercase): {response_upper}")

        # Explicitly reject if response contains NO
        if response_upper.startswith("NO"):
            logger.info("Validation rejected: Response starts with NO")
            return False

        # Only accept if response CLEARLY indicates it's a valid Venezuelan cedula
        # Must start with SI or SÍ
        if response_upper.startswith("SI") or response_upper.startswith("SÍ"):
            logger.info("Validation accepted: Response starts with SI/SÍ")
            return True

        # If response doesn't start with SI/SÍ, reject it
        logger.info(f"Validation rejected: Response doesn't start with SI/SÍ. Response: {response_upper}")
        return False

    def _is_valid_carnet(self, validation_response: str) -> bool:
        """
        Check if validation response indicates a valid Venezuelan carnet

        Args:
            validation_response: Response from validation prompt

        Returns:
            True if valid carnet, False otherwise
        """
        response_upper = validation_response.strip().upper()
        logger.info(f"Carnet validation response (uppercase): {response_upper}")

        # Explicitly reject if response contains NO
        if response_upper.startswith("NO"):
            logger.info("Validation rejected: Response starts with NO")
            return False

        # Only accept if response CLEARLY indicates it's a valid Venezuelan carnet
        # Must start with SI or SÍ
        if response_upper.startswith("SI") or response_upper.startswith("SÍ"):
            logger.info("Validation accepted: Response starts with SI/SÍ")
            return True

        # If response doesn't start with SI/SÍ, reject it
        logger.info(f"Validation rejected: Response doesn't start with SI/SÍ. Response: {response_upper}")
        return False

    def _convert_date_format(self, date_str: Optional[str]) -> Optional[str]:
        """
        Convert date from DD/MM/YYYY to YYYY-MM-DD (ISO format for HTML input date)

        Args:
            date_str: Date string in DD/MM/YYYY format

        Returns:
            Date string in YYYY-MM-DD format or None if invalid
        """
        if not date_str:
            return None

        try:
            # Try to parse DD/MM/YYYY format
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
            if match:
                day, month, year = match.groups()
                # Return in ISO format (YYYY-MM-DD)
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            return None
        except Exception as e:
            logger.warning(f"Failed to convert date format: {date_str} - {str(e)}")
            return None

    def _parse_cedula_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini response and extract structured data

        Args:
            response_text: Raw text response from Gemini

        Returns:
            Dictionary with extracted and validated data
        """
        import json

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")

            # Parse JSON
            data = json.loads(json_str)

            # Convert dates to ISO format (YYYY-MM-DD) for HTML input compatibility
            fecha_nacimiento_iso = self._convert_date_format(data.get("fecha_nacimiento"))
            fecha_expedicion_iso = self._convert_date_format(data.get("fecha_expedicion"))

            # Validate and normalize data
            validated_data = {
                "tipo_documento": data.get("tipo_documento", "V"),
                "numero_cedula": str(data.get("numero_cedula", "")).replace(".", "").replace("-", ""),
                "apellidos": data.get("apellidos"),
                "nombres": data.get("nombres"),
                "fecha_nacimiento": fecha_nacimiento_iso,  # ISO format (YYYY-MM-DD)
                "estado_civil": data.get("estado_civil"),
                "nacionalidad": data.get("nacionalidad"),
                "fecha_expedicion": fecha_expedicion_iso,  # ISO format (YYYY-MM-DD)
                "fecha_vencimiento": data.get("fecha_vencimiento"),
                "director": data.get("director"),
            }

            # Format cedula number with dots (V-12.345.678)
            if validated_data["numero_cedula"]:
                cedula_num = validated_data["numero_cedula"]
                if len(cedula_num) >= 7:
                    # Format with dots: 12345678 -> 12.345.678
                    formatted = f"{cedula_num[:-6]}.{cedula_num[-6:-3]}.{cedula_num[-3:]}"
                    validated_data["cedula_formateada"] = f"{validated_data['tipo_documento']}-{formatted}"
                else:
                    validated_data["cedula_formateada"] = f"{validated_data['tipo_documento']}-{cedula_num}"
            else:
                validated_data["cedula_formateada"] = None

            # Calculate confidence (Gemini doesn't provide per-field confidence, so we estimate)
            non_null_fields = sum(1 for v in validated_data.values() if v is not None)
            total_fields = 11  # Total expected fields
            confidence = round(non_null_fields / total_fields, 3)

            validated_data["confidence"] = {
                "overall": confidence,
                "campos_extraidos": non_null_fields,
                "campos_totales": total_fields
            }

            logger.info(f"Parsed cedula data: {validated_data['cedula_formateada']}")

            return validated_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {str(e)}")
            logger.error(f"Raw response: {response_text}")
            raise ValueError(f"Error al procesar el documento: formato de respuesta inválido")
        except Exception as e:
            logger.error(f"Failed to parse cedula response: {str(e)}")
            raise

    def _parse_carnet_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini response for carnet and extract structured data

        Args:
            response_text: Raw text response from Gemini

        Returns:
            Dictionary with extracted and validated carnet data
        """
        import json

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")

            # Parse JSON
            data = json.loads(json_str)

            # Normalize year format (handle "2025/2025" → "2025")
            año = data.get("año", "")
            if año and "/" in str(año):
                año = str(año).split("/")[0]

            # Validate and normalize data
            validated_data = {
                "placa": data.get("placa"),
                "marca": data.get("marca"),
                "modelo": data.get("modelo"),
                "año": año,
                "color": data.get("color"),
                "serial": data.get("serial"),
                "propietario": data.get("propietario"),
                "cedula_propietario": data.get("cedula_propietario"),
                "uso": data.get("uso"),
                "tipo": data.get("tipo"),
                "peso": data.get("peso"),
                "numero_ejes": data.get("numero_ejes"),
                "cantidad_puestos": data.get("cantidad_puestos"),
            }

            # Calculate confidence (Gemini doesn't provide per-field confidence, so we estimate)
            # Core fields: placa, marca, modelo, año, color, serial (6 fields)
            core_fields = ["placa", "marca", "modelo", "año", "color", "serial"]
            non_null_core = sum(1 for field in core_fields if validated_data.get(field))

            total_fields = len(validated_data)
            non_null_fields = sum(1 for v in validated_data.values() if v is not None and v != "")

            # Prioritize core fields in confidence calculation
            confidence = round((non_null_core / len(core_fields)) * 0.7 + (non_null_fields / total_fields) * 0.3, 3)

            validated_data["confidence"] = {
                "overall": confidence,
                "campos_extraidos": non_null_fields,
                "campos_totales": total_fields,
                "campos_core_extraidos": non_null_core,
                "campos_core_totales": len(core_fields)
            }

            logger.info(f"Parsed carnet data: {validated_data.get('placa')} - {validated_data.get('marca')} {validated_data.get('modelo')} | tipo={validated_data.get('tipo')}, peso={validated_data.get('peso')}, ejes={validated_data.get('numero_ejes')}, puestos={validated_data.get('cantidad_puestos')}")

            return validated_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from carnet response: {str(e)}")
            logger.error(f"Raw response: {response_text}")
            raise ValueError(f"Error al procesar el documento: formato de respuesta inválido")
        except Exception as e:
            logger.error(f"Failed to parse carnet response: {str(e)}")
            raise


# Singleton instance
_gemini_service: Optional[GeminiVisionService] = None


def get_gemini_vision_service() -> GeminiVisionService:
    """Get or create Gemini Vision service instance"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiVisionService()
    return _gemini_service
