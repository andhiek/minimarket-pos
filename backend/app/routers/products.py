from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, col, or_

from app.database import get_db
from app.models.pos_models import Product

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=List[Product])
def get_all_products(session: Session = Depends(get_db)):
    products = session.exec(select(Product)).all()
    return products


@router.get("/search", response_model=List[Product])
def search_products(
    q: Optional[str] = Query(None, description="Cari berdasarkan barcode atau nama"),
    session: Session = Depends(get_db),
):
    if not q:
        return session.exec(select(Product)).all()

    statement = select(Product).where(
        or_(
            Product.barcode == q,
            col(Product.name).ilike(f"%{q}%")
        )
    )
    return session.exec(statement).all()


@router.get("/barcode/{barcode}", response_model=Product)
def get_product_by_barcode(barcode: str, session: Session = Depends(get_db)):
    statement = select(Product).where(Product.barcode == barcode)
    product = session.exec(statement).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan!")
    return product


@router.post("", response_model=Product)
def create_product(product: Product, session: Session = Depends(get_db)):
    existing = session.exec(select(Product).where(Product.barcode == product.barcode)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Barcode sudah terdaftar!")
    
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int, product_data: Product, session: Session = Depends(get_db)
):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

    update_data = product_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key != "id":  # Hindari overwrite primary key
            setattr(db_product, key, value)

    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
def delete_product(product_id: int, session: Session = Depends(get_db)):
    db_product = session.get(Product, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
        
    session.delete(db_product)
    session.commit()
    return {"message": "Produk berhasil dihapus"}