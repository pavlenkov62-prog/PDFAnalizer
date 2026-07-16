import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from gui import MainWindow


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("PDF Translator")
    app.setApplicationDisplayName("PDF Translator")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()