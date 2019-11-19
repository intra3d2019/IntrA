import ui as ui
import sys

if __name__ == '__main__':
    app = ui.QApplication(sys.argv)
    win = ui.MainWindow()
    sys.exit(app.exec())
