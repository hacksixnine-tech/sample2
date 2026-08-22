-- ==============================================================================
-- PHANTOM SEED 06: Watchlists and Watchlist Entries (Demo Data)
-- ==============================================================================

-- Watchlist Categories
INSERT INTO watchlists (id, name, code, category, department_id, description, priority, is_active, created_by_user_id) VALUES
('70000000-0000-0000-0000-000000000001', 'Statewide Stolen Vehicle Hotlist', 'WL-STOLEN-VEHICLES', 'STOLEN_VEHICLES', '10000000-0000-0000-0000-000000000001', 'Active FIR reported stolen four-wheelers and two-wheelers in Gujarat', 'CRITICAL', TRUE, '30000000-0000-0000-0000-000000000002'),
('70000000-0000-0000-0000-000000000002', 'High-Risk Wanted Vehicles (CID / Crime Branch)', 'WL-WANTED-VEHICLES', 'WANTED_VEHICLES', '10000000-0000-0000-0000-000000000001', 'Vehicles involved in organized crime, narcotics transit or bank robberies', 'CRITICAL', TRUE, '30000000-0000-0000-0000-000000000002'),
('70000000-0000-0000-0000-000000000003', 'RTO Tax Evader & Blacklisted Commercial Fleet', 'WL-RTO-BLACKLISTED', 'BLACKLISTED_VEHICLES', '10000000-0000-0000-0000-000000000003', 'Overloaded, fitness expired, or habitual traffic offenders flagged for seizure', 'HIGH', TRUE, '30000000-0000-0000-0000-000000000003'),
('70000000-0000-0000-0000-000000000004', 'Statewide Missing Persons & Children Watchlist', 'WL-MISSING-PERSONS', 'MISSING_PERSONS', '10000000-0000-0000-0000-000000000001', 'Persons reported missing under TrackChild / Gujarat Police initiative', 'HIGH', TRUE, '30000000-0000-0000-0000-000000000002')
ON CONFLICT (code) DO NOTHING;

-- Watchlist Entries
INSERT INTO watchlist_entries (id, watchlist_id, identifier, normalized_identifier, entity_type, case_reference_number, fir_station, reason, priority, valid_from, is_active) VALUES
-- Entry matching Entity 1 (GJ01AB1234 - Fortuner)
('71000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001', 'GJ 01 AB 1234', 'GJ01AB1234', 'VEHICLE', 'FIR-AMD-CRIME-2026-8812', 'Navrangpura Police Station, Ahmedabad', 'Stolen White Toyota Fortuner outside CG Road jewellery showroom', 'CRITICAL', CURRENT_TIMESTAMP - INTERVAL '7 days', TRUE),

-- Entry matching Entity 2 (GJ05CD5678 - Creta)
('71000000-0000-0000-0000-000000000002', '70000000-0000-0000-0000-000000000002', 'GJ 05 CD 5678', 'GJ05CD5678', 'VEHICLE', 'FIR-SUR-CRIME-2026-4401', 'Khatodara Police Station, Surat', 'Suspect vehicle used in commercial tax evasion and contraband transport', 'CRITICAL', CURRENT_TIMESTAMP - INTERVAL '14 days', TRUE),

-- Additional Watchlist Entry
('71000000-0000-0000-0000-000000000003', '70000000-0000-0000-0000-000000000003', 'GJ 27 XY 9999', 'GJ27XY9999', 'VEHICLE', 'RTO-E-CHALLAN-9021', 'RTO Gandhinagar Checkpost', 'Over 15 unpaid dangerous driving e-challans and suspended fitness certificate', 'MEDIUM', CURRENT_TIMESTAMP - INTERVAL '30 days', TRUE)
ON CONFLICT (id) DO NOTHING;
