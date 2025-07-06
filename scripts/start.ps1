# Graph RAG Pipeline Startup Script for Windows
# Run this script in PowerShell to start the application

Write-Host "🏁 Graph RAG Pipeline Startup Script" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "✅ .env file found" -ForegroundColor Green
} else {
    Write-Host "❌ .env file not found" -ForegroundColor Red
    Write-Host "Please create a .env file with the required environment variables" -ForegroundColor Yellow
    exit 1
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Blue
try {
    python -m pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Start the server
Write-Host "🚀 Starting Graph RAG Pipeline server..." -ForegroundColor Blue
Write-Host "📖 API documentation will be available at: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🔍 Health check available at: http://localhost:8000/api/v1/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host "❌ Failed to start server" -ForegroundColor Red
}

Write-Host "👋 Server stopped" -ForegroundColor Yellow
