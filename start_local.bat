@echo off
echo ========================================
echo PDF Research Summarizer - Local Setup
echo ========================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Please follow these steps:
    echo 1. Copy .env.example to .env
    echo 2. Edit .env and add your GEMINI_API_KEY
    echo 3. Get your API key from: https://makersuite.google.com/app/apikey
    echo.
    pause
    exit /b 1
)

REM Check if backend dependencies are installed
echo Checking backend dependencies...
cd backend
python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo Installing backend dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install backend dependencies
        pause
        exit /b 1
    )
)

REM Check if frontend dependencies are installed
echo Checking frontend dependencies...
cd ../frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

cd ..

REM Test backend configuration
echo Testing backend configuration...
cd backend
python -c "from config import validate_startup_config; result = validate_startup_config(); print('✓ Backend configuration valid' if result['status'] == 'success' else f'✗ Configuration error: {result[\"message\"]}')"
if errorlevel 1 (
    echo ERROR: Backend configuration test failed
    echo Please check your .env file and ensure GEMINI_API_KEY is set
    pause
    exit /b 1
)
cd ..

echo.
echo ========================================
echo Starting Services...
echo ========================================

REM Start backend in new window
echo Starting FastAPI Backend...
start "PDF Summarizer Backend" cmd /k "cd /d "%CD%\backend" && echo Starting backend server... && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Start frontend in new window
echo Starting React Frontend...
start "PDF Summarizer Frontend" cmd /k "cd /d "%CD%\frontend" && echo Starting frontend development server... && npm run dev"

echo.
echo ========================================
echo PDF Research Summarizer is starting...
echo ========================================
echo.
echo Frontend URL: http://127.0.0.1:5173
echo Backend API:  http://127.0.0.1:8000
echo API Docs:     http://127.0.0.1:8000/docs
echo Health Check: http://127.0.0.1:8000/api/health
echo.
echo ========================================
echo.
echo Both services are starting in separate windows.
echo Wait a few seconds, then open: http://127.0.0.1:5173
echo.
echo To stop the services, close both terminal windows.
echo.
pause