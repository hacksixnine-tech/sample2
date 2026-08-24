"""
PHANTOM // Hierarchical Health Aggregation & Regional Gateway Health Engine
Enables scalable health monitoring across 80,000 cameras without central polling bottlenecks.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from app.core.config import settings
from app.core.logging import logger


@dataclass
class CameraHealthSummary:
    camera_id: str
    is_online: bool
    latency_ms: Optional[float] = None
    fps: float = 0.0
    error: Optional[str] = None


@dataclass
class RegionalHealthReport:
    region_id: str
    zone_name: str
    reported_at: str
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    degraded_cameras: int
    avg_latency_ms: float
    active_streams: int
    ai_workers_healthy: int
    ai_workers_total: int
    edge_buffer_used_mb: float
    edge_buffer_total_mb: float
    offline_camera_ids: List[str] = field(default_factory=list)


class RegionalHealthAgent:
    """
    Runs at District/Regional Edge Gateways.
    Aggregates local camera and AI telemetry, avoiding statewide central polling traffic.
    """

    def __init__(self, region_id: str = "REG-AHMEDABAD", zone_name: str = "CENTRAL_GUJARAT"):
        self.region_id = region_id
        self.zone_name = zone_name
        self._local_cameras: Dict[str, CameraHealthSummary] = {}
        self.ai_workers_healthy: int = 4
        self.ai_workers_total: int = 4
        self.edge_buffer_used_mb: float = 124.5
        self.edge_buffer_total_mb: float = float(settings.EDGE_BUFFER_MAX_MB)

    def record_camera_status(
        self,
        camera_id: str,
        is_online: bool,
        latency_ms: Optional[float] = None,
        fps: float = 25.0,
        error: Optional[str] = None,
    ):
        self._local_cameras[camera_id] = CameraHealthSummary(
            camera_id=camera_id,
            is_online=is_online,
            latency_ms=latency_ms,
            fps=fps if is_online else 0.0,
            error=error,
        )

    def generate_aggregated_report(self) -> RegionalHealthReport:
        total = len(self._local_cameras)
        if total == 0:
            return RegionalHealthReport(
                region_id=self.region_id,
                zone_name=self.zone_name,
                reported_at=datetime.now(timezone.utc).isoformat(),
                total_cameras=0,
                online_cameras=0,
                offline_cameras=0,
                degraded_cameras=0,
                avg_latency_ms=0.0,
                active_streams=0,
                ai_workers_healthy=self.ai_workers_healthy,
                ai_workers_total=self.ai_workers_total,
                edge_buffer_used_mb=self.edge_buffer_used_mb,
                edge_buffer_total_mb=self.edge_buffer_total_mb,
            )

        online_count = 0
        offline_count = 0
        degraded_count = 0
        latencies = []
        offline_ids = []

        for cam in self._local_cameras.values():
            if cam.is_online:
                if cam.latency_ms and cam.latency_ms > 500:
                    degraded_count += 1
                else:
                    online_count += 1
                if cam.latency_ms is not None:
                    latencies.append(cam.latency_ms)
            else:
                offline_count += 1
                offline_ids.append(cam.camera_id)

        avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        return RegionalHealthReport(
            region_id=self.region_id,
            zone_name=self.zone_name,
            reported_at=datetime.now(timezone.utc).isoformat(),
            total_cameras=total,
            online_cameras=online_count,
            offline_cameras=offline_count,
            degraded_cameras=degraded_count,
            avg_latency_ms=avg_lat,
            active_streams=online_count + degraded_count,
            ai_workers_healthy=self.ai_workers_healthy,
            ai_workers_total=self.ai_workers_total,
            edge_buffer_used_mb=self.edge_buffer_used_mb,
            edge_buffer_total_mb=self.edge_buffer_total_mb,
            offline_camera_ids=offline_ids[:100],  # Bound payload
        )


class CentralHealthService:
    """
    Central Health Aggregator that ingests regional summaries and maintains statewide telemetry.
    """

    def __init__(self):
        self._regional_reports: Dict[str, RegionalHealthReport] = {}
        self._last_heartbeats: Dict[str, datetime] = {}

    def ingest_regional_report(self, report: RegionalHealthReport):
        self._regional_reports[report.region_id] = report
        self._last_heartbeats[report.region_id] = datetime.now(timezone.utc)

    def get_statewide_health_rollup(self) -> Dict[str, Any]:
        total_cams = 0
        online_cams = 0
        offline_cams = 0
        degraded_cams = 0
        all_latencies = []
        active_streams = 0
        total_ai_healthy = 0
        total_ai_workers = 0

        for r in self._regional_reports.values():
            total_cams += r.total_cameras
            online_cams += r.online_cameras
            offline_cams += r.offline_cameras
            degraded_cams += r.degraded_cameras
            active_streams += r.active_streams
            total_ai_healthy += r.ai_workers_healthy
            total_ai_workers += r.ai_workers_total
            if r.avg_latency_ms > 0:
                all_latencies.append(r.avg_latency_ms)

        statewide_avg_latency = (
            round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else 0.0
        )
        health_score_pct = (
            round((online_cams / total_cams) * 100, 1) if total_cams > 0 else 100.0
        )

        return {
            "status": "HEALTHY" if health_score_pct >= 90.0 else "DEGRADED",
            "statewide_health_score_pct": health_score_pct,
            "total_cameras": total_cams,
            "online_cameras": online_cams,
            "offline_cameras": offline_cams,
            "degraded_cameras": degraded_cams,
            "active_streams": active_streams,
            "statewide_avg_latency_ms": statewide_avg_latency,
            "ai_workers": {
                "healthy": total_ai_healthy,
                "total": total_ai_workers,
                "status": "HEALTHY" if total_ai_healthy == total_ai_workers else "DEGRADED",
            },
            "connected_regions_count": len(self._regional_reports),
            "regions": [
                {
                    "region_id": r.region_id,
                    "zone_name": r.zone_name,
                    "total_cameras": r.total_cameras,
                    "online": r.online_cameras,
                    "offline": r.offline_cameras,
                    "avg_latency_ms": r.avg_latency_ms,
                    "reported_at": r.reported_at,
                }
                for r in self._regional_reports.values()
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


regional_health_agent = RegionalHealthAgent()
central_health_service = CentralHealthService()
