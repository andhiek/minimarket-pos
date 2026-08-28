import requests
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

API_URL = "http://127.0.0.1:8000/api"


class SalesReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Laporan Penjualan Harian & Laba-Rugi")
        self.setGeometry(150, 150, 950, 600)
        self.init_ui()
        self.load_report()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Pilih Tanggal Laporan:"))
        
        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.dateChanged.connect(self.load_report)
        filter_layout.addWidget(self.date_picker)

        btn_refresh = QPushButton("Muat Ulang")
        btn_refresh.clicked.connect(self.load_report)
        filter_layout.addWidget(btn_refresh)
        filter_layout.addStretch()

        main_layout.addLayout(filter_layout)

        cards_layout = QHBoxLayout()

        self.card_omset = self.create_card("TOTAL OMSET (PENJUALAN)", "Rp 0", "#2980b9")
        self.card_hpp = self.create_card("TOTAL HPP (MODAL)", "Rp 0", "#7f8c8d")
        self.card_profit = self.create_card("LABA KOTOR BERSIH", "Rp 0", "#27ae60")

        cards_layout.addWidget(self.card_omset)
        cards_layout.addWidget(self.card_hpp)
        cards_layout.addWidget(self.card_profit)

        main_layout.addLayout(cards_layout)

        main_layout.addWidget(QLabel("Daftar Transaksi Hari Ini:"))
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["No. Struk (Invoice)", "Jam", "Metode Bayar", "Total Nilai (Rp)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)

    def create_card(self, title, default_val, color_hex):
        box = QGroupBox(title)
        box.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout = QVBoxLayout()
        lbl_val = QLabel(default_val)
        lbl_val.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl_val.setStyleSheet(f"color: {color_hex};")
        lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_val)
        box.setLayout(layout)
        return box

    def load_report(self):
        selected_date = self.date_picker.date().toString("yyyy-MM-dd")
        try:
            response = requests.get(f"{API_URL}/reports/daily", params={"report_date": selected_date})
            if response.status_code == 200:
                data = response.json()
                self.update_ui(data)
            else:
                QMessageBox.warning(self, "Gagal", "Gagal mengambil data laporan.")
        except Exception as e:
            QMessageBox.critical(self, "Error Koneksi", f"Gagal terhubung ke backend:\n{str(e)}")

    def update_ui(self, data: dict):
    # Gunakan .get() dengan default value 0 agar aman dari KeyError
        total_omset = data.get('total_omset', 0)
        total_hpp = data.get('total_hpp', 0)
        laba_kotor = data.get('laba_kotor', 0)

        omset_lbl = self.card_omset.findChild(QLabel)
        if omset_lbl:
            omset_lbl.setText(f"Rp {total_omset:,.0f}")
            
        hpp_lbl = self.card_hpp.findChild(QLabel)
        if hpp_lbl:
            hpp_lbl.setText(f"Rp {total_hpp:,.0f}")
        
        profit_lbl = self.card_profit.findChild(QLabel)
        if profit_lbl:
            profit_lbl.setText(f"Rp {laba_kotor:,.0f}")
            if laba_kotor < 0:
                profit_lbl.setStyleSheet("color: #c0392b;")
            else:
                profit_lbl.setStyleSheet("color: #27ae60;")

        transactions = data.get("transactions", [])
        self.table.setRowCount(0)
        for row_idx, t in enumerate(transactions):
            self.table.insertRow(row_idx)
            # Gunakan .get() juga pada iterasi item tabel untuk mengantisipasi key hilang
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(t.get('invoice_number', '-'))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(t.get('time', '-'))))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(t.get('payment_method', '-'))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"Rp {t.get('grand_total', 0):,.0f}"))