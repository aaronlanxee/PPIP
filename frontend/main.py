import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from login_page import LoginPage
from home_page import HomePage
from register_page import RegisterPage
from otp_page import OTPVerificationPage
from add_pet_page import AddPetPage
from mark_as_loss_page import MarkAsLostPage
from camera_page import CameraPage
from map_page import MapWidget
from my_missing_pets import MyMissingPetsPage
from found_pet import FoundPetPage

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / ".." / "assets" / "PPIP.ico"
BACKEND_URL = "http://127.0.0.1:5000/"


# ---------------- MAIN WINDOW ----------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PawPrints In Pixels")
        self.setFixedSize(800, 600)
        
        # self.setStyleSheet("background-color: white;")
        self.move(self.screen().geometry().center() - self.rect().center())
        self.stack = QStackedWidget(self)

        self.current_user_id = None

        # Create pages
        self.otp_page = OTPVerificationPage(self.go_to_home, self.go_to_login)
        self.login_page = LoginPage(self.go_to_otp, self.go_to_register)
        self.home_page = HomePage(self.go_to_login, go_to_add_pet=self.go_to_add_pet, go_to_add_missing_page=self.go_to_mark_loss, go_to_missing_page=self.go_to_missing_page, go_to_found_pet_page=self.go_to_found_pet_page)
        self.register_page = RegisterPage(self.go_to_login)
        self.add_pet_page = AddPetPage(self. go_to_home, go_to_camera=self.go_to_camera)
        self.mark_as_loss_page = MarkAsLostPage(self.go_to_home, self.go_to_map)
        self.camera_page = CameraPage(self.go_to_add_pet)
        self.map_page = MapWidget(self.go_to_mark_loss, self.go_to_home)
        self.my_missing_pet_page = MyMissingPetsPage(self.go_to_home)
        self.found_pet_page = FoundPetPage(self.go_to_home, self.go_to_camera)


        # Add pages to stack
        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.register_page)
        self.stack.addWidget(self.otp_page)
        self.stack.addWidget(self.add_pet_page)
        self.stack.addWidget(self.mark_as_loss_page)
        self.stack.addWidget(self.camera_page)
        self.stack.addWidget(self.map_page)
        self.stack.addWidget(self.my_missing_pet_page)
        self.stack.addWidget(self.found_pet_page)


        # Main layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        # Start page
        self.go_to_login()
        self.add_pet_page.delete_captured_image()

    def go_to_login(self):
        self.current_user_id = None
        self.stack.setCurrentWidget(self.login_page)

    def go_to_register(self):
        self.stack.setCurrentWidget(self.register_page)

    def go_to_home(self):
        self.home_page.load_user(self.current_user_id)
        self.stack.setCurrentWidget(self.home_page)

    def go_to_otp(self, username=None, user_id=None):
        self.otp_page.set_username(username)
        self.current_user_id = user_id
        self.stack.setCurrentWidget(self.otp_page)
    
    def go_to_add_pet(self):
        self.add_pet_page.load_captured_image()
        self.stack.setCurrentWidget(self.add_pet_page)

    def go_to_mark_loss(self):
        self.mark_as_loss_page.load_user(self.current_user_id)
        self.stack.setCurrentWidget(self.mark_as_loss_page)
    
    def go_to_camera(self):
        self.stack.setCurrentWidget(self.camera_page)
    
    def go_to_map(self, pet_id=None):
        self.map_page.pet_id = pet_id
        self.stack.setCurrentWidget(self.map_page)

    def go_to_missing_page(self):
        self.my_missing_pet_page.user_id = self.current_user_id
        self.my_missing_pet_page.load_user(self.current_user_id)
        self.stack.setCurrentWidget(self.my_missing_pet_page)

    def go_to_found_pet_page(self):
        self.stack.setCurrentWidget(self.found_pet_page)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())