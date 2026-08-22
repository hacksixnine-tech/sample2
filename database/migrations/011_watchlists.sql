-- ==============================================================================
-- PHANTOM MIGRATION 011: Watchlists System
-- ==============================================================================

CREATE TABLE IF NOT EXISTS watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    code VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL CHECK (
        category IN (
            'STOLEN_VEHICLES',
            'WANTED_VEHICLES',
            'BLACKLISTED_VEHICLES',
            'WANTED_PERSONS',
            'MISSING_PERSONS',
            'SUSPECT_WATCHLIST',
            'TRAFFIC_OFFENDERS',
            'VIP_MONITORING',
            'OTHER'
        )
    ),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    description TEXT,
    priority VARCHAR(50) NOT NULL DEFAULT 'HIGH' CHECK (
        priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_watchlists_code ON watchlists(code);
CREATE INDEX IF NOT EXISTS idx_watchlists_category ON watchlists(category);
CREATE INDEX IF NOT EXISTS idx_watchlists_department_id ON watchlists(department_id);
CREATE INDEX IF NOT EXISTS idx_watchlists_is_active ON watchlists(is_active);

DROP TRIGGER IF EXISTS set_timestamp_watchlists ON watchlists;
CREATE TRIGGER set_timestamp_watchlists
    BEFORE UPDATE ON watchlists
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
