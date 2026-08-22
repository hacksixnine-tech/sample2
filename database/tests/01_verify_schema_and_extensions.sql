-- ==============================================================================
-- PHANTOM TEST 01: Verify Database Schema, Extensions & Indexes
-- ==============================================================================

-- 1. Verify PostGIS Extension and Version
SELECT 'TEST_EXTENSIONS' as test_group, extname, extversion 
FROM pg_extension 
WHERE extname IN ('postgis', 'uuid-ossp', 'pgcrypto', 'btree_gist');

-- 2. Verify Table Existence (Should list all 18 core domain tables)
SELECT 'TEST_TABLES' as test_group, table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 3. Verify Spatial Column PostGIS Type and SRID
SELECT 'TEST_GIS_COLUMN' as test_group, f_table_name, f_geography_column, srid, type 
FROM geography_columns 
WHERE f_table_name = 'locations';

-- 4. Verify Spatial and Core B-Tree Indexes
SELECT 'TEST_INDEXES' as test_group, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND (indexname LIKE 'idx_%' OR indexname LIKE '%_pkey')
ORDER BY tablename, indexname;
