# PHANTOM — External CCTV Source Integration Architecture

This document details the live external CCTV integration subsystem in **PHANTOM**, including the integration with the official Gujarat CCTV Hackathon 2026 camera source (`https://live.corp8.cloud/`).

---

## 1. External Source Provider Overview

During the Gujarat CCTV Hackathon 2026, an external live CCTV provider is integrated to supply dynamic camera feeds across multiple operational zones:

- **Provider Base Endpoint**: `https://live.corp8.cloud/`
- **Catalog API**: `GET /api/cameras` (discovers all 30 live test cameras)
- **Detailed Stream API**: `GET /api/cameras/{id}` or `GET /api/cameras/{id}/streams`
- **Supported Stream Protocols**: HLS (`.m3u8`), WebRTC, HTTP Live Streams.

---

## 2. Integration Pipeline Workflow

```
[ External Source: live.corp8.cloud ]
                    │
    1. PROBE (Health & Latency Check)
                    ▼
[ PHANTOM Source Discovery Engine (app/adapters/corp8_source_adapter.py) ]
                    │
    2. DISCOVER (Fetch Cameras & Stream Endpoints)
                    ▼
[ Metadata Normalization & District Mapping ]
    ├── Inferred Location Parsing (District, Junction, Latitude/Longitude)
    ├── Primary vs Secondary Stream Classification
    └── Protocol Validation (HLS / WebRTC / RTSP)
                    │
    3. SYNC (Idempotent Database Persistence)
                    ▼
[ PHANTOM Core Registry (PostGIS Locations + Cameras + Streams) ]
```

---

## 3. Verified Endpoints & Operational Guarantees

1. **`POST /api/v1/sources/{source_id}/probe`**:
   - Executes an out-of-band HTTP latency check against the external provider endpoint.
   - Measures round-trip latency, SSL certificate validity, and HTTP response code.
   - Returns provider reachability status without interrupting active streams.

2. **`POST /api/v1/sources/{source_id}/discover`**:
   - Queries the provider's `/api/cameras` endpoint.
   - Parses the JSON catalog, extracting camera codes, stream URLs, resolutions, and raw geographic strings.
   - Normalizes streams into structured `DiscoveredStream` schemas.

3. **`POST /api/v1/sources/{source_id}/sync`**:
   - Performs an idempotent upsert into PHANTOM's `cameras`, `locations`, and `camera_streams` tables.
   - Preserves custom operator metadata and ensures camera codes (`CAM-CORP8-01` through `CAM-CORP8-30`) do not collide with municipal cameras.

---

## 4. Resilience & Circuit Breaking

- **Timeout Configuration**: HTTP client timeout is capped at 10.0 seconds with exponential backoff retry (3 attempts).
- **Circuit Breaker**: If the external source provider fails 5 consecutive health probes, the source status transitions to `DEGRADED` or `INACTIVE`, preventing worker thread exhaustion.
- **SSRF Hardening**: All discovered and configured stream URLs pass strict SSRF validation (`validate_safe_url`), blocking loopbacks and cloud metadata endpoints.
