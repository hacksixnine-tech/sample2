-- ==============================================================================
-- PHANTOM MIGRATION 016: Evidence Metadata Model (S3 / MinIO Object Storage)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_code VARCHAR(100) NOT NULL UNIQUE,
    evidence_type VARCHAR(50) NOT NULL CHECK (
        evidence_type IN ('VIDEO_CLIP', 'FRAME_SNAPSHOT', 'CROPPED_IMAGE', 'ANPR_READING', 'TELEMETRY_LOG', 'DOCUMENT', 'OTHER')
    ),
    storage_provider VARCHAR(50) NOT NULL DEFAULT 'S3_COMPATIBLE' CHECK (
        storage_provider IN ('S3_COMPATIBLE', 'MINIO', 'CEPH', 'LOCAL_STORAGE', 'EXTERNAL_URL')
    ),
    bucket_name VARCHAR(100) NOT NULL DEFAULT 'phantom-evidence',
    object_key VARCHAR(500) NOT NULL,
    file_format VARCHAR(50) NOT NULL,
    file_size_bytes BIGINT CHECK (file_size_bytes >= 0),
    file_hash_sha256 VARCHAR(64) NOT NULL, -- Cryptographic hash for chain of custody and forensic integrity
    captured_at TIMESTAMPTZ NOT NULL,
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE RESTRICT,
    detection_id UUID REFERENCES detections(id) ON DELETE SET NULL,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    chain_of_custody_notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_code ON evidence(evidence_code);
CREATE INDEX IF NOT EXISTS idx_evidence_camera_id ON evidence(camera_id);
CREATE INDEX IF NOT EXISTS idx_evidence_detection_id ON evidence(detection_id);
CREATE INDEX IF NOT EXISTS idx_evidence_captured_at ON evidence(captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_file_hash ON evidence(file_hash_sha256);
