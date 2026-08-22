import ipaddress
import re
from typing import Optional, Set
from urllib.parse import urlparse

BLOCKED_HOSTNAMES: Set[str] = {
    "169.254.169.254",
    "metadata.google.internal",
    "instance-data",
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
}

ALLOWED_SCHEMES: Set[str] = {
    "http",
    "https",
    "rtsp",
    "rtsps",
    "rtmp",
    "rtmps",
    "srt",
    "hls",
    "webrtc",
    "whep",
}


def validate_safe_url(url: str, allow_localhost_in_dev: bool = True) -> str:
    """
    Validates that a URL does not point to internal metadata endpoints or dangerous network targets.
    Prevents Server-Side Request Forgery (SSRF) while supporting legitimate CCTV streaming endpoints.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    clean_url = url.strip()
    try:
        parsed = urlparse(clean_url)
    except Exception as e:
        raise ValueError(f"Malformed URL structure: {str(e)}")

    if not parsed.scheme or parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError(
            f"Unsupported or dangerous URL scheme: {parsed.scheme}. Allowed: {sorted(ALLOWED_SCHEMES)}"
        )

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValueError("URL must contain a valid hostname or IP address")

    # Check blocked hostnames (cloud metadata & sensitive internal IPs)
    if hostname in {"169.254.169.254", "metadata.google.internal", "instance-data"}:
        raise ValueError(f"Access to cloud metadata endpoint '{hostname}' is strictly prohibited.")

    if not allow_localhost_in_dev and hostname in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        raise ValueError(f"Access to localhost/loopback address '{hostname}' is not permitted.")

    # Check for link-local or metadata IP addresses
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_link_local:
            raise ValueError(f"Link-local IP address '{hostname}' is not permitted.")
    except ValueError:
        # Not an IP literal (regular domain name)
        pass

    return clean_url


def validate_gujarat_coordinates(latitude: float, longitude: float) -> None:
    """
    Validates that geographical coordinates are within standard ranges.
    """
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError(f"Latitude {latitude} out of valid range [-90.0, 90.0]")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"Longitude {longitude} out of valid range [-180.0, 180.0]")
