"""
UI Forms for Employee and Salary Management.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTableWidget, QTableWidgetItem, QTabWidget,
    QDoubleSpinBox, QHeaderView, QComboBox, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from egg_farm_system.modules.employees import EmployeeManager
from egg_farm_system.database.models import SalaryPeriod

# --- Dialog for Add/Edit Employee ---
class EmployeeDialog(QDialog):
    def __init__(self, employee=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Edit' if employee else 'Add'} Employee")
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(employee.full_name if employee else "")
        self.title_edit = QLineEdit(employee.job_title if employee else "")
        self.hire_date_edit = QDateEdit(employee.hire_date if employee else QDate.currentDate())
        self.hire_date_edit.setCalendarPopup(True)
        self.salary_amount_spin = QDoubleSpinBox()
        self.salary_amount_spin.setRange(0, 10_000_000)
        self.salary_amount_spin.setValue(employee.salary_amount if employee else 0)
        self.salary_period_combo = QComboBox()
        self.salary_period_combo.addItems([p.value for p in SalaryPeriod])
        if employee:
            self.salary_period_combo.setCurrentText(employee.salary_period.value)

        layout.addRow("Full Name:", self.name_edit)
        layout.addRow("Job Title:", self.title_edit)
        layout.addRow("Hire Date:", self.hire_date_edit)
        layout.addRow("Salary Amount (AFN):", self.salary_amount_spin)
        layout.addRow("Salary Period:", self.salary_period_combo)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save"); save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel"); cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn); buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

    def get_data(self):
        return {
            "full_name": self.name_edit.text(),
            "job_title": self.title_edit.text(),
            "hire_date": self.hire_date_edit.date().toPython(),
            "salary_amount": self.salary_amount_spin.value(),
            "salary_period": SalaryPeriod(self.salary_period_combo.currentText())
        }

# --- Employees Tab ---
class EmployeesTab(QWidget):
    def __init__(self, manager: EmployeeManager):
        super().__init__()
        self.manager = manager
        self.init_ui()
        self.load_employees()

    def init_ui(self):
        layout = QVBoxLayout(self)
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Employee"); add_btn.clicked.connect(self.add_employee)
        edit_btn = QPushButton("Edit Selected"); edit_btn.clicked.connect(self.edit_employee)
        status_btn = QPushButton("Toggle Active Status"); status_btn.clicked.connect(self.toggle_status)
        buttons_layout.addWidget(add_btn); buttons_layout.addWidget(edit_btn); buttons_layout.addWidget(status_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6); self.table.setHorizontalHeaderLabels(["ID", "Name", "Job Title", "Salary (AFN)", "Period", "Status"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)

    def load_employees(self):
        self.table.setRowCount(0)
        employees = self.manager.get_all_employees(active_only=False)
        for row, emp in enumerate(employees):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(emp.id)))
            self.table.setItem(row, 1, QTableWidgetItem(emp.full_name))
            self.table.setItem(row, 2, QTableWidgetItem(emp.job_title))
            self.table.setItem(row, 3, QTableWidgetItem(f"{emp.salary_amount:,.0f}"))
            self.table.setItem(row, 4, QTableWidgetItem(emp.salary_period.value))
            status = "Active" if emp.is_active else "Inactive"
            self.table.setItem(row, 5, QTableWidgetItem(status))

    def add_employee(self):
        dialog = EmployeeDialog(parent=self)
        if dialog.exec():
            try:
                self.manager.create_employee(**dialog.get_data())
                self.load_employees()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def edit_employee(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Selection Error", "Please select an employee.")
        emp_id = int(self.table.item(row, 0).text())
        employee = self.manager.get_employee_by_id(emp_id)
        dialog = EmployeeDialog(employee, self)
        if dialog.exec():
            try:
                self.manager.update_employee(emp_id, **dialog.get_data())
                self.load_employees()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))
    
    def toggle_status(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Selection Error", "Please select an employee.")
        emp_id = int(self.table.item(row, 0).text())
        employee = self.manager.get_employee_by_id(emp_id)
        
        new_status = not employee.is_active
        status_text = "activate" if new_status else "deactivate"
        reply = QMessageBox.question(self, "Confirm Status Change", f"Are you sure you want to {status_text} {employee.full_name}?")
        
        if reply == QMessageBox.Yes:
            try:
                self.manager.set_employee_status(emp_id, new_status)
                self.load_employees()
            except Exception as e: QMessageBox.critical(self, "Error", str(e))

from egg_farm_system.ui.forms.salary_forms import SalaryPaymentWidget

# --- Main Employee Management Widget ---
class EmployeeManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Employee & Salary Management")
        self.employee_manager = EmployeeManager()

        layout = QVBoxLayout(self)
        title = QLabel("Employee Management"); title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        tab_widget = QTabWidget()
        tab_widget.addTab(EmployeesTab(self.employee_manager), "Employees")
        tab_widget.addTab(SalaryPaymentWidget(), "Salary Payments")
        
        layout.addWidget(tab_widget)
        self.setLayout(layout)
