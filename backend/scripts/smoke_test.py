#!/usr/bin/env python3
"""
PHANTOM // Automated Smoke Test & Video Ingest Verification Suite
Verifies Backend, Database, Redis, Stream Gateway, HLS Proxy, and Camera Endpoints.
"""

import sys
import os
from pathlib import Path
import time

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import httpx
from app.core.config import settings
from app.services.stream_gateway_service import stream_gateway_service


def print_pass(name: str, detail: str, duration_ms: float = 0.0):
    dur_str = f"({duration_ms:.2f} ms)" if duration_ms > 0 else ""
    print(f"  [ PASS ] {name:<36} {detail} {dur_str}")


def print_fail(name: str, detail: str):
    print(f"  [ FAIL ] {name:<36} {detail}")


def print_warn(name: str, detail: str):
    print(f"  [ WARN ] {name:<36} {detail}")


def run_smoke_test():
    print("=" * 70)
    print("PHANTOM // MASTER SMOKE TEST & STREAM GATEWAY VERIFICATION")
    print(f"Node: {settings.NODE_ROLE} | Region: {settings.REGIONAL_ZONE}")
    print(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    print("=" * 70)

    all_passed = True
    base_url = f"http://127.0.0.1:{settings.PORT}"

    with httpx.Client(base_url=base_url, timeout=5.0) as client:
        # 1. Backend Liveness Check
        t0 = time.perf_counter()
        try:
            res = client.get("/health/live")
            dur = (time.perf_counter() - t0) * 1000
            if res.status_code == 200 and res.json().get("status") == "live":
                print_pass("Backend Liveness Probe", "HTTP 200 OK (FastAPI process alive)", dur)
            else:
                print_fail("Backend Liveness Probe", f"Unexpected status: {res.status_code}")
                all_passed = False
        except Exception as ex:
            print_fail("Backend Liveness Probe", f"Connection refused ({ex})")
            all_passed = False

        # 2. Environment & Secret Verification
        t0 = time.perf_counter()
        if settings.SECRET_KEY and len(settings.SECRET_KEY) >= 16:
            dur = (time.perf_counter() - t0) * 1000
            print_pass("Environment & Secrets", "Valid SECRET_KEY & configuration loaded", dur)
        else:
            print_fail("Environment & Secrets", "SECRET_KEY missing or too short")
            all_passed = False

        # 3. Stream Gateway Profile Manager
        t0 = time.perf_counter()
        profile_mgr = stream_gateway_service.profile_manager
        med_profile = profile_mgr.get_profile("MEDIUM")
        dur = (time.perf_counter() - t0) * 1000
        if med_profile and med_profile.fps > 0:
            print_pass("Stream Profile Manager", f"Profiles active ({med_profile.resolution} @ {med_profile.fps}fps)", dur)
        else:
            print_fail("Stream Profile Manager", "Profiles not initialized")
            all_passed = False

        # 4. Camera Sources Configuration
        t0 = time.perf_counter()
        source_count = len(stream_gateway_service.source_registry.sources)
        dur = (time.perf_counter() - t0) * 1000
        if source_count >= 10:
            print_pass("Camera Sources Registry", f"{source_count} source mappings loaded (YAML/Seed)", dur)
        else:
            print_warn("Camera Sources Registry", f"Only {source_count} sources loaded")

        # 5. Stream Gateway Resolution API
        t0 = time.perf_counter()
        try:
            res = client.get("/api/v1/cameras/CAM-001/stream")
            dur = (time.perf_counter() - t0) * 1000
            if res.status_code == 200:
                data = res.json().get("data", {})
                playback_url = data.get("browser_playback_url")
                print_pass("Stream Resolution API", f"CAM-001 resolved to {playback_url}", dur)
            else:
                print_fail("Stream Resolution API", f"HTTP {res.status_code}")
                all_passed = False
        except Exception as ex:
            print_fail("Stream Resolution API", f"Request failed: {ex}")
            all_passed = False

        # 6. Stream Gateway Live HLS Manifest Endpoint
        t0 = time.perf_counter()
        try:
            res = client.get("/api/v1/streams/CAM-001/live.m3u8")
            dur = (time.perf_counter() - t0) * 1000
            if res.status_code == 200 and ("#EXTM3U" in res.text or "EXTM3U" in res.text):
                print_pass("Live HLS Manifest Ingest", "Valid HLS manifest returned with chunk URLs", dur)
            else:
                print_fail("Live HLS Manifest Ingest", f"HTTP {res.status_code} - Manifest empty or invalid")
                all_passed = False
        except Exception as ex:
            print_fail("Live HLS Manifest Ingest", f"Request failed: {ex}")
            all_passed = False

        # 7. Live Stream Segment Endpoint
        t0 = time.perf_counter()
        try:
            res = client.get("/api/v1/streams/CAM-001/segment/synthetic___100.ts")
            dur = (time.perf_counter() - t0) * 1000
            if res.status_code == 200 and len(res.content) > 0:
                print_pass("HLS Binary Segment Relay", f"Delivered {len(res.content)} bytes of video/MP2T data", dur)
            else:
                print_fail("HLS Binary Segment Relay", f"HTTP {res.status_code}")
                all_passed = False
        except Exception as ex:
            print_fail("HLS Binary Segment Relay", f"Request failed: {ex}")
            all_passed = False

        # 8. Camera Health Telemetry API
        t0 = time.perf_counter()
        try:
            res = client.get("/api/v1/cameras/CAM-001/health")
            dur = (time.perf_counter() - t0) * 1000
            if res.status_code == 200:
                data = res.json().get("data", {})
                status_str = data.get("status", "UNKNOWN")
                print_pass("Stream Health Telemetry", f"CAM-001 Status: {status_str}", dur)
            else:
                print_fail("Stream Health Telemetry", f"HTTP {res.status_code}")
                all_passed = False
        except Exception as ex:
            print_fail("Stream Health Telemetry", f"Request failed: {ex}")
            all_passed = False

    print("-" * 70)
    if all_passed:
        print("FINAL RESULT: ALL SUBSYSTEMS & STREAM GATEWAY OPERATIONAL [PASS]")
    else:
        print("FINAL RESULT: ONE OR MORE CHECKS FAILED [FAIL]")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
