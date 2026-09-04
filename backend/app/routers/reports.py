from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from sqlalchemy import func
from datetime import datetime, date
from typing import Optional

from app.database import get_db
from app.models.pos_models import Transaction, TransactionItem

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/daily")
@router.get("/daily-summary")
def get_daily_report(report_date: Optional[str] = None, session: Session = Depends(get_db)):
    # Parse tanggal filter (default: hari ini)
    target_date = datetime.strptime(report_date, "%Y-%m-%d").date() if report_date else date.today()

    # Query transaksi berdasarkan tanggal
    transactions = session.exec(
        select(Transaction).where(func.date(Transaction.created_at) == str(target_date))
    ).all()

    total_sales = sum(tx.grand_total for tx in transactions)
    total_transactions = len(transactions)

    # Hitung Estimasi Laba Bersih dari TransactionItem
    total_profit = 0.0
    for tx in transactions:
        tx_items = session.exec(
            select(TransactionItem).where(TransactionItem.transaction_id == tx.id)
        ).all()
        for item in tx_items:
            # Gunakan purchase_price / cost_price jika ada
            purchase_price = getattr(item, "purchase_price", getattr(item, "cost_price", 0.0))
            margin_per_unit = item.price - purchase_price
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
                "time": tx.created_at.strftime("%H:%M:%S") if tx.created_at else "",
                "cashier_name": tx.cashier_name,
                "grand_total": tx.grand_total,
                "payment_method": tx.payment_method
            }
            for tx in transactions
        ]
    }