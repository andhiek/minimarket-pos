from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.transaction import Transaction, TransactionItem, PaymentMethod


class POSService:
    @staticmethod
    def process_checkout(
        db: Session,
        user_id: int,
        cart_items: list,
        paid_amount: Decimal,
        discount_amount: Decimal = Decimal('0.00'),
        payment_method: PaymentMethod = PaymentMethod.CASH
    ) -> Transaction:
        
        with db.begin():
            total_amount = Decimal('0.00')
            items_to_create = []

            for item in cart_items:
                product = db.query(Product).filter(
                    Product.id == item['product_id'], 
                    Product.is_active == True
                ).with_for_update().first()

                if not product:
                    raise ValueError(f"Produk ID {item['product_id']} tidak ditemukan.")
                
                if product.stock < item['quantity']:
                    raise ValueError(f"Stok '{product.name}' kurang (Tersedia: {product.stock}).")

                subtotal = Decimal(str(product.selling_price)) * item['quantity']
                total_amount += subtotal

                product.stock -= item['quantity']

                items_to_create.append({
                    "product_id": product.id,
                    "quantity": item['quantity'],
                    "price_per_unit": product.selling_price,
                    "subtotal": subtotal
                })

            grand_total = total_amount - discount_amount
            if paid_amount < grand_total:
                raise ValueError(f"Uang pembayaran kurang. Total: {grand_total}, Dibayar: {paid_amount}")

            change_amount = paid_amount - grand_total
            invoice_num = f"INV/{datetime.now().strftime('%Y%m%d')}/{int(datetime.now().timestamp())}"

            transaction = Transaction(
                invoice_number=invoice_num,
                user_id=user_id,
                total_amount=total_amount,
                discount_amount=discount_amount,
                grand_total=grand_total,
                paid_amount=paid_amount,
                change_amount=change_amount,
                payment_method=payment_method
            )
            db.add(transaction)
            db.flush()

            for item_data in items_to_create:
                t_item = TransactionItem(
                    transaction_id=transaction.id,
                    **item_data
                )
                db.add(t_item)

        return transaction