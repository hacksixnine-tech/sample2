-- ==============================================================================
-- PHANTOM MIGRATION 014: Alert Engine Model
-- ==============================================================================

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_code VARCHAR(100) NOT NULL UNIQUE,
    alert_type VARCHAR(100) NOT NULL CHECK (
        alert_type IN (
            'WATCHLIST_HIT',
            'ANPR_HOTLIST_MATCH',
            'GEO_FENCE_BREACH',
            'CAMERA_CRITICAL_FAILURE',
            'UNAUTHORIZED_ACCESS',
            'HIGH_SPEED_VIOLATION',
            'OTHER'
        )
    ),
    severity VARCHAR(50) NOT NULL DEFAULT 'HIGH' CHECK (
        severity IN ('LOW', 'INFO', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'NEW' CHECK (
        status IN ('NEW', 'ACKNOWLEDGED', 'INVESTIGATING', 'RESOLVED', 'DISMISSED')
    ),
    source_event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    source_match_id UUID REFERENCES matches(id) ON DELETE SET NULL,
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE RESTRICT,
    entity_id UUID REFERENCES entities(id) ON DELETE SET NULL,
    acknowledged_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    acknowledged_at TIMESTAMPTZ,
    resolved_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_alert_code ON alerts(alert_code);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_camera_id ON alerts(camera_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_entity_id ON alerts(entity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);

DROP TRIGGER IF EXISTS set_timestamp_alerts ON alerts;
CREATE TRIGGER set_timestamp_alerts
    BEFORE UPDATE ON alerts
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
