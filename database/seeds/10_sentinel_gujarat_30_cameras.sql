-- ==========================================================================
-- 10_sentinel_gujarat_30_cameras.sql
-- Real-Time 30 Surveillance Cameras Seed from live.sentinelgujarat.in
-- ==========================================================================

INSERT INTO locations (id, name, district, state, latitude, longitude, geom, created_at, updated_at)
VALUES
('a0000000-0000-0000-0000-000000000001', 'Chiman Bhai Bridge Corridor', 'Ahmedabad', 'Gujarat', 23.0583, 72.5833, ST_SetSRID(ST_MakePoint(72.5833, 23.0583), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000002', 'Janpath Road Junction', 'Ahmedabad', 'Gujarat', 23.0612, 72.5801, ST_SetSRID(ST_MakePoint(72.5801, 23.0612), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000003', 'ONGC Office Marg', 'Ahmedabad', 'Gujarat', 23.1028, 72.5856, ST_SetSRID(ST_MakePoint(72.5856, 23.1028), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000004', 'Paldi Crossroad', 'Ahmedabad', 'Gujarat', 23.0135, 72.5624, ST_SetSRID(ST_MakePoint(72.5624, 23.0135), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000005', 'Visat Teen Rasta Circle', 'Ahmedabad', 'Gujarat', 23.0945, 72.5882, ST_SetSRID(ST_MakePoint(72.5882, 23.0945), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000006', 'Timbavadi Gate Chowk', 'Junagadh', 'Gujarat', 21.5167, 70.45, ST_SetSRID(ST_MakePoint(70.45, 21.5167), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000007', 'National Highway 51 Veraval', 'Gir Somnath', 'Gujarat', 20.9, 70.3667, ST_SetSRID(ST_MakePoint(70.3667, 20.9), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000008', 'Majewadi Gate Entry', 'Junagadh', 'Gujarat', 21.528, 70.463, ST_SetSRID(ST_MakePoint(70.463, 21.528), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000009', 'Junagadh Bypass Ring Road', 'Junagadh', 'Gujarat', 21.505, 70.478, ST_SetSRID(ST_MakePoint(70.478, 21.505), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000010', 'Char Chowk Road Axis', 'Junagadh', 'Gujarat', 21.521, 70.459, ST_SetSRID(ST_MakePoint(70.459, 21.521), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000011', 'Dolatpara Industrial Corridor', 'Junagadh', 'Gujarat', 21.542, 70.471, ST_SetSRID(ST_MakePoint(70.471, 21.542), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000012', 'Adalaj Tollnaka Expressway', 'Gandhinagar', 'Gujarat', 23.1667, 72.5833, ST_SetSRID(ST_MakePoint(72.5833, 23.1667), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000013', 'Ambawadi Main Road', 'Ahmedabad', 'Gujarat', 23.021, 72.548, ST_SetSRID(ST_MakePoint(72.548, 23.021), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000014', 'University Road Junction', 'Ahmedabad', 'Gujarat', 23.035, 72.56, ST_SetSRID(ST_MakePoint(72.56, 23.035), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000015', 'Suvidha Park Crossroad', 'Ahmedabad', 'Gujarat', 23.018, 72.535, ST_SetSRID(ST_MakePoint(72.535, 23.018), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000016', 'Visat Perimeter Sector 2', 'Ahmedabad', 'Gujarat', 23.097, 72.589, ST_SetSRID(ST_MakePoint(72.589, 23.097), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000017', 'Central Bus Port Terminal', 'Rajkot', 'Gujarat', 22.3039, 70.8022, ST_SetSRID(ST_MakePoint(70.8022, 22.3039), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000018', 'Trikon Baug Junction', 'Rajkot', 'Gujarat', 22.298, 70.795, ST_SetSRID(ST_MakePoint(70.795, 22.298), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000019', 'Khaparia Panchayat Marg', 'Navsari', 'Gujarat', 20.8167, 72.9833, ST_SetSRID(ST_MakePoint(72.9833, 20.8167), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000020', 'Mohanpura Relief Road', 'Ahmedabad', 'Gujarat', 23.031, 72.592, ST_SetSRID(ST_MakePoint(72.592, 23.031), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000021', 'Dethali Char Rasta', 'Patan', 'Gujarat', 23.85, 72.12, ST_SetSRID(ST_MakePoint(72.12, 23.85), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000022', 'Mervada Tran Rasta NH-27', 'Banaskantha', 'Gujarat', 24.17, 72.43, ST_SetSRID(ST_MakePoint(72.43, 24.17), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000023', 'Kheram Circle NH-48', 'Kheda', 'Gujarat', 22.75, 72.68, ST_SetSRID(ST_MakePoint(72.68, 22.75), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000024', 'Dehgam Central Crossroad', 'Gandhinagar', 'Gujarat', 23.167, 72.817, ST_SetSRID(ST_MakePoint(72.817, 23.167), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000025', 'Dhanori State Highway', 'Navsari', 'Gujarat', 20.85, 73.01, ST_SetSRID(ST_MakePoint(73.01, 20.85), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000026', 'Tankal Chikhli Road', 'Navsari', 'Gujarat', 20.78, 73.05, ST_SetSRID(ST_MakePoint(73.05, 20.78), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000027', 'Bilimora Railway Station Road', 'Navsari', 'Gujarat', 20.76, 72.96, ST_SetSRID(ST_MakePoint(72.96, 20.76), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000028', 'Bilimora Town Market Circle', 'Navsari', 'Gujarat', 20.765, 72.968, ST_SetSRID(ST_MakePoint(72.968, 20.765), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000029', 'Bilimora Coastal Highway', 'Navsari', 'Gujarat', 20.77, 72.975, ST_SetSRID(ST_MakePoint(72.975, 20.77), 4326), NOW(), NOW()),
('a0000000-0000-0000-0000-000000000030', 'Rambaugh Road Sector 2', 'Kutch', 'Gujarat', 23.0753, 70.1337, ST_SetSRID(ST_MakePoint(70.1337, 23.0753), 4326), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO cameras (id, camera_code, name, department_code, location_id, latitude, longitude, geom, status, rtsp_url, is_active, created_at, updated_at)
VALUES
('c0000000-0000-0000-0000-000000000001', 'CAM_SEN_001', 'Camera 1 - Chiman Bhai Bridge', 'POLICE', 'a0000000-0000-0000-0000-000000000001', 23.0583, 72.5833, ST_SetSRID(ST_MakePoint(72.5833, 23.0583), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/1', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000002', 'CAM_SEN_002', 'Camera 2 - Janpath', 'POLICE', 'a0000000-0000-0000-0000-000000000002', 23.0612, 72.5801, ST_SetSRID(ST_MakePoint(72.5801, 23.0612), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/2', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000003', 'CAM_SEN_003', 'Camera 3 - ONGC Office', 'POLICE', 'a0000000-0000-0000-0000-000000000003', 23.1028, 72.5856, ST_SetSRID(ST_MakePoint(72.5856, 23.1028), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/3', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000004', 'CAM_SEN_004', 'Camera 4 - Paldi Circle', 'POLICE', 'a0000000-0000-0000-0000-000000000004', 23.0135, 72.5624, ST_SetSRID(ST_MakePoint(72.5624, 23.0135), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/4', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000005', 'CAM_SEN_005', 'Camera 5 - Visat Teen Rasta', 'POLICE', 'a0000000-0000-0000-0000-000000000005', 23.0945, 72.5882, ST_SetSRID(ST_MakePoint(72.5882, 23.0945), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/5', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000006', 'CAM_SEN_006', 'Camera 6 - Timbavadi Gate', 'POLICE', 'a0000000-0000-0000-0000-000000000006', 21.5167, 70.45, ST_SetSRID(ST_MakePoint(70.45, 21.5167), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/6', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000007', 'CAM_SEN_007', 'Camera 7 - Hero Showroom Veraval', 'POLICE', 'a0000000-0000-0000-0000-000000000007', 20.9, 70.3667, ST_SetSRID(ST_MakePoint(70.3667, 20.9), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/7', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000008', 'CAM_SEN_008', 'Camera 8 - Majewadi Gate', 'POLICE', 'a0000000-0000-0000-0000-000000000008', 21.528, 70.463, ST_SetSRID(ST_MakePoint(70.463, 21.528), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/8', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000009', 'CAM_SEN_009', 'Camera 9 - New Bypass Circle', 'POLICE', 'a0000000-0000-0000-0000-000000000009', 21.505, 70.478, ST_SetSRID(ST_MakePoint(70.478, 21.505), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/9', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000010', 'CAM_SEN_010', 'Camera 10 - Char Chowk Road', 'POLICE', 'a0000000-0000-0000-0000-000000000010', 21.521, 70.459, ST_SetSRID(ST_MakePoint(70.459, 21.521), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/10', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000011', 'CAM_SEN_011', 'Camera 11 - Dolatpara', 'POLICE', 'a0000000-0000-0000-0000-000000000011', 21.542, 70.471, ST_SetSRID(ST_MakePoint(70.471, 21.542), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/11', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000012', 'CAM_SEN_012', 'Camera 12 - Tri Mandir Adalaj', 'POLICE', 'a0000000-0000-0000-0000-000000000012', 23.1667, 72.5833, ST_SetSRID(ST_MakePoint(72.5833, 23.1667), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/12', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000013', 'CAM_SEN_013', 'Camera 13 - CN Vidhyalaya', 'POLICE', 'a0000000-0000-0000-0000-000000000013', 23.021, 72.548, ST_SetSRID(ST_MakePoint(72.548, 23.021), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/13', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000014', 'CAM_SEN_014', 'Camera 14 - Delight', 'POLICE', 'a0000000-0000-0000-0000-000000000014', 23.035, 72.56, ST_SetSRID(ST_MakePoint(72.56, 23.035), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/14', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000015', 'CAM_SEN_015', 'Camera 15 - Suvidha Park', 'POLICE', 'a0000000-0000-0000-0000-000000000015', 23.018, 72.535, ST_SetSRID(ST_MakePoint(72.535, 23.018), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/15', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000016', 'CAM_SEN_016', 'Camera 16 - Visat P2', 'POLICE', 'a0000000-0000-0000-0000-000000000016', 23.097, 72.589, ST_SetSRID(ST_MakePoint(72.589, 23.097), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/16', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000017', 'CAM_SEN_017', 'Camera 17 - Rajkot Bus Port', 'POLICE', 'a0000000-0000-0000-0000-000000000017', 22.3039, 70.8022, ST_SetSRID(ST_MakePoint(70.8022, 22.3039), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/17', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000018', 'CAM_SEN_018', 'Camera 18 - Rajkot CCTV', 'POLICE', 'a0000000-0000-0000-0000-000000000018', 22.298, 70.795, ST_SetSRID(ST_MakePoint(70.795, 22.298), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/18', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000019', 'CAM_SEN_019', 'Camera 19 - Khaparia Gram Panchayat', 'POLICE', 'a0000000-0000-0000-0000-000000000019', 20.8167, 72.9833, ST_SetSRID(ST_MakePoint(72.9833, 20.8167), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/19', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000020', 'CAM_SEN_020', 'Camera 20 - Mohanpura', 'POLICE', 'a0000000-0000-0000-0000-000000000020', 23.031, 72.592, ST_SetSRID(ST_MakePoint(72.592, 23.031), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/20', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000021', 'CAM_SEN_021', 'Camera 21 - Patan Dethali', 'POLICE', 'a0000000-0000-0000-0000-000000000021', 23.85, 72.12, ST_SetSRID(ST_MakePoint(72.12, 23.85), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/21', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000022', 'CAM_SEN_022', 'Camera 22 - BK Mervada', 'POLICE', 'a0000000-0000-0000-0000-000000000022', 24.17, 72.43, ST_SetSRID(ST_MakePoint(72.43, 24.17), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/22', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000023', 'CAM_SEN_023', 'Camera 23 - Kheram', 'POLICE', 'a0000000-0000-0000-0000-000000000023', 22.75, 72.68, ST_SetSRID(ST_MakePoint(72.68, 22.75), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/23', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000024', 'CAM_SEN_024', 'Camera 24 - Dehgam', 'POLICE', 'a0000000-0000-0000-0000-000000000024', 23.167, 72.817, ST_SetSRID(ST_MakePoint(72.817, 23.167), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/24', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000025', 'CAM_SEN_025', 'Camera 25 - Dhanori', 'POLICE', 'a0000000-0000-0000-0000-000000000025', 20.85, 73.01, ST_SetSRID(ST_MakePoint(73.01, 20.85), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/25', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000026', 'CAM_SEN_026', 'Camera 26 - Tankal', 'POLICE', 'a0000000-0000-0000-0000-000000000026', 20.78, 73.05, ST_SetSRID(ST_MakePoint(73.05, 20.78), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/26', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000027', 'CAM_SEN_027', 'Camera 27 - Bilimora Station', 'POLICE', 'a0000000-0000-0000-0000-000000000027', 20.76, 72.96, ST_SetSRID(ST_MakePoint(72.96, 20.76), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/27', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000028', 'CAM_SEN_028', 'Camera 28 - Bilimora Market', 'POLICE', 'a0000000-0000-0000-0000-000000000028', 20.765, 72.968, ST_SetSRID(ST_MakePoint(72.968, 20.765), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/28', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000029', 'CAM_SEN_029', 'Camera 29 - Bilimora Coastal', 'POLICE', 'a0000000-0000-0000-0000-000000000029', 20.77, 72.975, ST_SetSRID(ST_MakePoint(72.975, 20.77), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/29', true, NOW(), NOW()),
('c0000000-0000-0000-0000-000000000030', 'CAM_SEN_030', 'Camera 30 - Gandhidham Rambaugh', 'POLICE', 'a0000000-0000-0000-0000-000000000030', 23.0753, 70.1337, ST_SetSRID(ST_MakePoint(70.1337, 23.0753), 4326), 'ONLINE', 'rtsp://live.corp8.cloud:8554/stream/30', true, NOW(), NOW())
ON CONFLICT (camera_code) DO NOTHING;
