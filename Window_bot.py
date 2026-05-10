import sys
import json
import os
import threading
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel,
    QLineEdit, QComboBox, QVBoxLayout, QHBoxLayout,
    QWidget, QFrame, QGraphicsDropShadowEffect,
    QTabWidget, QScrollArea, QTextEdit
)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QObject
from PySide6.QtGui import QColor, QTextCursor

CONFIG_FILE = "jarvis_config.json"

DEFAULT_CONFIG = {
    "model_name": "deepseek-r1:8b",
    "ollama_address": "http://localhost:11434",
    "voice": "SYNTH_MALE_01",
    "mode": "ai",
    "wake_word": "джарвис",
    "app_map": {
        "ютуб музыка": "https://music.youtube.com/",
        "ютуб": "https://www.youtube.com/",
        "телеграм": "https://web.telegram.org/",
        "блокнот": "notepad.exe",
        "калькулятор": "calc.exe",
        "проводник": "explorer.exe",
        "хром": "chrome.exe",
    },
    "noise_words": ["пожалуйста", "давай", "ну", "короче", "быстро", "сейчас", "мне", "пж", "плиз"],
    "stop_words": ["стоп", "выход", "пока"],
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


class LogSignal(QObject):
    message = Signal(str)


class JarvisUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.bot_thread = None
        self.bot_instance = None
        self.bot_running = False
        self.log_signal = LogSignal()
        self.log_signal.message.connect(self._append_log)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(580, 700)

        self.main_widget = QFrame(self)
        self.main_widget.setObjectName("MainWidget")
        self.main_widget.setGeometry(10, 10, 560, 680)

        self._setup_styles()
        self._init_ui()
        self._load_config_to_ui()

    # ─────────────────────────── STYLES ───────────────────────────

    def _setup_styles(self):
        self.setStyleSheet("""
            #MainWidget {
                background-color: rgba(8, 16, 26, 240);
                border: 2px solid #00f2ff;
                border-radius: 20px;
            }
            QLabel {
                color: #00f2ff;
                font-family: 'Consolas', 'OCR A Extended', monospace;
                letter-spacing: 1px;
            }
            QLabel#SectionLabel {
                color: rgba(0, 242, 255, 140);
                font-size: 10px;
                border-bottom: 1px solid rgba(0, 242, 255, 50);
                padding-bottom: 2px;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: rgba(0, 242, 255, 8);
                border: 1px solid rgba(0, 242, 255, 100);
                color: #000000;
                padding: 8px 10px;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #00f2ff;
                background-color: rgba(0, 242, 255, 15);
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: #0a141e;
                color: #00f2ff;
                border: 1px solid rgba(0, 242, 255, 80);
                selection-background-color: rgba(0, 242, 255, 60);
                selection-color: white;
            }
            QPushButton {
                background-color: transparent;
                border: 1px solid #00f2ff;
                color: #00f2ff;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 16px;
                border-radius: 4px;
                letter-spacing: 1px;
            }
            QPushButton:hover { background-color: rgba(0, 242, 255, 30); color: white; }
            QPushButton:pressed { background-color: rgba(0, 242, 255, 55); }
            QPushButton#StartBtn { border: 2px solid #00f2ff; font-size: 14px; padding: 14px; }
            QPushButton#StopBtn  { border: 2px solid #ff4444; color: #ff4444; font-size: 14px; padding: 14px; }
            QPushButton#StopBtn:hover { background-color: rgba(255, 68, 68, 30); color: white; }
            QPushButton#CloseBtn { border: none; color: rgba(255, 80, 80, 200); font-size: 13px; padding: 4px 8px; }
            QPushButton#SaveBtn  { border: 1px solid #39FF14; color: #39FF14; font-size: 11px; padding: 6px 12px; }
            QPushButton#SaveBtn:hover { background-color: rgba(57, 255, 20, 20); color: white; }
            QPushButton#AddBtn, QPushButton#DelBtn {
                border: 1px solid rgba(0, 242, 255, 70);
                color: rgba(0, 242, 255, 150);
                font-size: 11px; padding: 5px 10px;
            }
            QTabWidget::pane {
                border: 1px solid rgba(0, 242, 255, 55);
                border-radius: 4px; background: transparent;
            }
            QTabBar::tab {
                background: rgba(0, 242, 255, 8);
                border: 1px solid rgba(0, 242, 255, 55);
                border-bottom: none;
                color: rgba(0, 242, 255, 150);
                font-family: 'Consolas', monospace;
                font-size: 11px; padding: 6px 14px; margin-right: 2px;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: rgba(0, 242, 255, 22);
                color: #00f2ff;
                border-color: rgba(0, 242, 255, 110);
            }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: rgba(0,242,255,10); width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: rgba(0,242,255,70); border-radius: 3px; }
        """)

    def _init_ui(self):
        root = QVBoxLayout(self.main_widget)
        root.setContentsMargins(24, 16, 24, 20)
        root.setSpacing(12)

        # Top bar
        top = QHBoxLayout()
        self.led = QLabel("● OFFLINE")
        self.led.setStyleSheet("font-size: 10px; color: #ff4444;")
        title = QLabel("J A R V I S")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; letter-spacing: 4px;")
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.clicked.connect(self.close)
        top.addWidget(self.led)
        top.addStretch()
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.close_btn)
        root.addLayout(top)

        # Tabs
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)
        self.tabs.addTab(self._tab_core(),  "CORE")
        self.tabs.addTab(self._tab_apps(),  "APPS MAP")
        self.tabs.addTab(self._tab_words(), "WORDS")
        self.tabs.addTab(self._tab_log(),   "LOG")

        # Save
        save_row = QHBoxLayout()
        self.save_btn = QPushButton("SAVE CONFIG")
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.clicked.connect(self._save_config_from_ui)
        save_row.addStretch()
        save_row.addWidget(self.save_btn)
        root.addLayout(save_row)

        # Start / Stop
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.start_btn = QPushButton("▶  START")
        self.start_btn.setObjectName("StartBtn")
        self._glow(self.start_btn, QColor(0, 242, 255, 120))
        self.start_btn.clicked.connect(self._on_start)

        self.stop_btn = QPushButton("■  STOP")
        self.stop_btn.setObjectName("StopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        root.addLayout(btn_row)

        footer = QLabel("ENCRYPTED CONNECTION ESTABLISHED")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 8px; color: rgba(0, 242, 255, 60);")
        root.addWidget(footer)

    def _tab_core(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 14, 12, 12)
        lay.setSpacing(10)

        lay.addWidget(self._section("── AI MODEL ──"))
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("deepseek-r1:8b")
        lay.addWidget(self.model_input)

        lay.addWidget(self._section("── OLLAMA ADDRESS ──"))
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("http://localhost:11434")
        lay.addWidget(self.address_input)

        lay.addWidget(self._section("── VOICE PROFILE ──"))
        self.voice_box = QComboBox()
        self.voice_box.addItems(["SYNTH_MALE_01", "SYNTH_FEMALE_02", "COMMANDER_VOICE"])
        lay.addWidget(self.voice_box)

        lay.addWidget(self._section("── START MODE ──"))
        self.mode_box = QComboBox()
        self.mode_box.addItems(["ai", "apps"])
        lay.addWidget(self.mode_box)

        lay.addWidget(self._section("── WAKE WORD ──"))
        self.wake_input = QLineEdit()
        self.wake_input.setPlaceholderText("джарвис")
        lay.addWidget(self.wake_input)

        lay.addStretch()
        return w

    def _tab_apps(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 14, 12, 12)
        lay.setSpacing(8)

        hint = QLabel("Ключ  →  URL или .exe")
        hint.setStyleSheet("font-size: 10px; color: rgba(0,242,255,110);")
        lay.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.apps_layout = QVBoxLayout(content)
        self.apps_layout.setSpacing(6)
        self.apps_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(content)
        lay.addWidget(scroll)

        add_btn = QPushButton("+ ADD ENTRY")
        add_btn.setObjectName("AddBtn")
        add_btn.clicked.connect(lambda: self._add_app_row("", ""))
        lay.addWidget(add_btn)
        return w

    def _tab_words(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 14, 12, 12)
        lay.setSpacing(10)

        lay.addWidget(self._section("── NOISE WORDS (через запятую) ──"))
        self.noise_input = QLineEdit()
        self.noise_input.setPlaceholderText("пожалуйста, давай, ну...")
        lay.addWidget(self.noise_input)

        lay.addWidget(self._section("── STOP WORDS (через запятую) ──"))
        self.stop_input = QLineEdit()
        self.stop_input.setPlaceholderText("стоп, выход, пока")
        lay.addWidget(self.stop_input)

        lay.addStretch()
        return w

    def _tab_log(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 10, 8, 8)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet(
            "background-color: rgba(0,0,0,60); color: #a0e8a0;"
            "font-size: 11px; border: 1px solid rgba(0,242,255,40); border-radius: 4px;"
        )
        lay.addWidget(self.log_box)

        clear_btn = QPushButton("CLEAR LOG")
        clear_btn.setObjectName("AddBtn")
        clear_btn.clicked.connect(self.log_box.clear)
        lay.addWidget(clear_btn)
        return w

    # ─────────────────────────── HELPERS ───────────────────────────

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("SectionLabel")
        return lbl

    def _glow(self, widget, color: QColor):
        fx = QGraphicsDropShadowEffect()
        fx.setBlurRadius(18)
        fx.setColor(color)
        fx.setOffset(0, 0)
        widget.setGraphicsEffect(fx)

    def _add_app_row(self, key: str, value: str):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        key_edit = QLineEdit()
        key_edit.setPlaceholderText("ключ")
        key_edit.setText(key)
        key_edit.setFixedWidth(150)

        val_edit = QLineEdit()
        val_edit.setPlaceholderText("URL или .exe")
        val_edit.setText(value)

        del_btn = QPushButton("✕")
        del_btn.setObjectName("DelBtn")
        del_btn.setFixedWidth(30)
        del_btn.clicked.connect(
            lambda: (self.apps_layout.removeWidget(container), container.deleteLater())
        )

        row.addWidget(key_edit)
        row.addWidget(val_edit)
        row.addWidget(del_btn)
        self.apps_layout.addWidget(container)

    def _append_log(self, text: str):
        self.log_box.append(text)
        self.log_box.moveCursor(QTextCursor.End)

    def log(self, text: str):
        self.log_signal.message.emit(text)

    # ─────────────────────────── CONFIG ───────────────────────────

    def _load_config_to_ui(self):
        cfg = self.config
        self.model_input.setText(cfg.get("model_name", ""))
        self.address_input.setText(cfg.get("ollama_address", ""))

        for box, key in [(self.voice_box, "voice"), (self.mode_box, "mode")]:
            idx = box.findText(cfg.get(key, ""))
            if idx >= 0:
                box.setCurrentIndex(idx)

        self.wake_input.setText(cfg.get("wake_word", ""))

        for key, val in cfg.get("app_map", {}).items():
            self._add_app_row(key, val)

        self.noise_input.setText(", ".join(cfg.get("noise_words", [])))
        self.stop_input.setText(", ".join(cfg.get("stop_words", [])))

    def _collect_config_from_ui(self) -> dict:
        app_map = {}
        for i in range(self.apps_layout.count()):
            item = self.apps_layout.itemAt(i)
            if item and item.widget():
                edits = item.widget().findChildren(QLineEdit)
                if len(edits) >= 2:
                    k, v = edits[0].text().strip(), edits[1].text().strip()
                    if k:
                        app_map[k] = v

        return {
            "model_name":     self.model_input.text().strip() or "deepseek-r1:8b",
            "ollama_address": self.address_input.text().strip() or "http://localhost:11434",
            "voice":          self.voice_box.currentText(),
            "mode":           self.mode_box.currentText(),
            "wake_word":      self.wake_input.text().strip(),
            "app_map":        app_map,
            "noise_words":    [w.strip() for w in self.noise_input.text().split(",") if w.strip()],
            "stop_words":     [w.strip() for w in self.stop_input.text().split(",") if w.strip()],
        }

    def _save_config_from_ui(self):
        self.config = self._collect_config_from_ui()
        save_config(self.config)
        self.log("[CONFIG] Конфигурация сохранена.")
        self.led.setText("● SAVED")
        self.led.setStyleSheet("font-size: 10px; color: #39FF14;")
        QTimer.singleShot(2000, self._refresh_led)

    def _refresh_led(self):
        if self.bot_running:
            self.led.setText("● ACTIVE")
            self.led.setStyleSheet("font-size: 10px; color: #00f2ff;")
        else:
            self.led.setText("● OFFLINE")
            self.led.setStyleSheet("font-size: 10px; color: #ff4444;")

    # ─────────────────────────── BOT CONTROL ───────────────────────────

    def _on_start(self):
        self._save_config_from_ui()
        self.start_btn.setEnabled(False)
        self.start_btn.setText("RUNNING...")
        self.stop_btn.setEnabled(True)
        self.led.setText("● ACTIVE")
        self.led.setStyleSheet("font-size: 10px; color: #00f2ff;")
        self.bot_running = True

        self.bot_thread = threading.Thread(
            target=self._run_bot, args=(self.config,), daemon=True
        )
        self.bot_thread.start()

    def _on_stop(self):
        self.bot_running = False
        if self.bot_instance:
            # Возвращаем стоп-слово чтобы разбудить блокирующий listen()
            self.bot_instance.speech.listen = lambda: "стоп"
        self.log("[JARVIS] Остановка запрошена...")
        self._set_stopped_ui()

    def _set_stopped_ui(self):
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶  START")
        self.stop_btn.setEnabled(False)
        self.led.setText("● OFFLINE")
        self.led.setStyleSheet("font-size: 10px; color: #ff4444;")

    def _run_bot(self, cfg: dict):
        """
        Создаёт MainBot, применяет настройки из GUI и вызывает bot.run().
        Никакой логики бота здесь нет — только конфигурирование и monkey-patch
        speak/listen для отображения лога в интерфейсе.
        """
        try:
            from main_bot import MainBot

            bot = MainBot()
            self.bot_instance = bot

            # Применяем настройки из GUI → в поля MainBot
            bot.ai.model_name = cfg["model_name"]
            bot.mode          = cfg["mode"]
            bot.app_map       = cfg["app_map"]
            bot._noise_words  = set(cfg["noise_words"])

            # Monkey-patch: только логирование, поведение не меняется
            _orig_speak  = bot.speech.speak
            _orig_listen = bot.speech.listen

            def _speak(text):
                self.log(f"[JARVIS] {text}")
                _orig_speak(text)

            def _listen():
                result = _orig_listen()
                if result:
                    self.log(f"[USER]   {result}")
                return result

            bot.speech.speak  = _speak
            bot.speech.listen = _listen

            self.log(f"[CONFIG] model={cfg['model_name']}  mode={cfg['mode']}")

            # Оригинальный run() без изменений
            bot.run()

        except ImportError as e:
            self.log(f"[ERROR] Не удалось импортировать main_bot: {e}")
        except Exception as e:
            self.log(f"[ERROR] {e}")
        finally:
            self.bot_instance = None
            self.bot_running  = False
            QTimer.singleShot(0, self._set_stopped_ui)

    # ─────────────────────────── DRAG ───────────────────────────

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()


