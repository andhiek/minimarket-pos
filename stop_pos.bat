@echo off
title Stop Minimarket POS Server
echo ===================================================
echo   Menghentikan Server Minimarket POS...
echo ===================================================

:: Menghentikan proses uvicorn dan python yang berjalan
taskkill /F /IM uvicorn.exe /T 2>nul
taskkill /FI "WINDOWTITLE eq Minimarket POS*" /F /T 2>nul

echo.
echo Server Minimarket POS berhasil dihentikan.
timeout /t 3