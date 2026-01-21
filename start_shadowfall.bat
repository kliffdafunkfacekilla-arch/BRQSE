@echo off
title Shadowfall Launcher
color 0B

echo ==========================================
echo      SHADOWFALL CHRONICLES (VITE)
echo ==========================================
echo.

echo [1/3] Generating Battle Data...
python scripts/generate_replay.py
echo Data Packet Generated.

echo.
echo [2/3] Installing Dependencies (First Run Only)...
cd Web_ui
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] npm install had issues. Trying to proceed anyway...
)

echo.
echo [3/3] Opening Dashboard...
start http://localhost:5173

echo.

echo [3/4] Starting Backend Server...
start "BRQSE API" python scripts/simple_api.py
timeout /t 2 >nul

echo.
echo [4/4] Starting Frontend...
echo (Press Ctrl+C to stop)
npm run dev
