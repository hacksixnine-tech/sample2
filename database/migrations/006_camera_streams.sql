-- ==============================================================================
-- PHANTOM MIGRATION 006: Camera Streams Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS camera_streams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    protocol VARCHAR(50) NOT NULL CHECK (
        protocol IN ('RTSP', 'HLS', 'WEBRTC', 'HTTP', 'ONVIF', 'VENDOR_API', 'OTHER')
    ),
    stream_url VARCHAR(500) NOT NULL,
    secret_ref VARCHAR(255), -- Reference to vault/env secret key; never plaintext secrets
    resolution VARCHAR(50) NOT NULL DEFAULT '1080p',
    fps NUMERIC(5, 2) NOT NULL DEFAULT 25.0 CHECK (fps > 0),
    codec VARCHAR(50) NOT NULL DEFAULT 'H264',
    bitrate_kbps INT,
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_camera_streams_camera_id ON camera_streams(camera_id);
CREATE INDEX IF NOT EXISTS idx_camera_streams_protocol ON camera_streams(protocol);
CREATE INDEX IF NOT EXISTS idx_camera_streams_is_active ON camera_streams(is_active);

DROP TRIGGER IF EXISTS set_timestamp_camera_streams ON camera_streams;
CREATE TRIGGER set_timestamp_camera_streams
    BEFORE UPDATE ON camera_streams
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
