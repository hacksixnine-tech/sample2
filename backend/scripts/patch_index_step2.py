import re

with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

ai_lab_modal_html = """
<!-- AI MODEL TESTING LAB MODAL -->
<div class="modal-overlay" id="aiLabModal">
    <div class="ai-lab-modal">
        <!-- Header -->
        <div class="modal-header" style="background: linear-gradient(180deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95));">
            <div>
                <h3 style="color:#34d399; display:flex; align-items:center; gap:8px;">
                    <span>🧪 TACTICAL AI TESTING LAB</span>
                    <span style="font-size:10px; padding:2px 6px; border-radius:4px; background:rgba(16,185,129,0.2); color:#6ee7b7; border:1px solid rgba(16,185,129,0.4);">6-MODEL ECOSYSTEM</span>
                </h3>
                <p style="margin:2px 0 0; font-size:11px; color:#94a3b8;">Interactive verification harness for YOLOv8, ByteTrack, Two-Stage ANPR, FastReID, VLM, and Copilot Agent</p>
            </div>
            <button class="modal-close" onclick="closeAiLabModal()">&times;</button>
        </div>

        <!-- Tabs Navigation -->
        <div class="ai-lab-tabs">
            <button class="ai-tab-btn active" onclick="switchAiTab('yolo')">1. 🎯 YOLOv8 Detection</button>
            <button class="ai-tab-btn" onclick="switchAiTab('bytetrack')">2. 🔄 ByteTrack Tracking</button>
            <button class="ai-tab-btn" onclick="switchAiTab('anpr')">3. 🔍 ANPR & RTO OCR</button>
            <button class="ai-tab-btn" onclick="switchAiTab('reid')">4. 🧬 FastReID Matcher</button>
            <button class="ai-tab-btn" onclick="switchAiTab('vlm')">5. 👁️ Contextual VLM</button>
            <button class="ai-tab-btn" onclick="switchAiTab('copilot')">6. 🤖 Police Copilot</button>
        </div>

        <!-- TAB 1: YOLOv8 Object Detection -->
        <div class="ai-tab-pane active" id="tab-yolo">
            <div class="ai-grid-2">
                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>SURVEILLANCE SCENE SELECTOR</span><span style="color:#10b981;">Ultralytics YOLOv8n</span></div>
                        <div style="margin-bottom:10px;">
                            <label style="font-size:11px; color:#94a3b8; display:block; margin-bottom:4px;">Test Scene:</label>
                            <select id="yoloSceneSelect" onchange="loadYoloScene(this.value)" style="width:100%; height:34px; background:#040711; border:1px solid #334155; color:#fff; border-radius:6px; padding:0 8px; font-family:'JetBrains Mono',monospace; font-size:11px;">
                                <option value="junction">Scene A: Ahmedabad CG Road Junction (Bus + Cars + Persons)</option>
                                <option value="highway">Scene B: SG Highway Express Corridor (Vehicles + Bikes)</option>
                                <option value="toll">Scene C: Night Adalaj Tollnaka (Low-Light Target)</option>
                            </select>
                        </div>
                        <div style="margin-bottom:12px;">
                            <label style="font-size:11px; color:#94a3b8; display:block; margin-bottom:4px;">Confidence Threshold: <b id="yoloConfVal" style="color:#38bdf8;">0.45</b></label>
                            <input type="range" min="0.20" max="0.90" step="0.05" value="0.45" oninput="document.getElementById('yoloConfVal').textContent = this.value; renderYoloDetections();" style="width:100%;">
                        </div>
                        <button class="btn-primary" onclick="renderYoloDetections()" style="width:100%;">▶ Run YOLOv8 Real-Time Inference</button>
                    </div>

                    <div style="position:relative; width:100%; height:230px; background:#020617; border-radius:10px; overflow:hidden; border:1px solid #1e293b;">
                        <canvas id="yoloCanvas" width="460" height="230" style="width:100%; height:100%; object-fit:contain;"></canvas>
                    </div>
                </div>

                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>MODEL INFERENCE TELEMETRY</span><span id="yoloLatency" style="color:#f59e0b;">LATENCY: 12.4 ms</span></div>
                        <div class="ai-output-box" id="yoloOutputText">Click "Run YOLOv8 Real-Time Inference" to process the frame...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: ByteTrack Multi-Object Tracking -->
        <div class="ai-tab-pane" id="tab-bytetrack">
            <div class="ai-grid-2">
                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>REAL-TIME TRAJECTORY ENGINE</span><span style="color:#10b981;">ByteTrack v0.28</span></div>
                        <div style="display:flex; gap:8px; margin-bottom:10px;">
                            <button class="btn-primary" onclick="toggleByteTrackLoop()" id="btnByteTrackPlay" style="flex:1;">⏸ Pause Motion</button>
                            <button class="btn-secondary" onclick="spawnTrackVehicle()" style="flex:1;">➕ Spawn Target</button>
                            <button class="btn-secondary" onclick="resetByteTracker()" style="flex:1;">🔄 Reset</button>
                        </div>
                    </div>

                    <div style="position:relative; width:100%; height:260px; background:#020617; border-radius:10px; overflow:hidden; border:1px solid #1e293b;">
                        <canvas id="trackCanvas" width="460" height="260" style="width:100%; height:100%;"></canvas>
                    </div>
                </div>

                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>ACTIVE TRACKS & VELOCITY LOG</span><span style="color:#34d399;" id="trackActiveCount">ACTIVE: 3</span></div>
                        <div class="ai-output-box" id="trackOutputLog">Tracking active objects...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 3: Two-Stage ANPR & Gujarat RTO -->
        <div class="ai-tab-pane" id="tab-anpr">
            <div class="ai-grid-2">
                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>LICENSE PLATE OCR SCANNER</span><span style="color:#10b981;">EasyOCR + Regex Normalizer</span></div>
                        <div style="margin-bottom:8px;">
                            <label style="font-size:11px; color:#94a3b8; display:block; margin-bottom:4px;">Vehicle License Plate:</label>
                            <input id="anprInputPlate" type="text" value="GJ01AB1234" style="width:100%; height:34px; background:#040711; border:1px solid #334155; color:#fff; border-radius:6px; padding:0 10px; font-family:'JetBrains Mono',monospace; font-size:13px; font-weight:700; text-transform:uppercase;">
                        </div>

                        <div style="margin-bottom:10px;">
                            <span style="font-size:10px; color:#64748b; display:block; margin-bottom:4px;">QUICK GUJARAT RTO PRESETS:</span>
                            <span class="quick-chip" onclick="setAnprPlate('GJ01AB1234')">GJ-01 Ahmedabad</span>
                            <span class="quick-chip" onclick="setAnprPlate('GJ02CD5678')">GJ-02 Mehsana</span>
                            <span class="quick-chip" onclick="setAnprPlate('GJ03EF9012')">GJ-03 Rajkot</span>
                            <span class="quick-chip" onclick="setAnprPlate('GJ05GH3456')">GJ-05 Surat</span>
                            <span class="quick-chip" onclick="setAnprPlate('GJ06IJ7890')">GJ-06 Vadodara</span>
                            <span class="quick-chip" onclick="setAnprPlate('GJ18KL1122')">GJ-18 Gandhinagar</span>
                            <span class="quick-chip" onclick="setAnprPlate('GJ24GH3344')">GJ-24 Patan</span>
                            <span class="quick-chip" onclick="setAnprPlate('GJ11JK6677')">GJ-11 Junagadh</span>
                            <span class="quick-chip" onclick="setAnprPlate('DL01AB9988')">DL-01 Delhi (Out-of-State)</span>
                        </div>

                        <button class="btn-primary" onclick="runAnprScan()" style="width:100%;">🔍 Execute ANPR & Jurisdiction OCR</button>
                    </div>

                    <!-- Visual Plate Rendering -->
                    <div style="background:#f8fafc; border:3px solid #000; border-radius:8px; padding:12px; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.5);">
                        <div style="display:flex; align-items:center; justify-content:center; gap:8px;">
                            <div style="background:#003399; color:#ffcc00; font-size:10px; font-weight:800; padding:2px 4px; border-radius:3px;">IND</div>
                            <div id="plateVisualText" style="font-family:'JetBrains Mono',monospace; font-size:24px; font-weight:900; color:#0f172a; letter-spacing:3px;">GJ 01 AB 1234</div>
                        </div>
                    </div>
                </div>

                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>JURISDICTION & WATCHLIST STATUS</span><span id="anprStatusBadge" style="color:#10b981;">VERIFIED</span></div>
                        <div class="ai-output-box" id="anprOutputResult">Click "Execute ANPR & Jurisdiction OCR" to parse plate...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 4: FastReID Cross-Camera Matching -->
        <div class="ai-tab-pane" id="tab-reid">
            <div class="ai-grid-2">
                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>CROSS-CAMERA VISUAL EMBEDDINGS</span><span style="color:#10b981;">FastReID / OSNet 512-dim</span></div>
                        <div style="margin-bottom:10px;">
                            <label style="font-size:11px; color:#94a3b8; display:block; margin-bottom:4px;">Target Suspect Signature:</label>
                            <select id="reidTargetSelect" onchange="runReidMatch()" style="width:100%; height:34px; background:#040711; border:1px solid #334155; color:#fff; border-radius:6px; padding:0 8px; font-family:'JetBrains Mono',monospace; font-size:11px;">
                                <option value="suspect_red">Suspect Alpha: Red Jacket, Dark Trousers, Black Cap</option>
                                <option value="vehicle_scorpio">Vehicle Bravo: Black Scorpio SUV (GJ-01-XX-9921)</option>
                                <option value="person_blue">Suspect Charlie: Blue Denim Shirt & Backpack</option>
                            </select>
                        </div>
                        <button class="btn-primary" onclick="runReidMatch()" style="width:100%;">🧬 Search Cross-Camera ReID Gallery</button>
                    </div>

                    <div class="ai-card">
                        <div class="ai-card-title"><span>TARGET APPEARANCE SIGNATURE</span></div>
                        <div style="font-size:11px; color:#94a3b8; line-height:1.5;" id="reidSignatureDesc">
                            Feature Vector: 512-dimensional normalized Euclidean embedding.<br>
                            Camera Gallery: 30 Sentinel Gujarat nodes active.
                        </div>
                    </div>
                </div>

                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>CROSS-DISTRICT MATCH RANKINGS</span><span style="color:#38bdf8;">COSINE SIMILARITY</span></div>
                        <div class="ai-output-box" id="reidOutputResults">Click "Search Cross-Camera ReID Gallery" to calculate similarity...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 5: Contextual VLM Scene Analyzer -->
        <div class="ai-tab-pane" id="tab-vlm">
            <div class="ai-grid-2">
                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>VISION-LANGUAGE INCIDENT REASONING</span><span style="color:#10b981;">Contextual VLM</span></div>
                        <div style="margin-bottom:8px;">
                            <label style="font-size:11px; color:#94a3b8; display:block; margin-bottom:4px;">Surveillance Incident Context / Prompt:</label>
                            <textarea id="vlmContextInput" style="width:100%; height:75px; background:#040711; border:1px solid #334155; color:#fff; border-radius:6px; padding:8px; font-family:'JetBrains Mono',monospace; font-size:11px; resize:none;">Red vehicle speeding through SG Highway Toll during curfew hours with concealed license plate</textarea>
                        </div>

                        <div style="margin-bottom:10px;">
                            <span style="font-size:10px; color:#64748b; display:block; margin-bottom:4px;">INCIDENT PRESETS:</span>
                            <span class="quick-chip" onclick="setVlmPrompt('Red vehicle speeding through SG Highway Toll during curfew hours with concealed license plate')">🚨 Night Curfew Breach</span>
                            <span class="quick-chip" onclick="setVlmPrompt('Suspicious group of 3 individuals loitering near perimeter transformer fence at 02:30 AM')">⚠️ Perimeter Loitering</span>
                            <span class="quick-chip" onclick="setVlmPrompt('Motorcycle collision with pedestrian on Janpath Road; rider fleeing North towards Sabarmati')">🚨 Hit-and-Run Incident</span>
                        </div>

                        <button class="btn-primary" onclick="runVlmAnalysis()" style="width:100%;">👁️ Analyze Scene with VLM</button>
                    </div>
                </div>

                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>VLM SITUATIONAL AWARENESS BRIEF</span><span id="vlmThreatBadge" style="color:#ef4444;">THREAT: HIGH</span></div>
                        <div class="ai-output-box" id="vlmOutputBrief">Click "Analyze Scene with VLM" to generate situational assessment...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 6: Police Copilot Agent -->
        <div class="ai-tab-pane" id="tab-copilot">
            <div class="ai-grid-2">
                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>POLICE COPILOT AUTONOMOUS AGENT</span><span style="color:#10b981;">LLM Tool-Calling Engine</span></div>
                        <div style="margin-bottom:8px;">
                            <label style="font-size:11px; color:#94a3b8; display:block; margin-bottom:4px;">Dispatcher / Officer Natural Language Query:</label>
                            <textarea id="copilotQueryInput" style="width:100%; height:75px; background:#040711; border:1px solid #334155; color:#fff; border-radius:6px; padding:8px; font-family:'JetBrains Mono',monospace; font-size:11px; resize:none;">Locate black Scorpio GJ-01-XX-9921 last seen near Chiman Bhai Bridge and dispatch intercept unit</textarea>
                        </div>

                        <div style="margin-bottom:10px;">
                            <span style="font-size:10px; color:#64748b; display:block; margin-bottom:4px;">QUERY PRESETS:</span>
                            <span class="quick-chip" onclick="setCopilotQuery('Locate black Scorpio GJ-01-XX-9921 last seen near Chiman Bhai Bridge and dispatch intercept unit')">🚨 Track Wanted Scorpio</span>
                            <span class="quick-chip" onclick="setCopilotQuery('Find white Swift involved in robbery near Navrangpura between 8 PM and 10 PM')">🔍 Correlate Robbery Timeline</span>
                            <span class="quick-chip" onclick="setCopilotQuery('Alert Gandhinagar and Sanand Toll gates for fleeing suspect on SG Highway')">📢 Broadcast Intercept Order</span>
                        </div>

                        <button class="btn-primary" onclick="runCopilotInvestigation()" style="width:100%;">🤖 Execute Copilot Investigation</button>
                    </div>
                </div>

                <div>
                    <div class="ai-card">
                        <div class="ai-card-title"><span>TACTICAL DECISION & TIMELINE</span><span id="copilotConfidence" style="color:#34d399;">CONF: 93.0%</span></div>
                        <div class="ai-output-box" id="copilotOutputPlan">Click "Execute Copilot Investigation" to generate operational dispatch...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
"""

if '<div class="modal-overlay" id="aiLabModal">' not in html:
    html = html.replace('<!-- CCTV Tactical Modal -->', f'{ai_lab_modal_html}\n\n<!-- CCTV Tactical Modal -->')

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Injected AI Model Lab Modal HTML successfully!")
