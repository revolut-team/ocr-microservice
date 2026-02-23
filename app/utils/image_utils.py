"""
Image processing utilities
"""
import base64
import io
import numpy as np
from PIL import Image
from typing import Tuple, Union
import cv2


def _pdf_to_image(pdf_bytes: bytes, max_dim: int = 2048) -> np.ndarray:
    """
    Convert the first page of a PDF to an OpenCV image array.
    Renders directly at a safe resolution to avoid huge intermediate buffers.

    Args:
        pdf_bytes: Raw PDF bytes
        max_dim: Maximum pixel dimension for the output image

    Returns:
        OpenCV image array (BGR format)
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]

    # Calculate zoom to keep largest dimension under max_dim
    page_rect = page.rect  # dimensions in points (1 point = 1/72 inch)
    page_w, page_h = page_rect.width, page_rect.height
    zoom = min(max_dim / page_w, max_dim / page_h, 200 / 72)  # cap at 200 DPI
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    image_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )

    if pix.n == 4:
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
    else:
        image_bgr = image_array

    doc.close()
    return image_bgr


def decode_base64_image(base64_string: str) -> np.ndarray:
    """
    Decode base64 string to OpenCV image array.
    Supports images (JPEG, PNG, etc.) and PDFs (renders first page).

    Args:
        base64_string: Base64 encoded image or PDF (with or without data URI)

    Returns:
        OpenCV image array (BGR format)

    Raises:
        ValueError: If image cannot be decoded
    """
    try:
        # Detect MIME type from data URI before stripping
        is_pdf = False
        if base64_string.startswith('data:'):
            mime_part = base64_string.split(',', 1)[0]
            if 'application/pdf' in mime_part:
                is_pdf = True
            base64_string = base64_string.split(',', 1)[1]

        # Decode base64
        image_bytes = base64.b64decode(base64_string)

        # Check PDF magic bytes (%PDF)
        if not is_pdf and image_bytes[:4] == b'%PDF':
            is_pdf = True

        if is_pdf:
            return _pdf_to_image(image_bytes)

        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Convert to numpy array (RGB)
        image_array = np.array(pil_image)

        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        return image_bgr

    except Exception as e:
        raise ValueError(f"Failed to decode image: {str(e)}")


def encode_image_to_base64(image: np.ndarray, format: str = 'PNG') -> str:
    """
    Encode OpenCV image to base64 string

    Args:
        image: OpenCV image array
        format: Image format (PNG, JPEG)

    Returns:
        Base64 encoded string with data URI
    """
    try:
        # Convert BGR to RGB
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image

        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)

        # Encode to bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format)
        image_bytes = buffer.getvalue()

        # Encode to base64
        base64_string = base64.b64encode(image_bytes).decode('utf-8')

        # Add data URI prefix
        mime_type = f"image/{format.lower()}"
        return f"data:{mime_type};base64,{base64_string}"

    except Exception as e:
        raise ValueError(f"Failed to encode image: {str(e)}")


def get_image_size_mb(image: Union[np.ndarray, bytes]) -> float:
    """
    Get image size in megabytes

    Args:
        image: OpenCV array or image bytes

    Returns:
        Size in MB
    """
    if isinstance(image, np.ndarray):
        size_bytes = image.nbytes
    elif isinstance(image, bytes):
        size_bytes = len(image)
    else:
        raise ValueError("Image must be numpy array or bytes")

    return size_bytes / (1024 * 1024)


def resize_image_if_needed(
    image: np.ndarray,
    max_dimension: int = 4096,
    optimal_width: int = 1500
) -> Tuple[np.ndarray, bool]:
    """
    Resize image intelligently for OCR

    Args:
        image: Input image
        max_dimension: Maximum dimension (width or height)
        optimal_width: Target width for best OCR results

    Returns:
        Tuple of (resized_image, was_resized)
    """
    height, width = image.shape[:2]

    # Check if resize needed
    if width <= max_dimension and height <= max_dimension and abs(width - optimal_width) < 200:
        return image, False

    # Calculate scale factor
    if width > max_dimension or height > max_dimension:
        # Scale down to max_dimension
        scale = max_dimension / max(width, height)
    else:
        # Scale to optimal width
        scale = optimal_width / width

    # Calculate new dimensions
    new_width = int(width * scale)
    new_height = int(height * scale)

    # Resize with high-quality interpolation
    if scale < 1:
        interpolation = cv2.INTER_AREA
    else:
        interpolation = cv2.INTER_CUBIC

    resized = cv2.resize(image, (new_width, new_height), interpolation=interpolation)

    return resized, True


def fix_image_orientation(image: np.ndarray, pil_image: Image.Image = None) -> np.ndarray:
    """
    Fix image orientation based on EXIF data

    Args:
        image: OpenCV image array
        pil_image: Optional PIL Image with EXIF data

    Returns:
        Corrected image
    """
    if pil_image is None:
        return image

    try:
        # Get EXIF orientation tag
        exif = pil_image._getexif()
        if exif is None:
            return image

        orientation = exif.get(274)  # 274 is the orientation tag

        if orientation == 3:
            image = cv2.rotate(image, cv2.ROTATE_180)
        elif orientation == 6:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif orientation == 8:
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

    except (AttributeError, KeyError, TypeError):
        pass

    return image


def get_image_dimensions(image: np.ndarray) -> Tuple[int, int]:
    """
    Get image dimensions

    Args:
        image: OpenCV image array

    Returns:
        Tuple of (width, height)
    """
    height, width = image.shape[:2]
    return width, height


def is_grayscale(image: np.ndarray) -> bool:
    """
    Check if image is grayscale

    Args:
        image: OpenCV image array

    Returns:
        True if grayscale, False if color
    """
    return len(image.shape) == 2 or image.shape[2] == 1
