-- ==============================================================================
-- PHANTOM TEST 02: Verify GIS Queries and Spatial Analysis (PostGIS)
-- ==============================================================================

-- 1. Find all cameras within 5 km of Income Tax Circle (Ahmedabad: Lat 23.0402, Lon 72.5714)
-- Uses ST_DWithin on GEOGRAPHY for accurate geodesic spherical distance in meters
SELECT 
    'GIS_RADIUS_5KM' as test_name,
    c.camera_code,
    c.name as camera_name,
    l.name as location_name,
    l.district,
    ROUND((ST_Distance(l.geom, ST_SetSRID(ST_MakePoint(72.5714, 23.0402), 4326)::geography) / 1000.0)::numeric, 2) as distance_km
FROM cameras c
JOIN locations l ON c.location_id = l.id
WHERE ST_DWithin(l.geom, ST_SetSRID(ST_MakePoint(72.5714, 23.0402), 4326)::geography, 5000)
ORDER BY distance_km ASC;

-- 2. Find cameras in Ahmedabad district sorted by proximity to Sabarmati Riverfront
SELECT 
    'GIS_DISTRICT_PROXIMITY' as test_name,
    c.camera_code,
    l.city,
    l.name as location,
    ROUND((ST_Distance(l.geom, ST_SetSRID(ST_MakePoint(72.5855, 23.0610), 4326)::geography) / 1000.0)::numeric, 2) as distance_from_riverfront_km
FROM cameras c
JOIN locations l ON c.location_id = l.id
WHERE l.district = 'Ahmedabad'
ORDER BY distance_from_riverfront_km ASC
LIMIT 10;

-- 3. Camera Count and Geo-Distribution aggregated across Gujarat Districts
SELECT 
    'GIS_DISTRICT_AGGREGATE' as test_name,
    l.district,
    COUNT(c.id) as total_cameras,
    COUNT(DISTINCT l.id) as total_locations
FROM locations l
LEFT JOIN cameras c ON l.id = c.location_id
GROUP BY l.district
ORDER BY total_cameras DESC;
