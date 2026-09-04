import sys
import os
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QMessageBox, QStackedWidget
)
from PySide6.QtCore import Qt

# Pastikan modul internal desktop_client dapat di-import
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

API_URL = "http://127.0.0.1:8000/api"

class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.setWindowTitle("POS Minimarket - Login")
        self.setFixedSize(350, 250)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("<h2>Login Minimarket POS</h2>", alignment=Qt.AlignmentFlag.AlignCenter))

        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Username")
        layout.addWidget(self.input_username)

        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Password")
        layout.addWidget(self.input_password)

        self.btn_login = QPushButton("Masuk")
        self.btn_login.clicked.connect(self.handle_login)
        layout.addWidget(self.btn_login)

        self.setLayout(layout)

    def handle_login(self):
        username = self.input_username.text().strip()
        password = self.input_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Peringatan", "Username dan Password wajib diisi!")
            return

        try:
            res = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
            if res.status_code == 200:
                user_data = res.json()
                self.on_login_success(user_data)
            else:
                detail = res.json().get("detail", "Login gagal!")
                QMessageBox.critical(self, "Error", detail)
        except Exception as e:
            QMessageBox.critical(self, "Koneksi Error", f"Gagal terhubung ke server backend:\n{e}")


class MainWindow(QMainWindow):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.setWindowTitle(f"Minimarket POS - Operator: {user_data['full_name']} ({user_data['role'].upper()})")
        self.resize(1024, 720)

        central_widget = QWidget()
        layout = QVBoxLayout()
        label_welcome = QLabel(f"<h1>Selamat Datang di Sistem POS, {user_data['full_name']}!</h1>")
        label_welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_welcome)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


class POSApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.login_window = LoginWindow(self.show_main_window)
        self.addWidget(self.login_window)
        self.setCurrentWidget(self.login_window)

    def show_main_window(self, user_data):
        self.main_window = MainWindow(user_data)
        self.addWidget(self.main_window)
        self.setCurrentWidget(self.main_window)
        
    # Tambahkan import dialog modul kamu di desktop_client/main.py
        # from sales_report import SalesReportDialog
        # from customer_management import CustomerManagementDialog

        # Di dalam class MainWindow pada desktop_client/main.py:
        def setup_menu_bar(self):
            menu_bar = self.menuBar()
            
            # Menu Transaksi & Laporan
            pos_menu = menu_bar.addMenu("Menu Utama")
            
            report_action = pos_menu.addAction("Laporan Penjualan Harian")
            report_action.triggered.connect(self.open_sales_report)

        def open_sales_report(self):
            # Parameter API_URL diteruskan ke dialog
            dialog = SalesReportDialog(api_url=API_URL, parent=self)
            dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POSApp()
    window.show()
    sys.exit(app.exec())