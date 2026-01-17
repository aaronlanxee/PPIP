from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QPushButton
)
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPainter, QPainterPath
import requests

BACKEND_URL = "http://127.0.0.1:5000/"
BASE_DIR = Path(__file__).resolve().parent


class MarkAsLostPage(QWidget):
    def __init__(self, go_back, go_to_map):
        super().__init__()
        self.go_back = go_back
        self.go_to_map = go_to_map  # callback to open the MapWidget
        self.user_id = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # ===== Back Button =====
        back_btn = QPushButton("← Back")
        back_btn.setFixedHeight(40)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #0d53bb;
                font-weight: bold;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        back_btn.clicked.connect(self.go_back)
        main_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # ===== Scroll Area =====
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        main_layout.addWidget(self.scroll_area)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)
        self.scroll_layout.setContentsMargins(0, 30, 0, 30)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.title_label = QLabel("Who is missing")
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #111827;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll_layout.addWidget(self.title_label)
        self.scroll_area.setWidget(self.scroll_content)

    # --------------------------------------------------
    def load_user(self, user_id):
        self.user_id = user_id

        # Clear existing cards
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.scroll_layout.addWidget(self.title_label)

        # Load pets from backend
        try:
            response = requests.get(f"{BACKEND_URL}api/user/{user_id}")
            data = response.json()
        except Exception as e:
            print(f"Error fetching user: {e}")
            return

        if response.status_code != 200 or not data.get("success"):
            return

        pets = data["user"].get("pets", [])

        if not pets:
            empty = QLabel("You don't have any pets registered yet.")
            empty.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            empty.setStyleSheet("color: #374151;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty)
            return

        for pet in pets:
            if not pet["is_missing"]:
                self.scroll_layout.addWidget(self._create_pet_card(pet))

    # --------------------------------------------------
    def _create_pet_card(self, pet):
        pet_card = QFrame()
        pet_card.setFixedWidth(600)
        pet_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
            }
        """)

        card_layout = QVBoxLayout(pet_card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(20, 20, 20, 20)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)

        # ===== Pet Image (Circular) =====
        pet_image = QLabel()
        pet_image.setFixedSize(120, 120)

        pixmap = QPixmap(str(BASE_DIR / ".." / "assets" / "default_pet.png"))
        if pet.get("image"):
            from PySide6.QtGui import QImage
            import base64
            image = QImage.fromData(base64.b64decode(pet["image"]))
            pixmap = QPixmap.fromImage(image)

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

        # ===== Info =====
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)

        name = QLabel(f"Name: {pet['name']}")
        name.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        pet_type = QLabel(f"Type: {pet['type']}")
        age = QLabel(f"Age: {pet['age']} years")
        breed = QLabel(f"Breed: {pet['breed']}")
        for lbl in (pet_type, age, breed):
            lbl.setFont(QFont("Segoe UI", 12))
            lbl.setStyleSheet("color: #374151;")

        info_layout.addWidget(name)
        info_layout.addWidget(pet_type)
        info_layout.addWidget(age)
        info_layout.addWidget(breed)

        top_layout.addWidget(pet_image)
        top_layout.addLayout(info_layout)

        # ===== Mark as Missing → Open Map =====
        mark_missing_btn = QPushButton("Mark as Missing")
        mark_missing_btn.setFixedHeight(45)
        mark_missing_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        mark_missing_btn.clicked.connect(lambda checked, id=pet['id']: self._show_map(id))

        card_layout.addLayout(top_layout)
        card_layout.addWidget(mark_missing_btn)
        return pet_card

    # --------------------------------------------------
    def _show_map(self, pet_id):
        self.go_to_map(pet_id)
