import shutil
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select
from passlib.context import CryptContext

from app.auth.router import router as auth_router
from app.routers import products, customers, transactions, reports, settings
from app.database import engine, get_db, create_db_and_tables
from app.models.pos_models import User, Product, Customer

# ==============================================================================
# 1. KONFIGURASI DIREKTORI & KRIPTOGRAFI PASSWORD
# ==============================================================================
# Menentukan folder lokasi penyimpanan file backup database
BACKUP_DIR = Path("./backups")

# Menginisialisasi context Passlib dengan algoritma bcrypt untuk hashing password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Fungsi untuk mengubah password teks biasa menjadi hash bcrypt aman
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Fungsi untuk memverifikasi apakah password teks cocok dengan hash bcrypt di DB
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ==============================================================================
# 2. FUNGSI PEMELIHARAAN SISTEM (BACKUP & SEEDING DATA)
# ==============================================================================
# Fungsi untuk membuat salinan cadangan (backup) file SQLite secara otomatis
def backup_database():
    db_path = Path("./minimarket.db")
    if db_path.exists():
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"minimarket_backup_{timestamp}.db"
        shutil.copy(db_path, backup_file)
        print(f"INFO: POS-Backup: Database berhasil di-backup ke {backup_file}")


# Fungsi untuk mengisi data awal (default/sample) jika database masih kosong
# Fungsi untuk mengisi data awal (default/sample) jika database masih kosong
# Tambahkan print debug di seed_initial_data
def seed_initial_data():
    with Session(engine) as session:
        user_exist = session.exec(select(User)).first()
        if not user_exist:
            admin_pwd = hash_password("adminpassword")
            kasir_pwd = hash_password("kasirpassword")

            admin_user = User(
                username="admin",
                password=admin_pwd,
                full_name="Administrator",
                role="admin",
            )
            kasir_user = User(
                username="kasir",
                password=kasir_pwd,
                full_name="Kasir Utama",
                role="kasir",
            )

            session.add(admin_user)
            session.add(kasir_user)
            session.commit()
            print("[DEBUG SEED] User admin & kasir BERHASIL dibuat di DB!")
        else:
            print("[DEBUG SEED] User sudah ada di DB, seeding dilewati.")


# ==============================================================================
# 3. LIFESPAN HANDLER (STARTUP & SHUTDOWN EVENTS)
# ==============================================================================
# Context manager untuk mengelola siklus hidup aplikasi (dijalankan saat start & stop)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dijalankan saat aplikasi startup:
    create_db_and_tables()  # Membuat tabel otomatis di database minimarket.db
    try:
        seed_initial_data()  # Memasukkan data sampel jika DB baru dibuat
        print("INFO: REST API POS Backend Siap Digunakan.")
    except Exception as e:
        print(f"ERROR: Seeding gagal: {e}")
    yield
    # Dijalankan saat aplikasi shutdown:
    backup_database()  # Melakukan backup database otomatis saat aplikasi dimatikan


# ==============================================================================
# 4. INISIALISASI FASTAPI & MIDDLEWARE
# ==============================================================================
app = FastAPI(title="Minimarket POS API", lifespan=lifespan)

# Mengaktifkan Cross-Origin Resource Sharing (CORS) agar Frontend dapat mengakses API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrasi Router Modular REST API dari folder routers
app.include_router(auth_router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(settings.router) 

# Mounting direktori frontend sebagai Static Files agar dapat diakses dari browser
BASE_DIR = Path(__file__).resolve().parent.parent
frontend_path = BASE_DIR / "frontend"

if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")


# ==============================================================================
# 5. SCHEMAS & ROUTE AUTHENTICATION
# ==============================================================================
# Skema Pydantic untuk memvalidasi payload request Body dari Login Form
class LoginRequest(BaseModel):
    username: str
    password: str


# Endpoint untuk otentikasi login pengguna (Kasir / Admin)
@app.post("/api/auth/login", tags=["Auth"])
def login(req: LoginRequest, session: Session = Depends(get_db)):

    # 1. Cari user di DB
    user = session.exec(
        select(User).where(User.username == req.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah!",
        )


    # 2. Verifikasi Password
    is_valid = verify_password(req.password, user.password)


    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah!",
        )

    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
    }


# Endpoint Root dasar untuk mengecek status kesehatan server API
@app.get("/", include_in_schema=False)
def root():
    return {"status": "Online", "message": "Minimarket POS REST API Engine Running."}


# ==============================================================================
# 6. SERVER EXECUTION ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    # Menjalankan ASGI Server Uvicorn pada host 0.0.0.0 agar bisa diakses di jaringan lokal (LAN)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)