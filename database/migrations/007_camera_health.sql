-- ==============================================================================
-- PHANTOM MIGRATION 007: Camera Health Monitoring Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS camera_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL CHECK (
        status IN ('ONLINE', 'DEGRADED', 'OFFLINE', 'MAINTENANCE')
    ),
    latency_ms INT CHECK (latency_ms >= 0),
    packet_loss_pct NUMERIC(5, 2) CHECK (packet_loss_pct >= 0 AND packet_loss_pct <= 100),
    current_fps NUMERIC(5, 2) CHECK (current_fps >= 0),
    bitrate_kbps INT CHECK (bitrate_kbps >= 0),
    health_score NUMERIC(5, 2) CHECK (health_score >= 0 AND health_score <= 100),
    last_error TEXT,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_camera_health_camera_id ON camera_health(camera_id);
CREATE INDEX IF NOT EXISTS idx_camera_health_status ON camera_health(status);
CREATE INDEX IF NOT EXISTS idx_camera_health_checked_at ON camera_health(checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_camera_health_camera_checked ON camera_health(camera_id, checked_at DESC);
