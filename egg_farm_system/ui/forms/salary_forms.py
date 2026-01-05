"""
UI Forms for Salary Payment Management.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QDoubleSpinBox,
    QDateEdit, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView,
)
from PySide6.QtCore import QDate

from egg_farm_system.modules.employees import EmployeeManager, SalaryManager
from egg_farm_system.database.models import Employee

class SalaryPaymentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.employee_manager = EmployeeManager()
        self.salary_manager = SalaryManager()
        self.employees = []

        self.setup_ui()
        self.load_employees()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Form for new payment
        form_layout = QFormLayout()
        
        self.employee_combo = QComboBox()
        self.employee_combo.currentIndexChanged.connect(self.on_employee_selected)

        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0, 10_000_000)
        self.amount_spinbox.setSuffix(" AFN")

        self.period_start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.period_start_date.setCalendarPopup(True)
        self.period_end_date = QDateEdit(QDate.currentDate())
        self.period_end_date.setCalendarPopup(True)

        self.payment_date = QDateEdit(QDate.currentDate())
        self.payment_date.setCalendarPopup(True)

        self.notes_edit = QLineEdit()

        self.record_button = QPushButton("Record Payment")
        self.record_button.clicked.connect(self.record_payment)

        form_layout.addRow("Select Employee:", self.employee_combo)
        form_layout.addRow("Payment Amount:", self.amount_spinbox)
        form_layout.addRow("Pay Period Start:", self.period_start_date)
        form_layout.addRow("Pay Period End:", self.period_end_date)
        form_layout.addRow("Payment Date:", self.payment_date)
        form_layout.addRow("Notes:", self.notes_edit)
        form_layout.addRow(self.record_button)

        main_layout.addLayout(form_layout)

        # Table for payment history
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(5)
        self.payments_table.setHorizontalHeaderLabels(["Payment Date", "Amount (AFN)", "Period Start", "Period End", "Notes"])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        main_layout.addWidget(self.payments_table)

    def load_employees(self):
        self.employee_combo.clear()
        self.employees = self.employee_manager.get_all_employees(active_only=True)
        for emp in self.employees:
            self.employee_combo.addItem(emp.full_name, userData=emp.id)

    def on_employee_selected(self, index):
        employee_id = self.employee_combo.itemData(index)
        if employee_id:
            self.load_payment_history(employee_id)

    def load_payment_history(self, employee_id):
        self.payments_table.setRowCount(0)
        payments = self.salary_manager.get_payments_for_employee(employee_id)
        if not payments:
            return
            
        self.payments_table.setRowCount(len(payments))
        for row, payment in enumerate(payments):
            self.payments_table.setItem(row, 0, QTableWidgetItem(payment.payment_date.strftime("%Y-%m-%d")))
            self.payments_table.setItem(row, 1, QTableWidgetItem(f"{payment.amount_paid:,.2f}"))
            self.payments_table.setItem(row, 2, QTableWidgetItem(payment.period_start.strftime("%Y-%m-%d")))
            self.payments_table.setItem(row, 3, QTableWidgetItem(payment.period_end.strftime("%Y-%m-%d")))
            self.payments_table.setItem(row, 4, QTableWidgetItem(payment.notes))

    def record_payment(self):
        employee_id = self.employee_combo.currentData()
        if not employee_id:
            QMessageBox.warning(self, "Warning", "Please select an employee.")
            return

        amount = self.amount_spinbox.value()
        if amount <= 0:
            QMessageBox.warning(self, "Warning", "Payment amount must be positive.")
            return

        period_start = self.period_start_date.date().toPython()
        period_end = self.period_end_date.date().toPython()
        payment_date = self.payment_date.date().toPython()
        notes = self.notes_edit.text()

        try:
            self.salary_manager.record_payment(
                employee_id=employee_id,
                amount_paid=amount,
                period_start=period_start,
                period_end=period_end,
                payment_date=payment_date,
                notes=notes,
            )
            QMessageBox.information(self, "Success", "Salary payment recorded successfully.")
            self.load_payment_history(employee_id)
            # Clear form
            self.amount_spinbox.setValue(0)
            self.notes_edit.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record payment: {e}")

