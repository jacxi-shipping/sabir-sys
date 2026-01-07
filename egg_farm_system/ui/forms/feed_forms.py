"""
Feed management forms for Raw Materials, Formulas, Production, and Issuing.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTableWidget, QTableWidgetItem, QTabWidget,
    QDoubleSpinBox, QHeaderView, QSplitter, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from egg_farm_system.modules.feed_mill import RawMaterialManager, FeedFormulaManager, FeedProductionManager, FeedIssueManager
from egg_farm_system.modules.sheds import ShedManager
from egg_farm_system.database.models import FeedType, Shed, FinishedFeed, RawMaterial

# --- Dialog for Add/Edit Raw Material ---
class RawMaterialDialog(QDialog):
    def __init__(self, material=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Edit' if material else 'Add'} Raw Material")
        self.layout = QFormLayout(self)
        self.name_edit = QLineEdit(material.name if material else "")
        self.cost_afg_spin = QDoubleSpinBox()
        self.cost_afg_spin.setRange(0, 1_000_000)
        self.cost_afg_spin.setValue(material.cost_afg if material else 0)
        self.alert_spin = QDoubleSpinBox()
        self.alert_spin.setRange(0, 1_000_000)
        self.alert_spin.setValue(material.low_stock_alert if material else 50)
        self.layout.addRow("Name:", self.name_edit)
        self.layout.addRow("Cost (AFG per unit):", self.cost_afg_spin)
        self.layout.addRow("Low Stock Alert (kg):", self.alert_spin)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        buttons_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(35)
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        self.layout.addRow(buttons_layout)

    def get_data(self):
        return {"name": self.name_edit.text(), "cost_afg": self.cost_afg_spin.value(), "cost_usd": 0, "low_stock_alert": self.alert_spin.value()}

# --- Raw Materials Tab ---
class RawMaterialsTab(QWidget):
    def __init__(self, manager: RawMaterialManager):
        super().__init__()
        self.manager = manager
        self.init_ui()
        self.load_materials()

    def init_ui(self):
        layout = QVBoxLayout(self)
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Material"); add_btn.clicked.connect(self.add_material)
        edit_btn = QPushButton("Edit Selected"); edit_btn.clicked.connect(self.edit_material)
        del_btn = QPushButton("Delete Selected"); del_btn.clicked.connect(self.delete_material)
        buttons_layout.addWidget(add_btn); buttons_layout.addWidget(edit_btn); buttons_layout.addWidget(del_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(5); self.table.setHorizontalHeaderLabels(["ID", "Name", "Current Stock (kg)", "Cost (AFG)", "Low Stock Alert"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)

    def load_materials(self):
        self.table.setRowCount(0)
        for row, material in enumerate(self.manager.get_all_materials()):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(material.id)))
            self.table.setItem(row, 1, QTableWidgetItem(material.name))
            self.table.setItem(row, 2, QTableWidgetItem(f"{material.current_stock:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{material.cost_afg:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{material.low_stock_alert:.2f}"))

    def add_material(self):
        dialog = RawMaterialDialog(parent=self)
        if dialog.exec():
            try:
                self.manager.create_material(**dialog.get_data())
                self.load_materials()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def edit_material(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Selection Error", "Please select a material.")
        mat_id = int(self.table.item(row, 0).text())
        material = self.manager.get_material_by_id(mat_id)
        dialog = RawMaterialDialog(material, self)
        if dialog.exec():
            try:
                self.manager.update_material(mat_id, **dialog.get_data())
                self.load_materials()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def delete_material(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Selection Error", "Please select a material.")
        mat_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete '{name}'? This cannot be undone.")
        if reply == QMessageBox.Yes:
            try:
                self.manager.delete_material(mat_id)
                self.load_materials()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

# --- Dialogs for Formula Tab ---
class FormulaDialog(QDialog):
    def __init__(self, formula=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Edit' if formula else 'Add'} Formula")
        layout = QFormLayout(self); self.name_edit = QLineEdit(formula.name if formula else "")
        self.type_combo = QComboBox(); self.type_combo.addItems([t.value for t in FeedType])
        if formula: self.type_combo.setCurrentText(formula.feed_type.value)
        layout.addRow("Name:", self.name_edit); layout.addRow("Type:", self.type_combo)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.setContentsMargins(0, 10, 0, 0)
        buttons.addStretch()
        save = QPushButton("Save")
        save.setMinimumWidth(100)
        save.setMinimumHeight(35)
        save.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.setMinimumWidth(100)
        cancel.setMinimumHeight(35)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        layout.addRow(buttons)
    def get_data(self): return {"name": self.name_edit.text(), "feed_type": FeedType(self.type_combo.currentText())}

class IngredientDialog(QDialog):
    def __init__(self, raw_material_manager: RawMaterialManager, parent=None):
        super().__init__(parent)
        self.raw_material_manager = raw_material_manager
        self.setWindowTitle("Add Ingredient")
        layout = QFormLayout(self)
        self.mat_combo = QComboBox()
        self.mat_combo.addItems([m.name for m in self.raw_material_manager.get_all_materials()])
        self.percent_spin = QDoubleSpinBox(); self.percent_spin.setRange(0.01, 100.0)
        layout.addRow("Material:", self.mat_combo); layout.addRow("Percentage:", self.percent_spin)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.setContentsMargins(0, 10, 0, 0)
        buttons.addStretch()
        save = QPushButton("Save")
        save.setMinimumWidth(100)
        save.setMinimumHeight(35)
        save.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.setMinimumWidth(100)
        cancel.setMinimumHeight(35)
        cancel.clicked.connect(self.reject)
        buttons.addWidget(save)
        buttons.addWidget(cancel)
        layout.addRow(buttons)
    def get_data(self):
        mat_name = self.mat_combo.currentText()
        material = next((m for m in self.raw_material_manager.get_all_materials() if m.name == mat_name), None)
        return {"material_id": material.id if material else None, "percentage": self.percent_spin.value()}

# --- Formulas Tab ---
class FormulasTab(QWidget):
    def __init__(self, formula_manager: FeedFormulaManager, raw_material_manager: RawMaterialManager):
        super().__init__()
        self.manager = formula_manager
        self.raw_material_manager = raw_material_manager
        self.init_ui(); self.load_formulas()

    def init_ui(self):
        layout = QVBoxLayout(self); splitter = QSplitter(Qt.Horizontal)
        formulas_widget = QWidget(); formulas_layout = QVBoxLayout(formulas_widget)
        formula_buttons = QHBoxLayout(); add_f = QPushButton("Add"); add_f.clicked.connect(self.add_formula)
        del_f = QPushButton("Delete"); del_f.clicked.connect(self.delete_formula)
        formula_buttons.addWidget(add_f); formula_buttons.addWidget(del_f); formula_buttons.addStretch()
        formulas_layout.addLayout(formula_buttons)
        self.formulas_table = QTableWidget(); self.formulas_table.setColumnCount(3); self.formulas_table.setHorizontalHeaderLabels(["ID", "Name", "Type"])
        self.formulas_table.setSelectionBehavior(QTableWidget.SelectRows); self.formulas_table.setColumnHidden(0, True)
        self.formulas_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.formulas_table.selectionModel().selectionChanged.connect(self.load_ingredients)
        formulas_layout.addWidget(self.formulas_table); splitter.addWidget(formulas_widget)
        ingredients_widget = QWidget(); ingredients_layout = QVBoxLayout(ingredients_widget)
        ing_buttons = QHBoxLayout(); add_i = QPushButton("Add"); add_i.clicked.connect(self.add_ingredient)
        del_i = QPushButton("Remove"); del_i.clicked.connect(self.remove_ingredient)
        ing_buttons.addWidget(add_i); ing_buttons.addWidget(del_i); ing_buttons.addStretch()
        ingredients_layout.addLayout(ing_buttons)
        self.ingredients_table = QTableWidget(); self.ingredients_table.setColumnCount(3); self.ingredients_table.setHorizontalHeaderLabels(["ID", "Ingredient", "%"])
        self.ingredients_table.setColumnHidden(0, True); self.ingredients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        ingredients_layout.addWidget(self.ingredients_table); self.validation_label = QLabel("Validation: N/A")
        ingredients_layout.addWidget(self.validation_label); splitter.addWidget(ingredients_widget)
        splitter.setSizes([250, 450]); layout.addWidget(splitter)

    def get_selected_formula_id(self):
        row = self.formulas_table.currentRow()
        return int(self.formulas_table.item(row, 0).text()) if row >= 0 else None

    def load_formulas(self):
        self.formulas_table.setRowCount(0)
        for row, f in enumerate(self.manager.get_formulas(active_only=False)):
            self.formulas_table.insertRow(row); self.formulas_table.setItem(row, 0, QTableWidgetItem(str(f.id)))
            self.formulas_table.setItem(row, 1, QTableWidgetItem(f.name)); self.formulas_table.setItem(row, 2, QTableWidgetItem(f.feed_type.value))

    def load_ingredients(self):
        self.ingredients_table.setRowCount(0); formula_id = self.get_selected_formula_id()
        if not formula_id: self.validation_label.setText("Validation: N/A"); return
        formula = self.manager.get_formula_by_id(formula_id)
        if formula:
            for row, ing in enumerate(formula.ingredients):
                self.ingredients_table.insertRow(row); self.ingredients_table.setItem(row, 0, QTableWidgetItem(str(ing.id)))
                self.ingredients_table.setItem(row, 1, QTableWidgetItem(ing.material.name)); self.ingredients_table.setItem(row, 2, QTableWidgetItem(f"{ing.percentage:.2f}"))
        is_valid, msg = self.manager.validate_formula(formula_id)
        self.validation_label.setText(f"Validation: {msg}"); self.validation_label.setStyleSheet("color: green;" if is_valid else "color: red;")

    def add_formula(self):
        dialog = FormulaDialog(parent=self)
        if dialog.exec():
            try: 
                self.manager.create_formula(**dialog.get_data())
                self.load_formulas()
                # Refresh production tab's formula list
                self.parent().parent().findChild(ProductionTab).load_formulas()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def delete_formula(self):
        formula_id = self.get_selected_formula_id()
        if not formula_id: return QMessageBox.warning(self, "Selection Error", "Please select a formula.")
        reply = QMessageBox.question(self, "Confirm Delete", "Delete selected formula? This is final.")
        if reply == QMessageBox.Yes:
            try: 
                self.manager.delete_formula(formula_id)
                self.load_formulas()
                self.load_ingredients()
                self.parent().parent().findChild(ProductionTab).load_formulas()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def add_ingredient(self):
        formula_id = self.get_selected_formula_id()
        if not formula_id: return QMessageBox.warning(self, "Selection Error", "Please select a formula first.")
        dialog = IngredientDialog(self.raw_material_manager, parent=self)
        if dialog.exec():
            try: data = dialog.get_data(); self.manager.add_ingredient(formula_id, data['material_id'], data['percentage']); self.load_ingredients()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def remove_ingredient(self):
        row = self.ingredients_table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Selection Error", "Please select an ingredient.")
        formulation_id = int(self.ingredients_table.item(row, 0).text())
        reply = QMessageBox.question(self, "Confirm Remove", "Remove selected ingredient?")
        if reply == QMessageBox.Yes:
            try: self.manager.remove_ingredient(formulation_id); self.load_ingredients()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

# --- Production Tab ---
class ProductionTab(QWidget):
    def __init__(self, production_manager: FeedProductionManager, formula_manager: FeedFormulaManager):
        super().__init__()
        self.manager = production_manager
        self.formula_manager = formula_manager
        self.init_ui()
    def init_ui(self):
        layout = QFormLayout(self)
        self.formula_combo = QComboBox(); self.quantity_spin = QDoubleSpinBox(); self.quantity_spin.setRange(1.0, 10000.0)
        self.exchange_rate_spin = QDoubleSpinBox(); self.exchange_rate_spin.setRange(1.0, 1000.0); self.exchange_rate_spin.setValue(78.0)
        produce_btn = QPushButton("Produce Batch"); produce_btn.clicked.connect(self.produce)
        layout.addRow("Formula:", self.formula_combo); layout.addRow("Quantity (kg):", self.quantity_spin)
        layout.addRow("Exchange Rate (AFN/USD):", self.exchange_rate_spin); layout.addRow(produce_btn)
        self.load_formulas()
    def load_formulas(self):
        self.formula_combo.clear()
        self.formula_combo.addItems([f.name for f in self.formula_manager.get_formulas()])
    def produce(self):
        formula_name = self.formula_combo.currentText()
        formula = next((f for f in self.formula_manager.get_formulas() if f.name == formula_name), None)
        if not formula: return QMessageBox.critical(self, "Error", "Formula not found.")
        is_valid, msg = self.formula_manager.validate_formula(formula.id)
        if not is_valid: return QMessageBox.warning(self, "Validation Error", f"Cannot produce with invalid formula: {msg}")
        reply = QMessageBox.question(self, "Confirm Production", f"This will consume raw materials. Proceed?")
        if reply == QMessageBox.Yes:
            try:
                self.manager.produce_batch(formula.id, self.quantity_spin.value(), self.exchange_rate_spin.value())
                QMessageBox.information(self, "Success", "Feed batch produced successfully.")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

# --- Issuing Tab ---
class IssuingTab(QWidget):
    def __init__(self, issue_manager: FeedIssueManager, shed_manager: ShedManager):
        super().__init__()
        self.manager = issue_manager
        self.shed_manager = shed_manager
        self.init_ui()
    def init_ui(self):
        layout = QFormLayout(self)
        self.feed_combo = QComboBox(); self.shed_combo = QComboBox()
        self.quantity_spin = QDoubleSpinBox(); self.quantity_spin.setRange(0.1, 5000.0)
        self.date_edit = QDateEdit(QDate.currentDate()); self.date_edit.setCalendarPopup(True)
        issue_btn = QPushButton("Issue Feed"); issue_btn.clicked.connect(self.issue)
        layout.addRow("Finished Feed:", self.feed_combo); layout.addRow("Issue to Shed:", self.shed_combo)
        layout.addRow("Quantity (kg):", self.quantity_spin); layout.addRow("Date:", self.date_edit); layout.addRow(issue_btn)
        self.load_combos()
    def load_combos(self):
        self.feed_combo.addItems([f.feed_type.value for f in self.manager.session.query(FinishedFeed).all()])
        self.shed_combo.addItems([s.name for s in self.shed_manager.get_all_sheds()])
    def issue(self):
        feed_type = FeedType(self.feed_combo.currentText())
        finished_feed = self.manager.session.query(FinishedFeed).filter_by(feed_type=feed_type).first()
        shed_name = self.shed_combo.currentText()
        shed = self.shed_manager.session.query(Shed).filter_by(name=shed_name).first()
        if not finished_feed or not shed: return QMessageBox.critical(self, "Error", "Feed or Shed not found.")
        try:
            self.manager.issue_feed(shed.id, finished_feed.id, self.quantity_spin.value(), self.date_edit.date().toPython())
            QMessageBox.information(self, "Success", "Feed issued successfully.")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

# --- Main Feed Widget ---
class FeedFormWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Centralized manager instances
        self.raw_material_manager = RawMaterialManager()
        self.formula_manager = FeedFormulaManager()
        self.production_manager = FeedProductionManager()
        self.issue_manager = FeedIssueManager()
        self.shed_manager = ShedManager()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Feed Management"); title_font = QFont(); title_font.setPointSize(14); title_font.setBold(True); title.setFont(title_font)
        layout.addWidget(title)
        
        tab_widget = QTabWidget()
        # Pass manager instances to each tab
        raw_materials_tab = RawMaterialsTab(self.raw_material_manager)
        formulas_tab = FormulasTab(self.formula_manager, self.raw_material_manager)
        production_tab = ProductionTab(self.production_manager, self.formula_manager)
        
        tab_widget.addTab(raw_materials_tab, "Raw Materials")
        tab_widget.addTab(formulas_tab, "Feed Formulas")
        tab_widget.addTab(production_tab, "Feed Production")
        tab_widget.addTab(IssuingTab(self.issue_manager, self.shed_manager), "Issue Feed")
        
        layout.addWidget(tab_widget)
        self.setLayout(layout)
