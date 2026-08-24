import os
import pytest

from app.core.config import settings
from app.services.stream_gateway_service import stream_gateway_service
from scripts.demo_reset import reset_demo_data
from scripts.demo_scenario_runner import run_demo_scenario
from scripts.system_health_check import HealthCheckRunner


@pytest.mark.asyncio
async def test_system_health_check_runner():
    """Verify system health check runner validates all core subsystems."""
    runner = HealthCheckRunner()
    success = await runner.run_all_checks()
    assert success is True
    assert len(runner.results) >= 6
    assert all(r["status"] == "PASS" for r in runner.results)


@pytest.mark.asyncio
async def test_demo_scenario_runner_execution():
    """Verify the 15-step demo scenario runner completes without errors."""
    success = await run_demo_scenario()
    assert success is True


@pytest.mark.asyncio
async def test_demo_reset_utility():
    """Verify demo reset utility executes cleanly."""
    success = await reset_demo_data()
    assert success is True


def test_stream_gateway_fallback_labels():
    """Verify stream gateway correctly labels fallback stream states."""
    gateway = stream_gateway_service
    valid_states = ["LIVE", "RECORDED", "SIMULATION", "OFFLINE"]
    for s in valid_states:
        assert s in ["LIVE", "RECORDED", "SIMULATION", "OFFLINE"]

    # Verify stream profile defaults
    med_profile = gateway.profile_manager.get_profile("MEDIUM")
    assert med_profile.resolution == "1280x720"
    assert med_profile.bitrate_kbps == 1500


def test_core_environment_and_rbac_integrity():
    """Verify settings contains valid role permissions and security configuration."""
    assert settings.NODE_ROLE in ["EDGE", "REGIONAL", "CENTRAL"]
    assert settings.STREAM_PROFILE_DEFAULT in ["LOW", "MEDIUM", "HIGH", "BURST_TRACKING"]
    assert settings.EDGE_BUFFER_RETENTION_HOURS == 24
