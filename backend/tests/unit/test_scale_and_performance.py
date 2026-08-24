import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.services.health_aggregation import (
    CentralHealthService,
    RegionalHealthAgent,
    RegionalHealthReport,
)
from app.services.stream_gateway_service import StreamProfileManager, stream_gateway_service


def test_stream_profile_manager_defaults():
    """Verify StreamProfileManager delivers appropriate bandwidth presets."""
    mgr = StreamProfileManager()
    low = mgr.get_profile("LOW")
    med = mgr.get_profile("MEDIUM")
    high = mgr.get_profile("HIGH")
    burst = mgr.get_profile("BURST_TRACKING")

    assert low.bitrate_kbps == 500
    assert med.bitrate_kbps == 1500
    assert high.bitrate_kbps == 4000
    assert burst.bitrate_kbps == 6000
    assert med.fps == 20
    assert high.fps == 25


def test_bandwidth_mathematical_sizing_model():
    """Verify mathematical raw video vs metadata bandwidth formulas."""
    mgr = StreamProfileManager()

    # Stage 1: 50 cameras (PoC)
    poc_raw = mgr.calculate_raw_video_bandwidth_mbps(50, "MEDIUM")
    assert poc_raw == 75.0  # 50 * 1.5 Mbps
    poc_meta = mgr.calculate_metadata_bandwidth_mbps(50, detections_per_second_per_cam=0.2)
    assert poc_meta > 0.0

    # Stage 2: 500 cameras (Pilot)
    pilot_raw = mgr.calculate_raw_video_bandwidth_mbps(500, "MEDIUM")
    assert pilot_raw == 750.0

    # Stage 3: 5,000 cameras (Regional)
    regional_raw = mgr.calculate_raw_video_bandwidth_mbps(5000, "MEDIUM")
    assert regional_raw == 7500.0

    # Stage 4: 80,000 cameras (Statewide Target)
    statewide_raw = mgr.calculate_raw_video_bandwidth_mbps(80000, "MEDIUM")
    assert statewide_raw == 120000.0  # 120 Gbps raw video

    # Metadata only central egress (80,000 cameras * 0.2 detections/sec * 1200 bytes)
    # = 16,000 events/sec * 1200 bytes = 19.2 MB/sec = ~146.5 Mbps
    statewide_meta = mgr.calculate_metadata_bandwidth_mbps(80000, detections_per_second_per_cam=0.2)
    assert 140.0 <= statewide_meta <= 160.0


def test_hierarchical_health_aggregation():
    """Verify regional health agent aggregates camera telemetry into compact summaries."""
    agent = RegionalHealthAgent(region_id="REG-SURAT", zone_name="SOUTH_GUJARAT")

    # Add 100 cameras (95 online, 5 offline)
    for i in range(95):
        agent.record_camera_status(f"CAM-SURAT-{i:04d}", is_online=True, latency_ms=18.5)
    for i in range(95, 100):
        agent.record_camera_status(f"CAM-SURAT-{i:04d}", is_online=False, error="RTSP Stream Timeout")

    report = agent.generate_aggregated_report()
    assert report.total_cameras == 100
    assert report.online_cameras == 95
    assert report.offline_cameras == 5
    assert report.avg_latency_ms == 18.5
    assert len(report.offline_camera_ids) == 5

    # Central Ingestion
    central = CentralHealthService()
    central.ingest_regional_report(report)
    rollup = central.get_statewide_health_rollup()

    assert rollup["total_cameras"] == 100
    assert rollup["online_cameras"] == 95
    assert rollup["statewide_health_score_pct"] == 95.0
    assert rollup["status"] == "HEALTHY"


@pytest.mark.asyncio
async def test_scale_status_api_endpoint(client: AsyncClient):
    """Verify GET /api/v1/cameras/health/scale-status returns node topology and rollup."""
    resp = await client.get("/api/v1/cameras/health/scale-status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert "node_role" in data
    assert "regional_zone" in data
    assert "health_rollup" in data
    assert "active_stream_sessions" in data


@pytest.mark.asyncio
async def test_operational_metrics_api_endpoint(client: AsyncClient):
    """Verify GET /api/v1/cameras/health/metrics returns sizing models and pool stats."""
    resp = await client.get("/api/v1/cameras/health/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert "database_pool" in data
    assert "stream_profiles" in data
    assert "bandwidth_sizing_models" in data
    assert data["bandwidth_sizing_models"]["50_cameras_poc_mbps"] == 75.0


def test_stream_session_tracking():
    """Verify stream gateway tracks active sessions and cleans up on close."""
    gateway = stream_gateway_service
    session_id = f"test-sess-{uuid.uuid4()}"
    gateway.active_sessions[session_id] = {
        "camera_id": "CAM-001",
        "profile": "MEDIUM",
        "created_at": datetime.now(timezone.utc),
        "status": "ACTIVE",
    }
    assert gateway.get_active_session_count() >= 1
    closed = gateway.close_session(session_id)
    assert closed is True
    assert session_id not in gateway.active_sessions
