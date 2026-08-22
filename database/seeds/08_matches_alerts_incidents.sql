-- ==============================================================================
-- PHANTOM SEED 08: Matches, Alerts, Incidents & Evidence
-- Connects AI Detections to Watchlist Matches, Automated Alerts, and Case Dossiers
-- ==============================================================================

-- 1. Watchlist Match
INSERT INTO matches (
    id, detection_id, watchlist_entry_id, match_score, matching_method,
    status, matched_at, verified_by_user_id, verified_at, verification_notes
) VALUES (
    '90000000-0000-0000-0000-000000000001',
    '80000000-0000-0000-0000-000000000005', -- GIFT City detection
    '71000000-0000-0000-0000-000000000001', -- Stolen Fortuner Hotlist entry
    0.9980,
    'EXACT_PLATE',
    'CONFIRMED',
    CURRENT_TIMESTAMP - INTERVAL '15 minutes',
    '30000000-0000-0000-0000-000000000002', -- DSP Ahmedabad
    CURRENT_TIMESTAMP - INTERVAL '10 minutes',
    'Plate alphanumeric string GJ01AB1234 and vehicle make/model (Toyota Fortuner White) confirmed by officer'
) ON CONFLICT (id) DO NOTHING;

-- 2. Triggered Alert
INSERT INTO alerts (
    id, alert_code, alert_type, severity, title, message, status,
    source_event_id, source_match_id, camera_id, entity_id,
    acknowledged_by_user_id, acknowledged_at, metadata
) VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'ALR-2026-0821-001',
    'WATCHLIST_HIT',
    'CRITICAL',
    'HOTLIST HIT: Stolen Toyota Fortuner at GIFT City Main Gate',
    'Vehicle GJ01AB1234 flagged under FIR-AMD-CRIME-2026-8812 was detected by CAM-GND-GFT-01 traveling East at 34 km/h.',
    'INVESTIGATING',
    '81000000-0000-0000-0000-000000000005',
    '90000000-0000-0000-0000-000000000001',
    '50000000-0000-0000-0000-000000000009',
    '60000000-0000-0000-0000-000000000001',
    '30000000-0000-0000-0000-000000000002',
    CURRENT_TIMESTAMP - INTERVAL '10 minutes',
    '{"intercept_team_dispatched": true, "pcr_van_callsign": "CH-0-EAGLE-1"}'::jsonb
) ON CONFLICT (alert_code) DO NOTHING;

-- 3. Investigation Incident
INSERT INTO incidents (
    id, incident_code, title, description, severity, status,
    assigned_department_id, assigned_user_id, occurred_at, metadata
) VALUES (
    'b0000000-0000-0000-0000-000000000001',
    'INC-2026-0821-9901',
    'Interception of Stolen Luxury Vehicle Entering GIFT City Security Perimeter',
    'Automated cross-camera tracking identified vehicle GJ01AB1234 traversing from Ahmedabad Income Tax Circle across SG Highway to GIFT City. Intercept team mobilized.',
    'CRITICAL',
    'IN_PROGRESS',
    '10000000-0000-0000-0000-000000000001', -- Gujarat Police
    '30000000-0000-0000-0000-000000000002', -- DSP Ahmedabad
    CURRENT_TIMESTAMP - INTERVAL '180 minutes',
    '{"fir_number": "FIR-AMD-CRIME-2026-8812", "dispatch_channel": "VHF_CH_04"}'::jsonb
) ON CONFLICT (incident_code) DO NOTHING;

-- 4. Evidence Records
INSERT INTO evidence (
    id, evidence_code, evidence_type, storage_provider, bucket_name, object_key,
    file_format, file_size_bytes, file_hash_sha256, captured_at, camera_id, detection_id, event_id, chain_of_custody_notes
) VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'EVD-20260821-001',
    'FRAME_SNAPSHOT',
    'MINIO',
    'phantom-evidence',
    '2026/08/21/c1009/frame_28004.jpg',
    'jpg',
    245890,
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    CURRENT_TIMESTAMP - INTERVAL '15 minutes',
    '50000000-0000-0000-0000-000000000009',
    '80000000-0000-0000-0000-000000000005',
    '81000000-0000-0000-0000-000000000005',
    'Digital evidence ingested from CAM-GND-GFT-01 and hashed on ingestion server'
),
(
    'c0000000-0000-0000-0000-000000000002',
    'EVD-20260821-002',
    'CROPPED_IMAGE',
    'MINIO',
    'phantom-evidence',
    '2026/08/21/c1009/crop_plate_28004.jpg',
    'jpg',
    45120,
    '5f4dcc3b5aa765d61d8327deb882cf992b96ee974e30eb0ad4c783457a414704',
    CURRENT_TIMESTAMP - INTERVAL '15 minutes',
    '50000000-0000-0000-0000-000000000009',
    '80000000-0000-0000-0000-000000000005',
    '81000000-0000-0000-0000-000000000005',
    'High resolution ANPR license plate crop'
) ON CONFLICT (evidence_code) DO NOTHING;

-- 5. Link Incident Relationships
INSERT INTO incident_alerts (incident_id, alert_id, notes) VALUES
('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'Primary trigger alert for the case');

INSERT INTO incident_events (incident_id, event_id, notes) VALUES
('b0000000-0000-0000-0000-000000000001', '81000000-0000-0000-0000-000000000001', 'Initial sighting at Income Tax Circle'),
('b0000000-0000-0000-0000-000000000001', '81000000-0000-0000-0000-000000000002', 'Intermediate sighting at Iskcon Cross Roads'),
('b0000000-0000-0000-0000-000000000001', '81000000-0000-0000-0000-000000000003', 'Intermediate sighting at Vaishnodevi Circle'),
('b0000000-0000-0000-0000-000000000001', '81000000-0000-0000-0000-000000000004', 'Intermediate sighting at Koba Circle'),
('b0000000-0000-0000-0000-000000000001', '81000000-0000-0000-0000-000000000005', 'Final interception point at GIFT City');

INSERT INTO incident_entities (incident_id, entity_id, involvement_role, notes) VALUES
('b0000000-0000-0000-0000-000000000001', '60000000-0000-0000-0000-000000000001', 'VEHICLE_OF_INTEREST', 'Stolen vehicle subject to active hotlist interception');

INSERT INTO incident_evidence (incident_id, evidence_id, notes) VALUES
('b0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'CCTV full frame capture at GIFT City gate'),
('b0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000002', 'High-res cropped plate image');
