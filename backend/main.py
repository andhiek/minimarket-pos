import shutil
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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


# PERBAIKAN: Fungsi untuk auto-add kolom discount_percent jika belum ada di SQLite
def run_auto_migrations():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE product ADD COLUMN discount_percent FLOAT DEFAULT 0.0;"))
            conn.commit()
            print("[MIGRATION] Kolom discount_percent BERHASIL ditambahkan ke DB!")
        except Exception:
            # Mengabaikan error jika kolom sudah ada
            pass


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
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Buat tabel jika belum ada
    create_db_and_tables()
    
    # 2. PERBAIKAN: Jalankan auto-migration kolom baru
    run_auto_migrations()
    
    try:
        # 3. Seed data sampel
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

# PERBAIKAN: Konfigurasi CORS agar mendukung akses lintas origin (127.0.0.1 & localhost)
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

# Mounting direktori frontend
BASE_DIR = Path(__file__).resolve().parent.parent
frontend_path = BASE_DIR / "frontend"

if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")


# ==============================================================================
# 5. SCHEMAS & ROUTE AUTHENTICATION
# ==============================================================================
class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login", tags=["Auth"])
def login(req: LoginRequest, session: Session = Depends(get_db)):
    user = session.exec(
        select(User).where(User.username == req.username)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah!",
        )

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


@app.get("/", include_in_schema=False)
def root():
    return {"status": "Online", "message": "Minimarket POS REST API Engine Running."}


# ==============================================================================
# 6. SERVER EXECUTION ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)