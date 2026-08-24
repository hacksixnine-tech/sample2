# ==============================================================================
# PHANTOM // Safe Reset Script
# ==============================================================================

Write-Host "Resetting PHANTOM containers and cache..." -ForegroundColor Yellow

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    docker info > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        docker compose down -v
        Write-Host "Cleaned up Docker volumes." -ForegroundColor Green
        docker compose up --build -d
        Write-Host "Rebuilt and started fresh containers." -ForegroundColor Green
        exit 0
    }
}

if (Test-Path "backend\var\hls_cache") {
    Remove-Item -Recurse -Force "backend\var\hls_cache\*" -ErrorAction SilentlyContinue
    Write-Host "Cleared local HLS stream cache." -ForegroundColor Green
}

Write-Host "Reset complete." -ForegroundColor Green
