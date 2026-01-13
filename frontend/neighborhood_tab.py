import os
import json
import requests
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Slot, QUrl, QTimer

BACKEND_URL = "http://127.0.0.1:5000/"  # adjust if needed


class Bridge(QObject):
    """JS-Python bridge to provide missing pets data."""
    def __init__(self):
        super().__init__()
        self.missing_pets = []

    @Slot(result=str)
    def getMissingPets(self):
        return json.dumps(self.missing_pets)


class NeighborhoodMapWidget(QWidget):
    """Neighborhood tab widget showing missing pets map."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bridge = Bridge()

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # QWebEngineView
        self.view = QWebEngineView()
        layout.addWidget(self.view)

        # Enable local file access
        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)

        # JS-Python bridge
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Map HTML path
        self.html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/map1.html"))

    def load_map(self):
        """Fetch missing pets and reload the map HTML."""
        try:
            # Fetch latest missing pets
            response = requests.get(f"{BACKEND_URL}api/missing_pets", timeout=5)
            data = response.json()
            if data.get("success"):
                self.bridge.missing_pets = data["missing_pets"]
            else:
                print("API error:", data.get("message"))
        except Exception as e:
            print("Failed to fetch missing pets:", e)

        # Reload the map HTML to reinitialize Leaflet with new data
        self.view.load(QUrl.fromLocalFile(self.html_path))
