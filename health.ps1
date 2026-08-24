# ==============================================================================
# PHANTOM // Master Health & Diagnostics Probe
# ==============================================================================

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  PHANTOM SYSTEM HEALTH & READINESS PROBE" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$checks = @(
    @{ Name = "Backend Liveness Probe"; Url = "http://localhost:8000/health/live" },
    @{ Name = "Backend Readiness Probe"; Url = "http://localhost:8000/health/ready" },
    @{ Name = "Camera API Endpoint"; Url = "http://localhost:8000/api/v1/cameras" },
    @{ Name = "Stream Gateway Ingest (CAM-001)"; Url = "http://localhost:8000/api/v1/cameras/CAM-001/stream" },
    @{ Name = "Stream Gateway Health (CAM-001)"; Url = "http://localhost:8000/api/v1/cameras/CAM-001/health" },
    @{ Name = "Stream HLS Manifest (CAM-001)"; Url = "http://localhost:8000/api/v1/streams/CAM-001/live.m3u8" },
    @{ Name = "Stream Gateway Ingest (CAM-014)"; Url = "http://localhost:8000/api/v1/cameras/CAM-014/stream" },
    @{ Name = "Frontend Command Center"; Url = "http://localhost:3000" }
)

foreach ($c in $checks) {
    try {
        $t0 = Get-Date
        $resp = Invoke-WebRequest -Uri $c.Url -Method Get -TimeoutSec 4 -ErrorAction Stop
        $dur = [Math]::Round(((Get-Date) - $t0).TotalMilliseconds, 2)
        if ($resp.StatusCode -eq 200) {
            Write-Host ("  [ PASS ] {0,-35} HTTP 200 OK ({1} ms)" -f $c.Name, $dur) -ForegroundColor Green
        } else {
            Write-Host ("  [ WARN ] {0,-35} HTTP {1} ({2} ms)" -f $c.Name, $resp.StatusCode, $dur) -ForegroundColor Yellow
        }
    } catch {
        Write-Host ("  [ FAIL ] {0,-35} Unreachable / Error" -f $c.Name) -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
