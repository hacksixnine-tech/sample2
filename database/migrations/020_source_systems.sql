-- ==============================================================================
-- PHANTOM MIGRATION 020: External Source Systems & Source Preservation
-- ==============================================================================

CREATE TABLE IF NOT EXISTS source_systems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(100) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    source_type VARCHAR(100) NOT NULL DEFAULT 'EXTERNAL_PROVIDED_CCTV_SOURCE',
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE' CHECK (
        status IN ('ACTIVE', 'INACTIVE', 'DEGRADED', 'MAINTENANCE')
    ),
    auth_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_systems_code ON source_systems(code);
CREATE INDEX IF NOT EXISTS idx_source_systems_status ON source_systems(status);

-- Add source mapping columns to cameras table if they don't already exist
ALTER TABLE cameras 
    ADD COLUMN IF NOT EXISTS source_system_id UUID REFERENCES source_systems(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS source_camera_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS source_reference VARCHAR(255),
    ADD COLUMN IF NOT EXISTS source_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS last_connected_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_cameras_source_system ON cameras(source_system_id, source_camera_id);

DROP TRIGGER IF EXISTS set_timestamp_source_systems ON source_systems;
CREATE TRIGGER set_timestamp_source_systems
    BEFORE UPDATE ON source_systems
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();

-- Seed the official external provided source system
INSERT INTO source_systems (id, name, code, base_url, source_type, status, metadata)
VALUES (
    '20000000-0000-0000-0000-000000000001',
    'CCTV Control Room',
    'SRC-CORP8-CONTROL-ROOM',
    'https://live.corp8.cloud/',
    'EXTERNAL_PROVIDED_CCTV_SOURCE',
    'ACTIVE',
    '{"provider": "Gujarat Hackathon Provided Source", "discovery_endpoint": "/api/cameras", "protocols": ["RTSP", "WebRTC", "HLS"]}'::jsonb
)
ON CONFLICT (code) DO UPDATE SET
    base_url = EXCLUDED.base_url,
    status = EXCLUDED.status,
    metadata = EXCLUDED.metadata;
