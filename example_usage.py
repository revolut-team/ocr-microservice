"""
Example usage of OCR Microservice
This script demonstrates how to use the OCR API endpoints
"""
import requests
import base64
import json


# Configuration
API_BASE_URL = "http://localhost:8080/api/v1"


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string

    Args:
        image_path: Path to image file

    Returns:
        Base64 encoded string
    """
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded}"


def check_health():
    """Check service health"""
    print("=" * 60)
    print("Checking service health...")
    print("=" * 60)

    response = requests.get(f"{API_BASE_URL}/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ Service is {data['status']}")
        print(f"  Version: {data['version']}")
        print(f"  PaddleOCR loaded: {data['paddle_ocr_loaded']}")
        print(f"  Uptime: {data['uptime_seconds']}s")
        print()
        return True
    else:
        print(f"✗ Health check failed: {response.status_code}")
        return False


def process_cedula(image_path: str):
    """
    Process a cedula image

    Args:
        image_path: Path to cedula image
    """
    print("=" * 60)
    print(f"Processing cedula: {image_path}")
    print("=" * 60)

    try:
        # Encode image
        image_base64 = encode_image_to_base64(image_path)

        # Make request
        response = requests.post(
            f"{API_BASE_URL}/ocr/cedula",
            json={
                "image": image_base64,
                "min_confidence": 0.7
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Processing successful ({data['processing_time_ms']}ms)")
            print()

            cedula_data = data['data']
            print(f"Tipo: {cedula_data['tipo_documento']}")
            print(f"Cédula: {cedula_data['cedula_formateada']}")
            print(f"Nombres: {cedula_data['nombres']}")
            print(f"Apellidos: {cedula_data['apellidos']}")
            print(f"Fecha Nacimiento: {cedula_data['fecha_nacimiento']}")
            print()

            print(f"Confidence:")
            conf = cedula_data['confidence']
            print(f"  Overall: {conf['overall']:.2%}")
            if conf['numero_cedula']:
                print(f"  Cédula: {conf['numero_cedula']:.2%}")
            if conf['nombres']:
                print(f"  Nombres: {conf['nombres']:.2%}")
            print()

            print(f"Preprocessing: {', '.join(data['preprocessing_applied'])}")
            print()

        else:
            print(f"✗ Request failed: {response.status_code}")
            print(response.json())

    except FileNotFoundError:
        print(f"✗ Image file not found: {image_path}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")


def process_vehicle(image_path: str):
    """
    Process a vehicle document image

    Args:
        image_path: Path to vehicle document image
    """
    print("=" * 60)
    print(f"Processing vehicle document: {image_path}")
    print("=" * 60)

    try:
        # Encode image
        image_base64 = encode_image_to_base64(image_path)

        # Make request
        response = requests.post(
            f"{API_BASE_URL}/ocr/vehicle",
            json={
                "image": image_base64,
                "min_confidence": 0.7
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Processing successful ({data['processing_time_ms']}ms)")
            print()

            vehicle_data = data['data']
            print(f"Placa: {vehicle_data['placa']}")
            print(f"Marca: {vehicle_data['marca']}")
            print(f"Modelo: {vehicle_data['modelo']}")
            print(f"Año: {vehicle_data['año']}")
            print(f"Serial: {vehicle_data['serial_carroceria']}")
            print(f"Color: {vehicle_data['color']}")
            print()

            print(f"Confidence:")
            conf = vehicle_data['confidence']
            print(f"  Overall: {conf['overall']:.2%}")
            if conf['placa']:
                print(f"  Placa: {conf['placa']:.2%}")
            if conf['marca']:
                print(f"  Marca: {conf['marca']:.2%}")
            print()

            print(f"Preprocessing: {', '.join(data['preprocessing_applied'])}")
            print()

        else:
            print(f"✗ Request failed: {response.status_code}")
            print(response.json())

    except FileNotFoundError:
        print(f"✗ Image file not found: {image_path}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")


def main():
    """Main function"""
    print()
    print("=" * 60)
    print("OCR Microservice - Example Usage")
    print("=" * 60)
    print()

    # Check health
    if not check_health():
        print("Service is not available. Please start the service first:")
        print("  docker-compose up -d")
        return

    # Example: Process cedula
    # Uncomment and provide a real image path
    # process_cedula("path/to/cedula.jpg")

    # Example: Process vehicle document
    # Uncomment and provide a real image path
    # process_vehicle("path/to/carnet.jpg")

    print("=" * 60)
    print("To use this script:")
    print("1. Uncomment the process_cedula() or process_vehicle() calls")
    print("2. Provide the path to your test images")
    print("3. Run: python example_usage.py")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
