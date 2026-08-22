-- ==============================================================================
-- PHANTOM MIGRATION 009: AI Detections & Observations Model
-- ==============================================================================

CREATE TABLE IF NOT EXISTS detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE RESTRICT,
    entity_id UUID REFERENCES entities(id) ON DELETE SET NULL,
    detection_type VARCHAR(50) NOT NULL CHECK (
        detection_type IN ('VEHICLE', 'LICENSE_PLATE', 'FACE', 'PERSON', 'OBJECT', 'WEAPON', 'CROWD', 'OTHER')
    ),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confidence NUMERIC(5, 4) NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    bounding_box JSONB NOT NULL DEFAULT '{}'::jsonb, -- {"x_min": 0.1, "y_min": 0.2, "x_max": 0.3, "y_max": 0.4}
    detected_plate_number VARCHAR(50),
    normalized_plate_number VARCHAR(50),
    frame_reference VARCHAR(500),
    crop_image_url VARCHAR(500),
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    speed_estimate_kmph NUMERIC(5, 2) CHECK (speed_estimate_kmph >= 0),
    direction_heading VARCHAR(50),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- High-performance query indexes for high volume searches
CREATE INDEX IF NOT EXISTS idx_detections_camera_time ON detections(camera_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_detections_entity_time ON detections(entity_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_detections_type_time ON detections(detection_type, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_detections_normalized_plate ON detections(normalized_plate_number, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON detections(detected_at DESC);
