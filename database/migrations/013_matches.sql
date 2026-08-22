-- ==============================================================================
-- PHANTOM MIGRATION 013: Watchlist Matching Engine Model
-- ==============================================================================

CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_id UUID NOT NULL REFERENCES detections(id) ON DELETE RESTRICT,
    watchlist_entry_id UUID NOT NULL REFERENCES watchlist_entries(id) ON DELETE RESTRICT,
    match_score NUMERIC(5, 4) NOT NULL CHECK (match_score >= 0.0 AND match_score <= 1.0),
    matching_method VARCHAR(50) NOT NULL DEFAULT 'EXACT_PLATE' CHECK (
        matching_method IN ('EXACT_PLATE', 'FUZZY_PLATE', 'FACIAL_RECOGNITION', 'REID', 'MANUAL')
    ),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'CONFIRMED', 'FALSE_POSITIVE', 'AUTO_CONFIRMED')
    ),
    matched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_at TIMESTAMPTZ,
    verification_notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_matches_detection_id ON matches(detection_id);
CREATE INDEX IF NOT EXISTS idx_matches_watchlist_entry ON matches(watchlist_entry_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_matched_at ON matches(matched_at DESC);
CREATE INDEX IF NOT EXISTS idx_matches_score ON matches(match_score DESC);
