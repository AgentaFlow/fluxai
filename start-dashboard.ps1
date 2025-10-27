#!/usr/bin/env powershell
# FluxAI Observability Dashboard Launcher

Write-Host "🚀 Starting FluxAI Observability Dashboard..." -ForegroundColor Cyan

# Check if Streamlit is installed
$streamlit = Get-Command streamlit -ErrorAction SilentlyContinue
if (-not $streamlit) {
    Write-Host "❌ Streamlit is not installed. Installing..." -ForegroundColor Red
    pip install streamlit plotly pandas sqlalchemy requests
}

# Check if Prometheus is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Prometheus is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Warning: Prometheus not reachable at http://localhost:9090" -ForegroundColor Yellow
    Write-Host "   Dashboard will have limited functionality without Prometheus" -ForegroundColor Yellow
}

# Check if PostgreSQL is running
try {
    $env:PGPASSWORD = "dev_password"
    $pgCheck = psql -U fluxai -h localhost -d fluxai -c "SELECT 1" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL is running" -ForegroundColor Green
    } else {
        throw "PostgreSQL not accessible"
    }
} catch {
    Write-Host "⚠️  Warning: PostgreSQL not reachable" -ForegroundColor Yellow
    Write-Host "   Historical data queries will not work" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 Dashboard Configuration:" -ForegroundColor Cyan
Write-Host "   Prometheus: $env:PROMETHEUS_URL" -ForegroundColor Gray
Write-Host "   Database:   $env:DATABASE_URL" -ForegroundColor Gray
Write-Host ""

# Start Streamlit
Write-Host "🌐 Starting dashboard at http://localhost:8501" -ForegroundColor Green
Write-Host ""
streamlit run dashboard/app.py
