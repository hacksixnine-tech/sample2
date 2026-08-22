-- ==============================================================================
-- PHANTOM SEED 07: Chronological Detections & Real-time Events
-- Demonstrates multi-camera tracking trajectory for vehicle GJ01AB1234
-- ==============================================================================

-- 1. Sighting 1: Income Tax Circle, Ahmedabad (T - 180 mins)
INSERT INTO detections (
    id, camera_id, entity_id, detection_type, detected_at, confidence,
    bounding_box, detected_plate_number, normalized_plate_number,
    frame_reference, crop_image_url, model_name, model_version, speed_estimate_kmph, direction_heading, metadata
) VALUES (
    '80000000-0000-0000-0000-000000000001',
    '50000000-0000-0000-0000-000000000001', -- Income Tax Circle ANPR
    '60000000-0000-0000-0000-000000000001', -- GJ01AB1234
    'LICENSE_PLATE',
    CURRENT_TIMESTAMP - INTERVAL '180 minutes',
    0.9850,
    '{"x_min": 0.35, "y_min": 0.42, "x_max": 0.62, "y_max": 0.78}'::jsonb,
    'GJ 01 AB 1234',
    'GJ01AB1234',
    's3://phantom-evidence/2026/08/21/c1001/frame_10401.jpg',
    's3://phantom-evidence/2026/08/21/c1001/crop_plate_10401.jpg',
    'YOLOv10-ANPR-Gujarat',
    'v2.4.1',
    48.50,
    'NORTH_WEST',
    '{"lane": 2, "ambient_light": "DAYLIGHT"}'::jsonb
);

INSERT INTO events (id, event_type, camera_id, entity_id, detection_id, occurred_at, severity, description) VALUES (
    '81000000-0000-0000-0000-000000000001',
    'PLATE_DETECTED',
    '50000000-0000-0000-0000-000000000001',
    '60000000-0000-0000-0000-000000000001',
    '80000000-0000-0000-0000-000000000001',
    CURRENT_TIMESTAMP - INTERVAL '180 minutes',
    'INFO',
    'Vehicle GJ01AB1234 detected moving north-west across Income Tax Circle Junction'
);

-- 2. Sighting 2: Iskcon Cross Roads, Ahmedabad (T - 135 mins)
INSERT INTO detections (
    id, camera_id, entity_id, detection_type, detected_at, confidence,
    bounding_box, detected_plate_number, normalized_plate_number,
    frame_reference, crop_image_url, model_name, model_version, speed_estimate_kmph, direction_heading, metadata
) VALUES (
    '80000000-0000-0000-0000-000000000002',
    '50000000-0000-0000-0000-000000000003', -- Iskcon Cross Roads ANPR
    '60000000-0000-0000-0000-000000000001', -- GJ01AB1234
    'LICENSE_PLATE',
    CURRENT_TIMESTAMP - INTERVAL '135 minutes',
    0.9780,
    '{"x_min": 0.40, "y_min": 0.45, "x_max": 0.68, "y_max": 0.81}'::jsonb,
    'GJ 01 AB 1234',
    'GJ01AB1234',
    's3://phantom-evidence/2026/08/21/c1003/frame_14209.jpg',
    's3://phantom-evidence/2026/08/21/c1003/crop_plate_14209.jpg',
    'YOLOv10-ANPR-Gujarat',
    'v2.4.1',
    62.10,
    'NORTH',
    '{"lane": 3, "ambient_light": "DAYLIGHT"}'::jsonb
);

INSERT INTO events (id, event_type, camera_id, entity_id, detection_id, occurred_at, severity, description) VALUES (
    '81000000-0000-0000-0000-000000000002',
    'PLATE_DETECTED',
    '50000000-0000-0000-0000-000000000003',
    '60000000-0000-0000-0000-000000000001',
    '80000000-0000-0000-0000-000000000002',
    CURRENT_TIMESTAMP - INTERVAL '135 minutes',
    'INFO',
    'Vehicle GJ01AB1234 sighted passing Iskcon Junction heading towards SG Highway North'
);

-- 3. Sighting 3: Vaishnodevi Circle, Ahmedabad Ring Road (T - 90 mins)
INSERT INTO detections (
    id, camera_id, entity_id, detection_type, detected_at, confidence,
    bounding_box, detected_plate_number, normalized_plate_number,
    frame_reference, crop_image_url, model_name, model_version, speed_estimate_kmph, direction_heading, metadata
) VALUES (
    '80000000-0000-0000-0000-000000000003',
    '50000000-0000-0000-0000-000000000007', -- Vaishnodevi Circle ANPR
    '60000000-0000-0000-0000-000000000001', -- GJ01AB1234
    'LICENSE_PLATE',
    CURRENT_TIMESTAMP - INTERVAL '90 minutes',
    0.9910,
    '{"x_min": 0.28, "y_min": 0.38, "x_max": 0.58, "y_max": 0.72}'::jsonb,
    'GJ 01 AB 1234',
    'GJ01AB1234',
    's3://phantom-evidence/2026/08/21/c1007/frame_18991.jpg',
    's3://phantom-evidence/2026/08/21/c1007/crop_plate_18991.jpg',
    'YOLOv10-ANPR-Gujarat',
    'v2.4.1',
    71.00,
    'NORTH_EAST',
    '{"lane": 1, "ambient_light": "DAYLIGHT"}'::jsonb
);

INSERT INTO events (id, event_type, camera_id, entity_id, detection_id, occurred_at, severity, description) VALUES (
    '81000000-0000-0000-0000-000000000003',
    'PLATE_DETECTED',
    '50000000-0000-0000-0000-000000000007',
    '60000000-0000-0000-0000-000000000001',
    '80000000-0000-0000-0000-000000000003',
    CURRENT_TIMESTAMP - INTERVAL '90 minutes',
    'INFO',
    'Vehicle GJ01AB1234 traversed SP Ring Road at Vaishnodevi Circle heading towards Gandhinagar'
);

-- 4. Sighting 4: Koba Circle, Gandhinagar Highway (T - 45 mins)
INSERT INTO detections (
    id, camera_id, entity_id, detection_type, detected_at, confidence,
    bounding_box, detected_plate_number, normalized_plate_number,
    frame_reference, crop_image_url, model_name, model_version, speed_estimate_kmph, direction_heading, metadata
) VALUES (
    '80000000-0000-0000-0000-000000000004',
    '50000000-0000-0000-0000-000000000011', -- Koba Circle ANPR
    '60000000-0000-0000-0000-000000000001', -- GJ01AB1234
    'LICENSE_PLATE',
    CURRENT_TIMESTAMP - INTERVAL '45 minutes',
    0.9940,
    '{"x_min": 0.32, "y_min": 0.40, "x_max": 0.60, "y_max": 0.75}'::jsonb,
    'GJ 01 AB 1234',
    'GJ01AB1234',
    's3://phantom-evidence/2026/08/21/c1011/frame_23412.jpg',
    's3://phantom-evidence/2026/08/21/c1011/crop_plate_23412.jpg',
    'YOLOv10-ANPR-Gujarat',
    'v2.4.1',
    78.40,
    'NORTH_EAST',
    '{"lane": 2, "ambient_light": "DAYLIGHT"}'::jsonb
);

INSERT INTO events (id, event_type, camera_id, entity_id, detection_id, occurred_at, severity, description) VALUES (
    '81000000-0000-0000-0000-000000000004',
    'PLATE_DETECTED',
    '50000000-0000-0000-0000-000000000011',
    '60000000-0000-0000-0000-000000000001',
    '80000000-0000-0000-0000-000000000004',
    CURRENT_TIMESTAMP - INTERVAL '45 minutes',
    'INFO',
    'Vehicle GJ01AB1234 detected entering Gandhinagar jurisdiction via Koba Circle Highway'
);

-- 5. Sighting 5: GIFT City Main Boulevard (T - 15 mins)
INSERT INTO detections (
    id, camera_id, entity_id, detection_type, detected_at, confidence,
    bounding_box, detected_plate_number, normalized_plate_number,
    frame_reference, crop_image_url, model_name, model_version, speed_estimate_kmph, direction_heading, metadata
) VALUES (
    '80000000-0000-0000-0000-000000000005',
    '50000000-0000-0000-0000-000000000009', -- GIFT City Main Gate ANPR
    '60000000-0000-0000-0000-000000000001', -- GJ01AB1234
    'LICENSE_PLATE',
    CURRENT_TIMESTAMP - INTERVAL '15 minutes',
    0.9960,
    '{"x_min": 0.38, "y_min": 0.44, "x_max": 0.65, "y_max": 0.80}'::jsonb,
    'GJ 01 AB 1234',
    'GJ01AB1234',
    's3://phantom-evidence/2026/08/21/c1009/frame_28004.jpg',
    's3://phantom-evidence/2026/08/21/c1009/crop_plate_28004.jpg',
    'YOLOv10-ANPR-Gujarat',
    'v2.4.1',
    34.20,
    'EAST',
    '{"lane": 1, "ambient_light": "DAYLIGHT"}'::jsonb
);

INSERT INTO events (id, event_type, camera_id, entity_id, detection_id, occurred_at, severity, description) VALUES (
    '81000000-0000-0000-0000-000000000005',
    'WATCHLIST_MATCH',
    '50000000-0000-0000-0000-000000000009',
    '60000000-0000-0000-0000-000000000001',
    '80000000-0000-0000-0000-000000000005',
    CURRENT_TIMESTAMP - INTERVAL '15 minutes',
    'CRITICAL',
    'CRITICAL ALERT: Stolen Hotlist Vehicle GJ01AB1234 detected entering GIFT City Main Boulevard'
);
