@echo off
REM Start Flask development server with proper configuration

setlocal enabledelayedexpansion

echo.
echo ====================================
echo   AI Assistant - Flask Dev Server
echo ====================================
echo.

REM Set Flask environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

echo [OK] FLASK_APP=%FLASK_APP%
echo [OK] FLASK_ENV=%FLASK_ENV%
echo [OK] FLASK_DEBUG=%FLASK_DEBUG%
echo.

REM Clear Python cache
echo [INFO] Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo [OK] Cache cleared
echo.

echo [INFO] Starting Flask server...
echo [INFO] Server running at http://127.0.0.1:8080
echo [INFO] Press Ctrl+C to stop
echo.

flask run --host=0.0.0.0 --port=8080

pause
