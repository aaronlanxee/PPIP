import sys, folium, tempfile
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QHBoxLayout,
    QPushButton, QVBoxLayout, QStackedWidget, QBoxLayout,
    QTabWidget, QScrollArea, QFrame, QDialog
)

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QPainterPath
from login_page import LoginPage
from neighborhood_tab import NeighborhoodMapWidget
from socket_client import SocketClient

import requests
BACKEND_URL = "http://127.0.0.1:5000/"

BASE_DIR = Path(__file__).resolve().parent

# ===== Floating Notification Dialog =====
class FloatingNotification(QWidget):
    def __init__(self, pet_data, parent=None):
        super().__init__(parent)
        self.pet_data = pet_data
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set to full width
        if parent:
            self.setGeometry(0, 0, parent.width(), 80)
        
        # Main container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(239, 68, 68, 128);
                border: none;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Message text
        message = QLabel("🚨 New Missing Pet!")
        message.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        message.setStyleSheet("color: white;")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        # Fade out animation
        self.opacity = 1.0
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self._fade_out)
        self.fade_timer.start(50)  # Update every 50ms
        self.fade_duration = 3000  # 3 seconds in milliseconds
        self.elapsed_time = 0
        
    def _fade_out(self):
        self.elapsed_time += 50
        
        if self.elapsed_time >= self.fade_duration:
            self.fade_timer.stop()
            self.close()
            return
        
        # Calculate opacity (fade from 1.0 to 0.0)
        self.opacity = 1.0 - (self.elapsed_time / self.fade_duration)
        self.setWindowOpacity(self.opacity)


# ===== Floating Notification Dialog for Found Pet =====
class FloatingFoundNotification(QWidget):
    def __init__(self, pet_data, parent=None):
        super().__init__(parent)
        self.pet_data = pet_data
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set to full width
        if parent:
            self.setGeometry(0, 0, parent.width(), 80)
        
        # Main container with green background
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(34, 197, 94, 128);
                border: none;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Message text
        message = QLabel("🎉 Great news! Your pet has been found!")
        message.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        message.setStyleSheet("color: white;")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)
        
        # Fade out animation
        self.opacity = 1.0
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self._fade_out)
        self.fade_timer.start(50)  # Update every 50ms
        self.fade_duration = 3000  # 3 seconds in milliseconds
        self.elapsed_time = 0
        
    def _fade_out(self):
        self.elapsed_time += 50
        
        if self.elapsed_time >= self.fade_duration:
            self.fade_timer.stop()
            self.close()
            return
        
        # Calculate opacity (fade from 1.0 to 0.0)
        self.opacity = 1.0 - (self.elapsed_time / self.fade_duration)
        self.setWindowOpacity(self.opacity)

class HomePage(QWidget):
    def __init__(self, go_to_login, go_to_add_pet, go_to_add_missing_page, go_to_missing_page, go_to_found_pet_page):
        super().__init__()
        self.log_out = go_to_login
        self.user_id = None
        self.add_pet = go_to_add_pet
        self.go_to_add_missing_page = go_to_add_missing_page
        self.go_to_missing_page = go_to_missing_page
        self.go_to_found_pet_page = go_to_found_pet_page
        
        # Initialize WebSocket client
        self.socket_client = SocketClient(BACKEND_URL)
        self.socket_client.pet_missing_signal.connect(self.on_pet_missing_notification)
        self.socket_client.pet_found_signal.connect(self.on_pet_found_notification)

        

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

        # ===== Notifications Tab =====
        notifications_tab = QWidget()
        notifications_layout = QVBoxLayout(notifications_tab)
        notifications_layout.setContentsMargins(20, 20, 20, 20)
        notifications_layout.setSpacing(15)
        notifications_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Title
        notif_title = QLabel("Notifications")
        notif_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        notif_title.setStyleSheet("color: #0d53bb;")
        notif_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        notifications_layout.addWidget(notif_title)

        # Scroll area for notifications
        notif_scroll = QScrollArea()
        notif_scroll.setWidgetResizable(True)
        notif_scroll.setFrameShape(QFrame.Shape.NoFrame)

        notif_content = QWidget()
        notif_content_layout = QVBoxLayout(notif_content)
        notif_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        notif_content_layout.setSpacing(12)

        self.notif_content_layout = notif_content_layout  # save for later updates

        notif_scroll.setWidget(notif_content)
        notifications_layout.addWidget(notif_scroll)

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
        tabs.addTab(notifications_tab, "Notifications")
        tabs.addTab(profile_tab, "Profile")   
        tabs.currentChanged.connect(
            lambda index: neighborhood_tab.load_map() if index == 2 else None
        )


        main_layout.addWidget(tabs)

    def on_pet_missing_notification(self, notification_data):
        """
        Called when a pet missing notification is received via WebSocket.
        Displays the pet info as a card in the notifications tab and shows floating notification.
        """
        try:
            pet = notification_data
            
            # Show floating notification at the top of the screen
            floating_notif = FloatingNotification(pet, parent=self)
            floating_notif.move(0, 60)  # Position below the navbar
            floating_notif.show()
            
            pet_card = QFrame()
            pet_card.setFixedWidth(600)
            pet_card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 10px;
                    border: 1px solid #ff6b6b;
                    padding: 5px;
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
                    background-color: #f0f0f0;
                    border-radius: 10px;
                }
            """)

            # Use pet image from notification if exists
            if pet.get("image"):
                from base64 import b64decode
                from PySide6.QtCore import QByteArray

                img_bytes = b64decode(pet["image"])
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray(img_bytes))
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

            # Add "Missing!" badge
            missing_badge = QLabel("🚨 MISSING PET ALERT")
            missing_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            missing_badge.setStyleSheet("color: #ff6b6b;")

            pet_name = QLabel(f"Name: {pet.get('name', 'Unknown')}")
            pet_name.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))

            pet_type = QLabel(f"Type: {pet.get('type', 'Unknown')}")
            pet_age = QLabel(f"Age: {pet.get('age', 'Unknown')} years")
            pet_breed = QLabel(f"Breed: {pet.get('breed', 'Unknown')}")

            for label in (pet_type, pet_age, pet_breed):
                label.setFont(QFont("Segoe UI", 11))
                label.setStyleSheet("color: #374151;")

            info_layout.addWidget(missing_badge)
            info_layout.addWidget(pet_name)
            info_layout.addWidget(pet_type)
            info_layout.addWidget(pet_age)
            info_layout.addWidget(pet_breed)
            
            # Add location info if available
            if pet.get("missing_location"):
                location_text = f"Location: {pet['missing_location'][0]:.4f}, {pet['missing_location'][1]:.4f}"
                location_label = QLabel(location_text)
                location_label.setFont(QFont("Segoe UI", 10))
                location_label.setStyleSheet("color: #dc2626;")
                info_layout.addWidget(location_label)
            
            info_layout.addStretch()

            # --- Add image and info to card ---
            card_layout.addWidget(pet_image, alignment=Qt.AlignmentFlag.AlignTop)
            card_layout.addLayout(info_layout)

            # --- Add card to notifications layout ---
            self.notif_content_layout.insertWidget(0, pet_card)  # Add to top
            
            print(f"✓ Added notification for pet: {pet.get('name')}")

        except Exception as e:
            print(f"Error displaying pet notification: {e}")

    def on_pet_found_notification(self, notification_data):
        """
        Called when a pet found notification is received via WebSocket.
        Display a success notification to the owner.
        """
        try:
            pet = notification_data
            message = pet.get("message", "A pet has been found!")
            
            # Show floating notification in green
            floating_notif = FloatingFoundNotification(pet, parent=self)
            floating_notif.move(0, 60)  # Position below the navbar
            floating_notif.show()
            
            print(f"✓ Pet found notification received: {message}")
            
        except Exception as e:
            print(f"Error displaying pet found notification: {e}")


    def load_user(self, user_id):
        """
        Load user info and pets from backend and populate the profile and pets tab.
        Connect to WebSocket for real-time notifications.
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
                
                # Connect to WebSocket server with user_id
                if not self.socket_client.connected:
                    self.socket_client.connect(user_id=self.user_id)

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
                            from PySide6.QtCore import QByteArray

                            img_bytes = b64decode(pet["image"])
                            pixmap = QPixmap()
                            pixmap.loadFromData(QByteArray(img_bytes))
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

