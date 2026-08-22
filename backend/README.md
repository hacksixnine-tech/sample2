# PHANTOM Backend API Architecture & Operational Guide (Step 2 of 7)

**PHANTOM** (Statewide Video Intelligence & Investigation Platform for Gujarat CCTV Hackathon 2026) Backend Foundation & CCTV Registry.

This service is built with **Python 3.12+**, **FastAPI**, **Pydantic v2**, **SQLAlchemy 2.0 (AsyncPG)**, and **PostgreSQL 16 + PostGIS 3.4**.

---

## 1. Architecture & Design Principles

```
HTTP Request
      ↓
FastAPI Router (/api/v1/...)
      ↓
Pydantic Schema (Validation & Serialization)
      ↓
Service Layer (Business Rules, Audit Logging, Integrity Checks)
      ↓
Repository Layer (SQLAlchemy 2.0 Async, PostGIS Spatial Functions)
      ↓
PostgreSQL 16 + PostGIS 3.4 (Geodesic Spatial Queries, Indexes, Foreign Keys)
```

---

## 2. Directory Structure

```text
backend/
├── app/
│   ├── main.py                     # FastAPI application factory, lifespan, CORS, middleware, routers
│   ├── core/
│   │   ├── config.py               # Pydantic v2 Settings
│   │   ├── security.py             # Password hashing (bcrypt) & JWT token utilities
│   │   ├── logging.py              # Structured JSON/Console logging with request context
│   │   └── exceptions.py           # Domain exceptions (NotFound, Validation, Auth, Conflict)
│   ├── middleware/
│   │   ├── request_id.py           # Correlation ID injection (X-Request-ID)
│   │   └── access_log.py           # Structured request/response access logging with latency
│   ├── db/
│   │   ├── session.py              # Async engine, connection pooling, check_db_connection
│   │   ├── base.py                 # DeclarativeBase, UUIDMixin, TimestampMixin
│   │   └── dependencies.py         # FastAPI dependency `get_db` providing async session
│   ├── models/                     # SQLAlchemy 2.0 ORM Models
│   │   ├── department.py           # Department entity
│   │   ├── location.py             # Location entity with PostGIS geometry
│   │   ├── camera.py               # Camera entity with relations
│   │   ├── stream.py               # CameraStream entity
│   │   ├── health.py               # CameraHealth entity
│   │   └── audit.py                # AuditLog entity
│   ├── schemas/                    # Pydantic v2 Schemas
│   │   ├── common.py               # ApiResponse, PaginatedResponse, ErrorResponse
│   │   ├── department.py           # DepartmentCreate, DepartmentUpdate, DepartmentResponse
│   │   ├── location.py             # LocationCreate, LocationUpdate, NearbyLocationResponse
│   │   ├── camera.py               # CameraCreate, CameraResponse, CameraDetailResponse, BulkImport
│   │   ├── stream.py               # CameraStreamCreate, CameraStreamResponse
│   │   └── health.py               # HealthResponse, CameraHealthCreate, CameraHealthSummary
│   ├── repositories/               # Async Data Access Layer
│   │   ├── department.py           # DepartmentRepository
│   │   ├── location.py             # LocationRepository (PostGIS ST_DWithin & ST_Distance)
│   │   ├── camera.py               # CameraRepository (Spatial queries, Coverage metrics)
│   │   ├── stream.py               # StreamRepository
│   │   ├── health.py               # CameraHealthRepository
│   │   └── audit.py                # AuditRepository
│   ├── services/                   # Business Logic & Orchestration
│   │   ├── department_service.py   # Department management & summaries
│   │   ├── location_service.py     # Location & spatial validation
│   │   ├── camera_service.py       # Camera lifecycle, soft-decommissioning
│   │   ├── stream_service.py       # Stream protocol validation & primary switching
│   │   ├── health_service.py       # Telemetry recording & summary aggregation
│   │   └── bulk_import_service.py  # High-speed CSV/JSON bulk camera onboarding
│   ├── api/
│   │   ├── router.py               # Central API v1 router
│   │   └── v1/
│   │       ├── health.py           # Root system liveness & readiness
│   │       ├── info.py             # Platform capability metadata
│   │       └── endpoints/          # Modular domain routers (Departments, Locations, Cameras, Streams, Health, GIS)
├── tests/
│   ├── conftest.py                 # Async test client fixture
│   ├── unit/                       # Unit tests (config, security, exceptions, validators)
│   └── integration/                # Integration tests (health, info, departments, locations, cameras, streams, health, bulk-import)
├── Dockerfile                      # Multi-stage Python 3.12 production build
├── requirements.txt                # Dependencies
└── README.md
```

---

## 3. Running Tests

```bash
cd backend
python -m pytest -v
```
All 36 unit and integration tests execute against the live PostGIS test database.

---

## 4. Endpoints Overview

| Area | Methods & Paths | Description |
|---|---|---|
| **Health** | `GET /health`, `GET /health/live`, `GET /health/ready` | Liveness & PostGIS database readiness probes |
| **System Info** | `GET /api/v1/info` | Application metadata and active modules |
| **Departments** | `GET/POST /api/v1/departments`, `GET/PATCH/DELETE /api/v1/departments/{id}`, `GET /api/v1/departments/{id}/cameras` | Department management & camera distribution summary |
| **Locations & GIS** | `GET/POST /api/v1/locations`, `GET/PATCH/DELETE /api/v1/locations/{id}`, `GET /api/v1/locations/nearby` | Location CRUD & PostGIS geodesic spatial search |
| **CCTV Registry** | `GET/POST /api/v1/cameras`, `GET/PATCH/DELETE /api/v1/cameras/{id}`, `GET /api/v1/cameras/nearby`, `GET /api/v1/cameras/search`, `GET /api/v1/cameras/coverage`, `POST /api/v1/cameras/bulk-import` | Camera lifecycle, PostGIS radius search, statewide coverage stats, bulk import |
| **Streams** | `GET/POST /api/v1/cameras/{id}/streams`, `GET/PATCH/DELETE /api/v1/cameras/{id}/streams/{stream_id}` | Multi-protocol video stream configurations |
| **Camera Health** | `GET /api/v1/cameras/health/summary`, `GET/POST /api/v1/cameras/{id}/health`, `GET /api/v1/cameras/{id}/health/history` | Camera telemetry ingest & real-time operational summaries |
| **GIS** | `GET /api/v1/gis/cameras/nearby`, `GET /api/v1/gis/locations/nearby`, `GET /api/v1/gis/coverage` | Unified GIS spatial endpoints |
