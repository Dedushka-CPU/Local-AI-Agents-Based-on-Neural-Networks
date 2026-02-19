import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                             QLineEdit, QComboBox, QVBoxLayout, QWidget, QFrame, QHBoxLayout)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                             QLineEdit, QComboBox, QVBoxLayout, QWidget, QFrame, 
                             QHBoxLayout, QGraphicsDropShadowEffect) 
from PyQt5.QtGui import QFont, QColor

class JarvisTechUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 600)

        self.main_widget = QFrame(self)
        self.main_widget.setObjectName("MainWidget")
        self.main_widget.setGeometry(10, 10, 480, 580)
        
        self.setup_styles()
        self.init_ui()

    def setup_styles(self):
        self.setStyleSheet("""
            #MainWidget {
                background-color: rgba(10, 20, 30, 230);
                border: 2px solid #00f2ff;
                border-radius: 20px;
            }
            QLabel {
                color: #00f2ff;
                font-family: 'OCR A Extended', 'Consolas', sans-serif;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            QLineEdit, QComboBox {
                background-color: rgba(0, 242, 255, 10);
                border: 1px solid #00f2ff;
                color: white;
                padding: 10px;
                border-radius: 2px;
                font-family: 'Consolas';
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #0a141e;
                color: #00f2ff;
                selection-background-color: #00f2ff;
                selection-color: #0a141e;
            }
            QPushButton {
                background-color: transparent;
                border: 2px solid #00f2ff;
                color: #00f2ff;
                font-weight: bold;
                font-size: 14px;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: rgba(0, 242, 255, 40);
                color: white;
                text-shadow: 0 0 10px #00f2ff;
            }
            #CloseBtn {
                border: none;
                color: #ff4444;
                font-size: 18px;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout(self.main_widget)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(15)

        top_bar = QHBoxLayout()
        self.status_led = QLabel("● SYSTEM READY")
        self.status_led.setStyleSheet("font-size: 10px; color: #39FF14;")
        self.close_btn = QPushButton("CLOSE")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close)
        top_bar.addWidget(self.status_led)
        top_bar.addStretch()
        top_bar.addWidget(self.close_btn)
        layout.addLayout(top_bar)

        # Заголовок
        title = QLabel("JARVIS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Поля выбора
        layout.addWidget(QLabel("── Core Model ──"))
        self.model_box = QComboBox()
        self.model_box.addItems(["deepseek", "qwen", ])
        layout.addWidget(self.model_box)

        layout.addWidget(QLabel("── Network Protocol ──"))
        self.address_input = QLineEdit()
        self.address_input.setText("https://localhost:8080")
        layout.addWidget(self.address_input)

        layout.addWidget(QLabel("── Vocal Matrix ──"))
        self.voice_box = QComboBox()
        self.voice_box.addItems(["SYNTH_MALE_01", "SYNTH_FEMALE_02", "COMMANDER_VOICE"])
        layout.addWidget(self.voice_box)

        layout.addStretch()

        self.start_btn = QPushButton("START")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 242, 255, 150))
        shadow.setOffset(0, 0)
        self.start_btn.setGraphicsEffect(shadow)
        self.start_btn.clicked.connect(self.on_start)
        layout.addWidget(self.start_btn)

        footer = QLabel("ENCRYPTED CONNECTION ESTABLISHED")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 8px; color: rgba(0, 242, 255, 100);")
        layout.addWidget(footer)

    def on_start(self):
        self.status_led.setText("● PROTOCOL ACTIVE")
        self.status_led.setStyleSheet("font-size: 10px; color: #00f2ff;")
        self.start_btn.setText("SYSTEM RUNNING...")

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisTechUI()
    window.show()
    sys.exit(app.exec_())