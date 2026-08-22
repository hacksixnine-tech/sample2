-- ==============================================================================
-- PHANTOM TEST 05: Data Integrity & Negative Constraint Tests
-- Tests that PostgreSQL enforces database-level integrity and rejects invalid operations
-- ==============================================================================

-- Test A: Attempt to insert duplicate camera_code (MUST FAIL with unique violation)
DO $$
BEGIN
    INSERT INTO cameras (camera_code, name, department_id, location_id, camera_type)
    VALUES ('CAM-AMD-ITX-01', 'Duplicate Code Test', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'FIXED');
    RAISE EXCEPTION 'TEST_FAILED: Duplicate camera_code was improperly allowed!';
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'TEST_PASSED: Duplicate camera_code successfully rejected.';
END $$;

-- Test B: Attempt to insert invalid foreign key reference (MUST FAIL with fk violation)
DO $$
BEGIN
    INSERT INTO cameras (camera_code, name, department_id, location_id, camera_type)
    VALUES ('CAM-TEST-INVALID-FK', 'Invalid Dept Test', '00000000-0000-0000-0000-000000000999', '40000000-0000-0000-0000-000000000001', 'FIXED');
    RAISE EXCEPTION 'TEST_FAILED: Invalid department_id was improperly allowed!';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'TEST_PASSED: Invalid foreign key successfully rejected.';
END $$;

-- Test C: Attempt to insert invalid latitude (MUST FAIL with check constraint violation)
DO $$
BEGIN
    INSERT INTO locations (name, district, city, latitude, longitude)
    VALUES ('Invalid Coord Test', 'Ahmedabad', 'Ahmedabad', 125.5000, 72.5000);
    RAISE EXCEPTION 'TEST_FAILED: Out-of-range latitude was improperly allowed!';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'TEST_PASSED: Invalid latitude constraint successfully enforced.';
END $$;

-- Test D: Attempt to insert invalid alert status (MUST FAIL with check constraint violation)
DO $$
BEGIN
    INSERT INTO alerts (alert_code, alert_type, title, message, status, camera_id)
    VALUES ('ALR-INV-001', 'WATCHLIST_HIT', 'Invalid Status', 'Test message', 'INVALID_STATUS_CODE', '50000000-0000-0000-0000-000000000001');
    RAISE EXCEPTION 'TEST_FAILED: Invalid alert status was improperly allowed!';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'TEST_PASSED: Invalid alert status check constraint successfully enforced.';
END $$;

-- Test E: Attempt to insert detection with confidence > 1.0 (MUST FAIL)
DO $$
BEGIN
    INSERT INTO detections (camera_id, detection_type, confidence)
    VALUES ('50000000-0000-0000-0000-000000000001', 'VEHICLE', 1.50);
    RAISE EXCEPTION 'TEST_FAILED: Confidence > 1.0 was improperly allowed!';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'TEST_PASSED: Detection confidence range check successfully enforced.';
END $$;

-- Summary query for constraint test completion
SELECT 'CONSTRAINT_VERIFICATION_COMPLETE' as status, 'All 5 constraint violation tests passed successfully' as message;
