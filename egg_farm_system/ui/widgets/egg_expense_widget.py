"""
Egg Expense Management Widget
Allows setting tray and carton expenses
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDoubleSpinBox, QMessageBox, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging

from egg_farm_system.utils.egg_management import EggManagementSystem

logger = logging.getLogger(__name__)


class EggExpenseWidget(QWidget):
    """Widget for managing egg expenses (tray and carton)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.egg_manager = EggManagementSystem()
        self.init_ui()
        self.load_current_expenses()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel("Egg Expense Management")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Info label
        info_label = QLabel(
            "Set the expenses for trays and cartons used in egg packaging.\n"
            "These expenses will be automatically calculated when selling eggs by carton."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 8px;")
        layout.addWidget(info_label)
        
        # Expense Settings Group
        expense_group = QGroupBox("Expense Settings")
        expense_layout = QFormLayout()
        expense_layout.setSpacing(12)
        expense_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        expense_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Tray expense
        self.tray_expense_spin = QDoubleSpinBox()
        self.tray_expense_spin.setMinimum(0)
        self.tray_expense_spin.setMaximum(10000)
        self.tray_expense_spin.setDecimals(2)
        self.tray_expense_spin.setSuffix(" AFG per tray")
        self.tray_expense_spin.setSingleStep(1.0)
        self.tray_expense_spin.setMinimumWidth(300)
        self.tray_expense_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        expense_layout.addRow("Tray Expense:", self.tray_expense_spin)
        
        # Carton expense
        self.carton_expense_spin = QDoubleSpinBox()
        self.carton_expense_spin.setMinimum(0)
        self.carton_expense_spin.setMaximum(10000)
        self.carton_expense_spin.setDecimals(2)
        self.carton_expense_spin.setSuffix(" AFG per carton")
        self.carton_expense_spin.setSingleStep(1.0)
        self.carton_expense_spin.setMinimumWidth(300)
        self.carton_expense_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        expense_layout.addRow("Carton Expense:", self.carton_expense_spin)
        
        expense_group.setLayout(expense_layout)
        layout.addWidget(expense_group)
        
        # Conversion Info Group
        info_group = QGroupBox("Conversion Information")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        conversion_info = QLabel(
            f"<b>Egg Conversion:</b><br>"
            f"• 30 eggs = 1 tray<br>"
            f"• 180 eggs = 1 carton (6 trays)<br>"
            f"• 1 carton uses 7 trays for packaging<br><br>"
            f"<b>Expense Calculation:</b><br>"
            f"• Tray expense = (Cartons × 7) × Tray Expense<br>"
            f"• Carton expense = Cartons × Carton Expense<br>"
            f"• Total expense = Tray expense + Carton expense"
        )
        conversion_info.setWordWrap(True)
        conversion_info.setStyleSheet("padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
        info_layout.addWidget(conversion_info)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Example Calculation Group
        example_group = QGroupBox("Example Calculation")
        example_layout = QVBoxLayout()
        
        self.example_label = QLabel()
        self.example_label.setWordWrap(True)
        self.example_label.setStyleSheet("padding: 8px; background-color: #e8f4f8; border-radius: 4px;")
        example_layout.addWidget(self.example_label)
        
        example_group.setLayout(example_layout)
        layout.addWidget(example_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("Save Expenses")
        self.save_btn.setMinimumWidth(150)
        self.save_btn.clicked.connect(self.save_expenses)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setMinimumWidth(100)
        self.reset_btn.clicked.connect(self.load_current_expenses)
        
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Connect signals to update example
        self.tray_expense_spin.valueChanged.connect(self.update_example)
        self.carton_expense_spin.valueChanged.connect(self.update_example)
    
    def load_current_expenses(self):
        """Load current expense settings"""
        try:
            tray_expense = self.egg_manager.get_tray_expense()
            carton_expense = self.egg_manager.get_carton_expense()
            
            self.tray_expense_spin.setValue(tray_expense)
            self.carton_expense_spin.setValue(carton_expense)
            
            self.update_example()
        except Exception as e:
            logger.error(f"Error loading expenses: {e}")
    
    def update_example(self):
        """Update example calculation"""
        try:
            tray_expense = self.tray_expense_spin.value()
            carton_expense = self.carton_expense_spin.value()
            cartons = 10  # Example: 10 cartons
            
            trays_needed = cartons * EggManagementSystem.TRAYS_EXPENSE_PER_CARTON
            tray_expense_total = trays_needed * tray_expense
            carton_expense_total = cartons * carton_expense
            total_expense = tray_expense_total + carton_expense_total
            
            eggs = EggManagementSystem.cartons_to_eggs(cartons)
            
            example_text = (
                f"<b>Example for {cartons} cartons ({eggs:,} eggs):</b><br>"
                f"• Tray expense: {trays_needed} trays × {tray_expense:.2f} AFG = {tray_expense_total:,.2f} AFG<br>"
                f"• Carton expense: {cartons} cartons × {carton_expense:.2f} AFG = {carton_expense_total:,.2f} AFG<br>"
                f"• <b>Total expense: {total_expense:,.2f} AFG</b><br>"
                f"• Expense per carton: {total_expense / cartons:,.2f} AFG"
            )
            
            self.example_label.setText(example_text)
        except Exception as e:
            logger.error(f"Error updating example: {e}")
    
    def save_expenses(self):
        """Save expense settings"""
        try:
            tray_expense = self.tray_expense_spin.value()
            carton_expense = self.carton_expense_spin.value()
            
            self.egg_manager.set_tray_expense(tray_expense)
            self.egg_manager.set_carton_expense(carton_expense)
            
            QMessageBox.information(
                self,
                "Success",
                f"Expenses saved successfully!\n\n"
                f"Tray Expense: {tray_expense:.2f} AFG\n"
                f"Carton Expense: {carton_expense:.2f} AFG"
            )
        except Exception as e:
            logger.error(f"Error saving expenses: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save expenses: {str(e)}")

