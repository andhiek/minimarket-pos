from sqlmodel import Session, select, create_engine
from main import Product, Customer, engine

def populate_test_data():
    sample_products = [
        Product(barcode="899110100001", name="Indomie Goreng Original 85g", price=3100.0, purchase_price=2700.0, stock=120, category="Makanan"),
        Product(barcode="899110100002", name="Pop Mie Rasa Ayam Bawang 75g", price=5500.0, purchase_price=4500.0, stock=48, category="Makanan"),
        Product(barcode="899110100003", name="Roti Tawar Kupas Sari Roti", price=15500.0, purchase_price=13000.0, stock=15, category="Makanan"),
        Product(barcode="899110100004", name="Aqua Air Mineral 600ml", price=3500.0, purchase_price=2800.0, stock=100, category="Minuman"),
        Product(barcode="899110100005", name="Teh Botol Sosro Sosro 450ml", price=6500.0, purchase_price=5000.0, stock=60, category="Minuman"),
        Product(barcode="899110100006", name="Ultra Milk Rasa Cokelat 250ml", price=7000.0, purchase_price=5800.0, stock=40, category="Minuman"),
        Product(barcode="899110100007", name="Kopi Kapal Api Grande 20g", price=1800.0, purchase_price=1200.0, stock=150, category="Minuman"),
        Product(barcode="899110100008", name="Sabun Biore Body Wash 450ml", price=25500.0, purchase_price=21000.0, stock=20, category="Perawatan Diri"),
        Product(barcode="899110100009", name="Shampoo Pantene Hairfall 160ml", price=23000.0, purchase_price=19500.0, stock=25, category="Perawatan Diri"),
        Product(barcode="899110100010", name="Pepsodent Herbal 190g", price=14500.0, purchase_price=1200.0, stock=30, category="Perawatan Diri"),
        Product(barcode="899110100011", name="Minyak Goreng Bimoli 2L", price=36000.0, purchase_price=32500.0, stock=24, category="Sembako"),
        Product(barcode="899110100012", name="Gula Pasir Gulaku 1kg", price=17500.0, purchase_price=15000.0, stock=50, category="Sembako"),
        Product(barcode="899110100013", name="Beras Ramos Super 5kg", price=74000.0, purchase_price=68000.0, stock=10, category="Sembako"),
        Product(barcode="899110100014", name="Chitato Rasa Sapi Panggang 68g", price=10000.0, purchase_price=8200.0, stock=35, category="Snack"),
        Product(barcode="899110100015", name="Oreo Vanilla Sandwich 133g", price=9500.0, purchase_price=7500.0, stock=40, category="Snack"),
    ]

    sample_customers = [
        Customer(phone="081234567890", name="Budi Santoso", points=250),
        Customer(phone="085712345678", name="Siti Aminah", points=80),
        Customer(phone="089987654321", name="Dewi Lestari", points=500),
    ]

    with Session(engine) as session:
        for p in sample_products:
            if not session.exec(select(Product).where(Product.barcode == p.barcode)).first():
                session.add(p)
        
        for c in sample_customers:
            if not session.exec(select(Customer).where(Customer.phone == c.phone)).first():
                session.add(c)
                
        session.commit()
        print("✅ Data produk & member dummy berhasil ditambahkan!")

if __name__ == "__main__":
    populate_test_data()