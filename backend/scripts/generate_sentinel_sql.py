import json

with open("var/sentinel_mapped.json", "r", encoding="utf-8") as f:
    cameras = json.load(f)

sql_lines = [
    "-- ==========================================================================",
    "-- 10_sentinel_gujarat_30_cameras.sql",
    "-- Real-Time 30 Surveillance Cameras Seed from live.sentinelgujarat.in",
    "-- ==========================================================================\n",
    "INSERT INTO locations (id, name, district, state, latitude, longitude, geom, created_at, updated_at)",
    "VALUES"
]

loc_rows = []
for cam in cameras:
    cam_id_num = cam["camera_id"].replace("CAM_SEN_", "")
    loc_id = f"a0000000-0000-0000-0000-{int(cam_id_num):012d}"
    name = cam["road_name"].replace("'", "''")
    dist = cam["district"].replace("'", "''")
    lat = cam["latitude"]
    lon = cam["longitude"]
    loc_rows.append(f"('{loc_id}', '{name}', '{dist}', 'Gujarat', {lat}, {lon}, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326), NOW(), NOW())")

sql_lines.append(",\n".join(loc_rows) + "\nON CONFLICT (id) DO NOTHING;\n")

sql_lines.append("INSERT INTO cameras (id, camera_code, name, department_code, location_id, latitude, longitude, geom, status, rtsp_url, is_active, created_at, updated_at)")
sql_lines.append("VALUES")

cam_rows = []
for cam in cameras:
    cam_id_num = cam["camera_id"].replace("CAM_SEN_", "")
    c_id = f"c0000000-0000-0000-0000-{int(cam_id_num):012d}"
    loc_id = f"a0000000-0000-0000-0000-{int(cam_id_num):012d}"
    c_code = cam["camera_id"]
    name = cam["name"].replace("'", "''")
    lat = cam["latitude"]
    lon = cam["longitude"]
    rtsp = cam["rtsp_url"]
    cam_rows.append(f"('{c_id}', '{c_code}', '{name}', 'POLICE', '{loc_id}', {lat}, {lon}, ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326), 'ONLINE', '{rtsp}', true, NOW(), NOW())")

sql_lines.append(",\n".join(cam_rows) + "\nON CONFLICT (camera_code) DO NOTHING;\n")

sql_content = "\n".join(sql_lines)

with open("../database/seeds/10_sentinel_gujarat_30_cameras.sql", "w", encoding="utf-8") as f:
    f.write(sql_content)

print("Generated database/seeds/10_sentinel_gujarat_30_cameras.sql successfully!")
