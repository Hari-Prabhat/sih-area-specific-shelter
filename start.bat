@echo off
echo ===================================================
echo   THERMOSHELTER AI - Starting Engineering Platform
echo ===================================================
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "ThermoShelter Backend API" cmd /k "python -m uvicorn api:app --port 8000 --host 127.0.0.1"
timeout /t 2 >nul
echo [2/2] Starting React + TypeScript Frontend on http://localhost:5173 ...
cd frontend
npm.cmd run dev
