import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from sqlmodel import Field, SQLModel, Relationship


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    QRIS = "QRIS"
    DEBIT = "DEBIT"


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_number: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Audit Kasir Bertugas
    cashier_id: Optional[int] = Field(default=None, foreign_key="user.id")
    cashier_name: str
    
    grand_total: Decimal = Field(default=Decimal("0.00"))
    paid_amount: Decimal = Field(default=Decimal("0.00"))
    change_amount: Decimal = Field(default=Decimal("0.00"))
    payment_method: str = Field(default="CASH")

    items: List["TransactionItem"] = Relationship(back_populates="transaction")

class TransactionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: Optional[int] = Field(default=None, foreign_key="transaction.id")
    product_id: int
    product_name: str
    price: Decimal
    quantity: int
    subtotal: Decimal

    transaction: Optional[Transaction] = Relationship(back_populates="items")