-- ==============================================================================
-- PHANTOM SEED 04: 30+ Cameras, Stream Configurations & Health Status (Demo Data)
-- ==============================================================================

-- 30 Distributed Cameras across Gujarat
INSERT INTO cameras (id, camera_code, name, department_id, location_id, camera_type, manufacturer, model, serial_number, ip_address, status, connectivity_status, storage_type, retention_days, field_of_view_deg, azimuth_angle_deg, metadata) VALUES
-- Ahmedabad Cameras
('50000000-0000-0000-0000-000000000001', 'CAM-AMD-ITX-01', 'Income Tax Circle ANPR Northbound', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'ANPR', 'Hikvision', 'iDS-2CD7A46G0/P-IZHS', 'DS7A46-2024-001', '10.101.10.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 60, 45.0, 0.0, '{"lane_count": 3, "pole_id": "AMD-POLE-101"}'::jsonb),
('50000000-0000-0000-0000-000000000002', 'CAM-AMD-ITX-02', 'Income Tax Circle 360 PTZ Junction', '10000000-0000-0000-0000-000000000004', '40000000-0000-0000-0000-000000000001', 'PTZ', 'Axis', 'Q6135-LE PTZ Network Camera', 'AXIS-Q6135-901', '10.101.10.2', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 30, 90.0, 180.0, '{"optical_zoom": "31x", "pole_id": "AMD-POLE-101"}'::jsonb),
('50000000-0000-0000-0000-000000000003', 'CAM-AMD-ISK-01', 'Iskcon Junction ANPR Flyover Approach', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000002', 'ANPR', 'Dahua', 'DHI-ITC431-RW1F-IRL8', 'DAHUA-431-882', '10.101.11.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 60, 40.0, 45.0, '{"lane_count": 4, "pole_id": "AMD-POLE-204"}'::jsonb),
('50000000-0000-0000-0000-000000000004', 'CAM-AMD-KLP-01', 'Kalupur Station Entry Fixed Surveillance', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000003', 'FIXED', 'Bosch', 'DINION IP 3000i IR', 'BOSCH-3000-112', '10.101.12.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 45, 85.0, 90.0, '{"crowd_analytics": true}'::jsonb),
('50000000-0000-0000-0000-000000000005', 'CAM-AMD-RIV-01', 'Sabarmati Riverfront Promenade Fixed 01', '10000000-0000-0000-0000-000000000004', '40000000-0000-0000-0000-000000000004', 'FIXED', 'Hikvision', 'DS-2CD2087G2-LU', 'DS2CD-RIV-009', '10.101.13.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 30, 95.0, 270.0, '{"night_color": true}'::jsonb),
('50000000-0000-0000-0000-000000000006', 'CAM-AMD-NRL-01', 'Narol Toll Plaza ANPR Entry Lane 1', '10000000-0000-0000-0000-000000000003', '40000000-0000-0000-0000-000000000005', 'ANPR', 'Hikvision', 'iDS-2CD7A46G0/P-IZHS', 'DS7A46-NRL-101', '10.101.14.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 90, 35.0, 180.0, '{"toll_lane": "1A", "rto_fastag_sync": true}'::jsonb),
('50000000-0000-0000-0000-000000000007', 'CAM-AMD-VSH-01', 'Vaishnodevi Circle ANPR North Ring', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000006', 'ANPR', 'Dahua', 'DHI-ITC431-RW1F-IRL8', 'DAHUA-VSH-774', '10.101.15.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 60, 45.0, 0.0, '{"ring_road_sector": "North"}'::jsonb),

-- Gandhinagar / Capital Corridor Cameras
('50000000-0000-0000-0000-000000000008', 'CAM-GND-CH0-01', 'CH-0 Secretariat Main Gate Security PTZ', '10000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000007', 'PTZ', 'Axis', 'Q6135-LE PTZ Network Camera', 'AXIS-GND-CH0', '10.102.10.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 90, 120.0, 90.0, '{"high_security": true}'::jsonb),
('50000000-0000-0000-0000-000000000009', 'CAM-GND-GFT-01', 'GIFT City Main Gate ANPR Boulevard', '10000000-0000-0000-0000-000000000012', '40000000-0000-0000-0000-000000000008', 'ANPR', 'Hikvision', 'iDS-2CD7A46G0/P-IZHS', 'DS7A46-GFT-01', '10.102.11.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 60, 45.0, 135.0, '{"smart_city_feed": true}'::jsonb),
('50000000-0000-0000-0000-000000000010', 'CAM-GND-GH5-01', 'GH-5 Sector 16 Fixed Junction Camera', '10000000-0000-0000-0000-000000000012', '40000000-0000-0000-0000-000000000009', 'FIXED', 'Bosch', 'FLEXIDOME IP 4000i', 'BOSCH-GH5-44', '10.102.12.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 30, 80.0, 180.0, '{"corridor": "GH Road"}'::jsonb),
('50000000-0000-0000-0000-000000000011', 'CAM-GND-KOB-01', 'Koba Circle Highway ANPR Corridor', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000010', 'ANPR', 'Hikvision', 'iDS-2CD7A46G0/P-IZHS', 'DS7A46-KOB-88', '10.102.13.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 60, 45.0, 225.0, '{"capital_highway_speed_limit": 80}'::jsonb),

-- Surat Cameras
('50000000-0000-0000-0000-000000000012', 'CAM-SUR-SDB-01', 'Surat Diamond Bourse Main Gate PTZ', '10000000-0000-0000-0000-000000000005', '40000000-0000-0000-0000-000000000011', 'PTZ', 'Axis', 'Q6135-LE PTZ Network Camera', 'AXIS-SUR-SDB', '10.103.10.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 90, 110.0, 0.0, '{"high_value_commercial_zone": true}'::jsonb),
('50000000-0000-0000-0000-000000000013', 'CAM-SUR-ATW-01', 'Athwa Gate Junction ANPR Westbound', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000012', 'ANPR', 'Dahua', 'DHI-ITC431-RW1F-IRL8', 'DAHUA-ATW-909', '10.103.11.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 60, 40.0, 270.0, '{"iccc_connected": true}'::jsonb),
('50000000-0000-0000-0000-000000000014', 'CAM-SUR-STN-01', 'Surat Railway Station Ring Road Fixed', '10000000-0000-0000-0000-000000000005', '40000000-0000-0000-0000-000000000013', 'FIXED', 'Hikvision', 'DS-2CD2087G2-LU', 'DS2CD-SUR-STN', '10.103.12.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 45, 90.0, 90.0, '{"traffic_management": true}'::jsonb),
('50000000-0000-0000-0000-000000000015', 'CAM-SUR-HZR-01', 'Hazira Port Logistics Gate ANPR', '10000000-0000-0000-0000-000000000010', '40000000-0000-0000-0000-000000000014', 'ANPR', 'Bosch', 'DINION IP 5000i', 'BOSCH-HZR-55', '10.103.13.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 90, 45.0, 180.0, '{"heavy_vehicle_corridor": true}'::jsonb),

-- Vadodara Cameras
('50000000-0000-0000-0000-000000000016', 'CAM-BDQ-KLG-01', 'Sayajigunj Kala Ghoda Circle PTZ', '10000000-0000-0000-0000-000000000006', '40000000-0000-0000-0000-000000000015', 'PTZ', 'Axis', 'Q6135-LE PTZ Network Camera', 'AXIS-BDQ-KLG', '10.104.10.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 45, 100.0, 45.0, '{"heritage_circle": true}'::jsonb),
('50000000-0000-0000-0000-000000000017', 'CAM-BDQ-ALK-01', 'Alkapuri RC Dutt Road Fixed Surveillance', '10000000-0000-0000-0000-000000000006', '40000000-0000-0000-0000-000000000016', 'FIXED', 'Hikvision', 'DS-2CD2087G2-LU', 'DS2CD-BDQ-ALK', '10.104.11.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 30, 85.0, 135.0, '{"commercial_hub": true}'::jsonb),
('50000000-0000-0000-0000-000000000018', 'CAM-BDQ-GLD-01', 'Golden Chokdi NH-48 ANPR Northbound', '10000000-0000-0000-0000-000000000003', '40000000-0000-0000-0000-000000000017', 'ANPR', 'Hikvision', 'iDS-2CD7A46G0/P-IZHS', 'DS7A46-GLD-01', '10.104.12.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 90, 40.0, 0.0, '{"nh48_national_highway": true}'::jsonb),

-- Rajkot Cameras
('50000000-0000-0000-0000-000000000019', 'CAM-RAJ-TRK-01', 'Trikon Baug City Center 360 PTZ', '10000000-0000-0000-0000-000000000007', '40000000-0000-0000-0000-000000000018', 'PTZ', 'Axis', 'Q6135-LE PTZ Network Camera', 'AXIS-RAJ-TRK', '10.105.10.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 45, 120.0, 180.0, '{"iccc_rmc_node": true}'::jsonb),
('50000000-0000-0000-0000-000000000020', 'CAM-RAJ-MDH-01', 'Madhapar Chokdi Ring Road ANPR', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000019', 'ANPR', 'Dahua', 'DHI-ITC431-RW1F-IRL8', 'DAHUA-RAJ-MDH', '10.105.11.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 60, 45.0, 270.0, '{"ring_road_checkpost": true}'::jsonb),
('50000000-0000-0000-0000-000000000021', 'CAM-RAJ-GRN-01', 'Greenland Chokdi NH-27 ANPR Toll', '10000000-0000-0000-0000-000000000003', '40000000-0000-0000-0000-000000000020', 'ANPR', 'Hikvision', 'iDS-2CD7A46G0/P-IZHS', 'DS7A46-RAJ-GRN', '10.105.12.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 90, 40.0, 90.0, '{"nh27_artery": true}'::jsonb),

-- Regional / Strategic Gateways
('50000000-0000-0000-0000-000000000022', 'CAM-BHV-GHG-01', 'Bhavnagar Ghogha Circle ANPR Checkpoint', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000021', 'ANPR', 'Hikvision', 'iDS-2CD7A46G0/P-IZHS', 'DS7A46-BHV-GHG', '10.106.10.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 60, 45.0, 180.0, '{"bhavnagar_police_zone": "South"}'::jsonb),
('50000000-0000-0000-0000-000000000023', 'CAM-JAM-DIG-01', 'Jamnagar Digjam Circle PTZ Camera', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000022', 'PTZ', 'Axis', 'Q6135-LE PTZ Network Camera', 'AXIS-JAM-DIG', '10.107.10.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 30, 90.0, 45.0, '{"airport_corridor": true}'::jsonb),
('50000000-0000-0000-0000-000000000024', 'CAM-JUN-MJV-01', 'Junagadh Majevadi Gate Surveillance Fixed', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000023', 'FIXED', 'Bosch', 'DINION IP 3000i IR', 'BOSCH-JUN-MJV', '10.108.10.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 30, 80.0, 0.0, '{"heritage_gate": true}'::jsonb),
('50000000-0000-0000-0000-000000000025', 'CAM-BHJ-JUB-01', 'Bhuj Jubilee Ground PTZ Command Camera', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000024', 'PTZ', 'Axis', 'Q6135-LE PTZ Network Camera', 'AXIS-BHJ-JUB', '10.109.10.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 45, 110.0, 90.0, '{"kutch_border_district": true}'::jsonb),
('50000000-0000-0000-0000-000000000026', 'CAM-MSH-RDH-01', 'Mehsana Radhanpur Cross Road ANPR', '10000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000025', 'ANPR', 'Hikvision', 'iDS-2CD7A46G0/P-IZHS', 'DS7A46-MSH-RDH', '10.110.10.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 60, 45.0, 315.0, '{"north_gujarat_gateway": true}'::jsonb),
('50000000-0000-0000-0000-000000000027', 'CAM-AND-EXP-01', 'Anand Express Highway Toll ANPR Inbound', '10000000-0000-0000-0000-000000000003', '40000000-0000-0000-0000-000000000026', 'ANPR', 'Hikvision', 'iDS-2CD7A46G0/P-IZHS', 'DS7A46-AND-EXP', '10.111.10.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 90, 35.0, 180.0, '{"expressway_toll": "NE-1"}'::jsonb),
('50000000-0000-0000-0000-000000000028', 'CAM-BRC-NRM-01', 'Bharuch Narmada Bridge Toll ANPR', '10000000-0000-0000-0000-000000000020', '40000000-0000-0000-0000-000000000027', 'ANPR', 'Dahua', 'DHI-ITC431-RW1F-IRL8', 'DAHUA-BRC-NRM', '10.112.10.1', 'ACTIVE', 'ONLINE', 'EDGE_AND_CENTRAL', 90, 40.0, 0.0, '{"narmada_corridor": true}'::jsonb),
('50000000-0000-0000-0000-000000000029', 'CAM-SMN-TMP-01', 'Somnath Temple Promenade Fixed Security', '10000000-0000-0000-0000-000000000015', '40000000-0000-0000-0000-000000000028', 'FIXED', 'Bosch', 'FLEXIDOME IP 4000i', 'BOSCH-SMN-01', '10.113.10.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 60, 90.0, 180.0, '{"pilgrimage_security": true}'::jsonb),
('50000000-0000-0000-0000-000000000030', 'CAM-SOU-KEV-01', 'Statue of Unity Welcome Gate 360 PTZ', '10000000-0000-0000-0000-000000000015', '40000000-0000-0000-0000-000000000029', 'PTZ', 'Axis', 'Q6135-LE PTZ Network Camera', 'AXIS-SOU-KEV', '10.114.10.1', 'ACTIVE', 'ONLINE', 'CENTRAL_ONLY', 90, 120.0, 90.0, '{"tourism_national_monument": true}'::jsonb)
ON CONFLICT (camera_code) DO NOTHING;

-- Camera Streams (Using Safe Placeholder URLs and Vault Secret References)
INSERT INTO camera_streams (camera_id, protocol, stream_url, secret_ref, resolution, fps, codec, bitrate_kbps, is_primary, is_active)
SELECT 
    id,
    'RTSP',
    'rtsp://stream-gateway.internal.phantom.local:8554/live/' || lower(camera_code),
    'vault://secrets/cctv/streams/' || lower(camera_code),
    '1080p',
    25.0,
    'H264',
    4096,
    TRUE,
    TRUE
FROM cameras;

-- Camera Health Records (Online status with realistic latency and metrics)
INSERT INTO camera_health (camera_id, status, latency_ms, packet_loss_pct, current_fps, bitrate_kbps, health_score, checked_at)
SELECT 
    id,
    'ONLINE',
    18 + (random() * 15)::int,
    0.00,
    25.0,
    4096,
    98.50,
    CURRENT_TIMESTAMP
FROM cameras;
