import shutil
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select
from passlib.context import CryptContext

from app.auth.router import router as auth_router
from app.routers import products, customers, transactions, reports, settings
from app.database import engine, get_db, create_db_and_tables
from app.models.pos_models import User, Product, Customer

BACKUP_DIR = Path("./backups")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def backup_database():
    db_path = Path("./minimarket.db")
    if db_path.exists():
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"minimarket_backup_{timestamp}.db"
        shutil.copy(db_path, backup_file)
        print(f"INFO: POS-Backup: Database di-backup ke {backup_file}")

def seed_initial_data():
    with Session(engine) as session:
        if not session.exec(select(User)).first():
            session.add(User(username="admin", password=hash_password("adminpassword"), full_name="Administrator", role="admin"))
            session.add(User(username="kasir", password=hash_password("kasirpassword"), full_name="Kasir Utama", role="kasir"))
            session.commit()

        if not session.exec(select(Product)).first():
            sample_products = [
                Product(barcode="8999999001", name="Air Mineral 600ml", price=3500.0, purchase_price=2500.0, stock=100, category="Minuman"),
                Product(barcode="8999999002", name="Kopi Instan Saset", price=1500.0, purchase_price=1000.0, stock=200, category="Minuman"),
                Product(barcode="8999999003", name="Roti Tawar Slice", price=12000.0, purchase_price=9000.0, stock=30, category="Makanan"),
            ]
            for prod in sample_products:
                session.add(prod)
            session.commit()

        if not session.exec(select(Customer)).first():
            session.add(Customer(phone="081234567890", name="Budi Santoso", points=150))
            session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Membuat tabel otomatis di database minimarket.db
    create_db_and_tables()
    try:
        seed_initial_data()
        print("INFO: REST API POS Backend Siap Digunakan.")
    except Exception as e:
        print(f"ERROR: Seeding gagal: {e}")
    yield
    backup_database()

app = FastAPI(title="Minimarket POS API", lifespan=lifespan)

# Allow CORS untuk koneksi dari Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrasi Router REST API
app.include_router(auth_router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(settings.router) 

# Mounting folder frontend sebagai Static Files
BASE_DIR = Path(__file__).resolve().parent.parent
frontend_path = BASE_DIR / "frontend"

if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login", tags=["Auth"])
def login(req: LoginRequest, session: Session = Depends(get_db)):
    user = session.exec(select(User).where(User.username == req.username)).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=400, detail="Username atau password salah!")
    return {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role}

@app.get("/", include_in_schema=False)
def root():
    return {"status": "Online", "message": "Minimarket POS REST API Engine Running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)