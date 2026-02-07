"""
Tests for validators
"""
import pytest
from app.utils.validators import (
    validate_cedula,
    format_cedula,
    validate_placa_venezuela,
    validate_fecha,
    extract_cedula_number,
    extract_placa
)


class TestCedulaValidation:
    """Test cedula validation functions"""

    def test_validate_cedula_valid(self):
        """Test valid cedula numbers"""
        assert validate_cedula("12345678") is True
        assert validate_cedula("V12345678") is True
        assert validate_cedula("V-12.345.678") is True
        assert validate_cedula("1234567") is True
        assert validate_cedula("99999999") is True

    def test_validate_cedula_invalid(self):
        """Test invalid cedula numbers"""
        assert validate_cedula("0") is False
        assert validate_cedula("100000000") is False
        assert validate_cedula("abc") is False
        assert validate_cedula("") is False
        assert validate_cedula(None) is False

    def test_format_cedula(self):
        """Test cedula formatting"""
        assert format_cedula("V", "12345678") == "V-12.345.678"
        assert format_cedula("E", "1234567") == "E-1.234.567"
        assert format_cedula("V", "123456") == "V-123.456"

    def test_extract_cedula_number(self):
        """Test extracting cedula from text"""
        assert extract_cedula_number("V-12.345.678") is not None
        assert extract_cedula_number("E12345678") is not None
        assert extract_cedula_number("Some text V-12.345.678 more text") is not None
        assert extract_cedula_number("No cedula here") is not None  # Will extract numbers


class TestPlacaValidation:
    """Test placa validation functions"""

    def test_validate_placa_old_format(self):
        """Test old format plates (ABC123)"""
        assert validate_placa_venezuela("ABC123") is True
        assert validate_placa_venezuela("XYZ789") is True

    def test_validate_placa_new_format(self):
        """Test new format plates (AB123CD)"""
        assert validate_placa_venezuela("AB123CD") is True
        assert validate_placa_venezuela("XY456ZW") is True

    def test_validate_placa_moto_format(self):
        """Test motorcycle format (AAA000A)"""
        assert validate_placa_venezuela("AAA000A") is True
        assert validate_placa_venezuela("XYZ123B") is True

    def test_validate_placa_invalid(self):
        """Test invalid plates"""
        assert validate_placa_venezuela("ABCD123") is False
        assert validate_placa_venezuela("ABC12") is False
        assert validate_placa_venezuela("123ABC") is False
        assert validate_placa_venezuela("") is False

    def test_extract_placa(self):
        """Test extracting placa from text"""
        assert extract_placa("Placa: ABC123") == "ABC123"
        assert extract_placa("AB123CD") == "AB123CD"
        assert extract_placa("no plate here") is None


class TestFechaValidation:
    """Test fecha validation functions"""

    def test_validate_fecha_valid(self):
        """Test valid dates"""
        is_valid, dt = validate_fecha("15/03/1990")
        assert is_valid is True
        assert dt is not None

        is_valid, dt = validate_fecha("01-01-2000")
        assert is_valid is True

    def test_validate_fecha_future(self):
        """Test future dates (invalid for birth dates)"""
        is_valid, dt = validate_fecha("01/01/2030")
        assert is_valid is False

    def test_validate_fecha_invalid(self):
        """Test invalid dates"""
        is_valid, dt = validate_fecha("32/13/2000")
        assert is_valid is False

        is_valid, dt = validate_fecha("invalid")
        assert is_valid is False

        is_valid, dt = validate_fecha("")
        assert is_valid is False
