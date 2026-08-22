-- ==============================================================================
-- PHANTOM MIGRATION 015: Incidents Management Model
-- ==============================================================================

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_code VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(50) NOT NULL DEFAULT 'HIGH' CHECK (
        severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),
    status VARCHAR(50) NOT NULL DEFAULT 'OPEN' CHECK (
        status IN ('OPEN', 'INVESTIGATING', 'IN_PROGRESS', 'CONTAINED', 'ESCALATED', 'CLOSED', 'ARCHIVED')
    ),
    assigned_department_id UUID REFERENCES departments(id) ON DELETE RESTRICT,
    assigned_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,
    closing_notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_incidents_closed_time CHECK (closed_at IS NULL OR closed_at >= occurred_at)
);

CREATE INDEX IF NOT EXISTS idx_incidents_code ON incidents(incident_code);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned_user ON incidents(assigned_user_id);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned_dept ON incidents(assigned_department_id);

DROP TRIGGER IF EXISTS set_timestamp_incidents ON incidents;
CREATE TRIGGER set_timestamp_incidents
    BEFORE UPDATE ON incidents
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
