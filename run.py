#!/usr/bin/env python3
"""
Startup script for Graph RAG Pipeline FastAPI application.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please create a .env file with the required environment variables")
        sys.exit(1)
    print("✅ .env file found")

def install_dependencies():
    """Install dependencies from requirements.txt."""
    try:
        print("📦 Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def run_server():
    """Run the FastAPI server."""
    try:
        print("🚀 Starting Graph RAG Pipeline server...")
        print("📖 API documentation will be available at: http://localhost:8000/docs")
        print("🔍 Health check available at: http://localhost:8000/api/v1/health")
        print("\nPress Ctrl+C to stop the server\n")
        
        # Run uvicorn server
        subprocess.check_call([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def main():
    """Main function to run all startup checks and start the server."""
    print("🏁 Graph RAG Pipeline Startup Script")
    print("=" * 50)
    
    # Run checks
    check_python_version()
    check_env_file()
    
    # Install dependencies
    install_dependencies()
    
    # Start server
    run_server()

if __name__ == "__main__":
    main()
