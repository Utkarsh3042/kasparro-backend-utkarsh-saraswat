# Helper script for testing API

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$baseUrl = "http://localhost:8000"

function Show-Help {
    Write-Host "Crypto ETL API Test Commands:" -ForegroundColor Cyan
    Write-Host "  .\test.ps1 health              - Check API health"
    Write-Host "  .\test.ps1 ingest-cg [limit]   - Ingest from CoinGecko (default: 50)"
    Write-Host "  .\test.ps1 ingest-cp [limit]   - Ingest from CoinPaprika (default: 30)"
    Write-Host "  .\test.ps1 ingest-all          - Ingest from both sources"
    Write-Host "  .\test.ps1 data [page] [size]  - Get data (default: page=1, size=10)"
    Write-Host "  .\test.ps1 stats               - Get statistics"
    Write-Host "  .\test.ps1 clear               - Clear all data"
}

function Test-Health {
    Write-Host "Checking API health..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "$baseUrl/health" -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
}

function Ingest-CoinGecko {
    param([int]$limit = 50)
    Write-Host "Ingesting from CoinGecko (limit=$limit)..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/ingest/coingecko?limit=$limit" -Method POST -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json
}

function Ingest-CoinPaprika {
    param([int]$limit = 30)
    Write-Host "Ingesting from CoinPaprika (limit=$limit)..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/ingest/coinpaprika?limit=$limit" -Method POST -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json
}

function Ingest-All {
    Write-Host "Ingesting from all sources..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/ingest/all" -Method POST -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
}

function Get-Data {
    param([int]$page = 1, [int]$size = 10)
    Write-Host "Getting data (page=$page, size=$size)..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/data?page=$page&page_size=$size" -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
}

function Get-Stats {
    Write-Host "Getting statistics..." -ForegroundColor Yellow
    $response = Invoke-WebRequest -Uri "$baseUrl/api/v1/stats" -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
}

# Main execution
switch ($Command.ToLower()) {
    "health" { Test-Health }
    "ingest-cg" { Ingest-CoinGecko -limit $(if ($args[0]) { [int]$args[0] } else { 50 }) }
    "ingest-cp" { Ingest-CoinPaprika -limit $(if ($args[0]) { [int]$args[0] } else { 30 }) }
    "ingest-all" { Ingest-All }
    "data" { Get-Data -page $(if ($args[0]) { [int]$args[0] } else { 1 }) -size $(if ($args[1]) { [int]$args[1] } else { 10 }) }
    "stats" { Get-Stats }
    default { Show-Help }
}