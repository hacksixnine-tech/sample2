# PHANTOM // Statewide CCTV Video Intelligence & Command Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_19_%2B_Vite-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_16_%2B_PostGIS_3.4-336791.svg?style=flat&logo=postgresql)](https://www.postgresql.org)
[![Security](https://img.shields.io/badge/Security-JWT_%2B_RBAC_%2B_Audit_Trail-E53935.svg?style=flat&logo=shield)](SECURITY.md)
[![Scale](https://img.shields.io/badge/Statewide_Scale-80%2C000_Cameras_Readiness-4CAF50.svg?style=flat)](docs/statewide-scale-architecture.md)

**PHANTOM** is a high-performance, vendor-neutral video intelligence, automated number plate recognition (ANPR), cross-camera vehicle tracking, and CCTV stream gateway command-and-control platform engineered for the **Gujarat Police Department & Law Enforcement Agencies**.

---

## 1. Quick Start for Fresh Machines (One-Command Launch)

### Prerequisites
- **Windows 10/11** with **Docker Desktop** (WSL2 enabled).
- **Git**
*(Zero host dependencies: Python, Node, PostgreSQL, Redis, and FFmpeg run completely containerized)*

### Fresh Clone & Instant Startup
```powershell
# 1. Clone the repository
git clone https://github.com/lvhinguroot-08/PHANTOM-FINAL.git
cd PHANTOM-FINAL

# 2. One-Click Setup (Windows Batch or PowerShell)
.\setup.bat
# OR via PowerShell:
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The bootstrap script will automatically:
1. Validate or generate `.env` from `.env.example`.
2. Check Docker daemon health.
3. Build and launch all 4 services via Docker Compose.
4. Run database migrations and PostGIS tables.
5. Seed 30 distributed Gujarat CCTV cameras across 33 districts.
6. Initialize Stream Gateway and verify live HLS / RTSP ingestion.
7. Execute automated smoke tests and print ready URLs.

---

## 2. Command Center & Platform Access URLs

| Interface | URL | Description |
| :--- | :--- | :--- |
| **Frontend Command Center** | [http://localhost:3000](http://localhost:3000) | Live 30-camera video wall, GIS map, ANPR & Alerts |
| **Backend OpenAPI Docs** | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | Interactive Swagger REST API Explorer |
| **System Liveness Endpoint** | [http://localhost:8000/health/live](http://localhost:8000/health/live) | Kubernetes/Docker health check |
| **Stream Gateway Playback** | [http://localhost:8000/api/v1/streams/CAM-001/live.m3u8](http://localhost:8000/api/v1/streams/CAM-001/live.m3u8) | Low-latency HLS stream for direct player ingest |

---

## 3. Live CCTV Stream Gateway Architecture

```
CAMERA SOURCES (Corp8 / RTSP / HLS / HTTP / Local Generator)
                            │
                            ▼
              PHANTOM STREAM GATEWAY SERVICE
              (Containerized inside Backend)
              - RTSP / HLS / MP4 Multi-Protocol Ingest
              - Containerized FFmpeg Transcoder & Remuxer
              - Dynamic HLS Manifest URL Rewriter & Segment Proxy
              - Zero-Zombie Process Garbage Collector
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
PHANTOM FRONTEND (React 19 + Hls.js)    AI INGESTION (YOLOv8 + ANPR)
- 100% Full-Frame (FIT/FILL toggle)    - High-throughput plate OCR
- Low-latency live monitoring wall      - Vehicle trajectory tracking
```

---

## 4. Video Framing & Aspect Ratio Controls

> **Frame Cropping Fix**: Previously, videos had CSS `object-cover` applied, causing browsers to zoom in and cut off left/right side details (road edges and camera timestamps).  
> **Now**: The video player defaults to `object-fit: contain` (**100% Full Frame Uncropped**). Operators can also toggle between:
> - `FIT (100%)`: Complete uncropped camera view showing all side lanes, timestamps, and road edges.
> - `FILL (ZOOM)`: Stretched fill mode to cover the entire container.

---

## 5. Camera Source Configuration

Camera mappings are managed dynamically via [`camera_sources.yaml`](camera_sources.yaml) and database seeds:

```yaml
cameras:
  - camera_code: "CAM-AMD-ITX-01"
    name: "Income Tax Circle ANPR Northbound"
    district: "Ahmedabad"
    department: "Ahmedabad City Police"
    source_type: "CORP8" # CORP8, RTSP, HLS, or HTTP
    source_url: "https://live.corp8.cloud/live/stream/13/index.m3u8"
    rtsp_url: "rtsp://live.corp8.cloud:8554/stream/13"
    enabled: true
```

---

## 6. Operational Scripts (Windows Batch & PowerShell)

| Script (Batch / PowerShell) | Purpose |
| :--- | :--- |
| `.\setup.bat` / `.\setup.ps1` | Fresh-machine complete bootstrapper (builds & starts all containers) |
| `.\start.bat` / `.\start.ps1` | Start PHANTOM containers |
| `.\stop.bat` / `.\stop.ps1` | Stop PHANTOM containers |
| `.\restart.bat` / `.\restart.ps1` | Restart all platform services |
| `.\health.ps1` | Run complete health and API diagnostic probe |
| `.\reset.ps1` | Cleanly reset containers and stream cache |

---

## 7. Running Automated Tests

```powershell
# Run backend test suite (81 unit & security tests)
python -m pytest backend/tests/unit -q

# Run frontend production build test
cd frontend; npm run build

# Run master stream smoke test
python backend/scripts/smoke_test.py
```

---

## 8. Documentation Index

- [`TEAM_HANDOVER.md`](TEAM_HANDOVER.md): Engineering runbook, sender/receiver protocol, and troubleshooting guide.
- [`SECURITY.md`](SECURITY.md): Enterprise security, RBAC governance, and audit trails.
- [`DEMO_GUIDE.md`](DEMO_GUIDE.md): 2–3 minute hackathon demonstration script.
- [`docs/statewide-scale-architecture.md`](docs/statewide-scale-architecture.md): 80,000-camera scale model and GPU sizing.
