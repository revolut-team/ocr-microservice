"""
Tests for document parsers
"""
import pytest
from app.services.cedula_parser import CedulaParser
from app.services.vehicle_doc_parser import VehicleDocParser


class TestCedulaParser:
    """Test cedula document parser"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return CedulaParser()

    @pytest.fixture
    def sample_detections(self):
        """Create sample OCR detections for a cedula"""
        return [
            # Format: [[bbox], (text, confidence)]
            [[[10, 10], [100, 10], [100, 30], [10, 30]], ("REPÚBLICA", 0.95)],
            [[[10, 40], [120, 40], [120, 60], [10, 60]], ("BOLIVARIANA", 0.93)],
            [[[10, 70], [100, 70], [100, 90], [10, 90]], ("VENEZUELA", 0.94)],
            [[[200, 100], [350, 100], [350, 130], [200, 130]], ("V-12.345.678", 0.98)],
            [[[200, 140], [350, 140], [350, 165], [200, 165]], ("JUAN CARLOS", 0.91)],
            [[[200, 175], [350, 175], [350, 200], [200, 200]], ("PÉREZ GÓMEZ", 0.93)],
            [[[200, 210], [300, 210], [300, 230], [200, 230]], ("15/03/1990", 0.89)],
        ]

    def test_parser_initialization(self, parser):
        """Test parser initialization"""
        assert parser is not None
        assert parser.min_confidence > 0

    def test_parse_cedula(self, parser, sample_detections):
        """Test parsing cedula data"""
        result = parser.parse(sample_detections)

        assert result is not None
        assert result.numero_cedula is not None
        assert result.confidence.overall > 0

    def test_extract_cedula_number(self, parser):
        """Test extracting cedula number"""
        texts = [
            ("V-12.345.678", 0.98, [[0, 0], [100, 0], [100, 20], [0, 20]]),
            ("Some text", 0.85, [[0, 30], [100, 30], [100, 50], [0, 50]])
        ]

        result = parser._extract_cedula(texts)
        assert result is not None
        assert result['numero_cedula'] == "12345678"
        assert result['tipo'] == "V"


class TestVehicleDocParser:
    """Test vehicle document parser"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return VehicleDocParser()

    @pytest.fixture
    def sample_detections(self):
        """Create sample OCR detections for a vehicle document"""
        return [
            [[[10, 10], [100, 10], [100, 30], [10, 30]], ("CARNET", 0.94)],
            [[[10, 40], [120, 40], [120, 60], [10, 60]], ("CIRCULACIÓN", 0.92)],
            [[[10, 80], [60, 80], [60, 95], [10, 95]], ("PLACA", 0.96)],
            [[[70, 80], [130, 80], [130, 95], [70, 95]], ("ABC123", 0.98)],
            [[[10, 110], [60, 110], [60, 125], [10, 125]], ("MARCA", 0.95)],
            [[[70, 110], [140, 110], [140, 125], [70, 125]], ("TOYOTA", 0.94)],
            [[[10, 140], [70, 140], [70, 155], [10, 155]], ("MODELO", 0.93)],
            [[[80, 140], [160, 140], [160, 155], [80, 155]], ("COROLLA", 0.91)],
            [[[10, 170], [50, 170], [50, 185], [10, 185]], ("AÑO", 0.96)],
            [[[60, 170], [100, 170], [100, 185], [60, 185]], ("2020", 0.97)],
        ]

    def test_parser_initialization(self, parser):
        """Test parser initialization"""
        assert parser is not None
        assert len(parser.BRANDS) > 0
        assert len(parser.COLORS) > 0

    def test_parse_vehicle(self, parser, sample_detections):
        """Test parsing vehicle data"""
        result = parser.parse(sample_detections)

        assert result is not None
        assert result.placa is not None or result.marca is not None
        assert result.confidence.overall > 0

    def test_extract_placa(self, parser):
        """Test extracting placa"""
        texts = [
            ("PLACA", 0.96, [[0, 0], [50, 0], [50, 20], [0, 20]]),
            ("ABC123", 0.98, [[60, 0], [120, 0], [120, 20], [60, 20]])
        ]

        result = parser._extract_placa(texts)
        assert result is not None
        assert result['placa'] == "ABC123"

    def test_extract_brand(self, parser):
        """Test extracting vehicle brand"""
        texts = [
            ("MARCA", 0.95, [[0, 0], [50, 0], [50, 20], [0, 20]]),
            ("TOYOTA", 0.94, [[60, 0], [120, 0], [120, 20], [60, 20]])
        ]

        result = parser._extract_marca(texts)
        assert result is not None
        assert result['marca'] == "TOYOTA"
