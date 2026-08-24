# PHANTOM // Portable Live CCTV Stream Gateway Handover & Runbook

This document details the master handover protocol for **PHANTOM CCTV Command Center**. It ensures that any teammate cloning the repository onto a fresh machine can start the entire platform, access live camera streams, and run AI analytics with zero friction.

---

## SECTION 1: SENDER HANDOVER PROTOCOL (Original Developer Checklist)

Before pushing the codebase and handing off to a teammate, verify that the repository is completely sanitized, portable, and free of developer-specific dependencies:

- [x] **Zero Hardcoded Machine References**: No references to developer's local IP, local directories (`C:\Users\username\...`), or uncommitted environment secrets.
- [x] **Containerized Stream Gateway**: FFmpeg and HLS transcoding tools are installed inside Docker images (`backend/Dockerfile`), eliminating manual host prerequisites.
- [x] **Frontend API Decoupling**: Frontend communicates strictly via PHANTOM API endpoints (`/api/v1/cameras/...` and `/api/v1/streams/...`), never attempting direct browser RTSP connects or direct internal IP calls.
- [x] **Full-Frame Uncropped Video Rendering**: Video elements default to `object-contain` (`FIT 100% Uncropped`) so that side road lanes, timestamps, and camera edge boundaries are never clipped by automatic zooming.
- [x] **Graceful Fallback & Standalone Verification**: `ENABLE_TEST_STREAM_FALLBACK=true` ensures the entire pipeline generates valid, live 25 FPS H.264 video streams locally even if the teammate has no external government VPN or network access.
- [x] **Configurable Camera Source Registry**: Complete 30-camera catalog configured in `camera_sources.yaml` and database migrations/seeds.
- [x] **One-Command Setup Script**: Windows PowerShell `setup.ps1` automates environment creation, container orchestration, readiness polling, and verification.

---

## SECTION 2: RECEIVER PROTOCOL (Teammate Fresh-Machine Runbook)

### Prerequisites on Fresh Laptop
1. **Windows 10/11** with **Docker Desktop** (WSL2 backend enabled).
2. **Git** installed.
*(No local Python, Node, PostgreSQL, Redis, or FFmpeg installations required; everything runs containerized)*

---

### Step-by-Step Launch Procedure

#### 1. Clone the Repository
```powershell
git clone <PHANTOM_REPOSITORY_URL>
cd PHANTOM
```

#### 2. Run the One-Command Setup
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The script will automatically:
1. Create `.env` from `.env.example` if not present.
2. Verify Docker Desktop daemon is active.
3. Build and launch the container stack (`phantom-postgres`, `phantom-redis`, `phantom-backend`, `phantom-frontend`).
4. Initialize database migrations and PostGIS tables.
5. Seed 30 distributed Gujarat CCTV cameras and metadata.
6. Initialize the Stream Gateway and probe video feeds.
7. Run automated smoke tests and display live URLs.

---

### Platform Access URLs

| Interface | URL | Purpose |
| :--- | :--- | :--- |
| **Frontend Command Center** | [http://localhost:3000](http://localhost:3000) | Live 30-cam video monitoring wall, GIS map, ANPR & Alerts |
| **Backend OpenAPI Docs** | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | Interactive Swagger API documentation |
| **System Health Check** | [http://localhost:8000/health/live](http://localhost:8000/health/live) | Container liveness and DB connectivity probe |
| **Stream Gateway Playback** | [http://localhost:8000/api/v1/streams/CAM-001/live.m3u8](http://localhost:8000/api/v1/streams/CAM-001/live.m3u8) | Low-latency HLS stream for direct player ingest |

---

## SECTION 3: STREAM GATEWAY ARCHITECTURE

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 CCTV CAMERA SOURCES                     │
                  │  - External Live Feed (live.corp8.cloud)                │
                  │  - Direct On-Prem RTSP (rtsp://host:8554/stream)        │
                  │  - Standard HLS / HTTP (http://.../live.m3u8)           │
                  │  - Local Synthetic Generator (testsrc2 H.264 25 FPS)    │
                  └────────────────────────────┬────────────────────────────┘
                                               │
                                               ▼
                  ┌─────────────────────────────────────────────────────────┐
                  │             PHANTOM STREAM GATEWAY SERVICE              │
                  │             (Containerized inside Backend)              │
                  │  - Multi-protocol Ingest & Cookie Persistence           │
                  │  - FFmpeg Transcoder & Remuxer (RTSP -> HLS)            │
                  │  - Dynamic Manifest URL Rewriter & Segment Proxy        │
                  │  - Dynamic Bandwidth Optimizer (LOW / MED / HIGH)       │
                  │  - Process Lifecycle & Zero-Zombie Process GC           │
                  └──────────────┬───────────────────────────┬──────────────┘
                                 │                           │
                 Browser HLS / HTTP Live             Normalized Frame Buffer
                                 │                           │
                                 ▼                           ▼
                  ┌────────────────────────────┐ ┌────────────────────────────┐
                  │     PHANTOM FRONTEND       │ │       AI INGESTION         │
                  │  - React 19 + Hls.js       │ │  - YOLOv8 / ByteTrack      │
                  │  - Full-Frame 100% (FIT)   │ │  - ANPR License Plate OCR  │
                  │  - Auto-reconnect & HUD    │ │  - Cross-Cam Intelligence  │
                  └────────────────────────────┘ └────────────────────────────┘
```

---

## SECTION 4: TROUBLESHOOTING & COMMON QUESTIONS

### Q1: CCTV frame was getting cropped on sides (auto-zoomed). How was this resolved?
**Cause**: The video element had CSS `object-cover` applied, causing the browser to zoom in and clip the horizontal edges (lane borders and timestamps) to fill a non-matching aspect box.  
**Resolution**: We updated `CameraPlayer.tsx` and `globals.css` to use `object-fit: contain` (`FIT (100%)`) by default with clean letterboxing. A tactical `[FIT (100%)]` / `[FILL (ZOOM)]` toggle button is now available in the player control bar so operators can choose their preferred framing mode at any time.

### Q2: What if the external government CCTV feed is unreachable?
**Status Reporting**: The Stream Gateway distinguishes between **PHANTOM Software Ready** and **External Camera Access Available**. If an external feed requires a private VPN or whitelisting that is not present on the developer machine:
- With `ENABLE_TEST_STREAM_FALLBACK=true`, the gateway generates a live 25 FPS H.264 test card with real-time timestamps and camera code, marked with the HUD badge `TEST FEED`.
- With fallback disabled, it displays a clear `CCTV SOURCE CONFIGURATION REQUIRED` banner with retry options instead of a silent black screen.

### Q3: How do I add or modify camera stream sources?
Edit [camera_sources.yaml](file:///d:/Phantom/camera_sources.yaml):
```yaml
  - camera_code: "CAM-CUSTOM-01"
    name: "Junction 5 Surveillance"
    district: "Ahmedabad"
    department: "Ahmedabad City Police"
    source_type: "RTSP" # CORP8, RTSP, HLS, or HTTP
    source_url: "rtsp://192.168.1.100:554/live/ch0"
    enabled: true
```
Then restart services using `.\restart.ps1`.

### Q4: Routine Maintenance Commands
- **Check Health**: `powershell -ExecutionPolicy Bypass -File .\health.ps1`
- **Restart Services**: `powershell -ExecutionPolicy Bypass -File .\restart.ps1`
- **Stop Services**: `powershell -ExecutionPolicy Bypass -File .\stop.ps1`
- **Reset Cache/DB**: `powershell -ExecutionPolicy Bypass -File .\reset.ps1`
