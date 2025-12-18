@echo off
echo ========================================
echo PDF Research Summarizer - Production
echo ========================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure for production
    pause
    exit /b 1
)

REM Set production environment
set ENVIRONMENT=production
set LOG_TO_FILE=true

echo Building frontend for production...
cd frontend
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed
    pause
    exit /b 1
)

echo.
echo Starting production server...
cd ../backend

REM Start with production settings
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

pause