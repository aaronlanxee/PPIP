import os, requests
from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Slot, QUrl, Signal, Qt

BACKEND_URL = "http://127.0.0.1:5000/"

# --------------------------------------------------
# Bridge: JS → Python
# --------------------------------------------------
class Bridge(QObject):
    def __init__(self):
        super().__init__()
        self.last_location = None

    @Slot(float, float)
    def pinClicked(self, lat, lng):
        self.last_location = (lat, lng)
        print(f"📍 Pin clicked at: {lat}, {lng}")


# --------------------------------------------------
# Map Widget
# --------------------------------------------------
class MapWidget(QWidget):
    pinConfirmed = Signal(float, float)

    def __init__(self, go_back, go_to_home, parent=None):
        super().__init__(parent)
        self.go_back = go_back
        self.pet_id = None
        self.go_to_home = go_to_home

        # ===== Layout =====
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # ===== Map View =====
        self.view = QWebEngineView(self)
        self.layout.addWidget(self.view)

        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True) # type: ignore
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True) # type: ignore

        # ===== Bridge =====
        self.bridge = Bridge()
        channel = QWebChannel(self.view.page())
        channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(channel)

        # ===== Load map =====
        html_path = os.path.abspath("../assets/map.html")
        self.view.load(QUrl.fromLocalFile(html_path))

        # --------------------------------------------------
        # Overlay UI
        # --------------------------------------------------
        # 🔙 Back button (top-left)
        self.back_button = QPushButton("← Back", self)
        self.back_button.setFixedSize(80, 36)
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 160);
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 200);
            }
        """)

        # 🏷️ Title (top-center)
        self.title_label = QLabel("Pin last seen location", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 160);
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
        """)

        # 📍 PIN button (bottom-center)
        self.pin_button = QPushButton("PIN", self)
        self.pin_button.setFixedSize(100, 40)
        self.pin_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #005ea6;
            }
        """)
        self.pin_button.clicked.connect(self._confirm_pin)

        # ===== Message widget (hidden initially) =====
        self.message_widget = QWidget(self)
        self.message_layout = QVBoxLayout(self.message_widget)
        self.message_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label = QLabel(
            "We're sorry to know that.\nWe will notify you when someone finds him/her."
        )
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2563eb;")
        self.back_home_btn = QPushButton("Back to Home")
        self.back_home_btn.setFixedHeight(40)
        self.back_home_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d53bb;
                color: white;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #0a3e8c;
            }
        """)
        self.back_home_btn.clicked.connect(self.go_to_home)

        self.message_layout.addWidget(self.message_label)
        self.message_layout.addWidget(self.back_home_btn)
        self.message_widget.hide()
        self.layout.addWidget(self.message_widget)

    # --------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        self.back_button.move(16, 16)
        self.title_label.adjustSize()
        self.title_label.move((w - self.title_label.width()) // 2, 16)
        self.pin_button.move((w - 100) // 2, h - 60)

    # --------------------------------------------------
    def _confirm_pin(self):
        if not self.bridge.last_location:
            print("❌ No pin selected yet!")
            return

        if not hasattr(self, "pet_id") or self.pet_id is None:
            print("❌ No pet ID provided for this map!")
            return

        lat, lng = self.bridge.last_location
        print(f"✅ Pin confirmed: {lat}, {lng}")

        # --- Send POST request to backend ---
        try:
            response = requests.post(
                f"{BACKEND_URL}api/pet/{self.pet_id}/mark_missing",
                json={"missing_location": [lat, lng]},
                timeout=5
            )
            data = response.json()
            if response.status_code == 200 and data.get("success"):
                print(f"Pet {self.pet_id} marked as missing successfully.")
            else:
                print(f"Failed to mark pet {self.pet_id} as missing: {data.get('message')}")
        except Exception as e:
            print(f"Error marking pet {self.pet_id} as missing: {e}")

        # Hide map view & overlay UI
        self.view.hide()
        self.back_button.hide()
        self.title_label.hide()
        self.pin_button.hide()

        # Show message widget
        self.message_widget.show()

    # --------------------------------------------------
    def reset(self):
        """Call this before showing the map again"""
        self.bridge.last_location = None
        self.view.show()
        self.back_button.show()
        self.title_label.show()
        self.pin_button.show()
        self.message_widget.hide()
        self.pet_id = None
