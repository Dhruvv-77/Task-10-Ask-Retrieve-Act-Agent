# ==============================================================================
# One-Click Master Launcher for "Ask, Retrieve, Act" Capstone
# Powered by Local Ollama (qwen2.5:7b-instruct)
# ==============================================================================

$RootPath = "c:\Users\dhruv\Desktop\task 10"
Set-Location $RootPath

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "   Starting 'Ask, Retrieve, Act' AI Agent Architecture" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Start Docker Infrastructure (Postgres & Redis)
Write-Host "[1/5] Starting PostgreSQL and Redis containers..." -ForegroundColor Yellow
docker compose up -d

# 2. Check / Start Ollama
Write-Host "[2/5] Checking Ollama daemon..." -ForegroundColor Yellow
$ollamaProc = Get-Process -Name "*ollama*" -ErrorAction SilentlyContinue
if (-not $ollamaProc) {
    Write-Host "Starting Ollama daemon in background..." -ForegroundColor Gray
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
} else {
    Write-Host "Ollama is already running." -ForegroundColor Green
}

# 3. Start MCP Tool Server (Port 9000)
Write-Host "[3/5] Starting MCP Server (Port 9000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootPath'; Write-Host '--- MCP Server (Port 9000) ---' -ForegroundColor Cyan; python mcp-server/server.py"

# 4. Start FastAPI Agent Backend (Port 8000)
Write-Host "[4/5] Starting FastAPI Backend (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootPath\apps\api'; Write-Host '--- FastAPI Backend (Port 8000) ---' -ForegroundColor Cyan; python -m uvicorn main:app --host 0.0.0.0 --port 8000"

# 5. Start Next.js Web UI (Port 3000)
Write-Host "[5/5] Starting Next.js Web UI (Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootPath\apps\web'; Write-Host '--- Next.js Web UI (Port 3000) ---' -ForegroundColor Cyan; npm run dev"

Start-Sleep -Seconds 4
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "   All Services Launched Successfully!" -ForegroundColor Green
Write-Host "   Web UI: http://localhost:3000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   MCP Health: http://localhost:9000/health" -ForegroundColor White
Write-Host "==================================================================" -ForegroundColor Green

# Open browser automatically
Start-Process "http://localhost:3000"
