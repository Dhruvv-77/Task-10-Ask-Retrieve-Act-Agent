# ==============================================================================
# Graceful Clean Shutdown for "Ask, Retrieve, Act" Capstone
# ==============================================================================

$RootPath = "c:\Users\dhruv\Desktop\task 10"
Set-Location $RootPath

Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host "   Stopping All Services for 'Ask, Retrieve, Act'..." -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Yellow

# 1. Stop Docker Containers
Write-Host "[1/3] Stopping Docker containers (PostgreSQL & Redis)..." -ForegroundColor Gray
docker compose down

# 2. Stop Python & Node Processes
Write-Host "[2/3] Stopping Python backend & Node web processes..." -ForegroundColor Gray
Get-Process -Name "python", "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# 3. Stop Ollama
Write-Host "[3/3] Stopping Ollama server..." -ForegroundColor Gray
Get-Process -Name "*ollama*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "==================================================================" -ForegroundColor Green
Write-Host "   All processes stopped cleanly. Ports and memory released." -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
