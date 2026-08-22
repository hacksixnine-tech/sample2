-- ==============================================================================
-- PHANTOM MIGRATION 008: Entities & Vehicles Data Model
-- ==============================================================================

-- Supertype Entity Table (Vehicles, Persons, Objects, etc.)
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL CHECK (
        entity_type IN ('VEHICLE', 'PERSON', 'OBJECT', 'OTHER')
    ),
    primary_identifier VARCHAR(255) NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_sightings INT NOT NULL DEFAULT 1 CHECK (total_sightings >= 0),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_identifier ON entities(primary_identifier);
CREATE INDEX IF NOT EXISTS idx_entities_last_seen ON entities(last_seen_at DESC);

DROP TRIGGER IF EXISTS set_timestamp_entities ON entities;
CREATE TRIGGER set_timestamp_entities
    BEFORE UPDATE ON entities
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();

-- Specialized Vehicle Table (Inherits / References Entity ID)
CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
    normalized_plate VARCHAR(50) NOT NULL, -- Standardized uppercase alphanumeric (e.g. GJ01AB1234)
    raw_plate VARCHAR(50) NOT NULL,        -- As detected / entered (e.g. GJ 01 AB 1234)
    plate_state_code VARCHAR(10) DEFAULT 'GJ',
    vehicle_type VARCHAR(50) CHECK (
        vehicle_type IN ('TWO_WHEELER', 'THREE_WHEELER', 'CAR', 'SUV', 'BUS', 'TRUCK', 'LCV', 'AMBULANCE', 'POLICE_VAN', 'OTHER')
    ),
    make VARCHAR(100),
    model VARCHAR(100),
    color VARCHAR(50),
    chassis_number VARCHAR(100),
    engine_number VARCHAR(100),
    owner_name VARCHAR(255),
    rto_registered_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vehicles_normalized_plate ON vehicles(normalized_plate);
CREATE INDEX IF NOT EXISTS idx_vehicles_raw_plate ON vehicles(raw_plate);
CREATE INDEX IF NOT EXISTS idx_vehicles_vehicle_type ON vehicles(vehicle_type);
CREATE INDEX IF NOT EXISTS idx_vehicles_make_model ON vehicles(make, model);
CREATE INDEX IF NOT EXISTS idx_vehicles_color ON vehicles(color);

DROP TRIGGER IF EXISTS set_timestamp_vehicles ON vehicles;
CREATE TRIGGER set_timestamp_vehicles
    BEFORE UPDATE ON vehicles
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
