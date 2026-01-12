"""
Flock management forms
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QMessageBox, QDialog, QFormLayout, QDateEdit, QSpinBox, QLineEdit, QToolButton
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QIcon, QStandardItem

from egg_farm_system.modules.farms import FarmManager
from egg_farm_system.modules.sheds import ShedManager
from egg_farm_system.modules.flocks import FlockManager
from egg_farm_system.ui.widgets.datatable import DataTableWidget
from egg_farm_system.config import get_asset_path

class FlockDialog(QDialog):
    def __init__(self, shed_id, flock=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Edit' if flock else 'Add'} Flock")
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit(flock.name if flock else "")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        if flock:
            self.date_edit.setDate(flock.start_date)
        else:
            self.date_edit.setDate(QDate.currentDate())
            
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100000)
        self.count_spin.setValue(flock.initial_count if flock else 1000)
        
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Start Date:", self.date_edit)
        layout.addRow("Initial Count:", self.count_spin)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)
        
    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "start_date": self.date_edit.date().toPython(),
            "initial_count": self.count_spin.value()
        }

class FlockManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.refresh_farms()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Flock Management")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        header.addWidget(title)
        header.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_flocks)
        header.addWidget(refresh_btn)
        layout.addLayout(header)
        
        # Filters
        filter_layout = QHBoxLayout()
        self.farm_combo = QComboBox()
        self.farm_combo.currentIndexChanged.connect(self.refresh_sheds)
        self.shed_combo = QComboBox()
        self.shed_combo.currentIndexChanged.connect(self.refresh_flocks)
        
        filter_layout.addWidget(QLabel("Farm:"))
        filter_layout.addWidget(self.farm_combo)
        filter_layout.addWidget(QLabel("Shed:"))
        filter_layout.addWidget(self.shed_combo)
        filter_layout.addStretch()
        
        self.add_btn = QPushButton("Add Flock")
        self.add_btn.clicked.connect(self.add_flock)
        self.add_btn.setEnabled(False)
        filter_layout.addWidget(self.add_btn)
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = DataTableWidget()
        self.table.set_headers(["ID", "Name", "Start Date", "Initial", "Live", "Age (Days)", "Actions"])
        self.table.view.setColumnHidden(0, True)
        layout.addWidget(self.table)

    def refresh_farms(self):
        self.farm_combo.blockSignals(True)
        self.farm_combo.clear()
        try:
            with FarmManager() as fm:
                for farm in fm.get_all_farms():
                    self.farm_combo.addItem(farm.name, farm.id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load farms: {e}")
        self.farm_combo.blockSignals(False)
        self.refresh_sheds()

    def refresh_sheds(self):
        self.shed_combo.blockSignals(True)
        self.shed_combo.clear()
        farm_id = self.farm_combo.currentData()
        if farm_id:
            try:
                with ShedManager() as sm:
                    for shed in sm.get_sheds_by_farm(farm_id):
                        self.shed_combo.addItem(shed.name, shed.id)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load sheds: {e}")
        self.shed_combo.blockSignals(False)
        self.refresh_flocks()

    def refresh_flocks(self):
        self.table.model.setRowCount(0)
        shed_id = self.shed_combo.currentData()
        if not shed_id:
            self.add_btn.setEnabled(False)
            return
            
        self.add_btn.setEnabled(True)
        fm = FlockManager()
        try:
            flocks = fm.get_flocks_by_shed(shed_id)
            
            for row, flock in enumerate(flocks):
                stats = fm.get_flock_stats(flock.id)
                live = stats['live_count'] if stats else flock.initial_count
                age = stats['age_days'] if stats else 0
                
                self.table.model.insertRow(row)
                self.table.model.setItem(row, 0, QStandardItem(str(flock.id)))
                self.table.model.setItem(row, 1, QStandardItem(flock.name))
                self.table.model.setItem(row, 2, QStandardItem(str(flock.start_date.date())))
                self.table.model.setItem(row, 3, QStandardItem(str(flock.initial_count)))
                self.table.model.setItem(row, 4, QStandardItem(str(live)))
                self.table.model.setItem(row, 5, QStandardItem(str(age)))
                
                # Actions
                edit_btn = QToolButton(); edit_btn.setIcon(QIcon(get_asset_path('icon_edit.svg')))
                edit_btn.clicked.connect(lambda checked=False, f=flock: self.edit_flock(f))
                delete_btn = QToolButton(); delete_btn.setIcon(QIcon(get_asset_path('icon_delete.svg')))
                delete_btn.clicked.connect(lambda checked=False, f=flock: self.delete_flock(f))
                
                container = QWidget()
                h = QHBoxLayout(container)
                h.setContentsMargins(0, 0, 0, 0)
                h.addWidget(edit_btn)
                h.addWidget(delete_btn)
                h.addStretch()
                
                proxy_idx = self.table.proxy.mapFromSource(self.table.model.index(row, 6))
                self.table.view.setIndexWidget(proxy_idx, container)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load flocks: {e}")

    def add_flock(self):
        shed_id = self.shed_combo.currentData()
        if not shed_id: return
        dialog = FlockDialog(shed_id, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                fm = FlockManager()
                fm.create_flock(shed_id, **data)
                self.refresh_flocks()
                QMessageBox.information(self, "Success", "Flock created successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def edit_flock(self, flock):
        dialog = FlockDialog(flock.shed_id, flock, self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                fm = FlockManager()
                fm.update_flock(flock.id, **data)
                self.refresh_flocks()
                QMessageBox.information(self, "Success", "Flock updated successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_flock(self, flock):
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete flock '{flock.name}'? This cannot be undone.")
        if reply == QMessageBox.Yes:
            try:
                fm = FlockManager()
                fm.delete_flock(flock.id)
                self.refresh_flocks()
                QMessageBox.information(self, "Success", "Flock deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
