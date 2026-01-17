from pathlib import Path
import requests

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QLineEdit
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt

BACKEND_URL = "http://127.0.0.1:5000"
BASE_DIR = Path(__file__).resolve().parent


class FoundPetPage(QWidget):
    def __init__(self, go_back, go_to_camera):
        super().__init__()

        self.go_back = go_back
        self.go_to_camera = go_to_camera
        self.image_path = None

        self.pet_id = None
        # ===== Container =====
        container = QWidget()
        container.setFixedSize(500, 520)

        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # ===== Top Bar =====
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #0d53bb;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { text-decoration: underline; }
        """)
        back_btn.clicked.connect(self.reset_page)
        back_btn.clicked.connect(go_back)

        top_bar.addWidget(back_btn)
        top_bar.addStretch()

        # ===== Title =====
        self.title = QLabel("I've found a missing pet")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.title.setStyleSheet("color: #0d53bb;")

        # ===== Image Preview =====
        self.image_preview = QLabel("No Image Selected")
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setFixedHeight(200)
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px dashed #0d53bb;
                border-radius: 12px;
                color: #6b7280;
            }
        """)

        # ===== Buttons =====
        self.upload_btn = QPushButton("Upload Image")
        self.upload_btn.setCursor(Qt.PointingHandCursor)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #0d53bb;
                border: 2px solid #0d53bb;
                border-radius: 10px;
                font-weight: bold;
            }
        """)
        self.upload_btn.clicked.connect(self.select_image)

        self.capture_btn = QPushButton("Capture Image")
        self.capture_btn.setCursor(Qt.PointingHandCursor)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background: #0d53bb;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
        """)
        self.capture_btn.clicked.connect(go_to_camera)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.upload_btn)
        btn_row.addWidget(self.capture_btn)

        # ===== Submit Button =====
        self.submit_btn = QPushButton("Submit Found Pet")
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setFixedHeight(45)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background: #0d53bb;
                color: white;
                border-radius: 12px;
                font-weight: bold;
            }
        """)
        self.submit_btn.clicked.connect(self.submit)

        # ===== Status Label =====
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        # ===== Not Found Label =====
        self.not_found_label = QLabel("Sorry, pet not recognized")
        self.not_found_label.setAlignment(Qt.AlignCenter)
        self.not_found_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.not_found_label.setStyleSheet("color: #dc2626;")
        self.not_found_label.hide()

        # ===== Finder Form =====
        self.form_widget = QWidget()
        form_layout = QVBoxLayout(self.form_widget)
        form_layout.setSpacing(12)

        input_style = """
        QLineEdit {
            border: 2px solid #0d53bb;
            border-radius: 10px;
            padding: 8px;
            font-size: 14px;
        }
        """

        self.finder_name = QLineEdit()
        self.finder_name.setPlaceholderText("Your Name")
        self.finder_name.setStyleSheet(input_style)

        self.finder_email = QLineEdit()
        self.finder_email.setPlaceholderText("Your Email")  # NEW EMAIL FIELD
        self.finder_email.setStyleSheet(input_style)

        self.finder_address = QLineEdit()
        self.finder_address.setPlaceholderText("Your Address")
        self.finder_address.setStyleSheet(input_style)

        self.submit_info_btn = QPushButton("Submit Finder Info")
        self.submit_info_btn.setFixedHeight(45)
        self.submit_info_btn.setStyleSheet("""
            QPushButton {
                background: #0d53bb;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
        """)
        self.submit_info_btn.clicked.connect(self.send_finder_info)

        form_layout.addWidget(self.finder_name)
        form_layout.addWidget(self.finder_email)  # add email to layout
        form_layout.addWidget(self.finder_address)
        form_layout.addWidget(self.submit_info_btn)
        self.form_widget.hide()

        # ===== Assemble =====
        layout.addLayout(top_bar)
        layout.addWidget(self.title)
        layout.addWidget(self.image_preview)
        layout.addLayout(btn_row)
        layout.addStretch()
        layout.addWidget(self.submit_btn)
        layout.addWidget(self.status_label)
        layout.addWidget(self.not_found_label)
        layout.addWidget(self.form_widget)

        # ===== Page Layout =====
        main_layout = QVBoxLayout(self)
        main_layout.addStretch()
        main_layout.addWidget(container, alignment=Qt.AlignCenter)
        main_layout.addStretch()

    # ===================== Helpers =====================

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.image_path = file_path
            pixmap = QPixmap(file_path).scaled(
                self.image_preview.width(),
                self.image_preview.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_preview.setPixmap(pixmap)
            self.image_preview.setText("")

    def load_captured_image(self):
        capture_path = BASE_DIR / "captured_images" / "capture.jpg"
        if capture_path.exists():
            self.image_path = str(capture_path)
            pixmap = QPixmap(str(capture_path)).scaled(
                self.image_preview.width(),
                self.image_preview.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_preview.setPixmap(pixmap)
            self.image_preview.setText("")

    def reset_page(self):
        self.image_path = None
        self.image_preview.show()
        self.image_preview.setText("No Image Selected")
        self.upload_btn.show()
        self.capture_btn.show()
        self.submit_btn.show()
        self.status_label.clear()
        self.status_label.show()
        self.not_found_label.hide()
        self.form_widget.hide()

    # ===================== Submit =====================

    def submit(self):
        if not self.image_path:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("Please select or capture an image.")
            return

        self.status_label.setStyleSheet("color: #0d53bb;")
        self.status_label.setText("Checking image...")

        try:
            with open(self.image_path, "rb") as img:
                response = requests.post(
                    f"{BACKEND_URL}/api/check_image",
                    files={"image": img},
                    timeout=10
                )

            data = response.json()

            if data.get("success") and data.get("match"):
                self.image_preview.hide()
                self.upload_btn.hide()
                self.capture_btn.hide()
                self.submit_btn.hide()
                self.status_label.hide()
                self.form_widget.show()
                self.pet_id = data.get("pet_id")

            else:
                self.image_preview.hide()
                self.upload_btn.hide()
                self.capture_btn.hide()
                self.submit_btn.hide()
                self.status_label.hide()
                self.not_found_label.show()

        except Exception as e:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText(f"Backend error: {e}")
    
    def send_finder_info(self):
        # Make sure a pet image was selected before
        if not self.image_path:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("No pet image selected.")
            return

        # Collect form data
        name = self.finder_name.text().strip()
        email = self.finder_email.text().strip()
        address = self.finder_address.text().strip()

        if not name or not email or not address:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("Please fill in all fields.")
            return

        # For simplicity, you need to know the pet_id. 
        # Here, let's assume it was set earlier after image check:
        # e.g., self.pet_id = data.get("pet_id") from the check image API
        if not hasattr(self, "pet_id") or self.pet_id is None:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("No pet matched to send info.")
            return

        self.status_label.setStyleSheet("color: #0d53bb;")
        self.status_label.setText("Sending info to pet owner...")

        try: 
            response = requests.post(
                f"{BACKEND_URL}/api/send_email",
                json={
                    "name": name,
                    "email": email,
                    "address": address,
                    "pet_id": self.pet_id
                },
                timeout=10
            )

            if response.status_code == 200:
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.status_label.setText("Info sent successfully!")
                self.go_back()
            else:
                data = response.json()
                self.status_label.setStyleSheet("color: red;")
                self.status_label.setText(data.get("message", "Failed to send info."))

        except Exception as e:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText(f"Error contacting backend: {e}")

