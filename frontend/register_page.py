from pathlib import Path
import requests

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QHBoxLayout,
    QPushButton, QVBoxLayout, QSizePolicy
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, QTimer

BASE_DIR = Path(__file__).resolve().parent
BACKEND_URL = "http://127.0.0.1:5000/"

class RegisterPage(QWidget):
    def __init__(self, go_to_login):
        super().__init__()
        self.go_to_login = go_to_login

        # -------- Container (card) --------
        container = QWidget()
        container.setFixedSize(500, 600)

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
        self.logo.setContentsMargins(0, 0, 0, 0)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # -------- Title --------
        self.title = QLabel("Register")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.title.setStyleSheet("color: #0d53bb;")
        self.title.setContentsMargins(0, 0, 0, 0)

        # -------- Inputs --------
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setFixedHeight(45)

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.email.setFixedHeight(45)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setFixedHeight(45)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Re-enter Password")
        self.confirm_password.setFixedHeight(45)
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

        # Apply same style as login inputs
        for inp in [self.username, self.email, self.password, self.confirm_password]:
            inp.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #0d53bb;
                    border-radius: 10px;
                    padding: 0 10px;
                    padding-top: 8px;
                    padding-bottom: 8px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 2px solid #1E90FF;
                }
            """)

        # -------- Buttons --------
        self.register_btn = QPushButton("Register")
        self.register_btn.setFixedHeight(45)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d53bb;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0F78D1;
            }
            QPushButton:pressed {
                background-color: #0A5A9E;
            }
        """)
        self.register_btn.clicked.connect(self.register)

        self.back_btn = QPushButton("Back to Login")
        self.back_btn.setFixedHeight(45)
        self.back_btn.setStyleSheet("""
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
        self.back_btn.clicked.connect(self.go_to_login)

        # Horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.back_btn)

        # -------- Error Label --------
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")
        self.error_label.setContentsMargins(0, 5, 0, 0)

        # -------- Add widgets to form layout --------
        form_layout.addWidget(self.logo)
        form_layout.addWidget(self.title)
        form_layout.addWidget(self.username)
        form_layout.addWidget(self.email)
        form_layout.addWidget(self.password)
        form_layout.addWidget(self.confirm_password)
        form_layout.addLayout(button_layout)
        form_layout.addWidget(self.error_label)

        # -------- Main layout (center container) --------
        main_layout = QVBoxLayout(self)
        main_layout.addStretch()
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()
    
    def register(self):
        data = {
            "username": self.username.text(),
            "email": self.email.text(),
            "password": self.password.text(),
            "confirm_password": self.confirm_password.text(),
        }

        # Frontend validation
        if not all(data.values()):
            self.error_label.setText("All fields are required")
            return

        if data["password"] != data["confirm_password"]:
            self.error_label.setText("Passwords do not match")
            return

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/register",
                json=data,
                timeout=5
            )

            if response.status_code == 201:
                self.username.clear()
                self.email.clear()
                self.password.clear()
                self.confirm_password.clear()
                self.error_label.setStyleSheet("color: green; font-weight: bold;")
                self.error_label.setText("Registration successful! Redirecting to Log In Page.....")
                QTimer.singleShot(2000, self.go_to_login)
                self.error_label.setText("")
            else:
                self.error_label.setStyleSheet("color: red;")
                self.error_label.setText(response.json().get("error"))

        except Exception as e:
            self.error_label.setText(f"Backend error: {e}")
