/**
 * PHANTOM // Mission-Critical CCTV Intelligence Platform
 * Pure Vanilla JavaScript Architecture (Zero Dependencies)
 */

    (function () {
        'use strict';

        // =========================================================================
        // 1. STATE & CONSTANTS
        // =========================================================================
        const API_BASE_URL = window.PHANTOM_API_URL || 'http://localhost:8000/api/v1';

        const STATE = {
            theme: 'dark',
            sidebarCollapsed: false,
            activeGrid: '2x2', // '2x2' or '1x1'
            focusedCamId: null,
            isPlaying: true,
            aiOverlayActive: true,
            nvgActive: false,
            sfxAudioActive: false,
            threatCount: 3,
            backendConnected: false,
            cameraStates: {
                'CAM-01': { pan: 0, tilt: 0, zoom: 1.0, name: 'PERIMETER NORTH GATE', sector: 'Sector 07-A' },
                'CAM-02': { pan: 0, tilt: 0, zoom: 1.0, name: 'CORE VAULT AIRLOCK', sector: 'Sector 07-B' },
                'CAM-03': { pan: 0, tilt: 0, zoom: 1.0, name: 'ROOF HELIPAD WEST', sector: 'Sector 07-C' },
                'CAM-04': { pan: 0, tilt: 0, zoom: 1.0, name: 'QUANTUM SERVER RACK B', sector: 'Sector 07-D' }
            },
            incidents: {
                'INC-802': {
                    id: 'INC-802',
                    type: 'UNAUTHORIZED PERIMETER BREACH',
                    severity: 'SEV-1 CRITICAL',
                    badgeClass: 'red-badge',
                    camera: 'CAM-01 (Sector 07-A)',
                    timestamp: '22:48:12 UTC (00:04:12 AGO)',
                    confidence: '96.8% Neural Match',
                    desc: 'Target bypassed secondary infrared perimeter tripwire at North Gate without encrypted biometric RFID token. Visual recognition confirms humanoid signature wearing tactical vest.',
                    coords: 'LAT 45.3128° N, LON 12.8941° E'
                },
                'INC-799': {
                    id: 'INC-799',
                    type: 'UNREGISTERED UAV DRONE SIGNATURE',
                    severity: 'SEV-2 WARNING',
                    badgeClass: 'amber-badge',
                    camera: 'CAM-03 (Sector 07-C)',
                    timestamp: '22:39:45 UTC (00:12:45 AGO)',
                    confidence: '91.2% Acoustic Doppler',
                    desc: 'Unregistered rotor sound frequency detected within 150m restricted airspace over Roof Helipad. Target altitude ~42m AGL heading 284° at 14 knots.',
                    coords: 'LAT 45.3134° N, LON 12.8955° E'
                },
                'INC-791': {
                    id: 'INC-791',
                    type: 'VEHICLE OCR MATCH // VIP CORTEGE',
                    severity: 'INFO / MATCH',
                    badgeClass: 'cyan-badge',
                    camera: 'CAM-02 (Sector 07-B)',
                    timestamp: '22:34:08 UTC (00:18:22 AGO)',
                    confidence: '99.4% OCR License Match',
                    desc: 'Vehicle license plate #KX-9281-B scanned at Vault Perimeter. Matched with Level-5 VIP Transport manifest for scheduled diplomatic escort arrival.',
                    coords: 'LAT 45.3119° N, LON 12.8920° E'
                }
            }
        };

        // DOM Elements Cache
        const DOM = {
            html: document.documentElement,
            appSidebar: document.getElementById('appSidebar'),
            sidebarCollapseBtn: document.getElementById('sidebarCollapseBtn'),
            mobileMenuBtn: document.getElementById('mobileMenuBtn'),
            themeToggleBtn: document.getElementById('themeToggleBtn'),
            themeModeLabel: document.getElementById('themeModeLabel'),
            liveUtcClock: document.getElementById('liveUtcClock'),
            cameraSearchInput: document.getElementById('cameraSearchInput'),
            alertBellBtn: document.getElementById('alertBellBtn'),
            cctvGrid: document.getElementById('cctvGrid'),
            gridModeLabel: document.getElementById('gridModeLabel'),
            feedBoxes: document.querySelectorAll('.cctv-feed-box'),
            gridToolBtns: document.querySelectorAll('.tool-btn[data-grid]'),
            thermalFilterBtn: document.getElementById('thermalFilterBtn'),
            nightVisionBtn: document.getElementById('nightVisionBtn'),
            snapshotFeedBtn: document.getElementById('snapshotFeedBtn'),
            dvrPlayPauseBtn: document.getElementById('dvrPlayPauseBtn'),
            dvrRewindBtn: document.getElementById('dvrRewindBtn'),
            dvrFastForwardBtn: document.getElementById('dvrFastForwardBtn'),
            timelineSlider: document.querySelector('.timeline-slider'),
            syncStatusText: document.getElementById('syncStatusText'),
            toastContainer: document.getElementById('toastContainer'),
            navLinks: document.querySelectorAll('.nav-link'),
            systemHealthPill: document.getElementById('systemHealthPill'),
            sfxAudioBtn: document.getElementById('sfxAudioBtn'),
            sfxAudioIcon: document.getElementById('sfxAudioIcon'),
            operatorProfileBtn: document.getElementById('operatorProfileBtn'),
            profileDropdownMenu: document.getElementById('profileDropdownMenu'),
            switchSectorBtn: document.getElementById('switchSectorBtn'),
            testAlertTriggerBtn: document.getElementById('testAlertTriggerBtn'),
            exportAuditBtn: document.getElementById('exportAuditBtn'),
            lockStationBtn: document.getElementById('lockStationBtn'),
            pageTitleHeading: document.getElementById('pageTitleHeading'),
            activeSectorLabel: document.getElementById('activeSectorLabel'),
            threatCountStat: document.getElementById('threatCountStat'),
            incidentFeedList: document.getElementById('incidentFeedList'),
            incidentModalBackdrop: document.getElementById('incidentModalBackdrop'),
            closeIncidentModalBtn: document.getElementById('closeIncidentModalBtn'),
            modalIncidentTitle: document.getElementById('modalIncidentTitle'),
            modalIncidentBody: document.getElementById('modalIncidentBody'),
            modalDismissBtn: document.getElementById('modalDismissBtn'),
            modalDispatchBtn: document.getElementById('modalDispatchBtn'),
            diagnosticsModalBackdrop: document.getElementById('diagnosticsModalBackdrop'),
            closeDiagModalBtn: document.getElementById('closeDiagModalBtn'),
            closeDiagBtn: document.getElementById('closeDiagBtn'),
            runDiagBtn: document.getElementById('runDiagBtn')
        };

        // =========================================================================
        // 2. SYNTHESIZED WEB AUDIO HUD SOUND EFFECTS (ZERO EXTERNAL ASSETS)
        // =========================================================================
        let audioCtx = null;

        function playTacticalSound(type = 'click') {
            if (!STATE.sfxAudioActive) return;
            try {
                if (!audioCtx) {
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                }
                if (audioCtx.state === 'suspended') {
                    audioCtx.resume();
                }

                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.connect(gain);
                gain.connect(audioCtx.destination);

                const now = audioCtx.currentTime;

                if (type === 'click') {
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(1400, now);
                    osc.frequency.exponentialRampToValueAtTime(800, now + 0.04);
                    gain.gain.setValueAtTime(0.12, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);
                    osc.start(now);
                    osc.stop(now + 0.04);
                } else if (type === 'alert') {
                    osc.type = 'sawtooth';
                    osc.frequency.setValueAtTime(880, now);
                    osc.frequency.setValueAtTime(1200, now + 0.08);
                    osc.frequency.setValueAtTime(880, now + 0.16);
                    gain.gain.setValueAtTime(0.15, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
                    osc.start(now);
                    osc.stop(now + 0.25);
                } else if (type === 'shutter') {
                    osc.type = 'triangle';
                    osc.frequency.setValueAtTime(3200, now);
                    osc.frequency.exponentialRampToValueAtTime(200, now + 0.08);
                    gain.gain.setValueAtTime(0.2, now);
                    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
                    osc.start(now);
                    osc.stop(now + 0.08);
                }
            } catch (e) {
                // Audio context not allowed without interaction
            }
        }

        function initAudioToggle() {
            if (!DOM.sfxAudioBtn) return;
            DOM.sfxAudioBtn.addEventListener('click', () => {
                STATE.sfxAudioActive = !STATE.sfxAudioActive;
                DOM.sfxAudioBtn.classList.toggle('active-audio', STATE.sfxAudioActive);

                if (STATE.sfxAudioActive) {
                    DOM.sfxAudioBtn.title = 'Tactical HUD SFX: ACTIVE (Click to Mute)';
                    DOM.sfxAudioIcon.innerHTML = `
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                `;
                    playTacticalSound('click');
                    displayToast('Tactical HUD Audio FX: ENGAGED', 'info');
                } else {
                    DOM.sfxAudioBtn.title = 'Tactical HUD SFX: MUTED (Click to Enable)';
                    DOM.sfxAudioIcon.innerHTML = `
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                    <line x1="23" y1="9" x2="17" y2="15"></line>
                    <line x1="17" y1="9" x2="23" y2="15"></line>
                `;
                    displayToast('Tactical HUD Audio FX: MUTED', 'info');
                }
            });
        }

        // =========================================================================
        // 3. THEME CONTROLLER (LIGHT / DARK CUSTOM PROPERTIES ENGINE)
        // =========================================================================
        function initThemeSystem() {
            const storedTheme = localStorage.getItem('phantom-theme');
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

            const initialTheme = storedTheme || (systemPrefersDark ? 'dark' : 'light');
            applyTheme(initialTheme, false);

            if (DOM.themeToggleBtn) {
                DOM.themeToggleBtn.addEventListener('click', () => {
                    toggleTheme();
                    playTacticalSound('click');
                });
            }

            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('phantom-theme')) {
                    applyTheme(e.matches ? 'dark' : 'light', true);
                }
            });
        }

        function applyTheme(theme, showToast = true) {
            STATE.theme = theme;
            DOM.html.setAttribute('data-theme', theme);
            localStorage.setItem('phantom-theme', theme);

            if (DOM.themeModeLabel) {
                DOM.themeModeLabel.textContent = theme === 'dark' ? 'OBSIDIAN' : 'FROSTED';
            }

            if (showToast) {
                displayToast(`Theme Mode: Switched to ${theme.toUpperCase()} profile`, 'info');
            }
        }

        function toggleTheme() {
            const nextTheme = STATE.theme === 'dark' ? 'light' : 'dark';
            applyTheme(nextTheme, true);
        }

        // =========================================================================
        // 4. PRECISION TACTICAL UTC / MISSION CLOCK
        // =========================================================================
        function initTacticalClock() {
            function updateClock() {
                if (!DOM.liveUtcClock) return;
                const now = new Date();
                const hours = String(now.getUTCHours()).padStart(2, '0');
                const minutes = String(now.getUTCMinutes()).padStart(2, '0');
                const seconds = String(now.getUTCSeconds()).padStart(2, '0');
                const ms = String(Math.floor(now.getUTCMilliseconds() / 10)).padStart(2, '0');

                DOM.liveUtcClock.textContent = `${hours}:${minutes}:${seconds}.${ms}`;
            }
            setInterval(updateClock, 40);
            updateClock();
        }

        // =========================================================================
        // 5. SIDEBAR COLLAPSE & NAVIGATION CONTROLLER
        // =========================================================================
        function initSidebarControls() {
            if (DOM.sidebarCollapseBtn) {
                DOM.sidebarCollapseBtn.addEventListener('click', () => {
                    STATE.sidebarCollapsed = !STATE.sidebarCollapsed;
                    document.body.classList.toggle('sidebar-collapsed', STATE.sidebarCollapsed);
                    playTacticalSound('click');
                });
            }

            if (DOM.mobileMenuBtn && DOM.appSidebar) {
                DOM.mobileMenuBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    DOM.appSidebar.classList.toggle('mobile-open');
                    playTacticalSound('click');
                });

                document.addEventListener('click', (e) => {
                    if (!DOM.appSidebar.contains(e.target) && !DOM.mobileMenuBtn.contains(e.target)) {
                        DOM.appSidebar.classList.remove('mobile-open');
                    }
                });
            }

            window.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
                    e.preventDefault();
                    if (DOM.sidebarCollapseBtn) DOM.sidebarCollapseBtn.click();
                }
            });

            // Navigation Link Switching
            DOM.navLinks.forEach((link) => {
                link.addEventListener('click', (e) => {
                    DOM.navLinks.forEach((l) => l.classList.remove('active'));
                    link.classList.add('active');
                    playTacticalSound('click');

                    const viewName = link.querySelector('.nav-text')?.textContent || 'Mission Overview';
                    if (DOM.pageTitleHeading) {
                        DOM.pageTitleHeading.textContent = `${viewName.toUpperCase()} // LIVE COMMAND`;
                    }
                    displayToast(`Navigation: Loaded [${viewName}]`, 'info');
                });
            });
        }

        // =========================================================================
        // 6. LIVE CCTV SIMULATED VIDEO CANVASES WITH PTZ VIEWPORT
        // =========================================================================
        function initCameraFeeds() {
            const canvases = [
                { id: 'canvasCam1', camId: 'CAM-01', type: 'perimeter', color: '#00f0ff' },
                { id: 'canvasCam2', camId: 'CAM-02', type: 'vault', color: '#00ff88' },
                { id: 'canvasCam3', camId: 'CAM-03', type: 'helipad', color: '#ffaa00' },
                { id: 'canvasCam4', camId: 'CAM-04', type: 'server', color: '#00f0ff' }
            ];

            canvases.forEach((cfg) => {
                const canvas = document.getElementById(cfg.id);
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                let frame = 0;

                function renderFeed() {
                    if (!STATE.isPlaying) {
                        requestAnimationFrame(renderFeed);
                        return;
                    }

                    frame++;
                    const w = canvas.width;
                    const h = canvas.height;
                    const camState = STATE.cameraStates[cfg.camId];

                    // Background Texture
                    ctx.fillStyle = STATE.nvgActive ? '#04180a' : '#050912';
                    ctx.fillRect(0, 0, w, h);

                    ctx.save();
                    // Apply PTZ transformations
                    ctx.translate(w / 2, h / 2);
                    ctx.scale(camState.zoom, camState.zoom);
                    ctx.translate(-w / 2 + camState.pan, -h / 2 + camState.tilt);

                    // Perspective Wireframe Ground
                    ctx.strokeStyle = STATE.nvgActive ? 'rgba(0, 255, 100, 0.18)' : 'rgba(0, 240, 255, 0.08)';
                    ctx.lineWidth = 1;

                    if (cfg.type === 'perimeter') {
                        drawPerimeterScene(ctx, w, h, frame);
                    } else if (cfg.type === 'vault') {
                        drawVaultScene(ctx, w, h, frame);
                    } else if (cfg.type === 'helipad') {
                        drawHelipadScene(ctx, w, h, frame);
                    } else if (cfg.type === 'server') {
                        drawServerScene(ctx, w, h, frame);
                    }

                    ctx.restore();

                    // AI Neural Overlays
                    if (STATE.aiOverlayActive) {
                        drawAIHUD(ctx, w, h, frame, cfg.color);
                    }

                    // Digital Noise & Scanline
                    drawCameraNoise(ctx, w, h, frame);

                    requestAnimationFrame(renderFeed);
                }

                renderFeed();
            });
        }

        function drawPerimeterScene(ctx, w, h, frame) {
            ctx.beginPath();
            ctx.moveTo(w * 0.45, h * 0.4);
            ctx.lineTo(w * 0.1, h);
            ctx.moveTo(w * 0.55, h * 0.4);
            ctx.lineTo(w * 0.9, h);
            ctx.stroke();

            ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
            ctx.fillRect(w * 0.2, h * 0.38, w * 0.6, 6);

            const xPos = w * 0.35 + Math.sin(frame * 0.02) * (w * 0.15);
            const yPos = h * 0.55 + Math.cos(frame * 0.02) * 8;

            ctx.strokeStyle = '#ff3366';
            ctx.lineWidth = 1.5;
            ctx.strokeRect(xPos - 18, yPos - 35, 36, 70);

            ctx.fillStyle = 'rgba(255, 51, 102, 0.9)';
            ctx.fillRect(xPos - 18, yPos - 48, 80, 12);
            ctx.fillStyle = '#ffffff';
            ctx.font = '8px monospace';
            ctx.fillText('TARGET #04 [94%]', xPos - 15, yPos - 39);
        }

        function drawVaultScene(ctx, w, h, frame) {
            ctx.strokeStyle = 'rgba(0, 255, 136, 0.3)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(w * 0.5, h * 0.5, 60, 0, Math.PI * 2);
            ctx.stroke();

            const laserY = h * 0.3 + (Math.sin(frame * 0.05) + 1) * 0.5 * (h * 0.4);
            ctx.strokeStyle = 'rgba(0, 255, 136, 0.8)';
            ctx.shadowColor = '#00ff88';
            ctx.shadowBlur = 8;
            ctx.beginPath();
            ctx.moveTo(w * 0.35, laserY);
            ctx.lineTo(w * 0.65, laserY);
            ctx.stroke();
            ctx.shadowBlur = 0;
        }

        function drawHelipadScene(ctx, w, h, frame) {
            ctx.strokeStyle = 'rgba(255, 170, 0, 0.3)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(w * 0.5, h * 0.55, 45, 0, Math.PI * 2);
            ctx.stroke();

            ctx.fillStyle = 'rgba(255, 170, 0, 0.4)';
            ctx.font = '24px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('H', w * 0.5, h * 0.62);
            ctx.textAlign = 'start';

            const uavX = w * 0.65 + Math.cos(frame * 0.03) * 30;
            const uavY = h * 0.25 + Math.sin(frame * 0.03) * 15;

            ctx.strokeStyle = '#ffaa00';
            ctx.strokeRect(uavX - 12, uavY - 12, 24, 24);
            ctx.fillStyle = '#ffaa00';
            ctx.font = '8px monospace';
            ctx.fillText('UAV-03 [42 KTS]', uavX - 12, uavY - 16);
        }

        function drawServerScene(ctx, w, h, frame) {
            for (let i = 0; i < 4; i++) {
                const rx = w * 0.15 + i * (w * 0.2);
                ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
                ctx.fillRect(rx, h * 0.2, w * 0.14, h * 0.65);

                for (let j = 0; j < 8; j++) {
                    const ledY = h * 0.25 + j * 14;
                    const active = Math.sin(frame * 0.1 + i * 2 + j) > 0.1;
                    ctx.fillStyle = active ? '#00f0ff' : 'rgba(0, 240, 255, 0.15)';
                    ctx.fillRect(rx + 6, ledY, 4, 4);
                }
            }
        }

        function drawAIHUD(ctx, w, h, frame, color) {
            ctx.strokeStyle = color;
            ctx.lineWidth = 1;

            const pad = 12;
            const len = 10;

            ctx.beginPath();
            ctx.moveTo(pad, pad + len); ctx.lineTo(pad, pad); ctx.lineTo(pad + len, pad);
            ctx.moveTo(w - pad - len, pad); ctx.lineTo(w - pad, pad); ctx.lineTo(w - pad, pad + len);
            ctx.moveTo(pad, h - pad - len); ctx.lineTo(pad, h - pad); ctx.lineTo(pad + len, h - pad);
            ctx.moveTo(w - pad - len, h - pad); ctx.lineTo(w - pad, h - pad); ctx.lineTo(w - pad, h - pad - len);
            ctx.stroke();
        }

        function drawCameraNoise(ctx, w, h, frame) {
            const scanY = (frame * 1.5) % h;
            ctx.fillStyle = 'rgba(255, 255, 255, 0.04)';
            ctx.fillRect(0, scanY, w, 2);
        }

        // =========================================================================
        // 7. PTZ CONTROLS & CAMERA INTERACTIVITY
        // =========================================================================
        function initCameraGridInteractions() {
            DOM.feedBoxes.forEach((box) => {
                box.addEventListener('click', (e) => {
                    // If clicked on PTZ controls, don't toggle grid focus
                    if (e.target.closest('.ptz-hud-controls')) return;
                    const camId = box.getAttribute('data-cam-id');
                    toggleFeedFocus(box, camId);
                    playTacticalSound('click');
                });

                box.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        box.click();
                    }
                });
            });

            // PTZ Buttons handling
            document.querySelectorAll('.ptz-btn').forEach((btn) => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const feedBox = btn.closest('.cctv-feed-box');
                    const camId = feedBox.getAttribute('data-cam-id');
                    const dir = btn.getAttribute('data-dir');
                    handlePTZPanTilt(camId, dir);
                    playTacticalSound('click');
                });
            });

            document.querySelectorAll('.ptz-zoom-btn').forEach((btn) => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const feedBox = btn.closest('.cctv-feed-box');
                    const camId = feedBox.getAttribute('data-cam-id');
                    const zoomType = btn.getAttribute('data-zoom');
                    handlePTZZoom(camId, zoomType);
                    playTacticalSound('click');
                });
            });

            // Grid Mode selectors
            DOM.gridToolBtns.forEach((btn) => {
                btn.addEventListener('click', () => {
                    DOM.gridToolBtns.forEach((b) => b.classList.remove('active'));
                    btn.classList.add('active');
                    const mode = btn.getAttribute('data-grid');
                    setGridMode(mode);
                    playTacticalSound('click');
                });
            });

            // AI HUD Toggle
            if (DOM.thermalFilterBtn) {
                DOM.thermalFilterBtn.addEventListener('click', () => {
                    STATE.aiOverlayActive = !STATE.aiOverlayActive;
                    DOM.thermalFilterBtn.classList.toggle('active', STATE.aiOverlayActive);
                    playTacticalSound('click');
                    displayToast(`AI Neural HUD: ${STATE.aiOverlayActive ? 'ENGAGED' : 'MUTED'}`, 'info');
                });
            }

            // Night Vision Toggle
            if (DOM.nightVisionBtn) {
                DOM.nightVisionBtn.addEventListener('click', () => {
                    STATE.nvgActive = !STATE.nvgActive;
                    DOM.nightVisionBtn.classList.toggle('active', STATE.nvgActive);
                    playTacticalSound('click');
                    displayToast(`Night Vision IR: ${STATE.nvgActive ? 'ENGAGED' : 'DISENGAGED'}`, 'info');
                });
            }

            // Snapshot Button
            if (DOM.snapshotFeedBtn) {
                DOM.snapshotFeedBtn.addEventListener('click', () => {
                    playTacticalSound('shutter');
                    const focusedId = STATE.focusedCamId || 'CAM-01';
                    displayToast(`📸 Frame Snapshot Captured [${focusedId}] Saved to Forensic Vault`, 'info');
                });
            }

            // DVR Play/Pause
            if (DOM.dvrPlayPauseBtn) {
                DOM.dvrPlayPauseBtn.addEventListener('click', () => {
                    STATE.isPlaying = !STATE.isPlaying;
                    DOM.dvrPlayPauseBtn.classList.toggle('play-active', STATE.isPlaying);
                    if (DOM.syncStatusText) {
                        DOM.syncStatusText.textContent = STATE.isPlaying ? 'LIVE SYNC' : 'STREAM PAUSED';
                    }
                    playTacticalSound('click');
                    displayToast(`DVR Playback: ${STATE.isPlaying ? 'RESUMED' : 'PAUSED'}`, 'info');
                });
            }

            if (DOM.dvrRewindBtn) {
                DOM.dvrRewindBtn.addEventListener('click', () => {
                    playTacticalSound('click');
                    displayToast('DVR: Rewound 10s into forensic buffer', 'info');
                });
            }

            if (DOM.dvrFastForwardBtn) {
                DOM.dvrFastForwardBtn.addEventListener('click', () => {
                    playTacticalSound('click');
                    displayToast('DVR: Fast forwarded to live head', 'info');
                });
            }
        }

        function handlePTZPanTilt(camId, dir) {
            const cam = STATE.cameraStates[camId];
            if (!cam) return;
            const step = 15;
            if (dir === 'up') cam.tilt -= step;
            if (dir === 'down') cam.tilt += step;
            if (dir === 'left') cam.pan -= step;
            if (dir === 'right') cam.pan += step;
            displayToast(`PTZ Offset [${camId}]: Pan ${cam.pan}px / Tilt ${cam.tilt}px`, 'info');
        }

        function handlePTZZoom(camId, zoomType) {
            const cam = STATE.cameraStates[camId];
            if (!cam) return;
            if (zoomType === 'in') cam.zoom = Math.min(cam.zoom + 0.25, 2.5);
            if (zoomType === 'out') cam.zoom = Math.max(cam.zoom - 0.25, 0.75);
            displayToast(`PTZ Optical Zoom [${camId}]: ${cam.zoom.toFixed(2)}x`, 'info');
        }

        function toggleFeedFocus(feedBox, camId) {
            if (STATE.focusedCamId === camId) {
                STATE.focusedCamId = null;
                DOM.feedBoxes.forEach((box) => box.classList.remove('focused'));
                setGridMode('2x2');
                displayToast(`Camera Grid: Restored 4-Way Quad Matrix`, 'info');
            } else {
                STATE.focusedCamId = camId;
                DOM.feedBoxes.forEach((box) => box.classList.remove('focused'));
                feedBox.classList.add('focused');
                setGridMode('1x1');
                displayToast(`Camera Focused: [${camId}] // PTZ Controls Active`, 'info');
            }
        }

        function setGridMode(mode) {
            STATE.activeGrid = mode;
            if (!DOM.cctvGrid) return;

            if (mode === '1x1') {
                DOM.cctvGrid.classList.add('single-mode');
                if (DOM.gridModeLabel) DOM.gridModeLabel.textContent = 'SINGLE FOCUS (1x1 EXPANDED)';
                if (!STATE.focusedCamId) {
                    const firstCam = DOM.feedBoxes[0];
                    firstCam.classList.add('focused');
                    STATE.focusedCamId = firstCam.getAttribute('data-cam-id');
                }
            } else {
                DOM.cctvGrid.classList.remove('single-mode');
                if (DOM.gridModeLabel) DOM.gridModeLabel.textContent = 'QUAD MATRIX (4-WAY DYNAMIC)';
                DOM.feedBoxes.forEach((box) => box.classList.remove('focused'));
                STATE.focusedCamId = null;
            }

            DOM.gridToolBtns.forEach((btn) => {
                btn.classList.toggle('active', btn.getAttribute('data-grid') === mode);
            });
        }

        // =========================================================================
        // 8. TACTICAL MODALS & INCIDENT INTERCEPT DOSSIER
        // =========================================================================
        function initIncidentModal() {
            // Click on incident item
            document.querySelectorAll('.incident-item').forEach((item) => {
                item.addEventListener('click', () => {
                    const incId = item.getAttribute('data-incident-id') || 'INC-802';
                    openIncidentModal(incId);
                    playTacticalSound('alert');
                });
            });

            if (DOM.closeIncidentModalBtn) {
                DOM.closeIncidentModalBtn.addEventListener('click', closeIncidentModal);
            }
            if (DOM.incidentModalBackdrop) {
                DOM.incidentModalBackdrop.addEventListener('click', (e) => {
                    if (e.target === DOM.incidentModalBackdrop) closeIncidentModal();
                });
            }
            if (DOM.modalDismissBtn) {
                DOM.modalDismissBtn.addEventListener('click', () => {
                    closeIncidentModal();
                    displayToast('Threat Alert Acknowledged and Archived', 'info');
                    playTacticalSound('click');
                });
            }
            if (DOM.modalDispatchBtn) {
                DOM.modalDispatchBtn.addEventListener('click', () => {
                    closeIncidentModal();
                    displayToast('🚨 Sentinel Tactical Rapid Response Unit Dispatched to Sector!', 'info');
                    playTacticalSound('alert');
                });
            }
        }

        function openIncidentModal(incId) {
            const inc = STATE.incidents[incId] || STATE.incidents['INC-802'];
            if (!DOM.modalIncidentBody || !DOM.incidentModalBackdrop) return;

            DOM.modalIncidentTitle.textContent = `THREAT INTERCEPT // ${inc.id}`;
            DOM.modalIncidentBody.innerHTML = `
            <div class="diag-grid">
                <div class="diag-card">
                    <span class="diag-lbl">INCIDENT TYPE</span>
                    <span class="diag-val" style="color: var(--accent-red); font-size: 0.82rem;">${inc.type}</span>
                </div>
                <div class="diag-card">
                    <span class="diag-lbl">SEVERITY CLASSIFICATION</span>
                    <span class="diag-val"><span class="badge ${inc.badgeClass}">${inc.severity}</span></span>
                </div>
                <div class="diag-card">
                    <span class="diag-lbl">CAPTURED CAMERA NODE</span>
                    <span class="diag-val cyan-val">${inc.camera}</span>
                </div>
                <div class="diag-card">
                    <span class="diag-lbl">TIMESTAMP / CONFIDENCE</span>
                    <span class="diag-val green-val">${inc.confidence}</span>
                </div>
            </div>
            <div class="diag-card">
                <span class="diag-lbl">TACTICAL INTELLIGENCE SUMMARY</span>
                <p style="font-size: 0.78rem; line-height: 1.4; color: var(--text-secondary); margin-top: 4px;">${inc.desc}</p>
                <div style="margin-top: 8px; font-size: 0.65rem; color: var(--text-muted);">GPS: ${inc.coords}</div>
            </div>
        `;

            DOM.incidentModalBackdrop.classList.add('open');
        }

        function closeIncidentModal() {
            if (DOM.incidentModalBackdrop) {
                DOM.incidentModalBackdrop.classList.remove('open');
            }
        }

        // =========================================================================
        // 9. SYSTEM HEALTH DIAGNOSTICS MODAL
        // =========================================================================
        function initDiagnosticsModal() {
            if (DOM.systemHealthPill) {
                DOM.systemHealthPill.addEventListener('click', () => {
                    if (DOM.diagnosticsModalBackdrop) {
                        DOM.diagnosticsModalBackdrop.classList.add('open');
                        playTacticalSound('click');
                    }
                });
            }

            if (DOM.closeDiagModalBtn) {
                DOM.closeDiagModalBtn.addEventListener('click', () => {
                    DOM.diagnosticsModalBackdrop.classList.remove('open');
                });
            }
            if (DOM.closeDiagBtn) {
                DOM.closeDiagBtn.addEventListener('click', () => {
                    DOM.diagnosticsModalBackdrop.classList.remove('open');
                });
            }
            if (DOM.diagnosticsModalBackdrop) {
                DOM.diagnosticsModalBackdrop.addEventListener('click', (e) => {
                    if (e.target === DOM.diagnosticsModalBackdrop) {
                        DOM.diagnosticsModalBackdrop.classList.remove('open');
                    }
                });
            }
            if (DOM.runDiagBtn) {
                DOM.runDiagBtn.addEventListener('click', () => {
                    playTacticalSound('click');
                    displayToast('Diagnostic: Full Neural Integrity Scan Passed (128/128 Nodes Nominal)', 'info');
                });
            }
        }

        // =========================================================================
        // 10. PROFILE MENU & TACTICAL ACTIONS
        // =========================================================================
        function initProfileMenu() {
            if (DOM.operatorProfileBtn && DOM.profileDropdownMenu) {
                DOM.operatorProfileBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    DOM.profileDropdownMenu.classList.toggle('open');
                    playTacticalSound('click');
                });

                document.addEventListener('click', () => {
                    DOM.profileDropdownMenu.classList.remove('open');
                });
            }

            if (DOM.switchSectorBtn) {
                DOM.switchSectorBtn.addEventListener('click', () => {
                    if (DOM.activeSectorLabel) DOM.activeSectorLabel.textContent = 'SECTOR-04 REDUNDANT CONTROL';
                    displayToast('Switching active node routing to SECTOR-04', 'info');
                    playTacticalSound('click');
                });
            }

            if (DOM.testAlertTriggerBtn) {
                DOM.testAlertTriggerBtn.addEventListener('click', () => {
                    STATE.threatCount++;
                    if (DOM.threatCountStat) DOM.threatCountStat.innerHTML = `0${STATE.threatCount}<span class="stat-unit"> ACTIVE</span>`;
                    displayToast('⚠️ Simulated Alert Injected: Motion Detected Sector 07-D', 'info');
                    playTacticalSound('alert');
                });
            }

            if (DOM.exportAuditBtn) {
                DOM.exportAuditBtn.addEventListener('click', () => {
                    displayToast('Exporting encrypted forensic event log (.json.enc)...', 'info');
                    playTacticalSound('click');
                });
            }

            if (DOM.lockStationBtn) {
                DOM.lockStationBtn.addEventListener('click', () => {
                    displayToast('Console Lockdown Engaged. Enter Biometric Pin to Resume.', 'info');
                    playTacticalSound('alert');
                });
            }
        }

        // =========================================================================
        // 11. SEARCH & QUICK FILTER ENGINE
        // =========================================================================
        function initSearchEngine() {
            if (!DOM.cameraSearchInput) return;

            DOM.cameraSearchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase().trim();
                DOM.feedBoxes.forEach((box) => {
                    const text = box.textContent.toLowerCase();
                    const matches = text.includes(query);
                    box.style.display = matches ? '' : 'none';
                });
            });

            window.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                    e.preventDefault();
                    DOM.cameraSearchInput.focus();
                    DOM.cameraSearchInput.select();
                    playTacticalSound('click');
                }
            });
        }

        // =========================================================================
        // 12. TOAST NOTIFICATION SYSTEM
        // =========================================================================
        function displayToast(message, type = 'info') {
            if (!DOM.toastContainer) return;

            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
            <span class="sync-dot"></span>
            <span>${message}</span>
        `;

            DOM.toastContainer.appendChild(toast);

            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => toast.remove(), 300);
            }, 3200);
        }

        // Alert Bell Click Action
        if (DOM.alertBellBtn) {
            DOM.alertBellBtn.addEventListener('click', () => {
                openIncidentModal('INC-802');
                playTacticalSound('alert');
            });
        }

        // =========================================================================
        // 13. BACKEND API INTEGRATION & REAL-TIME SYNC
        // =========================================================================
        async function fetchBackendHealth() {
            try {
                const response = await fetch(`${API_BASE_URL}/health`, { method: 'GET', headers: { 'Accept': 'application/json' } });
                if (response.ok) {
                    const healthData = await response.json();
                    STATE.backendConnected = true;
                    if (DOM.activeSectorLabel) {
                        DOM.activeSectorLabel.innerHTML = `BACKEND ONLINE // ${healthData.environment ? healthData.environment.toUpperCase() : 'PRODUCTION'}`;
                    }
                    return healthData;
                }
            } catch (err) {
                // Backend unreachable
            }
            STATE.backendConnected = false;
            return null;
        }

        async function fetchCameraCoverage() {
            try {
                const response = await fetch(`${API_BASE_URL}/cameras/coverage`, { method: 'GET', headers: { 'Accept': 'application/json' } });
                if (response.ok) {
                    const res = await response.json();
                    if (res.success && res.data) {
                        const total = res.data.total_cameras || 128;
                        const active = res.data.operational_cameras || total;
                        const statNum = document.querySelector('.stat-card:first-child .stat-number');
                        if (statNum) {
                            statNum.innerHTML = `${active}<span class="stat-unit">/${total}</span>`;
                        }
                    }
                }
            } catch (e) {
                // Ignore fallback to defaults
            }
        }

        async function initBackendSync() {
            const health = await fetchBackendHealth();
            if (health) {
                displayToast(`⚡ Backend Connected: FastAPI v${health.version || '1.0'} [${health.environment || 'DEV'}]`, 'info');
                await fetchCameraCoverage();
            } else {
                console.info('[PHANTOM] FastAPI Backend not detected at ' + API_BASE_URL + '. Running in Autonomous Tactical Simulation Mode.');
            }

            // Periodic sync check every 20 seconds
            setInterval(async () => {
                const h = await fetchBackendHealth();
                if (h && !STATE.backendConnected) {
                    STATE.backendConnected = true;
                    displayToast('⚡ FastAPI Backend Connection Restored', 'info');
                    await fetchCameraCoverage();
                }
            }, 20000);
        }

        // =========================================================================
        // 14. PLATFORM INITIALIZATION
        // =========================================================================
        function initPlatform() {
            initThemeSystem();
            initTacticalClock();
            initSidebarControls();
            initCameraFeeds();
            initCameraGridInteractions();
            initIncidentModal();
            initDiagnosticsModal();
            initProfileMenu();
            initAudioToggle();
            initSearchEngine();
            initBackendSync();

            console.log('%c[PHANTOM]%c CCTV Neural Intelligence Platform Initialized // Status: NOMINAL', 'color: #00f0ff; font-weight: bold;', 'color: #00ff88;');
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initPlatform);
        } else {
            initPlatform();
        }
    })();