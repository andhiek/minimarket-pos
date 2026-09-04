# PANDUAN INSTALASI SISTEM POS MINIMARKET
Aplikasi Kasir Multi-Platform (Backend FastAPI + Frontend PySide6 GUI)

---

## 1. PERSYARATAN SISTEM
* **Python:** Versi 3.10 atau lebih baru (Disarankan Python 3.11).
* **Network:** Local Area Network (LAN) / Wi-Fi lokal jika server dan kasir berada di PC terpisah.

---

## 2. INSTALASI DI WINDOWS (CLIENT KASIR)

### Langkah 1: Install Python
1. Unduh installer dari python.org.
2. **Wajib centang** opsi **`Add python.exe to PATH`** sebelum mengklik *Install Now*.

### Langkah 2: Setup Virtual Environment & Library
Buka **Command Prompt (cmd.exe)** di folder project `minimarket-pos`:
```cmd
cd C:\path\to\minimarket-pos
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn sqlmodel passlib bcrypt PySide6 requests
