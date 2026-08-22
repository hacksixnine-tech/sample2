from app.ai.anpr.normalize import normalize_plate_text
from app.ai.interfaces import OCRProcessor, PlateOCRResult


class NullOCRProcessor:
    """Safe fallback when no OCR backend is installed. Does not invent plates."""

    def read_text(self, plate_crop) -> PlateOCRResult:
        return PlateOCRResult(raw_text="", normalized_text="", confidence=0.0)


class EasyOCRProcessor:
    def __init__(self):
        import easyocr  # type: ignore

        self.reader = easyocr.Reader(["en"], gpu=False)

    def read_text(self, plate_crop) -> PlateOCRResult:
        if plate_crop is None:
            return PlateOCRResult(raw_text="", normalized_text="", confidence=0.0)
        results = self.reader.readtext(plate_crop)
        if not results:
            return PlateOCRResult(raw_text="", normalized_text="", confidence=0.0)
        text, conf = max(((r[1], float(r[2])) for r in results), key=lambda x: x[1])
        return PlateOCRResult(raw_text=text, normalized_text=normalize_plate_text(text), confidence=conf)


def build_ocr_processor(prefer_demo: bool = False) -> OCRProcessor:
    if prefer_demo:
        from app.ai.detection.engines import DemoOCRProcessor

        return DemoOCRProcessor()
    try:
        return EasyOCRProcessor()
    except Exception:
        return NullOCRProcessor()
