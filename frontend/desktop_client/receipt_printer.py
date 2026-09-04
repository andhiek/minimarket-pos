import json
import os
import sys
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QMessageBox, QGroupBox,
    QTextEdit, QCheckBox
)
from PySide6.QtCore import QSizeF, QMarginsF
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

CONFIG_FILE = "receipt_config.json"

DEFAULT_CONFIG = {
    "store_name": "MINIMARKET BAROKAH",
    "store_address": "Jl. Raya Batu No. 123, Batu",
    "store_phone": "0812-3456-7890",
    "footer_message": "Terima Kasih Atas Kunjungan Anda!\nBarang yang sudah dibeli tidak dapat ditukar.",
    "paper_type": "58mm",  # Options: 58mm, 80mm, Custom
    "custom_width_mm": 58,
    "font_family": "Courier New",
    "auto_print": False,
    "show_preview": True
}

def load_receipt_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    config.setdefault(k, v)
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_receipt_config(config: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Gagal menyimpan konfigurasi struk: {e}")

class ReceiptPrinter:
    """Helper class untuk merender HTML Struk dan mengirim ke Printer Qt"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_receipt_config()

    def generate_html(self, transaction_data: Dict[str, Any]) -> str:
        """Membuat string HTML struk belanja sesuai ukuran kertas"""
        store_name = self.config.get("store_name", "MINIMARKET")
        store_address = self.config.get("store_address", "")
        store_phone = self.config.get("store_phone", "")
        footer = self.config.get("footer_message", "").replace("\n", "<br>")
        font_family = self.config.get("font_family", "Courier New")
        
        paper_type = self.config.get("paper_type", "58mm")
        if paper_type == "58mm":
            width_px = "48mm"
            font_size = "8pt"
        elif paper_type == "80mm":
            width_px = "70mm"
            font_size = "9.5pt"
        else:
            custom_w = self.config.get("custom_width_mm", 58)
            width_px = f"{max(30, custom_w - 8)}mm"
            font_size = "8.5pt"

        items = transaction_data.get("items", [])
        items_html = ""
        for item in items:
            name = item.get("name", "Produk")
            qty = item.get("qty", 1)
            price = item.get("price", 0)
            total = qty * price
            
            items_html += f"""
            <tr>
                <td colspan="3" style="font-weight: bold; padding-top: 3px;">{name}</td>
            </tr>
            <tr>
                <td style="padding-left: 8px;">@ {price:,.0f}</td>
                <td style="text-align: right;">{qty}</td>
                <td style="text-align: right;">{total:,.0f}</td>
            </tr>
            """

        subtotal = transaction_data.get("subtotal", 0)
        discount = transaction_data.get("discount", 0)
        total_amount = transaction_data.get("total", subtotal - discount)
        paid = transaction_data.get("paid", total_amount)
        change = max(0, paid - total_amount)
        trx_id = transaction_data.get("trx_id", "TRX-0000")
        date_str = transaction_data.get("date", "-")
        cashier = transaction_data.get("cashier", "Kasir")
        customer = transaction_data.get("customer_name", "Umum")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            @page {{
                margin: 2mm;
            }}
            body {{
                font-family: '{font_family}', Courier, monospace;
                font-size: {font_size};
                width: {width_px};
                margin: 0 auto;
                padding: 0;
                color: #000;
            }}
            .text-center {{ text-align: center; }}
            .text-right {{ text-align: right; }}
            .bold {{ font-weight: bold; }}
            .divider {{
                border-top: 1px dashed #000;
                margin: 4px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: {font_size};
            }}
            td {{ padding: 1px 0; vertical-align: top; }}
            th {{ border-bottom: 1px solid #000; text-align: left; padding: 2px 0; }}
        </style>
        </head>
        <body>
            <div class="text-center">
                <div style="font-size: 1.2em; font-weight: bold;">{store_name}</div>
                <div>{store_address}</div>
                <div>Telp: {store_phone}</div>
            </div>

            <div class="divider"></div>

            <table>
                <tr><td>No. Struk</td><td>: {trx_id}</td></tr>
                <tr><td>Tanggal</td><td>: {date_str}</td></tr>
                <tr><td>Kasir</td><td>: {cashier}</td></tr>
                <tr><td>Pelanggan</td><td>: {customer}</td></tr>
            </table>

            <div class="divider"></div>

            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th style="text-align: right;">Qty</th>
                        <th style="text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <div class="divider"></div>

            <table>
                <tr>
                    <td>Subtotal</td>
                    <td class="text-right">Rp {subtotal:,.0f}</td>
                </tr>
                {f'<tr><td>Diskon</td><td class="text-right">-Rp {discount:,.0f}</td></tr>' if discount > 0 else ''}
                <tr class="bold">
                    <td>TOTAL</td>
                    <td class="text-right">Rp {total_amount:,.0f}</td>
                </tr>
                <tr>
                    <td>Bayar</td>
                    <td class="text-right">Rp {paid:,.0f}</td>
                </tr>
                <tr>
                    <td>Kembali</td>
                    <td class="text-right">Rp {change:,.0f}</td>
                </tr>
            </table>

            <div class="divider"></div>

            <div class="text-center" style="margin-top: 6px;">
                {footer}
            </div>
        </body>
        </html>
        """
        return html

    def print_receipt(self, transaction_data: Dict[str, Any], parent_widget=None) -> bool:
        """Fungsi utama untuk mencetak struk dengan opsi Preview atau Direct Print"""
        html_content = self.generate_html(transaction_data)
        doc = QTextDocument()
        doc.setHtml(html_content)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        
        # 1. Tentukan Lebar Kertas (mm)
        paper_type = self.config.get("paper_type", "58mm")
        if paper_type == "58mm":
            width_mm = 58.0
        elif paper_type == "80mm":
            width_mm = 80.0
        else:
            width_mm = float(self.config.get("custom_width_mm", 58))

        height_mm = 200.0

        # 2. Buat QPageSize menggunakan QSizeF
        custom_page_size = QPageSize(
            QSizeF(width_mm, height_mm),
            QPageSize.Unit.Millimeter
        )
        printer.setPageSize(custom_page_size)

        # 3. Set Margin Kertas (Margin Tipis 2mm)
        margins = QMarginsF(2.0, 2.0, 2.0, 2.0)
        printer.setPageMargins(margins, QPageLayout.Unit.Millimeter)

        # Cek opsi preview
        if self.config.get("show_preview", True):
            preview = QPrintPreviewDialog(printer, parent_widget)
            preview.setWindowTitle("Preview Struk Belanja")
            preview.paintRequested.connect(lambda p: doc.print_(p))
            preview.exec()
            return True
        else:
            dialog = QPrintDialog(printer, parent_widget)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                doc.print_(printer)
                return True
            return False


class ReceiptSettingsDialog(QDialog):
    """Dialog GUI Pengaturan Kertas & Header Struk Toko"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pengaturan Kertas & Cetak Struk")
        self.resize(500, 520)
        self.config = load_receipt_config()
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Group 1: Informasi Toko
        group_store = QGroupBox("Informasi Toko Pada Struk")
        g1_layout = QVBoxLayout(group_store)

        g1_layout.addWidget(QLabel("Nama Toko / Minimarket:"))
        self.input_store_name = QLineEdit(self.config.get("store_name", ""))
        g1_layout.addWidget(self.input_store_name)

        g1_layout.addWidget(QLabel("Alamat Toko:"))
        self.input_address = QLineEdit(self.config.get("store_address", ""))
        g1_layout.addWidget(self.input_address)

        g1_layout.addWidget(QLabel("Nomor Telepon:"))
        self.input_phone = QLineEdit(self.config.get("store_phone", ""))
        g1_layout.addWidget(self.input_phone)

        g1_layout.addWidget(QLabel("Pesan Catatan Footer:"))
        self.input_footer = QTextEdit()
        self.input_footer.setMaximumHeight(65)
        self.input_footer.setPlainText(self.config.get("footer_message", ""))
        g1_layout.addWidget(self.input_footer)

        layout.addWidget(group_store)

        # Group 2: Pengaturan Kertas Printer
        group_paper = QGroupBox("Ukuran Kertas & Printer")
        g2_layout = QVBoxLayout(group_paper)

        paper_row = QHBoxLayout()
        paper_row.addWidget(QLabel("Format / Lebar Kertas:"))
        self.combo_paper = QComboBox()
        self.combo_paper.addItems(["58mm (Thermal Standar)", "80mm (Thermal Wide)", "Custom Width"])
        
        pt = self.config.get("paper_type", "58mm")
        if pt == "80mm":
            self.combo_paper.setCurrentIndex(1)
        elif pt == "Custom":
            self.combo_paper.setCurrentIndex(2)
        else:
            self.combo_paper.setCurrentIndex(0)
            
        self.combo_paper.currentIndexChanged.connect(self.on_paper_changed)
        paper_row.addWidget(self.combo_paper)
        g2_layout.addLayout(paper_row)

        custom_row = QHBoxLayout()
        custom_row.addWidget(QLabel("Custom Lebar Kertas (mm):"))
        self.spin_custom_width = QSpinBox()
        self.spin_custom_width.setRange(30, 300)
        self.spin_custom_width.setValue(self.config.get("custom_width_mm", 58))
        self.spin_custom_width.setEnabled(pt == "Custom")
        custom_row.addWidget(self.spin_custom_width)
        g2_layout.addLayout(custom_row)

        self.chk_preview = QCheckBox("Tampilkan Preview Struk Sebelum Mencetak")
        self.chk_preview.setChecked(self.config.get("show_preview", True))
        g2_layout.addWidget(self.chk_preview)

        layout.addWidget(group_paper)

        # Action Buttons
        btn_layout = QHBoxLayout()
        
        btn_test = QPushButton("📄 Test Print Preview")
        btn_test.clicked.connect(self.test_print)
        
        btn_save = QPushButton("💾 Simpan Pengaturan")
        btn_save.setStyleSheet("background-color: #22c55e; color: white; font-weight: bold; padding: 6px;")
        btn_save.clicked.connect(self.save_settings)
        
        btn_layout.addWidget(btn_test)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def on_paper_changed(self, index: int) -> None:
        self.spin_custom_width.setEnabled(index == 2)

    def save_settings(self) -> None:
        paper_idx = self.combo_paper.currentIndex()
        paper_type = "58mm" if paper_idx == 0 else ("80mm" if paper_idx == 1 else "Custom")

        self.config["store_name"] = self.input_store_name.text().strip()
        self.config["store_address"] = self.input_address.text().strip()
        self.config["store_phone"] = self.input_phone.text().strip()
        self.config["footer_message"] = self.input_footer.toPlainText().strip()
        self.config["paper_type"] = paper_type
        self.config["custom_width_mm"] = self.spin_custom_width.value()
        self.config["show_preview"] = self.chk_preview.isChecked()

        save_receipt_config(self.config)
        QMessageBox.information(self, "Sukses", "Pengaturan cetak struk berhasil disimpan!")
        self.accept()

    def test_print(self) -> None:
        """Uji cetak struk dummy dengan setting saat ini"""
        test_config = {
            "store_name": self.input_store_name.text(),
            "store_address": self.input_address.text(),
            "store_phone": self.input_phone.text(),
            "footer_message": self.input_footer.toPlainText(),
            "paper_type": "58mm" if self.combo_paper.currentIndex() == 0 else ("80mm" if self.combo_paper.currentIndex() == 1 else "Custom"),
            "custom_width_mm": self.spin_custom_width.value(),
            "show_preview": True
        }
        
        dummy_trx = {
            "trx_id": "TRX-TEST-001",
            "date": "2026-08-28 23:20",
            "cashier": "Admin / Test",
            "customer_name": "Member Test",
            "items": [
                {"name": "Indomie Goreng Original 85g", "qty": 3, "price": 3100},
                {"name": "Aqua Air Mineral 600ml", "qty": 2, "price": 3500}
            ],
            "subtotal": 16300,
            "discount": 1000,
            "total": 15300,
            "paid": 20000,
            "change": 4700
        }
        
        printer = ReceiptPrinter(test_config)
        printer.print_receipt(dummy_trx, self)