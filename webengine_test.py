import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

app = QApplication(sys.argv)
window = QMainWindow()
view = QWebEngineView(window)
view.load(QUrl("https://www.google.com"))
window.setCentralWidget(view)
window.resize(900, 600)
window.show()
sys.exit(app.exec_())

