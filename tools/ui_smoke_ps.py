from pathlib import Path
import sys
# ensure project root is on path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'egg_farm_system'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from database.db import DatabaseManager
from ui.main_window import MainWindow
from utils.i18n import get_i18n

SCREEN_DIR = Path(__file__).parent.parent / 'egg_farm_system' / 'assets' / 'screenshots'
SCREEN_DIR.mkdir(parents=True, exist_ok=True)

PAGES = [
    ('dashboard', 'load_dashboard'),
    ('farm_management', 'load_farm_management'),
    ('production', 'load_production'),
    ('feed', 'load_feed_management'),
    ('inventory', 'load_inventory'),
    ('parties', 'load_parties'),
    ('sales', 'load_sales'),
    ('purchases', 'load_purchases'),
    ('expenses', 'load_expenses'),
    ('reports', 'load_reports'),
]


def capture_sequence(window, app, pages, idx=0):
    if idx >= len(pages):
        # all done
        QTimer.singleShot(400, app.quit)
        return

    name, method = pages[idx]
    # call the load method
    try:
        getattr(window, method)()
    except Exception:
        pass

    # allow UI to update then capture
    def do_capture():
        try:
            pix = window.grab()
            out = SCREEN_DIR / f"smoke_ps_{idx:02d}_{name}.png"
            pix.save(str(out))
            print(f"Saved screenshot: {out}")
        except Exception as e:
            print(f"Failed to capture {name}: {e}")
        # proceed to next page
        QTimer.singleShot(300, lambda: capture_sequence(window, app, pages, idx+1))

    QTimer.singleShot(600, do_capture)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # load stylesheet like app.py
    qss_path = Path(__file__).parent.parent / 'egg_farm_system' / 'styles.qss'
    if qss_path.exists():
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())

    DatabaseManager.initialize()
    # set Pashto language
    get_i18n().set_language('ps')

    window = MainWindow()
    window.show()

    # start capture sequence after small delay
    QTimer.singleShot(400, lambda: capture_sequence(window, app, PAGES))

    sys.exit(app.exec())
