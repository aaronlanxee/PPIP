from pathlib import Path
import requests
from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt

BASE_DIR = Path(__file__).resolve().parent
BACKEND_URL = "http://127.0.0.1:5000"


class OTPVerificationPage(QWidget):
    def __init__(self, on_otp_success, go_back):
        super().__init__()
        self.on_otp_success = on_otp_success
        self.go_back = go_back

        # -------- Container --------
        container = QWidget()
        container.setFixedSize(500, 500)
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # -------- Logo --------
        self.logo = QLabel()
        logo_path = BASE_DIR / ".." / "assets" / "text_logo.png"
        pixmap = QPixmap(str(logo_path))
        pixmap = pixmap.scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio)
        self.logo.setPixmap(pixmap)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # -------- Title --------
        self.title = QLabel("OTP Verification")
        self.title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("color: #0d53bb;")

        # -------- OTP Input --------
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter a 6-digit OTP")
        self.otp_input.setFixedHeight(45)
        self.otp_input.setStyleSheet("""
            QLineEdit {border: 2px solid #0d53bb; border-radius: 10px; padding: 0 10px; padding-top: 8px; padding-bottom: 8px; font-size: 14px;}
            QLineEdit:focus {border: 2px solid #1E90FF;}
        """)

        # -------- Buttons --------
        self.verify_btn = QPushButton("Verify")
        self.verify_btn.setFixedHeight(45)
        self.verify_btn.setStyleSheet("""
            QPushButton {background-color: #0d53bb; color: white; border-radius: 10px; font-weight: bold; font-size: 16px;}
            QPushButton:hover {background-color: #0F78D1;}
            QPushButton:pressed {background-color: #0A5A9E;}
        """)
        self.verify_btn.clicked.connect(self.verify_otp)

        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedHeight(45)
        self.back_btn.setStyleSheet("""
            QPushButton {background-color: #FFFFFF; color: #0d53bb; border: 2px solid #0d53bb; border-radius: 10px; font-weight: bold; font-size: 16px;}
            QPushButton:hover {background-color: #E0F0FF;}
            QPushButton:pressed {background-color: #B0D8FF;}
        """)
        self.back_btn.clicked.connect(self.go_back)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.verify_btn)
        button_layout.addWidget(self.back_btn)

        # -------- Error Label --------
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")

        # -------- Add widgets to layout --------
        layout.addWidget(self.logo)
        layout.addWidget(self.title)
        layout.addWidget(self.otp_input)
        layout.addLayout(button_layout)
        layout.addWidget(self.error_label)

        # -------- Main layout --------
        main_layout = QVBoxLayout(self)
        main_layout.addStretch()
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()

    def verify_otp(self):
        otp = self.otp_input.text()
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/verify_otp",
                json={"otp": otp, "username": self.username},
                timeout=5
            )
            data = response.json()
            if response.status_code == 200:
                self.otp_input.setText("")
                self.error_label.setText("")
                self.on_otp_success()
            else:
                self.error_label.setText(data.get("message", "Invalid OTP"))
        except Exception as e:
            self.error_label.setText(f"Backend not reachable: {e}")
    
    def set_username(self, username):
        self.username = username
