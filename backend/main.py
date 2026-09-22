import shutil
import uvicorn
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
from sqlmodel import Session, select, text
from passlib.context import CryptContext

from app.auth.router import router as auth_router
from app.routers import products, customers, transactions, reports, settings
from app.database import engine, get_db, create_db_and_tables
from app.models.pos_models import User, Product, Customer

# ==============================================================================
# 1. KONFIGURASI DIREKTORI & KRIPTOGRAFI PASSWORD
# ==============================================================================
BACKUP_DIR = Path("./backups")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ==============================================================================
# 2. FUNGSI PEMELIHARAAN SISTEM (BACKUP, MIGRATION, & SEEDING DATA)
# ==============================================================================
def backup_database():
    db_path = Path("./minimarket.db")
    if db_path.exists():
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"minimarket_backup_{timestamp}.db"
        shutil.copy(db_path, backup_file)
        print(f"INFO: POS-Backup: Database berhasil di-backup ke {backup_file}")


def run_auto_migrations():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE product ADD COLUMN discount_percent FLOAT DEFAULT 0.0;"))
            conn.commit()
            print("[MIGRATION] Kolom discount_percent BERHASIL ditambahkan ke DB!")
        except Exception:
            pass

        # Auto-migration untuk kolom NIK dan PIN di tabel users jika belum ada
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN nik VARCHAR;"))
            conn.commit()
            print("[MIGRATION] Kolom nik BERHASIL ditambahkan ke tabel users!")
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN pin VARCHAR;"))
            conn.commit()
            print("[MIGRATION] Kolom pin BERHASIL ditambahkan ke tabel users!")
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR;"))
            conn.commit()
            print("[MIGRATION] Kolom password_hash BERHASIL ditambahkan ke tabel users!")
        except Exception:
            pass


def seed_initial_data():
    with Session(engine) as session:
        user_exist = session.exec(select(User)).first()
        if not user_exist:
            admin_pwd = hash_password("adminpassword")
            kasir_pwd = hash_password("kasirpassword")

            admin_user = User(
                username="admin",  
                password_hash=admin_pwd,  # Diperbarui menggunakan password_hash
                full_name="Administrator",
                role="ADMIN",
            )
            kasir_user = User(  
                nik="3201011234560001",  # Contoh NIK awal untuk kasir
                username="kasir",
                password_hash=kasir_pwd,  # Diperbarui menggunakan password_hash
                pin="1234",               # Contoh PIN awal kasir
                full_name="Kasir Utama",
                role="KASIR",
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
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    run_auto_migrations()
    
    try:
        seed_initial_data()
        print("INFO: REST API POS Backend Siap Digunakan.")
    except Exception as e:
        print(f"ERROR: Seeding gagal: {e}")
    yield
    backup_database()


# ==============================================================================
# 4. INISIALISASI FASTAPI & MIDDLEWARE
# ==============================================================================
app = FastAPI(title="Minimarket POS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrasi Router Modular REST API
app.include_router(auth_router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(settings.router) 

BASE_DIR = Path(__file__).resolve().parent.parent
frontend_path = BASE_DIR / "frontend"

if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")


# ==============================================================================
# 5. SCHEMAS & ROUTE AUTHENTICATION (Mendukung NIK+PIN & Username+Password)
# ==============================================================================
class LoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    nik: Optional[str] = Field(default=None, description="NIK kasir untuk login cepat")
    pin: Optional[str] = Field(default=None, description="PIN kasir")


@app.post("/api/auth/login", tags=["Auth"])
def login(req: LoginRequest, session: Session = Depends(get_db)):
    user = None

    # 1. Login via NIK + PIN (Biasanya untuk Kasir)
    if req.nik and req.pin:
        user = session.exec(
            select(User).where(User.nik == req.nik)
        ).first()
        
        if not user or user.pin != req.pin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="NIK atau PIN salah!",
            )

    # 2. Login via Username + Password (Biasanya untuk Admin/Kasir umum)
    elif req.username and req.password:
        user = session.exec(
            select(User).where(User.username == req.username)
        ).first()

        # Fallback pengecekan password_hash ataupun password biasa jika ada data lama
        target_hash = getattr(user, "password_hash", None) or getattr(user, "password", None)
        
        if not user or not target_hash or not verify_password(req.password, target_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah!",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Harap masukkan (Username & Password) atau (NIK & PIN)!",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun anda telah dinonaktifkan!",
        )

    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
    }


@app.get("/", include_in_schema=False)
def root():
    return {"status": "Online", "message": "Minimarket POS REST API Engine Running."}


# ==============================================================================
# 5.1 ENDPOINT MANAJEMEN USER (CRUD KARYAWAN)
# ==============================================================================
class UserCreateRequest(BaseModel):
    nik: str = Field(..., description="NIK unik karyawan/kasir")
    username: str = Field(..., description="Username login")
    password: str = Field(..., description="Password akun")
    pin: str = Field(..., min_length=4, max_length=6, description="PIN 4-6 digit")
    full_name: str = Field(..., description="Nama lengkap karyawan")
    role: str = Field(default="KASIR", description="ADMIN atau KASIR")


@app.get("/api/users", tags=["Users"])
def get_all_users(session: Session = Depends(get_db)):
    users = session.exec(select(User)).all()
    return [
        {
            "id": u.id,
            "nik": u.nik,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at
        }
        for u in users
    ]


@app.post("/api/users", tags=["Users"])
def create_user(req: UserCreateRequest, session: Session = Depends(get_db)):
    # Cek duplikasi NIK jika diisi
    if req.nik:
        existing_nik = session.exec(select(User).where(User.nik == req.nik)).first()
        if existing_nik:
            raise HTTPException(status_code=400, detail="NIK tersebut sudah terdaftar!")

    # Cek duplikasi Username
    existing_username = session.exec(select(User).where(User.username == req.username)).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username tersebut sudah digunakan!")

    hashed_pwd = hash_password(req.password)

    new_user = User(
        nik=req.nik,
        username=req.username,
        password_hash=hashed_pwd,
        pin=req.pin,
        full_name=req.full_name,
        role=req.role.upper(),
        is_active=True
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return {
        "message": "Karyawan baru berhasil ditambahkan!",
        "user": {
            "id": new_user.id,
            "nik": new_user.nik,
            "username": new_user.username,
            "full_name": new_user.full_name,
            "role": new_user.role
        }
    }


@app.patch("/api/users/{user_id}/toggle-status", tags=["Users"])
def toggle_user_status(user_id: int, session: Session = Depends(get_db)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan!")
    
    # Toggle status aktif / non-aktif
    user.is_active = not user.is_active
    session.add(user)
    session.commit()
    
    status_msg = "diaktifkan" if user.is_active else "dinonaktifkan"
    return {"message": f"Akun {user.full_name} berhasil {status_msg}.", "is_active": user.is_active}


# ==============================================================================
# 6. SERVER EXECUTION ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    
    cert_file = current_dir / "192.168.1.8+2.pem"
    key_file = current_dir / "192.168.1.8+2-key.pem"

    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        ssl_keyfile=str(key_file),
        ssl_certfile=str(cert_file),
        reload=True
    )