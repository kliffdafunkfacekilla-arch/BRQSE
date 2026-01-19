@echo off
title BRQSE Arena Launcher
color 0A

echo ==========================================
echo        BRQSE ARENA SYSTEM LAUNCHER
echo ==========================================
echo.

echo [1/3] Generating Fresh Combat Replay...
python generate_replay.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to generate replay data.
    pause
    exit /b
)
echo [SUCCESS] Replay packet generated.

echo.
echo [2/3] Opening Arena Viewer...
start http://localhost:3000/arena

echo.
echo [3/3] Starting Web Server...
echo (Press Ctrl+C to stop)
echo.
cd web-character-creator
npm run dev
