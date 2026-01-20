"""
Form widgets for farms and sheds, with a master-detail layout.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDialog, QFormLayout, QSplitter,
    QSpinBox, QToolButton
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QStandardItem
from pathlib import Path
from egg_farm_system.ui.widgets.datatable import DataTableWidget
from egg_farm_system.ui.widgets.loading_overlay import LoadingOverlay
from egg_farm_system.ui.widgets.success_message import SuccessMessage
from egg_farm_system.ui.widgets.keyboard_shortcuts import KeyboardShortcuts
from egg_farm_system.utils.error_handler import ErrorHandler
from egg_farm_system.utils.i18n import tr, get_i18n

from egg_farm_system.modules.farms import FarmManager
from egg_farm_system.modules.sheds import ShedManager
from egg_farm_system.config import MAX_FARMS

# --- Shed Dialog ---
class ShedDialog(QDialog):
    def __init__(self, shed=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{tr('Edit') if shed else tr('Add')} {tr('Shed')}")
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(shed.name if shed else "")
        self.name_edit.setToolTip(tr("Enter the name of the shed (required)"))
        # Placeholder text might need translation too, but QLineEdit doesn't support i18n_key easily without subclass
        self.name_edit.setPlaceholderText(tr("e.g., Shed A, North Shed")) 
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 100000)
        self.capacity_spin.setValue(shed.capacity if shed else 1000)
        self.capacity_spin.setToolTip(tr("Enter the maximum number of birds this shed can accommodate (required)"))
        self.capacity_spin.setSuffix(f" {tr('birds')}")
        
        # Required field indicators
        name_label = QLabel(f"{tr('Shed Name')}: <span style='color: red;'>*</span>")
        name_label.setTextFormat(Qt.RichText)
        capacity_label = QLabel(f"{tr('Capacity (birds)')}: <span style='color: red;'>*</span>")
        capacity_label.setTextFormat(Qt.RichText)
        
        layout.addRow(name_label, self.name_edit)
        layout.addRow(capacity_label, self.capacity_spin)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.setContentsMargins(0, 10, 0, 0)
        buttons.addStretch()
        save_btn = QPushButton(tr("Save"))
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(35)
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.SAVE, self.accept)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.CLOSE, self.reject)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.ESCAPE, self.reject)

    def get_data(self):
        return {"name": self.name_edit.text().strip(), "capacity": self.capacity_spin.value()}
    
    def validate(self):
        """Validate form inputs"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, tr("Validation Error"), tr("Shed name is required."))
            return False
        if self.capacity_spin.value() <= 0:
            QMessageBox.warning(self, tr("Validation Error"), tr("Capacity must be greater than 0."))
            return False
        return True
    
    def accept(self):
        """Override accept to validate before closing"""
        if self.validate():
            super().accept()

# --- Farm Dialog ---
class FarmDialog(QDialog):
    def __init__(self, parent, farm):
        super().__init__(parent)
        self.farm = farm
        self.setWindowTitle(tr("Farm Details") if farm else tr("New Farm"))
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.name_edit.setToolTip(tr("Enter the name of the farm (required)"))
        self.name_edit.setPlaceholderText(tr("e.g., Main Farm, North Farm"))
        self.location_edit = QLineEdit()
        self.location_edit.setToolTip(tr("Enter the location/address of the farm (optional)"))
        self.location_edit.setPlaceholderText(tr("e.g., Kabul, District 5"))
        if farm:
            self.name_edit.setText(farm.name)
            self.location_edit.setText(farm.location or "")
        
        # Required field indicators
        name_label = QLabel(f"{tr('Farm Name')}: <span style='color: red;'>*</span>")
        name_label.setTextFormat(Qt.RichText)
        location_label = QLabel(f"{tr('Location')}:")
        
        layout.addRow(name_label, self.name_edit)
        layout.addRow(location_label, self.location_edit)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        save_btn = QPushButton(tr("Save"))
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(35)
        save_btn.clicked.connect(self.save_farm)
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        self.setLayout(layout)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.SAVE, self.save_farm)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.CLOSE, self.reject)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.ESCAPE, self.reject)
    
    def save_farm(self):
        """Save farm with loading indicator and success feedback"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, tr("Validation Error"), tr("Farm name is required."))
            return
        
        # Show loading overlay
        loading = LoadingOverlay(self, tr("Saving farm..."))
        loading.show()
        QTimer.singleShot(50, lambda: self._do_save(name, loading))
    
    def _do_save(self, name, loading):
        """Perform the actual save operation"""
        try:
            location = self.location_edit.text().strip()
            
            with FarmManager() as manager:
                if self.farm:
                    manager.update_farm(self.farm.id, name, location)
                    message = tr("Saved successfully")
                else:
                    manager.create_farm(name, location)
                    message = tr("Saved successfully")
            
            loading.hide()
            loading.deleteLater()
            
            # Show success message
            success_msg = SuccessMessage(self, message)
            success_msg.show()
            QTimer.singleShot(100, lambda: self.accept())
        except ValueError as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.warning(self, tr("Validation Error"), f"{tr('Error')}: {str(e)}")
        except Exception as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.critical(
                self, 
                tr("Failed to save"), 
                f"{tr('Error')}: {str(e)}"
            )

# --- Main Widget ---
class FarmFormWidget(QWidget):
    farm_changed = Signal()

    def __init__(self):
        super().__init__()
        self.selected_farm_id = None
        self.loading_overlay = LoadingOverlay(self)
        
        get_i18n().language_changed.connect(self._update_texts)
        
        self.init_ui()
        self.refresh_farms()

    def _update_texts(self, lang_code):
        """Update texts when language changes"""
        # Update persistent widgets
        self.farms_title.setText(tr("Farms"))
        self.new_farm_btn.setText(tr("Add New Farm"))
        
        # Update table headers
        self.farms_table.set_headers(["ID", tr("Name"), tr("Location"), tr("Sheds"), tr("Actions")])
        self.sheds_table.set_headers(["ID", tr("Name"), tr("Capacity"), tr("Actions")])
        
        # Refresh dynamic content (sheds title, table data might contain static strings?)
        # Table data usually comes from DB, so it's fine.
        # But Sheds Title depends on selected farm
        if self.selected_farm_id:
            # We can't easily get the farm name again without querying or storing it separately
            # Just reset to "Sheds" or try to keep context
            pass
        else:
            self.sheds_title.setText(tr("Sheds"))
            
        self.add_shed_btn.setText(tr("Add Shed"))

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)
        
        # Farms section
        farms_widget = QWidget()
        layout = QVBoxLayout(farms_widget)
        
        header_hbox = QHBoxLayout()
        self.farms_title = QLabel(tr("Farms"))
        self.farms_title.setFont(QFont("Arial", 14, QFont.Bold))
        header_hbox.addWidget(self.farms_title)
        header_hbox.addStretch()
        
        self.new_farm_btn = QPushButton(tr("Add New Farm"))
        self.new_farm_btn.clicked.connect(self.add_farm)
        self.new_farm_btn.setToolTip(tr("Add a new farm"))
        header_hbox.addWidget(self.new_farm_btn)
        layout.addLayout(header_hbox)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.add_standard_shortcuts(self, {
            'new': self.add_farm,
            'refresh': self.refresh_farms
        })
        
        self.farms_table = DataTableWidget()
        self.farms_table.set_headers(["ID", tr("Name"), tr("Location"), tr("Sheds"), tr("Actions")])
        self.farms_table.view.setColumnHidden(0, True)
        self.farms_table.view.selectionModel().selectionChanged.connect(self.farm_selected)
        layout.addWidget(self.farms_table)
        splitter.addWidget(farms_widget)
        
        # Sheds section
        sheds_widget = QWidget()
        sheds_layout = QVBoxLayout(sheds_widget)
        
        shed_header_hbox = QHBoxLayout()
        self.sheds_title = QLabel(tr("Sheds"))
        self.sheds_title.setFont(QFont("Arial", 14, QFont.Bold))
        shed_header_hbox.addWidget(self.sheds_title)
        shed_header_hbox.addStretch()
        
        self.add_shed_btn = QPushButton(tr("Add Shed"))
        self.add_shed_btn.clicked.connect(self.add_shed)
        self.add_shed_btn.setEnabled(False)
        self.add_shed_btn.setToolTip(tr("Add a new shed"))
        shed_header_hbox.addWidget(self.add_shed_btn)
        sheds_layout.addLayout(shed_header_hbox)
        
        self.sheds_table = DataTableWidget()
        self.sheds_table.set_headers(["ID", tr("Name"), tr("Capacity"), tr("Actions")])
        self.sheds_table.view.setColumnHidden(0, True)
        sheds_layout.addWidget(self.sheds_table)
        splitter.addWidget(sheds_widget)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def farm_selected(self):
        selected_indexes = self.farms_table.view.selectionModel().selectedRows()
        if not selected_indexes:
            self.selected_farm_id = None
            self.sheds_table.model.setRowCount(0)
            self.sheds_title.setText(tr("Sheds"))
            self.add_shed_btn.setEnabled(False)
            return
        
        source_index = self.farms_table.proxy.mapToSource(selected_indexes[0])
        farm_id = int(self.farms_table.model.item(source_index.row(), 0).text())
        farm_name = self.farms_table.model.item(source_index.row(), 1).text()

        self.selected_farm_id = farm_id
        # Simple concatenation for title
        self.sheds_title.setText(f"{tr('Sheds')} - {farm_name}")
        self.add_shed_btn.setEnabled(True)
        self.refresh_sheds()

    def refresh_farms(self):
        """Refresh farms table with loading indicator"""
        self.loading_overlay.set_message(tr("Loading..."))
        self.loading_overlay.show()
        QTimer.singleShot(50, self._do_refresh_farms)
    
    def _do_refresh_farms(self):
        """Perform the actual refresh"""
        try:
            self.farms_table.model.setRowCount(0)
            
            with FarmManager() as fm:
                farms = fm.get_all_farms()
                rows = []
                for farm in farms:
                    row = self.farms_table.model.rowCount()
                    self.farms_table.model.insertRow(row)
                    self.farms_table.model.setItem(row, 0, QStandardItem(str(farm.id)))
                    self.farms_table.model.setItem(row, 1, QStandardItem(farm.name))
                    self.farms_table.model.setItem(row, 2, QStandardItem(farm.location or ""))
                    # Pre-fetch shed count before session closes
                    shed_count = len(farm.sheds)
                    self.farms_table.model.setItem(row, 3, QStandardItem(str(shed_count)))
                    self.add_action_buttons(self.farms_table, row, farm, self.edit_farm, self.delete_farm)
                    rows.append([str(farm.id), farm.name, farm.location or "", str(shed_count), ""])
            
            # Update empty state
            if len(rows) == 0:
                self.farms_table.stacked.setCurrentIndex(1)
            else:
                self.farms_table.stacked.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"{tr('Error')}: {str(e)}")
        finally:
            self.loading_overlay.hide()

    def refresh_sheds(self):
        """Refresh sheds table"""
        try:
            self.sheds_table.model.setRowCount(0)
            rows = []
            if self.selected_farm_id:
                with ShedManager() as sm:
                    for shed in sm.get_sheds_by_farm(self.selected_farm_id):
                        row = self.sheds_table.model.rowCount()
                        self.sheds_table.model.insertRow(row)
                        self.sheds_table.model.setItem(row, 0, QStandardItem(str(shed.id)))
                        self.sheds_table.model.setItem(row, 1, QStandardItem(shed.name))
                        self.sheds_table.model.setItem(row, 2, QStandardItem(str(shed.capacity)))
                        self.add_action_buttons(self.sheds_table, row, shed, self.edit_shed, self.delete_shed)
                        rows.append([str(shed.id), shed.name, str(shed.capacity), ""])
            
            # Update empty state
            if len(rows) == 0:
                self.sheds_table.stacked.setCurrentIndex(1)
            else:
                self.sheds_table.stacked.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"{tr('Error')}: {str(e)}")

    def add_action_buttons(self, table, row, item_instance, edit_func, delete_func):
        from egg_farm_system.config import get_asset_path
        edit_btn = QToolButton(); edit_btn.setIcon(QIcon(get_asset_path('icon_edit.svg')))
        edit_btn.setToolTip(tr('Edit')); edit_btn.clicked.connect(lambda: edit_func(item_instance))
        delete_btn = QToolButton(); delete_btn.setIcon(QIcon(get_asset_path('icon_delete.svg')))
        delete_btn.setToolTip(tr('Delete')); delete_btn.clicked.connect(lambda: delete_func(item_instance))
        container = QWidget()
        container.setMinimumHeight(36)
        container.setMaximumHeight(36)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        layout.addStretch()
        # Last column is assumed to be actions - use proxy index for correct mapping
        source_idx = table.model.index(row, table.model.columnCount() - 1)
        proxy_idx = table.proxy.mapFromSource(source_idx)
        table.view.setIndexWidget(proxy_idx, container)

    def add_farm(self):
        dialog = FarmDialog(self, None)
        if dialog.exec():
            self.refresh_farms()
            self.farm_changed.emit()
            success_msg = SuccessMessage(self, tr("Saved successfully"))
            success_msg.show()

    def edit_farm(self, farm):
        dialog = FarmDialog(self, farm)
        if dialog.exec():
            self.refresh_farms()
            self.farm_changed.emit()
            success_msg = SuccessMessage(self, tr("Saved successfully"))
            success_msg.show()

    def delete_farm(self, farm):
        """Delete farm with detailed confirmation"""
        # Count related data
        shed_count = len(farm.sheds) if hasattr(farm, 'sheds') else 0
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(tr("Confirm Delete"))
        msg.setText(f"{tr('Are you sure you want to delete')} '{farm.name}'?")
        
        if shed_count > 0:
            msg.setInformativeText(
                f"{tr('This action cannot be undone')}"
            )
        else:
            msg.setInformativeText(tr("This action cannot be undone"))
        
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        if msg.exec() == QMessageBox.Yes:
            try:
                self.loading_overlay.set_message(tr("Loading..."))
                self.loading_overlay.show()
                QTimer.singleShot(50, lambda: self._do_delete_farm(farm))
            except Exception as e:
                self.loading_overlay.hide()
                QMessageBox.critical(self, tr("Error"), f"{tr('Error')}: {str(e)}")
    
    def _do_delete_farm(self, farm):
        """Perform the actual delete"""
        try:
            farm_name = farm.name
            with FarmManager() as fm:
                fm.delete_farm(farm.id)
            
            self.loading_overlay.hide()
            self.refresh_farms()
            self.farm_changed.emit()
            success_msg = SuccessMessage(self, tr("Saved successfully")) # Generic success
            success_msg.show()
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(
                self, 
                tr("Error"), 
                f"{tr('Error')}: {str(e)}"
            )

    def add_shed(self):
        if not self.selected_farm_id: return
        dialog = ShedDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.loading_overlay.set_message(tr("Loading..."))
                self.loading_overlay.show()
                QTimer.singleShot(50, lambda: self._do_add_shed(data))
            except Exception as e:
                self.loading_overlay.hide()
                QMessageBox.critical(self, tr("Error"), f"{tr('Error')}: {str(e)}")
    
    def _do_add_shed(self, data):
        """Perform the actual add"""
        try:
            with ShedManager() as sm:
                sm.create_shed(self.selected_farm_id, data['name'], data['capacity'])
            
            self.loading_overlay.hide()
            self.refresh_sheds()
            self.refresh_farms()
            success_msg = SuccessMessage(self, tr("Saved successfully"))
            success_msg.show()
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, tr("Error"), f"{tr('Error')}: {str(e)}")

    def edit_shed(self, shed):
        dialog = ShedDialog(shed, self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                self.loading_overlay.set_message(tr("Loading..."))
                self.loading_overlay.show()
                QTimer.singleShot(50, lambda: self._do_edit_shed(shed, data))
            except Exception as e:
                self.loading_overlay.hide()
                QMessageBox.critical(self, tr("Error"), f"{tr('Error')}: {str(e)}")
    
    def _do_edit_shed(self, shed, data):
        """Perform the actual edit"""
        try:
            with ShedManager() as sm:
                sm.update_shed(shed.id, data['name'], data['capacity'])
            
            self.loading_overlay.hide()
            self.refresh_sheds()
            success_msg = SuccessMessage(self, tr("Saved successfully"))
            success_msg.show()
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, tr("Error"), f"{tr('Error')}: {str(e)}")

    def delete_shed(self, shed):
        """Delete shed with detailed confirmation"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(tr("Confirm Delete"))
        msg.setText(f"{tr('Are you sure you want to delete')} '{shed.name}'?")
        msg.setInformativeText(tr("This action cannot be undone"))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        if msg.exec() == QMessageBox.Yes:
            try:
                shed_name = shed.name
                self.loading_overlay.set_message(tr("Loading..."))
                self.loading_overlay.show()
                QTimer.singleShot(50, lambda: self._do_delete_shed(shed, shed_name))
            except Exception as e:
                self.loading_overlay.hide()
                QMessageBox.critical(self, tr("Error"), f"{tr('Error')}: {str(e)}")
    
    def _do_delete_shed(self, shed, shed_name):
        """Perform the actual delete"""
        try:
            with ShedManager() as sm:
                sm.delete_shed(shed.id)
            
            self.loading_overlay.hide()
            self.refresh_sheds()
            self.refresh_farms()
            success_msg = SuccessMessage(self, tr("Saved successfully"))
            success_msg.show()
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, tr("Error"), f"{tr('Error')}: {str(e)}")
