-- ==============================================================================
-- PHANTOM SEED 02: Official 33 Districts of Gujarat
-- ==============================================================================

INSERT INTO districts (district_code, name, state, zone, headquarters, centroid_lat, centroid_lng)
VALUES
    ('GJ-AHM', 'Ahmedabad', 'Gujarat', 'Central Gujarat', 'Ahmedabad', 23.0225, 72.5714),
    ('GJ-GNR', 'Gandhinagar', 'Gujarat', 'Central Gujarat', 'Gandhinagar', 23.2156, 72.6369),
    ('GJ-SUR', 'Surat', 'Gujarat', 'South Gujarat', 'Surat', 21.1702, 72.8311),
    ('GJ-VAD', 'Vadodara', 'Gujarat', 'Central Gujarat', 'Vadodara', 22.3072, 73.1812),
    ('GJ-RAJ', 'Rajkot', 'Gujarat', 'Saurashtra', 'Rajkot', 22.3039, 70.8022),
    ('GJ-BHV', 'Bhavnagar', 'Gujarat', 'Saurashtra', 'Bhavnagar', 21.7645, 72.1519),
    ('GJ-JAM', 'Jamnagar', 'Gujarat', 'Saurashtra', 'Jamnagar', 22.4707, 70.0577),
    ('GJ-JUN', 'Junagadh', 'Gujarat', 'Saurashtra', 'Junagadh', 21.5222, 70.4579),
    ('GJ-KUT', 'Kutch', 'Gujarat', 'Kutch', 'Bhuj', 23.2420, 69.6669),
    ('GJ-NAV', 'Navsari', 'Gujarat', 'South Gujarat', 'Navsari', 20.9467, 72.9520),
    ('GJ-PAT', 'Patan', 'Gujarat', 'North Gujarat', 'Patan', 23.8493, 72.1266),
    ('GJ-GIR', 'Gir Somnath', 'Gujarat', 'Saurashtra', 'Veraval', 20.9042, 70.3667),
    ('GJ-BAN', 'Banaskantha', 'Gujarat', 'North Gujarat', 'Palanpur', 24.1724, 72.4346),
    ('GJ-PAN', 'Panchmahal', 'Gujarat', 'Central Gujarat', 'Godhra', 22.7758, 73.6149),
    ('GJ-ANA', 'Anand', 'Gujarat', 'Central Gujarat', 'Anand', 22.5645, 72.9289),
    ('GJ-KHE', 'Kheda', 'Gujarat', 'Central Gujarat', 'Nadiad', 22.6916, 72.8634),
    ('GJ-MEH', 'Mehsana', 'Gujarat', 'North Gujarat', 'Mehsana', 23.5880, 72.3693),
    ('GJ-DAH', 'Dahod', 'Gujarat', 'Central Gujarat', 'Dahod', 22.8340, 74.2558),
    ('GJ-BHA', 'Bharuch', 'Gujarat', 'South Gujarat', 'Bharuch', 21.7051, 72.9959),
    ('GJ-VAL', 'Valsad', 'Gujarat', 'South Gujarat', 'Valsad', 20.5992, 72.9342),
    ('GJ-AMR', 'Amreli', 'Gujarat', 'Saurashtra', 'Amreli', 21.6032, 71.2221),
    ('GJ-POR', 'Porbandar', 'Gujarat', 'Saurashtra', 'Porbandar', 21.6417, 69.6293),
    ('GJ-SUR2', 'Surendranagar', 'Gujarat', 'Saurashtra', 'Surendranagar', 22.7278, 71.6378),
    ('GJ-MOR', 'Morbi', 'Gujarat', 'Saurashtra', 'Morbi', 22.8120, 70.8377),
    ('GJ-BOT', 'Botad', 'Gujarat', 'Saurashtra', 'Botad', 22.1704, 71.6664),
    ('GJ-ARA', 'Aravalli', 'Gujarat', 'North Gujarat', 'Modasa', 23.4636, 73.3034),
    ('GJ-MAH', 'Mahisagar', 'Gujarat', 'Central Gujarat', 'Lunawada', 23.1345, 73.6186),
    ('GJ-CHO', 'Chhotaudepur', 'Gujarat', 'Central Gujarat', 'Chhota Udepur', 22.3082, 74.0116),
    ('GJ-NAR', 'Narmada', 'Gujarat', 'South Gujarat', 'Rajpipla', 21.8700, 73.5000),
    ('GJ-TAP', 'Tapi', 'Gujarat', 'South Gujarat', 'Vyara', 21.1118, 73.3934),
    ('GJ-DAN', 'Dang', 'Gujarat', 'South Gujarat', 'Ahwa', 20.7583, 73.6844),
    ('GJ-DWA', 'Devbhumi Dwarka', 'Gujarat', 'Saurashtra', 'Khambhalia', 22.2089, 69.6547),
    ('GJ-SAB', 'Sabarkantha', 'Gujarat', 'North Gujarat', 'Himmatnagar', 23.5977, 72.9698)
ON CONFLICT (name) DO UPDATE SET
    district_code = EXCLUDED.district_code,
    centroid_lat = EXCLUDED.centroid_lat,
    centroid_lng = EXCLUDED.centroid_lng,
    zone = EXCLUDED.zone,
    headquarters = EXCLUDED.headquarters;
