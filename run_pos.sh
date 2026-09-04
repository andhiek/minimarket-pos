#!/bin/bash

echo "==================================================="
echo "  Menjalankan Minimarket POS System..."
echo "==================================================="

# Membuka browser default sesuai OS setelah jeda 3 detik
(
  sleep 3
  if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8000
  elif command -v open > /dev/null; then
    open http://localhost:8000
  fi
) &

# Menjalankan Server FastAPI Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
