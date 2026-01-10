"""
Advanced Sales Dialog with Carton-based Selling - New Clean Version
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDoubleSpinBox, QComboBox, QDateTimeEdit, QMessageBox, QGroupBox,
    QGridLayout, QTextEdit, QScrollArea, QWidget
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
        self.setMinimumSize(750, 650)
        self.setModal(True)
        
        self.init_ui()
        self.load_data()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Egg Sale - Carton Based")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50;")
        title_layout.addWidget(title)
        
        main_layout.addWidget(title_container)
        
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QWidget { background: transparent; }
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 24px;
                font-weight: bold;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 5px;
                background-color: white;
                color: #546e7a;
            }
            QLineEdit, QComboBox, QDoubleSpinBox, QDateTimeEdit {
                padding: 8px;
                border: 1px solid #cfd8dc;
                border-radius: 4px;
                background-color: #ffffff;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus {
                border: 1px solid #2196f3;
                background-color: #f5f9ff;
            }
        """)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(4, 4, 16, 4)  # Extra right margin for scrollbar
        
        # ===== SALE INFORMATION GROUP =====
        basic_group = QGroupBox("Sale Information")
        basic_layout = QGridLayout()
        basic_layout.setVerticalSpacing(16)
        basic_layout.setHorizontalSpacing(24)
        basic_layout.setContentsMargins(16, 16, 16, 16)
        
        # Date field
        basic_layout.addWidget(QLabel("Date:"), 0, 0)
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        basic_layout.addWidget(self.date_edit, 0, 1)
        
        # Party field
        basic_layout.addWidget(QLabel("Customer:"), 1, 0)
        self.party_combo = QComboBox()
        parties = self.party_manager.get_all_parties()
        for party in parties:
            self.party_combo.addItem(party.name, party.id)
        basic_layout.addWidget(self.party_combo, 1, 1)
        
        # Payment method field
        basic_layout.addWidget(QLabel("Payment Method:"), 2, 0)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Credit"])
        self.payment_method_combo.setCurrentText("Cash")
        basic_layout.addWidget(self.payment_method_combo, 2, 1)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # ===== CARTON & GRADE GROUP =====
        carton_group = QGroupBox("Carton & Grade Details")
        carton_layout = QGridLayout()
        carton_layout.setVerticalSpacing(16)
        carton_layout.setHorizontalSpacing(24)
        carton_layout.setContentsMargins(16, 16, 16, 16)
        
        # Carton quantity spinbox
        carton_layout.addWidget(QLabel("Number of Cartons:"), 0, 0)
        self.carton_spin = QDoubleSpinBox()
        self.carton_spin.setMinimum(0.0)
        self.carton_spin.setMaximum(10000.0)
        self.carton_spin.setValue(0.0)
        self.carton_spin.setDecimals(2)
        self.carton_spin.setSingleStep(0.5)
        self.carton_spin.setSuffix(" cartons")
        self.carton_spin.setFocusPolicy(Qt.StrongFocus)
        carton_layout.addWidget(self.carton_spin, 0, 1)
        
        # Grade combo
        carton_layout.addWidget(QLabel("Egg Grade:"), 0, 2)
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["Small", "Medium", "Large", "Broken", "Mixed"])
        self.grade_combo.setCurrentText("Medium")
        carton_layout.addWidget(self.grade_combo, 0, 3)
        
        # Display calculated eggs
        carton_layout.addWidget(QLabel("Total Eggs:"), 1, 0)
        self.eggs_label = QLabel("0 eggs")
        eggs_font = QFont()
        eggs_font.setBold(True)
        eggs_font.setPointSize(10)
        self.eggs_label.setFont(eggs_font)
        self.eggs_label.setStyleSheet("color: #455a64;")
        carton_layout.addWidget(self.eggs_label, 1, 1)
        
        # Display trays
        carton_layout.addWidget(QLabel("Total Trays:"), 1, 2)
        self.tray_label = QLabel("0 trays")
        tray_font = QFont()
        tray_font.setBold(True)
        self.tray_label.setFont(tray_font)
        self.tray_label.setStyleSheet("color: #455a64;")
        carton_layout.addWidget(self.tray_label, 1, 3)
        
        carton_group.setLayout(carton_layout)
        layout.addWidget(carton_group)
        
        # ===== PRICING GROUP =====
        pricing_group = QGroupBox("Pricing")
        pricing_layout = QGridLayout()
        pricing_layout.setVerticalSpacing(16)
        pricing_layout.setHorizontalSpacing(24)
        pricing_layout.setContentsMargins(16, 16, 16, 16)
        
        # Rate per egg AFG
        pricing_layout.addWidget(QLabel("Rate per Egg (AFG):"), 0, 0)
        self.rate_per_egg_afg = QDoubleSpinBox()
        self.rate_per_egg_afg.setMinimum(0.0)
        self.rate_per_egg_afg.setMaximum(1000.0)
        self.rate_per_egg_afg.setValue(0.0)
        self.rate_per_egg_afg.setDecimals(2)
        self.rate_per_egg_afg.setSingleStep(1.0)
        self.rate_per_egg_afg.setSuffix(" AFG/egg")
        self.rate_per_egg_afg.setFocusPolicy(Qt.StrongFocus)
        pricing_layout.addWidget(self.rate_per_egg_afg, 0, 1)
        
        # Rate per egg USD
        pricing_layout.addWidget(QLabel("Rate per Egg (USD):"), 1, 0)
        self.rate_per_egg_usd = QDoubleSpinBox()
        self.rate_per_egg_usd.setMinimum(0.0)
        self.rate_per_egg_usd.setMaximum(100.0)
        self.rate_per_egg_usd.setValue(0.0)
        self.rate_per_egg_usd.setDecimals(2)
        self.rate_per_egg_usd.setSingleStep(0.1)
        self.rate_per_egg_usd.setSuffix(" USD/egg")
        self.rate_per_egg_usd.setFocusPolicy(Qt.StrongFocus)
        pricing_layout.addWidget(self.rate_per_egg_usd, 1, 1)
        
        pricing_group.setLayout(pricing_layout)
        layout.addWidget(pricing_group)
        
        # ===== EXPENSES & SUMMARY ROW =====
        summary_row = QHBoxLayout()
        summary_row.setSpacing(20)
        
        # ===== EXPENSES GROUP =====
        expense_group = QGroupBox("Expenses (Auto-calculated)")
        expense_layout = QFormLayout()
        expense_layout.setSpacing(10)
        expense_layout.setContentsMargins(16, 16, 16, 16)
        
        self.tray_expense_label = QLabel("0.00 AFG")
        self.carton_expense_label = QLabel("0.00 AFG")
        self.total_expense_label = QLabel("0.00 AFG")
        self.total_expense_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        
        expense_layout.addRow("Tray Expense:", self.tray_expense_label)
        expense_layout.addRow("Carton Expense:", self.carton_expense_label)
        expense_layout.addRow("Total Expense:", self.total_expense_label)
        
        expense_group.setLayout(expense_layout)
        summary_row.addWidget(expense_group)
        
        # ===== COST SUMMARY GROUP =====
        summary_group = QGroupBox("Financial Summary")
        summary_layout = QFormLayout()
        summary_layout.setSpacing(10)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        
        self.egg_cost_label = QLabel("0.00 AFG")
        self.total_cost_label = QLabel("0.00 AFG")
        self.selling_price_label = QLabel("0.00 AFG")
        self.selling_price_label.setStyleSheet("font-weight: bold; color: #1976d2; font-size: 11pt;")
        
        self.profit_label = QLabel("0.00 AFG")
        self.profit_label.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 4px; border-radius: 4px;")
        
        summary_layout.addRow("Egg Cost:", self.egg_cost_label)
        summary_layout.addRow("Total Cost (w/ Exp):", self.total_cost_label)
        summary_layout.addRow("Total Sales:", self.selling_price_label)
        summary_layout.addRow("Net Profit:", self.profit_label)
        
        summary_group.setLayout(summary_layout)
        summary_row.addWidget(summary_group)
        
        layout.addLayout(summary_row)
        
        # ===== NOTES =====
        notes_group = QWidget()
        notes_layout = QVBoxLayout(notes_group)
        notes_layout.setContentsMargins(0, 0, 0, 0)
        notes_layout.setSpacing(8)
        
        notes_label = QLabel("Notes / Comments")
        notes_label.setStyleSheet("font-weight: bold; color: #546e7a;")
        notes_layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setMinimumHeight(60)
        self.notes_edit.setPlaceholderText("Add any additional notes here...")
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_group)
        layout.addStretch()
        
        content_widget.setLayout(layout)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)
        
        # ===== BUTTONS =====
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 16, 0, 0)
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.setMinimumHeight(38)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #cfd8dc;
                color: #546e7a;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #eceff1; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Sale")
        self.save_btn.setFixedWidth(160)
        self.save_btn.setMinimumHeight(38)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                border: none;
                color: white;
                border-radius: 4px;
                font-weight: 600;
                font-size: 10pt;
            }
            QPushButton:hover { background-color: #1e88e5; }
            QPushButton:pressed { background-color: #1976d2; }
        """)
        self.save_btn.clicked.connect(self.save_sale)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addWidget(button_container)
        
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
    
    def showEvent(self, event):
        """Ensure everything is enabled when shown"""
        super().showEvent(event)
        QTimer.singleShot(10, self.ensure_enabled_and_focused)

    def ensure_enabled_and_focused(self):
        """Force enable the dialog and set initial focus"""
        self.setEnabled(True)
        self.carton_spin.setEnabled(True)
        self.carton_spin.setReadOnly(False)
        self.party_combo.setEnabled(True)
        self.date_edit.setEnabled(True)
        self.date_edit.setReadOnly(False)
        
        # Set focus
        self.carton_spin.setFocus()

