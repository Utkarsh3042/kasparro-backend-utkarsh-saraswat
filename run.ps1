# Crypto ETL Backend - PowerShell Management Script

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "`n╔════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   Crypto ETL Backend - Commands           ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  .\run.ps1 up        " -NoNewline
    Write-Host "- Start all services" -ForegroundColor Green
    Write-Host "  .\run.ps1 down      " -NoNewline
    Write-Host "- Stop all services" -ForegroundColor Yellow
    Write-Host "  .\run.ps1 build     " -NoNewline
    Write-Host "- Build Docker images" -ForegroundColor Blue
    Write-Host "  .\run.ps1 logs      " -NoNewline
    Write-Host "- View logs" -ForegroundColor Cyan
    Write-Host "  .\run.ps1 test      " -NoNewline
    Write-Host "- Run tests" -ForegroundColor Magenta
    Write-Host "  .\run.ps1 clean     " -NoNewline
    Write-Host "- Clean up containers" -ForegroundColor Red
    Write-Host "  .\run.ps1 restart   " -NoNewline
    Write-Host "- Restart all services" -ForegroundColor DarkGreen
    Write-Host "  .\run.ps1 status    " -NoNewline
    Write-Host "- Show service status" -ForegroundColor DarkCyan
    Write-Host ""
}

function Start-Services {
    Write-Host "🚀 Starting services..." -ForegroundColor Green
    docker-compose up -d
    Write-Host "✅ Services started!" -ForegroundColor Green
    Write-Host "📍 API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📖 Docs: http://localhost:8000/docs" -ForegroundColor Cyan
}

function Stop-Services {
    Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Services stopped!" -ForegroundColor Green
}

function Build-Images {
    Write-Host "🔨 Building Docker images..." -ForegroundColor Blue
    docker-compose build
    Write-Host "✅ Build completed!" -ForegroundColor Green
}

function Show-Logs {
    Write-Host "📋 Showing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    docker-compose logs -f
}

function Run-Tests {
    Write-Host "🧪 Running tests..." -ForegroundColor Magenta
    docker-compose run --rm backend pytest -v
}

function Clean-Up {
    Write-Host "🧹 Cleaning up containers and volumes..." -ForegroundColor Red
    docker-compose down -v
    docker system prune -f
    Write-Host "✅ Cleanup completed!" -ForegroundColor Green
}

function Restart-Services {
    Write-Host "🔄 Restarting services..." -ForegroundColor DarkGreen
    docker-compose down
    docker-compose up -d
    Write-Host "✅ Services restarted!" -ForegroundColor Green
}

function Show-Status {
    Write-Host "📊 Service Status:" -ForegroundColor DarkCyan
    docker-compose ps
}

# Main execution
switch ($Command.ToLower()) {
    "up" { Start-Services }
    "down" { Stop-Services }
    "build" { Build-Images }
    "logs" { Show-Logs }
    "test" { Run-Tests }
    "clean" { Clean-Up }
    "restart" { Restart-Services }
    "status" { Show-Status }
    default { Show-Help }
}
