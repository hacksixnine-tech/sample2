-- ==============================================================================
-- PHANTOM MIGRATION 019: Application User Grants & Roles
-- ==============================================================================

DO $$
BEGIN
    -- Create application user if it does not already exist
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'phantom_app') THEN
        CREATE USER phantom_app WITH PASSWORD 'phantom_app_secure_password_2026';
    END IF;
END
$$;

-- Grant standard DML rights to application user
GRANT CONNECT ON DATABASE phantom TO phantom_app;
GRANT USAGE ON SCHEMA public TO phantom_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO phantom_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO phantom_app;

-- Ensure future tables and sequences automatically grant privileges to phantom_app
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO phantom_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO phantom_app;
