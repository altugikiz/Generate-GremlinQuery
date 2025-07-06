@echo off
echo 🏁 Graph RAG Pipeline Startup
echo ===============================

echo 📦 Installing dependencies...
python -m pip install -r requirements.txt

echo.
echo 🚀 Starting Graph RAG Pipeline server...
echo 📖 API documentation: http://localhost:8000/docs
echo 🔍 Health check: http://localhost:8000/api/v1/health
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
