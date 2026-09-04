import sys
import logging
from typing import Dict, Any, List
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from escpos.printer import Usb, Dummy
    ESCPOS_AVAILABLE = True
except ImportError:
    ESCPOS_AVAILABLE = False
    logger.warning("Library 'python-escpos' belum terinstall. Mode simulasi/fallback aktif.")


class ThermalPrinter:
    def __init__(self, vendor_id: int = 0x04b8, product_id: int = 0x0e15, width_chars: int = 32):
        """
        Inisialisasi koneksi printer thermal USB ESC/POS.
        
        :param vendor_id: Vendor ID USB printer (contoh: 0x04b8 untuk Epson, 0x0483 untuk Xprinter/POS58)
        :param product_id: Product ID USB printer
        :param width_chars: Lebar karakter per baris (32 karakter untuk kertas 58mm, 48 karakter untuk 80mm)
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.width_chars = width_chars
        self.printer = None

    def connect(self) -> bool:
        """Membuka koneksi hardware ke printer thermal USB."""
        if not ESCPOS_AVAILABLE:
            return False
        
        try:
            # Mencoba hubungi printer via USB Direct
            self.printer = Usb(idVendor=self.vendor_id, idProduct=self.product_id, timeout=0, in_ep=0x81, out_ep=0x01)
            logger.info("Berhasil terhubung ke printer thermal USB.")
            return True
        except Exception as e:
            logger.error(f"Gagal terhubung ke printer thermal USB: {e}")
            self.printer = None
            return False

    def format_line_two_columns(self, left_text: str, right_text: str) -> str:
        """Membuat susunan teks rapi 2 kolom (kiri & kanan) sesuai lebar kertas."""
        space_count = self.width_chars - (len(left_text) + len(right_text))
        if space_count < 1:
            # Jika teks terlalu panjang, potong teks sebelah kiri
            max_left = self.width_chars - len(right_text) - 1
            left_text = left_text[:max_left]
            space_count = 1
        return left_text + (" " * space_count) + right_text

    def print_receipt(
        self, 
        transaction_data: Dict[str, Any], 
        store_info: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Mencetak struk belanja berdasarkan dictionary transaksi.
        
        Structure transaction_data expected:
        {
            "invoice_number": "INV/20260824/0001",
            "created_at": "24-08-2026 12:00",
            "cashier_name": "Kasir 1",
            "items": [
                {"name": "Kopi Susu 250ml", "qty": 2, "price": 15000, "subtotal": 30000}
            ],
            "grand_total": 30000,
            "cash_amount": 50000,
            "change_amount": 20000
        }
        """
        if store_info is None:
            store_info = {
                "name": "TOKO POS SAYA",
                "address": "Jl. Raya Utama No. 123",
                "phone": "0812-3456-7890",
                "footer": "Terima kasih telah berbelanja!"
            }

        # Coba koneksi jika belum terhubung
        connected = self.connect()

        # Gunakan Dummy jika printer hardware tidak terdeteksi (agar tidak throw error)
        p = self.printer if connected else (Dummy() if ESCPOS_AVAILABLE else None)

        if not p:
            logger.info("=== SIMULASI CETAK STRUK (NO HARDWARE) ===")
            print(self.generate_plain_text_receipt(transaction_data, store_info))
            return False

        try:
            # Header Toko
            p.set(align='center', bold=True, width=1, height=1)
            p.text(f"{store_info['name']}\n")
            p.set(align='center', bold=False)
            p.text(f"{store_info['address']}\n")
            p.text(f"Telp: {store_info['phone']}\n")
            p.text("-" * self.width_chars + "\n")

            # Informasi Transaksi
            p.set(align='left')
            p.text(f"No  : {transaction_data.get('invoice_number', '-')}\n")
            p.text(f"Tgl : {transaction_data.get('created_at', '-')}\n")
            p.text(f"Ksr : {transaction_data.get('cashier_name', 'Kasir')}\n")
            p.text("=" * self.width_chars + "\n")

            # Rincian Barang
            for item in transaction_data.get('items', []):
                name = item.get('name', 'Barang')
                qty = item.get('qty', 1)
                price = float(item.get('price', 0))
                subtotal = float(item.get('subtotal', price * qty))

                p.text(f"{name}\n")
                qty_price_str = f"  {qty} x {price:,.0f}"
                subtotal_str = f"{subtotal:,.0f}"
                p.text(self.format_line_two_columns(qty_price_str, subtotal_str) + "\n")

            p.text("-" * self.width_chars + "\n")

            # Total & Pembayaran
            grand_total = float(transaction_data.get('grand_total', 0))
            cash_amount = float(transaction_data.get('cash_amount', 0))
            change_amount = float(transaction_data.get('change_amount', 0))

            p.set(bold=True)
            p.text(self.format_line_two_columns("TOTAL", f"Rp {grand_total:,.0f}") + "\n")
            p.set(bold=False)
            p.text(self.format_line_two_columns("TUNAI", f"Rp {cash_amount:,.0f}") + "\n")
            p.text(self.format_line_two_columns("KEMBALI", f"Rp {change_amount:,.0f}") + "\n")
            p.text("=" * self.width_chars + "\n")

            # Footer
            p.set(align='center')
            p.text(f"{store_info['footer']}\n\n\n")

            # Cut Paper (Potong Kertas Automatic jika didukung hardware)
            p.cut()
            return True

        except Exception as e:
            logger.error(f"Gagal melakukan percetakan ke printer: {e}")
            return False

    def generate_plain_text_receipt(self, transaction_data: Dict[str, Any], store_info: Dict[str, str]) -> str:
        """Fungsi fallback untuk menghasilkan string teks polos (untuk debugging/preview)."""
        lines = []
        lines.append(store_info['name'].center(self.width_chars))
        lines.append(store_info['address'].center(self.width_chars))
        lines.append(f"Telp: {store_info['phone']}".center(self.width_chars))
        lines.append("-" * self.width_chars)
        lines.append(f"No  : {transaction_data.get('invoice_number', '-')}")
        lines.append(f"Tgl : {transaction_data.get('created_at', '-')}")
        lines.append("=" * self.width_chars)

        for item in transaction_data.get('items', []):
            lines.append(item.get('name', 'Barang'))
            qty_price = f"  {item.get('qty', 1)} x {float(item.get('price', 0)):,.0f}"
            subtotal = f"{float(item.get('subtotal', 0)):,.0f}"
            lines.append(self.format_line_two_columns(qty_price, subtotal))

        lines.append("-" * self.width_chars)
        lines.append(self.format_line_two_columns("TOTAL", f"Rp {float(transaction_data.get('grand_total', 0)):,.0f}"))
        lines.append(self.format_line_two_columns("TUNAI", f"Rp {float(transaction_data.get('cash_amount', 0)):,.0f}"))
        lines.append(self.format_line_two_columns("KEMBALI", f"Rp {float(transaction_data.get('change_amount', 0)):,.0f}"))
        lines.append("=" * self.width_chars)
        lines.append(store_info['footer'].center(self.width_chars))
        return "\n".join(lines)


# Pengujian Mandiri
if __name__ == "__main__":
    printer_service = ThermalPrinter(width_chars=32)
    sample_transaction = {
        "invoice_number": "INV/20260824/0001",
        "created_at": "24-08-2026 12:00",
        "cashier_name": "Kasir 1",
        "items": [
            {"name": "Kopi Susu Bottle 250ml", "qty": 2, "price": 15000, "subtotal": 30000}
        ],
        "grand_total": 30000,
        "cash_amount": 50000,
        "change_amount": 20000
    }
    printer_service.print_receipt(sample_transaction)