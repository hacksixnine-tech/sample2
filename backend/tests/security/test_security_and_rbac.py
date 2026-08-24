import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token, get_password_hash, verify_password


@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected(client: AsyncClient):
    """Verify that protected endpoints strictly reject unauthenticated calls with 401."""
    endpoints = [
        ("GET", "/api/v1/alerts"),
        ("POST", "/api/v1/alerts"),
        ("GET", "/api/v1/watchlists"),
        ("POST", "/api/v1/watchlists"),
        ("GET", "/api/v1/incidents"),
        ("POST", "/api/v1/incidents"),
        ("GET", "/api/v1/investigations/search"),
        ("GET", "/api/v1/anpr/observations"),
    ]

    for method, path in endpoints:
        if method == "GET":
            resp = await client.get(path)
        else:
            resp = await client.post(path, json={})
        assert resp.status_code in (401, 403), f"Expected 401/403 for {method} {path}, got {resp.status_code}"
        body = resp.json()
        assert body["success"] is False
        assert "error" in body


@pytest.mark.asyncio
async def test_rbac_viewer_restricted_from_mutations(client: AsyncClient):
    """Verify that VIEWER role cannot execute mutative or management actions (403)."""
    viewer_token = create_access_token(
        subject=str(uuid.uuid4()), extra_claims={"role": "VIEWER"}
    )
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # 1. VIEWER cannot create a watchlist
    wl_resp = await client.post(
        "/api/v1/watchlists",
        json={"name": "Illegal Watchlist", "code": "WL-ILLEGAL-01", "category": "STOLEN_VEHICLE"},
        headers=headers,
    )
    assert wl_resp.status_code == 403, f"Expected 403, got {wl_resp.status_code}"

    # 2. VIEWER cannot create an incident
    inc_resp = await client.post(
        "/api/v1/incidents",
        json={"title": "Illegal Incident", "description": "Desc", "severity": "HIGH"},
        headers=headers,
    )
    assert inc_resp.status_code == 403, f"Expected 403, got {inc_resp.status_code}"

    # 3. VIEWER cannot resolve or acknowledge alerts
    fake_alert_id = str(uuid.uuid4())
    ack_resp = await client.post(
        f"/api/v1/alerts/{fake_alert_id}/acknowledge",
        json={"notes": "Illegal ack"},
        headers=headers,
    )
    assert ack_resp.status_code == 403, f"Expected 403, got {ack_resp.status_code}"


@pytest.mark.asyncio
async def test_ssrf_cloud_metadata_rejection(client: AsyncClient):
    """Verify SSRF protection blocks cloud metadata endpoints (169.254.169.254) and invalid schemes."""
    admin_token = create_access_token(
        subject=str(uuid.uuid4()), extra_claims={"role": "SYSTEM_ADMIN"}
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Attempt to register external source pointing to AWS/GCP metadata
    ssrf_payload = {
        "name": "Malicious Metadata Source",
        "code": "SRC-METADATA-ATTACK",
        "base_url": "http://169.254.169.254/latest/meta-data/",
    }
    resp = await client.post("/api/v1/sources", json=ssrf_payload, headers=headers)
    assert resp.status_code in (400, 422), f"Expected 400/422 for SSRF metadata attempt, got {resp.status_code}"

    # 2. Attempt stream with file:// or gopher:// scheme
    stream_payload = {
        "protocol": "RTSP",
        "stream_url": "file:///etc/passwd",
    }
    cam_id = str(uuid.uuid4())
    st_resp = await client.post(f"/api/v1/cameras/{cam_id}/streams", json=stream_payload, headers=headers)
    assert st_resp.status_code in (400, 422), f"Expected 400/422 for file:// scheme, got {st_resp.status_code}"


@pytest.mark.asyncio
async def test_token_expiration_and_tampering(client: AsyncClient):
    """Verify expired and tampered JWT tokens are strictly rejected on protected routes."""
    # 1. Expired Token
    expired_token = create_access_token(
        subject=str(uuid.uuid4()),
        expires_delta=timedelta(seconds=-10),
        extra_claims={"role": "POLICE_OFFICER"},
    )
    exp_resp = await client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {expired_token}"})
    assert exp_resp.status_code == 401

    # 2. Tampered Token signature
    tampered_token = expired_token[:-5] + "XXXXX"
    tam_resp = await client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {tampered_token}"})
    assert tam_resp.status_code == 401


@pytest.mark.asyncio
async def test_password_hashing_security():
    """Verify passwords are never stored in plaintext and bcrypt verification works reliably."""
    raw = "GujaratSecretPass@2026"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
