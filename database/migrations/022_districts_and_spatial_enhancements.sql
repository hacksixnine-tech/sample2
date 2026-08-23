-- ==============================================================================
-- PHANTOM MIGRATION 022: Normalized Districts & Spatial Registry Enhancements
-- ==============================================================================

-- 1. Districts Registry Table
CREATE TABLE IF NOT EXISTS districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL UNIQUE,
    state VARCHAR(100) NOT NULL DEFAULT 'Gujarat',
    zone VARCHAR(100),
    headquarters VARCHAR(100),
    centroid_lat NUMERIC(10, 7) NOT NULL CHECK (centroid_lat >= -90.0 AND centroid_lat <= 90.0),
    centroid_lng NUMERIC(10, 7) NOT NULL CHECK (centroid_lng >= -180.0 AND centroid_lng <= 180.0),
    geom GEOGRAPHY(Polygon, 4326),
    centroid_geom GEOGRAPHY(Point, 4326) GENERATED ALWAYS AS (
        ST_SetSRID(ST_MakePoint(centroid_lng, centroid_lat), 4326)::geography
    ) STORED,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Spatial and standard indices for districts
CREATE INDEX IF NOT EXISTS idx_districts_code ON districts(district_code);
CREATE INDEX IF NOT EXISTS idx_districts_name ON districts(name);
CREATE INDEX IF NOT EXISTS idx_districts_centroid_geom ON districts USING GIST(centroid_geom);
CREATE INDEX IF NOT EXISTS idx_districts_geom ON districts USING GIST(geom);

DROP TRIGGER IF EXISTS set_timestamp_districts ON districts;
CREATE TRIGGER set_timestamp_districts
    BEFORE UPDATE ON districts
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();

-- 2. Enhance Cameras Table with Asset Management & Spatial Fields if missing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'external_id') THEN
        ALTER TABLE cameras ADD COLUMN external_id VARCHAR(100);
        CREATE INDEX IF NOT EXISTS idx_cameras_external_id ON cameras(external_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'coverage_radius_meters') THEN
        ALTER TABLE cameras ADD COLUMN coverage_radius_meters NUMERIC(8, 2) NOT NULL DEFAULT 150.0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'has_ptz') THEN
        ALTER TABLE cameras ADD COLUMN has_ptz BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'has_audio') THEN
        ALTER TABLE cameras ADD COLUMN has_audio BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'has_night_vision') THEN
        ALTER TABLE cameras ADD COLUMN has_night_vision BOOLEAN NOT NULL DEFAULT TRUE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'ai_capabilities') THEN
        ALTER TABLE cameras ADD COLUMN ai_capabilities TEXT[] DEFAULT ARRAY['ANPR', 'CROWD_DENSITY', 'OBJECT_DETECTION']::TEXT[];
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'source_system') THEN
        ALTER TABLE cameras ADD COLUMN source_system VARCHAR(100) DEFAULT 'CORP8_LIVE_CLOUD';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'last_health_check') THEN
        ALTER TABLE cameras ADD COLUMN last_health_check TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'cameras' AND column_name = 'last_seen') THEN
        ALTER TABLE cameras ADD COLUMN last_seen TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;
