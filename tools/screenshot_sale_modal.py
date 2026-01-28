"""
Screenshot test to see what the dialog actually looks like
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.ui.widgets.advanced_sales_dialog_new import AdvancedSalesDialogNew

SCREENSHOT_DIR = Path(__file__).parent.parent / 'egg_farm_system' / 'assets' / 'screenshots'
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """Run and screenshot the sales dialog"""
    app = QApplication(sys.argv)
    
    # Load stylesheet
    qss_path = Path(__file__).parent.parent / 'egg_farm_system' / 'styles.qss'
    if qss_path.exists():
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    
    # Initialize database
    DatabaseManager.initialize()
    
    # Create and show the dialog
    dialog = AdvancedSalesDialogNew(None, None, farm_id=1)
    dialog.show()
    
    # Screenshot after a delay
    def take_screenshot():
        pixmap = dialog.grab()
        screenshot_path = SCREENSHOT_DIR / 'advanced_sales_dialog_new.png'
        pixmap.save(str(screenshot_path))
        print(f"Screenshot saved: {screenshot_path}")
        
        # Also try to interact
        dialog.carton_spin.setValue(3.0)
        dialog.rate_per_egg_afg.setValue(5.0)
        
        pixmap2 = dialog.grab()
        screenshot_path2 = SCREENSHOT_DIR / 'advanced_sales_dialog_with_values.png'
        pixmap2.save(str(screenshot_path2))
        print(f"Screenshot with values saved: {screenshot_path2}")
        
        # Close after screenshots
        QTimer.singleShot(500, lambda: app.quit())
    
    QTimer.singleShot(1000, take_screenshot)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
