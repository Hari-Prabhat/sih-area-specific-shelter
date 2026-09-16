# =============================================================================
# THERMOSHELTER - Development Launcher
# =============================================================================
# Starts the two-process development architecture in separate windows:
#
#   Terminal 1: FastAPI backend   -> python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
#   Terminal 2: Vite frontend     -> npm run dev (thermoshelter-design-studio, port 5173)
#
# Pre-flight port checks warn clearly if 8000/5173 are already occupied so a
# half-running stack is never silently assumed. The frontend reaches the API
# through the Vite proxy (/api -> http://127.0.0.1:8000) configured in
# thermoshelter-design-studio/vite.config.js.
#
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\start-dev.ps1
# =============================================================================

$ErrorActionPreference = 'Stop'

$repoRoot    = Split-Path -Parent $PSScriptRoot
$studioDir   = Join-Path $repoRoot 'thermoshelter-design-studio'
$backendUrl  = 'http://127.0.0.1:8000'
$frontendUrl = 'http://localhost:5173'
$docsUrl     = "$backendUrl/docs"

function Test-PortInUse {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return ($null -ne $conn)
}

Write-Host ''
Write-Host '=== THERMOSHELTER dev launcher ===' -ForegroundColor Cyan
Write-Host "Repository : $repoRoot"

# --- Pre-flight checks -------------------------------------------------------
$backendBusy = Test-PortInUse -Port 8000
$frontendBusy = Test-PortInUse -Port 5173

if ($backendBusy) {
    Write-Host '[WARN] Port 8000 is ALREADY IN USE - backend NOT started.' -ForegroundColor Yellow
    Write-Host '       An existing FastAPI/uvicorn process may already be serving the API.' -ForegroundColor Yellow
} else {
    Write-Host '[OK]   Port 8000 free - will start FastAPI backend.' -ForegroundColor Green
}

if ($frontendBusy) {
    Write-Host '[WARN] Port 5173 is ALREADY IN USE - frontend NOT started.' -ForegroundColor Yellow
    Write-Host '       An existing Vite dev server is likely already running.' -ForegroundColor Yellow
} else {
    Write-Host '[OK]   Port 5173 free - will start Vite frontend.' -ForegroundColor Green
}

# --- Launch backend ----------------------------------------------------------
if (-not $backendBusy) {
    Start-Process -FilePath 'powershell' -ArgumentList @(
        '-NoExit', '-Command',
        "Set-Location '$repoRoot'; Write-Host 'THERMOSHELTER FastAPI backend' -ForegroundColor Cyan; python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
    ) | Out-Null
    Write-Host '[START] FastAPI backend launching in a new window...' -ForegroundColor Green
}

# --- Launch frontend ---------------------------------------------------------
if (-not $frontendBusy) {
    if (-not (Test-Path (Join-Path $studioDir 'node_modules'))) {
        Write-Host '[WARN] node_modules missing - running npm install first...' -ForegroundColor Yellow
        Push-Location $studioDir
        npm install
        Pop-Location
    }
    Start-Process -FilePath 'powershell' -ArgumentList @(
        '-NoExit', '-Command',
        "Set-Location '$studioDir'; Write-Host 'THERMOSHELTER Vite frontend' -ForegroundColor Cyan; npm run dev"
    ) | Out-Null
    Write-Host '[START] Vite frontend launching in a new window...' -ForegroundColor Green
}

# --- Summary -----------------------------------------------------------------
Write-Host ''
Write-Host '=== URLs ===' -ForegroundColor Cyan
Write-Host "  Frontend (React/Vite) : $frontendUrl"
Write-Host "  Backend  (FastAPI)    : $backendUrl"
Write-Host "  API docs (Swagger)    : $docsUrl"
Write-Host '  Health check          : GET  http://127.0.0.1:8000/api/health'
Write-Host '  Simulation            : POST http://127.0.0.1:8000/api/simulation/run'
Write-Host ''
if ($backendBusy -or $frontendBusy) {
    Write-Host 'One or both ports were busy - resolve the conflicts above, then re-run.' -ForegroundColor Yellow
} else {
    Write-Host 'Both processes are starting. Open the frontend URL in your browser.' -ForegroundColor Green
}
