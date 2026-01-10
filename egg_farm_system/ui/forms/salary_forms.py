"""
UI Forms for Salary Payment Management.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QDoubleSpinBox,
    QDateEdit, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QLabel,
)
from PySide6.QtCore import QDate, QTimer, Qt
from PySide6.QtGui import QFont

from egg_farm_system.modules.employees import EmployeeManager, SalaryManager
from egg_farm_system.database.models import Employee
from egg_farm_system.ui.widgets.loading_overlay import LoadingOverlay
from egg_farm_system.ui.widgets.success_message import SuccessMessage
from egg_farm_system.ui.widgets.keyboard_shortcuts import KeyboardShortcuts

class SalaryPaymentWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.employee_manager = EmployeeManager()
        self.salary_manager = SalaryManager()
        self.employees = []
        self.loading_overlay = LoadingOverlay(self)

        self.setup_ui()
        self.load_employees()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Form for new payment
        form_layout = QFormLayout()
        
        # Employee selection with required indicator
        employee_label = QLabel("Select Employee: <span style='color: red;'>*</span>")
        employee_label.setTextFormat(Qt.RichText)
        self.employee_combo = QComboBox()
        self.employee_combo.setEditable(False)  # Prevent editing
        self.employee_combo.setToolTip("Select the employee for salary payment (required)")
        self.employee_combo.currentIndexChanged.connect(self.on_employee_selected)

        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0, 10_000_000)
        self.amount_spinbox.setSuffix(" AFN")
        self.amount_spinbox.setToolTip("Enter the payment amount in AFN (required)")
        self.amount_spinbox.setValue(0.00)  # Set default value instead of placeholder

        self.period_start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.period_start_date.setCalendarPopup(True)
        self.period_start_date.setDisplayFormat("yyyy-MM-dd")
        self.period_start_date.setToolTip("Select the start date of the pay period (required)")
        
        self.period_end_date = QDateEdit(QDate.currentDate())
        self.period_end_date.setCalendarPopup(True)
        self.period_end_date.setDisplayFormat("yyyy-MM-dd")
        self.period_end_date.setToolTip("Select the end date of the pay period (required)")

        self.payment_date = QDateEdit(QDate.currentDate())
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDisplayFormat("yyyy-MM-dd")
        self.payment_date.setToolTip("Select the payment date (required)")

        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional notes about this payment...")
        self.notes_edit.setToolTip("Enter any additional notes about this payment (optional)")

        self.record_button = QPushButton("Record Payment")
        self.record_button.setMinimumWidth(120)
        self.record_button.setMinimumHeight(35)
        self.record_button.setToolTip("Record the salary payment (Ctrl+S)")
        self.record_button.clicked.connect(self.record_payment)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.SAVE, self.record_payment)

        # Required field indicators
        amount_label = QLabel("Payment Amount: <span style='color: red;'>*</span>")
        amount_label.setTextFormat(Qt.RichText)
        period_start_label = QLabel("Pay Period Start: <span style='color: red;'>*</span>")
        period_start_label.setTextFormat(Qt.RichText)
        period_end_label = QLabel("Pay Period End: <span style='color: red;'>*</span>")
        period_end_label.setTextFormat(Qt.RichText)
        payment_date_label = QLabel("Payment Date: <span style='color: red;'>*</span>")
        payment_date_label.setTextFormat(Qt.RichText)

        form_layout.addRow(employee_label, self.employee_combo)
        form_layout.addRow(amount_label, self.amount_spinbox)
        form_layout.addRow(period_start_label, self.period_start_date)
        form_layout.addRow(period_end_label, self.period_end_date)
        form_layout.addRow(payment_date_label, self.payment_date)
        form_layout.addRow("Notes:", self.notes_edit)
        form_layout.addRow(self.record_button)

        main_layout.addLayout(form_layout)

        # Table for payment history
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(5)
        self.payments_table.setHorizontalHeaderLabels(["Payment Date", "Amount (AFN)", "Period Start", "Period End", "Notes"])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.payments_table.verticalHeader().setMinimumSectionSize(40)
        self.payments_table.verticalHeader().setDefaultSectionSize(40)
        
        main_layout.addWidget(self.payments_table)

    def load_employees(self):
        """Load employees into combo box"""
        self.loading_overlay.set_message("Loading employees...")
        self.loading_overlay.show()
        QTimer.singleShot(50, self._do_load_employees)
    
    def _do_load_employees(self):
        """Perform the actual employee loading"""
        # Block signals during loading to prevent unwanted triggers
        self.employee_combo.blockSignals(True)
        self.employee_combo.clear()
        try:
            self.employees = self.employee_manager.get_all_employees(active_only=True)
            if not self.employees:
                self.employee_combo.addItem("No employees available", None)
                self.loading_overlay.hide()
                self.employee_combo.blockSignals(False)
                return
            
            for emp in self.employees:
                self.employee_combo.addItem(emp.full_name, emp.id)  # text, userData
            
            # Select first employee by default if available
            if self.employee_combo.count() > 0:
                self.employee_combo.setCurrentIndex(0)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading employees: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load employees: {str(e)}")
            self.employee_combo.addItem("Error loading employees", None)
        finally:
            self.employee_combo.blockSignals(False)
            self.loading_overlay.hide()
            # Trigger selection manually after loading
            if self.employee_combo.count() > 0 and self.employee_combo.currentIndex() >= 0:
                self.on_employee_selected(self.employee_combo.currentIndex())

    def on_employee_selected(self, index):
        """Handle employee selection"""
        if index < 0:
            return
        
        employee_id = self.employee_combo.itemData(index)
        if employee_id is not None:
            self.load_payment_history(employee_id)

    def load_payment_history(self, employee_id):
        """Load payment history for selected employee"""
        try:
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
                self.payments_table.setItem(row, 4, QTableWidgetItem(payment.notes or ""))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading payment history: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load payment history: {str(e)}")

    def record_payment(self):
        """Record salary payment"""
        current_index = self.employee_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "Validation Error", "Please select an employee.")
            return
        
        employee_id = self.employee_combo.itemData(current_index)
        if not employee_id or employee_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select a valid employee.")
            return

        amount = self.amount_spinbox.value()
        if amount <= 0:
            QMessageBox.warning(self, "Warning", "Payment amount must be positive.")
            return

        # Validate dates
        period_start = self.period_start_date.date().toPython()
        period_end = self.period_end_date.date().toPython()
        payment_date = self.payment_date.date().toPython()
        
        if period_start > period_end:
            QMessageBox.warning(self, "Validation Error", "Pay period start date must be before end date.")
            return
        
        notes = self.notes_edit.text().strip()

        # Show loading overlay
        self.loading_overlay.set_message("Recording payment...")
        self.loading_overlay.show()
        QTimer.singleShot(50, lambda: self._do_record_payment(employee_id, amount, period_start, period_end, payment_date, notes))
    
    def _do_record_payment(self, employee_id, amount, period_start, period_end, payment_date, notes):
        """Perform the actual payment recording"""
        try:
            self.salary_manager.record_payment(
                employee_id=employee_id,
                amount_paid=amount,
                period_start=period_start,
                period_end=period_end,
                payment_date=payment_date,
                notes=notes,
            )
            self.loading_overlay.hide()
            
            # Show success message
            success_msg = SuccessMessage(self, "Salary payment recorded successfully")
            success_msg.show()
            
            # Refresh payment history
            self.load_payment_history(employee_id)
            
            # Clear form (keep employee selected)
            self.amount_spinbox.setValue(0)
            self.notes_edit.clear()

        except ValueError as e:
            self.loading_overlay.hide()
            QMessageBox.warning(self, "Validation Error", f"Invalid input: {str(e)}")
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, "Error", f"Failed to record payment: {str(e)}")

