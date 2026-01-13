import sys, folium, tempfile
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QHBoxLayout,
    QPushButton, QVBoxLayout, QStackedWidget, QBoxLayout,
    QTabWidget, QScrollArea, QFrame
)

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QPainterPath
from login_page import LoginPage
from neighborhood_tab import NeighborhoodMapWidget

import requests
BACKEND_URL = "http://127.0.0.1:5000/"

BASE_DIR = Path(__file__).resolve().parent

class HomePage(QWidget):
    def __init__(self, go_to_login, go_to_add_pet, go_to_add_missing_page, go_to_missing_page, go_to_found_pet_page):
        super().__init__()
        self.log_out = go_to_login
        self.user_id = None
        self.add_pet = go_to_add_pet
        self.go_to_add_missing_page = go_to_add_missing_page
        self.go_to_missing_page = go_to_missing_page
        self.go_to_found_pet_page = go_to_found_pet_page

        

        # ===== Main Layout =====
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)

        # ===== Top Navigation Bar =====
        navbar = QWidget()
        navbar.setFixedHeight(60)
        navbar.setStyleSheet("""
            QWidget {
                background-color: #0d53bb;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;

            }
        """)

        navbar_layout = QHBoxLayout(navbar)

        navbar_layout.addStretch()

        logo = QLabel("Pawprints in Pixles")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        logo.setStyleSheet("color: white;")
        navbar_layout.addWidget(logo)

        navbar_layout.addStretch()

        main_layout.addWidget(navbar)

        # ===== Tab Widget =====
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.South)
        tabs.setDocumentMode(True)

        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #000000;
            }

            QTabBar {
                background-color: #f0f0f0;
            }

            QTabBar::tab {
                font-family: "Segoe UI";
                font-size: 16px;
                font-weight: bold;
                min-width: 0;
                padding: 14px 0;
                color: #374151;
                border: none;

            }

            QTabBar::tab:selected {
                background-color: #0d53bb;
                color: white;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }

            QTabBar::tab:hover {
                background-color: #9ca3af;
                color: white;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }
        """)

        tab_bar = tabs.tabBar()
        tab_bar.setExpanding(True)

        # ===== Home Tab =====
        home_tab = QWidget()
        home_layout = QVBoxLayout(home_tab)
        home_layout.setSpacing(0)          
        home_layout.setContentsMargins(0, 0, 0, 0) 

        # ===== First Row: Full Width =====
        first_row = QWidget()
        first_row.setStyleSheet("""
            background-color: #0d53bb;s
        """)
        # ===== Add Image inside first_row =====
        image_label = QLabel(first_row)  # QLabel child of first_row
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Get the size of first_row
        row_width = 750   # replace with your window width
        row_height = 350  # approximate height for first row, adjust as needed
        image_label.setFixedSize(row_width, row_height)

        # Load image
        pixmap = QPixmap(str(BASE_DIR / ".."/ "assets" / "welcome.png"))

        # Scale image to fill the row and crop excess
        pixmap = pixmap.scaled(
            row_width, row_height,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        image_label.setPixmap(pixmap)
        # Add first row with stretch factor 3 (takes more space)
        home_layout.addWidget(first_row, 3)

        # ===== Second Row: Full Width =====
        second_row = QWidget()
        second_row.setStyleSheet("""
            background-color: #0d53bb;
        """)

        # Layout for buttons
        second_row_layout = QHBoxLayout(second_row)
        second_row_layout.setContentsMargins(25, 20, 25, 20)
        second_row_layout.setSpacing(12)
        second_row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ===== Buttons =====
        btn_found = QPushButton("I've found a missing pet.")
        btn_loss = QPushButton("I've loss my pet.")

        # Shared button style
        button_style = """
        QPushButton {
            background-color: white;
            color: #0d53bb;
            font-size: 14px;
            font-weight: bold;
            padding: 10px 18px;
            border-radius: 6px;
            border: none;
        }
        QPushButton:hover {
            background-color: #e5e7eb;
        }
        QPushButton:pressed {
            background-color: #d1d5db;
        }
        """

        btn_found.setStyleSheet(button_style)
        btn_loss.setStyleSheet(button_style)

        # Optional: same height for both
        btn_found.setFixedHeight(40)
        btn_loss.setFixedHeight(40)
        btn_loss.setFixedWidth(220)
        btn_found.setFixedWidth(220)

        btn_loss.clicked.connect(self.go_to_add_missing_page)
        btn_found.clicked.connect(self.go_to_found_pet_page)
        # Add buttons (left aligned)
        second_row_layout.addWidget(btn_found)
        second_row_layout.addWidget(btn_loss)

        # Add second row with stretch factor 1 (smaller)
        home_layout.addWidget(second_row, 1)
        # ===== Posts Tab =====
        pets_tab = QWidget()
        pets_layout = QVBoxLayout(pets_tab)
        pets_layout.setSpacing(0)
        pets_layout.setContentsMargins(0, 0, 0, 0)

        # ===== First Row (Larger) =====
        pets_top_row = QWidget()
        pets_top_row.setStyleSheet("background-color: #0d53bb;")

        pets_top_layout = QVBoxLayout(pets_top_row)
        pets_top_layout.setContentsMargins(0, 0, 0, 0)

        # -------- Scroll Area --------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        pets_top_layout.addWidget(scroll_area)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 20, 0, 20)
        scroll_layout.setSpacing(20)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.scroll_layout = scroll_layout  # <--- store it for later use

        scroll_area.setWidget(scroll_content)
        pets_layout.addWidget(pets_top_row, 3)

        # ===== Second Row (Smaller, Buttons) =====
        pets_bottom_row = QWidget()
        pets_bottom_row.setStyleSheet("""
            background-color: #0d53bb;
        """)

        pets_bottom_layout = QHBoxLayout(pets_bottom_row)
        pets_bottom_layout.setContentsMargins(25, 20, 25, 20)
        pets_bottom_layout.setSpacing(15)
        pets_bottom_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ===== Buttons =====
        btn_view_missing = QPushButton("My Missing Pet")
        btn_add_pet = QPushButton("Add Pet")

        button_style = """
        QPushButton {
            background-color: white;
            color: #0d53bb;
            font-size: 14px;
            font-weight: bold;
            padding: 10px 18px;
            border-radius: 6px;
            border: none;
        }
        QPushButton:hover {
            background-color: #e5e7eb;
        }
        QPushButton:pressed {
            background-color: #d1d5db;
        }
        """
        
        btn_view_missing.setStyleSheet(button_style)
        btn_add_pet.setStyleSheet(button_style)

        btn_view_missing.setFixedHeight(40)
        btn_add_pet.setFixedHeight(40)
        btn_view_missing.setFixedWidth(240)
        btn_add_pet.setFixedWidth(160)
        btn_add_pet.clicked.connect(self.add_pet)
        btn_view_missing.clicked.connect(self.go_to_missing_page)
        pets_bottom_layout.addWidget(btn_view_missing)
        pets_bottom_layout.addWidget(btn_add_pet)

        # Stretch factor 1 → smaller row
        pets_layout.addWidget(pets_bottom_row, 1)

        # ===== Neighborhood Tab =====
        neighborhood_tab = NeighborhoodMapWidget()
        # ===== Profile Tab =====
        profile_tab = QWidget()
        profile_layout = QVBoxLayout(profile_tab)
        profile_layout.setSpacing(20)
        profile_layout.setContentsMargins(50, 30, 50, 30)
        profile_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # -------- Profile Picture --------
        self.profile_pic = QLabel()
        self.profile_pic.setFixedSize(140, 140)
        self.profile_pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_pic.setStyleSheet("""
            QLabel {
                background-color: #e5e7eb;
                border-radius: 70px;
            }
        """)

        # Load image
        pixmap = QPixmap(str(BASE_DIR / ".." / "assets" / "default_profile.jpg"))

        # --- Make circular pixmap INLINE ---
        size = 140
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

        self.profile_pic.setPixmap(rounded)

        # -------- Username Label --------
        self.profile_username = QLabel("")
        self.profile_username.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.profile_username.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_username.setStyleSheet("color: #0d53bb;")

        # -------- Email Label --------
        self.profile_email = QLabel("")
        self.profile_email.setFont(QFont("Segoe UI", 14))
        self.profile_email.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_email.setStyleSheet("color: #374151;")

        # -------- Logout Button --------
        logout_btn = QPushButton("Logout")
        logout_btn.setFixedHeight(45)
        logout_btn.setFixedWidth(180)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d53bb;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #0F78D1;
            }
            QPushButton:pressed {
                background-color: #0A5A9E;
            }
        """)
        logout_btn.clicked.connect(self.log_out)

        # -------- Add widgets to layout (centered) --------
        profile_layout.addWidget(self.profile_pic, alignment=Qt.AlignmentFlag.AlignHCenter)
        profile_layout.addWidget(self.profile_username, alignment=Qt.AlignmentFlag.AlignHCenter)
        profile_layout.addWidget(self.profile_email, alignment=Qt.AlignmentFlag.AlignHCenter)
        profile_layout.addStretch()  # push logout button to bottom
        profile_layout.addWidget(logout_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ===== Add Tabs =====
        tabs.addTab(home_tab, "Home")
        tabs.addTab(pets_tab, "Pets")
        tabs.addTab(neighborhood_tab, "Neighborhood")
        tabs.addTab(profile_tab, "Profile")   
        tabs.currentChanged.connect(
            lambda index: neighborhood_tab.load_map() if index == 2 else None
        )


        main_layout.addWidget(tabs)

    def load_user(self, user_id):
        """
        Load user info and pets from backend and populate the profile and pets tab.
        """
        try:
            response = requests.get(f"{BACKEND_URL}api/user/{user_id}", timeout=5)
            data = response.json()

            if response.status_code == 200 and data.get("success"):
                self.current_user_data = data["user"]
                self.user_id = self.current_user_data["id"]
                self.profile_username.setText(self.current_user_data["username"])
                self.profile_email.setText(self.current_user_data["email"])
                print(f"Loaded user: {self.current_user_data}")

                for i in reversed(range(self.scroll_layout.count())):
                    widget = self.scroll_layout.itemAt(i).widget()
                    if widget:
                        widget.setParent(None)

                # --- Clear previous pets ---
                if self.current_user_data.get("pets", []):
                    # --- Loop through pets ---
                    for pet in self.current_user_data.get("pets", []):
                        pet_card = QFrame()
                        pet_card.setFixedWidth(600)
                        pet_card.setStyleSheet("""
                            QFrame {
                                background-color: white;
                                border-radius: 10px;
                                border: 1px solid #e5e7eb;
                            }
                        """)

                        card_layout = QHBoxLayout(pet_card)
                        card_layout.setContentsMargins(20, 20, 20, 20)
                        card_layout.setSpacing(20)

                        # --- Pet Image ---
                        pet_image = QLabel()
                        pet_image.setFixedSize(120, 120)
                        pet_image.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                        pet_image.setStyleSheet("""
                            QLabel {
                                background-color: white;
                                border-radius: 10px;
                            }
                        """)

                        # Use pet image from backend if exists
                        if pet.get("image"):
                            from base64 import b64decode
                            import io
                            from PySide6.QtGui import QImage

                            img_bytes = bytes.fromhex(pet["image"])
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


                        # --- Info Layout ---
                        info_layout = QVBoxLayout()
                        info_layout.setSpacing(8)

                        pet_name = QLabel(f"Name: {pet.get('name', '')}")
                        pet_name.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

                        pet_type = QLabel(f"Type: {pet.get('type', '')}")
                        pet_age = QLabel(f"Age: {pet.get('age', '')} years")
                        pet_breed = QLabel(f"Breed: {pet.get('breed', '')}")

                        for label in (pet_type, pet_age, pet_breed):
                            label.setFont(QFont("Segoe UI", 12))
                            label.setStyleSheet("color: #374151;")

                        info_layout.addWidget(pet_name)
                        info_layout.addWidget(pet_type)
                        info_layout.addWidget(pet_age)
                        info_layout.addWidget(pet_breed)
                        info_layout.addStretch()

                        # --- Add image and info to card ---
                        card_layout.addWidget(pet_image, alignment=Qt.AlignmentFlag.AlignTop)
                        card_layout.addLayout(info_layout)

                        # --- Add card to scroll layout ---
                        self.scroll_layout.addWidget(pet_card)

                else:  # No pets registered
                    no_pet_label = QLabel("You don't have any pets registered yet.")
                    no_pet_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
                    no_pet_label.setStyleSheet("color: white;")
                    no_pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.scroll_layout.addWidget(no_pet_label)

                return self.current_user_data

            else:
                self.current_user_data = None
                self.current_user_id = None
                print(f"Failed to load user: {data.get('message')}")
                return None

        except Exception as e:
            print(f"Error loading user: {e}")
            self.current_user_data = None
            self.current_user_id = None
            return None

    def delete_captured_image(self):
        capture_path = Path("../assets/captured_images/capture.jpg")
        if capture_path.exists():
            try:
                capture_path.unlink()
            except Exception as e:
                print(f"Failed to delete captured image: {e}")

