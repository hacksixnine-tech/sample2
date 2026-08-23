import pytest
from app.services.stream_gateway_service import StreamGatewayService, Corp8StreamProvider

@pytest.mark.asyncio
async def test_stream_gateway_resolve_stream():
    service = StreamGatewayService()
    res = await service.resolve_stream(camera_id="CAM-13", protocol="HLS")
    assert res is not None
    assert res["camera_id"] == "CAM-13"
    assert "https://live.corp8.cloud/stream/13" in res["browser_playback_url"]
    assert res["is_direct_browser_supported"] is True
    assert "session_id" in res
    assert res["session_id"] in service.active_sessions

    # Test closing session
    closed = service.close_session(res["session_id"])
    assert closed is True
    assert res["session_id"] not in service.active_sessions


@pytest.mark.asyncio
async def test_corp8_provider_resolve():
    provider = Corp8StreamProvider()
    res = await provider.resolve_browser_stream(
        camera_id="14",
        raw_stream_url="",
        protocol="HLS",
    )
    assert res["browser_playback_url"] == "https://live.corp8.cloud/stream/14"
    assert res["webrtc_fallback_url"] == "http://live.corp8.cloud:8889/stream/14/whep"
