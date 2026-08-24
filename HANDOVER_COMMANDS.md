# PHANTOM // Group Member Handover & Run Guide 🚀

Yeh guide aapke group members ke liye banayi gayi hai taaki woh project ko **1 command me clone karke bina kisi issue ke run kar sakein**, aur CCTV streams / automated gateway turant play hone lagein.

---

## 📌 STEP 1: Push To GitHub (Admin / Developer)
Repository remote pehle se set hai: `https://github.com/lvhinguroot-08/PHANTOM-FINAL.git`

Terminal me bas yeh command run karein:
```bash
git push -u origin main
```
*(Agar GitHub login pop-up aaye to Browser sign-in ya Personal Access Token select karein).*

---

## 📌 STEP 2: Group Member Machine Setup (Clone & Run)

Aapke group member ko bas **Docker Desktop** open rakhna hai aur yeh commands run karni hain:

### Option A: 1-Click Windows Batch Run (Sabse Simple)
```cmd
# 1. Clone repo
git clone https://github.com/lvhinguroot-08/PHANTOM-FINAL.git
cd PHANTOM-FINAL

# 2. 1-Click Setup & Launch
setup.bat
```

### Option B: PowerShell Run
```powershell
# 1. Clone repo
git clone https://github.com/lvhinguroot-08/PHANTOM-FINAL.git
cd PHANTOM-FINAL

# 2. Run automated setup script
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

---

## 🌐 Live URLs & Access Endpoints

Once setup completes, sabhi services automatically online ho jaayengi:

| Interface | URL | Description |
| :--- | :--- | :--- |
| **🖥️ Frontend Command Center** | [http://localhost:3000](http://localhost:3000) | Live 30-Camera Video Wall, GIS Map, ANPR & Alerts |
| **📑 Backend OpenAPI Docs** | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | Interactive Swagger REST API Explorer |
| **❤️ System Health Probe** | [http://localhost:8000/health/live](http://localhost:8000/health/live) | Container Liveness & Database Check |
| **🎥 CCTV Stream Gateway** | [http://localhost:8000/api/v1/streams/CAM-001/live.m3u8](http://localhost:8000/api/v1/streams/CAM-001/live.m3u8) | Low-Latency Transcoded Live HLS Stream |

---

## 🎥 CCTV Stream & Automated Gateway Tunnel Details

1. **Automatic Stream Fallback & Proxying**:
   - Backend ke andar built-in **Stream Gateway Engine** hai jo RTSP, HLS, aur Corp8 feeds ko automatically ingest aur transcode karta hai.
   - Agar koi camera feed external network/VPN issues ki wajah se unreachable ho, to system **automatically live 25 FPS synthetic test stream** generate karta hai real-time timestamp ke saath.
   - Isse video player kabhi blank ya crash nahi hota aur 100% full-frame playback chalta rehta hai.

2. **Aspect Ratio & Framing Control**:
   - Har camera card par **`[FIT (100%)]`** button diya gaya hai jisse 100% uncropped frame (edges, timestamps, road lanes) visible rehte hain.

---

## 🛠️ Daily Maintenance Commands List

| Action | Windows Batch | PowerShell |
| :--- | :--- | :--- |
| **Start Project** | `start.bat` | `powershell -ExecutionPolicy Bypass -File .\start.ps1` |
| **Stop Project** | `stop.bat` | `powershell -ExecutionPolicy Bypass -File .\stop.ps1` |
| **Restart Project** | `restart.bat` | `powershell -ExecutionPolicy Bypass -File .\restart.ps1` |
| **Health Diagnostic** | - | `powershell -ExecutionPolicy Bypass -File .\health.ps1` |
| **Reset Cache/DB** | - | `powershell -ExecutionPolicy Bypass -File .\reset.ps1` |
