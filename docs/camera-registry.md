# PHANTOM CCTV Camera Registry & Management Architecture

**PHANTOM** (Statewide Video Intelligence & Investigation Platform for Gujarat CCTV Hackathon 2026) provides a centralized, high-throughput CCTV registry capable of scaling across 80,000+ statewide cameras.

---

## 1. Architectural Highlights

- **Heterogeneous Hardware Ingestion**: Vendor-neutral registry supporting ANPR, PTZ, FIXED, IP, DRONE, and BODY-WORN devices.
- **External Source Systems Integration**:
  ```
  Official External CCTV Source (https://live.corp8.cloud/)
         ↓
  Corp8SourceAdapter (/api/cameras)
         ↓
  SourceDiscoveryService (RTSP, WebRTC/WHEP, HLS)
         ↓
  PHANTOM Camera Registry (Preserves source_system_id, source_camera_id, source_metadata)
         ↓
  AI Analytics & GIS Mapping
  ```
- **Strict 4-Layer Separation**:
  ```
  FastAPI Route -> Pydantic Schema -> Service Layer -> Repository Layer -> PostgreSQL/PostGIS
  ```
- **Referential Integrity & Soft Decommissioning**: Prevents accidental hard-deletion of cameras with active historical observation trails.
- **Streaming Agnostic**: Protocol metadata for RTSP, HLS, WebRTC, ONVIF, HTTP, and proprietary VENDOR APIs.
- **Bulk Onboarding**: High-speed batch ingestion with atomic row-level validation, coordinate bounds checking, and duplicate prevention.

---

## 2. API Endpoints

### 2.1 External CCTV Sources & Ingestion
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/sources` | List registered external CCTV sources |
| `POST` | `/api/v1/sources` | Register external source provider |
| `GET` | `/api/v1/sources/{id}` | Get source details and configuration |
| `POST` | `/api/v1/sources/{id}/probe` | Live reachability and latency probe |
| `GET` | `/api/v1/sources/{id}/discover` | Discover live feeds without modifying database |
| `POST` | `/api/v1/sources/{id}/sync` | Synchronize and onboard live camera catalog into PHANTOM |

### 2.2 Cameras Registry
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/cameras` | Register a new camera device |
| `GET` | `/api/v1/cameras` | List cameras with multi-field filtering & pagination |
| `GET` | `/api/v1/cameras/{id}` | Detailed camera profile with department, location, streams, source mapping, and latest health |
| `PATCH` | `/api/v1/cameras/{id}` | Update camera parameters |
| `DELETE` | `/api/v1/cameras/{id}` | Soft-decommission camera |
| `GET` | `/api/v1/cameras/nearby` | Find cameras within geodesic radius via PostGIS |
| `GET` | `/api/v1/cameras/search` | Unified global keyword search |
| `GET` | `/api/v1/cameras/coverage` | Statewide camera coverage statistics |
| `POST` | `/api/v1/cameras/bulk-import` | Bulk onboarding from CSV or JSON payload |

### 2.3 Camera Streams
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/cameras/{id}/streams` | Attach video stream to camera |
| `GET` | `/api/v1/cameras/{id}/streams` | List streams for camera |
| `GET` | `/api/v1/cameras/{id}/streams/{stream_id}` | Get stream configuration |
| `PATCH` | `/api/v1/cameras/{id}/streams/{stream_id}` | Update stream parameters |
| `DELETE` | `/api/v1/cameras/{id}/streams/{stream_id}` | Detach video stream |

### 2.4 Camera Health & Observability
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/cameras/health/summary` | Statewide fleet health summary |
| `GET` | `/api/v1/cameras/{id}/health` | Latest health observation |
| `GET` | `/api/v1/cameras/{id}/health/history` | Historical telemetry records |
| `POST` | `/api/v1/cameras/{id}/health` | Ingest heartbeat / probe telemetry |
