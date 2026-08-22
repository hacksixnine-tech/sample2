# PHANTOM — Statewide Scalability Architecture (80,000 CCTV Cameras)

This document outlines the end-to-end distributed systems architecture designed to scale **PHANTOM** across all **33 districts of Gujarat**, accommodating **80,000+ continuous CCTV camera streams** without core network saturation or database exhaustion.

---

## 1. The Scale Challenge

Operating 80,000 CCTV cameras across a state generates astronomical data volumes if processed centrally:
- **Raw Video Bandwidth**: 80,000 cameras × 4 Mbps (1080p H.264) = **320 Gbps (40 GB/sec)**.
- **Continuous Frame Volume**: 80,000 cameras × 25 fps = **2,000,000 frames per second**.
- **Central Storage Requirement**: 40 GB/sec × 86,400s = **3.45 Petabytes per day**.

Centralized transmission and centralized AI inference on raw video at this scale is technically and economically unfeasible over statewide WAN links.

---

## 2. Distributed Edge-to-Cloud Tiered Architecture

PHANTOM solves this scale challenge through a **Three-Tiered Distributed Architecture**:

```
[ Tier 1: District Edge Nodes (33 Districts) ]
  ├── 80,000 Cameras on Local LAN/Fiber
  ├── Regional Edge Gateways (NVIDIA Jetson / x86 + T4 GPUs)
  ├── Local Frame Extraction & YOLO/OCR Inference (1-5 fps sampling)
  └── Lightweight JSON Metadata Egress (ANPR, Detections, Vectors)
                     │
                     ▼ (Encrypted WAN / 5G / State Fiber: < 2 Gbps Statewide)
[ Tier 2: Central Messaging & Stream Ingestion ]
  ├── Ingress API / Kafka / Redis Streams Cluster (Partitioned by District)
  ├── Dynamic Ingestion Workers & Deduplication Layer
  └── Real-Time In-Memory Watchlist Matching Engine
                     │
                     ▼
[ Tier 3: Core Database & Object Storage ]
  ├── PostGIS PostgreSQL Primary + 4 Read Replicas (Partitioned by District/Month)
  ├── In-Memory Hot Cache (Redis Cluster for Watchlists & Active Trajectories)
  └── MinIO / S3 Object Store for SHA-256 Frame Evidence & Snapshots
```

---

## 3. Tier 1: Regional Edge Processing

1. **Local Network Containment**:
   - Cameras stream locally over high-speed Municipal Corporation / Police fiber rings to **33 District Edge Data Centers** (e.g., Ahmedabad, Surat, Vadodara, Rajkot, Gandhinagar).
   - High-bitrate 1080p/4K video streams never leave the local district network under normal surveillance conditions.

2. **Edge AI Acceleration & Dynamic Frame Sampling**:
   - Edge gateways run lightweight containerized inference workers (YOLOv8 + TensorRT / ONNX Runtime).
   - Cameras operate on dynamic frame sampling:
     - **Static / Low-Traffic Scenes**: 1 to 2 frames per second (FPS).
     - **Motion-Triggered / High-Activity Scenes**: 5 to 10 FPS.
     - **Active Tracking Mode (Subject of Interest detected)**: Full 25 FPS burst.

3. **Metadata-Only Statewide Egress**:
   - Rather than streaming 4 Mbps video, the edge node transmits **lightweight JSON inference events** (~1.2 KB per vehicle sighting):
     - `camera_id`, `timestamp`, `normalized_plate`, `plate_confidence`, `vehicle_type`, `bbox`, `evidence_sha256_hash`.
   - **Statewide Ingestion Bandwidth**: 80,000 cameras × average 0.2 detections/sec × 1.2 KB = **~19.2 MB/sec (153.6 Mbps)** for the entire state of Gujarat (a 99.95% bandwidth reduction).

---

## 4. Tier 2: Ingestion Pipeline & Backpressure Control

1. **District-Partitioned Ingestion Queues**:
   - Central message brokers (Apache Kafka or Redis Streams) are partitioned across 33 district topics (`ingest.district.ahmedabad`, `ingest.district.surat`, etc.).
   - If an edge node undergoes a temporary network disconnect, it buffers metadata locally and flushes in batches upon reconnection without losing chronological fidelity.

2. **Idempotency & Deduplication Engine**:
   - Ingestion workers employ a 2-stage deduplication check:
     - **Stage 1 (In-Memory Redis Hash Ring)**: Fast O(1) deduplication of identical plates on the same camera within `AI_DEDUPE_WINDOW_SECONDS` (default: 5.0 seconds).
     - **Stage 2 (Database Level)**: `X-Inference-Event-Id` uniqueness check and savepoint rollback protection.

3. **Backpressure & Load Shedding**:
   - When queue depth exceeds safe thresholds during extreme traffic surges:
     1. Ingestion workers drop sub-threshold confidence detections (< 0.60) first.
     2. Retain all high-confidence ANPR and active watchlist target detections with 100% reliability.

---

## 5. Tier 3: Database Sharding & Partitioning

1. **Declarative PostgreSQL Partitioning**:
   - The high-volume tables (`detections`, `vehicle_observations`, `camera_health_logs`, `audit_logs`) are partitioned using **PostgreSQL Declarative Partitioning**:
     - **Composite Partitioning**: Partition by `district` (List) and sub-partition by `observed_at` (Range by Month).
   - Old partitions (> 180 days) are automatically detached, compressed with `pg_dump`/Parquet, and migrated to cold object storage.

2. **PostGIS Spatial Index Tuning**:
   - `GEOGRAPHY(Point, 4326)` columns are indexed with spatial R-Trees using PostgreSQL `SP-GiST` or `GIST` indexes with fillfactor 90.
   - Spatial bounding box queries (`ST_DWithin`) execute in **< 4ms** across millions of records.

3. **Read Replicas & CQRS Separation**:
   - **Primary Database**: Dedicated to continuous write ingestion, watchlist correlation, and critical alert commits.
   - **Read Replicas (4 Nodes)**: Serve GIS map visualization, dashboard aggregation queries, and historical investigation searches.

---

## 6. Tiered Evidence Storage Strategy

| Tier | Storage Media | Retention | Content | Access SLA |
|---|---|:---:|---|:---:|
| **Hot (Tier 1)** | NVMe SSD Object Store | 7 Days | Full-resolution keyframes and ANPR crops with SHA-256 digests | < 50ms |
| **Warm (Tier 2)** | Standard S3 / MinIO Cluster | 90 Days | Incident-linked snapshots, active investigation dossiers | < 300ms |
| **Cold (Tier 3)** | Encrypted Tape / Glacier Archive | 3–7 Years | Certified court-admissible evidence packages and audit logs | < 2 Hours |
