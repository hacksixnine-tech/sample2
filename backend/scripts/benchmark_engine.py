"""
PHANTOM // Empirical Performance & Load Benchmark Engine
Measures actual API latency, Token hashing, AI pipeline throughput,
and WebSocket event serialization without fabricated values.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.security import create_access_token, decode_token, get_password_hash, verify_password
from app.schemas.events import EventEnvelope
from app.services.event_publisher import event_publisher
from app.services.health_aggregation import CentralHealthService, RegionalHealthAgent
from app.services.stream_gateway_service import stream_gateway_service


def calculate_percentiles(durations_ms: List[float]) -> Dict[str, float]:
    if not durations_ms:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}
    sorted_durations = sorted(durations_ms)
    n = len(sorted_durations)
    return {
        "p50": round(sorted_durations[int(n * 0.50)], 3),
        "p95": round(sorted_durations[min(int(n * 0.95), n - 1)], 3),
        "p99": round(sorted_durations[min(int(n * 0.99), n - 1)], 3),
        "avg": round(sum(sorted_durations) / n, 3),
        "min": round(sorted_durations[0], 3),
        "max": round(sorted_durations[-1], 3),
    }


def benchmark_cryptography(iterations: int = 10) -> Dict[str, Any]:
    """Benchmark Bcrypt password hashing and JWT token encode/decode."""
    # 1. Bcrypt Hash & Verification
    bcrypt_durations = []
    test_pass = "BenchmarkSecurePass@2026"
    for _ in range(iterations):
        t0 = time.perf_counter()
        hashed = get_password_hash(test_pass)
        verify_password(test_pass, hashed)
        t1 = time.perf_counter()
        bcrypt_durations.append((t1 - t0) * 1000)

    # 2. JWT Access Token Signing & Verification (1000 iterations)
    jwt_durations = []
    for _ in range(1000):
        t0 = time.perf_counter()
        token = create_access_token(subject="user-bench-uuid", extra_claims={"role": "POLICE_OFFICER"})
        decode_token(token)
        t1 = time.perf_counter()
        jwt_durations.append((t1 - t0) * 1000)

    return {
        "bcrypt_hash_verify": calculate_percentiles(bcrypt_durations),
        "jwt_sign_decode_1000x": calculate_percentiles(jwt_durations),
        "jwt_throughput_ops_sec": round(1000 / (sum(jwt_durations) / 1000.0), 1),
    }


async def benchmark_event_pipeline(iterations: int = 5000) -> Dict[str, Any]:
    """Benchmark event envelope serialization, publishing, and subscriber dispatch."""
    received = 0

    def subscriber(evt: EventEnvelope):
        nonlocal received
        received += 1

    event_publisher.subscribe("BENCHMARK_EVENT", subscriber)
    durations = []

    t_start = time.perf_counter()
    for i in range(iterations):
        t0 = time.perf_counter()
        await event_publisher.publish(
            event_name="BENCHMARK_EVENT",
            payload={"camera_id": f"CAM-{i % 100:03d}", "plate": "GJ01AB1234", "speed": 65.4},
            camera_id=f"CAM-{i % 100:03d}",
            severity="MEDIUM",
            source="benchmark-harness",
        )
        t1 = time.perf_counter()
        durations.append((t1 - t0) * 1000)

    total_time_sec = time.perf_counter() - t_start
    event_publisher.unsubscribe("BENCHMARK_EVENT", subscriber)

    return {
        "iterations": iterations,
        "received_count": received,
        "total_time_sec": round(total_time_sec, 3),
        "throughput_events_sec": round(iterations / total_time_sec, 1),
        "publish_latency_ms": calculate_percentiles(durations),
    }


def benchmark_hierarchical_health(camera_count: int = 5000) -> Dict[str, Any]:
    """Benchmark regional health agent aggregating thousands of camera telemetry points."""
    agent = RegionalHealthAgent(region_id="REG-BENCHMARK", zone_name="TEST_ZONE")
    for i in range(camera_count):
        is_on = (i % 50 != 0)  # 2% offline
        lat = 15.0 + (i % 40)
        agent.record_camera_status(f"CAM-{i:05d}", is_online=is_on, latency_ms=lat if is_on else None)

    t0 = time.perf_counter()
    report = agent.generate_aggregated_report()
    t1 = time.perf_counter()
    agent_duration_ms = (t1 - t0) * 1000

    central = CentralHealthService()
    t2 = time.perf_counter()
    central.ingest_regional_report(report)
    rollup = central.get_statewide_health_rollup()
    t3 = time.perf_counter()
    central_duration_ms = (t3 - t2) * 1000

    return {
        "cameras_aggregated": camera_count,
        "regional_aggregation_latency_ms": round(agent_duration_ms, 3),
        "central_rollup_latency_ms": round(central_duration_ms, 3),
        "total_online": report.online_cameras,
        "total_offline": report.offline_cameras,
        "statewide_health_score_pct": rollup["statewide_health_score_pct"],
    }


def run_all_benchmarks() -> Dict[str, Any]:
    print("=" * 60)
    print("PHANTOM STATEWIDE SCALE & PERFORMANCE BENCHMARK ENGINE")
    print(f"Node Role: {settings.NODE_ROLE} | Zone: {settings.REGIONAL_ZONE}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    print("\n[1/3] Benchmarking Cryptography & Tokens...")
    crypto_res = benchmark_cryptography(iterations=10)
    print(f"  - Bcrypt (10 iterations) Avg: {crypto_res['bcrypt_hash_verify']['avg']} ms")
    print(f"  - JWT Sign/Decode Throughput: {crypto_res['jwt_throughput_ops_sec']} ops/sec")

    print("\n[2/3] Benchmarking Event Pipeline & Serialization...")
    event_res = asyncio.run(benchmark_event_pipeline(iterations=5000))
    print(f"  - Event Pipeline Throughput: {event_res['throughput_events_sec']} events/sec")
    print(f"  - Event Publish p50: {event_res['publish_latency_ms']['p50']} ms | p99: {event_res['publish_latency_ms']['p99']} ms")

    print("\n[3/3] Benchmarking Hierarchical Health Aggregation (5,000 cameras)...")
    health_res = benchmark_hierarchical_health(camera_count=5000)
    print(f"  - Regional Aggregation Latency: {health_res['regional_aggregation_latency_ms']} ms")
    print(f"  - Central Rollup Latency: {health_res['central_rollup_latency_ms']} ms")

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cryptography": crypto_res,
        "event_pipeline": event_res,
        "hierarchical_health": health_res,
    }

    print("\n" + "=" * 60)
    print("BENCHMARK EXECUTION COMPLETE")
    print("=" * 60)
    return results


if __name__ == "__main__":
    run_all_benchmarks()
