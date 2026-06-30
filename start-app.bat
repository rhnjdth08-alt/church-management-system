@echo off
REM ============================================================
REM  Church Management System - one-click launcher
REM  Double-click this file to start the app and open it in
REM  your browser. Close this window (or press Ctrl+C) to stop.
REM ============================================================

setlocal
set PYTHON=C:\Users\Onwa\AppData\Local\Python\pythoncore-3.14-64\python.exe
set HOST=127.0.0.1
set PORT=8000

cd /d "%~dp0backend"

echo.
echo  Starting Church Management System...
echo  When it says "Application startup complete", your browser will open.
echo  Leave this window open while you use the app. Close it to stop the server.
echo.

REM Open the browser a few seconds after the server begins starting.
start "" cmd /c "timeout /t 3 >nul & start http://%HOST%:%PORT%/"

REM Start the server (this blocks until you close the window / Ctrl+C).
"%PYTHON%" -m uvicorn app.main:app --host %HOST% --port %PORT%

echo.
echo  Server stopped.
pause
