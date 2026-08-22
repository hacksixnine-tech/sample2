-- ==============================================================================
-- PHANTOM MIGRATION 010: Events Model (Real-time Stream / Queue Integration)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL CHECK (
        event_type IN (
            'VEHICLE_DETECTED',
            'PLATE_DETECTED',
            'PERSON_DETECTED',
            'WATCHLIST_MATCH',
            'CAMERA_OFFLINE',
            'CAMERA_DEGRADED',
            'INTRUSION',
            'OVER_SPEEDING',
            'WRONG_SIDE_DRIVING',
            'CONGESTION',
            'OBJECT_DETECTED',
            'OTHER'
        )
    ),
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE RESTRICT,
    entity_id UUID REFERENCES entities(id) ON DELETE SET NULL,
    detection_id UUID REFERENCES detections(id) ON DELETE SET NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(50) NOT NULL DEFAULT 'INFO' CHECK (
        severity IN ('LOW', 'INFO', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),
    description TEXT NOT NULL,
    processed_by_worker VARCHAR(100),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_camera_id ON events(camera_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_entity_id ON events(entity_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_occurred_at ON events(occurred_at DESC);
