"""
Demo/Example showing usage of new UI/UX enhancement widgets.

This file demonstrates how to use:
- QuickDatePicker and QuickDateTimePicker
- SearchableComboBox
- Password visibility toggle (in login_dialog.py)
- Data export functionality

Run this file to see the widgets in action.
"""
import sys
from datetime import date, datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QGroupBox, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt

# Import new widgets
from egg_farm_system.ui.widgets.quick_date_picker import QuickDatePicker, QuickDateTimePicker
from egg_farm_system.ui.widgets.searchable_combobox import SearchableComboBox, SearchableComboBoxWithAddNew


class WidgetDemoWindow(QWidget):
    """Demo window showcasing all new UI widgets"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UI/UX Enhancement Widgets Demo")
        self.setMinimumWidth(800)
        self.setMinimumHeight(700)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the demo UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🎨 New UI/UX Enhancement Widgets Demo")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 1. Quick Date Picker Demo
        date_group = QGroupBox("1. Quick Date Selection")
        date_layout = QVBoxLayout()
        
        date_label = QLabel(
            "QuickDatePicker adds convenient buttons for common date selections.\n"
            "Try clicking 'Today', 'Yesterday', 'This Week', or 'This Month'."
        )
        date_layout.addWidget(date_label)
        
        self.date_picker = QuickDatePicker(show_quick_buttons=True)
        self.date_picker.dateChanged.connect(self._on_date_changed)
        date_layout.addWidget(self.date_picker)
        
        self.date_result = QLabel("Selected date will appear here")
        self.date_result.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        date_layout.addWidget(self.date_result)
        
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)
        
        # 2. Quick DateTime Picker Demo
        datetime_group = QGroupBox("2. Quick DateTime Selection")
        datetime_layout = QVBoxLayout()
        
        datetime_label = QLabel(
            "QuickDateTimePicker includes time selection with quick buttons.\n"
            "Try 'Now', 'Today', or 'Yesterday'."
        )
        datetime_layout.addWidget(datetime_label)
        
        self.datetime_picker = QuickDateTimePicker(show_quick_buttons=True)
        self.datetime_picker.dateTimeChanged.connect(self._on_datetime_changed)
        datetime_layout.addWidget(self.datetime_picker)
        
        self.datetime_result = QLabel("Selected datetime will appear here")
        self.datetime_result.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        datetime_layout.addWidget(self.datetime_result)
        
        datetime_group.setLayout(datetime_layout)
        layout.addWidget(datetime_group)
        
        # 3. Searchable ComboBox Demo
        combo_group = QGroupBox("3. Searchable ComboBox")
        combo_layout = QVBoxLayout()
        
        combo_label = QLabel(
            "SearchableComboBox lets users type to filter items.\n"
            "Try typing 'apple' or 'banana' - the list filters as you type!"
        )
        combo_layout.addWidget(combo_label)
        
        self.searchable_combo = SearchableComboBox()
        # Add sample data
        fruits = [
            "Apple", "Apricot", "Avocado", "Banana", "Blackberry", "Blueberry",
            "Cherry", "Coconut", "Cranberry", "Date", "Dragon Fruit", "Elderberry",
            "Fig", "Grape", "Grapefruit", "Guava", "Kiwi", "Lemon", "Lime",
            "Mango", "Melon", "Orange", "Papaya", "Peach", "Pear", "Pineapple",
            "Plum", "Pomegranate", "Raspberry", "Strawberry", "Tangerine", "Watermelon"
        ]
        for i, fruit in enumerate(fruits):
            self.searchable_combo.addItem(fruit, i)
        self.searchable_combo.activated.connect(self._on_combo_selected)
        combo_layout.addWidget(self.searchable_combo)
        
        self.combo_result = QLabel("Selected item will appear here")
        self.combo_result.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        combo_layout.addWidget(self.combo_result)
        
        combo_group.setLayout(combo_layout)
        layout.addWidget(combo_group)
        
        # 4. SearchableComboBox with "Add New"
        combo_add_group = QGroupBox("4. Searchable ComboBox with 'Add New'")
        combo_add_layout = QVBoxLayout()
        
        combo_add_label = QLabel(
            "This version includes a '➕ Add New...' option at the top.\n"
            "Useful for party/material selection where users might need to add new items."
        )
        combo_add_layout.addWidget(combo_add_label)
        
        self.searchable_combo_add = SearchableComboBoxWithAddNew()
        # Add sample parties
        parties = ["ABC Company", "XYZ Suppliers", "John's Farm", "Green Valley Co.", "Fresh Foods Inc."]
        for i, party in enumerate(parties):
            self.searchable_combo_add.addItem(party, i)
        self.searchable_combo_add.addNewRequested.connect(self._on_add_new_requested)
        self.searchable_combo_add.activated.connect(self._on_party_selected)
        combo_add_layout.addWidget(self.searchable_combo_add)
        
        self.party_result = QLabel("Selected party will appear here")
        self.party_result.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        combo_add_layout.addWidget(self.party_result)
        
        combo_add_group.setLayout(combo_add_layout)
        layout.addWidget(combo_add_group)
        
        # 5. Other Features Info
        info_group = QGroupBox("5. Other Features")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "✅ Password Visibility Toggle - Added to login dialog (eye icon)\n"
            "✅ Data Export Utilities - Use TableExportMixin to add CSV/Excel export buttons\n"
            "✅ All widgets follow PySide6 best practices and are fully documented"
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close Demo")
        close_btn.clicked.connect(self.close)
        close_btn.setMinimumHeight(40)
        layout.addWidget(close_btn)
    
    def _on_date_changed(self, qdate):
        """Handle date picker change"""
        py_date = date(qdate.year(), qdate.month(), qdate.day())
        self.date_result.setText(f"📅 Selected: {py_date.strftime('%Y-%m-%d (%A)')}")
    
    def _on_datetime_changed(self, qdatetime):
        """Handle datetime picker change"""
        py_datetime = datetime(
            qdatetime.date().year(), qdatetime.date().month(), qdatetime.date().day(),
            qdatetime.time().hour(), qdatetime.time().minute()
        )
        self.datetime_result.setText(f"🕐 Selected: {py_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _on_combo_selected(self, index):
        """Handle searchable combo selection"""
        if index >= 0:
            text = self.searchable_combo.itemText(index)
            self.combo_result.setText(f"🍎 Selected: {text}")
    
    def _on_party_selected(self, index):
        """Handle party combo selection"""
        if index > 0:  # Skip "Add New" item
            text = self.searchable_combo_add.itemText(index)
            self.party_result.setText(f"🏢 Selected: {text}")
    
    def _on_add_new_requested(self):
        """Handle Add New button click"""
        QMessageBox.information(
            self,
            "Add New",
            "This would open a dialog to add a new party.\n"
            "You can connect this signal to your 'Add Party' dialog."
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set a nice style
    app.setStyle("Fusion")
    
    window = WidgetDemoWindow()
    window.show()
    
    sys.exit(app.exec())
