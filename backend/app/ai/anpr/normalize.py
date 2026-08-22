import re
from typing import Optional

# Keep raw OCR text. Only apply formatting cleanup that cannot invent a different plate.
_STRIP_CHARS = re.compile(r"[^A-Za-z0-9]")


def normalize_plate_text(raw: Optional[str]) -> str:
    """Uppercase and strip spaces/hyphens/punctuation. Does not substitute look-alike characters."""
    if raw is None:
        return ""
    return _STRIP_CHARS.sub("", str(raw)).upper()


def looks_like_indian_plate(normalized: str) -> bool:
    """Heuristic for Indian registration format (e.g. GJ01AB1234). Not a legal validity check."""
    return bool(re.fullmatch(r"[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{1,4}", normalized or ""))
