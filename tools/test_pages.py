import sys
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'egg_farm_system'))
from PySide6.QtWidgets import QApplication
from database.db import DatabaseManager
from ui.main_window import MainWindow

app = QApplication([])
DatabaseManager.initialize()
window = MainWindow()

pages = [
    ('sales', 'load_sales'),
    ('purchases', 'load_purchases'),
    ('expenses', 'load_expenses'),
]

for name, method in pages:
    try:
        print(f"Loading {name}...")
        getattr(window, method)()
        print(f"{name} loaded OK")
    except Exception:
        print(f"Error loading {name}:")
        traceback.print_exc()

DatabaseManager.close()
print('done')
