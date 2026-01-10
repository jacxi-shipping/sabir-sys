"""
Advanced Sales Dialog with Carton-based Selling - New Clean Version
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDoubleSpinBox, QComboBox, QDateTimeEdit, QMessageBox, QGroupBox,
    QGridLayout, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, QDateTime, Signal, QTimer, QSize
from PySide6.QtGui import QFont
from datetime import datetime
import logging

from egg_farm_system.utils.egg_management import EggManagementSystem
from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.farms import FarmManager

logger = logging.getLogger(__name__)


class AdvancedSalesDialogNew(QDialog):
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
        self.setMinimumWidth(800)
        self.setMinimumHeight(700)
        self.resize(800, 900)
        self.setModal(True)
        
        self.init_ui()
        self.load_data()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Egg Sale - Carton Based")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ===== SALE INFORMATION GROUP =====
        basic_group = QGroupBox("Sale Information")
        basic_group.setMinimumHeight(120)
        basic_layout = QFormLayout()
        basic_layout.setSpacing(12)
        basic_layout.setContentsMargins(15, 15, 15, 15)
        
        # Date field
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumWidth(300)
        self.date_edit.setMinimumHeight(35)
        basic_layout.addRow("Date:", self.date_edit)
        
        # Party field
        self.party_combo = QComboBox()
        self.party_combo.setMinimumWidth(300)
        self.party_combo.setMinimumHeight(35)
        parties = self.party_manager.get_all_parties()
        for party in parties:
            self.party_combo.addItem(party.name, party.id)
        basic_layout.addRow("Customer:", self.party_combo)
        
        # Payment method field
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Credit"])
        self.payment_method_combo.setCurrentText("Cash")
        self.payment_method_combo.setMinimumWidth(300)
        self.payment_method_combo.setMinimumHeight(35)
        basic_layout.addRow("Payment Method:", self.payment_method_combo)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # ===== CARTON & GRADE GROUP =====
        carton_group = QGroupBox("Carton & Grade Details")
        carton_group.setMinimumHeight(140)
        carton_layout = QGridLayout()
        carton_layout.setSpacing(12)
        carton_layout.setContentsMargins(15, 15, 15, 15)
        
        # Carton quantity spinbox - ROW 0
        carton_label = QLabel("Number of Cartons:")
        carton_label.setMinimumWidth(150)
        carton_layout.addWidget(carton_label, 0, 0)
        
        self.carton_spin = QDoubleSpinBox()
        self.carton_spin.setMinimum(0.0)
        self.carton_spin.setMaximum(10000.0)
        self.carton_spin.setValue(0.0)
        self.carton_spin.setDecimals(2)
        self.carton_spin.setSingleStep(0.5)
        self.carton_spin.setSuffix(" cartons")
        self.carton_spin.setMinimumWidth(200)
        self.carton_spin.setMinimumHeight(35)
        self.carton_spin.setFocusPolicy(Qt.StrongFocus)
        carton_layout.addWidget(self.carton_spin, 0, 1)
        
        # Grade combo - ROW 0
        grade_label = QLabel("Egg Grade:")
        grade_label.setMinimumWidth(150)
        carton_layout.addWidget(grade_label, 0, 2)
        
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["Small", "Medium", "Large", "Broken", "Mixed"])
        self.grade_combo.setCurrentText("Medium")
        self.grade_combo.setMinimumWidth(200)
        self.grade_combo.setMinimumHeight(35)
        carton_layout.addWidget(self.grade_combo, 0, 3)
        
        # Display calculated eggs - ROW 1
        eggs_display_label = QLabel("Total Eggs:")
        eggs_display_label.setMinimumWidth(150)
        carton_layout.addWidget(eggs_display_label, 1, 0)
        
        self.eggs_label = QLabel("0 eggs")
        eggs_font = QFont()
        eggs_font.setBold(True)
        eggs_font.setPointSize(11)
        self.eggs_label.setFont(eggs_font)
        self.eggs_label.setMinimumWidth(200)
        self.eggs_label.setMinimumHeight(35)
        carton_layout.addWidget(self.eggs_label, 1, 1)
        
        # Display trays - ROW 1
        trays_label = QLabel("Total Trays:")
        trays_label.setMinimumWidth(150)
        carton_layout.addWidget(trays_label, 1, 2)
        
        self.tray_label = QLabel("0 trays")
        tray_font = QFont()
        tray_font.setBold(True)
        self.tray_label.setFont(tray_font)
        self.tray_label.setMinimumWidth(200)
        self.tray_label.setMinimumHeight(35)
        carton_layout.addWidget(self.tray_label, 1, 3)
        
        carton_group.setLayout(carton_layout)
        layout.addWidget(carton_group)
        
        # ===== PRICING GROUP =====
        pricing_group = QGroupBox("Pricing")
        pricing_group.setMinimumHeight(120)
        pricing_layout = QFormLayout()
        pricing_layout.setSpacing(12)
        pricing_layout.setContentsMargins(15, 15, 15, 15)
        
        # Rate per egg AFG
        self.rate_per_egg_afg = QDoubleSpinBox()
        self.rate_per_egg_afg.setMinimum(0.0)
        self.rate_per_egg_afg.setMaximum(1000.0)
        self.rate_per_egg_afg.setValue(0.0)
        self.rate_per_egg_afg.setDecimals(2)
        self.rate_per_egg_afg.setSingleStep(1.0)
        self.rate_per_egg_afg.setSuffix(" AFG/egg")
        self.rate_per_egg_afg.setMinimumWidth(300)
        self.rate_per_egg_afg.setMinimumHeight(35)
        self.rate_per_egg_afg.setFocusPolicy(Qt.StrongFocus)
        pricing_layout.addRow("Rate per Egg (AFG):", self.rate_per_egg_afg)
        
        # Rate per egg USD
        self.rate_per_egg_usd = QDoubleSpinBox()
        self.rate_per_egg_usd.setMinimum(0.0)
        self.rate_per_egg_usd.setMaximum(100.0)
        self.rate_per_egg_usd.setValue(0.0)
        self.rate_per_egg_usd.setDecimals(2)
        self.rate_per_egg_usd.setSingleStep(0.1)
        self.rate_per_egg_usd.setSuffix(" USD/egg")
        self.rate_per_egg_usd.setMinimumWidth(300)
        self.rate_per_egg_usd.setMinimumHeight(35)
        self.rate_per_egg_usd.setFocusPolicy(Qt.StrongFocus)
        pricing_layout.addRow("Rate per Egg (USD):", self.rate_per_egg_usd)
        
        pricing_group.setLayout(pricing_layout)
        layout.addWidget(pricing_group)
        
        # ===== EXPENSES GROUP =====
        expense_group = QGroupBox("Expenses (Auto-calculated)")
        expense_group.setMinimumHeight(130)
        expense_layout = QFormLayout()
        expense_layout.setSpacing(12)
        expense_layout.setContentsMargins(15, 15, 15, 15)
        
        self.tray_expense_label = QLabel("0.00 AFG")
        tray_exp_font = QFont()
        tray_exp_font.setBold(True)
        self.tray_expense_label.setFont(tray_exp_font)
        self.tray_expense_label.setMinimumHeight(35)
        expense_layout.addRow("Tray Expense:", self.tray_expense_label)
        
        self.carton_expense_label = QLabel("0.00 AFG")
        carton_exp_font = QFont()
        carton_exp_font.setBold(True)
        self.carton_expense_label.setFont(carton_exp_font)
        self.carton_expense_label.setMinimumHeight(35)
        expense_layout.addRow("Carton Expense:", self.carton_expense_label)
        
        self.total_expense_label = QLabel("0.00 AFG")
        total_exp_font = QFont()
        total_exp_font.setBold(True)
        total_exp_font.setPointSize(11)
        self.total_expense_label.setFont(total_exp_font)
        self.total_expense_label.setMinimumHeight(35)
        expense_layout.addRow("Total Expense:", self.total_expense_label)
        
        expense_group.setLayout(expense_layout)
        layout.addWidget(expense_group)
        
        # ===== COST SUMMARY GROUP =====
        summary_group = QGroupBox("Cost Summary")
        summary_group.setMinimumHeight(160)
        summary_layout = QFormLayout()
        summary_layout.setSpacing(12)
        summary_layout.setContentsMargins(15, 15, 15, 15)
        
        self.egg_cost_label = QLabel("0.00 AFG")
        egg_cost_font = QFont()
        egg_cost_font.setBold(True)
        self.egg_cost_label.setFont(egg_cost_font)
        self.egg_cost_label.setMinimumHeight(35)
        summary_layout.addRow("Egg Cost:", self.egg_cost_label)
        
        self.total_cost_label = QLabel("0.00 AFG")
        total_cost_font = QFont()
        total_cost_font.setBold(True)
        total_cost_font.setPointSize(11)
        self.total_cost_label.setFont(total_cost_font)
        self.total_cost_label.setMinimumHeight(35)
        summary_layout.addRow("Total Cost:", self.total_cost_label)
        
        self.selling_price_label = QLabel("0.00 AFG")
        selling_font = QFont()
        selling_font.setBold(True)
        selling_font.setPointSize(11)
        self.selling_price_label.setFont(selling_font)
        self.selling_price_label.setStyleSheet("color: green;")
        self.selling_price_label.setMinimumHeight(35)
        summary_layout.addRow("Selling Price:", self.selling_price_label)
        
        self.profit_label = QLabel("0.00 AFG")
        profit_font = QFont()
        profit_font.setBold(True)
        profit_font.setPointSize(11)
        self.profit_label.setFont(profit_font)
        self.profit_label.setMinimumHeight(35)
        summary_layout.addRow("Profit:", self.profit_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # ===== NOTES =====
        notes_label = QLabel("Notes:")
        notes_font = QFont()
        notes_font.setBold(True)
        notes_label.setFont(notes_font)
        layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setMinimumHeight(60)
        self.notes_edit.setMinimumWidth(300)
        layout.addWidget(self.notes_edit)
        
        layout.addStretch()
        
        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)
        
        # ===== BUTTONS =====
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save Sale")
        self.save_btn.setMinimumWidth(150)
        self.save_btn.setMinimumHeight(45)
        self.save_btn.clicked.connect(self.save_sale)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(150)
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def setup_connections(self):
        """Setup signal connections for auto-calculations"""
        self.carton_spin.valueChanged.connect(self.update_calculations)
        self.rate_per_egg_afg.valueChanged.connect(self.update_calculations)
        self.rate_per_egg_usd.valueChanged.connect(self.update_calculations)
        self.grade_combo.currentTextChanged.connect(self.update_calculations)
    
    def load_data(self):
        """Load existing sale data if editing"""
        if self.sale:
            try:
                self.date_edit.setDateTime(QDateTime.fromString(
                    self.sale.date.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss"
                ))
                
                # Find and set party
                for i in range(self.party_combo.count()):
                    if self.party_combo.itemData(i) == self.sale.party_id:
                        self.party_combo.setCurrentIndex(i)
                        break
                
                # Set payment method
                if hasattr(self.sale, 'payment_method') and self.sale.payment_method:
                    index = self.payment_method_combo.findText(self.sale.payment_method)
                    if index >= 0:
                        self.payment_method_combo.setCurrentIndex(index)
                
                # Load carton data
                if self.sale.cartons:
                    self.carton_spin.setValue(self.sale.cartons)
                else:
                    cartons = self.egg_manager.eggs_to_cartons(self.sale.quantity)
                    self.carton_spin.setValue(cartons)
                
                # Set grade
                if self.sale.egg_grade:
                    index = self.grade_combo.findText(self.sale.egg_grade.capitalize())
                    if index >= 0:
                        self.grade_combo.setCurrentIndex(index)
                
                # Set rates
                self.rate_per_egg_afg.setValue(self.sale.rate_afg)
                self.rate_per_egg_usd.setValue(self.sale.rate_usd)
                
                # Load notes
                if self.sale.notes:
                    self.notes_edit.setPlainText(self.sale.notes)
            except Exception as e:
                logger.error(f"Error loading sale data: {e}")
        
        # Initial calculation
        self.update_calculations()
    
    def update_calculations(self):
        """Update all calculations"""
        try:
            cartons = self.carton_spin.value()
            eggs = self.egg_manager.cartons_to_eggs(cartons)
            trays = self.egg_manager.eggs_to_trays(eggs)
            
            # Update display
            self.eggs_label.setText(f"{eggs:,} eggs")
            self.tray_label.setText(f"{trays:.2f} trays")
            
            # Get expenses
            tray_expense_per_tray = self.egg_manager.get_tray_expense()
            carton_expense_per_carton = self.egg_manager.get_carton_expense()
            
            # Calculate expenses
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
            selling_price = eggs * rate_per_egg
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
            
            # Record sale
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



class AdvancedSalesDialogNew(QDialog):
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
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.setModal(False)  # Non-modal to allow interaction testing
        
        self.init_ui()
        self.load_data()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Egg Sale - Carton Based")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # ===== SALE INFORMATION GROUP =====
        basic_group = QGroupBox("Sale Information")
        basic_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(12)
        basic_layout.setContentsMargins(15, 15, 15, 15)
        
        # Date field
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumWidth(250)
        self.date_edit.setEnabled(True)
        basic_layout.addRow("Date:", self.date_edit)
        
        # Party field
        self.party_combo = QComboBox()
        self.party_combo.setMinimumWidth(250)
        self.party_combo.setEnabled(True)
        parties = self.party_manager.get_all_parties()
        for party in parties:
            self.party_combo.addItem(party.name, party.id)
        basic_layout.addRow("Customer:", self.party_combo)
        
        # Payment method field
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Credit"])
        self.payment_method_combo.setCurrentText("Cash")
        self.payment_method_combo.setMinimumWidth(250)
        self.payment_method_combo.setEnabled(True)
        basic_layout.addRow("Payment Method:", self.payment_method_combo)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # ===== CARTON & GRADE GROUP =====
        carton_group = QGroupBox("Carton & Grade Details")
        carton_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        carton_layout = QGridLayout()
        carton_layout.setSpacing(12)
        carton_layout.setContentsMargins(15, 15, 15, 15)
        
        # Carton quantity spinbox
        carton_label = QLabel("Number of Cartons:")
        carton_label.setMinimumWidth(120)
        carton_layout.addWidget(carton_label, 0, 0)
        
        self.carton_spin = QDoubleSpinBox()
        self.carton_spin.setMinimum(0.0)
        self.carton_spin.setMaximum(10000.0)
        self.carton_spin.setValue(0.0)
        self.carton_spin.setDecimals(2)
        self.carton_spin.setSingleStep(0.5)
        self.carton_spin.setSuffix(" cartons")
        self.carton_spin.setMinimumWidth(200)
        self.carton_spin.setEnabled(True)
        carton_layout.addWidget(self.carton_spin, 0, 1)
        
        # Grade combo
        grade_label = QLabel("Egg Grade:")
        grade_label.setMinimumWidth(120)
        carton_layout.addWidget(grade_label, 0, 2)
        
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["Small", "Medium", "Large", "Broken", "Mixed"])
        self.grade_combo.setCurrentText("Medium")
        self.grade_combo.setMinimumWidth(150)
        self.grade_combo.setEnabled(True)
        carton_layout.addWidget(self.grade_combo, 0, 3)
        
        # Display calculated eggs
        eggs_display_label = QLabel("Total Eggs:")
        eggs_display_label.setMinimumWidth(120)
        carton_layout.addWidget(eggs_display_label, 1, 0)
        
        self.eggs_label = QLabel("0 eggs")
        eggs_font = QFont()
        eggs_font.setBold(True)
        eggs_font.setPointSize(11)
        self.eggs_label.setFont(eggs_font)
        self.eggs_label.setMinimumWidth(200)
        carton_layout.addWidget(self.eggs_label, 1, 1)
        
        # Display trays
        trays_label = QLabel("Total Trays:")
        trays_label.setMinimumWidth(120)
        carton_layout.addWidget(trays_label, 1, 2)
        
        self.tray_label = QLabel("0 trays")
        tray_font = QFont()
        tray_font.setBold(True)
        self.tray_label.setFont(tray_font)
        self.tray_label.setMinimumWidth(150)
        carton_layout.addWidget(self.tray_label, 1, 3)
        
        carton_group.setLayout(carton_layout)
        layout.addWidget(carton_group)
        
        # ===== PRICING GROUP =====
        pricing_group = QGroupBox("Pricing")
        pricing_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        pricing_layout = QFormLayout()
        pricing_layout.setSpacing(12)
        pricing_layout.setContentsMargins(15, 15, 15, 15)
        
        # Rate per egg AFG
        self.rate_per_egg_afg = QDoubleSpinBox()
        self.rate_per_egg_afg.setMinimum(0.0)
        self.rate_per_egg_afg.setMaximum(1000.0)
        self.rate_per_egg_afg.setValue(0.0)
        self.rate_per_egg_afg.setDecimals(2)
        self.rate_per_egg_afg.setSingleStep(1.0)
        self.rate_per_egg_afg.setSuffix(" AFG/egg")
        self.rate_per_egg_afg.setMinimumWidth(250)
        self.rate_per_egg_afg.setEnabled(True)
        pricing_layout.addRow("Rate per Egg (AFG):", self.rate_per_egg_afg)
        
        # Rate per egg USD
        self.rate_per_egg_usd = QDoubleSpinBox()
        self.rate_per_egg_usd.setMinimum(0.0)
        self.rate_per_egg_usd.setMaximum(100.0)
        self.rate_per_egg_usd.setValue(0.0)
        self.rate_per_egg_usd.setDecimals(2)
        self.rate_per_egg_usd.setSingleStep(0.1)
        self.rate_per_egg_usd.setSuffix(" USD/egg")
        self.rate_per_egg_usd.setMinimumWidth(250)
        self.rate_per_egg_usd.setEnabled(True)
        pricing_layout.addRow("Rate per Egg (USD):", self.rate_per_egg_usd)
        
        pricing_group.setLayout(pricing_layout)
        layout.addWidget(pricing_group)
        
        # ===== EXPENSES GROUP =====
        expense_group = QGroupBox("Expenses (Auto-calculated)")
        expense_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        expense_layout = QFormLayout()
        expense_layout.setSpacing(12)
        expense_layout.setContentsMargins(15, 15, 15, 15)
        
        self.tray_expense_label = QLabel("0.00 AFG")
        tray_exp_font = QFont()
        tray_exp_font.setBold(True)
        self.tray_expense_label.setFont(tray_exp_font)
        expense_layout.addRow("Tray Expense:", self.tray_expense_label)
        
        self.carton_expense_label = QLabel("0.00 AFG")
        carton_exp_font = QFont()
        carton_exp_font.setBold(True)
        self.carton_expense_label.setFont(carton_exp_font)
        expense_layout.addRow("Carton Expense:", self.carton_expense_label)
        
        self.total_expense_label = QLabel("0.00 AFG")
        total_exp_font = QFont()
        total_exp_font.setBold(True)
        total_exp_font.setPointSize(11)
        self.total_expense_label.setFont(total_exp_font)
        expense_layout.addRow("Total Expense:", self.total_expense_label)
        
        expense_group.setLayout(expense_layout)
        layout.addWidget(expense_group)
        
        # ===== COST SUMMARY GROUP =====
        summary_group = QGroupBox("Cost Summary")
        summary_group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }")
        summary_layout = QFormLayout()
        summary_layout.setSpacing(12)
        summary_layout.setContentsMargins(15, 15, 15, 15)
        
        self.egg_cost_label = QLabel("0.00 AFG")
        egg_cost_font = QFont()
        egg_cost_font.setBold(True)
        self.egg_cost_label.setFont(egg_cost_font)
        summary_layout.addRow("Egg Cost:", self.egg_cost_label)
        
        self.total_cost_label = QLabel("0.00 AFG")
        total_cost_font = QFont()
        total_cost_font.setBold(True)
        total_cost_font.setPointSize(11)
        self.total_cost_label.setFont(total_cost_font)
        summary_layout.addRow("Total Cost:", self.total_cost_label)
        
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
        
        # ===== NOTES =====
        notes_label = QLabel("Notes:")
        notes_font = QFont()
        notes_font.setBold(True)
        notes_label.setFont(notes_font)
        layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setMinimumHeight(50)
        self.notes_edit.setEnabled(True)
        layout.addWidget(self.notes_edit)
        
        # ===== BUTTONS =====
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Save Sale")
        self.save_btn.setMinimumWidth(130)
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setEnabled(True)
        self.save_btn.clicked.connect(self.save_sale)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(130)
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def setup_connections(self):
        """Setup signal connections for auto-calculations"""
        self.carton_spin.valueChanged.connect(self.update_calculations)
        self.rate_per_egg_afg.valueChanged.connect(self.update_calculations)
        self.rate_per_egg_usd.valueChanged.connect(self.update_calculations)
        self.grade_combo.currentTextChanged.connect(self.update_calculations)
    
    def load_data(self):
        """Load existing sale data if editing"""
        if self.sale:
            try:
                self.date_edit.setDateTime(QDateTime.fromString(
                    self.sale.date.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss"
                ))
                
                # Find and set party
                for i in range(self.party_combo.count()):
                    if self.party_combo.itemData(i) == self.sale.party_id:
                        self.party_combo.setCurrentIndex(i)
                        break
                
                # Set payment method
                if hasattr(self.sale, 'payment_method') and self.sale.payment_method:
                    index = self.payment_method_combo.findText(self.sale.payment_method)
                    if index >= 0:
                        self.payment_method_combo.setCurrentIndex(index)
                
                # Load carton data
                if self.sale.cartons:
                    self.carton_spin.setValue(self.sale.cartons)
                else:
                    cartons = self.egg_manager.eggs_to_cartons(self.sale.quantity)
                    self.carton_spin.setValue(cartons)
                
                # Set grade
                if self.sale.egg_grade:
                    index = self.grade_combo.findText(self.sale.egg_grade.capitalize())
                    if index >= 0:
                        self.grade_combo.setCurrentIndex(index)
                
                # Set rates
                self.rate_per_egg_afg.setValue(self.sale.rate_afg)
                self.rate_per_egg_usd.setValue(self.sale.rate_usd)
                
                # Load notes
                if self.sale.notes:
                    self.notes_edit.setPlainText(self.sale.notes)
            except Exception as e:
                logger.error(f"Error loading sale data: {e}")
        
        # Initial calculation
        self.update_calculations()
    
    def update_calculations(self):
        """Update all calculations"""
        try:
            cartons = self.carton_spin.value()
            eggs = self.egg_manager.cartons_to_eggs(cartons)
            trays = self.egg_manager.eggs_to_trays(eggs)
            
            # Update display
            self.eggs_label.setText(f"{eggs:,} eggs")
            self.tray_label.setText(f"{trays:.2f} trays")
            
            # Get expenses
            tray_expense_per_tray = self.egg_manager.get_tray_expense()
            carton_expense_per_carton = self.egg_manager.get_carton_expense()
            
            # Calculate expenses
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
            selling_price = eggs * rate_per_egg
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
            
            # Record sale
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
