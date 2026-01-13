from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, QTimer

import requests
BACKEND_URL = "http://127.0.0.1:5000"

BASE_DIR = Path(__file__).resolve().parent


class AddPetPage(QWidget):
    def __init__(self, go_back, go_to_camera):
        super().__init__()
        self.go_back = go_back
        self.image_path = None
        self.user_id = None
        self.go_to_camera = go_to_camera

        # -------- Container (card) --------
        container = QWidget()
        container.setFixedSize(500, 620)

        form_layout = QVBoxLayout(container)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(20, 20, 20, 20)

        # -------- Top bar (Back button) --------
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setFixedHeight(32)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0d53bb;
                font-size: 14px;
                font-weight: bold;
                border: none;
                text-align: left;
            }
            QPushButton:hover {
                color: #0F78D1;
                text-decoration: underline;
            }
        """)
        back_btn.clicked.connect(self.delete_captured_image)
        back_btn.clicked.connect(self.go_back)
        back_btn.clicked.connect(lambda: self.image_preview.clear())
        top_bar.addWidget(back_btn)
        top_bar.addStretch()

        # -------- Title --------
        title = QLabel("Add Pet")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #0d53bb;")

        # -------- Input Style --------
        input_style = """
            QLineEdit {
                border: 2px solid #0d53bb;
                border-radius: 10px;
                padding: 8px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #1E90FF;
            }
        """

        # -------- Inputs --------
        self.pet_type = QLineEdit()
        self.pet_type.setPlaceholderText("Type of Pet (Dog, Cat, etc.)")
        self.pet_type.setFixedHeight(45)
        self.pet_type.setStyleSheet(input_style)

        self.pet_name = QLineEdit()
        self.pet_name.setPlaceholderText("Pet Name")
        self.pet_name.setFixedHeight(45)
        self.pet_name.setStyleSheet(input_style)

        self.pet_age = QLineEdit()
        self.pet_age.setPlaceholderText("Age")
        self.pet_age.setFixedHeight(45)
        self.pet_age.setStyleSheet(input_style)

        self.pet_breed = QLineEdit()
        self.pet_breed.setPlaceholderText("Breed")
        self.pet_breed.setFixedHeight(45)
        self.pet_breed.setStyleSheet(input_style)

        # -------- Image Preview --------
        self.image_preview = QLabel("No Image Selected")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setFixedHeight(160)
        self.image_preview.setStyleSheet("""
            QLabel {
                border: 2px dashed #0d53bb;
                border-radius: 10px;
                color: #6b7280;
                font-size: 12px;
            }
        """)

        # -------- Upload Button --------
        upload_btn = QPushButton("Upload Image")
        upload_btn.setFixedHeight(40)
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #0d53bb;
                border: 2px solid #0d53bb;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E0F0FF;
            }
        """)

        capture_btn = QPushButton("Capture Image")
        capture_btn.setFixedHeight(40)
        capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d53bb;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0F78D1;
            }
        """)
        capture_btn.clicked.connect(self.go_to_camera)
        upload_btn.clicked.connect(self.select_image)

        # -------- Submit Button --------
        submit_btn = QPushButton("Submit")
        submit_btn.setFixedHeight(45)
        submit_btn.setStyleSheet("""
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
        submit_btn.clicked.connect(self.submit)

        # -------- Error Label --------
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")

        # -------- Layout Assembly --------
        form_layout.addLayout(top_bar)
        form_layout.addWidget(title)
        form_layout.addWidget(self.pet_type)
        form_layout.addWidget(self.pet_name)
        form_layout.addWidget(self.pet_age)
        form_layout.addWidget(self.pet_breed)
        form_layout.addWidget(self.image_preview)
        image_btn_layout = QHBoxLayout()
        image_btn_layout.setSpacing(10)
        image_btn_layout.addWidget(upload_btn)
        image_btn_layout.addWidget(capture_btn)

        form_layout.addLayout(image_btn_layout)

        form_layout.addWidget(submit_btn)
        form_layout.addWidget(self.error_label)

        # -------- Main Layout --------
        main_layout = QVBoxLayout(self)
        main_layout.addStretch()
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()

    # -------- Image Picker --------
    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Pet Image",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )

        if file_path:
            self.image_path = file_path
            pixmap = QPixmap(file_path)
            pixmap = pixmap.scaled(
                self.image_preview.width(),
                self.image_preview.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_preview.setPixmap(pixmap)
            self.image_preview.setText("")

    # -------- Submit Handler --------
    def submit(self):
        if not all([
            self.pet_type.text(),
            self.pet_name.text(),
            self.pet_age.text(),
            self.pet_breed.text()
        ]):
            self.error_label.setText("Please fill in all fields.")
            return

        self.error_label.setText("Submitting...")

        data = {
            "type": self.pet_type.text(),
            "name": self.pet_name.text(),
            "age": self.pet_age.text(),
            "breed": self.pet_breed.text(),
        }

        files = {}
        if self.image_path:
            image_file_path = Path(self.image_path)
            try:
                # Open the image as binary only if it exists
                files["image"] = (
                    image_file_path.name, 
                    open(image_file_path, "rb"), 
                    "application/octet-stream"
                )
            except Exception as e:
                self.error_label.setText(f"Failed to read image: {e}")
                return

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/register_pet",
                data=data,
                files=files if files else None,
                timeout=5
            )

            # Close the file after upload
            if "image" in files:
                files["image"][1].close()

            if response.status_code == 200:
                self.pet_name.setText("")
                self.pet_age.setText("")
                self.pet_type.setText("")
                self.pet_breed.setText("")
                self.image_preview.clear()
                self.error_label.setStyleSheet("color: green; font-size: 12px; font-weight: bold;")
                self.error_label.setText("Pet registered successfully!")
                
                
                QTimer.singleShot(2000, self.go_back)
                self.error_label.setText("")
            else:
                self.error_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")
                self.error_label.setText(response.json().get("message", "Error registering pet"))
                self.delete_captured_image()
        except Exception as e:
            self.error_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")
            self.error_label.setText(f"Backend not reachable: {e}")

    def load_captured_image(self):
        capture_path = Path(str(BASE_DIR / "captured_images" / "capture.jpg"))
        if capture_path.exists():
            self.image_path = str(capture_path)

            pixmap = QPixmap(str(capture_path))
            pixmap = pixmap.scaled(
                self.image_preview.width(),
                self.image_preview.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_preview.setPixmap(pixmap)
            self.image_preview.setText("")

    def delete_captured_image(self):
        capture_path = Path(str(BASE_DIR / "captured_images" / "capture.jpg"))
        if capture_path.exists():
            try:
                capture_path.unlink()
            except Exception as e:
                print(f"Failed to delete captured image: {e}")
    
    