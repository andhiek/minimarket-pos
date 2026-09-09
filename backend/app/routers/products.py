
import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query,UploadFile,File
from fastapi.responses import StreamingResponse
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

# ==============================================================================
# FITUR BARU: IMPORT & EXPORT CSV PRODUK
# ==============================================================================

@router.post("/import-csv")
async def import_products_csv(file: UploadFile = File(...), session: Session = Depends(get_db)):
    # Validasi jika file tidak ada atau ekstensi bukan .csv
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat .csv")

    content = await file.read()
    try:
        # Decode isi file CSV (UTF-8)
        decoded_content = content.decode("utf-8-sig")
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
    except Exception:
        raise HTTPException(status_code=400, detail="Gagal membaca format file CSV!")

    inserted_count = 0
    updated_count = 0

    for row in csv_reader:
        barcode = row.get("barcode", "").strip() if row.get("barcode") else ""
        name = row.get("name", "").strip() if row.get("name") else ""
        
        if not barcode or not name:
            continue

        price = float(row.get("price", 0))
        purchase_price = float(row.get("purchase_price", 0))
        stock = int(row.get("stock", 0))
        category = row.get("category", "Umum").strip() if row.get("category") else "Umum"

        # Cek apakah produk sudah ada (Update jika ada, Insert jika baru)
        existing = session.exec(select(Product).where(Product.barcode == barcode)).first()
        if existing:
            existing.name = name
            existing.price = price
            existing.purchase_price = purchase_price
            existing.stock = stock
            existing.category = category
            session.add(existing)
            updated_count += 1
        else:
            new_prod = Product(
                barcode=barcode,
                name=name,
                price=price,
                purchase_price=purchase_price,
                stock=stock,
                category=category,
            )
            session.add(new_prod)
            inserted_count += 1

    session.commit()
    return {
        "message": f"Import selesai! {inserted_count} produk baru ditambahkan, {updated_count} produk diperbarui."
    }
    
@router.get("/export-csv")
def export_products_csv(session: Session = Depends(get_db)):
    products = session.exec(select(Product)).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write Header
    writer.writerow(["barcode", "name", "category", "price", "purchase_price", "stock"])

    # Write Data
    for p in products:
        writer.writerow([p.barcode, p.name, p.category or "Umum", p.price, p.purchase_price, p.stock])

    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=daftar_produk.csv"}
    )