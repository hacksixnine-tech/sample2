# PHANTOM — Digital Forensics & Investigation Intelligence Blueprint

## 1. Executive Summary & Forensic Philosophy

The **PHANTOM Digital Forensics & Investigation Intelligence Workspace** bridges real-time automated video analytics with law enforcement evidentiary investigation workflows. It allows an authorized investigator or intelligence officer to pivot seamlessly across multiple entry points:

$$\text{Alert / Plate / Camera / Incident / District / Time Range} \longrightarrow \text{Sightings} \longrightarrow \text{Timeline} \longrightarrow \text{GIS Route} \longrightarrow \text{Evidence} \longrightarrow \text{Certified Forensic Report}$$

---

## 2. Multi-Source Investigation Entry Points

Investigators can initiate inquiries through 8 distinct operational starting points:

```
+-----------------------------------------------------------------------------------+
|                        INVESTIGATION ENTRY POINTS                                 |
+-------------------+--------------------+--------------------+---------------------+
| 1. License Plate  | 2. Active Alert    | 3. Incident Code   | 4. Specific Camera  |
|    (GJ05AB1234)   |    (ALT-2026-081)  |    (INC-2026-042)  |    (CAM-014 Surat)  |
+-------------------+--------------------+--------------------+---------------------+
| 5. District Name  | 6. Geo-Coordinates | 7. Time Window     | 8. Detection Event  |
|    (Ahmedabad)    |    (ST_DWithin 2km)|    (08:00 - 12:00) |    (UUID / ANPR Hit)|
+-------------------+--------------------+--------------------+---------------------+
```

### Safe License Plate Normalization
- Safe transformation: `GJ 05 AB 1234` $\longrightarrow$ `GJ05AB1234` (case-insensitive, whitespace and special character stripping).
- **Rule**: Raw plate strings are preserved alongside normalized values in the database for auditing and optical character recognition (OCR) fidelity.

---

## 3. Cross-Camera Correlation & Forensic Timeline

### Chronological Sighting Sequence
Sightings are grouped deterministically across the 80,000-camera statewide grid without assuming continuous physical routes:

```
[ CAM-011: Ring Road West ]  ──(14 mins @ 38.4 km/h)──> [ CAM-017: Varachha Junction ]
         09:10:14                                                09:24:22
            │                                                       │
            ▼                                                       ▼
[ CAM-029: Surat Highway ]   ──(22 mins @ 54.1 km/h)──> [ CAM-034: Toll Plaza South ]
         09:41:05                                                10:03:19
```

### Transition Telemetry & Speed Disclaimers
- Straight-line distance $d = \text{ST\_DistanceSphere}(p_1, p_2)$ in meters.
- Time delta $\Delta t = t_2 - t_1$ in seconds.
- Estimated transition speed:
$$\text{Speed (km/h)} = \left(\frac{d}{\Delta t}\right) \times 3.6$$
- **Mandatory Demarcation**: Labeled explicitly as `ESTIMATED AVERAGE SPEED BETWEEN CAMERAS` and `OBSERVED SIGHTING PATH`.

---

## 4. Evidence Management & Cryptographic Chain of Custody

### Evidence Object Architecture
Every physical frame or crop collected by PHANTOM is indexed with immutable metadata:

| Field | Description | Example |
| :--- | :--- | :--- |
| `evidence_id` | Unique UUID | `7c9e6679-7425-40de-944b-e07fc1f90ae7` |
| `source` | Originating subsystem | `ANPR_YOLOV8_OCR` |
| `camera_id` | Capture camera UUID | `d3b07384-d113-484d-a9da-10330dc3e3a1` |
| `detection_id`| Associated detection | `e4d909c2-9014-44b2-92cf-b5b5b291d904` |
| `algorithm` | Hash standard | `SHA-256` |
| `sha256_hash`| Cryptographic digest | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `created_at` | Timestamp in UTC | `2026-08-23T08:42:00Z` |

### Integrity Verification Protocol (`GET /api/v1/evidence/{id}/verify`)
1. Fetches recorded hash from the evidence table.
2. Computes runtime SHA-256 digest of binary evidence/metadata payload.
3. Compares digests:
   - Equal $\longrightarrow$ `INTEGRITY_VERIFIED`
   - Mismatch $\longrightarrow$ `INTEGRITY_CHECK_FAILED`
4. Writes an immutable audit entry (`VERIFY_EVIDENCE`) recording operator ID, IP, and outcome.

---

## 5. False-Positive Classification Workflow

Investigators can classify AI detections directly without mutating raw video or optical logs:

- `CONFIRMED`: Validated target sighting.
- `FALSE_POSITIVE`: Misread character, reflection, or non-target vehicle.
- `NEEDS_REVIEW`: Ambiguous read requiring secondary human review.

```json
{
  "classification": "CONFIRMED",
  "notes": "Visual confirmation of Hyundai Creta Silver matching FIR #402/2026",
  "reviewed_by": "00000000-0000-0000-0000-000000000001",
  "reviewed_at": "2026-08-23T23:30:00Z"
}
```

---

## 6. Certified Forensic Investigation Report (`GET /api/v1/investigations/vehicle/{id}/report`)

Generates a complete, downloadable, tamper-evident investigation dossier:

1. **Header & Metadata**: Report UUID, Investigation Code, Timestamp, Requesting Officer.
2. **Entity Profile**: Plate, Vehicle Make, Model, Color, Registered Owner, Risk Level.
3. **Chronological Timeline**: Multi-source sightings, alerts, and incident links.
4. **GIS Route Telemetry**: Ordered camera coordinates, time deltas, and anomaly indicators.
5. **Evidence Digest Table**: All linked frame crops with respective SHA-256 hashes.
6. **Investigator Notes & Audit History**: Timestamped officer remarks and status lifecycle.
7. **Cryptographic Report Seal**:
$$\text{SHA-256}(\text{Report UUID} + \text{Plate} + \text{Timestamp} + \text{Officer} + \text{Evidence Count})$$
