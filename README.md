# OCR Microservice

Microservicio especializado en OCR (Reconocimiento Óptico de Caracteres) para documentos venezolanos usando PaddleOCR. Optimizado para procesar imágenes capturadas desde cámaras de celulares en condiciones reales (baja luz, ángulos, desenfoque, reflejos).

## Características

- **Motor OCR**: PaddleOCR con modelo en español
- **Documentos soportados**:
  - Cédulas de identidad venezolanas (V, E, J, G, P)
  - Documentos vehiculares (Carnet de Circulación)
  - OCR genérico para cualquier imagen
- **Pipeline de preprocesamiento**: 10 pasos optimizados para imágenes móviles
- **API REST**: FastAPI con endpoints async
- **Validación**: Pydantic v2 para requests/responses
- **Containerización**: Docker + Docker Compose
- **Logging estructurado**: Tiempos de procesamiento por etapa

## Stack Tecnológico

- **Python**: 3.11+
- **Framework**: FastAPI 0.115.6
- **OCR**: PaddleOCR 2.9.1 + PaddlePaddle 2.6.2
- **Procesamiento**: OpenCV 4.10 + Pillow 11.0
- **Servidor**: Uvicorn con workers async
- **Container**: Docker con health checks

## Estructura del Proyecto

```
ocr-microservice/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app principal
│   ├── config.py                # Configuración con Pydantic Settings
│   ├── routes/
│   │   ├── ocr.py               # Endpoints /ocr/cedula, /ocr/vehicle, /ocr/generic
│   │   └── health.py            # Health check
│   ├── services/
│   │   ├── ocr_engine.py        # Singleton PaddleOCR
│   │   ├── image_preprocessor.py # Pipeline de preprocesamiento
│   │   ├── cedula_parser.py     # Parser de cédulas venezolanas
│   │   └── vehicle_doc_parser.py # Parser de documentos vehiculares
│   ├── models/
│   │   ├── requests.py          # Modelos de request
│   │   └── responses.py         # Modelos de response
│   ├── utils/
│   │   ├── validators.py        # Validación de cédula, placa, fecha
│   │   └── image_utils.py       # Utilidades de imagen
│   └── middleware/
│       └── error_handler.py     # Manejo global de errores
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Instalación y Uso

### Opción 1: Docker (Recomendado)

```bash
# 1. Copiar configuración de ejemplo
cp .env.example .env

# 2. Editar .env según necesidades (opcional)
nano .env

# 3. Construir y levantar el servicio
docker-compose up --build -d

# 4. Ver logs
docker-compose logs -f ocr-service

# 5. Health check
curl http://localhost:8080/api/v1/health
```

### Opción 2: Instalación Local

```bash
# 1. Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Copiar configuración
cp .env.example .env

# 4. Ejecutar servicio
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## Endpoints

### Health Check

```bash
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "ocr-microservice",
  "version": "1.0.0",
  "paddle_ocr_loaded": true,
  "uptime_seconds": 120.45,
  "timestamp": "2026-02-07T12:00:00",
  "config": {
    "ocr_lang": "es",
    "ocr_use_gpu": false,
    "ocr_min_confidence": 0.7,
    "preprocessing_pipeline": "resize,exif_fix,grayscale,denoise,clahe,adaptive_threshold,sharpen"
  }
}
```

### Procesar Cédula Venezolana

```bash
POST /api/v1/ocr/cedula
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "min_confidence": 0.7,
  "preprocessing_steps": "resize,grayscale,clahe"  // Opcional
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tipo_documento": "V",
    "numero_cedula": "12345678",
    "cedula_formateada": "V-12.345.678",
    "nombres": "JUAN CARLOS",
    "apellidos": "PÉREZ GÓMEZ",
    "fecha_nacimiento": "15/03/1990",
    "estado_civil": null,
    "raw_text": ["REPÚBLICA", "BOLIVARIANA", "V-12.345.678", ...],
    "confidence": {
      "overall": 0.94,
      "numero_cedula": 0.98,
      "nombres": 0.91,
      "apellidos": 0.93,
      "fecha_nacimiento": 0.89
    },
    "low_confidence_fields": []
  },
  "processing_time_ms": 450,
  "preprocessing_applied": ["resize", "grayscale", "clahe", "denoise"]
}
```

### Procesar Documento Vehicular

```bash
POST /api/v1/ocr/vehicle
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "min_confidence": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "placa": "ABC123",
    "marca": "TOYOTA",
    "modelo": "COROLLA",
    "año": "2020",
    "serial_carroceria": "JT2AB12E3K0123456",
    "serial_motor": null,
    "color": "BLANCO",
    "clase": null,
    "tipo": null,
    "uso": null,
    "raw_text": ["PLACA", "ABC123", "MARCA", "TOYOTA", ...],
    "confidence": {
      "overall": 0.89,
      "placa": 0.95,
      "marca": 0.88,
      "modelo": 0.87,
      "año": 0.91,
      "serial": 0.85,
      "color": 0.92
    },
    "low_confidence_fields": []
  },
  "processing_time_ms": 520,
  "preprocessing_applied": ["resize", "exif_fix", "grayscale", "denoise", "clahe"]
}
```

### OCR Genérico

```bash
POST /api/v1/ocr/generic
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "min_confidence": 0.6
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "detected_texts": [
      {
        "text": "REPÚBLICA BOLIVARIANA",
        "confidence": 0.95,
        "bbox": {
          "x1": 120, "y1": 50,
          "x2": 450, "y2": 50,
          "x3": 450, "y3": 85,
          "x4": 120, "y4": 85
        },
        "position_index": 0
      },
      ...
    ],
    "total_texts": 15,
    "average_confidence": 0.87,
    "raw_text_lines": ["REPÚBLICA BOLIVARIANA", "VENEZUELA", ...]
  },
  "processing_time_ms": 380,
  "preprocessing_applied": ["resize", "grayscale"]
}
```

## Pipeline de Preprocesamiento

El microservicio aplica un pipeline configurable de 10 pasos optimizados para imágenes de celular:

1. **resize** - Escala a ancho óptimo (~1500px) manteniendo aspect ratio
2. **exif_fix** - Corrección de orientación EXIF (celulares rotan metadata)
3. **grayscale** - Conversión a escala de grises
4. **denoise** - Reducción de ruido con `cv2.fastNlMeansDenoising`
5. **perspective_correction** - Corrección de perspectiva/skew (detecta bordes y hace warp)
6. **clahe** - Mejora de contraste adaptativo (CLAHE)
7. **adaptive_threshold** - Binarización adaptativa con método Gaussian
8. **sharpen** - Filtro de enfoque (sharpening kernel)
9. **morphology** - Operaciones morfológicas (opening/closing)

**Configuración por defecto:**
```env
PREPROCESSING_PIPELINE=resize,exif_fix,grayscale,denoise,clahe,adaptive_threshold,sharpen
```

Puedes personalizar el pipeline por request:
```json
{
  "image": "...",
  "preprocessing_steps": "resize,grayscale,clahe"
}
```

## Validaciones

### Cédula Venezolana
- Formato: `[V|E|J|G|P]-XX.XXX.XXX`
- Rango numérico: 1 a 99,999,999
- Normalización automática con puntos

### Placa Vehicular
- Formato antiguo: `ABC123` (3 letras + 3 números)
- Formato nuevo: `AB123CD` (2 letras + 3 números + 2 letras)
- Formato moto: `AAA000A` (3 letras + 3 números + 1 letra)

### Fecha
- Formatos soportados: `DD/MM/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`
- Validación de fechas futuras (para fechas de nacimiento)
- Rango razonable: 1900-presente

## Configuración Avanzada

### Variables de Entorno (.env)

```env
# OCR Engine
OCR_LANG=es                    # Idioma del modelo
OCR_USE_GPU=false              # Usar GPU (requiere CUDA)
OCR_DET_THRESHOLD=0.3          # Umbral de detección (bajar = más texto)
OCR_MIN_CONFIDENCE=0.7         # Confianza mínima

# Imágenes
MAX_IMAGE_SIZE_MB=10           # Tamaño máximo de imagen
MAX_IMAGE_DIMENSION=4096       # Dimensión máxima (ancho/alto)
OPTIMAL_IMAGE_WIDTH=1500       # Ancho óptimo para OCR

# Preprocesamiento
CLAHE_CLIP_LIMIT=2.0           # CLAHE clip limit
CLAHE_TILE_GRID_SIZE=8         # CLAHE grid size
DENOISE_H=10                   # Fuerza del denoising
ADAPTIVE_BLOCK_SIZE=11         # Tamaño de bloque adaptativo

# Servidor
PORT=8080
WORKERS=2                      # Workers de Uvicorn
LOG_LEVEL=info                 # debug, info, warning, error
CORS_ORIGINS=*                 # Orígenes CORS (separados por coma)

# Rate Limiting
RATE_LIMIT_PER_SECOND=10
REQUEST_TIMEOUT_SECONDS=30
```

### Optimización de Rendimiento

**CPU (Default):**
- Workers: 2-4 (según núcleos disponibles)
- Memoria: ~2GB por worker
- Tiempo promedio: 400-600ms por imagen

**GPU (Opcional):**
```env
OCR_USE_GPU=true
```
- Requiere CUDA + cuDNN instalado
- Tiempo promedio: 100-200ms por imagen
- Memoria GPU: ~1GB

### Logging

El servicio logea información estructurada:

```
2026-02-07 12:00:00 - app.services.ocr_engine - INFO - Loading PaddleOCR model...
2026-02-07 12:00:05 - app.services.ocr_engine - INFO - PaddleOCR model loaded successfully
2026-02-07 12:00:10 - app.routes.ocr - INFO - Processing cedula image
2026-02-07 12:00:10 - app.services.image_preprocessor - INFO - Initialized preprocessor with pipeline: ['resize', 'grayscale', 'clahe']
2026-02-07 12:00:10 - app.services.image_preprocessor - DEBUG - Step 'resize' took 15.32ms
2026-02-07 12:00:10 - app.services.image_preprocessor - DEBUG - Step 'grayscale' took 8.21ms
2026-02-07 12:00:10 - app.services.image_preprocessor - INFO - Total preprocessing time: 45.67ms
2026-02-07 12:00:10 - app.routes.ocr - INFO - Cedula processing completed in 450ms
```

## Integración con Seguramiga Backend

El backend de Seguramiga (Node.js/Express) consume este microservicio:

```javascript
// Backend Node.js
const axios = require('axios');

async function processCedula(imageBase64) {
  const response = await axios.post('http://ocr-service:8080/api/v1/ocr/cedula', {
    image: imageBase64,
    min_confidence: 0.7
  });

  return response.data;
}
```

**Red Docker:**
- El microservicio debe estar en la misma red Docker que el backend
- Network: `seguramiga-network`
- Host interno: `ocr-service` o `seguramiga-ocr`

## Manejo de Errores

### Errores Comunes

**400 Bad Request:**
```json
{
  "success": false,
  "message": "Invalid base64 string: Incorrect padding",
  "error_type": "value_error"
}
```

**422 Validation Error:**
```json
{
  "success": false,
  "message": "Validation error",
  "error_type": "validation_error",
  "details": {
    "errors": [
      {
        "field": "image",
        "message": "field required",
        "type": "value_error.missing"
      }
    ]
  }
}
```

**408 Timeout:**
```json
{
  "success": false,
  "message": "Request timeout",
  "error_type": "timeout"
}
```

**500 Internal Error:**
```json
{
  "success": false,
  "message": "Internal server error",
  "error_type": "runtime_error",
  "details": {
    "error": "OCR processing error: ..."
  }
}
```

## Testing

```bash
# Health check
curl http://localhost:8080/api/v1/health

# Procesar cédula con imagen de prueba
curl -X POST http://localhost:8080/api/v1/ocr/cedula \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "min_confidence": 0.7
  }'

# Ver documentación interactiva
open http://localhost:8080/docs
```

## Rendimiento Esperado

| Métrica | Valor Típico |
|---------|--------------|
| Tiempo de procesamiento (CPU) | 400-600ms |
| Tiempo de preprocesamiento | 40-80ms |
| Tiempo de OCR | 300-500ms |
| Memoria por request | ~100-200MB |
| Throughput (2 workers) | ~3-5 requests/seg |
| Primera inicialización | 10-15s (carga de modelo) |

## Troubleshooting

### El modelo PaddleOCR no se carga

```bash
# Verificar que se descargó el modelo
docker exec seguramiga-ocr ls -la /root/.paddleocr

# Rebuild con cache limpio
docker-compose build --no-cache
```

### Errores de memoria

```bash
# Aumentar límite de memoria en docker-compose.yml
mem_limit: 4g
mem_reservation: 2g
```

### Imágenes muy lentas

```bash
# Reducir calidad del preprocesamiento
PREPROCESSING_PIPELINE=resize,grayscale,clahe
```

### OCR no detecta texto

```bash
# Bajar threshold de detección
OCR_DET_THRESHOLD=0.2
OCR_MIN_CONFIDENCE=0.5
```

## Licencia

Proyecto Seguramiga - 2026

## Contacto

Para reportar issues o contribuir, contactar al equipo de desarrollo de Seguramiga.
