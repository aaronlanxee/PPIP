import sys
import os
import json
import requests
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Slot, QUrl

# Bridge to pass data to JS
class Bridge(QObject):
    def __init__(self):
        super().__init__()
        self.missing_pets = []

    @Slot(result=str)
    def getMissingPets(self):
        # Return JSON string
        return json.dumps(self.missing_pets)

# PySide6 app
app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Missing Pets Map")
window.resize(1000, 700)

central = QWidget()
window.setCentralWidget(central)
layout = QVBoxLayout(central)
layout.setContentsMargins(0, 0, 0, 0)

view = QWebEngineView()
layout.addWidget(view)

# Enable local file access
settings = view.settings()
settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)

# JS-Python bridge
bridge = Bridge()
channel = QWebChannel()
channel.registerObject("bridge", bridge)
view.page().setWebChannel(channel)

# --- Fetch missing pets from API in Python ---
try:
    response = requests.get("http://127.0.0.1:5000/api/missing_pets", timeout=5)
    data = response.json()
    if data.get("success"):
        bridge.missing_pets = data["missing_pets"]
    else:
        print("API error:", data.get("message"))
except Exception as e:
    print("Failed to fetch missing pets:", e)

# Load local map.html
html_path = os.path.abspath("map.html")
view.load(QUrl.fromLocalFile(html_path))

window.show()
sys.exit(app.exec())
