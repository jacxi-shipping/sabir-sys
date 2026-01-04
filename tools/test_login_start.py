from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'egg_farm_system'))
from PySide6.QtWidgets import QApplication
from database.db import DatabaseManager
from modules.users import UserManager
from ui.main_window import MainWindow

if __name__ == '__main__':
    DatabaseManager.initialize()
    user = UserManager.get_user_by_username('admin')
    app = QApplication([])
    win = MainWindow(current_user=user)
    print('MainWindow instantiated with user:', user)
    try:
        print('user_label:', win.user_label.text())
    except Exception:
        print('user_label not present')
    win.close()
    app.quit()
