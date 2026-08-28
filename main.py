import shutil
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, Session, create_engine, select
from sqlalchemy import func
from passlib.context import CryptContext

# ==============================================================================
# SECURITY & DATABASE CONFIGURATION
# ==============================================================================
DATABASE_URL = "sqlite:///./minimarket.db"
BACKUP_DIR = Path("./backups")

# Konfigurasi Hashing Password dengan Bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def backup_database():
    """Auto-backup file minimarket.db ke folder backups/"""
    db_path = Path("./minimarket.db")
    if db_path.exists():
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"minimarket_backup_{timestamp}.db"
        shutil.copy(db_path, backup_file)
        print(f"INFO: POS-Backup: Database berhasil di-backup ke {backup_file}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# ==============================================================================
# SQLMODEL DEFINITIONS
# ==============================================================================
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str
    full_name: str
    role: str = Field(default="kasir")


class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(index=True, unique=True)
    name: str
    points: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    barcode: str = Field(index=True, unique=True)
    name: str
    price: float
    purchase_price: float = Field(default=0.0)
    stock: int = Field(default=0)
    category: Optional[str] = Field(default="Umum")


class TransactionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id")
    product_id: int = Field(foreign_key="product.id")
    product_name: str
    quantity: int
    price: float
    subtotal: float
    purchase_price: float = Field(default=0.0)

    transaction: Optional["Transaction"] = Relationship(back_populates="items")


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_number: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.now)
    cashier_id: int
    cashier_name: str
    customer_id: Optional[int] = Field(default=None, foreign_key="customer.id")
    customer_name: Optional[str] = Field(default="Non-Member")
    subtotal_amount: float = Field(default=0.0)
    discount_amount: float = Field(default=0.0)
    grand_total: float
    paid_amount: float
    change_amount: float
    points_earned: int = Field(default=0)
    payment_method: str = Field(default="CASH")

    items: List[TransactionItem] = Relationship(back_populates="transaction")


def get_session():
    with Session(engine) as session:
        yield session


# ==============================================================================
# SEEDING & LIFESPAN MANAGEMENT
# ==============================================================================
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
    SQLModel.metadata.create_all(engine)
    try:
        seed_initial_data()
        print("INFO: POS-Main: Sistem POS Backend Siap Digunakan.")
    except Exception as e:
        print(f"ERROR: POS-Main: Gagal seeding data: {e}")
    yield
    backup_database()


app = FastAPI(title="Minimarket POS API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================
class LoginRequest(BaseModel):
    username: str
    password: str


class CartItemSchema(BaseModel):
    product_id: int
    quantity: int


class CheckoutRequest(BaseModel):
    cashier_id: int
    cashier_name: str
    customer_phone: Optional[str] = None
    cart_items: List[CartItemSchema]
    paid_amount: float
    discount_amount: float = 0.0
    payment_method: str = "CASH"


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

# --- AUTH ---
@app.post("/api/auth/login")
def login(req: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == req.username)).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=400, detail="Username atau password salah!")
    return {"id": user.id, "username": user.username, "full_name": user.full_name, "role": user.role}


# --- CUSTOMER / MEMBER ---
@app.get("/api/customers/phone/{phone}")
def get_customer_by_phone(phone: str, session: Session = Depends(get_session)):
    customer = session.exec(select(Customer).where(Customer.phone == phone)).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Member tidak ditemukan!")
    return customer


@app.post("/api/customers")
def create_customer(customer: Customer, session: Session = Depends(get_session)):
    existing = session.exec(select(Customer).where(Customer.phone == customer.phone)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Nomor HP member sudah terdaftar!")
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


# --- PRODUCTS ---
@app.get("/api/products/barcode/{barcode}")
def get_product_by_barcode(barcode: str, session: Session = Depends(get_session)):
    product = session.exec(select(Product).where(Product.barcode == barcode)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan!")
    return product


@app.get("/api/products/all")
def get_all_products(session: Session = Depends(get_session)):
    """Mengambil seluruh daftar produk"""
    return session.exec(select(Product)).all()


@app.post("/api/products")
def create_product(product: Product, session: Session = Depends(get_session)):
    """Tambah produk baru"""
    existing = session.exec(select(Product).where(Product.barcode == product.barcode)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Barcode sudah terdaftar!")
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

@app.put("/api/products/{product_id}")
def update_product(product_id: int, product_data: Product, session: Session = Depends(get_session)):
    """Update data produk"""
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    db_product.barcode = product_data.barcode
    db_product.name = product_data.name
    db_product.category = product_data.category
    db_product.price = product_data.price
    if hasattr(db_product, "purchase_price"):
        db_product.purchase_price = product_data.purchase_price
    db_product.stock = product_data.stock
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, session: Session = Depends(get_session)):
    """Hapus produk"""
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    session.delete(db_product)
    session.commit()
    return {"message": "Produk berhasil dihapus"}


# --- CHECKOUT / TRANSACTIONS ---
@app.post("/api/pos/checkout")
def checkout(req: CheckoutRequest, session: Session = Depends(get_session)):
    if not req.cart_items:
        raise HTTPException(status_code=400, detail="Keranjang belanja kosong!")

    subtotal_total = 0.0
    items_to_create = []

    for item_req in req.cart_items:
        product = session.get(Product, item_req.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Produk ID {item_req.product_id} tidak ditemukan!")
        if product.stock < item_req.quantity:
            raise HTTPException(status_code=400, detail=f"Stok '{product.name}' tidak mencukupi (Tersisa: {product.stock})!")

        assert product.id is not None, "Product ID tidak valid"

        item_subtotal = product.price * item_req.quantity
        subtotal_total += item_subtotal

        product.stock -= item_req.quantity
        session.add(product)

        items_to_create.append(TransactionItem(
            product_id=product.id,
            product_name=product.name,
            quantity=item_req.quantity,
            price=product.price,
            subtotal=item_subtotal,
            purchase_price=product.purchase_price
        ))

    grand_total = max(0.0, subtotal_total - req.discount_amount)
    change_amount = req.paid_amount - grand_total
    if change_amount < 0:
        raise HTTPException(status_code=400, detail="Uang pembayaran kurang!")

    # Cek & proses poin member
    customer_id = None
    customer_name = "Non-Member"
    points_earned = 0

    if req.customer_phone:
        customer = session.exec(select(Customer).where(Customer.phone == req.customer_phone)).first()
        if customer:
            customer_id = customer.id
            customer_name = customer.name
            points_earned = int(grand_total // 10000)
            customer.points += points_earned
            session.add(customer)

    inv_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    new_transaction = Transaction(
        invoice_number=inv_number,
        cashier_id=req.cashier_id,
        cashier_name=req.cashier_name,
        customer_id=customer_id,
        customer_name=customer_name,
        subtotal_amount=subtotal_total,
        discount_amount=req.discount_amount,
        grand_total=grand_total,
        paid_amount=req.paid_amount,
        change_amount=change_amount,
        points_earned=points_earned,
        payment_method=req.payment_method
    )

    session.add(new_transaction)
    session.commit()
    session.refresh(new_transaction)

    for item in items_to_create:
        item.transaction_id = new_transaction.id
        session.add(item)

    session.commit()

    return {
        "invoice_number": new_transaction.invoice_number,
        "customer_name": customer_name,
        "subtotal": subtotal_total,
        "discount": req.discount_amount,
        "grand_total": grand_total,
        "paid_amount": req.paid_amount,
        "change_amount": change_amount,
        "points_earned": points_earned,
        "cashier_name": new_transaction.cashier_name,
        "created_at": new_transaction.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }


# --- REPORTS ---
@app.get("/api/reports/daily")
def get_daily_report(report_date: Optional[str] = None, session: Session = Depends(get_session)):
    target_date = datetime.strptime(report_date, "%Y-%m-%d").date() if report_date else date.today()

    transactions = session.exec(
        select(Transaction).where(func.date(Transaction.created_at) == str(target_date))
    ).all()

    total_sales = sum(tx.grand_total for tx in transactions)
    total_transactions = len(transactions)

    total_profit = 0.0
    for tx in transactions:
        tx_items = session.exec(select(TransactionItem).where(TransactionItem.transaction_id == tx.id)).all()
        for item in tx_items:
            margin_per_unit = item.price - item.purchase_price
            total_profit += margin_per_unit * item.quantity

    return {
        "report_date": str(target_date),
        "total_transactions": total_transactions,
        "total_sales": total_sales,
        "total_profit": total_profit,
        "transactions": [
            {
                "id": tx.id,
                "invoice_number": tx.invoice_number,
                "time": tx.created_at.strftime("%H:%M:%S"),
                "cashier_name": tx.cashier_name,
                "grand_total": tx.grand_total,
                "payment_method": tx.payment_method
            }
            for tx in transactions
        ]
    }
    
# --- CUSTOMER ENDPOINTS (Tambahkan/Update di main.py) ---

@app.get("/api/customers")
def get_all_customers(session: Session = Depends(get_session)):
    """Mengambil seluruh daftar member"""
    return session.exec(select(Customer)).all()

class RedeemPointRequest(BaseModel):
    phone: str
    points_to_redeem: int
    conversion_rate: float = 100.0  # 1 Poin = Rp 100

@app.post("/api/customers/redeem-points")
def redeem_customer_points(req: RedeemPointRequest, session: Session = Depends(get_session)):
    """Tukar poin member menjadi nilai diskon (Rp)"""
    customer = session.exec(select(Customer).where(Customer.phone == req.phone)).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Member tidak ditemukan!")
    
    if customer.points < req.points_to_redeem:
        raise HTTPException(status_code=400, detail=f"Poin tidak cukup! Sisa poin: {customer.points}")
    
    discount_value = req.points_to_redeem * req.conversion_rate
    customer.points -= req.points_to_redeem
    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    return {
        "message": "Poin berhasil ditukar",
        "remaining_points": customer.points,
        "discount_amount": discount_value
    }
    
    
