# PHANTOM — Evidence Management & Chain of Custody Architecture

This document specifies the technical architecture, cryptographic integrity guarantees, and legal compliance standards governing digital evidence handling in **PHANTOM**.

---

## 1. Core Principles of Evidence Handling

1. **Zero Binary Storage in Core Relational Database**:
   - PostgreSQL/PostGIS stores **strictly metadata, cryptographic hashes, timestamps, and storage pointers**.
   - Video files, full-frame snapshots, and audio streams are stored in S3/MinIO compliant object storage.

2. **Immediate Cryptographic Hashing at Ingestion**:
   - Every video clip, frame snapshot, and OCR crop is hashed using **SHA-256** at the exact moment of creation or edge extraction.
   - The resulting hash digest is written to the immutable `evidence` database record.

3. **Tamper-Evident Chain of Custody**:
   - Every read, view, download, export, and status change generates an immutable `audit_logs` record containing:
     - `user_id`, `officer_badge_number`, `department_id`, `ip_address`, `user_agent`, `timestamp`, `action` (`VIEW_EVIDENCE`, `EXPORT_EVIDENCE`, etc.).

---

## 2. Evidence Data Model & Schema

```sql
CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_code VARCHAR(100) NOT NULL UNIQUE,
    evidence_type VARCHAR(100) NOT NULL, -- FRAME_SNAPSHOT, VIDEO_CLIP, ANPR_CROP
    storage_provider VARCHAR(50) NOT NULL, -- S3, MINIO, LOCAL_STORE
    bucket_name VARCHAR(100) NOT NULL,
    object_key VARCHAR(500) NOT NULL,
    file_format VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_hash_sha256 VARCHAR(64) NOT NULL, -- Cryptographic digest
    hash_algorithm VARCHAR(20) DEFAULT 'SHA-256',
    captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
    camera_id UUID REFERENCES cameras(id),
    incident_id UUID REFERENCES incidents(id),
    public_reference VARCHAR(150) UNIQUE,
    retention_days INT DEFAULT 90,
    is_demo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Compliance with Legal Admissibility (Section 65B Indian Evidence Act)

To meet the legal threshold for digital evidence admissibility in judicial proceedings:

1. **Automated Section 65B Electronic Certificate Generation**:
   - PHANTOM provides an automated export format that bundles:
     - The raw media file with matching SHA-256 checksum.
     - System hardware & OS identifier of the capturing server.
     - Complete cryptographic audit log of the camera feed from ingestion to export.
     - Digital signature of the investigating officer.

2. **Integrity Verification on Retrieval**:
   - Whenever an investigator downloads an evidence package, PHANTOM re-calculates the SHA-256 hash of the object stored in MinIO/S3 and asserts match against `evidence.file_hash_sha256`.
   - If a mismatch occurs, the download is blocked and a **CRITICAL_SECURITY_ALERT** is dispatched to the System Auditor.

---

## 4. Tiered Storage Lifecycle & Retention

| Stage | Retention Window | Storage Layer | Encryption | Integrity Policy |
|---|:---:|---|:---:|:---:|
| **Active / Hot** | 0 – 30 Days | NVMe / High-Speed S3 Object Pool | AES-256 (GCM) | Real-time SHA-256 checksum check |
| **Investigation / Warm**| 31 – 180 Days | Standard MinIO / S3 Standard | AES-256 (GCM) | Monthly background integrity patrol |
| **Court Hold / Cold** | Up to 7 Years | S3 Glacier / Write-Once-Read-Many (WORM) | AES-256 (GCM) | Cryptographically sealed export bundle |
