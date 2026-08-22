-- ==============================================================================
-- PHANTOM MIGRATION 005: CCTV Cameras Registry
-- ==============================================================================

CREATE TABLE IF NOT EXISTS cameras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE RESTRICT,
    camera_type VARCHAR(50) NOT NULL CHECK (
        camera_type IN ('ANPR', 'PTZ', 'FIXED', 'IP', 'BODY_WORN', 'DRONE', 'THERMAL', 'OTHER')
    ),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    mac_address VARCHAR(50),
    ip_address INET,
    ownership VARCHAR(100) NOT NULL DEFAULT 'Gujarat Government',
    installation_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE' CHECK (
        status IN ('ACTIVE', 'INACTIVE', 'MAINTENANCE', 'DECOMMISSIONED')
    ),
    connectivity_status VARCHAR(50) NOT NULL DEFAULT 'ONLINE' CHECK (
        connectivity_status IN ('ONLINE', 'DEGRADED', 'OFFLINE', 'UNKNOWN')
    ),
    storage_type VARCHAR(50) NOT NULL DEFAULT 'EDGE_AND_CENTRAL',
    retention_days INT NOT NULL DEFAULT 30 CHECK (retention_days > 0),
    field_of_view_deg NUMERIC(5, 2),
    azimuth_angle_deg NUMERIC(5, 2),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cameras_camera_code ON cameras(camera_code);
CREATE INDEX IF NOT EXISTS idx_cameras_department_id ON cameras(department_id);
CREATE INDEX IF NOT EXISTS idx_cameras_location_id ON cameras(location_id);
CREATE INDEX IF NOT EXISTS idx_cameras_camera_type ON cameras(camera_type);
CREATE INDEX IF NOT EXISTS idx_cameras_status ON cameras(status);
CREATE INDEX IF NOT EXISTS idx_cameras_connectivity ON cameras(connectivity_status);

DROP TRIGGER IF EXISTS set_timestamp_cameras ON cameras;
CREATE TRIGGER set_timestamp_cameras
    BEFORE UPDATE ON cameras
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
