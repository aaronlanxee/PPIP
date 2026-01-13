import logging
logging.getLogger("ultralytics").setLevel(logging.ERROR)

import cv2
from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap

from ultralytics import YOLO # type: ignore


class CameraPage(QWidget):
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.go_back_callback = go_back_callback

        # Load YOLO ONCE (no camera yet)
        self.model = YOLO("yolov8n.pt")
        self.TARGET_CLASSES = [15, 16]

        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # ---------------- UI ----------------
        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet(
            "background-color: black; border-radius: 12px;"
        )

        self.capture_btn = QPushButton("📸", self.video_label)
        self.capture_btn.setFixedSize(56, 56)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7DFF;
                border-radius: 28px;
                color: white;
                font-size: 20px;
            }
            QPushButton:hover { background-color: #1E5EFF; }
        """)
        self.capture_btn.clicked.connect(self.capture_image)

        self.back_btn = QPushButton("⬅", self.video_label)
        self.back_btn.setFixedSize(44, 44)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,0,0,140);
                border-radius: 22px;
                color: white;
                font-size: 18px;
            }
        """)
        self.back_btn.clicked.connect(self.go_back)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.video_label)

        self.current_frame = None

    # ---------------- PAGE LIFECYCLE ----------------

    def showEvent(self, event):
        """Called when page becomes visible"""
        super().showEvent(event)
        self.start_camera()

    def hideEvent(self, event):
        """Called when page is hidden"""
        super().hideEvent(event)
        self.stop_camera()

    # ---------------- CAMERA CONTROL ----------------

    def start_camera(self):
        if self.cap is not None:
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.cap = None
            return

        self.timer.start(30)

    def stop_camera(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

        self.video_label.clear()
        self.video_label.setStyleSheet(
            "background-color: black; border-radius: 12px;"
        )

    # ---------------- CAMERA LOOP ----------------

    def update_frame(self):
        if not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # YOLO inference (NO LOGS)
        results = self.model(frame, conf=0.4, verbose=False)

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id in self.TARGET_CLASSES:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = self.model.names[cls_id]
                    conf = box.conf[0]

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"{label} {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

        self.current_frame = frame.copy()

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(
            rgb.data, w, h, ch * w, QImage.Format.Format_RGB888
        )
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

    # ---------------- ACTIONS ----------------

    def capture_image(self):
        if self.current_frame is None:
            return

        save_dir = Path("../assets/captured_images")
        save_dir.mkdir(exist_ok=True)

        # Only capture the first detected target
        cropped_saved = False

        results = self.model(self.current_frame, conf=0.4, verbose=False)
        
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id in self.TARGET_CLASSES:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Crop the detected pet from the frame
                    cropped_frame = self.current_frame[y1:y2, x1:x2]

                    # Save cropped image
                    filename = save_dir / "capture.jpg"
                    cv2.imwrite(str(filename), cropped_frame)
                    cropped_saved = True
                    break  # only capture first detected rectangle
            if cropped_saved:
                break

        if not cropped_saved:
            # If no rectangles detected, fallback to full image
            filename = save_dir / "capture.jpg"
            cv2.imwrite(str(filename), self.current_frame)
        self.go_back()

    def go_back(self):
        self.stop_camera()
        if self.go_back_callback:
            self.go_back_callback()

    # ---------------- FLOATING BUTTON POSITIONS ----------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.video_label.width()
        h = self.video_label.height()

        self.capture_btn.move(
            w // 2 - self.capture_btn.width() // 2,
            h - self.capture_btn.height() - 16
        )
        self.back_btn.move(16, 16)
