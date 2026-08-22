-- ==============================================================================
-- PHANTOM TEST 03: Cross-Camera Vehicle Chronological Tracking & Trajectory
-- ==============================================================================

-- Reconstruct complete chronological sightings and route for vehicle GJ01AB1234
SELECT 
    'VEHICLE_TRAJECTORY' as test_name,
    ROW_NUMBER() OVER (ORDER BY d.detected_at ASC) as step_seq,
    d.detected_at,
    v.normalized_plate,
    v.make || ' ' || v.model || ' (' || v.color || ')' as vehicle_description,
    c.camera_code,
    c.name as camera_name,
    l.name as location_name,
    l.city,
    l.district,
    l.latitude,
    l.longitude,
    d.confidence,
    d.speed_estimate_kmph,
    d.direction_heading,
    d.frame_reference
FROM detections d
JOIN entities e ON d.entity_id = e.id
JOIN vehicles v ON e.id = v.id
JOIN cameras c ON d.camera_id = c.id
JOIN locations l ON c.location_id = l.id
WHERE v.normalized_plate = 'GJ01AB1234'
ORDER BY d.detected_at ASC;

-- Calculate trajectory step distance between successive camera sightings
WITH chronological_path AS (
    SELECT 
        d.detected_at,
        c.camera_code,
        l.name as location_name,
        l.geom,
        LAG(l.geom) OVER (ORDER BY d.detected_at ASC) as prev_geom,
        LAG(d.detected_at) OVER (ORDER BY d.detected_at ASC) as prev_time
    FROM detections d
    JOIN vehicles v ON d.entity_id = v.id
    JOIN cameras c ON d.camera_id = c.id
    JOIN locations l ON c.location_id = l.id
    WHERE v.normalized_plate = 'GJ01AB1234'
)
SELECT 
    'TRAJECTORY_DISTANCE_SEGMENTS' as test_name,
    camera_code,
    location_name,
    detected_at,
    ROUND((ST_Distance(geom, prev_geom) / 1000.0)::numeric, 2) as hop_distance_km,
    ROUND(EXTRACT(EPOCH FROM (detected_at - prev_time)) / 60.0, 1) as hop_duration_mins
FROM chronological_path;
