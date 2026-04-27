@echo off
echo ========================================
echo Starting WeatherAI Backend Server (Vercel Native)
echo ========================================
echo.

cd /d "%~dp0"

echo Starting FastAPI server on http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn api.index:app --reload --port 8000
