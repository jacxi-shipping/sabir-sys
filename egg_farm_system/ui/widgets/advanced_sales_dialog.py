"""
Advanced Sales Dialog with Carton-based Selling
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDoubleSpinBox, QComboBox, QDateTimeEdit, QMessageBox, QGroupBox,
    QGridLayout, QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt, QDateTime, Signal, QTimer
from PySide6.QtGui import QFont
from datetime import datetime
import logging

from egg_farm_system.utils.egg_management import EggManagementSystem
from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.farms import FarmManager

logger = logging.getLogger(__name__)


class AdvancedSalesDialog(QDialog):
    """Advanced sales dialog with carton-based selling"""
    
    sale_saved = Signal()
    
    def __init__(self, parent=None, sale=None, farm_id=None):
        super().__init__(parent)
        self.sale = sale
        self.farm_id = farm_id
        self.egg_manager = EggManagementSystem()
        self.sales_manager = SalesManager()
        self.party_manager = PartyManager()
        self.farm_manager = FarmManager()
        
        self.setWindowTitle("Advanced Egg Sale" if not sale else "Edit Sale")
        self.setMinimumWidth(600)
        self.setMinimumHeight(550)
        self.setModal(True)  # Make dialog modal
        
        self.init_ui()
        self.load_data()
        self.setup_connections()
        
        # Ensure critical inputs are definitely enabled/writable
        self.carton_spin.setReadOnly(False)
        self.rate_per_egg_afg.setReadOnly(False)
        self.rate_per_egg_usd.setReadOnly(False)
        self.date_edit.setReadOnly(False)
        self.notes_edit.setReadOnly(False)
    
    def showEvent(self, event):
        """Ensure everything is enabled when shown"""
        super().showEvent(event)
        # Use a timer to ensure enabled state after the dialog is fully shown
        # This handles cases where parent modality might initially affect state
        QTimer.singleShot(10, self.ensure_enabled_and_focused)

    def ensure_enabled_and_focused(self):
        """Force enable the dialog and set initial focus"""
        self.setEnabled(True)
        # Ensure inputs are enabled
        self.carton_spin.setEnabled(True)
        self.party_combo.setEnabled(True)
        
        # Set focus
        self.carton_spin.setFocus()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel("Egg Sale - Carton Based")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Basic Information Group
        basic_group = QGroupBox("Sale Information")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(8)
        
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        
        self.party_combo = QComboBox()
        self.party_combo.setEditable(False)
        parties = self.party_manager.get_all_parties()
        for party in parties:
            self.party_combo.addItem(party.name, party.id)
        
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Credit"])
        self.payment_method_combo.setCurrentText("Cash")
        
        basic_layout.addRow("Date:", self.date_edit)
        basic_layout.addRow("Customer:", self.party_combo)
        basic_layout.addRow("Payment Method:", self.payment_method_combo)
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Carton & Grade Information Group
        carton_group = QGroupBox("Carton & Grade Details")
        carton_layout = QGridLayout()
        carton_layout.setSpacing(8)
        
        # Carton quantity
        carton_layout.addWidget(QLabel("Cartons:"), 0, 0)
        self.carton_spin = QDoubleSpinBox()
        self.carton_spin.setMinimum(0)
        self.carton_spin.setMaximum(10000)
        self.carton_spin.setDecimals(2)
        self.carton_spin.setSuffix(" cartons")
        self.carton_spin.setKeyboardTracking(True)
        self.carton_spin.setReadOnly(False)
        carton_layout.addWidget(self.carton_spin, 0, 1)
        
        # Egg grade
        carton_layout.addWidget(QLabel("Egg Grade:"), 0, 2)
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["Small", "Medium", "Large", "Broken", "Mixed"])
        carton_layout.addWidget(self.grade_combo, 0, 3)
        
        # Calculated eggs display
        self.eggs_label = QLabel("= 0 eggs")
        eggs_font = QFont()
        eggs_font.setBold(True)
        self.eggs_label.setFont(eggs_font)
        carton_layout.addWidget(self.eggs_label, 1, 0, 1, 2)
        
        # Tray conversion display
        self.tray_label = QLabel("= 0 trays")
        carton_layout.addWidget(self.tray_label, 1, 2, 1, 2)
        
        carton_group.setLayout(carton_layout)
        layout.addWidget(carton_group)
        
        # Pricing Group
        pricing_group = QGroupBox("Pricing")
        pricing_layout = QFormLayout()
        pricing_layout.setSpacing(8)
        
        self.rate_per_egg_afg = QDoubleSpinBox()
        self.rate_per_egg_afg.setMinimum(0)
        self.rate_per_egg_afg.setMaximum(1000)
        self.rate_per_egg_afg.setDecimals(2)
        self.rate_per_egg_afg.setSuffix(" AFG/egg")
        self.rate_per_egg_afg.setKeyboardTracking(True)
        self.rate_per_egg_afg.setReadOnly(False)
        
        self.rate_per_egg_usd = QDoubleSpinBox()
        self.rate_per_egg_usd.setMinimum(0)
        self.rate_per_egg_usd.setMaximum(100)
        self.rate_per_egg_usd.setDecimals(2)
        self.rate_per_egg_usd.setSuffix(" USD/egg")
        self.rate_per_egg_usd.setKeyboardTracking(True)
        self.rate_per_egg_usd.setReadOnly(False)
        
        pricing_layout.addRow("Rate per Egg (AFG):", self.rate_per_egg_afg)
        pricing_layout.addRow("Rate per Egg (USD):", self.rate_per_egg_usd)
        pricing_group.setLayout(pricing_layout)
        layout.addWidget(pricing_group)
        
        # Expenses Group
        expense_group = QGroupBox("Expenses")
        expense_layout = QFormLayout()
        expense_layout.setSpacing(8)
        
        # Tray expense (auto-calculated)
        self.tray_expense_label = QLabel("0.00 AFG")
        expense_layout.addRow("Tray Expense:", self.tray_expense_label)
        
        # Carton expense (auto-calculated)
        self.carton_expense_label = QLabel("0.00 AFG")
        expense_layout.addRow("Carton Expense:", self.carton_expense_label)
        
        # Total expense
        self.total_expense_label = QLabel("0.00 AFG")
        expense_font = QFont()
        expense_font.setBold(True)
        self.total_expense_label.setFont(expense_font)
        expense_layout.addRow("Total Expense:", self.total_expense_label)
        
        expense_group.setLayout(expense_layout)
        layout.addWidget(expense_group)
        
        # Cost Summary Group
        summary_group = QGroupBox("Cost Summary")
        summary_layout = QFormLayout()
        summary_layout.setSpacing(8)
        
        self.egg_cost_label = QLabel("0.00 AFG")
        summary_layout.addRow("Egg Cost:", self.egg_cost_label)
        
        self.total_cost_label = QLabel("0.00 AFG")
        cost_font = QFont()
        cost_font.setBold(True)
        cost_font.setPointSize(11)
        self.total_cost_label.setFont(cost_font)
        summary_layout.addRow("Total Cost (Eggs + Expenses):", self.total_cost_label)
        
        self.selling_price_label = QLabel("0.00 AFG")
        selling_font = QFont()
        selling_font.setBold(True)
        selling_font.setPointSize(11)
        self.selling_price_label.setFont(selling_font)
        self.selling_price_label.setStyleSheet("color: green;")
        summary_layout.addRow("Selling Price:", self.selling_price_label)
        
        self.profit_label = QLabel("0.00 AFG")
        profit_font = QFont()
        profit_font.setBold(True)
        profit_font.setPointSize(11)
        self.profit_label.setFont(profit_font)
        summary_layout.addRow("Profit:", self.profit_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Notes
        notes_label = QLabel("Notes:")
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        layout.addWidget(notes_label)
        layout.addWidget(self.notes_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("Save Sale")
        self.save_btn.setMinimumWidth(120)
        self.save_btn.setMinimumHeight(35)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(120)
        self.cancel_btn.setMinimumHeight(35)
        
        self.save_btn.clicked.connect(self.save_sale)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.carton_spin.valueChanged.connect(self.update_calculations)
        self.rate_per_egg_afg.valueChanged.connect(self.update_calculations)
        self.rate_per_egg_usd.valueChanged.connect(self.update_calculations)
        self.grade_combo.currentTextChanged.connect(self.update_calculations)
    
    def load_data(self):
        """Load existing sale data if editing"""
        if self.sale:
            self.date_edit.setDateTime(QDateTime.fromString(
                self.sale.date.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss"
            ))
            
            # Find party index
            for i in range(self.party_combo.count()):
                if self.party_combo.itemData(i) == self.sale.party_id:
                    self.party_combo.setCurrentIndex(i)
                    break
            
            # Load payment method
            if hasattr(self.sale, 'payment_method') and self.sale.payment_method:
                index = self.payment_method_combo.findText(self.sale.payment_method)
                if index >= 0:
                    self.payment_method_combo.setCurrentIndex(index)
            
            # Load carton data if available
            if self.sale.cartons:
                self.carton_spin.setValue(self.sale.cartons)
            else:
                # Convert quantity to cartons
                cartons = self.egg_manager.eggs_to_cartons(self.sale.quantity)
                self.carton_spin.setValue(cartons)
            
            if self.sale.egg_grade:
                index = self.grade_combo.findText(self.sale.egg_grade.capitalize())
                if index >= 0:
                    self.grade_combo.setCurrentIndex(index)
            
            self.rate_per_egg_afg.setValue(self.sale.rate_afg)
            self.rate_per_egg_usd.setValue(self.sale.rate_usd)
            
            if self.sale.notes:
                self.notes_edit.setPlainText(self.sale.notes)
        
        self.update_calculations()
    
    def update_calculations(self):
        """Update all calculations"""
        try:
            cartons = self.carton_spin.value()
            eggs = self.egg_manager.cartons_to_eggs(cartons)
            trays = self.egg_manager.eggs_to_trays(eggs)
            
            # Update display
            self.eggs_label.setText(f"= {eggs:,} eggs")
            self.tray_label.setText(f"= {trays:.2f} trays")
            
            # Get expenses
            tray_expense_per_tray = self.egg_manager.get_tray_expense()
            carton_expense_per_carton = self.egg_manager.get_carton_expense()
            
            # Calculate expenses (7 trays per carton for packaging)
            trays_needed = cartons * EggManagementSystem.TRAYS_EXPENSE_PER_CARTON
            tray_expense = trays_needed * tray_expense_per_tray
            carton_expense = cartons * carton_expense_per_carton
            total_expense = tray_expense + carton_expense
            
            # Update expense labels
            self.tray_expense_label.setText(f"{tray_expense:,.2f} AFG")
            self.carton_expense_label.setText(f"{carton_expense:,.2f} AFG")
            self.total_expense_label.setText(f"{total_expense:,.2f} AFG")
            
            # Calculate costs
            rate_per_egg = self.rate_per_egg_afg.value()
            egg_cost = eggs * rate_per_egg
            total_cost = egg_cost + total_expense
            
            # Update cost labels
            self.egg_cost_label.setText(f"{egg_cost:,.2f} AFG")
            self.total_cost_label.setText(f"{total_cost:,.2f} AFG")
            
            # Calculate selling price and profit
            selling_price = eggs * rate_per_egg  # Selling price (without expenses)
            profit = selling_price - total_cost
            
            self.selling_price_label.setText(f"{selling_price:,.2f} AFG")
            
            # Color code profit
            if profit >= 0:
                self.profit_label.setText(f"{profit:,.2f} AFG")
                self.profit_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.profit_label.setText(f"{profit:,.2f} AFG")
                self.profit_label.setStyleSheet("color: red; font-weight: bold;")
        
        except Exception as e:
            logger.error(f"Error updating calculations: {e}")
    
    def save_sale(self):
        """Save the sale"""
        try:
            # Validation
            if self.party_combo.currentData() is None:
                QMessageBox.warning(self, "Validation Error", "Please select a customer.")
                return
            
            if self.carton_spin.value() <= 0:
                QMessageBox.warning(self, "Validation Error", "Carton quantity must be greater than 0.")
                return
            
            if self.rate_per_egg_afg.value() <= 0:
                QMessageBox.warning(self, "Validation Error", "Rate per egg must be greater than 0.")
                return
            
            # Get values
            cartons = self.carton_spin.value()
            eggs = self.egg_manager.cartons_to_eggs(cartons)
            grade = self.grade_combo.currentText().lower()
            rate_afg = self.rate_per_egg_afg.value()
            rate_usd = self.rate_per_egg_usd.value()
            
            # Calculate expenses
            tray_expense_per_tray = self.egg_manager.get_tray_expense()
            carton_expense_per_carton = self.egg_manager.get_carton_expense()
            trays_needed = cartons * EggManagementSystem.TRAYS_EXPENSE_PER_CARTON
            tray_expense = trays_needed * tray_expense_per_tray
            carton_expense = cartons * carton_expense_per_carton
            total_expense = tray_expense + carton_expense
            
            # Calculate totals
            total_afg = eggs * rate_afg
            total_usd = eggs * rate_usd
            
            # Get exchange rate
            from egg_farm_system.utils.currency import CurrencyConverter
            converter = CurrencyConverter()
            exchange_rate = converter.get_exchange_rate()
            
            # Record sale with advanced fields
            if self.sale:
                # Update existing sale
                from egg_farm_system.database.db import DatabaseManager
                session = DatabaseManager.get_session()
                try:
                    sale = session.query(self.sale.__class__).filter_by(id=self.sale.id).first()
                    if sale:
                        sale.party_id = self.party_combo.currentData()
                        sale.date = self.date_edit.dateTime().toPython()
                        sale.quantity = eggs
                        sale.cartons = cartons
                        sale.egg_grade = grade
                        sale.rate_afg = rate_afg
                        sale.rate_usd = rate_usd
                        sale.total_afg = total_afg
                        sale.total_usd = total_usd
                        sale.tray_expense_afg = tray_expense
                        sale.carton_expense_afg = carton_expense
                        sale.total_expense_afg = total_expense
                        sale.payment_method = self.payment_method_combo.currentText()
                        sale.notes = self.notes_edit.toPlainText()
                        session.commit()
                finally:
                    session.close()
            else:
                # Create new sale
                self.sales_manager.record_sale_advanced(
                    party_id=self.party_combo.currentData(),
                    cartons=cartons,
                    eggs=eggs,
                    grade=grade,
                    rate_afg=rate_afg,
                    rate_usd=rate_usd,
                    tray_expense_afg=tray_expense,
                    carton_expense_afg=carton_expense,
                    date=self.date_edit.dateTime().toPython(),
                    notes=self.notes_edit.toPlainText(),
                    exchange_rate_used=exchange_rate,
                    payment_method=self.payment_method_combo.currentText()
                )
            
            QMessageBox.information(self, "Success", "Sale recorded successfully!")
            self.sale_saved.emit()
            self.accept()
        
        except Exception as e:
            logger.error(f"Error saving sale: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save sale: {str(e)}")

