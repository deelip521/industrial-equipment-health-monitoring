@echo off
title Share Industrial Health Monitor to Public Internet
echo =====================================================================
echo  Creating Instant Public URL for Industrial Equipment Health App
echo =====================================================================
echo.
echo Make sure your app is running on http://localhost:8000 first!
echo.
echo Select your preferred public tunnel method:
echo  [1] Pinggy (Built-in SSH, No login, Fast HTTPS URL) - RECOMMENDED
echo  [2] Cloudflare Quick Tunnel (Free, Highly Reliable)
echo  [3] Localtunnel (via Node.js npx)
echo.

set /p choice="Enter choice [1, 2, or 3] (Default is 1): "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo.
    echo Starting SSH Tunnel via Pinggy...
    echo Your public URL will appear below (e.g. https://xxxxx.a.pinggy.link):
    echo ---------------------------------------------------------------------
    ssh -o StrictHostKeyChecking=no -p 443 -R0:localhost:8000 a.pinggy.io
    goto end
)

if "%choice%"=="2" (
    echo.
    echo Starting Cloudflare Tunnel...
    echo Your public URL will appear below (e.g. https://xxxxx.trycloudflare.com):
    echo ---------------------------------------------------------------------
    npx --yes cloudflared tunnel --url http://localhost:8000
    goto end
)

if "%choice%"=="3" (
    echo.
    echo Starting Localtunnel...
    echo ---------------------------------------------------------------------
    npx --yes localtunnel --port 8000
    goto end
)

:end
pause
