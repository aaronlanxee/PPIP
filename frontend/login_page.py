from pathlib import Path
import requests
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QHBoxLayout,
    QPushButton, QVBoxLayout, QSizePolicy
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt

BASE_DIR = Path(__file__).resolve().parent
BACKEND_URL = "http://127.0.0.1:5000/"

class LoginPage(QWidget):
    def __init__(self, on_login_success, go_to_register):
        super().__init__()
        self.on_login_success = on_login_success
        self.go_to_register = go_to_register

        # -------- Container (card) --------
        container = QWidget()
        container.setFixedSize(500, 500)

        form_layout = QVBoxLayout(container)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(20, 20, 20, 20)

        # -------- Logo --------
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = BASE_DIR / ".." / "assets" / "text_logo.png"
        pixmap = QPixmap(str(logo_path))
        pixmap = pixmap.scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.logo.setPixmap(pixmap)
        self.logo.setContentsMargins(0, 0, 0, 0)       # remove extra margin
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        # -------- Title --------
        self.title = QLabel("Login")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.title.setStyleSheet("color: #0d53bb;")  # Dodger Blue
        self.title.setContentsMargins(0, 0, 0, 0)

        # -------- Inputs --------
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setFixedHeight(45)
        self.username.setStyleSheet("""
            QLineEdit {
                border: 2px solid #0d53bb;
                border-radius: 10px;
                padding: 0 10px;      /* left/right padding */
                padding-top: 8px;     /* top padding to center text */
                padding-bottom: 8px;  /* bottom padding */
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1E90FF;
            }
        """)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setFixedHeight(45)
        self.password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #0d53bb;
                border-radius: 10px;
                padding: 0 10px;      /* left/right padding */
                padding-top: 8px;     /* top padding to center text */
                padding-bottom: 8px;  /* bottom padding */
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1E90FF;
            }
        """)
        self.otp = QLineEdit()
        self.otp.setPlaceholderText("otp")
        self.otp.setFixedHeight(45)
        self.otp.setStyleSheet("""
            QLineEdit {
                border: 2px solid #0d53bb;
                border-radius: 10px;
                padding: 0 10px;      /* left/right padding */
                padding-top: 8px;     /* top padding to center text */
                padding-bottom: 8px;  /* bottom padding */
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1E90FF;
            }
        """)
        self.otp.hide()

        # -------- Login Button --------
        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedHeight(45)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d53bb;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                padding: 0px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0F78D1;
            }
            QPushButton:pressed {
                background-color: #0A5A9E;
            }
        """)
        self.login_btn.clicked.connect(self.login)

        self.register_btn = QPushButton("register")
        self.register_btn.setFixedHeight(45)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #0d53bb;
                border: 2px solid #0d53bb;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #E0F0FF;
            }
            QPushButton:pressed {
                background-color: #B0D8FF;
            }
        """)
        self.register_btn.clicked.connect(self.go_to_register)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        self.button_layout.addWidget(self.login_btn)
        self.button_layout.addWidget(self.register_btn)

        # -------- Error Label --------
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")
        self.error_label.setContentsMargins(0, 5, 0, 0)

        # -------- Add widgets to form layout --------
        form_layout.addWidget(self.logo)
        form_layout.addWidget(self.title)
        form_layout.addWidget(self.username)
        form_layout.addWidget(self.password)
        form_layout.addWidget(self.otp)
        form_layout.addLayout(self.button_layout)
        form_layout.addWidget(self.error_label)

        # -------- Main layout (center container) --------
        main_layout = QVBoxLayout(self)
        main_layout.addStretch()
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()
        

    def login(self):
        username = self.username.text()
        password = self.password.text()
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/login",
                json={"username": username, "password": password},
                timeout=5
            )
            data = response.json()
            if response.status_code == 200:
                self.username.setText("")
                self.password.setText("")
                self.error_label.setText("")
                self.on_login_success(username, data["user_id"])
                self.error_label.setText("")
            else:
                self.error_label.setText(data.get("message", "Error"))
        except Exception as e:
            self.error_label.setText(f"Backend not reachable: {e}")