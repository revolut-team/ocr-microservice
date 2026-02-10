# OCR Microservice - CLAUDE.md

This file provides detailed guidance for working with the OCR microservice component of Seguramiga.

## Overview

Python/FastAPI microservice for processing Venezuelan identity documents (cedulas) and vehicle registration certificates (carnets de circulación) using Google Gemini Vision AI and PaddleOCR.

**Key Features:**
- Document type validation (rejects non-Venezuelan documents)
- High-accuracy extraction with Gemini Vision AI
- PaddleOCR fallback engine
- Docker containerized
- Structured JSON responses

## Architecture

```
FastAPI Routes → Services (Gemini Vision, PaddleOCR) → Image Processing → JSON Response
```

**Technology Stack:**
- **Framework**: FastAPI (Python 3.11)
- **AI Engine**: Google Gemini Pro Vision (primary)
- **OCR Engine**: PaddleOCR (fallback)
- **Image Processing**: OpenCV, Pillow
- **Container**: Docker with Python 3.11-slim
- **Port**: 8080

## Directory Structure

```
ocr-microservice/
├── app/
│   ├── main.py                          # FastAPI application entry
│   ├── config.py                        # Configuration settings
│   ├── routes/
│   │   └── ocr.py                       # OCR endpoints (cedula, carnet, generic)
│   ├── services/
│   │   ├── gemini_vision_service.py     # Gemini Vision integration + validation
│   │   ├── ocr_engine.py                # PaddleOCR engine
│   │   └── image_preprocessor.py        # Image preprocessing pipeline
│   ├── models/
│   │   ├── requests.py                  # Request models
│   │   └── responses.py                 # Response models
│   └── utils/
│       └── image_utils.py               # Image utilities
├── Dockerfile                            # Docker image definition
├── docker-compose.yml                    # Docker compose config
├── requirements.txt                      # Python dependencies
└── .env                                  # Environment variables
```

## Key Files

### Services

**`app/services/gemini_vision_service.py` (525 lines)**
- Primary document extraction service
- **Document validation** (lines 44-53 for cedula, 93-102 for carnet)
- Validation prompts (lines 226-274)
- Response parsing with date format conversion
- Confidence calculation

**`app/services/ocr_engine.py`**
- PaddleOCR integration
- Fallback when Gemini Vision is unavailable

### Routes

**`app/routes/ocr.py` (440 lines)**
- `POST /api/v1/ocr/cedula-vision` - Cedula with Gemini Vision
- `POST /api/v1/ocr/carnet-vision` - Carnet with Gemini Vision
- `POST /api/v1/ocr/cedula` - Cedula with PaddleOCR
- `POST /api/v1/ocr/vehicle` - Vehicle document with PaddleOCR
- `POST /api/v1/ocr/generic` - Generic OCR
- `GET /api/v1/health` - Health check

## Document Validation

### Validation Flow

1. **Image received** → Decode base64, convert BGR to RGB
2. **Validation prompt** → Send to Gemini Vision with strict validation instructions
3. **Type verification** → Parse Gemini response (must start with "SI" or "SÍ")
4. **Extraction** → If valid, proceed with data extraction
5. **Error handling** → If invalid, raise ValueError with Spanish message

### Cedula Validation

**Location:** `gemini_vision_service.py:44-53`

```python
validation_prompt = self._get_cedula_validation_prompt()
validation_response = self.model.generate_content([validation_prompt, pil_image])

if not self._is_valid_cedula(validation_response.text):
    raise ValueError("La imagen no corresponde a una cédula de identidad venezolana válida. Por favor, cargue una imagen de su cédula.")
```

**Validation Criteria:**
- Must have "REPÚBLICA BOLIVARIANA DE VENEZUELA" header
- Cedula number with V, E, J, G, or P prefix
- Fields: APELLIDOS, NOMBRES, FECHA DE NACIMIENTO
- Venezuelan national emblem
- Can be green (new) or laminated (old)

**Validation Prompt:** `gemini_vision_service.py:226-249`

### Carnet Validation

**Location:** `gemini_vision_service.py:93-102`

```python
validation_prompt = self._get_carnet_validation_prompt()
validation_response = self.model.generate_content([validation_prompt, pil_image])

if not self._is_valid_carnet(validation_response.text):
    raise ValueError("La imagen no corresponde a un certificado de circulación venezolano válido. Por favor, cargue una imagen de su carnet de circulación.")
```

**Validation Criteria:**
- Must have "INSTITUTO NACIONAL DE TRANSPORTE TERRESTRE" or "INTT" header
- Fields: PLACA, MARCA, MODELO, AÑO, COLOR, SERIAL (N.I.V.)
- Owner information with cedula
- Can be digital (QR code) or printed

**Validation Prompt:** `gemini_vision_service.py:251-274`

### Validation Logic

**Location:** `gemini_vision_service.py:276-330`

```python
def _is_valid_cedula(self, validation_response: str) -> bool:
    response_upper = validation_response.strip().upper()

    # Explicitly reject if starts with NO
    if response_upper.startswith("NO"):
        return False

    # Only accept if starts with SI or SÍ
    if response_upper.startswith("SI") or response_upper.startswith("SÍ"):
        return True

    # Reject ambiguous responses
    return False
```

**Strict validation rules:**
- Response MUST start with "SI" or "SÍ" to be accepted
- Responses starting with "NO" are rejected
- Ambiguous responses are rejected
- Detailed logging for debugging

## Extraction Prompts

### Cedula Extraction Prompt

**Location:** `gemini_vision_service.py:126-173`

Extracts:
- `numero_cedula` - Cedula number (digits only, no dots)
- `tipo_documento` - Document type (V, E, J, G, P)
- `apellidos` - Last names (uppercase)
- `nombres` - First names (uppercase)
- `fecha_nacimiento` - Birth date (DD/MM/YYYY)
- `estado_civil` - Civil status
- `nacionalidad` - Nationality
- `fecha_expedicion` - Expedition date (DD/MM/YYYY)
- `fecha_vencimiento` - Expiration date (MM/YYYY)
- `director` - Director name

**Output:** Dates converted to ISO format (YYYY-MM-DD) for HTML input compatibility

### Carnet Extraction Prompt

**Location:** `gemini_vision_service.py:175-224`

Extracts:
- `placa` - License plate
- `marca` - Vehicle brand
- `modelo` - Vehicle model
- `año` - Vehicle year
- `color` - Vehicle color
- `serial` - Serial number (N.I.V.)
- `propietario` - Owner name
- `cedula_propietario` - Owner cedula (with prefix)
- `uso` - Vehicle use
- `tipo` - Vehicle type

## Development

### Docker Commands

```bash
# Start OCR service
cd ocr-microservice
docker-compose up -d

# Stop service
docker-compose down

# View logs
docker-compose logs -f

# Restart service (does NOT apply code changes)
docker-compose restart

# Rebuild image with code changes (REQUIRED after modifying .py files)
docker-compose down
docker-compose build
docker-compose up -d
```

**CRITICAL:** Code is inside Docker image. After modifying `.py` files, you MUST rebuild the image for changes to take effect. Simple restart won't work.

### Environment Variables

Required in `.env`:

```bash
# Gemini Vision AI
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# OCR Configuration
OCR_LANG=es
OCR_USE_GPU=false
OCR_DET_THRESHOLD=0.3
OCR_MIN_CONFIDENCE=0.7

# Application
MAX_IMAGE_SIZE_MB=10
PORT=8080
WORKERS=2
LOG_LEVEL=info
CORS_ORIGINS=*
```

### Testing Validation

To test document validation, send an invalid image (not a cedula/carnet) to the endpoint and check logs:

```bash
# In one terminal - watch logs
docker logs -f seguramiga-ocr

# In another terminal - send test request
curl -X POST http://localhost:8080/api/v1/ocr/cedula-vision \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_encoded_image_here"}'
```

**Expected log output:**
```
INFO: Validating that image is a Venezuelan cedula...
INFO: Cedula validation raw response: NO - imagen de logo/paisaje/otro documento
INFO: Validation rejected: Response starts with NO
WARNING: Image validation failed: Not a Venezuelan cedula. Response: NO - [description]
ERROR: Gemini Vision processing failed: La imagen no corresponde a una cédula de identidad venezolana válida...
```

## API Response Format

### Success Response

```json
{
  "success": true,
  "message": "Cédula procesada correctamente con Gemini Vision AI",
  "data": {
    "document_type": "V",
    "document_number": "24757906",
    "first_name": "LUIGY ANTONI",
    "last_name": "HERNANDEZ RIVERO",
    "birth_date": "1994-08-13",
    "cedula_formateada": "V-24.757.906",
    "confidence": 0.818
  },
  "metadatos": {
    "confianza": 0.818,
    "cedula_formateada": "V-24.757.906",
    "campos_extraidos": 9,
    "campos_totales": 11,
    "motor": "Gemini Vision AI",
    "modelo": "gemini-1.5-flash",
    "servicio": "gemini-vision-microservice",
    "tiempo_procesamiento_ms": 3162,
    "tiempo_request_ms": 3271
  }
}
```

### Error Response (Invalid Document)

```json
{
  "detail": "La imagen no corresponde a una cédula de identidad venezolana válida. Por favor, cargue una imagen de su cédula."
}
```

## Troubleshooting

### Validation Not Working

1. **Check if container was rebuilt:**
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

2. **Check logs for validation responses:**
   ```bash
   docker logs -f seguramiga-ocr | grep -i validation
   ```

3. **Verify Gemini API key:**
   ```bash
   docker exec seguramiga-ocr env | grep GEMINI
   ```

### High Error Rate

- Check `OCR_MIN_CONFIDENCE` setting (lower for more lenient detection)
- Verify image quality (blur, lighting, angle)
- Check Gemini API quota/limits

### Slow Performance

- Consider upgrading to `gemini-1.5-pro` for better accuracy (slower)
- Increase `WORKERS` count
- Increase container memory limit in `docker-compose.yml`

## Integration with Frontend

**Frontend service:** `seguramiga_frontend/src/services/ocr.service.js`

**Usage in components:**
- `CedulaCaptureStep.jsx` - Calls `/api/v1/ocr/cedula-vision`
- `CarnetCaptureStep.jsx` - Calls `/api/v1/ocr/carnet-vision`

**Error handling:**
```javascript
try {
  const result = await ocrService.processCedulaVision(base64Image);
  // Success - populate form fields
} catch (error) {
  // Display Spanish error message
  setError(error.response?.data?.detail || 'Error procesando imagen');
}
```

## Performance Metrics

**Average Processing Time:**
- Validation: ~1-2 seconds
- Extraction: ~2-3 seconds
- Total: ~3-5 seconds per document

**Accuracy:**
- Venezuelan cedula: ~95% field extraction
- Venezuelan carnet: ~90% field extraction
- Document validation: ~99% accuracy

**Throughput:**
- Max concurrent requests: 2 (configurable via WORKERS)
- Memory usage: ~1-2GB per worker

---

**Last Updated:** 2026-02-07
**Version:** 1.0.0
**Python Version:** 3.11
**FastAPI Version:** 0.100+
**Gemini Model:** gemini-1.5-flash
