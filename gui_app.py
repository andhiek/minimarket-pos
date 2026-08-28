import sys
import requests
from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import datetime
from receipt_printer import ReceiptPrinter, ReceiptSettingsDialog

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QComboBox, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# ==============================================================================
# DYNAMIC IMPORTS & FALLBACK DIALOGS
# ==============================================================================
try:
    from product_management import ProductManagementDialog
except ImportError:
    class MockProductManagementDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Kelola Produk")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Modul product_management.py tidak ditemukan."))
    ProductManagementDialog = MockProductManagementDialog  # type: ignore

try:
    from sales_report import SalesReportDialog
except ImportError:
    class MockSalesReportDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Laporan Harian")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Modul sales_report.py tidak ditemukan."))
    SalesReportDialog = MockSalesReportDialog  # type: ignore

try:
    from user_management import UserManagementDialog
except ImportError:
    class MockUserManagementDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Manajemen User")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Modul user_management.py tidak ditemukan."))
    UserManagementDialog = MockUserManagementDialog  # type: ignore
    
try:
    from customer_management import CustomerManagementDialog
except ImportError:
    class MockCustomerManagementDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Manajemen Member")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Modul customer_management.py tidak ditemukan."))
    CustomerManagementDialog = MockCustomerManagementDialog  # type: ignore

API_URL = "http://127.0.0.1:8000/api"

class HelpDialog(QDialog):
    """Dialog Panduan Penggunaan & Shortcut Keyboard POS"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Panduan & Shortcut Kasir")
        self.resize(480, 420)
        self.setMinimumSize(400, 320)

        layout = QVBoxLayout(self)

        lbl_title = QLabel("📖 PANDUAN PENGGUNAAN POS")
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        help_text = """
<b>⌨️ SHORTCUT KEYBOARD (TOMBOL CEPAT)</b><br>
• <b>[F2]</b> : Focus langsung ke kolom Scan Barcode<br>
• <b>[F5]</b> : Eksekusi Proses Bayar (Checkout)<br>
• <b>[Delete]</b> : Hapus item produk yang dipilih dari keranjang<br>
• <b>[Enter]</b> : Scan Barcode / Cari Member / Cetak Struk<br>
<hr>
<b>🛒 ALUR TRANSAKSI KASIR</b><br>
1. <b>Scan Barang</b>: Tembakkan Barcode Scanner ke produk. Jika kursor lepas, tekan <b>F2</b>.<br>
2. <b>Input Member</b> (Opsional): Masukkan No. HP pelanggan lalu tekan Enter.<br>
3. <b>Bayar</b>: Masukkan Uang Dibayar (dan Diskon jika ada).<br>
4. <b>Selesaikan</b>: Tekan <b>F5</b> untuk mencetak struk & mereset keranjang.<br>
<hr>
<b>⏸️ FITUR TAHAN TRANSAKSI (HOLD)</b><br>
• Klik <b>Tahan Transaksi</b> jika pembeli ingin mengambil barang tambahan.<br>
• Klik <b>Buka Pending</b> untuk melanjutkan transaksi yang ditahan.
        """

        lbl_content = QLabel(help_text)
        lbl_content.setWordWrap(True)
        lbl_content.setStyleSheet("background-color: #1e293b; padding: 12px; border-radius: 6px; color: #f8fafc;")
        layout.addWidget(lbl_content)

        btn_close = QPushButton("Tutup Panduan")
        btn_close.setObjectName("btnPrimary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login Kasir / User")
        self.resize(360, 250)
        self.setMinimumSize(320, 220)
        self.user_data: Optional[Dict[str, Any]] = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl_title = QLabel("LOGIN KASIR POS")
        lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        layout.addWidget(QLabel("Username / ID Kasir:"))
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Masukkan username...")
        layout.addWidget(self.input_username)

        layout.addWidget(QLabel("Password / PIN:"))
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Masukkan password / PIN...")
        self.input_password.returnPressed.connect(self.handle_login)
        layout.addWidget(self.input_password)

        self.btn_login = QPushButton("LOGIN")
        self.btn_login.setObjectName("btnPrimary")
        self.btn_login.clicked.connect(self.handle_login)
        layout.addWidget(self.btn_login)

    def handle_login(self) -> None:
        username = self.input_username.text().strip()
        password = self.input_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Peringatan", "Username dan Password wajib diisi!")
            return

        try:
            payload = {"username": username, "password": password}
            response = requests.post(f"{API_URL}/auth/login", json=payload, timeout=5)

            if response.status_code == 200:
                self.user_data = response.json()
                self.accept()
            else:
                try:
                    err_msg = response.json().get("detail", "Username atau Password salah!")
                except Exception:
                    err_msg = f"Gagal login (Status {response.status_code})"
                QMessageBox.warning(self, "Gagal Login", err_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error Koneksi", f"Gagal terhubung ke backend:\n{str(e)}")


DARK_STYLE_SHEET = """
QWidget { background-color: #1e293b; color: #f8fafc; font-family: "Segoe UI", Arial, sans-serif; font-size: 13px; }
QMainWindow, QDialog { background-color: #0f172a; }
QLabel { color: #cbd5e1; }
QLabel#headerTitle { color: #f8fafc; font-size: 18px; font-weight: bold; }
QLabel#userBadge { background-color: #1e3a8a; color: #60a5fa; border: 1px solid #2563eb; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: bold; }
QLineEdit, QComboBox { background-color: #334155; border: 1px solid #475569; border-radius: 6px; color: #ffffff; padding: 6px 10px; font-size: 12px; }
QLineEdit:focus, QComboBox:focus { border: 2px solid #3b82f6; background-color: #1e293b; }
QTableWidget { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; gridline-color: #334155; color: #f8fafc; font-size: 12px; }
QHeaderView::section { background-color: #0f172a; color: #94a3b8; padding: 8px; font-weight: bold; border: none; border-bottom: 2px solid #334155; font-size: 12px; }

/* PENYESUAIAN UKURAN FONT PADA TOMBOL */
QPushButton { background-color: #334155; color: #f8fafc; border: none; border-radius: 6px; padding: 7px 12px; font-size: 12px; font-weight: bold; }
QPushButton:hover { background-color: #475569; }
QPushButton#btnPrimary { background-color: #2563eb; color: #ffffff; }
QPushButton#btnPrimary:hover { background-color: #1d4ed8; }
QPushButton#btnSecondary { background-color: #334155; color: #f8fafc; border: 1px solid #475569; }
QPushButton#btnSecondary:hover { background-color: #475569; }
QPushButton#btnSwitch { background-color: #d97706; color: #ffffff; padding: 4px 10px; font-size: 11px; }
QPushButton#btnSwitch:hover { background-color: #b45309; }
QPushButton#btnDanger { background-color: #dc2626; color: #ffffff; }
QPushButton#btnDanger:hover { background-color: #b91c1c; }
QPushButton#btnHold { background-color: #d97706; color: #ffffff; }
QPushButton#btnHold:hover { background-color: #b45309; }
QPushButton#btnCheckout { background-color: #16a34a; color: #ffffff; font-size: 14px; padding: 10px; border-radius: 8px; font-weight: bold; }
QPushButton#btnCheckout:hover { background-color: #15803d; }
QLabel#totalLabel { color: #38bdf8; background-color: #0f172a; border: 2px solid #0284c7; border-radius: 8px; padding: 10px; }
QLabel#changeLabel { font-size: 16px; font-weight: bold; }

/* DUDUKAN RAPAH TOMBOL HELP */
QPushButton#btnHelpIcon {
    background-color: #0284c7;
    color: #ffffff;
    font-size: 12px;
    font-weight: bold;
    border-radius: 13px;
    padding: 0px;
}
QPushButton#btnHelpIcon:hover {
    background-color: #0369a1;
}
"""

class ReprintDialog(QDialog):
    """Dialog untuk mencari transaksi lama dan mencetak ulang struknya"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cetak Ulang Struk Transaksi")
        self.resize(450, 180)
        self.setMinimumSize(350, 150)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Masukkan Nomor Struk / Invoice (misal: TRX-1001):"))
        self.input_invoice = QLineEdit()
        self.input_invoice.setPlaceholderText("TRX-...")
        self.input_invoice.returnPressed.connect(self.reprint_invoice)
        layout.addWidget(self.input_invoice)

        btn_layout = QHBoxLayout()
        self.btn_search_print = QPushButton("📄 Cari & Cetak Struk")
        self.btn_search_print.setObjectName("btnPrimary")
        self.btn_search_print.clicked.connect(self.reprint_invoice)
        btn_layout.addWidget(self.btn_search_print)

        layout.addLayout(btn_layout)

    def reprint_invoice(self) -> None:
        inv_number = self.input_invoice.text().strip()
        if not inv_number:
            QMessageBox.warning(self, "Peringatan", "Nomor struk tidak boleh kosong!")
            return

        try:
            res = requests.get(f"{API_URL}/pos/transaction/{inv_number}", timeout=5)
            if res.status_code == 200:
                trx_data = res.json()
                
                formatted_receipt = {
                    "trx_id": trx_data.get("invoice_number", inv_number),
                    "date": trx_data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
                    "cashier": trx_data.get("cashier_name", "Kasir"),
                    "customer_name": trx_data.get("customer_name", "Umum"),
                    "items": trx_data.get("items", []),
                    "subtotal": float(trx_data.get("subtotal", 0)),
                    "discount": float(trx_data.get("discount", 0)),
                    "total": float(trx_data.get("grand_total", 0)),
                    "paid": float(trx_data.get("paid_amount", 0)),
                    "change": float(trx_data.get("change_amount", 0))
                }

                printer = ReceiptPrinter()
                printer.print_receipt(formatted_receipt, self)
                self.accept()
            else:
                QMessageBox.warning(self, "Tidak Ditemukan", f"Transaksi '{inv_number}' tidak ditemukan!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal terhubung ke server: {e}")


class POSMainWindow(QMainWindow):
    def __init__(self, current_user: Dict[str, Any]) -> None:
        super().__init__()
        self.current_user = current_user
        self.current_member: Optional[Dict[str, Any]] = None
        self.pending_transactions: List[Dict[str, Any]] = []

        display_name = self.current_user.get('full_name') or self.current_user.get('username', 'Kasir')
        user_role = str(self.current_user.get('role', 'kasir')).upper()

        self.setWindowTitle(f"Minimarket Billing & POS System - [{display_name} ({user_role})]")
        
        self.resize(1180, 760)
        self.setMinimumSize(950, 620)

        self.cart: List[Dict[str, Any]] = []
        self.subtotal_amount: Decimal = Decimal('0.00')
        self.discount_amount: Decimal = Decimal('0.00')
        self.grand_total: Decimal = Decimal('0.00')

        self.init_ui()
        
    def keyPressEvent(self, event) -> None:
        """Shortcut Keyboard Kasir"""
        key = event.key()
        
        # F5 -> Process Checkout
        if key == Qt.Key.Key_F5:
            self.process_checkout()
        # F2 -> Focus ke input barcode
        elif key == Qt.Key.Key_F2:
            self.barcode_input.setFocus()
            self.barcode_input.selectAll()
        # Delete -> Hapus item terpilih di tabel
        elif key == Qt.Key.Key_Delete:
            self.delete_selected_item()
        else:
            super().keyPressEvent(event)
            
    def open_help_dialog(self) -> None:
        """Handler untuk membuka dialog bantuan kasir"""
        dialog = HelpDialog(self)
        dialog.exec()

    def init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(16)

        # --- LEFT PANEL ---
        left_layout = QVBoxLayout()

        # Header Top Layout (Judul + Help + User Badge + Switch)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("KASIR MINIMARKET")
        title_label.setObjectName("headerTitle")
        header_layout.addWidget(title_label)

        # Tombol Help disandingkan langsung dengan Judul
        self.btn_help = QPushButton("❓")
        self.btn_help.setObjectName("btnHelpIcon")
        self.btn_help.setFixedSize(26, 26)
        self.btn_help.setToolTip("Buka Panduan & Shortcut Kasir")
        self.btn_help.clicked.connect(self.open_help_dialog)
        header_layout.addWidget(self.btn_help)

        header_layout.addStretch()

        user_name = self.current_user.get('full_name') or self.current_user.get('username', 'Kasir')
        lbl_user = QLabel(f"👤 {user_name}")
        lbl_user.setObjectName("userBadge")
        header_layout.addWidget(lbl_user)

        btn_switch_user = QPushButton("🔒 Switch User")
        btn_switch_user.setObjectName("btnSwitch")
        btn_switch_user.clicked.connect(self.switch_user)
        header_layout.addWidget(btn_switch_user)

        left_layout.addLayout(header_layout)

        # Barcode & Member Row
        scan_layout = QHBoxLayout()
        scan_layout.addWidget(QLabel("Scan Barcode:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan barcode lalu tekan Enter...")
        self.barcode_input.returnPressed.connect(self.scan_barcode)
        scan_layout.addWidget(self.barcode_input)

        btn_tambah = QPushButton("Tambah")
        btn_tambah.setObjectName("btnPrimary")
        btn_tambah.clicked.connect(self.scan_barcode)
        scan_layout.addWidget(btn_tambah)
        left_layout.addLayout(scan_layout)

        # Member Info Input Row
        member_layout = QHBoxLayout()
        member_layout.addWidget(QLabel("No. HP Member:"))
        self.input_member_phone = QLineEdit()
        self.input_member_phone.setPlaceholderText("Masukkan No. HP Member...")
        self.input_member_phone.returnPressed.connect(self.search_member)
        btn_search_member = QPushButton("Cari Member")
        btn_search_member.setObjectName("btnPrimary")
        btn_search_member.clicked.connect(self.search_member)

        member_layout.addWidget(self.input_member_phone)
        member_layout.addWidget(btn_search_member)
        left_layout.addLayout(member_layout)

        self.label_member_info = QLabel("Status Member: Non-Member")
        self.label_member_info.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px;")
        left_layout.addWidget(self.label_member_info)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Barcode", "Nama Produk", "Harga (Rp)", "Qty", "Subtotal (Rp)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.table)

        # Bottom Action Buttons (Left Panel)
        bottom_left_btn_layout = QHBoxLayout()

        self.btn_delete_item = QPushButton("Hapus Item [Del]")
        self.btn_delete_item.setObjectName("btnDanger")
        self.btn_delete_item.clicked.connect(self.delete_selected_item)
        bottom_left_btn_layout.addWidget(self.btn_delete_item)

        self.btn_hold = QPushButton("Tahan Transaksi (Hold)")
        self.btn_hold.setObjectName("btnHold")
        self.btn_hold.clicked.connect(self.hold_transaction)
        bottom_left_btn_layout.addWidget(self.btn_hold)

        self.btn_pending = QPushButton("Buka Pending (0)")
        self.btn_pending.setObjectName("btnSecondary")
        self.btn_pending.clicked.connect(self.open_pending_transactions)
        bottom_left_btn_layout.addWidget(self.btn_pending)

        left_layout.addLayout(bottom_left_btn_layout)
        main_layout.addLayout(left_layout, stretch=2)

        # --- RIGHT PANEL ---
        right_layout = QVBoxLayout()

        right_layout.addWidget(QLabel("TOTAL BELANJA / GRAND TOTAL"))
        self.label_grand_total = QLabel("Rp 0")
        self.label_grand_total.setObjectName("totalLabel")
        self.label_grand_total.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.label_grand_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.label_grand_total)

        right_layout.addWidget(QLabel("Diskon Nominal (Rp):"))
        self.input_discount = QLineEdit()
        self.input_discount.setPlaceholderText("0")
        self.input_discount.textChanged.connect(self.update_totals)
        right_layout.addWidget(self.input_discount)

        right_layout.addWidget(QLabel("Metode Pembayaran:"))
        self.combo_payment = QComboBox()
        self.combo_payment.addItems(["CASH", "QRIS", "DEBIT"])
        right_layout.addWidget(self.combo_payment)

        right_layout.addWidget(QLabel("Uang Dibayar (Rp):"))
        self.input_paid = QLineEdit()
        self.input_paid.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.input_paid.textChanged.connect(self.calculate_change)
        right_layout.addWidget(self.input_paid)

        right_layout.addWidget(QLabel("Kembalian:"))
        self.label_change = QLabel("Rp 0")
        self.label_change.setObjectName("changeLabel")
        right_layout.addWidget(self.label_change)
        
        self.btn_reprint = QPushButton("🔄 Cetak Ulang Struk")
        self.btn_reprint.setObjectName("btnSecondary")
        self.btn_reprint.clicked.connect(self.open_reprint_dialog)
        right_layout.addWidget(self.btn_reprint)

        right_layout.addStretch()

        self.btn_checkout = QPushButton("PROSES BAYAR [F5]")
        self.btn_checkout.setObjectName("btnCheckout")
        self.btn_checkout.clicked.connect(self.process_checkout)
        right_layout.addWidget(self.btn_checkout)

        # Management Dialog Buttons (Right Panel)
        self.btn_manage_products = QPushButton("Kelola Produk (Admin)")
        self.btn_manage_products.setObjectName("btnSecondary")
        self.btn_manage_products.clicked.connect(self.open_product_management)
        right_layout.addWidget(self.btn_manage_products)
        
        self.btn_manage_customers = QPushButton("Manajemen Member & Poin")
        self.btn_manage_customers.setObjectName("btnSecondary")
        self.btn_manage_customers.clicked.connect(self.open_customer_management)
        right_layout.addWidget(self.btn_manage_customers)

        self.btn_sales_report = QPushButton("Laporan Harian / Laba")
        self.btn_sales_report.setObjectName("btnSecondary")
        self.btn_sales_report.clicked.connect(self.open_sales_report)
        right_layout.addWidget(self.btn_sales_report)

        self.btn_manage_users = QPushButton("Manajemen User (Admin)")
        self.btn_manage_users.setObjectName("btnSecondary")
        self.btn_manage_users.clicked.connect(self.open_user_management)
        right_layout.addWidget(self.btn_manage_users)
        
        self.btn_receipt_settings = QPushButton("⚙️ Setting Struk")
        self.btn_receipt_settings.setObjectName("btnSecondary")
        self.btn_receipt_settings.clicked.connect(self.open_receipt_settings)
        right_layout.addWidget(self.btn_receipt_settings)

        main_layout.addLayout(right_layout, stretch=1)
        self.barcode_input.setFocus()

    # --- ACTIONS & LOGIC ---
    def switch_user(self) -> None:
        reply = QMessageBox.question(
            self, "Switch User", "Apakah Anda yakin ingin keluar dan mengganti akun?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            login = LoginDialog()
            if login.exec() == QDialog.DialogCode.Accepted and login.user_data:
                self.__init__(current_user=login.user_data)
                self.show()

    def search_member(self) -> None:
        phone = self.input_member_phone.text().strip()
        if not phone:
            self.current_member = None
            self.label_member_info.setText("Status Member: Non-Member")
            self.label_member_info.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px;")
            return

        try:
            res = requests.get(f"{API_URL}/customers/phone/{phone}")
            if res.status_code == 200:
                member_data = res.json()
                self.current_member = member_data
                self.label_member_info.setText(
                    f"Member: {member_data['name']} | Total Poin: {member_data['points']} Poin"
                )
                self.label_member_info.setStyleSheet("color: #22c55e; font-weight: bold; font-size: 11px;")
            else:
                self.current_member = None
                self.label_member_info.setText("Status: Member Tidak Ditemukan!")
                self.label_member_info.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal mengecek member: {e}")

    def scan_barcode(self) -> None:
        barcode = self.barcode_input.text().strip()
        if not barcode:
            return

        try:
            res = requests.get(f"{API_URL}/products/barcode/{barcode}")
            if res.status_code == 200:
                product = res.json()
                self.add_product_to_cart(product)
                self.barcode_input.clear()
            else:
                QMessageBox.warning(self, "Tidak Ditemukan", "Produk tidak terdaftar!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal terhubung ke server: {e}")

    def add_product_to_cart(self, product: Dict[str, Any]) -> None:
        for item in self.cart:
            if item['product_id'] == product['id']:
                item['qty'] += 1
                item['subtotal'] = Decimal(str(item['price'])) * item['qty']
                self.update_cart_table()
                return

        self.cart.append({
            'product_id': product['id'],
            'barcode': product['barcode'],
            'name': product['name'],
            'price': Decimal(str(product['price'])),
            'qty': 1,
            'subtotal': Decimal(str(product['price']))
        })
        self.update_cart_table()

    def update_cart_table(self) -> None:
        self.table.setRowCount(0)
        self.subtotal_amount = Decimal('0.00')

        for row_idx, item in enumerate(self.cart):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(item['barcode'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(item['name'])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{item['price']:,}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(item['qty'])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{item['subtotal']:,}"))

            self.subtotal_amount += item['subtotal']

        self.update_totals()

    def delete_selected_item(self) -> None:
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.cart.pop(current_row)
            self.update_cart_table()
        else:
            QMessageBox.warning(self, "Peringatan", "Pilih item yang ingin dihapus terlebih dahulu!")

    def hold_transaction(self) -> None:
        if not self.cart:
            QMessageBox.warning(self, "Peringatan", "Keranjang belanja kosong!")
            return

        self.pending_transactions.append({
            "cart": self.cart.copy(),
            "member": self.current_member,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

        self.cart = []
        self.current_member = None
        self.input_member_phone.clear()
        self.label_member_info.setText("Status Member: Non-Member")
        self.update_cart_table()

        self.btn_pending.setText(f"Buka Pending ({len(self.pending_transactions)})")
        QMessageBox.information(self, "Transaksi Ditahan", "Transaksi berhasil ditahan/pending.")

    def open_pending_transactions(self) -> None:
        if not self.pending_transactions:
            QMessageBox.information(self, "Info", "Tidak ada transaksi yang ditahan.")
            return

        last_pending = self.pending_transactions.pop()
        self.cart = last_pending["cart"]
        self.current_member = last_pending["member"]
        if self.current_member:
            self.input_member_phone.setText(self.current_member.get('phone', ''))
            self.label_member_info.setText(f"Member: {self.current_member['name']}")
        self.update_cart_table()

        self.btn_pending.setText(f"Buka Pending ({len(self.pending_transactions)})")

    def update_totals(self) -> None:
        try:
            disc_str = self.input_discount.text().replace(',', '').replace('.', '')
            self.discount_amount = Decimal(disc_str) if disc_str else Decimal('0')
        except Exception:
            self.discount_amount = Decimal('0')

        self.grand_total = max(Decimal('0'), self.subtotal_amount - self.discount_amount)
        self.label_grand_total.setText(f"Rp {self.grand_total:,.0f}")
        self.calculate_change()

    def calculate_change(self) -> None:
        try:
            paid_str = self.input_paid.text().replace(',', '').replace('.', '')
            paid_val = Decimal(paid_str) if paid_str else Decimal('0')
            change = paid_val - self.grand_total

            if change >= 0:
                self.label_change.setText(f"Rp {change:,.0f}")
                self.label_change.setStyleSheet("color: #22c55e;")
            else:
                self.label_change.setText(f"Kurang Rp {abs(change):,.0f}")
                self.label_change.setStyleSheet("color: #ef4444;")
        except Exception:
            self.label_change.setText("Rp 0")

    def process_checkout(self) -> None:
        if not self.cart:
            QMessageBox.warning(self, "Peringatan", "Keranjang belanja kosong!")
            return

        try:
            paid_str = self.input_paid.text().replace(',', '').replace('.', '')
            paid_val = Decimal(paid_str) if paid_str else Decimal('0')

            if paid_val < self.grand_total:
                QMessageBox.warning(self, "Gagal", "Uang pembayarannya kurang!")
                return

            customer_phone = self.current_member['phone'] if self.current_member else None

            payload = {
                "cashier_id": self.current_user.get("id", 1),
                "cashier_name": self.current_user.get("full_name") or self.current_user.get("username", "Kasir"),
                "customer_phone": customer_phone,
                "cart_items": [{"product_id": item['product_id'], "quantity": item['qty']} for item in self.cart],
                "paid_amount": float(paid_val),
                "discount_amount": float(self.discount_amount),
                "payment_method": self.combo_payment.currentText()
            }

            res = requests.post(f"{API_URL}/pos/checkout", json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                msg = (
                    f"No. Struk: {data['invoice_number']}\n"
                    f"Member: {data.get('customer_name', 'Umum')}\n"
                    f"Total: Rp {data['grand_total']:,.0f}\n"
                    f"Diskon: Rp {data['discount']:,.0f}\n"
                    f"Kembalian: Rp {data['change_amount']:,.0f}\n"
                )
                if data.get('points_earned', 0) > 0:
                    msg += f"\n🎉 Poin Diperoleh: +{data['points_earned']} Poin!"

                QMessageBox.information(self, "Transaksi Sukses", msg)

                # --- INTEGRASI CETAK STRUK OTOMATIS ---
                trx_receipt_data = {
                    "trx_id": data.get("invoice_number", "TRX-0000"),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "cashier": self.current_user.get("full_name") or self.current_user.get("username", "Kasir"),
                    "customer_name": data.get("customer_name", "Umum"),
                    "items": self.cart,
                    "subtotal": float(self.subtotal_amount),
                    "discount": float(self.discount_amount),
                    "total": float(self.grand_total),
                    "paid": float(paid_val),
                    "change": float(paid_val - self.grand_total)
                }
                
                # Panggil modul printer
                self.print_transaction_receipt(trx_receipt_data)

                # Reset Form Belanja
                self.cart = []
                self.current_member = None
                self.input_member_phone.clear()
                self.input_discount.clear()
                self.input_paid.clear()
                self.label_member_info.setText("Status Member: Non-Member")
                self.label_member_info.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px;")
                self.update_cart_table()
                self.barcode_input.setFocus()
            else:
                QMessageBox.critical(self, "Gagal", res.json().get('detail', 'Terjadi kesalahan'))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memproses transaksi: {e}")

    # Open Dialog Methods
    def open_reprint_dialog(self) -> None:
        """Handler untuk membuka dialog cetak ulang struk"""
        dialog = ReprintDialog(self)
        dialog.exec()

    def open_product_management(self) -> None:
        dialog = ProductManagementDialog(self)
        dialog.exec()

    def open_sales_report(self) -> None:
        dialog = SalesReportDialog(self)
        dialog.exec()

    def open_user_management(self) -> None:
        dialog = UserManagementDialog(self)
        dialog.exec()
        
    def open_customer_management(self) -> None:
        dialog = CustomerManagementDialog(self)
        dialog.exec()
        # Refresh status member aktif jika ada
        if self.current_member:
            self.search_member()
            
    def open_receipt_settings(self) -> None:
        dialog = ReceiptSettingsDialog(self)
        dialog.exec()

    def print_transaction_receipt(self, transaction_data: dict) -> None:
        """Dipanggil setelah transaksi pembayaran berhasil"""
        printer = ReceiptPrinter()
        printer.print_receipt(transaction_data, self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE_SHEET)

    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.DialogCode.Accepted and login_dialog.user_data:
        window = POSMainWindow(current_user=login_dialog.user_data)
        window.show()
    sys.exit(app.exec())