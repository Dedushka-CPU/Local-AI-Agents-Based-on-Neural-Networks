import sys
from PySide6.QtWidgets import QApplication
from Window_bot import JarvisUI

# from main_bot import MainBot
# if __name__ == "__main__":
#     bot = MainBot()
#     bot.run()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisUI()
    window.show()
    sys.exit(app.exec())