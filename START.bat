@echo off
title Marsh Pitch Generator — Starting...
color 0F
cls

echo.
echo  ============================================================
echo    Marsh  /  AI Pitch Generator
echo    NMIMS 2026  ^|  Multi-Agent System
echo  ============================================================
echo.

:: ── Step 1: Check Python ──────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo.
    echo  Please install Python 3.10+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER% found
echo.

:: ── Step 2: Create virtual environment if missing ─────────────────────
if not exist "venv\Scripts\activate.bat" (
    echo  [SETUP] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created
    echo.
)

:: ── Step 3: Activate venv ─────────────────────────────────────────────
call venv\Scripts\activate.bat

:: ── Step 4: Install / update dependencies ─────────────────────────────
echo  [SETUP] Checking dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    echo  Try running: pip install -r requirements.txt
    pause
    exit /b 1
)
echo  [OK] All dependencies ready
echo.

:: ── Step 5: Check .env file ───────────────────────────────────────────
if not exist ".env" (
    echo  [WARN] No .env file found!
    echo.
    echo  Please copy .env.example to .env and add your API keys.
    echo  You can get a free key from: https://console.groq.com
    echo.
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo  [INFO] Created .env from .env.example — please open it and add your keys.
        echo.
        notepad .env
    )
    pause
    exit /b 1
)
echo  [OK] .env file found
echo.

:: ── Step 6: Open browser after 2 seconds ─────────────────────────────
echo  [INFO] Starting server at http://localhost:5000
echo  [INFO] Browser will open automatically...
echo.
echo  Press Ctrl+C to stop the server.
echo  ============================================================
echo.

:: Open browser in background after short delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

:: ── Step 7: Start the Flask server ───────────────────────────────────
python -m app.server

:: If server exits, pause so user can see any error
echo.
echo  Server stopped. Press any key to close.
pause >nul
