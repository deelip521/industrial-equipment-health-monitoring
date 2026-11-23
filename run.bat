@echo off
title Industrial Equipment Health Monitoring Platform
echo =====================================================================
echo  Industrial Equipment Health Monitoring System
echo  Predictive Maintenance Analytics for Industrial IoT Equipment
echo =====================================================================
echo.
cd /d "%~dp0"

echo Checking dependencies...
python -m pip install -r requirements.txt --quiet

echo.
echo Starting FastAPI & IoT Telemetry Streaming Engine on http://localhost:8000
echo Open http://localhost:8000 in your web browser.
echo Press Ctrl+C to stop the server.
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
pause
