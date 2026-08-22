-- ==============================================================================
-- PHANTOM MIGRATION 012: Watchlist Entries
-- ==============================================================================

CREATE TABLE IF NOT EXISTS watchlist_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watchlist_id UUID NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    identifier VARCHAR(255) NOT NULL,            -- e.g. "GJ 01 AB 1234" or "AARAV SHARMA"
    normalized_identifier VARCHAR(255) NOT NULL, -- e.g. "GJ01AB1234" or "AARAVSHARMA"
    entity_type VARCHAR(50) NOT NULL CHECK (
        entity_type IN ('VEHICLE', 'PERSON', 'OBJECT', 'OTHER')
    ),
    case_reference_number VARCHAR(100),          -- FIR / Crime / GD No.
    fir_station VARCHAR(255),
    reason TEXT NOT NULL,
    priority VARCHAR(50) NOT NULL DEFAULT 'HIGH' CHECK (
        priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
    ),
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_watchlist_entries_valid_range CHECK (valid_until IS NULL OR valid_until >= valid_from)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_entries_watchlist_id ON watchlist_entries(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_entries_normalized ON watchlist_entries(normalized_identifier);
CREATE INDEX IF NOT EXISTS idx_watchlist_entries_type ON watchlist_entries(entity_type);
CREATE INDEX IF NOT EXISTS idx_watchlist_entries_is_active ON watchlist_entries(is_active);

DROP TRIGGER IF EXISTS set_timestamp_watchlist_entries ON watchlist_entries;
CREATE TRIGGER set_timestamp_watchlist_entries
    BEFORE UPDATE ON watchlist_entries
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
