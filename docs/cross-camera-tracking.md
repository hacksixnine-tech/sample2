# PHANTOM — Cross-Camera Tracking & Trajectory Analysis

This document describes the algorithms, data models, and analytical distinctions governing cross-camera entity tracking and vehicle journey reconstruction in **PHANTOM**.

---

## 1. Fundamental Architectural Principle

> **CRITICAL SCIENTIFIC INTEGRITY PRINCIPLE:**
> PHANTOM strictly distinguishes between **factual observed camera sightings** and **inferred / estimated travel corridors**. The platform never synthesizes or misrepresents an interpolated road path as an observed physical sighting.

| Category | Definition | Data Source | Confidence Level |
|---|---|---|:---:|
| `OBSERVED_CAMERA_SEQUENCE` | Factual, verified sightings of an entity at specific physical camera coordinates at recorded timestamps. | PostGIS `vehicle_observations` + AI OCR detection | **100% Deterministic Fact** |
| `ESTIMATED_ROUTE` | Projected travel corridor between two discrete camera sightings based on geographic shortest path or road network topology. | OSRM / PostGIS `ST_MakeLine` / Road graph interpolation | **Probabilistic Estimation** |

---

## 2. Chronological Trajectory Assembly Algorithm

When an investigator queries the movement history of a target vehicle (`GET /api/v1/investigations/dossier` or `GET /api/v1/anpr/history`):

1. **Sighting Fetch & Deduplication**:
   - Query all `vehicle_observations` for `normalized_plate` across all cameras, ordered chronologically (`observed_at ASC`).
   - Group consecutive sightings at the same camera within a 30-second window to prevent duplicate trajectory vertices.

2. **Distance & Kinematics Computation**:
   - For every consecutive sighting pair $(S_i, S_{i+1})$ at cameras $(C_i, C_{i+1})$:
     - **Haversine Distance**: Compute geodesic surface distance:
       $$d = 2 R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
     - **Time Delta**: $\Delta t = t_{i+1} - t_i$ (seconds).
     - **Average Travel Speed**: $v = \frac{d}{\Delta t} \times 3.6$ (km/h).

3. **Anomaly & Speed Flagging**:
   - If calculated speed exceeds physical road feasibility (> 160 km/h on urban roads or > 220 km/h on expressways), the hop is flagged as `POTENTIAL_CLONED_PLATE_ANOMALY` or `IMPROBABLE_TRANSIT`.

---

## 3. Trajectory Data Structure

```json
{
  "vehicle_id": "848e0fe9-4e00-47b8-80f4-8da0bf9b7944",
  "normalized_plate": "GJ01AB1234",
  "trajectory_type": "OBSERVED_CAMERA_SEQUENCE",
  "total_sightings": 4,
  "first_seen_at": "2026-08-22T08:15:00Z",
  "last_seen_at": "2026-08-22T08:42:00Z",
  "total_distance_km": 14.82,
  "legs": [
    {
      "from_camera": { "id": "CAM-001", "name": "SG Highway Junction", "lat": 23.033, "lon": 72.502 },
      "to_camera": { "id": "CAM-002", "name": "Iskcon Crossroads", "lat": 23.028, "lon": 72.507 },
      "distance_meters": 780.4,
      "transit_time_seconds": 90,
      "average_speed_kmh": 31.2,
      "evidence_reference": "evd:EVD-9812A4B1"
    }
  ]
}
```

---

## 4. Multi-Camera Dossier Export

The investigation service compiles the complete intelligence footprint of an entity into an exportable court dossier containing:
1. Complete Sighting Chronology with PostGIS coordinates.
2. Verified high-resolution frame snapshot references and SHA-256 digests.
3. Associated Watchlist entries, FIR case files, and active Alert histories.
4. Linked Incidents and Investigating Officer notes.
