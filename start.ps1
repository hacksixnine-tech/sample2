# ==============================================================================
# PHANTOM // Start Platform Services
# ==============================================================================

Write-Host "Starting PHANTOM services..." -ForegroundColor Cyan

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    docker info > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        docker compose up -d
        Write-Host "PHANTOM containers started." -ForegroundColor Green
        exit 0
    }
}

Write-Host "Docker daemon not running. Please start Docker Desktop or run via python/npm." -ForegroundColor Yellow
