@echo off
title Minimarket POS Server
echo ===================================================
echo   Menjalankan Minimarket POS System...
echo ===================================================

:: Membuka browser default ke http://localhost:8000 setelah jeda 3 detik
start "" powershell -Command "Start-Sleep -s 3; Start-Process 'http://localhost:8000'"

:: Menjalankan Server FastAPI Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause