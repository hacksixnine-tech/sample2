# PHANTOM // Hackathon Demonstration Guide & Judge Pitch

## 1. Fast 2–3 Minute Presentation Script

### ⏱️ Minute 0:00 – The Problem & Mission
> *"Judges, modern law enforcement agencies manage tens of thousands of CCTV feeds, but when a critical suspect vehicle moves across districts, investigators are forced to manually sift through hours of disjointed DVR footage. **PHANTOM** solves this by delivering an automated, statewide video intelligence and digital forensics platform engineered specifically for the 33 districts of Gujarat."*

### ⏱️ Minute 0:45 – Live Feed & Automated ANPR Hit
> *"Here on the **Live Monitoring Dashboard**, our stream gateway ingests Government CCTV feeds. Watch as a vehicle passes **CAM-014 on Surat Ring Road**: our YOLOv8 and OCR pipeline detects the plate `GJ05AB1234`, normalizes the format, correlates it against the statewide active watchlist in **under 40 milliseconds**, and fires a **Real-Time Critical Alert** directly to our command center."*

### ⏱️ Minute 1:30 – Cross-Camera Correlation & GIS Sighting Path
> *"Opening the **Vehicle Intelligence Workspace**, PHANTOM doesn't just show one sighting—it correlates the vehicle's chronological journey across multiple cameras: CAM-011 at 09:10, CAM-017 at 09:24, CAM-029 at 09:41, and CAM-034 at 10:03. On our **GIS Map Canvas**, the system reconstructs the **Observed Sighting Path** across 14.8 km, calculating time deltas and estimated transition speeds with full PostGIS spatial indexing."*

### ⏱️ Minute 2:15 – Digital Forensics & Certified Evidentiary Report
> *"In the **Forensics Workspace**, every evidence crop is protected with cryptographic **SHA-256 integrity verification**. With one click, the investigator creates an Incident Dossier, records tactical remarks, confirms the review classification, and exports a **Certified Tamper-Evident Forensic Report** bearing a unique cryptographic seal—all audited in an immutable append-only ledger."*

### ⏱️ Minute 2:45 – Statewide Scale & Conclusion
> *"By separating edge video processing from central metadata egress, PHANTOM slashes WAN bandwidth by **99.88%**, making it ready to scale from 50 cameras to **80,000 cameras** across Gujarat without WAN saturation. Thank you."*

---

## 2. Step-by-Step UI Demonstration Sequence

| Step | Navigation View | Action on Screen | Key Highlight for Judges |
| :---: | :--- | :--- | :--- |
| **1** | **Dashboard** | View top operational KPI cards & stream telemetry | Total cameras online, active alerts count, 24h sightings |
| **2** | **Live Monitoring** | Select Camera `CAM-014 (Surat Ring Road)` | Multi-profile streaming (`MEDIUM` 720p @ 1.5 Mbps) |
| **3** | **Alerts & Incidents**| Click Critical Alert `ALT-2026-081` | Real-time WebSocket delivery without manual page refresh |
| **4** | **Vehicle Tracking** | Query License Plate `GJ05AB1234` | Safe plate normalization (`gj 05 ab 1234` $\to$ `GJ05AB1234`) |
| **5** | **Chronological Timeline**| Review sequential sighting cards | Sighting transitions with time gap ($\Delta t$) & estimated speed |
| **6** | **GIS Route Canvas** | View reconstructed observed sighting path | PostGIS spatial geometry mapping with marker clustering |
| **7** | **Forensic Dossier** | Click `Verify Evidence Integrity` | SHA-256 hash checksum verified against immutable ledger |
| **8** | **Certified Report**| Click `Export Forensic Dossier Report` | Downloadable tamper-evident report with SHA-256 seal |
| **9** | **Audit Trail** | Open System Health & Audit logs | Complete chain-of-custody logging for every officer action |

---

## 3. Key Technical Differentiators (Why PHANTOM Wins)

1. **Vendor-Neutral CCTV Streaming**: Universal compatibility with RTSP, HLS, WebRTC, and Corp8 VMS feeds.
2. **Deterministic Cross-Camera Correlation**: Reconstructs vehicle sighting paths without making false claims about unseen road segments.
3. **Bandwidth Optimization**: Edge computing keeps high-bitrate video on local district networks while sending only metadata (< 150 Mbps statewide) to the central command hub.
4. **Evidentiary Rigor**: Cryptographic SHA-256 integrity seals on evidence crops and generated investigation reports.
5. **Zero-Fluff Production Architecture**: PostgreSQL 16 + PostGIS 3.4, FastAPI Asyncpg connection pools, strict RBAC privilege escalation protection, and sliding window rate limiting.
