# PHANTOM GIS & Spatial Intelligence Engine

**PHANTOM** utilizes **PostGIS 3.4** on **PostgreSQL 16** with EPSG:4326 (WGS 84) coordinate referencing for all statewide geospatial operations.

---

## 1. Spatial Data Model

- **Location Points**: Stored in `locations.geom` as `GEOGRAPHY(Point, 4326)`.
- **Generated Column**:
  ```sql
  geom GEOGRAPHY(Point, 4326) GENERATED ALWAYS AS (
      ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
  ) STORED
  ```
- **Spatial Indexing**: Native GiST index on `locations.geom` (`idx_locations_geom`).

---

## 2. Spatial Query Primitives

### 2.1 Find Nearby Cameras
```sql
SELECT 
    c.id, c.camera_code, c.name, l.latitude, l.longitude,
    ROUND(ST_Distance(l.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)::numeric, 2)::float as distance_meters
FROM cameras c
JOIN locations l ON c.location_id = l.id
WHERE ST_DWithin(l.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
ORDER BY distance_meters ASC
LIMIT :limit;
```

### 2.2 Endpoints

| Method | Endpoint | Query Parameters |
|---|---|---|
| `GET` | `/api/v1/locations/nearby` | `latitude`, `longitude`, `radius_meters` (default 5000), `limit` |
| `GET` | `/api/v1/cameras/nearby` | `latitude`, `longitude`, `radius_meters` (default 5000), `limit` |
| `GET` | `/api/v1/gis/cameras/nearby` | `latitude`, `longitude`, `radius_meters` (default 5000), `limit` |
| `GET` | `/api/v1/gis/coverage` | Statewide district & department camera distribution |
