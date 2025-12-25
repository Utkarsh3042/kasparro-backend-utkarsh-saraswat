Write-Host "`n=== Diagnostic Check ===" -ForegroundColor Cyan

# Check if Docker containers are running
Write-Host "`n[1] Checking Docker containers..." -ForegroundColor Yellow
docker ps --filter "name=crypto-etl" --format "table {{.Names}}\t{{.Status}}"

# Check if CSV file exists
Write-Host "`n[2] Checking CSV file..." -ForegroundColor Yellow
if (Test-Path "data\crypto_data.csv") {
    Write-Host "  ✓ CSV file exists" -ForegroundColor Green
    Write-Host "  Rows: $((Get-Content data\crypto_data.csv | Measure-Object -Line).Lines)" -ForegroundColor Cyan
} else {
    Write-Host "  ✗ CSV file NOT found" -ForegroundColor Red
    Write-Host "  → Run: python scripts\generate_sample_csv.py" -ForegroundColor Yellow
}

# Check if API is responding
Write-Host "`n[3] Checking API health..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 | ConvertFrom-Json
    Write-Host "  ✓ API is running" -ForegroundColor Green
    Write-Host "  Version: $($health.version)" -ForegroundColor Cyan
} catch {
    Write-Host "  ✗ API not responding" -ForegroundColor Red
    Write-Host "  → Check: docker-compose logs backend" -ForegroundColor Yellow
}

# Check available endpoints
Write-Host "`n[4] Checking endpoints..." -ForegroundColor Yellow
try {
    $openapi = Invoke-WebRequest -Uri "http://localhost:8000/openapi.json" -UseBasicParsing | ConvertFrom-Json
    
    if ($openapi.paths.'/api/v1/ingest/csv') {
        Write-Host "  ✓ CSV endpoint available" -ForegroundColor Green
    } else {
        Write-Host "  ✗ CSV endpoint NOT found" -ForegroundColor Red
        Write-Host "  → Rebuild required: .\run.ps1 down && docker-compose build --no-cache && .\run.ps1 up" -ForegroundColor Yellow
    }
    
    Write-Host "`n  Available POST endpoints:" -ForegroundColor Cyan
    $openapi.paths.PSObject.Properties | Where-Object { $_.Value.post } | ForEach-Object {
        Write-Host "    • $($_.Name)" -ForegroundColor White
    }
} catch {
    Write-Host "  ✗ Cannot fetch API schema" -ForegroundColor Red
}

# Check database
Write-Host "`n[5] Checking database..." -ForegroundColor Yellow
try {
    $dbCheck = docker exec crypto-etl-db psql -U crypto_user -d crypto_etl -c "SELECT COUNT(*) FROM cryptocurrencies;" 2>&1
    if ($dbCheck -match "count") {
        Write-Host "  ✓ Database is accessible" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Database error" -ForegroundColor Red
        Write-Host "  → Check: docker-compose logs postgres" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Cannot connect to database" -ForegroundColor Red
}

Write-Host "`n=== Diagnostic Complete ===" -ForegroundColor Cyan