# ==============================================================================
# PHANTOM // Stop Platform Services
# ==============================================================================

Write-Host "Stopping PHANTOM services..." -ForegroundColor Cyan

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    docker info > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        docker compose stop
        Write-Host "PHANTOM containers stopped." -ForegroundColor Green
        exit 0
    }
}

Write-Host "No active docker containers found to stop." -ForegroundColor Gray
