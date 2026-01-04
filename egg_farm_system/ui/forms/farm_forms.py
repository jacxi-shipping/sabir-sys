"""
Form widgets for farms
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QDoubleSpinBox, QSizePolicy, QHeaderView, QToolButton, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from ui.widgets.datatable import DataTableWidget

from modules.farms import FarmManager
from modules.sheds import ShedManager
from config import MAX_FARMS

class FarmFormWidget(QWidget):
    """Farm management widget"""
    
    farm_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self.farm_manager = FarmManager()
        self.shed_manager = ShedManager()
        self.init_ui()
        self.refresh_farms()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12,12,12,12)
        
        # Header: title left, actions right
        header_hbox = QHBoxLayout()
        title = QLabel("Farm Management")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_hbox.addWidget(title)
        header_hbox.addStretch()
        new_farm_btn = QPushButton("Add New Farm")
        new_farm_btn.clicked.connect(self.add_farm)
        header_hbox.addWidget(new_farm_btn)
        layout.addLayout(header_hbox)
        
        # Farms table
        self.table = DataTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.set_headers(["Name", "Location", "Sheds", "Actions"])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh_farms(self):
        """Refresh farms table"""
        try:
            farms = self.farm_manager.get_all_farms()
            rows = []
            action_widgets = []
            for idx, farm in enumerate(farms):
                rows.append([farm.name, farm.location or "", str(len(farm.sheds)), ""])
                action_widgets.append((idx, farm))

            self.table.set_rows(rows)
            asset_dir = Path(__file__).parent.parent.parent / 'assets'
            edit_icon = asset_dir / 'icon_edit.svg'
            delete_icon = asset_dir / 'icon_delete.svg'
            for row_idx, farm in action_widgets:
                edit_btn = QToolButton()
                edit_btn.setAutoRaise(True)
                edit_btn.setFixedSize(28, 28)
                if edit_icon.exists():
                    edit_btn.setIcon(QIcon(str(edit_icon)))
                    edit_btn.setIconSize(QSize(16, 16))
                edit_btn.setToolTip('Edit')
                edit_btn.clicked.connect(lambda checked, f=farm: self.edit_farm(f))

                delete_btn = QToolButton()
                delete_btn.setAutoRaise(True)
                delete_btn.setFixedSize(28, 28)
                if delete_icon.exists():
                    delete_btn.setIcon(QIcon(str(delete_icon)))
                    delete_btn.setIconSize(QSize(16, 16))
                delete_btn.setToolTip('Delete')
                delete_btn.clicked.connect(lambda checked, f=farm: self.delete_farm(f))

                container = QWidget()
                l = QHBoxLayout(container)
                l.setContentsMargins(0, 0, 0, 0)
                l.setSpacing(6)
                l.addWidget(edit_btn)
                l.addWidget(delete_btn)
                self.table.set_cell_widget(row_idx, 3, container)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load farms: {e}")

    def delete_farm(self, farm):
        """Delete farm"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete farm '{farm.name}'?"
        )
        if reply == QMessageBox.Yes:
            try:
                self.farm_manager.delete_farm(farm.id)
                self.refresh_farms()
                self.farm_changed.emit()
                QMessageBox.information(self, "Success", "Farm deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete farm: {e}")

    def add_farm(self):
        """Open dialog to add a new farm"""
        dialog = FarmDialog(self, None)
        if dialog.exec():
            self.refresh_farms()
            try:
                self.farm_changed.emit()
            except Exception:
                pass

    def edit_farm(self, farm):
        """Open dialog to edit an existing farm"""
        dialog = FarmDialog(self, farm)
        if dialog.exec():
            self.refresh_farms()
            try:
                self.farm_changed.emit()
            except Exception:
                pass


class FarmDialog(QDialog):
    """Farm creation/edit dialog"""
    
    def __init__(self, parent, farm):
        super().__init__(parent)
        self.farm = farm
        self.farm_manager = FarmManager()
        
        self.setWindowTitle("Farm Details" if farm else "New Farm")
        self.setGeometry(100, 100, 400, 200)
        
        layout = QFormLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8,8,8,8)
        
        self.name_edit = QLineEdit()
        self.location_edit = QLineEdit()
        
        if farm:
            self.name_edit.setText(farm.name)
            self.location_edit.setText(farm.location or "")
        
        layout.addRow("Farm Name:", self.name_edit)
        layout.addRow("Location:", self.location_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        save_btn.clicked.connect(self.save_farm)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
    
    def save_farm(self):
        """Save farm"""
        try:
            name = self.name_edit.text().strip()
            location = self.location_edit.text().strip()
            
            if not name:
                QMessageBox.warning(self, "Validation", "Farm name is required")
                return
            
            if self.farm:
                self.farm_manager.update_farm(self.farm.id, name, location)
                QMessageBox.information(self, "Success", "Farm updated successfully")
            else:
                farms = self.farm_manager.get_all_farms()
                if len(farms) >= 4:
                    QMessageBox.warning(
                        self, "Limit Reached",
                        f"Maximum {4} farms allowed"
                    )
                    return
                
                self.farm_manager.create_farm(name, location)
                QMessageBox.information(self, "Success", "Farm created successfully")
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save farm: {e}")
