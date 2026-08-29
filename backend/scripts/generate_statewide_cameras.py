import json
import os
import sys

print("Generating Statewide Gujarat CCTV Network Dataset...")

statewide_cameras = [
    # --- AHMEDABAD DISTRICT ---
    {"camera_id": "CAM_AMD_001", "latitude": 23.0225, "longitude": 72.5714, "district": "Ahmedabad", "police_station": "Navrangpura PS", "road_name": "CG Road Center", "direction": "North", "status": "Active"},
    {"camera_id": "CAM_AMD_002", "latitude": 23.0525, "longitude": 72.5314, "district": "Ahmedabad", "police_station": "Bodakdev PS", "road_name": "SG Highway Junction", "direction": "East", "status": "Active"},
    {"camera_id": "CAM_AMD_003", "latitude": 23.0378, "longitude": 72.5122, "district": "Ahmedabad", "police_station": "Vastrapur PS", "road_name": "Pakwan Crossroad", "direction": "North", "status": "Active"},
    {"camera_id": "CAM_AMD_004", "latitude": 23.0298, "longitude": 72.5065, "district": "Ahmedabad", "police_station": "Satellite PS", "road_name": "Iskcon Bridge Flyover", "direction": "South", "status": "Active"},
    {"camera_id": "CAM_AMD_005", "latitude": 23.0150, "longitude": 72.5850, "district": "Ahmedabad", "police_station": "Kalupur PS", "road_name": "Railway Station Entry", "direction": "West", "status": "Active"},
    {"camera_id": "CAM_AMD_006", "latitude": 23.0400, "longitude": 72.5650, "district": "Ahmedabad", "police_station": "Sabarmati Riverfront PS", "road_name": "Riverfront Promenade", "direction": "East", "status": "Active"},
    {"camera_id": "CAM_AMD_007", "latitude": 22.9850, "longitude": 72.5850, "district": "Ahmedabad", "police_station": "Narol PS", "road_name": "Narol Toll Plaza", "direction": "South", "status": "Active"},
    {"camera_id": "CAM_AMD_008", "latitude": 23.1250, "longitude": 72.5400, "district": "Ahmedabad", "police_station": "Sola PS", "road_name": "Vaishnodevi Circle", "direction": "North", "status": "Active"},

    # --- GANDHINAGAR DISTRICT ---
    {"camera_id": "CAM_GND_001", "latitude": 23.2156, "longitude": 72.6369, "district": "Gandhinagar", "police_station": "Sector 7 PS", "road_name": "CH-0 Secretariat Gate", "direction": "North", "status": "Active"},
    {"camera_id": "CAM_GND_002", "latitude": 23.1890, "longitude": 72.6280, "district": "Gandhinagar", "police_station": "Infocity PS", "road_name": "Infocity IT Corridor", "direction": "East", "status": "Active"},
    {"camera_id": "CAM_GND_003", "latitude": 23.1750, "longitude": 72.6150, "district": "Gandhinagar", "police_station": "Koba PS", "road_name": "Koba Circle North Entry", "direction": "South", "status": "Active"},
    {"camera_id": "CAM_GND_004", "latitude": 23.2300, "longitude": 72.6500, "district": "Gandhinagar", "police_station": "Sector 21 PS", "road_name": "Akshardham Marg", "direction": "West", "status": "Active"},
    {"camera_id": "CAM_GND_005", "latitude": 23.2450, "longitude": 72.6620, "district": "Gandhinagar", "police_station": "Pethapur PS", "road_name": "Pethapur Crossroad", "direction": "North", "status": "Inactive"},

    # --- SURAT DISTRICT ---
    {"camera_id": "CAM_SRT_001", "latitude": 21.1702, "longitude": 72.8311, "district": "Surat", "police_station": "Khatodara PS", "road_name": "Surat Ring Road Toll", "direction": "East", "status": "Active"},
    {"camera_id": "CAM_SRT_002", "latitude": 21.2100, "longitude": 72.8600, "district": "Surat", "police_station": "Varachha PS", "road_name": "Diamond Bourse Junction", "direction": "North", "status": "Active"},
    {"camera_id": "CAM_SRT_003", "latitude": 21.1450, "longitude": 72.7850, "district": "Surat", "police_station": "Dumas PS", "road_name": "Dumas Airport Highway", "direction": "South", "status": "Active"},
    {"camera_id": "CAM_SRT_004", "latitude": 21.1950, "longitude": 72.8150, "district": "Surat", "police_station": "Athwa PS", "road_name": "Athwa Lines Chowk", "direction": "West", "status": "Active"},
    {"camera_id": "CAM_SRT_005", "latitude": 21.1550, "longitude": 72.8450, "district": "Surat", "police_station": "Udhna PS", "road_name": "Udhna Main Road", "direction": "North", "status": "Active"},

    # --- VADODARA DISTRICT ---
    {"camera_id": "CAM_VAD_001", "latitude": 22.3072, "longitude": 73.1812, "district": "Vadodara", "police_station": "Sayajiganj PS", "road_name": "Alkapuri Main Hub", "direction": "North", "status": "Active"},
    {"camera_id": "CAM_VAD_002", "latitude": 22.2980, "longitude": 73.2050, "district": "Vadodara", "police_station": "Raopura PS", "road_name": "Nyaymandir Heritage Node", "direction": "East", "status": "Active"},
    {"camera_id": "CAM_VAD_003", "latitude": 22.3250, "longitude": 73.1650, "district": "Vadodara", "police_station": "Gorwa PS", "road_name": "Industrial Area Access", "direction": "West", "status": "Active"},
    {"camera_id": "CAM_VAD_004", "latitude": 22.2850, "longitude": 73.2200, "district": "Vadodara", "police_station": "Makarpura PS", "road_name": "NH-48 National Highway", "direction": "South", "status": "Active"},

    # --- RAJKOT DISTRICT ---
    {"camera_id": "CAM_RJK_001", "latitude": 22.3039, "longitude": 70.8022, "district": "Rajkot", "police_station": "A-Division PS", "road_name": "Trikon Baug Central Chowk", "direction": "North", "status": "Active"},
    {"camera_id": "CAM_RJK_002", "latitude": 22.2850, "longitude": 70.7850, "district": "Rajkot", "police_station": "Malaviya Nagar PS", "road_name": "150 Feet Ring Road", "direction": "East", "status": "Active"},
    {"camera_id": "CAM_RJK_003", "latitude": 22.3300, "longitude": 70.8250, "district": "Rajkot", "police_station": "Kuuvadva PS", "road_name": "Ahmedabad Highway Checkpost", "direction": "North", "status": "Active"},

    # --- KUTCH / BHUJ DISTRICT ---
    {"camera_id": "CAM_KCH_001", "latitude": 23.2420, "longitude": 69.6669, "district": "Kutch", "police_station": "Bhuj City PS", "road_name": "Jubilee Ground Perimeter", "direction": "North", "status": "Active"},
    {"camera_id": "CAM_KCH_002", "latitude": 23.0150, "longitude": 70.1350, "district": "Kutch", "police_station": "Gandhidham PS", "road_name": "Port Access Corridor", "direction": "East", "status": "Active"},

    # --- BHAVNAGAR DISTRICT ---
    {"camera_id": "CAM_BHV_001", "latitude": 21.7645, "longitude": 72.1519, "district": "Bhavnagar", "police_station": "A-Division PS", "road_name": "Waghawadi Road ANPR", "direction": "South", "status": "Active"},
    {"camera_id": "CAM_BHV_002", "latitude": 21.7820, "longitude": 72.1380, "district": "Bhavnagar", "police_station": "Ghogha PS", "road_name": "Rupale Ring Road", "direction": "West", "status": "Active"},

    # --- JUNAGADH DISTRICT ---
    {"camera_id": "CAM_JND_001", "latitude": 21.5222, "longitude": 70.4579, "district": "Junagadh", "police_station": "Junagadh City PS", "road_name": "Majewadi Gate Security", "direction": "North", "status": "Active"},
    {"camera_id": "CAM_JND_002", "latitude": 21.5050, "longitude": 70.4850, "district": "Junagadh", "police_station": "Bhavnath PS", "road_name": "Girnar Foothills Entry", "direction": "East", "status": "Active"},

    # --- JAMNAGAR DISTRICT ---
    {"camera_id": "CAM_JAM_001", "latitude": 22.4707, "longitude": 70.0577, "district": "Jamnagar", "police_station": "City A Division", "road_name": "Lakhota Lake Perimeter", "direction": "North", "status": "Active"},
    {"camera_id": "CAM_JAM_002", "latitude": 22.4450, "longitude": 70.0820, "district": "Jamnagar", "police_station": "Panchkoshi PS", "road_name": "Reliance Refinery Highway", "direction": "South", "status": "Active"},
]

print(f"Generated {len(statewide_cameras)} high-priority CCTV nodes across Gujarat.")

# Update backend/static/index.html
html_path = "static/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace cameraData in HTML
start_marker = "const cameraData = ["
end_marker = "];\n\nlet mapObject = null;"

json_str = json.dumps(statewide_cameras, indent=4)
replacement = f"const cameraData = {json_str};\n\nlet mapObject = null;"

if start_marker in content and end_marker in content:
    idx_start = content.find(start_marker)
    idx_end = content.find(end_marker) + 2
    new_content = content[:idx_start] + replacement + content[idx_end + len(end_marker) - 2:]
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully updated static/index.html with Statewide Gujarat Camera Network!")
else:
    print("Could not find exact markers in static/index.html")
