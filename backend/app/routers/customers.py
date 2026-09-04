from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import List

from app.database import get_db
from app.models.pos_models import Customer

router = APIRouter(prefix="/api/customers", tags=["Customers"])

class RedeemPointRequest(BaseModel):
    phone: str
    points_to_redeem: int
    conversion_rate: float = 100.0

@router.get("", response_model=List[Customer])
def get_all_customers(session: Session = Depends(get_db)):
    return session.exec(select(Customer)).all()

@router.get("/phone/{phone}", response_model=Customer)
def get_customer_by_phone(phone: str, session: Session = Depends(get_db)):
    customer = session.exec(select(Customer).where(Customer.phone == phone)).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Member tidak ditemukan!")
    return customer

@router.post("", response_model=Customer)
def create_customer(customer: Customer, session: Session = Depends(get_db)):
    existing = session.exec(select(Customer).where(Customer.phone == customer.phone)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Nomor HP member sudah terdaftar!")
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer

@router.post("/redeem-points")
def redeem_customer_points(req: RedeemPointRequest, session: Session = Depends(get_db)):
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