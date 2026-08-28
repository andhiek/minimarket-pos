import requests
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QDoubleSpinBox, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

API_URL = "http://127.0.0.1:8000/api"

class ProductManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manajemen Produk & Stok Barcode")
        self.resize(950, 600)
        
        self.products_data: List[Dict[str, Any]] = []
        self.selected_product_id: Optional[int] = None
        
        self.init_ui()
        self.load_products()

    def init_ui(self) -> None:
        main_layout = QHBoxLayout(self)

        # ==========================================
        # LEFT PANEL: Search & Product Table
        # ==========================================
        left_layout = QVBoxLayout()
        
        # Search Bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Cari (Barcode / Nama):"))
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Ketik kode barcode atau nama barang...")
        self.input_search.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.input_search)
        left_layout.addLayout(search_layout)

        # Table Products
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Barcode", "Nama Produk", "Kategori", "Harga Jual", "Stok"
        ])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemClicked.connect(self.on_table_item_clicked)
        left_layout.addWidget(self.table)

        # Action Buttons under Table
        table_btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Refresh Table")
        btn_refresh.clicked.connect(self.load_products)
        
        btn_clear_form = QPushButton("🧹 Reset Form / Batal Select")
        btn_clear_form.clicked.connect(self.clear_form)
        
        table_btn_layout.addWidget(btn_refresh)
        table_btn_layout.addWidget(btn_clear_form)
        left_layout.addLayout(table_btn_layout)

        main_layout.addLayout(left_layout, stretch=3)

        # ==========================================
        # RIGHT PANEL: Form Add / Edit / Delete
        # ==========================================
        right_layout = QVBoxLayout()
        
        form_group = QGroupBox("Form Detail Produk")
        form_layout = QVBoxLayout(form_group)

        form_layout.addWidget(QLabel("Kode Barcode:"))
        self.input_barcode = QLineEdit()
        self.input_barcode.setPlaceholderText("Scan atau ketik barcode...")
        form_layout.addWidget(self.input_barcode)

        form_layout.addWidget(QLabel("Nama Produk:"))
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nama produk...")
        form_layout.addWidget(self.input_name)

        form_layout.addWidget(QLabel("Kategori:"))
        self.input_category = QComboBox()
        self.input_category.setEditable(True)
        self.input_category.addItems(["Makanan", "Minuman", "Perawatan Diri", "Sembako", "Snack", "Lainnya"])
        form_layout.addWidget(self.input_category)

        form_layout.addWidget(QLabel("Harga Beli (Modal):"))
        self.spin_purchase_price = QDoubleSpinBox()
        self.spin_purchase_price.setRange(0, 100000000)
        self.spin_purchase_price.setSingleStep(500)
        self.spin_purchase_price.setPrefix("Rp ")
        form_layout.addWidget(self.spin_purchase_price)

        form_layout.addWidget(QLabel("Harga Jual:"))
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 100000000)
        self.spin_price.setSingleStep(500)
        self.spin_price.setPrefix("Rp ")
        form_layout.addWidget(self.spin_price)

        form_layout.addWidget(QLabel("Stok Barang:"))
        self.spin_stock = QSpinBox()
        self.spin_stock.setRange(0, 100000)
        form_layout.addWidget(self.spin_stock)

        # Form Buttons
        self.btn_save = QPushButton("💾 Simpan Produk Baru")
        self.btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold; padding: 8px;")
        self.btn_save.clicked.connect(self.save_product)
        form_layout.addWidget(self.btn_save)

        self.btn_delete = QPushButton("🗑️ Hapus Produk")
        self.btn_delete.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; padding: 8px;")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.delete_product)
        form_layout.addWidget(self.btn_delete)

        right_layout.addWidget(form_group)
        right_layout.addStretch()

        main_layout.addLayout(right_layout, stretch=2)

    def load_products(self) -> None:
        """Mengambil data produk dari Backend API"""
        try:
            res = requests.get(f"{API_URL}/products/all", timeout=5)
            if res.status_code == 200:
                self.products_data = res.json()
                self.populate_table(self.products_data)
            else:
                QMessageBox.warning(self, "Peringatan", f"Gagal mengambil data dari server. Code: {res.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Error Koneksi", f"Gagal mengambil data produk dari server:\n{e}")

    def populate_table(self, data: List[Dict[str, Any]]) -> None:
        """Menampilkan data produk ke QTableWidget dengan penanganan aman key KeyError"""
        self.table.setRowCount(0)
        for row_idx, item in enumerate(data):
            self.table.insertRow(row_idx)
            
            p_id = item.get("id", "")
            barcode = item.get("barcode", "")
            name = item.get("name", "")
            category = item.get("category", "-")
            price = item.get("price", 0.0)
            stock = item.get("stock", 0)

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(p_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(barcode)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(name)))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(category)))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"Rp {price:,.0f}"))

            stock_item = QTableWidgetItem(str(stock))
            # Highlight warna jika stok < 5
            if stock <= 5:
                stock_item.setBackground(QColor(239, 68, 68, 80))  # Light Red
                stock_item.setToolTip("Peringatan: Stok hampir habis!")
            self.table.setItem(row_idx, 5, stock_item)

    def filter_products(self) -> None:
        """Filter tabel secara langsung berdasarkan keyword pencarian"""
        query = self.input_search.text().lower().strip()
        filtered = [
            p for p in self.products_data
            if query in str(p.get("barcode", "")).lower() or query in str(p.get("name", "")).lower()
        ]
        self.populate_table(filtered)

    def on_table_item_clicked(self) -> None:
        """Mengisi data form saat salah satu produk pada tabel diklik (Mode Edit)"""
        row = self.table.currentRow()
        if row >= 0:
            item_id = self.table.item(row, 0)
            # Pastikan item_id tidak None sebelum memanggil .text()
            if item_id is not None and item_id.text():
                self.selected_product_id = int(item_id.text())
                product = next((p for p in self.products_data if p.get("id") == self.selected_product_id), None)
                if product:
                    self.input_barcode.setText(str(product.get("barcode", "")))
                    self.input_name.setText(str(product.get("name", "")))
                    
                    cat = str(product.get("category", "Makanan"))
                    idx = self.input_category.findText(cat)
                    if idx >= 0:
                        self.input_category.setCurrentIndex(idx)
                    else:
                        self.input_category.setEditText(cat)

                    # Pembacaan aman untuk purchase_price / cost_price
                    purchase_p = product.get("purchase_price", product.get("cost_price", 0.0))
                    self.spin_purchase_price.setValue(float(purchase_p))
                    self.spin_price.setValue(float(product.get("price", 0.0)))
                    self.spin_stock.setValue(int(product.get("stock", 0)))

                    self.btn_save.setText("✏️ Update Produk")
                    self.btn_save.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; padding: 8px;")
                    self.btn_delete.setEnabled(True)

    def clear_form(self) -> None:
        """Mengosongkan form untuk mode Tambah Produk Baru"""
        self.selected_product_id = None
        self.input_barcode.clear()
        self.input_name.clear()
        self.input_category.setCurrentIndex(0)
        self.spin_purchase_price.setValue(0.0)
        self.spin_price.setValue(0.0)
        self.spin_stock.setValue(0)
        
        self.btn_save.setText("💾 Simpan Produk Baru")
        self.btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold; padding: 8px;")
        self.btn_delete.setEnabled(False)
        self.table.clearSelection()

    def save_product(self) -> None:
        """Menyimpan (Tambah Baru atau Update) Produk ke Server API"""
        barcode = self.input_barcode.text().strip()
        name = self.input_name.text().strip()
        category = self.input_category.currentText().strip()
        purchase_price = self.spin_purchase_price.value()
        price = self.spin_price.value()
        stock = self.spin_stock.value()

        if not barcode or not name:
            QMessageBox.warning(self, "Peringatan", "Barcode dan Nama Produk wajib diisi!")
            return

        payload = {
            "barcode": barcode,
            "name": name,
            "category": category,
            "purchase_price": purchase_price,
            "price": price,
            "stock": stock
        }

        try:
            if self.selected_product_id is None:
                # HTTP POST: Tambah Produk Baru
                res = requests.post(f"{API_URL}/products", json=payload, timeout=5)
            else:
                # HTTP PUT: Update Produk Existed
                res = requests.put(f"{API_URL}/products/{self.selected_product_id}", json=payload, timeout=5)

            if res.status_code in (200, 201):
                QMessageBox.information(self, "Sukses", "Data produk berhasil disimpan!")
                self.clear_form()
                self.load_products()
            else:
                err_detail = res.json().get("detail", "Gagal menyimpan data produk.")
                QMessageBox.warning(self, "Gagal", f"Server error: {err_detail}")
        except Exception as e:
            QMessageBox.critical(self, "Error Koneksi", f"Gagal terhubung ke server API:\n{e}")

    def delete_product(self) -> None:
        """Menghapus Produk yang sedang dipilih"""
        if self.selected_product_id is None:
            return

        confirm = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Apakah Anda yakin ingin menghapus produk '{self.input_name.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                res = requests.delete(f"{API_URL}/products/{self.selected_product_id}", timeout=5)
                if res.status_code == 200:
                    QMessageBox.information(self, "Sukses", "Produk berhasil dihapus!")
                    self.clear_form()
                    self.load_products()
                else:
                    QMessageBox.warning(self, "Gagal", "Gagal menghapus produk dari server.")
            except Exception as e:
                QMessageBox.critical(self, "Error Koneksi", f"Gagal terhubung ke server API:\n{e}")