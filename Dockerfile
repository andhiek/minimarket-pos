FROM python:3.11-slim

WORKDIR /workspace

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code backend
COPY ./app ./app
COPY ./minimarket.db ./minimarket.db

EXPOSE 8000

# Jalankan Uvicorn FastAPI Server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
