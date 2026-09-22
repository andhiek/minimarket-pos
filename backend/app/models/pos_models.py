from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    nik: Optional[str] = Field(default=None, index=True, unique=True, nullable=True)  # Tambahan NIK untuk kasir
    username: str = Field(index=True, unique=True, nullable=False)
    password_hash: str = Field(nullable=False)  # Menggantikan 'password' biasa agar aman
    pin: Optional[str] = Field(default=None, nullable=True)  # PIN 4-6 digit untuk login cepat kasir
    full_name: str = Field(nullable=False)
    role: str = Field(default="KASIR", nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)


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
    discount_percent: float = Field(default=0.0)  # <-- Tambahkan field ini
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
    
    