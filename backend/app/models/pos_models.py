from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

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
    
    