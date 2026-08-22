-- ==============================================================================
-- PHANTOM TEST 04: Watchlist Matching, Alert Engine & Incident Dossier
-- ==============================================================================

-- 1. Verify Watchlist Match with Detection & Camera Information
SELECT 
    'WATCHLIST_MATCH_DETAIL' as test_name,
    m.id as match_id,
    m.matching_method,
    m.match_score,
    m.status as match_status,
    we.identifier as watchlist_plate,
    w.name as watchlist_name,
    w.category as watchlist_category,
    we.case_reference_number,
    c.camera_code,
    c.name as camera_name,
    d.detected_at,
    u.full_name as verified_by_officer
FROM matches m
JOIN watchlist_entries we ON m.watchlist_entry_id = we.id
JOIN watchlists w ON we.watchlist_id = w.id
JOIN detections d ON m.detection_id = d.id
JOIN cameras c ON d.camera_id = c.id
LEFT JOIN users u ON m.verified_by_user_id = u.id;

-- 2. Verify Generated Alert, Escalation Status, and Acknowledging Officer
SELECT 
    'ALERT_LIFECYCLE' as test_name,
    a.alert_code,
    a.alert_type,
    a.severity,
    a.status as alert_status,
    a.title,
    c.camera_code,
    u.full_name as acknowledged_by,
    a.acknowledged_at
FROM alerts a
JOIN cameras c ON a.camera_id = c.id
LEFT JOIN users u ON a.acknowledged_by_user_id = u.id;

-- 3. Verify Complete Incident Case Dossier (Incident + Events + Evidence + Alerts)
SELECT 
    'INCIDENT_DOSSIER' as test_name,
    i.incident_code,
    i.title as incident_title,
    i.status as incident_status,
    dept.name as assigned_dept,
    u.full_name as assigned_officer,
    COUNT(DISTINCT ie.event_id) as linked_events_count,
    COUNT(DISTINCT ia.alert_id) as linked_alerts_count,
    COUNT(DISTINCT iev.evidence_id) as linked_evidence_count
FROM incidents i
JOIN departments dept ON i.assigned_department_id = dept.id
LEFT JOIN users u ON i.assigned_user_id = u.id
LEFT JOIN incident_events ie ON i.id = ie.incident_id
LEFT JOIN incident_alerts ia ON i.id = ia.incident_id
LEFT JOIN incident_evidence iev ON i.id = iev.incident_id
GROUP BY i.incident_code, i.title, i.status, dept.name, u.full_name;
