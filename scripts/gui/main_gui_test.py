import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Map - RealAirlinesPlanner")
        self.setGeometry(100, 100, 1200, 800)

        # QWebEngineView pour la carte
        self.map_view = QWebEngineView()
        self.refresh_map()

        # Bouton refresh simple
        btn_refresh = QPushButton("Refresh Map")
        btn_refresh.clicked.connect(self.refresh_map)

        # Layout vertical
        layout = QVBoxLayout()
        layout.addWidget(self.map_view)
        layout.addWidget(btn_refresh)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def refresh_map(self):
        map_path = r"C:\Users\Bertrand\Documents\RealAirlinesPlanner\map\map.html"
        self.map_view.load(QUrl.fromLocalFile(map_path))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
