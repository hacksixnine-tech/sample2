-- ==============================================================================
-- PHANTOM MIGRATION 017: Incident Relationship Junction Tables
-- ==============================================================================

-- Incident <-> Alerts
CREATE TABLE IF NOT EXISTS incident_alerts (
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    PRIMARY KEY (incident_id, alert_id)
);

CREATE INDEX IF NOT EXISTS idx_incident_alerts_alert_id ON incident_alerts(alert_id);

-- Incident <-> Events
CREATE TABLE IF NOT EXISTS incident_events (
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    PRIMARY KEY (incident_id, event_id)
);

CREATE INDEX IF NOT EXISTS idx_incident_events_event_id ON incident_events(event_id);

-- Incident <-> Entities
CREATE TABLE IF NOT EXISTS incident_entities (
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    involvement_role VARCHAR(50) NOT NULL DEFAULT 'SUSPECT' CHECK (
        involvement_role IN ('SUSPECT', 'VICTIM', 'WITNESS', 'VEHICLE_OF_INTEREST', 'ASSOCIATE', 'OTHER')
    ),
    added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    PRIMARY KEY (incident_id, entity_id, involvement_role)
);

CREATE INDEX IF NOT EXISTS idx_incident_entities_entity_id ON incident_entities(entity_id);

-- Incident <-> Evidence
CREATE TABLE IF NOT EXISTS incident_evidence (
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    evidence_id UUID NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    PRIMARY KEY (incident_id, evidence_id)
);

CREATE INDEX IF NOT EXISTS idx_incident_evidence_evidence_id ON incident_evidence(evidence_id);
