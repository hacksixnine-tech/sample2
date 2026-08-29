import json

with open('var/sentinel_mapped.json', 'r', encoding='utf-8') as f:
    cams = json.load(f)

# Also add key strategic city nodes
extra = [
    {
        'camera_id': 'CAM_AMD_001', 'name': 'CG Road Center', 'latitude': 23.0225, 'longitude': 72.5714,
        'district': 'Ahmedabad', 'police_station': 'Navrangpura PS', 'road_name': 'CG Road Center',
        'direction': 'North', 'status': 'Active', 'hls_url': 'https://live.sentinelgujarat.in/live/stream/1/index.m3u8',
        'rtsp_url': 'rtsp://live.corp8.cloud:8554/stream/1'
    },
    {
        'camera_id': 'CAM_AMD_002', 'name': 'SG Highway Junction', 'latitude': 23.0525, 'longitude': 72.5314,
        'district': 'Ahmedabad', 'police_station': 'Bodakdev PS', 'road_name': 'SG Highway Junction',
        'direction': 'East', 'status': 'Active', 'hls_url': 'https://live.sentinelgujarat.in/live/stream/2/index.m3u8',
        'rtsp_url': 'rtsp://live.corp8.cloud:8554/stream/2'
    },
    {
        'camera_id': 'CAM_AMD_003', 'name': 'Pakwan Crossroad', 'latitude': 23.0378, 'longitude': 72.5122,
        'district': 'Ahmedabad', 'police_station': 'Vastrapur PS', 'road_name': 'Pakwan Crossroad',
        'direction': 'North', 'status': 'Active', 'hls_url': 'https://live.sentinelgujarat.in/live/stream/4/index.m3u8',
        'rtsp_url': 'rtsp://live.corp8.cloud:8554/stream/4'
    },
    {
        'camera_id': 'CAM_AMD_004', 'name': 'Iskcon Bridge Flyover', 'latitude': 23.0298, 'longitude': 72.5065,
        'district': 'Ahmedabad', 'police_station': 'Satellite PS', 'road_name': 'Iskcon Bridge Flyover',
        'direction': 'South', 'status': 'Active', 'hls_url': 'https://live.sentinelgujarat.in/live/stream/5/index.m3u8',
        'rtsp_url': 'rtsp://live.corp8.cloud:8554/stream/5'
    },
    {
        'camera_id': 'CAM_AMD_006', 'name': 'Riverfront Promenade', 'latitude': 23.0400, 'longitude': 72.5650,
        'district': 'Ahmedabad', 'police_station': 'Sabarmati Riverfront PS', 'road_name': 'Riverfront Promenade',
        'direction': 'East', 'status': 'Active', 'hls_url': 'https://live.sentinelgujarat.in/live/stream/13/index.m3u8',
        'rtsp_url': 'rtsp://live.corp8.cloud:8554/stream/13'
    }
]

all_cams = cams + extra
cams_json = json.dumps(all_cams, indent=2)

with open('var/all_cameras.json', 'w', encoding='utf-8') as f:
    f.write(cams_json)

print('Saved all_cameras.json with', len(all_cams), 'nodes')
