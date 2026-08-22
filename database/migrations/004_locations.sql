-- ==============================================================================
-- PHANTOM MIGRATION 004: Locations Table (GIS / PostGIS)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    state VARCHAR(100) NOT NULL DEFAULT 'Gujarat',
    district VARCHAR(100) NOT NULL,
    taluka VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    zone VARCHAR(100),
    ward VARCHAR(100),
    address TEXT,
    landmark TEXT,
    postal_code VARCHAR(20),
    latitude NUMERIC(10, 7) NOT NULL CHECK (latitude >= -90.0 AND latitude <= 90.0),
    longitude NUMERIC(10, 7) NOT NULL CHECK (longitude >= -180.0 AND longitude <= 180.0),
    geom GEOGRAPHY(Point, 4326) GENERATED ALWAYS AS (
        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
    ) STORED,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Spatial GiST Index for high-performance radius and polygon searches
CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_locations_district ON locations(district);
CREATE INDEX IF NOT EXISTS idx_locations_city ON locations(city);

DROP TRIGGER IF EXISTS set_timestamp_locations ON locations;
CREATE TRIGGER set_timestamp_locations
    BEFORE UPDATE ON locations
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
