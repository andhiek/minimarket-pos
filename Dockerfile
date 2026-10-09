# Menggunakan image resmi Python yang ringan (slim)
FROM python:3.10-slim

# Menetapkan direktori kerja di dalam container
WORKDIR /app

# Menyalin file daftar dependensi terlebih dahulu (agar caching Docker optimal)
COPY requirements.txt .

# Menginstal modul Python yang dibutuhkan
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin seluruh file project (backend, frontend, database, dll) ke dalam container
COPY . .

# Membuka port yang digunakan FastAPI
EXPOSE 8000

# Perintah untuk menjalankan aplikasi FastAPI dengan Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]