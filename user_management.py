import requests
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QLineEdit, QComboBox, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt

API_URL = "http://127.0.0.1:8000/api"

class UserManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manajemen User & Kasir")
        self.resize(650, 420)
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Form Input User Baru
        form_layout = QHBoxLayout()
        
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Username")

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nama Lengkap")

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Password")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.combo_role = QComboBox()
        self.combo_role.addItems(["kasir", "admin"])

        btn_add = QPushButton("Tambah User")
        btn_add.setObjectName("btnPrimary")
        btn_add.clicked.connect(self.add_user)

        form_layout.addWidget(self.input_username)
        form_layout.addWidget(self.input_name)
        form_layout.addWidget(self.input_password)
        form_layout.addWidget(self.combo_role)
        form_layout.addWidget(btn_add)

        layout.addLayout(form_layout)

        # Tabel Daftar User
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Nama Lengkap", "Role"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_users(self):
        try:
            res = requests.get(f"{API_URL}/users", timeout=5)
            if res.status_code == 200:
                users = res.json()
                self.table.setRowCount(0)
                for row_idx, u in enumerate(users):
                    self.table.insertRow(row_idx)
                    self.table.setItem(row_idx, 0, QTableWidgetItem(str(u.get("id"))))
                    self.table.setItem(row_idx, 1, QTableWidgetItem(u.get("username")))
                    self.table.setItem(row_idx, 2, QTableWidgetItem(u.get("full_name")))
                    self.table.setItem(row_idx, 3, QTableWidgetItem(u.get("role")))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Gagal memuat data user: {e}")

    def add_user(self):
        username = self.input_username.text().strip()
        name = self.input_name.text().strip()
        pwd = self.input_password.text().strip()
        role = self.combo_role.currentText()

        if not username or not pwd or not name:
            QMessageBox.warning(self, "Peringatan", "Semua field input harus diisi!")
            return

        payload = {
            "username": username,
            "full_name": name,
            "password": pwd,
            "role": role
        }

        try:
            res = requests.post(f"{API_URL}/users", json=payload, timeout=5)
            if res.status_code in (200, 201):
                QMessageBox.information(self, "Sukses", f"User/Kasir '{username}' berhasil ditambahkan!")
                self.input_username.clear()
                self.input_name.clear()
                self.input_password.clear()
                self.load_users()
            else:
                err_detail = res.json().get("detail", "Gagal menambah user")
                QMessageBox.warning(self, "Gagal", err_detail)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Koneksi gagal: {e}")