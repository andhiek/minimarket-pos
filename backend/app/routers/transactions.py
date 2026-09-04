from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models.pos_models import Product, Customer, Transaction, TransactionItem

router = APIRouter(prefix="/api/pos", tags=["Transactions"])

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

@router.post("/checkout")
def checkout(req: CheckoutRequest, session: Session = Depends(get_db)):
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

        assert product.id is not None

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