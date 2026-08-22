# PHANTOM — Video Streaming & Bandwidth Architecture

This document describes the video distribution and streaming architecture of **PHANTOM**, designed to deliver low-latency live video to police command centers while preserving statewide network bandwidth.

---

## 1. Protocol Architecture Matrix

PHANTOM supports multiple heterogeneous video streaming protocols to accommodate diverse CCTV vendor ecosystems:

| Protocol | Ingestion Direction | Use Case | Latency | Bandwidth Overhead |
|---|:---:|---|:---:|:---:|
| **RTSP (TCP/UDP)** | Edge / Camera -> Gateway | Raw camera feed ingestion at edge gateways | 200–500ms | 2–6 Mbps / stream |
| **WebRTC (WHEP)** | Gateway -> Browser Client | Real-time live operator tactical viewing | **< 200ms** | 1.5–3 Mbps / active viewer |
| **HLS (LL-HLS)** | Gateway -> Storage & UI | DVR playback, historical review, and mobile clients | 2–4s | Adaptive Bitrate (ABR) |
| **ONVIF Profile S/G/T** | Edge Gateway <-> Camera | PTZ camera control, motion alarms, and time sync | Low | Control channel only |
| **HTTP-FLV / MJPEG** | Legacy Camera -> Gateway | Legacy city surveillance cameras | 500ms–1s | Variable |

---

## 2. On-Demand Streaming Paradigm (Zero Idle Bandwidth)

A core tenet of PHANTOM's streaming design is **Zero Idle Central Streaming**:
- Under normal operations, 80,000 CCTV streams are **NOT** pushed to the central state cloud.
- Video streams remain at the edge node or within the local NVR ring.
- Video streaming across the WAN occurs **strictly on-demand**:
  1. When an operator in the Command Control Center opens a camera for live inspection (via WebRTC).
  2. When an automated **CRITICAL Alert** triggers a 10-second pre/post incident evidence clip upload.
  3. When an investigator requests a historical video review for a specific time window.

This reduces central video bandwidth requirements from **320 Gbps** down to **< 500 Mbps** during peak active monitoring hours.

---

## 3. Media Gateway & Transcoding Pipeline

```
[ CCTV Camera ] (RTSP H.264 / H.265)
       │
       ▼
[ Media Gateway (MediaMTX / SRS Cluster) ]
       ├── Frame Grabber -> Local AI Inference Worker (YOLO / OCR)
       ├── WebRTC Publisher -> Low-Latency Browser Player (< 200ms)
       ├── HLS Segmenter -> Hot NVMe Buffer (Rolling 24h Circular Buffer)
       └── Snapshot Extractor -> SHA-256 Verified Frame Snapshots
```

---

## 4. Bandwidth Optimization Techniques

1. **Adaptive Bitrate (ABR) & Dynamic Profiles**:
   - Multi-camera grid views (e.g. 16-camera or 32-camera surveillance matrix) automatically switch to sub-stream resolution (480p / 360p @ 15fps, ~400 Kbps).
   - When an operator double-clicks a camera to expand to full-screen, the stream dynamically escalates to primary 1080p stream (4 Mbps).

2. **Adaptive Frame Rate Reduction**:
   - For PTZ cameras pointing at static highways or low-activity junctions during nighttime, cameras switch to 5 FPS until motion/AI detection triggers 25 FPS burst capture.

3. **H.265 / AV1 Compression**:
   - Edge encoders utilize hardware-accelerated H.265/HEVC encoding, achieving a 50% bitrate reduction over H.264 at identical perceptual quality.
