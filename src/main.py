# init application before everything
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase, QFont
app = QApplication(sys.argv)
QFontDatabase.addApplicationFont("res/fonts/HarmonyOS_Sans_SC_Regular.ttf")
app.setFont(QFont("HarmonyOS Sans SC"))

# main
from modules.ui.windows import MainWindow

window = MainWindow()
window.show()
app.exec()