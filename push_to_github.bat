@echo off
title Push to GitHub - Industrial Equipment Health Monitoring
echo =====================================================================
echo  Pushing Industrial Equipment Health Monitor to GitHub
echo  Repository: https://github.com/deelip521/industrial-equipment-health-monitoring
echo =====================================================================
echo.
cd /d "%~dp0"

echo Current remote origin:
git remote -v
echo.
echo Pushing branch 'main' to origin...
git push -u origin main --force

if %ERRORLEVEL% equ 0 (
    echo.
    echo =====================================================================
    echo  SUCCESS! Project pushed to https://github.com/deelip521/industrial-equipment-health-monitoring
    echo =====================================================================
) else (
    echo.
    echo If GitHub asks for authentication:
    echo 1. Sign in via your browser when prompted, OR
    echo 2. Use your GitHub Personal Access Token (PAT) as password.
)

echo.
pause
