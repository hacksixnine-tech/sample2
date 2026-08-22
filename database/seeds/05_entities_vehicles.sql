-- ==============================================================================
-- PHANTOM SEED 05: Entities & Vehicles (Gujarat Registrations)
-- ==============================================================================

-- Entity 1: Primary Suspect Vehicle for Cross-Camera Trajectory Testing
INSERT INTO entities (id, entity_type, primary_identifier, first_seen_at, last_seen_at, total_sightings, metadata) VALUES
('60000000-0000-0000-0000-000000000001', 'VEHICLE', 'GJ01AB1234', CURRENT_TIMESTAMP - INTERVAL '4 hours', CURRENT_TIMESTAMP - INTERVAL '30 minutes', 5, '{"is_flagged": true, "alert_priority": "CRITICAL"}'::jsonb),
('60000000-0000-0000-0000-000000000002', 'VEHICLE', 'GJ05CD5678', CURRENT_TIMESTAMP - INTERVAL '6 hours', CURRENT_TIMESTAMP - INTERVAL '1 hour', 3, '{"is_flagged": true, "alert_priority": "HIGH"}'::jsonb),
('60000000-0000-0000-0000-000000000003', 'VEHICLE', 'GJ27EF9012', CURRENT_TIMESTAMP - INTERVAL '2 days', CURRENT_TIMESTAMP - INTERVAL '5 hours', 2, '{"is_flagged": false}'::jsonb),
('60000000-0000-0000-0000-000000000004', 'VEHICLE', 'GJ06GH3456', CURRENT_TIMESTAMP - INTERVAL '1 day', CURRENT_TIMESTAMP - INTERVAL '2 hours', 4, '{"is_flagged": false}'::jsonb),
('60000000-0000-0000-0000-000000000005', 'PERSON', 'AARAV_KUMAR_SHARMA', CURRENT_TIMESTAMP - INTERVAL '12 hours', CURRENT_TIMESTAMP - INTERVAL '2 hours', 1, '{"facial_reid_enrolled": true}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- Vehicle Attributes
INSERT INTO vehicles (id, normalized_plate, raw_plate, plate_state_code, vehicle_type, make, model, color, chassis_number, engine_number, owner_name, rto_registered_at) VALUES
('60000000-0000-0000-0000-000000000001', 'GJ01AB1234', 'GJ 01 AB 1234', 'GJ', 'SUV', 'Toyota', 'Fortuner', 'White', 'MBJ11FTE40998124', '1GD998124', 'Kailash Verma (Reported Stolen)', CURRENT_TIMESTAMP - INTERVAL '2 years'),
('60000000-0000-0000-0000-000000000002', 'GJ05CD5678', 'GJ 05 CD 5678', 'GJ', 'CAR', 'Hyundai', 'Creta', 'Silver', 'MALC811FL0089123', 'G4FL0089123', 'Ramesh Chand (Wanted in Smuggling Case)', CURRENT_TIMESTAMP - INTERVAL '3 years'),
('60000000-0000-0000-0000-000000000003', 'GJ27EF9012', 'GJ 27 EF 9012', 'GJ', 'CAR', 'Maruti Suzuki', 'Swift Dzire', 'White', 'MA3EWB1S80012345', 'K12M80012345', 'Dinesh Solanki', CURRENT_TIMESTAMP - INTERVAL '1 year'),
('60000000-0000-0000-0000-000000000004', 'GJ06GH3456', 'GJ 06 GH 3456', 'GJ', 'TRUCK', 'Tata Motors', 'Signa 4825.TK', 'Blue', 'MAT804008K004567', 'ISB674567', 'Gujarat Logistics Fleet Ltd', CURRENT_TIMESTAMP - INTERVAL '4 years')
ON CONFLICT (id) DO NOTHING;
