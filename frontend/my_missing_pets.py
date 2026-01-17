import requests
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QSizePolicy
)

from base64 import b64decode
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QFont, QImage

BASE_DIR = Path(__file__).resolve().parent
BACKEND_URL = "http://127.0.0.1:5000/"  # adjust as needed


class MyMissingPetsPage(QWidget):
    def __init__(self, go_back):
        """
        :param go_back: callable function to execute when Back button is pressed
        """
        super().__init__()
        self.user_id = None
        self.go_back = go_back

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar with Back button
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 10)
    
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(100, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d53bb;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #0F78D1; }
        """)
        back_btn.clicked.connect(self.go_back)
        top_bar.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # Scroll area for missing pets
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: #0d53bb; border-radius: 10px;")
        main_layout.addWidget(self.scroll_area)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)

    def load_user(self, user_id):
        """
        Load missing pets for user_id
        """
        self.user_id = user_id

        # Clear previous items
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        try:
            response = requests.get(f"{BACKEND_URL}api/user/{user_id}", timeout=5)
            data = response.json()
            if response.status_code == 200 and data.get("success"):
                pets = data["user"].get("pets", [])
                missing_pets = [pet for pet in pets if pet.get("is_missing") == 1]

                if not missing_pets:
                    no_pet_label = QLabel("You don't have any missing pets.")
                    no_pet_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
                    no_pet_label.setStyleSheet("color: white;")
                    no_pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.scroll_layout.addWidget(no_pet_label)
                    return

                for pet in missing_pets:
                    self.add_pet_card(pet)

            else:
                print("Failed to load user:", data.get("message"))

        except Exception as e:
            print("Error loading user:", e)

    def add_pet_card(self, pet):
        """
        Add a full-width card for a missing pet inside the scroll layout.
        """

        # --- Card frame ---
        pet_card = QFrame()
        pet_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
            }
        """)
        pet_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # --- Card layout ---
        card_layout = QHBoxLayout(pet_card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(20)

        # --- Pet image ---
        pet_image = QLabel()
        pet_image.setFixedSize(120, 120)
        pet_image.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        pet_image.setStyleSheet("QLabel { background-color: white; }")

        # Load image from backend if exists
        if pet.get("image"):
            img_bytes = b64decode(pet["image"])
            image = QImage.fromData(img_bytes)
            pixmap = QPixmap.fromImage(image)
        else:
            pixmap = QPixmap(str(BASE_DIR / ".." / "assets" / "default_pet.png"))

        # --- Make circular pixmap ---
        size = 120
        rounded = QPixmap(size, size)
        rounded.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)

        pixmap = pixmap.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        pet_image.setPixmap(rounded)
        card_layout.addWidget(pet_image, alignment=Qt.AlignmentFlag.AlignTop)

        # --- Info layout ---
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        pet_name = QLabel(f"Name: {pet.get('name', '')}")
        pet_name.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

        pet_type = QLabel(f"Type: {pet.get('type', '')}")
        pet_age = QLabel(f"Age: {pet.get('age', '')} years")
        pet_breed = QLabel(f"Breed: {pet.get('breed', '')}")

        for lbl in (pet_type, pet_age, pet_breed):
            lbl.setFont(QFont("Segoe UI", 12))
            lbl.setStyleSheet("color: #374151;")

        info_layout.addWidget(pet_name)
        info_layout.addWidget(pet_type)
        info_layout.addWidget(pet_age)
        info_layout.addWidget(pet_breed)

        # --- Spacer to push button down ---
        info_layout.addStretch()

        # --- Mark as Found button ---
        found_btn = QPushButton("Mark as Found")
        found_btn.setFixedHeight(36)
        found_btn.setStyleSheet("""
            QPushButton {
                background-color: green;
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: green; }
        """)
        found_btn.clicked.connect(lambda checked, pet_id=pet["id"]: self.mark_pet_found(pet_id))
        info_layout.addWidget(found_btn)

        card_layout.addLayout(info_layout)

        # --- Add card to scroll layout ---
        self.scroll_layout.addWidget(pet_card)

        # Ensure scroll content widget expands horizontally
        self.scroll_area.widget().setMinimumWidth(self.scroll_area.viewport().width())


    def mark_pet_found(self, pet_id):
        """
        Call API to mark pet as found
        """
        try:
            response = requests.post(f"{BACKEND_URL}api/pet/{pet_id}/found", timeout=5)
            data = response.json()
            if data.get("success"):
                print(f"Pet {pet_id} marked as found.")
                # Reload missing pets
                if self.user_id:
                    self.load_user(self.user_id)
            else:
                print("Failed to mark pet as found:", data.get("message"))
        except Exception as e:
            print("Error marking pet as found:", e)
