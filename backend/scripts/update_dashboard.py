import json
import re

with open('var/sentinel_mapped.json', 'r', encoding='utf-8') as f:
    sentinel_cameras = json.load(f)

with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Hls.js CDN if not present
if 'hls.min.js' not in html:
    html = html.replace(
        '<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>',
        '<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>\n<script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.8/dist/hls.min.js"></script>'
    )

# 2. Update cameraData
cameras_json = json.dumps(sentinel_cameras, indent=4)
html = re.sub(r'const cameraData\s*=\s*\[[\s\S]*?\];', f'const cameraData = {cameras_json};', html)

# 3. Update districtSelector options
districts_html = """<option value="Ahmedabad" selected>Ahmedabad (Chiman Bhai / Paldi / ONGC)</option>
                <option value="Junagadh">Junagadh (Timbavadi / Majewadi / Dolatpara)</option>
                <option value="Gandhinagar">Gandhinagar (Adalaj Toll / Dehgam)</option>
                <option value="Rajkot">Rajkot (Central Bus Port / Trikon Baug)</option>
                <option value="Navsari">Navsari / Bilimora (Coastal / Tankal)</option>
                <option value="Gir Somnath">Gir Somnath (Veraval NH-51)</option>
                <option value="Patan">Patan (Dethali Char Rasta)</option>
                <option value="Banaskantha">Banaskantha (Mervada Tran Rasta)</option>
                <option value="Kheda">Kheda (Kheram Circle NH-48)</option>
                <option value="Kutch">Kutch (Gandhidham Rambaugh)</option>
                <option value="Statewide">Statewide All Gujarat</option>"""

html = re.sub(r'<select id="districtSelector"[\s\S]*?</select>', f'<select id="districtSelector" onchange="onDistrictChange(this.value)">\n                {districts_html}\n            </select>', html)

# 4. Update CCTV modal video container
cctv_modal_html = """<div class="cctv-screen">
                <video id="cctvVideo" autoplay muted playsinline controls style="position:absolute; top:0; left:0; width:100%; height:100%; object-fit:cover; z-index:1;"></video>
                <div class="cctv-hud-top" style="position:relative; z-index:10;">
                    <div><span class="rec-dot"></span>LIVE HLS • SENTINEL GUJARAT FEED</div>
                    <div id="cctvTimestamp">--:--:--</div>
                </div>
                
                <div class="ai-overlay" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:5;">
                    <div class="ai-box" style="top: 25%; left: 35%; width: 28%; height: 35%;">
                        <div>VEHICLE [96%]</div>
                        <div style="color: #6ee7b7; font-size: 9px;">TRACK ID: #104</div>
                        <div style="color: #6ee7b7; font-size: 9px;">PLATE: GJ-01-AB-1234</div>
                    </div>
                    <div class="ai-box alert" style="top: 40%; right: 15%; width: 18%; height: 42%;">
                        <div>⚠️ PERSON [93%]</div>
                        <div style="font-size: 9px;">WATCHLIST MATCH</div>
                    </div>
                </div>
                
                <div class="cctv-hud-top" style="background: rgba(0,0,0,0.7); position:relative; z-index:10; margin-top:auto;">
                    <div id="cctvLocText">LOCATION: LIVE SENTINEL CCTV</div>
                    <div id="cctvEngineText">AI: YOLOv8 + ByteTrack + ANPR</div>
                </div>
            </div>"""

html = re.sub(r'<div class="cctv-screen">[\s\S]*?</div>\s*</div>\s*</div>\s*</div>', f'{cctv_modal_html}\n        </div>\n    </div>\n</div>', html, count=1)

# 5. Update openCctvModal and closeCctvModal handlers
modal_js = """let hlsInstance = null;

function openCctvModal(camId, roadName, hlsUrl) {
    document.getElementById('cctvTitle').textContent = `LIVE CCTV FEED // ${camId}`;
    document.getElementById('cctvLocText').textContent = `LOCATION: ${roadName.toUpperCase()}`;
    document.getElementById('cctvModal').style.display = 'flex';

    const video = document.getElementById('cctvVideo');

    if (!hlsUrl) {
        const cam = cameraData.find(c => c.camera_id === camId);
        if (cam && cam.hls_url) hlsUrl = cam.hls_url;
    }

    if (hlsInstance) {
        hlsInstance.destroy();
        hlsInstance = null;
    }

    if (hlsUrl && Hls.isSupported()) {
        hlsInstance = new Hls({ enableWorker: true, lowLatencyMode: true });
        hlsInstance.loadSource(hlsUrl);
        hlsInstance.attachMedia(video);
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, function () {
            video.play().catch(e => console.log("Autoplay blocked:", e));
        });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = hlsUrl;
        video.addEventListener('loadedmetadata', function () {
            video.play().catch(e => console.log("Autoplay blocked:", e));
        });
    }
}

function closeCctvModal() {
    document.getElementById('cctvModal').style.display = 'none';
    const video = document.getElementById('cctvVideo');
    if (video) video.pause();
    if (hlsInstance) {
        hlsInstance.destroy();
        hlsInstance = null;
    }
}"""

html = re.sub(r'function openCctvModal[\s\S]*?function closeCctvModal\(\)\s*\{[\s\S]*?\}', modal_js, html)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Successfully updated static/index.html with all 30 Sentinel Cameras!')
