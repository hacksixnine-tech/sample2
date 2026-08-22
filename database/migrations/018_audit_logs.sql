-- ==============================================================================
-- PHANTOM MIGRATION 018: Audit Logging System
-- ==============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL CHECK (
        action IN (
            'LOGIN',
            'LOGOUT',
            'VIEW_ENTITY',
            'VIEW_EVIDENCE',
            'SEARCH_VEHICLE',
            'CREATE_ALERT',
            'ACKNOWLEDGE_ALERT',
            'RESOLVE_ALERT',
            'UPDATE_WATCHLIST',
            'CREATE_CAMERA',
            'UPDATE_CAMERA',
            'DELETE_CAMERA',
            'CREATE_INCIDENT',
            'UPDATE_INCIDENT',
            'EXPORT_DATA',
            'SECURITY_VIOLATION',
            'OTHER'
        )
    ),
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    details TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
