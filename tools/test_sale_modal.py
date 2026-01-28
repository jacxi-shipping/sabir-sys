"""
Test script to run the advanced sales dialog
"""
from pathlib import Path
import sys

# ensure project root is on path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.ui.widgets.advanced_sales_dialog_new import AdvancedSalesDialogNew

def main():
    """Run the sales dialog"""
    app = QApplication(sys.argv)
    
    # Load stylesheet
    qss_path = Path(__file__).parent.parent / 'egg_farm_system' / 'styles.qss'
    if qss_path.exists():
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    
    # Initialize database
    DatabaseManager.initialize()
    
    # Create and show the advanced sales dialog
    dialog = AdvancedSalesDialogNew(None, None, farm_id=1)
    dialog.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
