"""
Form widgets for farms and sheds, with a master-detail layout.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDialog, QFormLayout, QSplitter,
    QSpinBox, QToolButton
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QStandardItem
from pathlib import Path
from egg_farm_system.ui.widgets.datatable import DataTableWidget

from egg_farm_system.modules.farms import FarmManager
from egg_farm_system.modules.sheds import ShedManager
from egg_farm_system.config import MAX_FARMS

# --- Shed Dialog ---
class ShedDialog(QDialog):
    def __init__(self, shed=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Edit' if shed else 'Add'} Shed")
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(shed.name if shed else "")
        self.capacity_spin = QSpinBox()
        self.capacity_spin.setRange(1, 100000)
        self.capacity_spin.setValue(shed.capacity if shed else 1000)
        layout.addRow("Shed Name:", self.name_edit)
        layout.addRow("Capacity (birds):", self.capacity_spin)
        buttons = QHBoxLayout()
        save_btn = QPushButton("Save"); save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel"); cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn); buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

    def get_data(self):
        return {"name": self.name_edit.text(), "capacity": self.capacity_spin.value()}

# --- Farm Dialog ---
class FarmDialog(QDialog):
    def __init__(self, parent, farm):
        super().__init__(parent)
        self.farm = farm
        self.farm_manager = FarmManager()
        self.setWindowTitle("Farm Details" if farm else "New Farm")
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.location_edit = QLineEdit()
        if farm:
            self.name_edit.setText(farm.name)
            self.location_edit.setText(farm.location or "")
        layout.addRow("Farm Name:", self.name_edit)
        layout.addRow("Location:", self.location_edit)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save"); save_btn.clicked.connect(self.save_farm)
        cancel_btn = QPushButton("Cancel"); cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn); btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        self.setLayout(layout)
    
    def save_farm(self):
        try:
            name = self.name_edit.text().strip()
            if not name: return QMessageBox.warning(self, "Validation", "Farm name is required")
            if self.farm:
                self.farm_manager.update_farm(self.farm.id, name, self.location_edit.text().strip())
            else:
                self.farm_manager.create_farm(name, self.location_edit.text().strip())
            self.accept()
        except Exception as e: QMessageBox.critical(self, "Error", f"Failed to save farm: {e}")

# --- Main Widget ---
class FarmFormWidget(QWidget):
    farm_changed = Signal()

    def __init__(self):
        super().__init__()
        self.farm_manager = FarmManager()
        self.shed_manager = ShedManager()
        self.selected_farm_id = None
        self.init_ui()
        self.refresh_farms()

    def init_ui(self):
        main_layout = QVBoxLayout(self); splitter = QSplitter(Qt.Vertical)
        farms_widget = QWidget(); layout = QVBoxLayout(farms_widget)
        header_hbox = QHBoxLayout(); title = QLabel("Farms"); title.setFont(QFont("Arial", 14, QFont.Bold))
        header_hbox.addWidget(title); header_hbox.addStretch()
        new_farm_btn = QPushButton("Add New Farm"); new_farm_btn.clicked.connect(self.add_farm)
        header_hbox.addWidget(new_farm_btn); layout.addLayout(header_hbox)
        self.farms_table = DataTableWidget()
        self.farms_table.set_headers(["ID", "Name", "Location", "Sheds", "Actions"])
        self.farms_table.view.setColumnHidden(0, True)
        self.farms_table.view.selectionModel().selectionChanged.connect(self.farm_selected)
        layout.addWidget(self.farms_table); splitter.addWidget(farms_widget)
        sheds_widget = QWidget(); sheds_layout = QVBoxLayout(sheds_widget)
        shed_header_hbox = QHBoxLayout(); self.sheds_title = QLabel("Sheds"); self.sheds_title.setFont(QFont("Arial", 14, QFont.Bold))
        shed_header_hbox.addWidget(self.sheds_title); shed_header_hbox.addStretch()
        self.add_shed_btn = QPushButton("Add Shed"); self.add_shed_btn.clicked.connect(self.add_shed)
        self.add_shed_btn.setEnabled(False)
        shed_header_hbox.addWidget(self.add_shed_btn); sheds_layout.addLayout(shed_header_hbox)
        self.sheds_table = DataTableWidget()
        self.sheds_table.set_headers(["ID", "Name", "Capacity", "Actions"])
        self.sheds_table.view.setColumnHidden(0, True)
        sheds_layout.addWidget(self.sheds_table); splitter.addWidget(sheds_widget)
        main_layout.addWidget(splitter); self.setLayout(main_layout)

    def farm_selected(self):
        selected_indexes = self.farms_table.view.selectionModel().selectedRows()
        if not selected_indexes:
            self.selected_farm_id = None; self.sheds_table.model.setRowCount(0)
            self.sheds_title.setText("Sheds"); self.add_shed_btn.setEnabled(False)
            return
        
        source_index = self.farms_table.proxy.mapToSource(selected_indexes[0])
        farm_id = int(self.farms_table.model.item(source_index.row(), 0).text())
        farm_name = self.farms_table.model.item(source_index.row(), 1).text()

        self.selected_farm_id = farm_id
        self.sheds_title.setText(f"Sheds for {farm_name}")
        self.add_shed_btn.setEnabled(True)
        self.refresh_sheds()

    def refresh_farms(self):
        self.farms_table.model.setRowCount(0)
        farms = self.farm_manager.get_all_farms()
        for farm in farms:
            row = self.farms_table.model.rowCount()
            self.farms_table.model.insertRow(row)
            self.farms_table.model.setItem(row, 0, QStandardItem(str(farm.id)))
            self.farms_table.model.setItem(row, 1, QStandardItem(farm.name))
            self.farms_table.model.setItem(row, 2, QStandardItem(farm.location or ""))
            self.farms_table.model.setItem(row, 3, QStandardItem(str(len(farm.sheds))))
            self.add_action_buttons(self.farms_table, row, farm, self.edit_farm, self.delete_farm)

    def refresh_sheds(self):
        self.sheds_table.model.setRowCount(0)
        if self.selected_farm_id:
            for shed in self.shed_manager.get_sheds_by_farm(self.selected_farm_id):
                row = self.sheds_table.model.rowCount()
                self.sheds_table.model.insertRow(row)
                self.sheds_table.model.setItem(row, 0, QStandardItem(str(shed.id)))
                self.sheds_table.model.setItem(row, 1, QStandardItem(shed.name))
                self.sheds_table.model.setItem(row, 2, QStandardItem(str(shed.capacity)))
                self.add_action_buttons(self.sheds_table, row, shed, self.edit_shed, self.delete_shed)

    def add_action_buttons(self, table, row, item_instance, edit_func, delete_func):
        edit_btn = QToolButton(); edit_btn.setIcon(QIcon(str(Path(__file__).parent.parent.parent / 'assets' / 'icon_edit.svg')))
        edit_btn.setToolTip('Edit'); edit_btn.clicked.connect(lambda: edit_func(item_instance))
        delete_btn = QToolButton(); delete_btn.setIcon(QIcon(str(Path(__file__).parent.parent.parent / 'assets' / 'icon_delete.svg')))
        delete_btn.setToolTip('Delete'); delete_btn.clicked.connect(lambda: delete_func(item_instance))
        container = QWidget(); layout = QHBoxLayout(container); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(5)
        layout.addWidget(edit_btn); layout.addWidget(delete_btn); layout.addStretch()
        # Last column is assumed to be actions
        table.view.setIndexWidget(table.model.index(row, table.model.columnCount() - 1), container)

    def add_farm(self):
        dialog = FarmDialog(self, None)
        if dialog.exec(): self.refresh_farms(); self.farm_changed.emit()

    def edit_farm(self, farm):
        dialog = FarmDialog(self, farm)
        if dialog.exec(): self.refresh_farms(); self.farm_changed.emit()

    def delete_farm(self, farm):
        if QMessageBox.question(self, "Confirm", f"Delete farm '{farm.name}'?") == QMessageBox.Yes:
            self.farm_manager.delete_farm(farm.id); self.refresh_farms(); self.farm_changed.emit()

    def add_shed(self):
        if not self.selected_farm_id: return
        dialog = ShedDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data(); self.shed_manager.create_shed(self.selected_farm_id, data['name'], data['capacity'])
            self.refresh_sheds(); self.refresh_farms()

    def edit_shed(self, shed):
        dialog = ShedDialog(shed, self)
        if dialog.exec():
            data = dialog.get_data(); self.shed_manager.update_shed(shed.id, data['name'], data['capacity'])
            self.refresh_sheds()

    def delete_shed(self, shed):
        if QMessageBox.question(self, "Confirm", f"Delete shed '{shed.name}'?") == QMessageBox.Yes:
            self.shed_manager.delete_shed(shed.id); self.refresh_sheds(); self.refresh_farms()
