from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import PaymentMethod


class CartItemSchema(BaseModel):
    """Schema item keranjang belanja dari client."""
    product_id: int
    quantity: int = Field(gt=0, description="Jumlah barang harus lebih dari 0")


class CheckoutRequest(BaseModel):
    """Schema payload request untuk proses checkout."""
    cashier_id: int
    cashier_name: str
    cart_items: List[CartItemSchema]
    paid_amount: Decimal = Field(ge=Decimal("0.00"), description="Uang dibayar tidak boleh negatif")
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    payment_method: PaymentMethod = PaymentMethod.CASH


class TransactionItemResponse(BaseModel):
    """Schema response item detail dalam transaksi."""
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    price_per_unit: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    """Schema response lengkap transaksi setelah checkout/query."""
    id: int
    invoice_number: str
    cashier_id: int
    cashier_name: str
    total_amount: Decimal
    discount_amount: Decimal
    grand_total: Decimal
    paid_amount: Decimal
    change_amount: Decimal
    payment_method: PaymentMethod
    created_at: datetime
    items: List[TransactionItemResponse]

    model_config = ConfigDict(from_attributes=True)