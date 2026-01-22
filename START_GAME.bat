@echo off
title Shadowfall Chronicles Launcher
color 0A

echo ============================================
echo    SHADOWFALL CHRONICLES - DEV LAUNCHER
echo ============================================
echo.

REM Set the project root
set PROJECT_ROOT=%~dp0

echo [1/2] Starting Backend API (Port 5001)...
start "BRQSE Backend" cmd /k "cd /d %PROJECT_ROOT% && python scripts/simple_api.py"

echo [2/2] Starting Frontend (Port 5173)...
timeout /t 2 >nul
start "BRQSE Frontend" cmd /k "cd /d %PROJECT_ROOT%Web_ui && npm run dev"

echo.
echo ============================================
echo  SERVERS STARTING...
echo  
echo  Backend:  http://localhost:5001
echo  Frontend: http://localhost:5173
echo ============================================
echo.

timeout /t 3 >nul
start http://localhost:5173

echo Press any key to close this launcher window...
pause >nul
