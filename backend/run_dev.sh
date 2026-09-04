#!/bin/bash

# Pastikan berada di root direktori project
cd "$(dirname "$0")"

echo "🚀 Menjalankan Backend FastAPI..."

# Cek lokasi main.py secara tepat
if [ -f "main.py" ]; then
    uvicorn main:app --reload --port 8000 &
elif [ -f "app/main.py" ]; then
    uvicorn app.main:app --reload --port 8000 &
else
    echo "❌ Error: File main.py backend tidak ditemukan!"
    exit 1
fi

BACKEND_PID=$!

# Jeda 2 detik agar FastAPI startup dengan sempurna
sleep 2

echo "🖥️ Menjalankan Frontend PySide6 POS (gui_app.py)..."

if [ -f "desktop_client/gui_app.py" ]; then
    python3 desktop_client/gui_app.py
else
    echo "❌ Error: File desktop_client/gui_app.py tidak ditemukan!"
fi

# Matikan server backend saat aplikasi GUI ditutup
kill $BACKEND_PID
