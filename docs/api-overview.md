# PHANTOM REST API Overview & Reference (Step 2)

All API endpoints are mounted under prefix `/api/v1/`.

---

## 1. Unified Response Envelope

### Standard Success Response
```json
{
  "success": true,
  "data": { ... },
  "request_id": "8f8da8e0-1c66-4c91-9e79-bc2d5c317f2a"
}
```

### Standard Paginated Response
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 30,
    "total_pages": 2
  },
  "request_id": "8f8da8e0-1c66-4c91-9e79-bc2d5c317f2a"
}
```

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": null
  },
  "request_id": "8f8da8e0-1c66-4c91-9e79-bc2d5c317f2a"
}
```

---

## 2. Implemented API Summary

| Module | Method | Path | Summary |
|---|---|---|---|
| **Health** | `GET` | `/health` | Application liveness probe |
| **Health** | `GET` | `/health/live` | Container orchestrator liveness |
| **Health** | `GET` | `/health/ready` | Database readiness check with PostGIS ping |
| **Info** | `GET` | `/api/v1/info` | Platform metadata and active modules |
| **Departments** | `POST` | `/api/v1/departments` | Register government department |
| **Departments** | `GET` | `/api/v1/departments` | List departments (paginated, search, filter) |
| **Departments** | `GET` | `/api/v1/departments/{id}` | Get department details |
| **Departments** | `PATCH` | `/api/v1/departments/{id}` | Update department |
| **Departments** | `DELETE` | `/api/v1/departments/{id}` | Soft deactivate department |
| **Departments** | `GET` | `/api/v1/departments/{id}/cameras` | Department camera intelligence summary |
| **Locations** | `POST` | `/api/v1/locations` | Create location |
| **Locations** | `GET` | `/api/v1/locations` | List locations (district, city, keyword filter) |
| **Locations** | `GET` | `/api/v1/locations/nearby` | PostGIS spatial nearby search |
| **Locations** | `GET` | `/api/v1/locations/{id}` | Get location details |
| **Locations** | `PATCH` | `/api/v1/locations/{id}` | Update location |
| **Locations** | `DELETE` | `/api/v1/locations/{id}` | Delete unused location |
| **Cameras** | `POST` | `/api/v1/cameras` | Register camera |
| **Cameras** | `GET` | `/api/v1/cameras` | List cameras (multi-criteria filters, pagination) |
| **Cameras** | `GET` | `/api/v1/cameras/nearby` | PostGIS nearby cameras search |
| **Cameras** | `GET` | `/api/v1/cameras/search` | Unified camera search bar endpoint |
| **Cameras** | `GET` | `/api/v1/cameras/coverage` | Statewide camera distribution summary |
| **Cameras** | `POST` | `/api/v1/cameras/bulk-import` | High-speed CSV/JSON bulk onboarding |
| **Cameras** | `GET` | `/api/v1/cameras/{id}` | Camera details with relations |
| **Cameras** | `PATCH` | `/api/v1/cameras/{id}` | Update camera |
| **Cameras** | `DELETE` | `/api/v1/cameras/{id}` | Soft-decommission camera |
| **Streams** | `POST` | `/api/v1/cameras/{id}/streams` | Attach video stream |
| **Streams** | `GET` | `/api/v1/cameras/{id}/streams` | List streams for camera |
| **Streams** | `GET` | `/api/v1/cameras/{id}/streams/{stream_id}` | Get stream configuration |
| **Streams** | `PATCH` | `/api/v1/cameras/{id}/streams/{stream_id}` | Update stream |
| **Streams** | `DELETE` | `/api/v1/cameras/{id}/streams/{stream_id}` | Detach stream |
| **Health** | `GET` | `/api/v1/cameras/health/summary` | Statewide camera fleet health summary |
| **Health** | `GET` | `/api/v1/cameras/{id}/health` | Latest health observation |
| **Health** | `GET` | `/api/v1/cameras/{id}/health/history` | Historical telemetry records |
| **Health** | `POST` | `/api/v1/cameras/{id}/health` | Record heartbeat/telemetry |
| **GIS** | `GET` | `/api/v1/gis/cameras/nearby` | Dedicated GIS nearby camera query |
| **GIS** | `GET` | `/api/v1/gis/locations/nearby` | Dedicated GIS nearby location query |
| **GIS** | `GET` | `/api/v1/gis/coverage` | GIS coverage & density metrics |
