# Smart Auto-Scaling System Startup Script for PowerShell

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Smart Auto-Scaling System - Setup" -ForegroundColor Cyan  
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if pip is available
try {
    $pipVersion = pip --version 2>&1
    Write-Host "✅ pip is available: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: pip is not available" -ForegroundColor Red
    Write-Host "Please ensure pip is installed with Python" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Run system tests
Write-Host ""
Write-Host "🧪 Running system tests..." -ForegroundColor Yellow
try {
    python test_system.py
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed"
    }
} catch {
    Write-Host "❌ ERROR: System tests failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "   🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Menu
while ($true) {
    Write-Host "Choose an option:" -ForegroundColor Cyan
    Write-Host "1. Run Demo (Quick demonstration)" -ForegroundColor White
    Write-Host "2. Start Monitoring (Background monitoring)" -ForegroundColor White
    Write-Host "3. Start Dashboard (Web interface)" -ForegroundColor White
    Write-Host "4. Exit" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (1-4)"
    
    switch ($choice) {
        "1" {
            Write-Host ""
            Write-Host "🎬 Starting Demo..." -ForegroundColor Yellow
            python main.py
            break
        }
        "2" {
            Write-Host ""
            Write-Host "📊 Starting Monitoring..." -ForegroundColor Yellow
            Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
            python main.py --monitor
            break
        }
        "3" {
            Write-Host ""
            Write-Host "🌐 Starting Dashboard..." -ForegroundColor Yellow
            Write-Host "Dashboard will be available at: http://localhost:5000" -ForegroundColor Gray
            Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
            python dashboard.py
            break
        }
        "4" {
            Write-Host "Goodbye!" -ForegroundColor Green
            exit 0
        }
        default {
            Write-Host "Invalid choice. Please enter 1-4." -ForegroundColor Red
        }
    }
}

Read-Host "Press Enter to exit"
