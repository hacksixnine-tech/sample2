# ==============================================================================
# PHANTOM // Restart Platform Services
# ==============================================================================

Write-Host "Restarting PHANTOM services..." -ForegroundColor Cyan

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    docker info > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        docker compose restart
        Write-Host "PHANTOM containers restarted successfully." -ForegroundColor Green
        exit 0
    }
}

Write-Host "Docker daemon not active. Please restart local services manually." -ForegroundColor Yellow
