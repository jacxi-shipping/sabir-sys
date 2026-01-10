"""
Debug test script to check input field functionality
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt, QTimer
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.ui.widgets.advanced_sales_dialog_new import AdvancedSalesDialogNew

class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sales Dialog Test")
        self.setGeometry(100, 100, 300, 200)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Click button to open dialog")
        layout.addWidget(self.status_label)
        
        btn = QPushButton("Open Sales Dialog")
        btn.clicked.connect(self.open_dialog)
        layout.addWidget(btn)
        
        self.setLayout(layout)
    
    def open_dialog(self):
        """Open the sales dialog"""
        self.status_label.setText("Opening dialog...")
        dialog = AdvancedSalesDialogNew(self, None, farm_id=1)
        
        # Try to programmatically test input
        QTimer.singleShot(500, lambda: self.test_inputs(dialog))
        
        result = dialog.exec()
        self.status_label.setText(f"Dialog closed with result: {result}")
    
    def test_inputs(self, dialog):
        """Test if inputs respond"""
        try:
            print("Testing spinbox value change...")
            initial_value = dialog.carton_spin.value()
            print(f"Initial carton value: {initial_value}")
            
            # Try to set value
            dialog.carton_spin.setValue(5.0)
            print(f"Set carton to 5.0")
            
            new_value = dialog.carton_spin.value()
            print(f"Current carton value: {new_value}")
            
            # Check if enabled
            print(f"Carton spinbox enabled: {dialog.carton_spin.isEnabled()}")
            print(f"Carton spinbox visible: {dialog.carton_spin.isVisible()}")
            print(f"Carton spinbox can focus: {dialog.carton_spin.focusPolicy()}")
            
            # Test other fields
            print(f"\nParty combo enabled: {dialog.party_combo.isEnabled()}")
            print(f"Party combo count: {dialog.party_combo.count()}")
            
            print(f"\nRate AFG spinbox enabled: {dialog.rate_per_egg_afg.isEnabled()}")
            dialog.rate_per_egg_afg.setValue(10.0)
            print(f"Rate AFG set to 10.0, current value: {dialog.rate_per_egg_afg.value()}")
            
            print("\nAll input field tests completed!")
            
        except Exception as e:
            print(f"Error during test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Load stylesheet
    qss_path = Path(__file__).parent.parent / 'egg_farm_system' / 'styles.qss'
    if qss_path.exists():
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    
    # Initialize database
    DatabaseManager.initialize()
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())
