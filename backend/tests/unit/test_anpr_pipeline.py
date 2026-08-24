import pytest
from app.ai.anpr.normalize import (
    extract_plate_structure,
    is_gujarat_plate,
    looks_like_indian_plate,
    normalize_plate_text,
)
from app.ai.anpr.ocr import NullOCRProcessor, build_ocr_processor
from app.ai.interfaces import PlateOCRResult
from app.ai.postprocessing.validation import meets_ocr_threshold, validate_confidence


def test_plate_normalization_standard_clean():
    # Basic cleanup
    assert normalize_plate_text("GJ01AB1234") == "GJ01AB1234"
    assert normalize_plate_text("gj01ab1234") == "GJ01AB1234"
    
    # Whitespace and punctuation stripping
    assert normalize_plate_text(" GJ 05 AB 1234 ") == "GJ05AB1234"
    assert normalize_plate_text("GJ-01-AB-1234") == "GJ01AB1234"
    assert normalize_plate_text("GJ.06.M.9999") == "GJ06M9999"
    assert normalize_plate_text("GJ_18_Z_0001") == "GJ18Z0001"
    
    # None handling
    assert normalize_plate_text(None) == ""
    assert normalize_plate_text("") == ""


def test_plate_normalization_bharat_series():
    assert normalize_plate_text("22 BH 1234 AA") == "22BH1234AA"
    assert normalize_plate_text("21-BH-9999-Z") == "21BH9999Z"


def test_looks_like_indian_plate():
    # Valid State formats
    assert looks_like_indian_plate("GJ01AB1234") is True
    assert looks_like_indian_plate("GJ05M9999") is True
    assert looks_like_indian_plate("MH12DE1433") is True
    assert looks_like_indian_plate("DL10CA0001") is True
    assert looks_like_indian_plate("GJ1A1234") is True

    # Valid Bharat series
    assert looks_like_indian_plate("22BH1234AA") is True
    assert looks_like_indian_plate("21BH9999Z") is True

    # Invalid noise
    assert looks_like_indian_plate("INVALID_PLATE_TEXT") is False
    assert looks_like_indian_plate("12345") is False
    assert looks_like_indian_plate("") is False
    assert looks_like_indian_plate(None) is False


def test_is_gujarat_plate():
    assert is_gujarat_plate("GJ01AB1234") is True
    assert is_gujarat_plate("GJ05M9999") is True
    assert is_gujarat_plate("MH12DE1433") is False
    assert is_gujarat_plate("22BH1234AA") is False
    assert is_gujarat_plate("") is False
    assert is_gujarat_plate(None) is False


def test_extract_plate_structure():
    # Gujarat Standard Format
    struct_gj = extract_plate_structure("GJ05AB1234")
    assert struct_gj["format"] == "STANDARD"
    assert struct_gj["state_code"] == "GJ"
    assert struct_gj["rto_code"] == "05"
    assert struct_gj["series"] == "AB"
    assert struct_gj["number"] == "1234"
    assert struct_gj["rto_jurisdiction"] == "Surat"
    assert struct_gj["is_gujarat"] is True

    # Ahmedabad East (GJ27)
    struct_ah = extract_plate_structure("GJ27C5555")
    assert struct_ah["rto_code"] == "27"
    assert struct_ah["rto_jurisdiction"] == "Ahmedabad East"

    # Bharat Series
    struct_bh = extract_plate_structure("22BH1234AA")
    assert struct_bh["format"] == "BHARAT_SERIES"
    assert struct_bh["state_code"] == "BH"
    assert struct_bh["number"] == "1234"
    assert struct_bh["series"] == "AA"
    assert struct_bh["is_gujarat"] is False


from app.core.exceptions import ValidationError


def test_confidence_threshold_and_validation():
    assert validate_confidence(0.95) == 0.95
    assert validate_confidence(0.0) == 0.0
    assert validate_confidence(1.0) == 1.0

    with pytest.raises((ValidationError, ValueError)):
        validate_confidence(-0.1)
    with pytest.raises((ValidationError, ValueError)):
        validate_confidence(1.05)

    assert meets_ocr_threshold(0.92, 0.80) is True
    assert meets_ocr_threshold(0.79, 0.80) is False
    assert meets_ocr_threshold(None, 0.80) is False


def test_ocr_processor_fallback():
    proc = NullOCRProcessor()
    res = proc.read_text(None)
    assert isinstance(res, PlateOCRResult)
    assert res.raw_text == ""
    assert res.normalized_text == ""
    assert res.confidence == 0.0

    demo_proc = build_ocr_processor(prefer_demo=True)
    demo_res = demo_proc.read_text(None)
    assert demo_res.confidence > 0.80
    assert "GJ" in demo_res.normalized_text
