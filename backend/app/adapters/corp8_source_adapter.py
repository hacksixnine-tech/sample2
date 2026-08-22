from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional
import httpx

from app.adapters.base_source_adapter import BaseSourceAdapter
from app.core.exceptions import DatabaseConnectionError, NotFoundError
from app.core.logging import logger
from app.schemas.source_system import DiscoveredStream, SourceDiscoveryCamera

# Known Gujarat districts for heuristic resolution from raw location text
GUJARAT_DISTRICTS = [
    "Ahmedabad", "Gandhinagar", "Surat", "Vadodara", "Rajkot", "Junagadh",
    "Navsari", "Patan", "Gir Somnath", "Kutch", "Kachchh", "Bhavnagar",
    "Jamnagar", "Banaskantha", "Panchmahal", "Anand", "Kheda", "Mehsana",
    "Dahod", "Bharuch", "Valsad", "Amreli", "Porbandar", "Surendranagar",
    "Morbi", "Botad", "Aravalli", "Mahisagar", "Chhotaudepur", "Narmada",
    "Tapi", "Dang", "Devbhumi Dwarka"
]


class Corp8SourceAdapter(BaseSourceAdapter):
    """
    Production adapter for the official Hackathon-provided CCTV Control Room source (live.corp8.cloud).
    Discovers live multi-protocol streams (RTSP, WebRTC/WHEP, HLS) and camera telemetry.
    """

    def _infer_district_and_city(self, location_str: Optional[str]) -> tuple[str, str]:
        if not location_str:
            return "UNKNOWN", "UNKNOWN"

        loc_lower = location_str.lower()
        for dist in GUJARAT_DISTRICTS:
            if dist.lower() in loc_lower:
                return dist, dist

        # Specific city/junction keyword heuristics
        if "adalaj" in loc_lower or "dehgam" in loc_lower:
            return "Gandhinagar", "Gandhinagar"
        if "bilimora" in loc_lower or "gandevi" in loc_lower:
            return "Navsari", "Bilimora"
        if "gandhidham" in loc_lower:
            return "Kutch", "Gandhidham"
        if "chiman bhai" in loc_lower or "janpath" in loc_lower or "paldi" in loc_lower or "visat" in loc_lower:
            return "Ahmedabad", "Ahmedabad"

        return "UNKNOWN", "UNKNOWN"

    async def probe(self, base_url: str, auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Probes live health and connectivity of live.corp8.cloud."""
        clean_base = base_url.rstrip("/")
        api_url = f"{clean_base}/api/cameras"

        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.get(api_url)
                    if res.status_code == 200:
                        data = res.json()
                        catalog = data.get("catalog", {})
                        cameras = data.get("cameras", [])
                        return {
                            "accessible": True,
                            "status_code": res.status_code,
                            "catalog_state": catalog.get("state", "ready"),
                            "total_cameras": len(cameras),
                            "latency_ms": round(res.elapsed.total_seconds() * 1000, 2),
                        }
                    return {
                        "accessible": False,
                        "status_code": res.status_code,
                        "error": f"HTTP {res.status_code}",
                    }
            except Exception as ex:
                if attempt == 1:
                    logger.warning(f"Failed to probe CCTV source {base_url}: {str(ex)}")
                    return {
                        "accessible": False,
                        "error": str(ex),
                    }

    async def discover_cameras(
        self, base_url: str, auth_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetches the complete camera catalog from the external source,
        extracting all available RTSP, WebRTC, and HLS stream references.
        """
        clean_base = base_url.rstrip("/")
        api_url = f"{clean_base}/api/cameras"

        last_error = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    res = await client.get(api_url)
                    if res.status_code != 200:
                        raise RuntimeError(f"Source returned HTTP {res.status_code}: {res.text}")

                    data = res.json()
                    raw_cameras = data.get("cameras", [])
                    catalog = data.get("catalog", {})

                    discovered_cameras: List[SourceDiscoveryCamera] = []

                    for raw in raw_cameras:
                        cam_id = str(raw.get("id"))
                        cam_name = str(raw.get("name") or f"Camera {cam_id}")
                        raw_loc = raw.get("location")
                        district, city = self._infer_district_and_city(raw_loc)

                        # Extract streams
                        streams: List[DiscoveredStream] = []
                        width = int(raw.get("width", 0) or 0)
                        height = int(raw.get("height", 0) or 0)
                        res_label = f"{width}x{height}" if width and height else "1080p"
                        fps = float(raw.get("fps", 0.0) or 25.0)
                        if fps <= 0:
                            fps = 25.0
                        codec = str(raw.get("codec") or "H264").upper()
                        bitrate = int(raw.get("bitrate_kbps", 0) or 0)

                        # 1. RTSP Stream
                        rtsp_url = raw.get("rtsp_url")
                        if rtsp_url:
                            streams.append(
                                DiscoveredStream(
                                    protocol="RTSP",
                                    stream_url=rtsp_url,
                                    resolution=res_label,
                                    fps=fps,
                                    codec=codec,
                                    bitrate_kbps=bitrate if bitrate > 0 else None,
                                    is_primary=True,
                                )
                            )

                        # 2. WebRTC / WHEP Stream
                        webrtc_url = raw.get("webrtc_url")
                        if webrtc_url:
                            streams.append(
                                DiscoveredStream(
                                    protocol="WEBRTC",
                                    stream_url=webrtc_url,
                                    resolution=res_label,
                                    fps=fps,
                                    codec=codec,
                                    bitrate_kbps=bitrate if bitrate > 0 else None,
                                    is_primary=False,
                                )
                            )

                        # 3. HLS Live Stream
                        hls_rel = raw.get("hls_live_url")
                        if hls_rel:
                            hls_url = f"{clean_base}{hls_rel}" if hls_rel.startswith("/") else hls_rel
                            streams.append(
                                DiscoveredStream(
                                    protocol="HLS",
                                    stream_url=hls_url,
                                    resolution=res_label,
                                    fps=fps,
                                    codec=codec,
                                    bitrate_kbps=bitrate if bitrate > 0 else None,
                                    is_primary=False,
                                )
                            )

                        discovered_cameras.append(
                            SourceDiscoveryCamera(
                                source_camera_id=cam_id,
                                number=raw.get("number"),
                                name=cam_name,
                                raw_location_string=raw_loc,
                                inferred_district=district,
                                inferred_city=city,
                                status=str(raw.get("status") or "live").upper(),
                                delivery=str(raw.get("delivery") or "rtsp").upper(),
                                streams=streams,
                                raw_metadata=raw,
                            )
                        )

                    return {
                        "catalog_state": catalog.get("state", "ready"),
                        "scanned_at": datetime.now(timezone.utc),
                        "total_discovered": len(discovered_cameras),
                        "cameras": discovered_cameras,
                    }
            except Exception as ex:
                last_error = ex
                logger.warning(f"Attempt {attempt+1} failed discovering cameras from {base_url}: {ex}")

        raise RuntimeError(f"Could not reach external CCTV source at {base_url}: {last_error}")
