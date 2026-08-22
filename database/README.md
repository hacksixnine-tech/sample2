# PHANTOM Database Foundation (Step 1)

**PHANTOM** (Statewide Video Intelligence & Investigation Platform for Gujarat CCTV Hackathon 2026) is engineered around a core architectural principle:
> **CCTV is an EVENT + ENTITY network, not simply a video stream.**

This database foundation is built on **PostgreSQL 16+** with the **PostGIS 3.4** spatial extension, providing high-performance spatial-temporal queries, deterministic schema migrations, robust RBAC, audit governance, and cross-camera trajectory reconstruction.

---

## 1. Domain Separation Architecture

The data model cleanly isolates the system into 5 distinct operational tiers:

```
+-----------------------------------------------------------------------------------+
|                               1. INFRASTRUCTURE                                  |
|  departments (26) | locations (GIS Point) | cameras (30+) | streams | health      |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                              2. OBSERVATIONS & AI                                 |
|  entities (Supertype) | vehicles (Subtype) | detections (ANPR / BBox) | events    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                3. INTELLIGENCE                                    |
|  watchlists (Hotlists) | watchlist_entries | matches (Score/Method) | alerts       |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                               4. INVESTIGATION                                    |
|  incidents (Case Dossiers) | evidence (S3 Object Storage & SHA-256) | relations    |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                 5. GOVERNANCE                                     |
|  users (RBAC) | roles (Permissions JSONB) | audit_logs (Append-Only Audit)        |
+-----------------------------------------------------------------------------------+
```

---

## 2. Directory Structure

```text
database/
├── docker-compose.yml              # PostGIS 16 Container definition & health checks
├── .env.example                    # Environment credentials template
├── .env                            # Local dev environment configuration
├── README.md                       # Comprehensive operational guide
├── migrations/                     # Ordered deterministic SQL migrations
│   ├── 001_extensions.sql          # PostGIS, uuid-ossp, pgcrypto, btree_gist
│   ├── 002_departments.sql         # 26 Gujarat Government departments
│   ├── 003_roles_users.sql         # RBAC roles & user accounts
│   ├── 004_locations.sql           # PostGIS GEOGRAPHY(Point, 4326) & GiST index
│   ├── 005_cameras.sql             # Camera registry & connectivity status
│   ├── 006_camera_streams.sql      # RTSP/HLS/WebRTC stream metadata & vault refs
│   ├── 007_camera_health.sql       # Latency, FPS, bitrate, and health telemetry
│   ├── 008_entities.sql            # Entity supertype & normalized vehicle registry
│   ├── 009_detections.sql          # AI observations with spatial/temporal indexes
│   ├── 010_events.sql              # Real-time event queue model
│   ├── 011_watchlists.sql          # Hotlist definitions (Stolen, Wanted, etc.)
│   ├── 012_watchlist_entries.sql   # Watchlist plate & person search targets
│   ├── 013_matches.sql             # Detection-to-Watchlist matching engine
│   ├── 014_alerts.sql              # Automated alert lifecycle management
│   ├── 015_incidents.sql           # Investigation incident dossiers
│   ├── 016_evidence.sql            # Object storage references & SHA-256 checksums
│   ├── 017_incident_relations.sql  # M:N junction tables (Events, Alerts, Evidence)
│   ├── 018_audit_logs.sql          # Append-only forensic audit trail
│   └── 019_app_user_grants.sql     # Dedicated application user permissions
├── seeds/                          # Realistic non-sensitive demo seed data
│   ├── 01_departments.sql          # 26 Gujarat State departments
│   ├── 02_roles_users.sql          # RBAC roles & test users
│   ├── 03_locations.sql            # Accurate Gujarat coordinates across 12+ districts
│   ├── 04_cameras_streams_health.sql # 30 geo-distributed cameras + streams + health
│   ├── 05_entities_vehicles.sql    # Gujarat-registered vehicles & suspects
│   ├── 06_watchlists.sql           # Stolen vehicle & wanted lists
│   ├── 07_detections_events.sql    # Multi-camera vehicle trajectory sightings
│   ├── 08_matches_alerts_incidents.sql # Match -> Alert -> Incident -> Evidence pipeline
│   └── 09_audit_logs.sql           # Administrative audit trails
├── tests/                          # Automated SQL verification suites
│   ├── 01_verify_schema_and_extensions.sql
│   ├── 02_verify_gis_queries.sql
│   ├── 03_verify_vehicle_cross_camera_tracking.sql
│   ├── 04_verify_watchlist_alert_workflow.sql
│   └── 05_verify_integrity_and_constraints.sql
└── scripts/
    └── manage_db.py                # Automated migration & test orchestrator
```

---

## 3. Quickstart & Deployment

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (optional, or run directly via `docker exec`)

### Step 1: Start Container
```bash
cd d:/Phantom/database
docker compose up -d
```

### Step 2: Apply Migrations, Seeds & Run Tests
```bash
python scripts/manage_db.py all
```
*(Or individually: `python scripts/manage_db.py migrate`, `seed`, or `test`)*

---

## 4. GIS & Spatial Strategy

1. **Standardized Coordinate System**: All spatial coordinates use **WGS 84 (EPSG:4326)**.
2. **PostGIS Column Type**: `GEOGRAPHY(Point, 4326)` stored as a generated column from validated `(longitude, latitude)`.
3. **Spatial Index**: GiST index (`CREATE INDEX idx_locations_geom ON locations USING GIST(geom)`).
4. **Geodesic Distance Queries**:
   ```sql
   -- Find all cameras within 5,000 meters of a coordinate
   SELECT c.camera_code, l.name, ROUND((ST_Distance(l.geom, ST_SetSRID(ST_MakePoint(72.5714, 23.0402), 4326)::geography) / 1000.0)::numeric, 2) AS distance_km
   FROM cameras c
   JOIN locations l ON c.location_id = l.id
   WHERE ST_DWithin(l.geom, ST_SetSRID(ST_MakePoint(72.5714, 23.0402), 4326)::geography, 5000)
   ORDER BY distance_km ASC;
   ```

---

## 5. Cross-Camera Vehicle Tracking Engine

PHANTOM reconstructs vehicle trajectories strictly from timestamped observations across cameras without storing pre-baked routes:

```sql
SELECT 
    d.detected_at,
    v.normalized_plate,
    c.camera_code,
    l.name AS location_name,
    l.latitude,
    l.longitude,
    d.speed_estimate_kmph,
    d.frame_reference
FROM detections d
JOIN vehicles v ON d.entity_id = v.id
JOIN cameras c ON d.camera_id = c.id
JOIN locations l ON c.location_id = l.id
WHERE v.normalized_plate = 'GJ01AB1234'
ORDER BY d.detected_at ASC;
```

---

## 6. Security & Application Grants

- **Dedicated User**: `phantom_app` with DML permissions (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).
- **No Superuser for API**: The FastAPI backend does NOT use the `postgres` superuser.
- **No Plaintext Stream Credentials**: Camera stream URLs store vault/secret references (e.g. `vault://secrets/cctv/streams/...`).
- **Non-Destructive Deletions**: Incidents, evidence, audit logs, and cameras use `ON DELETE RESTRICT` or `ON DELETE SET NULL` to preserve forensic chain of custody.

---

## 7. Future FastAPI Connection Information (Step 2 Integration)

For the upcoming FastAPI backend in Step 2, connect using:

```env
# Database Connection URI (AsyncPG / SQLAlchemy)
DATABASE_URL=postgresql+asyncpg://phantom_app:phantom_app_secure_password_2026@localhost:5432/phantom
```
*(Production passwords should be loaded via environment variables or Docker secrets).*
