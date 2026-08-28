import requests
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

API_URL = "http://127.0.0.1:8000/api"

class CustomerManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manajemen Member & Tukar Poin")
        self.resize(750, 500)
        self.selected_customer: Optional[Dict[str, Any]] = None
        
        self.init_ui()
        self.load_customers()

    def init_ui(self) -> None:
        layout = QHBoxLayout(self)

        # --- LEFT PANEL: Table & Search ---
        left_layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Cari Member (HP/Nama):"))
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Ketik No HP atau Nama...")
        self.input_search.textChanged.connect(self.filter_customers)
        search_layout.addWidget(self.input_search)
        left_layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["No. HP", "Nama Member", "Total Poin"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemClicked.connect(self.on_table_item_clicked)
        left_layout.addWidget(self.table)

        btn_refresh = QPushButton("🔄 Refresh Data")
        btn_refresh.clicked.connect(self.load_customers)
        left_layout.addWidget(btn_refresh)

        layout.addLayout(left_layout, stretch=2)

        # --- RIGHT PANEL: Register & Redeem ---
        right_layout = QVBoxLayout()

        # Group 1: Tambah Member Baru
        group_add = QGroupBox("Tambah Member Baru")
        group_add_layout = QVBoxLayout(group_add)

        group_add_layout.addWidget(QLabel("No. HP / Telepon:"))
        self.input_new_phone = QLineEdit()
        self.input_new_phone.setPlaceholderText("08xxxxxxxxxx")
        group_add_layout.addWidget(self.input_new_phone)

        group_add_layout.addWidget(QLabel("Nama Lengkap:"))
        self.input_new_name = QLineEdit()
        self.input_new_name.setPlaceholderText("Nama Pelanggan...")
        group_add_layout.addWidget(self.input_new_name)

        btn_save_customer = QPushButton("➕ Simpan Member")
        btn_save_customer.setObjectName("btnPrimary")
        btn_save_customer.clicked.connect(self.register_customer)
        group_add_layout.addWidget(btn_save_customer)

        right_layout.addWidget(group_add)

        # Group 2: Tukar Poin (Redeem)
        group_redeem = QGroupBox("Tukar Poin Member")
        group_redeem_layout = QVBoxLayout(group_redeem)

        self.lbl_selected_info = QLabel("Pilih member dari tabel terlebih dahulu.")
        self.lbl_selected_info.setWordWrap(True)
        self.lbl_selected_info.setStyleSheet("color: #94a3b8; font-weight: bold;")
        group_redeem_layout.addWidget(self.lbl_selected_info)

        group_redeem_layout.addWidget(QLabel("Jumlah Poin Ditukar:"))
        self.spin_points = QSpinBox()
        self.spin_points.setRange(1, 100000)
        self.spin_points.setSingleStep(10)
        self.spin_points.valueChanged.connect(self.calculate_discount_preview)
        group_redeem_layout.addWidget(self.spin_points)

        self.lbl_preview_discount = QLabel("Nilai Diskon: Rp 0")
        self.lbl_preview_discount.setStyleSheet("color: #22c55e; font-weight: bold;")
        group_redeem_layout.addWidget(self.lbl_preview_discount)

        btn_redeem = QPushButton("🎁 Tukar Poin")
        btn_redeem.setObjectName("btnWarning")
        btn_redeem.clicked.connect(self.redeem_points)
        group_redeem_layout.addWidget(btn_redeem)

        right_layout.addWidget(group_redeem)
        right_layout.addStretch()

        layout.addLayout(right_layout, stretch=1)

    def load_customers(self) -> None:
        try:
            res = requests.get(f"{API_URL}/customers", timeout=5)
            if res.status_code == 200:
                self.customers_data = res.json()
                self.populate_table(self.customers_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal mengambil data member: {e}")

    def populate_table(self, data: list) -> None:
        self.table.setRowCount(0)
        for row_idx, item in enumerate(data):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(item.get("phone", ""))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(item.get("name", ""))))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{item.get('points', 0)} Poin"))

    def filter_customers(self) -> None:
        query = self.input_search.text().lower()
        filtered = [
            c for c in self.customers_data 
            if query in c.get("phone", "").lower() or query in c.get("name", "").lower()
        ]
        self.populate_table(filtered)

    def register_customer(self) -> None:
        phone = self.input_new_phone.text().strip()
        name = self.input_new_name.text().strip()

        if not phone or not name:
            QMessageBox.warning(self, "Peringatan", "No. HP dan Nama Wajib Diisi!")
            return

        try:
            payload = {"phone": phone, "name": name, "points": 0}
            res = requests.post(f"{API_URL}/customers", json=payload, timeout=5)
            if res.status_code == 200:
                QMessageBox.information(self, "Sukses", f"Member '{name}' berhasil didaftarkan!")
                self.input_new_phone.clear()
                self.input_new_name.clear()
                self.load_customers()
            else:
                err = res.json().get("detail", "Gagal mendaftar member.")
                QMessageBox.warning(self, "Gagal", err)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal terhubung ke backend: {e}")

    def on_table_item_clicked(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            phone_item = self.table.item(row, 0)
            if phone_item:
                phone = phone_item.text()
                self.selected_customer = next((c for c in self.customers_data if c["phone"] == phone), None)
                if self.selected_customer:
                    self.lbl_selected_info.setText(
                        f"Member: {self.selected_customer['name']}\n"
                        f"Poin Tersedia: {self.selected_customer['points']} Poin"
                    )
                    self.lbl_selected_info.setStyleSheet("color: #38bdf8; font-weight: bold;")
                    self.calculate_discount_preview()

    def calculate_discount_preview(self) -> None:
        pts = self.spin_points.value()
        discount_val = pts * 100  # 1 Poin = Rp 100
        self.lbl_preview_discount.setText(f"Nilai Diskon: Rp {discount_val:,.0f}")

    def redeem_points(self) -> None:
        if not self.selected_customer:
            QMessageBox.warning(self, "Peringatan", "Pilih member dari tabel terlebih dahulu!")
            return

        pts = self.spin_points.value()
        if pts > self.selected_customer.get("points", 0):
            QMessageBox.warning(self, "Gagal", "Jumlah poin melebihi poin yang dimiliki member!")
            return

        try:
            payload = {
                "phone": self.selected_customer["phone"],
                "points_to_redeem": pts,
                "conversion_rate": 100.0
            }
            res = requests.post(f"{API_URL}/customers/redeem-points", json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                QMessageBox.information(
                    self, "Penukaran Berhasil",
                    f"Berhasil menukar {pts} Poin!\n"
                    f"Voucher Diskon: Rp {data['discount_amount']:,.0f}\n"
                    f"Sisa Poin: {data['remaining_points']} Poin"
                )
                self.load_customers()
                self.selected_customer = None
                self.lbl_selected_info.setText("Pilih member dari tabel terlebih dahulu.")
            else:
                err = res.json().get("detail", "Gagal menukar poin.")
                QMessageBox.warning(self, "Gagal", err)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal terhubung ke backend: {e}")