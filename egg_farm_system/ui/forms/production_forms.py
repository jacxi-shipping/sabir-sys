"""
Form widgets for egg production
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDialog, QFormLayout, QSpinBox, QDateTimeEdit, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, QDateTime, QSize, QTimer
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from egg_farm_system.ui.widgets.datatable import DataTableWidget
from egg_farm_system.ui.widgets.loading_overlay import LoadingOverlay
from egg_farm_system.ui.widgets.success_message import SuccessMessage
from egg_farm_system.ui.widgets.keyboard_shortcuts import KeyboardShortcuts
from egg_farm_system.utils.error_handler import ErrorHandler
from PySide6.QtWidgets import QToolButton

from egg_farm_system.modules.farms import FarmManager
from egg_farm_system.modules.sheds import ShedManager
from egg_farm_system.modules.flocks import FlockManager
from egg_farm_system.modules.egg_production import EggProductionManager
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
        self.loading_overlay = LoadingOverlay(self)
        
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
        shed_label = QLabel("Shed: <span style='color: red;'>*</span>")
        shed_label.setTextFormat(Qt.RichText)
        selector_layout.addWidget(shed_label)
        self.shed_combo = QComboBox()
        self.shed_combo.setToolTip("Select the shed for which to record production (required)")
        self.shed_combo.currentIndexChanged.connect(self.on_shed_changed)
        selector_layout.addWidget(self.shed_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # New production button (aligned right in header)
        new_prod_btn = QPushButton("Record Production")
        new_prod_btn.clicked.connect(self.record_production)
        new_prod_btn.setToolTip("Record new production (Ctrl+N)")
        header_hbox.addWidget(new_prod_btn)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.add_standard_shortcuts(self, {
            'new': self.record_production,
            'refresh': self.refresh_productions
        })
        
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
        shed_id = self.shed_combo.currentData()
        if not shed_id:
            self.table.set_rows([])
            return
        
        self.loading_overlay.set_message("Loading production data...")
        self.loading_overlay.show()
        QTimer.singleShot(50, lambda: self._do_refresh_productions(shed_id))
    
    def _do_refresh_productions(self, shed_id):
        """Perform the actual refresh"""
        try:
            start_date = datetime.utcnow() - timedelta(days=30)
            end_date = datetime.utcnow()
            
            productions = self.egg_manager.get_daily_production(shed_id, start_date, end_date)
            
            rows = []
            action_widgets = []
            for row, prod in enumerate(productions):
                rows.append([prod.date.strftime("%Y-%m-%d"), prod.small_count, prod.medium_count, prod.large_count, prod.broken_count, prod.total_eggs, ""])
                action_widgets.append((row, prod))

            self.loading_overlay.hide()
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
                    edit_btn.setIconSize(QSize(20, 20))
                edit_btn.setToolTip('Edit')
                edit_btn.clicked.connect(lambda checked, p=prod: self.edit_production(p))

                delete_btn = QToolButton()
                delete_btn.setAutoRaise(True)
                delete_btn.setFixedSize(28, 28)
                if delete_icon.exists():
                    delete_btn.setIcon(QIcon(str(delete_icon)))
                    delete_btn.setIconSize(QSize(20, 20))
                delete_btn.setToolTip('Delete')
                delete_btn.clicked.connect(lambda checked, p=prod: self.delete_production(p))

                container = QWidget()
                container.setMinimumHeight(36)
                container.setMaximumHeight(36)
                l = QHBoxLayout(container)
                l.setContentsMargins(4, 2, 4, 2)
                l.setSpacing(4)
                l.addWidget(edit_btn)
                l.addWidget(delete_btn)
                l.addStretch()
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
        """Delete production with detailed confirmation"""
        total_eggs = production.total_eggs if hasattr(production, 'total_eggs') else 0
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Confirm Delete")
        msg.setText(f"Are you sure you want to delete the production record for {production.date.strftime('%Y-%m-%d')}?")
        msg.setInformativeText(
            f"Total eggs: {total_eggs:,}\n"
            f"Small: {production.small_count}, Medium: {production.medium_count}, "
            f"Large: {production.large_count}, Broken: {production.broken_count}\n\n"
            "This action cannot be undone."
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        if msg.exec() == QMessageBox.Yes:
            try:
                self.loading_overlay.set_message("Deleting production record...")
                self.loading_overlay.show()
                QTimer.singleShot(50, lambda: self._do_delete_production(production))
            except Exception as e:
                self.loading_overlay.hide()
                QMessageBox.critical(self, "Delete Failed", f"Failed to delete production: {str(e)}")
    
    def _do_delete_production(self, production):
        """Perform the actual delete"""
        try:
            self.egg_manager.delete_production(production.id)
            self.loading_overlay.hide()
            self.refresh_productions()
            success_msg = SuccessMessage(self, "Production record deleted successfully")
            success_msg.show()
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, "Delete Failed", f"Failed to delete production: {str(e)}")


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
        date_label = QLabel("Date: <span style='color: red;'>*</span>")
        date_label.setTextFormat(Qt.RichText)
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_edit.setToolTip("Select the date and time for this production record (required)\nFormat: YYYY-MM-DD HH:MM")
        date_layout.addRow(date_label, self.date_edit)
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
        
        self.small_spin.setToolTip("Enter the number of small eggs (optional)")
        self.small_spin.setSuffix(" eggs")
        self.medium_spin.setToolTip("Enter the number of medium eggs (optional)")
        self.medium_spin.setSuffix(" eggs")
        self.large_spin.setToolTip("Enter the number of large eggs (optional)")
        self.large_spin.setSuffix(" eggs")
        self.broken_spin.setToolTip("Enter the number of broken eggs (optional)")
        self.broken_spin.setSuffix(" eggs")
        
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
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(35)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        
        save_btn.clicked.connect(self.save_production)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.SAVE, self.save_production)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.CLOSE, self.reject)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.ESCAPE, self.reject)
        
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
        """Save production with loading indicator and success feedback"""
        # Validate that at least some eggs are recorded
        total = (self.small_spin.value() + self.medium_spin.value() + 
                 self.large_spin.value() + self.broken_spin.value())
        if total == 0:
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "Please enter at least one egg count. Total eggs cannot be zero."
            )
            return
        
        # Show loading overlay
        loading = LoadingOverlay(self, "Saving production record...")
        loading.show()
        QTimer.singleShot(50, lambda: self._do_save_production(loading))
    
    def _do_save_production(self, loading):
        """Perform the actual save"""
        try:
            if self.production:
                self.egg_manager.update_production(
                    self.production.id,
                    self.small_spin.value(),
                    self.medium_spin.value(),
                    self.large_spin.value(),
                    self.broken_spin.value()
                )
                message = "Production record updated successfully."
            else:
                self.egg_manager.record_production(
                    self.shed_id,
                    self.date_edit.dateTime().toPython(),
                    self.small_spin.value(),
                    self.medium_spin.value(),
                    self.large_spin.value(),
                    self.broken_spin.value()
                )
                message = "Production record saved successfully."
            
            loading.hide()
            loading.deleteLater()
            
            # Show success message
            success_msg = SuccessMessage(self, message)
            success_msg.show()
            QTimer.singleShot(100, lambda: self.accept())
        except ValueError as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.warning(self, "Validation Error", f"Invalid input: {str(e)}")
        except Exception as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.critical(
                self, 
                "Save Failed", 
                f"Failed to save production record.\n\nError: {str(e)}\n\nPlease check your input and try again."
            )
