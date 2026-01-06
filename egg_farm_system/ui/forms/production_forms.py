"""
Form widgets for egg production
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDialog, QFormLayout, QSpinBox, QDateTimeEdit, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, QDateTime, QSize
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from ui.widgets.datatable import DataTableWidget
from PySide6.QtWidgets import QToolButton

from modules.farms import FarmManager
from modules.sheds import ShedManager
from modules.flocks import FlockManager
from modules.egg_production import EggProductionManager
from egg_farm_system.utils.egg_management import EggManagementSystem
from PySide6.QtWidgets import QGroupBox, QGridLayout

class ProductionFormWidget(QWidget):
    """Egg production tracking widget"""
    
    def __init__(self, farm_id):
        super().__init__()
        self.farm_id = farm_id
        self.farm_manager = FarmManager()
        self.shed_manager = ShedManager()
        self.flock_manager = FlockManager()
        self.egg_manager = EggProductionManager()
        
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header: title left, actions right
        header_hbox = QHBoxLayout()
        title = QLabel("Egg Production Tracking")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_hbox.addWidget(title)
        header_hbox.addStretch()
        layout.addLayout(header_hbox)
        
        # Farm and shed selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Shed:"))
        self.shed_combo = QComboBox()
        self.shed_combo.currentIndexChanged.connect(self.on_shed_changed)
        selector_layout.addWidget(self.shed_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # New production button (aligned right in header)
        new_prod_btn = QPushButton("Record Production")
        new_prod_btn.clicked.connect(self.record_production)
        header_hbox.addWidget(new_prod_btn)
        
        # Production table
        self.table = DataTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.set_headers(["Date", "Small", "Medium", "Large", "Broken", "Total", "Actions"])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh_data(self):
        """Refresh sheds and production data"""
        try:
            if not self.farm_id:
                return
            
            self.shed_combo.clear()
            farm = self.farm_manager.get_farm_by_id(self.farm_id)
            if farm:
                for shed in farm.sheds:
                    self.shed_combo.addItem(shed.name, shed.id)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")
    
    def on_shed_changed(self):
        """Handle shed selection change"""
        self.refresh_productions()
    
    def refresh_productions(self):
        """Refresh production table"""
        try:
            shed_id = self.shed_combo.currentData()
            if not shed_id:
                return
            
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
            
            productions = self.egg_manager.get_daily_production(shed_id, start_date, end_date)
            self.table.setRowCount(len(productions))
            
            rows = []
            action_widgets = []
            for row, prod in enumerate(productions):
                rows.append([prod.date.strftime("%Y-%m-%d"), prod.small_count, prod.medium_count, prod.large_count, prod.broken_count, prod.total_eggs, ""])
                action_widgets.append((row, prod))

            self.table.set_rows(rows)
            asset_dir = Path(__file__).parent.parent.parent / 'assets'
            edit_icon = asset_dir / 'icon_edit.svg'
            delete_icon = asset_dir / 'icon_delete.svg'
            for row_idx, prod in action_widgets:
                edit_btn = QToolButton()
                edit_btn.setAutoRaise(True)
                edit_btn.setFixedSize(28, 28)
                if edit_icon.exists():
                    edit_btn.setIcon(QIcon(str(edit_icon)))
                    edit_btn.setIconSize(QSize(16, 16))
                edit_btn.setToolTip('Edit')
                edit_btn.clicked.connect(lambda checked, p=prod: self.edit_production(p))

                delete_btn = QToolButton()
                delete_btn.setAutoRaise(True)
                delete_btn.setFixedSize(28, 28)
                if delete_icon.exists():
                    delete_btn.setIcon(QIcon(str(delete_icon)))
                    delete_btn.setIconSize(QSize(16, 16))
                delete_btn.setToolTip('Delete')
                delete_btn.clicked.connect(lambda checked, p=prod: self.delete_production(p))

                container = QWidget()
                l = QHBoxLayout(container)
                l.setContentsMargins(0, 0, 0, 0)
                l.setSpacing(6)
                l.addWidget(edit_btn)
                l.addWidget(delete_btn)
                self.table.set_cell_widget(row_idx, 6, container)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load productions: {e}")
    
    def record_production(self):
        """Record new production"""
        shed_id = self.shed_combo.currentData()
        if not shed_id:
            QMessageBox.warning(self, "Error", "Please select a shed")
            return
        
        dialog = ProductionDialog(self, shed_id, None, self.egg_manager)
        if dialog.exec():
            self.refresh_productions()
    
    def edit_production(self, production):
        """Edit production"""
        dialog = ProductionDialog(self, production.shed_id, production, self.egg_manager)
        if dialog.exec():
            self.refresh_productions()
    
    def delete_production(self, production):
        """Delete production"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete production record for {production.date.date()}?"
        )
        if reply == QMessageBox.Yes:
            try:
                self.egg_manager.delete_production(production.id)
                self.refresh_productions()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")


class ProductionDialog(QDialog):
    """Production recording dialog with tray/carton conversion"""
    
    def __init__(self, parent, shed_id, production, egg_manager):
        super().__init__(parent)
        self.shed_id = shed_id
        self.production = production
        self.egg_manager = egg_manager
        self.egg_management = EggManagementSystem()
        
        self.setWindowTitle("Egg Production" if production else "Record Production")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Date
        date_layout = QFormLayout()
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        date_layout.addRow("Date:", self.date_edit)
        layout.addLayout(date_layout)
        
        # Egg Counts Group
        counts_group = QGroupBox("Egg Counts by Grade")
        counts_layout = QFormLayout()
        counts_layout.setSpacing(8)
        
        self.small_spin = QSpinBox()
        self.small_spin.setMinimum(0)
        self.small_spin.setMaximum(100000)
        self.small_spin.valueChanged.connect(self.update_conversion)
        
        self.medium_spin = QSpinBox()
        self.medium_spin.setMinimum(0)
        self.medium_spin.setMaximum(100000)
        self.medium_spin.valueChanged.connect(self.update_conversion)
        
        self.large_spin = QSpinBox()
        self.large_spin.setMinimum(0)
        self.large_spin.setMaximum(100000)
        self.large_spin.valueChanged.connect(self.update_conversion)
        
        self.broken_spin = QSpinBox()
        self.broken_spin.setMinimum(0)
        self.broken_spin.setMaximum(100000)
        self.broken_spin.valueChanged.connect(self.update_conversion)
        
        if production:
            self.date_edit.setDateTime(QDateTime.fromString(
                production.date.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss"
            ))
            self.small_spin.setValue(production.small_count)
            self.medium_spin.setValue(production.medium_count)
            self.large_spin.setValue(production.large_count)
            self.broken_spin.setValue(production.broken_count)
        
        counts_layout.addRow("Small:", self.small_spin)
        counts_layout.addRow("Medium:", self.medium_spin)
        counts_layout.addRow("Large:", self.large_spin)
        counts_layout.addRow("Broken:", self.broken_spin)
        counts_group.setLayout(counts_layout)
        layout.addWidget(counts_group)
        
        # Conversion Display Group
        conversion_group = QGroupBox("Conversion Summary")
        conversion_layout = QGridLayout()
        conversion_layout.setSpacing(8)
        
        self.total_eggs_label = QLabel("Total: 0 eggs")
        total_font = QFont()
        total_font.setBold(True)
        total_font.setPointSize(11)
        self.total_eggs_label.setFont(total_font)
        conversion_layout.addWidget(self.total_eggs_label, 0, 0, 1, 2)
        
        self.tray_label = QLabel("= 0.00 trays")
        conversion_layout.addWidget(self.tray_label, 1, 0)
        
        self.carton_label = QLabel("= 0.00 cartons")
        conversion_layout.addWidget(self.carton_label, 1, 1)
        
        conversion_group.setLayout(conversion_layout)
        layout.addWidget(conversion_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(100)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        
        save_btn.clicked.connect(self.save_production)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Initial conversion update
        self.update_conversion()
    
    def update_conversion(self):
        """Update tray/carton conversion display"""
        try:
            total_eggs = (
                self.small_spin.value() +
                self.medium_spin.value() +
                self.large_spin.value() +
                self.broken_spin.value()
            )
            
            trays = self.egg_management.eggs_to_trays(total_eggs)
            cartons = self.egg_management.eggs_to_cartons(total_eggs)
            
            self.total_eggs_label.setText(f"Total: {total_eggs:,} eggs")
            self.tray_label.setText(f"= {trays:.2f} trays")
            self.carton_label.setText(f"= {cartons:.2f} cartons")
        except Exception as e:
            pass
    
    def save_production(self):
        """Save production"""
        try:
            if self.production:
                self.egg_manager.update_production(
                    self.production.id,
                    self.small_spin.value(),
                    self.medium_spin.value(),
                    self.large_spin.value(),
                    self.broken_spin.value()
                )
            else:
                self.egg_manager.record_production(
                    self.shed_id,
                    self.date_edit.dateTime().toPython(),
                    self.small_spin.value(),
                    self.medium_spin.value(),
                    self.large_spin.value(),
                    self.broken_spin.value()
                )
            
            QMessageBox.information(self, "Success", "Production recorded successfully")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")
