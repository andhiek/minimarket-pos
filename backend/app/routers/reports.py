from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy import func
from datetime import datetime, date
from typing import Optional

from app.database import get_db
from app.models.pos_models import Transaction, TransactionItem, Product

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# --- Helper Functions ---
def calculate_profit(session: Session, transactions):
    total_profit = 0.0
    for tx in transactions:
        tx_items = session.exec(
            select(TransactionItem).where(TransactionItem.transaction_id == tx.id)
        ).all()
        for item in tx_items:
            purchase_price = getattr(item, "purchase_price", getattr(item, "cost_price", 0.0))
            margin_per_unit = item.price - purchase_price
            total_profit += margin_per_unit * item.quantity
    return total_profit

def calculate_payment_breakdown(transactions):
    """Menghitung total nominal berdasarkan metode pembayaran (CASH, QRIS, TRANSFER, dll)"""
    breakdown = {}
    for tx in transactions:
        method = getattr(tx, "payment_method", "CASH") or "CASH"
        method = method.upper()
        total = getattr(tx, "grand_total", getattr(tx, "total", 0.0))
        breakdown[method] = breakdown.get(method, 0.0) + total
    return breakdown

# Helper function untuk format response transaksi
def format_transactions(transactions):
    result = []
    for tx in transactions:
        created_at_dt = getattr(tx, "created_at", None)
        
        date_str = "-"
        time_str = "-"
        iso_str = ""

        if isinstance(created_at_dt, datetime):
            date_str = created_at_dt.strftime("%d/%m/%Y")
            time_str = created_at_dt.strftime("%H:%M")
            iso_str = created_at_dt.isoformat()
        elif isinstance(created_at_dt, str):
            iso_str = created_at_dt
            if "T" in created_at_dt:
                parts = created_at_dt.split("T")
                date_str = datetime.strptime(parts[0], "%Y-%m-%d").strftime("%d/%m/%Y") if parts[0] else "-"
                time_str = parts[1][:5]
            elif " " in created_at_dt:
                parts = created_at_dt.split(" ")
                date_str = parts[0]
                time_str = parts[1][:5]

        invoice_no = getattr(tx, "invoice_number", getattr(tx, "invoice_no", f"INV-{tx.id}"))
        cashier = getattr(tx, "cashier_name", getattr(tx, "cashier", "Administrator"))

        result.append({
            "id": tx.id,
            "invoice_no": invoice_no,
            "created_at": iso_str,
            "date": date_str,
            "time": time_str,
            "cashier": cashier if cashier else "Administrator",
            "grand_total": getattr(tx, "grand_total", getattr(tx, "total", 0.0)),
            "payment_method": getattr(tx, "payment_method", "CASH")
        })
    return result

# 1. ENDPOINT LAPORAN HARIAN
@router.get("/daily")
@router.get("/daily-summary")
def get_daily_report(report_date: Optional[str] = None, session: Session = Depends(get_db)):
    target_date = datetime.strptime(report_date, "%Y-%m-%d").date() if report_date else date.today()

    transactions = session.exec(
        select(Transaction).where(func.date(Transaction.created_at) == str(target_date))
    ).all()

    total_sales = sum(getattr(tx, "grand_total", getattr(tx, "total", 0.0)) for tx in transactions)
    total_transactions = len(transactions)
    total_profit = calculate_profit(session, transactions)
    payment_breakdown = calculate_payment_breakdown(transactions)

    return {
        "summary": {
            "total_tx": total_transactions,
            "total_sales": total_sales,
            "total_profit": total_profit,
            "payment_breakdown": payment_breakdown
        },
        "transactions": format_transactions(transactions)
    }

# 2. ENDPOINT LAPORAN BULANAN
@router.get("/monthly")
def get_monthly_report(report_month: Optional[str] = None, session: Session = Depends(get_db)):
    if not report_month:
        report_month = date.today().strftime("%Y-%m")

    transactions = session.exec(
        select(Transaction).where(func.strftime("%Y-%m", Transaction.created_at) == report_month)
    ).all()

    total_sales = sum(getattr(tx, "grand_total", getattr(tx, "total", 0.0)) for tx in transactions)
    total_transactions = len(transactions)
    total_profit = calculate_profit(session, transactions)
    payment_breakdown = calculate_payment_breakdown(transactions)

    return {
        "summary": {
            "total_tx": total_transactions,
            "total_sales": total_sales,
            "total_profit": total_profit,
            "payment_breakdown": payment_breakdown
        },
        "transactions": format_transactions(transactions)
    }

# 3. ENDPOINT DETAIL TRANSAKSI / ITEM NOTA
@router.get("/transaction/{tx_id}")
def get_transaction_detail(tx_id: int, session: Session = Depends(get_db)):
    tx = session.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")

    items = session.exec(
        select(TransactionItem).where(TransactionItem.transaction_id == tx_id)
    ).all()

    item_list = []
    for it in items:
        product_name = getattr(it, "product_name", "Produk")
        if not product_name and getattr(it, "product_id", None):
            prod = session.get(Product, it.product_id)
            if prod:
                product_name = prod.name

        item_list.append({
            "product_name": product_name,
            "price": it.price,
            "quantity": it.quantity,
            "subtotal": it.price * it.quantity
        })

    created_at_str = tx.created_at.strftime("%d/%m/%Y %H:%M:%S") if getattr(tx, "created_at", None) else "-"

    return {
        "id": tx.id,
        "invoice_no": getattr(tx, "invoice_number", getattr(tx, "invoice_no", f"INV-{tx.id}")),
        "date_time": created_at_str,
        "cashier": getattr(tx, "cashier_name", getattr(tx, "cashier", "Administrator")),
        "payment_method": getattr(tx, "payment_method", "CASH"),
        "grand_total": getattr(tx, "grand_total", 0.0),
        "paid_amount": getattr(tx, "paid_amount", getattr(tx, "grand_total", 0.0)),
        "change_amount": getattr(tx, "change_amount", 0.0),
        "items": item_list
    }