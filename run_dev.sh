#!/bin/bash
echo "🚀 Menjalankan Backend FastAPI..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

sleep 2

echo "🖥️ Menjalankan Frontend PySide6 POS..."
python3 desktop_client/main.py

kill $BACKEND_PID
