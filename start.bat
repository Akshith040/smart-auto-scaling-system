@echo off
REM Smart Auto-Scaling System Startup Script for Windows

echo ================================================
echo    Smart Auto-Scaling System - Setup
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✅ pip is available

REM Install dependencies
echo.
echo 📦 Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Run system tests
echo.
echo 🧪 Running system tests...
python test_system.py
if errorlevel 1 (
    echo ERROR: System tests failed
    pause
    exit /b 1
)

echo.
echo ================================================
echo    🎉 Setup completed successfully!
echo ================================================
echo.
echo Choose an option:
echo 1. Run Demo (Quick demonstration)
echo 2. Start Monitoring (Background monitoring)
echo 3. Start Dashboard (Web interface)
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🎬 Starting Demo...
    python main.py
) else if "%choice%"=="2" (
    echo.
    echo 📊 Starting Monitoring...
    echo Press Ctrl+C to stop
    python main.py --monitor
) else if "%choice%"=="3" (
    echo.
    echo 🌐 Starting Dashboard...
    echo Dashboard will be available at: http://localhost:5000
    echo Press Ctrl+C to stop
    python dashboard.py
) else (
    echo Goodbye!
)

pause
