import re
from typing import Dict, Optional, Tuple

# Strip all non-alphanumeric noise (spaces, hyphens, dots, underscores, special characters)
_STRIP_CHARS = re.compile(r"[^A-Za-z0-9]")

# Standard State format: State (2 letters) + RTO (1-2 digits) + Series (0-3 letters) + Number (1-4 digits)
_STD_INDIAN_PLATE = re.compile(r"^([A-Z]{2})([0-9]{1,2})([A-Z]{0,3})([0-9]{1,4})$")

# Bharat Series: Year (2 digits) + BH + Number (4 digits) + Letters (1-2 letters)
_BH_SERIES_PLATE = re.compile(r"^([0-9]{2})(BH)([0-9]{4})([A-Z]{1,2})$")

# Gujarat specific State Codes
GUJARAT_RTO_CODES = {
    "01": "Ahmedabad", "02": "Mehsana", "03": "Rajkot", "04": "Bhavnagar",
    "05": "Surat", "06": "Vadodara", "07": "Nadiad/Kheda", "08": "Palanpur/Banaskantha",
    "09": "Himmatnagar/Sabar Kantha", "10": "Jamnagar", "11": "Junagadh",
    "12": "Bhuj/Kutch", "13": "Surendranagar", "14": "Amreli", "15": "Valsad",
    "16": "Bharuch", "17": "Godhra/Panchmahal", "18": "Gandhinagar", "19": "Bardoli",
    "20": "Dahod", "21": "Navsari", "22": "Rajpipla/Narmada", "23": "Anand",
    "24": "Patan", "25": "Porbandar", "26": "Vyara/Tapi", "27": "Ahmedabad East",
    "28": "Surat West", "29": "Vadodara Rural", "30": "Dang/Ahwa", "31": "Modasa/Aravalli",
    "32": "Veraval/Gir Somnath", "33": "Botad", "34": "Chhota Udepur", "35": "Lunawada/Mahisagar",
    "36": "Morbi", "37": "Khambhalia/Devbhumi Dwarka", "38": "Bavla/Ahmedabad Rural",
}


def normalize_plate_text(raw: Optional[str]) -> str:
    """Uppercase and strip spaces/hyphens/punctuation.
    
    Deterministic formatting cleanup that strictly preserves alphanumeric characters
    without fabricating characters.
    """
    if raw is None:
        return ""
    return _STRIP_CHARS.sub("", str(raw)).strip().upper()


def looks_like_indian_plate(normalized: str) -> bool:
    """Check if normalized string matches Indian vehicle registration pattern (State or BH series)."""
    if not normalized:
        return False
    norm = normalized.strip().upper()
    return bool(_STD_INDIAN_PLATE.fullmatch(norm) or _BH_SERIES_PLATE.fullmatch(norm))


def is_gujarat_plate(normalized: str) -> bool:
    """Check if plate belongs to Gujarat state registration (GJ prefix)."""
    if not normalized:
        return False
    return normalized.strip().upper().startswith("GJ")


def extract_plate_structure(normalized: str) -> Dict[str, Optional[str]]:
    """Extract state code, district RTO code, series, and registration number."""
    norm = (normalized or "").strip().upper()
    
    # Check Standard State Format (e.g. GJ05AB1234)
    m = _STD_INDIAN_PLATE.fullmatch(norm)
    if m:
        state, rto, series, number = m.groups()
        rto_padded = rto.zfill(2)
        rto_name = GUJARAT_RTO_CODES.get(rto_padded) if state == "GJ" else None
        return {
            "format": "STANDARD",
            "state_code": state,
            "rto_code": rto_padded,
            "series": series or "",
            "number": number,
            "rto_jurisdiction": rto_name,
            "is_gujarat": state == "GJ",
        }
        
    # Check BH Series (e.g. 22BH1234AA)
    m_bh = _BH_SERIES_PLATE.fullmatch(norm)
    if m_bh:
        year, bh, number, letters = m_bh.groups()
        return {
            "format": "BHARAT_SERIES",
            "state_code": "BH",
            "rto_code": year,
            "series": letters,
            "number": number,
            "rto_jurisdiction": "All-India Defense / Multi-State Commercial",
            "is_gujarat": False,
        }
        
    return {
        "format": "UNKNOWN",
        "state_code": norm[:2] if len(norm) >= 2 and norm[:2].isalpha() else None,
        "rto_code": None,
        "series": None,
        "number": None,
        "rto_jurisdiction": None,
        "is_gujarat": norm.startswith("GJ"),
    }

