import re

with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

ai_lab_js = """
// =========================================================================
// AI MODEL TESTING LAB CONTROLLER (6-ENGINE ECOSYSTEM)
// =========================================================================

function openAiLabModal() {
    document.getElementById('aiLabModal').style.display = 'flex';
    switchAiTab('yolo');
}

function closeAiLabModal() {
    document.getElementById('aiLabModal').style.display = 'none';
    if (byteTrackAnim) {
        cancelAnimationFrame(byteTrackAnim);
        byteTrackAnim = null;
    }
}

function switchAiTab(tabName) {
    document.querySelectorAll('.ai-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.ai-tab-pane').forEach(p => p.classList.remove('active'));

    const tabBtn = Array.from(document.querySelectorAll('.ai-tab-btn')).find(b => b.textContent.toLowerCase().includes(tabName));
    if (tabBtn) tabBtn.classList.add('active');

    const pane = document.getElementById(`tab-${tabName}`);
    if (pane) pane.classList.add('active');

    if (tabName === 'yolo') renderYoloDetections();
    else if (tabName === 'bytetrack') startByteTrackSim();
    else if (tabName === 'anpr') runAnprScan();
    else if (tabName === 'reid') runReidMatch();
    else if (tabName === 'vlm') runVlmAnalysis();
    else if (tabName === 'copilot') runCopilotInvestigation();
}

// -------------------------------------------------------------------------
// MODEL 1: YOLOv8 Object Detection
// -------------------------------------------------------------------------
const yoloScenes = {
    "junction": [
        { cls: "BUS", conf: 0.94, x: 40, y: 50, w: 160, h: 120, color: "#3b82f6" },
        { cls: "CAR", conf: 0.96, x: 220, y: 110, w: 110, h: 75, color: "#10b981" },
        { cls: "PERSON", conf: 0.89, x: 350, y: 90, w: 35, h: 85, color: "#f59e0b" },
        { cls: "MOTORCYCLE", conf: 0.91, x: 395, y: 125, w: 45, h: 55, color: "#a855f7" }
    ],
    "highway": [
        { cls: "CAR", conf: 0.98, x: 60, y: 80, w: 130, h: 85, color: "#10b981" },
        { cls: "TRUCK", conf: 0.92, x: 210, y: 40, w: 150, h: 140, color: "#3b82f6" },
        { cls: "CAR", conf: 0.95, x: 375, y: 100, w: 75, h: 65, color: "#10b981" }
    ],
    "toll": [
        { cls: "CAR", conf: 0.93, x: 120, y: 90, w: 140, h: 90, color: "#10b981" },
        { cls: "PERSON", conf: 0.88, x: 290, y: 85, w: 35, h: 95, color: "#f59e0b" },
        { cls: "OTHER_VEHICLE", conf: 0.79, x: 340, y: 70, w: 100, h: 110, color: "#ef4444" }
    ]
};

function loadYoloScene(val) {
    renderYoloDetections();
}

function renderYoloDetections() {
    const canvas = document.getElementById('yoloCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = 460;
    const h = canvas.height = 230;

    const sceneKey = document.getElementById('yoloSceneSelect').value || 'junction';
    const thresh = parseFloat(document.getElementById('yoloConfVal').textContent) || 0.45;
    const detections = yoloScenes[sceneKey] || yoloScenes['junction'];

    // Dark Road Background
    ctx.fillStyle = '#090e1a';
    ctx.fillRect(0, 0, w, h);

    // Grid Perspective
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(w*0.35, 30); ctx.lineTo(0, h);
    ctx.moveTo(w*0.65, 30); ctx.lineTo(w, h);
    ctx.stroke();

    let passedDets = [];
    detections.forEach(d => {
        if (d.conf >= thresh) {
            passedDets.push(d);
            // Box
            ctx.fillStyle = d.color + '22';
            ctx.fillRect(d.x, d.y, d.w, d.h);
            ctx.strokeStyle = d.color;
            ctx.lineWidth = 2;
            ctx.strokeRect(d.x, d.y, d.w, d.h);

            // Tag
            ctx.fillStyle = d.color;
            ctx.fillRect(d.x - 1, d.y - 18, ctx.measureText(`${d.cls} ${(d.conf*100).toFixed(0)}%`).width + 12, 18);
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 10px JetBrains Mono, monospace';
            ctx.fillText(`${d.cls} ${(d.conf*100).toFixed(0)}%`, d.x + 4, d.y - 5);
        }
    });

    const latency = (10 + Math.random() * 4).toFixed(1);
    document.getElementById('yoloLatency').textContent = `LATENCY: ${latency} ms`;

    let log = `=== [YOLOv8 REAL-TIME DETECTION SUMMARY] ===\n`;
    log += `Input Frame:       1280x720 RGB Keyframe\n`;
    log += `Inference Device:  NVIDIA CUDA / PyTorch Acceleration\n`;
    log += `Total Detected:    ${passedDets.length} objects (Filtered with IoU 0.45, Conf >= ${thresh})\n\n`;
    passedDets.forEach((d, i) => {
        log += `[${i+1}] ${d.cls.padEnd(14)} Conf: ${(d.conf*100).toFixed(1)}% | Box: (${d.x}, ${d.y}, ${d.x+d.w}, ${d.y+d.h})\n`;
    });
    document.getElementById('yoloOutputText').textContent = log;
}

// -------------------------------------------------------------------------
// MODEL 2: ByteTrack Multi-Object Tracking
// -------------------------------------------------------------------------
let byteTrackAnim = null;
let isByteTrackPlaying = true;
let trackObjects = [
    { id: 104, type: "CAR", x: 60, y: 130, w: 90, h: 55, speed: 2.2, color: "#10b981", heading: "EAST" },
    { id: 107, type: "BUS", x: 220, y: 70, w: 140, h: 80, speed: 1.4, color: "#3b82f6", heading: "EAST" },
    { id: 109, type: "MOTORCYCLE", x: 380, y: 170, w: 45, h: 40, speed: 2.8, color: "#ef4444", heading: "NORTH_EAST" }
];

function startByteTrackSim() {
    const canvas = document.getElementById('trackCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = 460;
    const h = canvas.height = 260;

    function loop() {
        ctx.fillStyle = '#060a14';
        ctx.fillRect(0, 0, w, h);

        // Highway Lanes
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, 60); ctx.lineTo(w, 60);
        ctx.moveTo(0, 150); ctx.lineTo(w, 150);
        ctx.moveTo(0, 240); ctx.lineTo(w, 240);
        ctx.stroke();

        ctx.strokeStyle = '#334155';
        ctx.setLineDash([12, 12]);
        ctx.beginPath();
        ctx.moveTo(0, 105); ctx.lineTo(w, 105);
        ctx.moveTo(0, 195); ctx.lineTo(w, 195);
        ctx.stroke();
        ctx.setLineDash([]);

        if (isByteTrackPlaying) {
            trackObjects.forEach(v => {
                v.x += v.speed;
                if (v.x > w + 40) v.x = -v.w - 20;
            });
        }

        let log = `=== [BYTETRACK MULTI-CAMERA TRAJECTORY LOG] ===\n`;
        log += `Association Mode:  Kalman Filter + Hungarian IoU\n`;
        log += `Active Trackers:   ${trackObjects.length} Persistent IDs\n\n`;

        trackObjects.forEach((v, idx) => {
            // Draw Box
            ctx.fillStyle = v.color + '22';
            ctx.fillRect(v.x, v.y, v.w, v.h);
            ctx.strokeStyle = v.color;
            ctx.lineWidth = 2;
            ctx.strokeRect(v.x, v.y, v.w, v.h);

            // Trajectory Trail
            ctx.strokeStyle = v.color;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(v.x, v.y + v.h/2);
            ctx.lineTo(v.x - 35, v.y + v.h/2);
            ctx.stroke();

            // Label
            ctx.fillStyle = v.color;
            ctx.font = 'bold 10px JetBrains Mono, monospace';
            ctx.fillText(`TRACK #${v.id} [${v.type}]`, v.x + 2, v.y - 6);

            const speedKmph = (v.speed * 22).toFixed(1);
            log += `[TRACK #${v.id}] ${v.type.padEnd(10)} | Speed: ${speedKmph.padStart(4)} km/h | Heading: ${v.heading.padEnd(10)} | Center: (${Math.round(v.x+v.w/2)}, ${Math.round(v.y+v.h/2)})\n`;
        });

        document.getElementById('trackOutputLog').textContent = log;
        document.getElementById('trackActiveCount').textContent = `ACTIVE: ${trackObjects.length}`;

        byteTrackAnim = requestAnimationFrame(loop);
    }

    if (byteTrackAnim) cancelAnimationFrame(byteTrackAnim);
    byteTrackAnim = requestAnimationFrame(loop);
}

function toggleByteTrackLoop() {
    isByteTrackPlaying = !isByteTrackPlaying;
    document.getElementById('btnByteTrackPlay').textContent = isByteTrackPlaying ? '⏸ Pause Motion' : '▶ Resume Motion';
}

function spawnTrackVehicle() {
    const types = ["CAR", "SUV", "VAN", "BIKE"];
    const colors = ["#10b981", "#3b82f6", "#f59e0b", "#a855f7"];
    const newId = 110 + trackObjects.length;
    const t = types[Math.floor(Math.random() * types.length)];
    const c = colors[Math.floor(Math.random() * colors.length)];
    trackObjects.push({
        id: newId, type: t, x: -60, y: 70 + Math.random() * 120, w: 75, h: 50,
        speed: 1.5 + Math.random() * 1.5, color: c, heading: "EAST"
    });
}

function resetByteTracker() {
    trackObjects = [
        { id: 104, type: "CAR", x: 60, y: 130, w: 90, h: 55, speed: 2.2, color: "#10b981", heading: "EAST" },
        { id: 107, type: "BUS", x: 220, y: 70, w: 140, h: 80, speed: 1.4, color: "#3b82f6", heading: "EAST" },
        { id: 109, type: "MOTORCYCLE", x: 380, y: 170, w: 45, h: 40, speed: 2.8, color: "#ef4444", heading: "NORTH_EAST" }
    ];
}

// -------------------------------------------------------------------------
// MODEL 3: Two-Stage ANPR & Gujarat RTO
// -------------------------------------------------------------------------
const gujaratRtoDict = {
    "01": { district: "Ahmedabad City", rto: "Subhash Bridge RTO" },
    "02": { district: "Mehsana", rto: "Mehsana District RTO" },
    "03": { district: "Rajkot", rto: "Rajkot Central RTO" },
    "04": { district: "Bhavnagar", rto: "Bhavnagar RTO" },
    "05": { district: "Surat", rto: "Surat City RTO" },
    "06": { district: "Vadodara", rto: "Vadodara Central RTO" },
    "07": { district: "Kheda / Nadiad", rto: "Nadiad RTO" },
    "08": { district: "Banaskantha", rto: "Palanpur RTO" },
    "09": { district: "Sabar Kantha", rto: "Himmatnagar RTO" },
    "10": { district: "Jamnagar", rto: "Jamnagar RTO" },
    "11": { district: "Junagadh", rto: "Junagadh RTO" },
    "12": { district: "Kutch", rto: "Bhuj / Gandhidham RTO" },
    "18": { district: "Gandhinagar", rto: "Gandhinagar Capital RTO" },
    "21": { district: "Navsari", rto: "Navsari Coastal RTO" },
    "24": { district: "Patan", rto: "Patan RTO" },
    "32": { district: "Gir Somnath", rto: "Veraval NH-51 RTO" }
};

function setAnprPlate(p) {
    document.getElementById('anprInputPlate').value = p;
    runAnprScan();
}

function runAnprScan() {
    const raw = (document.getElementById('anprInputPlate').value || 'GJ01AB1234').toUpperCase().replace(/[^A-Z0-9]/g, '');
    document.getElementById('plateVisualText').textContent = raw.match(/.{1,2}/g)?.join(' ') || raw;

    let isGj = raw.startsWith('GJ');
    let rtoCode = raw.substring(2, 4);
    let rtoInfo = gujaratRtoDict[rtoCode] || (isGj ? { district: "Gujarat State", rto: `GJ-${rtoCode} Regional Office` } : { district: "Out-of-State Vehicle", rto: "Non-Gujarat Jurisdiction" });

    const isWatchlist = raw.includes("9921") || raw.includes("1234");
    const badge = document.getElementById('anprStatusBadge');
    if (isWatchlist) {
        badge.textContent = "🚨 SUSPECT HOTLIST HIT";
        badge.style.color = "#ef4444";
    } else {
        badge.textContent = "✅ VERIFIED CLEAN";
        badge.style.color = "#10b981";
    }

    let out = `=== [TWO-STAGE ANPR & GUJARAT RTO EXTRACTION] ===\n`;
    out += `Raw OCR Text:         '${raw}'\n`;
    out += `Normalized String:    '${raw}' (Confidence: 96.8%)\n`;
    out += `State Jurisdiction:   ${isGj ? 'GUJARAT STATE (GJ)' : 'OUT-OF-STATE REGISTRATION'}\n`;
    out += `RTO District:         ${rtoInfo.district}\n`;
    out += `Authority Office:     ${rtoInfo.rto}\n`;
    out += `Watchlist Status:     ${isWatchlist ? '🚨 HIGH-PRIORITY INTERCEPT ALERT' : 'Normal / No active flags'}\n\n`;
    out += `Tactical Directive:   ${isWatchlist ? 'Broadcasting sighting to nearest PCR vans & toll plaza barriers.' : 'Logged to surveillance telemetry database.'}`;

    document.getElementById('anprOutputResult').textContent = out;
}

// -------------------------------------------------------------------------
// MODEL 4: FastReID Cross-Camera Matching
// -------------------------------------------------------------------------
function runReidMatch() {
    const target = document.getElementById('reidTargetSelect').value;
    const desc = document.getElementById('reidSignatureDesc');
    
    let targetName = "Suspect Alpha";
    if (target === "vehicle_scorpio") targetName = "Black Scorpio SUV";
    if (target === "person_blue") targetName = "Suspect Charlie (Blue Denim)";

    desc.innerHTML = `Target: <b>${targetName}</b><br>Embedding Dimension: <b>512-dim Normalized Vector</b><br>Camera Network: <b>30 Sentinel Gujarat Nodes Active</b>`;

    let out = `=== [FAST-REID CROSS-CAMERA EMBEDDING COMPARISON] ===\n`;
    out += `Query Signature:   512-dim visual vector for [${targetName}]\n`;
    out += `Metric:            Cosine Distance Similarity (Threshold >= 0.70)\n\n`;

    out += `[RANK #1] 🎯 100.0% MATCH  | Camera: CAM_SEN_001 (Chiman Bhai Bridge, Ahmedabad)\n`;
    out += `          Timestamp: 21:10:15 IST | Status: CONFIRMED SIGHTING\n`;
    out += `          Vector Sim: 0.9982 | Evidence: /evidence/ahm_001_crop.jpg\n\n`;

    out += `[RANK #2] 🎯  98.4% MATCH  | Camera: CAM_SEN_002 (Janpath Road Junction, Ahmedabad)\n`;
    out += `          Timestamp: 21:14:30 IST | Status: CONFIRMED SIGHTING\n`;
    out += `          Vector Sim: 0.9841 | Evidence: /evidence/ahm_002_crop.jpg\n\n`;

    out += `[RANK #3] ⚠️  41.2% NO MATCH | Camera: CAM_SEN_017 (Central Bus Port, Rajkot)\n`;
    out += `          Timestamp: 21:28:00 IST | Status: REJECTED (Below Similarity Threshold)\n`;
    out += `          Vector Sim: 0.4120 | Evidence: /evidence/rjk_017_crop.jpg\n\n`;

    out += `--> Result: Target trajectory correlated moving North along Ahmedabad Corridor.`;
    document.getElementById('reidOutputResults').textContent = out;
}

// -------------------------------------------------------------------------
// MODEL 5: Contextual VLM Scene Analyzer
// -------------------------------------------------------------------------
function setVlmPrompt(p) {
    document.getElementById('vlmContextInput').value = p;
    runVlmAnalysis();
}

function runVlmAnalysis() {
    const prompt = document.getElementById('vlmContextInput').value || 'Surveillance scene review';
    let isHighThreat = prompt.toLowerCase().includes('curfew') || prompt.toLowerCase().includes('hit-and-run') || prompt.toLowerCase().includes('concealed');

    const badge = document.getElementById('vlmThreatBadge');
    badge.textContent = isHighThreat ? 'THREAT: HIGH (92%)' : 'THREAT: LOW (95%)';
    badge.style.color = isHighThreat ? '#ef4444' : '#10b981';

    let out = `=== [CONTEXTUAL VISION-LANGUAGE INCIDENT ASSESSMENT] ===\n`;
    out += `Incident Category:    ${isHighThreat ? 'PERIMETER_SECURITY_VIOLATION' : 'ROUTINE_TRAFFIC_FLOW'}\n`;
    out += `Threat Level:         ${isHighThreat ? 'CRITICAL / HIGH-RISK' : 'NORMAL'}\n`;
    out += `Confidence Score:     92.6%\n\n`;
    out += `[TACTICAL SITUATION SUMMARY]:\n`;
    out += `VLM analysis evaluated camera keyframe against contextual incident parameters: "${prompt}".\n`;
    out += `Visual telemetry identifies anomaly corresponding to high-velocity movement during restricted sector window.\n\n`;
    out += `Recommended Protocol: Dispatch patrol interceptor and capture high-resolution plate snapshot.`;

    document.getElementById('vlmOutputBrief').textContent = out;
}

// -------------------------------------------------------------------------
// MODEL 6: Police Copilot Agent
// -------------------------------------------------------------------------
function setCopilotQuery(q) {
    document.getElementById('copilotQueryInput').value = q;
    runCopilotInvestigation();
}

function runCopilotInvestigation() {
    const query = document.getElementById('copilotQueryInput').value || 'Locate suspect';

    let out = `=== [POLICE COPILOT AUTONOMOUS INVESTIGATION AGENT] ===\n`;
    out += `Officer Query:       "${query}"\n`;
    out += `Intent Detected:     VEHICLE_INCIDENT_CORRELATION\n`;
    out += `Extracted Filters:   { 'vehicle': 'Scorpio/Sedan', 'district': 'Ahmedabad', 'plate': 'GJ-01-XX-9921' }\n`;
    out += `Confidence Score:    94.5%\n\n`;
    out += `[CORRELATED MOVEMENT TIMELINE]:\n`;
    out += `  • 21:10:00 IST - Sighting at CAM_SEN_001 (Chiman Bhai Bridge Corridor) | Speed: 42 km/h\n`;
    out += `  • 21:14:30 IST - Sighting at CAM_SEN_002 (Janpath Road Junction)      | Speed: 38 km/h\n`;
    out += `  • 21:20:15 IST - Sighting at CAM_SEN_005 (Visat Teen Rasta Circle)    | Speed: 55 km/h\n`;
    out += `  • 21:23:40 IST - Predicted Trajectory -> Adalaj Tollnaka (Gandhinagar Gateway)\n\n`;
    out += `[TACTICAL ACTION ORDERS]:\n`;
    out += `  1. 🚨 Alert Gandhinagar & Sanand Toll Plazas to lower security barriers for plate GJ-01-XX-9921.\n`;
    out += `  2. 🚓 Dispatch Sabarmati PCR Mobile Unit #4 to intercept along SG Highway North axis.\n`;
    out += `  3. 📹 Lock pan-tilt-zoom surveillance focus on CAM_SEN_012 (Adalaj Expressway).`;

    document.getElementById('copilotOutputPlan').textContent = out;
}
"""

# Insert JS before window.onload = initMap;
if "function openAiLabModal()" not in html:
    html = html.replace('window.onload = initMap;', f'{ai_lab_js}\n\nwindow.onload = initMap;')

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Injected AI Model Lab JavaScript controller functions successfully!")
