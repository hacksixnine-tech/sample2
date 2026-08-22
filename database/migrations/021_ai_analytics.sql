-- ==============================================================================
-- PHANTOM MIGRATION 021: AI Analytics, ANPR Observations, Evidence Integrity
-- Backend Step 5 — detections, vehicles, observations, evidence, ingest idempotency
-- ==============================================================================

-- -----------------------------------------------------------------------------
-- Detections: PHANTOM class types, ingest identity, demo flag, performance
-- -----------------------------------------------------------------------------
ALTER TABLE detections DROP CONSTRAINT IF EXISTS detections_detection_type_check;
ALTER TABLE detections ADD CONSTRAINT detections_detection_type_check CHECK (
    detection_type IN (
        'VEHICLE',
        'LICENSE_PLATE',
        'FACE',
        'PERSON',
        'OBJECT',
        'WEAPON',
        'CROWD',
        'OTHER',
        'CAR',
        'TRUCK',
        'BUS',
        'MOTORCYCLE',
        'BICYCLE',
        'OTHER_VEHICLE'
    )
);

ALTER TABLE detections ADD COLUMN IF NOT EXISTS object_class VARCHAR(50);
ALTER TABLE detections ADD COLUMN IF NOT EXISTS inference_event_id VARCHAR(128);
ALTER TABLE detections ADD COLUMN IF NOT EXISTS source_camera_id VARCHAR(100);
ALTER TABLE detections ADD COLUMN IF NOT EXISTS source_system_id UUID REFERENCES source_systems(id) ON DELETE SET NULL;
ALTER TABLE detections ADD COLUMN IF NOT EXISTS inference_time_ms NUMERIC(12, 3);
ALTER TABLE detections ADD COLUMN IF NOT EXISTS device VARCHAR(20);
ALTER TABLE detections ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE detections ADD COLUMN IF NOT EXISTS anpr_claimed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE detections ADD COLUMN IF NOT EXISTS evidence_id UUID REFERENCES evidence(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_detections_inference_event ON detections(inference_event_id);
CREATE INDEX IF NOT EXISTS idx_detections_object_class_time ON detections(object_class, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_detections_is_demo ON detections(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_detections_camera_type_time ON detections(camera_id, detection_type, detected_at DESC);

COMMENT ON COLUMN detections.object_class IS 'Normalized PHANTOM class (CAR, TRUCK, PERSON, LICENSE_PLATE, ...). Model-specific names must not be stored here.';
COMMENT ON COLUMN detections.is_demo IS 'TRUE when produced by DEMO_AI_MODE. Never treat as live government CCTV detections.';

-- -----------------------------------------------------------------------------
-- Events: ANPR_RECOGNIZED (watchlist matching remains Step 6)
-- -----------------------------------------------------------------------------
ALTER TABLE events DROP CONSTRAINT IF EXISTS events_event_type_check;
ALTER TABLE events ADD CONSTRAINT events_event_type_check CHECK (
    event_type IN (
        'VEHICLE_DETECTED',
        'PLATE_DETECTED',
        'PERSON_DETECTED',
        'ANPR_RECOGNIZED',
        'OBJECT_DETECTED',
        'WATCHLIST_MATCH',
        'CAMERA_OFFLINE',
        'CAMERA_DEGRADED',
        'INTRUSION',
        'OVER_SPEEDING',
        'WRONG_SIDE_DRIVING',
        'CONGESTION',
        'OTHER'
    )
);

ALTER TABLE events ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT FALSE;

-- -----------------------------------------------------------------------------
-- Vehicles: unique normalized plate identity (no row per detection)
-- -----------------------------------------------------------------------------
DROP INDEX IF EXISTS idx_vehicles_normalized_plate;
CREATE UNIQUE INDEX IF NOT EXISTS idx_vehicles_normalized_plate_unique ON vehicles(normalized_plate);

-- -----------------------------------------------------------------------------
-- Vehicle observations (sightings) — separate from raw detections
-- Unknown plates use observation_identity instead of inventing a vehicle_id
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicle_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE SET NULL,
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE RESTRICT,
    location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    detection_id UUID REFERENCES detections(id) ON DELETE SET NULL,
    evidence_id UUID REFERENCES evidence(id) ON DELETE SET NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    raw_plate VARCHAR(50),
    normalized_plate VARCHAR(50),
    plate_confidence NUMERIC(5, 4) CHECK (plate_confidence IS NULL OR (plate_confidence >= 0.0 AND plate_confidence <= 1.0)),
    vehicle_confidence NUMERIC(5, 4) CHECK (vehicle_confidence IS NULL OR (vehicle_confidence >= 0.0 AND vehicle_confidence <= 1.0)),
    frame_reference VARCHAR(500),
    detection_reference VARCHAR(128),
    observation_identity VARCHAR(255),
    inference_event_id VARCHAR(128),
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    anpr_claimed BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vobs_vehicle_time ON vehicle_observations(vehicle_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_vobs_camera_time ON vehicle_observations(camera_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_vobs_plate_time ON vehicle_observations(normalized_plate, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_vobs_observed_at ON vehicle_observations(observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_vobs_inference_event ON vehicle_observations(inference_event_id);
CREATE INDEX IF NOT EXISTS idx_vobs_identity ON vehicle_observations(observation_identity);
CREATE INDEX IF NOT EXISTS idx_vobs_camera_plate_time ON vehicle_observations(camera_id, normalized_plate, observed_at DESC);

COMMENT ON TABLE vehicle_observations IS 'Per-sighting ANPR/vehicle observations. Deduplicated by camera + plate + time window. Unknown plates do not create vehicle entities.';

-- -----------------------------------------------------------------------------
-- Evidence integrity metadata (no media blobs in PostgreSQL)
-- -----------------------------------------------------------------------------
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS hash_algorithm VARCHAR(32) NOT NULL DEFAULT 'SHA-256';
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS is_demo BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS retention_days INT CHECK (retention_days IS NULL OR retention_days > 0);
ALTER TABLE evidence ADD COLUMN IF NOT EXISTS public_reference VARCHAR(128);

CREATE INDEX IF NOT EXISTS idx_evidence_camera_time ON evidence(camera_id, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_type_time ON evidence(evidence_type, captured_at DESC);

-- -----------------------------------------------------------------------------
-- Idempotent AI result ingestion
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_ingest_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inference_event_id VARCHAR(128) NOT NULL UNIQUE,
    camera_id UUID REFERENCES cameras(id) ON DELETE SET NULL,
    payload_hash VARCHAR(64),
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    result_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_ingest_camera_time ON ai_ingest_events(camera_id, created_at DESC);

COMMENT ON TABLE ai_ingest_events IS 'Idempotency ledger for AI worker retries keyed by inference_event_id.';

-- -----------------------------------------------------------------------------
-- Grants for application user
-- -----------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON vehicle_observations TO phantom_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_ingest_events TO phantom_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO phantom_app;
