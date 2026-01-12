import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDoubleSpinBox, QComboBox, QDateTimeEdit, QMessageBox, QTextEdit, QSizePolicy,
    QGroupBox, QWidget
)
from PySide6.QtCore import Qt, QDateTime, Signal
from PySide6.QtGui import QFont
from datetime import datetime

from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.feed_mill import RawMaterialManager # This manager handles raw materials
from egg_farm_system.modules.sales import RawMaterialSaleManager
from egg_farm_system.utils.currency import CurrencyConverter
from egg_farm_system.utils.performance_monitoring import measure_time

logger = logging.getLogger(__name__)

class RawMaterialSaleDialog(QDialog):
    """Dialog for selling raw materials"""
    
    sale_saved = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sell Raw Material")
        self.setMinimumSize(600, 700)
        self.setModal(True)
        
        self.converter = CurrencyConverter()
        self.exchange_rate = self.converter.get_exchange_rate()
        
        self.init_ui()
        self.load_data()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize UI elements"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Sell Raw Material")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # --- Sale Details Group ---
        sale_details_group = QGroupBox("Sale Details")
        sale_details_layout = QFormLayout()
        sale_details_layout.setSpacing(10)
        sale_details_layout.setLabelAlignment(Qt.AlignRight)
        
        # Date
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumWidth(200)
        sale_details_layout.addRow("Date:", self.date_edit)
        
        # Party (Customer)
        self.party_combo = QComboBox()
        self.party_combo.setMinimumWidth(200)
        sale_details_layout.addRow("Customer:", self.party_combo)
        
        # Payment Method
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Credit"])
        self.payment_method_combo.setCurrentText("Cash")
        self.payment_method_combo.setMinimumWidth(200)
        sale_details_layout.addRow("Payment Method:", self.payment_method_combo)
        
        sale_details_group.setLayout(sale_details_layout)
        main_layout.addWidget(sale_details_group)

        # --- Raw Material Details Group ---
        material_details_group = QGroupBox("Raw Material Details")
        material_details_layout = QFormLayout()
        material_details_layout.setSpacing(10)
        material_details_layout.setLabelAlignment(Qt.AlignRight)
        
        # Raw Material
        self.raw_material_combo = QComboBox()
        self.raw_material_combo.setMinimumWidth(200)
        material_details_layout.addRow("Raw Material:", self.raw_material_combo)
        
        # Current Stock Display with better styling
        stock_layout = QHBoxLayout()
        self.current_stock_label = QLabel("Available: 0.00 units")
        self.current_stock_label.setFont(QFont("Arial", 10))
        self.current_stock_label.setProperty("state", "info")
        
        self.avg_price_label = QLabel("Avg Price: N/A")
        self.avg_price_label.setFont(QFont("Arial", 9))
        self.avg_price_label.setStyleSheet("color: #7f8c8d;") # Keep generic grey or use theme class if available
        
        stock_layout.addWidget(self.current_stock_label)
        stock_layout.addStretch()
        stock_layout.addWidget(self.avg_price_label)
        stock_widget = QWidget()
        stock_widget.setLayout(stock_layout)
        material_details_layout.addRow("Stock Info:", stock_widget)
        
        # Quantity
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMinimum(0.01)
        self.quantity_spin.setMaximum(100000.00)
        self.quantity_spin.setDecimals(2)
        self.quantity_spin.setSingleStep(0.1)
        self.quantity_spin.setSuffix(" units")
        self.quantity_spin.setMinimumWidth(200)
        material_details_layout.addRow("Quantity:", self.quantity_spin)
        
        # Rate AFG
        self.rate_afg_spin = QDoubleSpinBox()
        self.rate_afg_spin.setMinimum(0.00) 
        self.rate_afg_spin.setMaximum(100000.00)
        self.rate_afg_spin.setDecimals(2)
        self.rate_afg_spin.setSingleStep(0.1)
        self.rate_afg_spin.setSuffix(" AFG/unit")
        self.rate_afg_spin.setMinimumWidth(200)
        material_details_layout.addRow("Rate (AFG):", self.rate_afg_spin)
        
        # Rate USD
        self.rate_usd_spin = QDoubleSpinBox()
        self.rate_usd_spin.setMinimum(0.00)
        self.rate_usd_spin.setMaximum(10000.00)
        self.rate_usd_spin.setDecimals(2)
        self.rate_usd_spin.setSingleStep(0.01)
        self.rate_usd_spin.setSuffix(" USD/unit")
        self.rate_usd_spin.setMinimumWidth(200)
        material_details_layout.addRow("Rate (USD):", self.rate_usd_spin)
        
        material_details_group.setLayout(material_details_layout)
        main_layout.addWidget(material_details_group)
        
        # --- Total Calculation Group ---
        total_group = QGroupBox("Sale Total")
        total_layout = QFormLayout()
        total_layout.setSpacing(10)
        total_layout.setLabelAlignment(Qt.AlignRight)
        
        # Total AFG
        self.total_afg_label = QLabel("0.00 AFG")
        self.total_afg_label.setObjectName("totalLabel")
        total_layout.addRow("Total (AFG):", self.total_afg_label)
        
        # Total USD
        self.total_usd_label = QLabel("0.00 USD")
        self.total_usd_label.setObjectName("totalLabel")
        total_layout.addRow("Total (USD):", self.total_usd_label)
        
        total_group.setLayout(total_layout)
        main_layout.addWidget(total_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add any notes for the sale...")
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group)
        
        main_layout.addStretch() # Push everything upwards
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumSize(120, 40)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save Sale")
        self.save_btn.setMinimumSize(120, 40)
        self.save_btn.setProperty("class", "success")
        self.save_btn.clicked.connect(self.save_sale)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def load_data(self):
        """Load data into combos"""
        # Load Parties
        with PartyManager() as pm:
            parties = pm.get_all_parties()
            for party in parties:
                self.party_combo.addItem(party.name, party.id)
            
        # Load Raw Materials
        with RawMaterialManager() as rmm:
            raw_materials = rmm.get_all_materials() # Corrected method name
            for material in raw_materials:
                self.raw_material_combo.addItem(f"{material.name} ({material.unit})", material.id)
        
        self.update_stock_display()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.raw_material_combo.currentIndexChanged.connect(self.update_stock_display)
        self.quantity_spin.valueChanged.connect(self.update_totals)
        self.rate_afg_spin.valueChanged.connect(self.on_rate_afg_changed)
        self.rate_usd_spin.valueChanged.connect(self.on_rate_usd_changed)
        self.quantity_spin.valueChanged.connect(self.validate_stock)
    
    def update_stock_display(self):
        """Update the displayed stock for the selected raw material"""
        material_id = self.raw_material_combo.currentData()
        if material_id:
            with RawMaterialManager() as rmm:
                material = rmm.get_material_by_id(material_id)
                if material:
                    stock_text = f"Available: {material.current_stock:.2f} {material.unit}"
                    # Color code based on stock level
                    state = "success"
                    if material.current_stock <= 0:
                        state = "error"
                        stock_text += " ⚠️ OUT OF STOCK"
                    elif material.current_stock <= material.low_stock_alert:
                        state = "warning"
                        stock_text += " ⚠️ LOW STOCK"
                    
                    self.current_stock_label.setText(stock_text)
                    self.current_stock_label.setProperty("state", state)
                    self.current_stock_label.style().unpolish(self.current_stock_label)
                    self.current_stock_label.style().polish(self.current_stock_label)
                    
                    # Show average price
                    if material.total_quantity_purchased > 0:
                        avg_price_text = f"Avg Price: {material.cost_afg:,.2f} AFG ({material.cost_usd:,.2f} USD)"
                    else:
                        avg_price_text = "Avg Price: N/A (No purchases yet)"
                    self.avg_price_label.setText(avg_price_text)
                    
                    self.quantity_spin.setMaximum(material.current_stock) # Limit quantity to current stock
                    self.quantity_spin.setValue(min(self.quantity_spin.value(), material.current_stock))
                    self.update_totals()
                else:
                    self.current_stock_label.setText("Available: N/A")
                    self.current_stock_label.setProperty("state", "info")
                    self.current_stock_label.style().unpolish(self.current_stock_label)
                    self.current_stock_label.style().polish(self.current_stock_label)
                    self.avg_price_label.setText("Avg Price: N/A")
                    self.quantity_spin.setMaximum(0.0)
                    self.quantity_spin.setValue(0.0)
        else:
            self.current_stock_label.setText("Available: N/A")
            self.current_stock_label.setProperty("state", "info")
            self.current_stock_label.style().unpolish(self.current_stock_label)
            self.current_stock_label.style().polish(self.current_stock_label)
            self.avg_price_label.setText("Avg Price: N/A")
            self.quantity_spin.setMaximum(0.0)
            self.quantity_spin.setValue(0.0)
        self.update_totals()
    
    def on_rate_afg_changed(self):
        """Auto-calculate USD rate from AFG rate"""
        if self.rate_afg_spin.value() > 0 and self.exchange_rate > 0:
            # Temporarily block signals to avoid recursion
            self.rate_usd_spin.blockSignals(True)
            calculated_usd = self.rate_afg_spin.value() / self.exchange_rate
            self.rate_usd_spin.setValue(round(calculated_usd, 2))
            self.rate_usd_spin.blockSignals(False)
            self.update_totals()
    
    def on_rate_usd_changed(self):
        """Auto-calculate AFG rate from USD rate"""
        if self.rate_usd_spin.value() > 0 and self.exchange_rate > 0:
            # Temporarily block signals to avoid recursion
            self.rate_afg_spin.blockSignals(True)
            calculated_afg = self.rate_usd_spin.value() * self.exchange_rate
            self.rate_afg_spin.setValue(round(calculated_afg, 2))
            self.rate_afg_spin.blockSignals(False)
            self.update_totals()
    
    def update_totals(self):
        """Update total calculation display"""
        quantity = self.quantity_spin.value()
        rate_afg = self.rate_afg_spin.value()
        rate_usd = self.rate_usd_spin.value()
        
        total_afg = quantity * rate_afg
        total_usd = quantity * rate_usd
        
        self.total_afg_label.setText(f"{total_afg:,.2f} AFG")
        self.total_usd_label.setText(f"{total_usd:,.2f} USD")
    
    def validate_stock(self):
        """Validate if the quantity to sell is within available stock"""
        material_id = self.raw_material_combo.currentData()
        if material_id:
            with RawMaterialManager() as rmm:
                material = rmm.get_material_by_id(material_id)
                if material and self.quantity_spin.value() > material.current_stock:
                    QMessageBox.warning(self, "Insufficient Stock", 
                                        f"Cannot sell {self.quantity_spin.value():.2f} {material.unit} of {material.name}. Only {material.current_stock:.2f} {material.unit} available.")
                    self.quantity_spin.setValue(material.current_stock) # Reset to max available
                    self.update_totals()
    
    def save_sale(self):
        """Save the raw material sale"""
        try:
            # Validation
            party_id = self.party_combo.currentData()
            material_id = self.raw_material_combo.currentData()
            quantity = self.quantity_spin.value()
            rate_afg = self.rate_afg_spin.value()
            rate_usd = self.rate_usd_spin.value()
            payment_method = self.payment_method_combo.currentText()
            notes = self.notes_edit.toPlainText().strip()
            
            if not party_id:
                QMessageBox.warning(self, "Validation Error", "Please select a customer.")
                return
            if not material_id:
                QMessageBox.warning(self, "Validation Error", "Please select a raw material.")
                return
            if quantity <= 0:
                QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0.")
                return
            
            # Check if at least one rate is positive
            if rate_afg <= 0 and rate_usd <= 0:
                QMessageBox.warning(self, "Validation Error", "At least one rate (AFG or USD) must be greater than 0.")
                return
            
            # Additional stock validation (should already be handled by spinbox, but for safety)
            with RawMaterialManager() as rmm:
                material = rmm.get_material_by_id(material_id)
                if not material or quantity > material.current_stock:
                    QMessageBox.warning(self, "Insufficient Stock", 
                                        f"Cannot sell {quantity:.2f} {material.unit} of {material.name}. Only {material.current_stock:.2f} {material.unit} available.")
                    return
            
            # Use the exchange rate we already have
            exchange_rate = self.exchange_rate
            
            with RawMaterialSaleManager() as rmsm:
                rmsm.record_raw_material_sale(
                    party_id=party_id,
                    material_id=material_id,
                    quantity=quantity,
                    rate_afg=rate_afg,
                    rate_usd=rate_usd,
                    exchange_rate_used=exchange_rate,
                    date=self.date_edit.dateTime().toPython(),
                    payment_method=payment_method,
                    notes=notes if notes else None
                )
            
            QMessageBox.information(self, "Success", "Raw material sale recorded successfully!")
            self.sale_saved.emit()
            self.accept()
        
        except ValueError as ve:
            QMessageBox.warning(self, "Validation Error", str(ve))
        except Exception as e:
            logger.error(f"Error saving raw material sale: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save raw material sale: {str(e)}")
    
    def reject(self):
        """Close dialog"""
        super().reject()

    def accept(self):
        """Close dialog"""
        super().accept()
