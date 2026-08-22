-- ==============================================================================
-- PHANTOM MIGRATION 001: Extensions & Base Helper Functions
-- ==============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable PostGIS Spatial Database Extension
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Enable B-tree indexing support for GiST (useful for compound spatial + scalar queries)
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Base automatic updated_at timestamp trigger function
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
