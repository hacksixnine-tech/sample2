-- ==============================================================================
-- PHANTOM MIGRATION 002: Departments Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);
CREATE INDEX IF NOT EXISTS idx_departments_is_active ON departments(is_active);

DROP TRIGGER IF EXISTS set_timestamp_departments ON departments;
CREATE TRIGGER set_timestamp_departments
    BEFORE UPDATE ON departments
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_timestamp();
