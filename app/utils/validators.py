"""
Validation utilities for Venezuelan documents
"""
import re
from datetime import datetime
from typing import Optional, Tuple


def validate_cedula(cedula: str) -> bool:
    """
    Validate Venezuelan cedula number

    Args:
        cedula: Cedula number (can include type prefix V, E, etc.)

    Returns:
        True if valid, False otherwise
    """
    if not cedula:
        return False

    # Extract only numbers
    numbers = re.sub(r'[^0-9]', '', cedula)

    if not numbers:
        return False

    try:
        cedula_int = int(numbers)
        # Venezuelan cedulas range from 1 to 99,999,999
        return 1 <= cedula_int <= 99999999
    except ValueError:
        return False


def format_cedula(tipo: str, numero: str) -> str:
    """
    Format cedula in standard Venezuelan format: V-12.345.678

    Args:
        tipo: Document type (V, E, J, G, P)
        numero: Cedula number (can include separators)

    Returns:
        Formatted cedula string
    """
    # Clean numero
    numbers = re.sub(r'[^0-9]', '', numero)

    if not numbers or len(numbers) > 8:
        return f"{tipo}-{numero}"

    # Pad with zeros if needed
    numbers = numbers.zfill(8)

    # Format as XX.XXX.XXX
    formatted = f"{numbers[0:2]}.{numbers[2:5]}.{numbers[5:8]}"

    # Remove leading zeros from first group
    formatted = formatted.lstrip('0').lstrip('.')

    return f"{tipo}-{formatted}"


def validate_placa_venezuela(placa: str) -> bool:
    """
    Validate Venezuelan license plate format

    Common formats:
    - ABC123 (old format: 3 letters + 3 numbers)
    - AB123CD (new format: 2 letters + 3 numbers + 2 letters)
    - AAA000A (moto format)

    Args:
        placa: License plate string

    Returns:
        True if valid, False otherwise
    """
    if not placa:
        return False

    # Remove spaces and convert to uppercase
    placa = placa.strip().replace(' ', '').replace('-', '').upper()

    # Old format: 3 letters + 3 numbers
    pattern1 = r'^[A-Z]{3}\d{3}$'

    # New format: 2 letters + 3 numbers + 2 letters
    pattern2 = r'^[A-Z]{2}\d{3}[A-Z]{2}$'

    # Moto format: 3 letters + 3 numbers + 1 letter
    pattern3 = r'^[A-Z]{3}\d{3}[A-Z]$'

    return bool(
        re.match(pattern1, placa) or
        re.match(pattern2, placa) or
        re.match(pattern3, placa)
    )


def validate_fecha(fecha_str: str) -> Tuple[bool, Optional[datetime]]:
    """
    Validate date string in DD/MM/YYYY format

    Args:
        fecha_str: Date string

    Returns:
        Tuple of (is_valid, datetime_object)
    """
    if not fecha_str:
        return False, None

    # Try common date formats
    formats = [
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%d.%m.%Y',
        '%Y-%m-%d',
        '%Y/%m/%d'
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(fecha_str, fmt)

            # Check if date is not in the future (for birth dates)
            if dt > datetime.now():
                return False, None

            # Check if date is reasonable (not too old)
            if dt.year < 1900:
                return False, None

            return True, dt
        except ValueError:
            continue

    return False, None


def clean_text(text: str) -> str:
    """
    Clean OCR text output

    Args:
        text: Raw OCR text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = ' '.join(text.split())

    # Remove common OCR artifacts
    text = text.replace('|', 'I')
    text = text.replace('0', 'O')  # In names, 0 is usually O

    # Convert to uppercase for consistency
    text = text.upper()

    return text.strip()


def extract_cedula_number(text: str) -> Optional[str]:
    """
    Extract cedula number from text using regex

    Args:
        text: Text containing cedula

    Returns:
        Extracted cedula number or None
    """
    # Pattern for Venezuelan cedula: [V|E|J|G|P]-XX.XXX.XXX
    patterns = [
        r'[VvEeJjGgPp][-.\s]?\d{1,2}[.\s]?\d{3}[.\s]?\d{3}',
        r'\d{6,8}',  # Just numbers
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    return None


def extract_placa(text: str) -> Optional[str]:
    """
    Extract license plate from text

    Args:
        text: Text containing plate

    Returns:
        Extracted plate or None
    """
    text = text.upper().replace(' ', '').replace('-', '')

    patterns = [
        r'[A-Z]{3}\d{3}',
        r'[A-Z]{2}\d{3}[A-Z]{2}',
        r'[A-Z]{3}\d{3}[A-Z]'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    return None
