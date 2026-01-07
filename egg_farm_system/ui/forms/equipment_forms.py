"""
UI Forms for Equipment Management.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTableWidget, QTableWidgetItem,
    QDoubleSpinBox, QHeaderView, QComboBox, QDateEdit, QTextEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from egg_farm_system.modules.equipments import EquipmentManager
from egg_farm_system.database.models import EquipmentStatus

# --- Dialog for Add/Edit Equipment ---
class EquipmentDialog(QDialog):
    def __init__(self, equipment=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Edit' if equipment else 'Add'} Equipment")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(equipment.name if equipment else "")
        self.description_edit = QTextEdit(equipment.description if equipment else "")
        self.purchase_date_edit = QDateEdit(equipment.purchase_date if equipment else QDate.currentDate())
        self.purchase_date_edit.setCalendarPopup(True)
        self.purchase_price_spin = QDoubleSpinBox()
        self.purchase_price_spin.setRange(0, 100_000_000)
        self.purchase_price_spin.setValue(equipment.purchase_price if equipment else 0)
        self.purchase_price_spin.setSuffix(" AFN")
        self.status_combo = QComboBox()
        self.status_combo.addItems([s.value for s in EquipmentStatus])
        if equipment:
            self.status_combo.setCurrentText(equipment.status.value)

        layout.addRow("Name:", self.name_edit)
        layout.addRow("Description:", self.description_edit)
        layout.addRow("Purchase Date:", self.purchase_date_edit)
        layout.addRow("Purchase Price:", self.purchase_price_spin)
        layout.addRow("Status:", self.status_combo)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.setContentsMargins(0, 10, 0, 0)
        buttons.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(35)
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText(),
            "purchase_date": self.purchase_date_edit.date().toPython(),
            "purchase_price": self.purchase_price_spin.value(),
            "status": EquipmentStatus(self.status_combo.currentText())
        }

# --- Main Equipment Management Widget ---
class EquipmentFormWidget(QWidget):
    def __init__(self, farm_id):
        super().__init__()
        self.farm_id = farm_id
        self.manager = EquipmentManager()
        self.init_ui()
        self.load_equipment()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Equipment Management"); title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)

        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Equipment"); add_btn.clicked.connect(self.add_equipment)
        edit_btn = QPushButton("Edit Selected"); edit_btn.clicked.connect(self.edit_equipment)
        delete_btn = QPushButton("Delete Selected"); delete_btn.clicked.connect(self.delete_equipment)
        buttons_layout.addWidget(add_btn); buttons_layout.addWidget(edit_btn); buttons_layout.addWidget(delete_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6); self.table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Purchase Date", "Price", "Status"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)

    def set_farm_id(self, farm_id):
        self.farm_id = farm_id
        self.load_equipment()

    def load_equipment(self):
        self.table.setRowCount(0)
        if not self.farm_id:
            return
            
        equipments = self.manager.get_all_equipment(farm_id=self.farm_id)
        for row, eq in enumerate(equipments):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(eq.id)))
            self.table.setItem(row, 1, QTableWidgetItem(eq.name))
            self.table.setItem(row, 2, QTableWidgetItem(eq.description))
            self.table.setItem(row, 3, QTableWidgetItem(eq.purchase_date.strftime("%Y-%m-%d") if eq.purchase_date else ""))
            self.table.setItem(row, 4, QTableWidgetItem(f"{eq.purchase_price:,.0f}" if eq.purchase_price else ""))
            self.table.setItem(row, 5, QTableWidgetItem(eq.status.value))

    def add_equipment(self):
        if not self.farm_id:
            QMessageBox.warning(self, "Warning", "Please select a farm first.")
            return
            
        dialog = EquipmentDialog(parent=self)
        if dialog.exec():
            try:
                data = dialog.get_data()
                data['farm_id'] = self.farm_id
                self.manager.create_equipment(**data)
                self.load_equipment()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def edit_equipment(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Selection Error", "Please select an equipment to edit.")
        eq_id = int(self.table.item(row, 0).text())
        equipment = self.manager.get_equipment_by_id(eq_id)
        dialog = EquipmentDialog(equipment, self)
        if dialog.exec():
            try:
                self.manager.update_equipment(eq_id, **dialog.get_data())
                self.load_equipment()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))
    
    def delete_equipment(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Selection Error", "Please select an equipment to delete.")
        eq_id = int(self.table.item(row, 0).text())
        
        reply = QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete this equipment record?")
        
        if reply == QMessageBox.Yes:
            try:
                self.manager.delete_equipment(eq_id)
                self.load_equipment()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))
            
    def refresh_data(self):
        self.load_equipment()
