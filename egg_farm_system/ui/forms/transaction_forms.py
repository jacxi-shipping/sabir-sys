"""
Form widgets for transactions (sales, purchases, expenses)
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDialog, QFormLayout, QDoubleSpinBox, QDateTimeEdit, QComboBox, QSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt, QDateTime, QSize, QTimer
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from egg_farm_system.ui.widgets.datatable import DataTableWidget
from egg_farm_system.ui.widgets.loading_overlay import LoadingOverlay
from egg_farm_system.ui.widgets.success_message import SuccessMessage
from egg_farm_system.ui.widgets.keyboard_shortcuts import KeyboardShortcuts
from egg_farm_system.utils.error_handler import ErrorHandler
from PySide6.QtWidgets import QToolButton

from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.modules.purchases import PurchaseManager
from egg_farm_system.modules.expenses import ExpenseManager, PaymentManager
from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.inventory import InventoryManager
from egg_farm_system.modules.feed_mill import RawMaterialManager
from egg_farm_system.database.models import RawMaterial, Sale, Purchase, Expense
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.config import EXPENSE_CATEGORIES
from egg_farm_system.ui.widgets.advanced_sales_dialog import AdvancedSalesDialog

class TransactionFormWidget(QWidget):
    """Transaction management widget (Sales, Purchases, Expenses)"""

    def __init__(self, transaction_type, farm_id=None):
        super().__init__()
        self.transaction_type = transaction_type
        self.farm_id = farm_id
        self.sales_manager = SalesManager()
        self.purchase_manager = PurchaseManager()
        self.expense_manager = ExpenseManager()
        self.party_manager = PartyManager()
        self.inventory_manager = InventoryManager()
        self.loading_overlay = LoadingOverlay(self)
        
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Title
        title_text = {
            'sales': 'Sales Management',
            'purchases': 'Purchase Management',
            'expenses': 'Expense Management'
        }.get(self.transaction_type, 'Transactions')
        
        # Header: title left, actions right
        header_hbox = QHBoxLayout()
        title = QLabel(title_text)
        title.setObjectName('titleLabel')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_hbox.addWidget(title)
        header_hbox.addStretch()
        new_btn = QPushButton(f"New {title_text.split()[0]}")
        new_btn.clicked.connect(self.add_transaction)
        new_btn.setToolTip(f"Add new {self.transaction_type} (Ctrl+N)")
        header_hbox.addWidget(new_btn)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.add_standard_shortcuts(self, {
            'new': self.add_transaction,
            'refresh': self.refresh_data
        })
        layout.addLayout(header_hbox)
        
        # Transactions table
        if self.transaction_type == 'sales':
            headers = ["Date", "Party", "Quantity", "Rate AFG", "Total AFG", "Actions"]
        elif self.transaction_type == 'purchases':
            headers = ["Date", "Party", "Material", "Quantity", "Total AFG", "Actions"]
        else:  # expenses
            headers = ["Date", "Category", "Amount AFG", "Party", "Actions"]
        
        self.table = DataTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.set_headers(headers)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh_data(self):
        """Refresh transaction data"""
        self.loading_overlay.set_message("Loading transactions...")
        self.loading_overlay.show()
        QTimer.singleShot(50, self._do_refresh_data)
    
    def _do_refresh_data(self):
        """Perform the actual refresh"""
        try:
            rows = []
            action_items = []

            if self.transaction_type == 'sales':
                transactions = self.sales_manager.get_sales()
                for row, trans in enumerate(transactions):
                    party = self.party_manager.get_party_by_id(trans.party_id)
                    # Show cartons if available, otherwise show quantity
                    qty_display = f"{trans.cartons:.2f} cartons" if trans.cartons else f"{trans.quantity} eggs"
                    rows.append([
                        trans.date.strftime("%Y-%m-%d"),
                        party.name if party else "",
                        qty_display,
                        f"{trans.rate_afg:.2f}",
                        f"{trans.total_afg:.2f}",
                        ""
                    ])
                    action_items.append((row, trans, 'sale'))

            elif self.transaction_type == 'purchases':
                transactions = self.purchase_manager.get_purchases()
                for row, trans in enumerate(transactions):
                    party = self.party_manager.get_party_by_id(trans.party_id)
                    session = DatabaseManager.get_session()
                    try:
                        material = session.query(RawMaterial).filter(RawMaterial.id == trans.material_id).first()
                    finally:
                        session.close()
                    rows.append([
                        trans.date.strftime("%Y-%m-%d"),
                        party.name if party else "",
                        material.name if material else "",
                        f"{trans.quantity:.2f}",
                        f"{trans.total_afg:.2f}",
                        ""
                    ])
                    action_items.append((row, trans, 'purchase'))

            else:  # expenses
                transactions = self.expense_manager.get_expenses(farm_id=self.farm_id)
                for row, trans in enumerate(transactions):
                    party = self.party_manager.get_party_by_id(trans.party_id) if trans.party_id else None
                    rows.append([
                        trans.date.strftime("%Y-%m-%d"),
                        trans.category,
                        f"{trans.amount_afg:.2f}",
                        party.name if party else "",
                        ""
                    ])
                    action_items.append((row, trans, 'expense'))

            # populate rows and attach action widgets
            if rows:
                self.table.set_rows(rows)

            # attach action widgets into last column
            asset_dir = Path(__file__).parent.parent.parent / 'assets'
            edit_icon = asset_dir / 'icon_edit.svg'
            delete_icon = asset_dir / 'icon_delete.svg'
            for row_idx, trans, ttype in action_items:
                edit_btn = QToolButton()
                edit_btn.setAutoRaise(True)
                edit_btn.setFixedSize(28, 28)
                if edit_icon.exists():
                    edit_btn.setIcon(QIcon(str(edit_icon)))
                    edit_btn.setIconSize(QSize(20, 20))
                edit_btn.setToolTip('Edit')
                if ttype == 'sale':
                    edit_btn.clicked.connect(lambda checked, t=trans: self.edit_sale(t))
                elif ttype == 'purchase':
                    edit_btn.clicked.connect(lambda checked, t=trans: self.edit_purchase(t))
                else:  # expense
                    edit_btn.clicked.connect(lambda checked, t=trans: self.edit_expense(t))

                delete_btn = QToolButton()
                delete_btn.setAutoRaise(True)
                delete_btn.setFixedSize(28, 28)
                if delete_icon.exists():
                    delete_btn.setIcon(QIcon(str(delete_icon)))
                    delete_btn.setIconSize(QSize(20, 20))
                delete_btn.setToolTip('Delete')
                delete_btn.clicked.connect(lambda checked, t=trans, tt=ttype: self.delete_transaction(t, tt))

                container = QWidget()
                container.setMinimumHeight(36)
                container.setMaximumHeight(36)
                l = QHBoxLayout(container)
                l.setContentsMargins(4, 2, 4, 2)
                l.setSpacing(4)
                l.addWidget(edit_btn)
                l.addWidget(delete_btn)
                l.addStretch()
                self.table.set_cell_widget(row_idx, self.table.model.columnCount()-1, container)
            
            self.loading_overlay.hide()
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, "Error", f"Failed to load transactions: {str(e)}")
    
    def create_action_buttons(self, transaction, trans_type):
        """Create action buttons for transaction"""
        action_layout = QHBoxLayout()
        asset_dir = Path(__file__).parent.parent.parent / 'assets'
        edit_icon = asset_dir / 'icon_edit.svg'
        delete_icon = asset_dir / 'icon_delete.svg'

        edit_btn = QToolButton()
        edit_btn.setAutoRaise(True)
        edit_btn.setFixedSize(28, 28)
        if edit_icon.exists():
            edit_btn.setIcon(QIcon(str(edit_icon)))
            edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setToolTip('Edit')
        edit_btn.clicked.connect(lambda checked=False, t=transaction, tt=trans_type: self.edit_transaction(t, tt) if hasattr(self, 'edit_transaction') else None)

        delete_btn = QToolButton()
        delete_btn.setAutoRaise(True)
        delete_btn.setFixedSize(28, 28)
        if delete_icon.exists():
            delete_btn.setIcon(QIcon(str(delete_icon)))
            delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setToolTip('Delete')
        delete_btn.clicked.connect(lambda checked=False, t=transaction, tt=trans_type: self.delete_transaction(t, tt))

        action_widget = QWidget()
        action_widget.setLayout(action_layout)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(6)
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(delete_btn)
        action_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        return action_widget
    
    def add_transaction(self):
        """Add new transaction"""
        if self.transaction_type == 'sales':
            # Use advanced sales dialog
            dialog = AdvancedSalesDialog(self, None, farm_id=self.farm_id)
            dialog.sale_saved.connect(self.refresh_data)
            if dialog.exec():
                success_msg = SuccessMessage(self, "Sale added successfully")
                success_msg.show()
        elif self.transaction_type == 'purchases':
            dialog = PurchaseDialog(self, None, self.purchase_manager, self.party_manager, self.inventory_manager)
            if dialog.exec():
                self.refresh_data()
                success_msg = SuccessMessage(self, "Purchase added successfully")
                success_msg.show()
        else:
            dialog = ExpenseDialog(self, None, self.expense_manager, self.party_manager, farm_id=self.farm_id)
            if dialog.exec():
                self.refresh_data()
                success_msg = SuccessMessage(self, "Expense added successfully")
                success_msg.show()
    
    def delete_transaction(self, transaction, trans_type):
        """Delete transaction with detailed confirmation"""
        # Get transaction details for confirmation
        if trans_type == 'sale':
            party = self.party_manager.get_party_by_id(transaction.party_id)
            qty_display = f"{transaction.cartons:.2f} cartons" if transaction.cartons else f"{transaction.quantity} eggs"
            details = (
                f"Date: {transaction.date.strftime('%Y-%m-%d')}\n"
                f"Party: {party.name if party else 'N/A'}\n"
                f"Quantity: {qty_display}\n"
                f"Total: {transaction.total_afg:,.2f} AFG"
            )
            title = "Delete Sale"
        elif trans_type == 'purchase':
            party = self.party_manager.get_party_by_id(transaction.party_id)
            session = DatabaseManager.get_session()
            try:
                material = session.query(RawMaterial).filter(RawMaterial.id == transaction.material_id).first()
            finally:
                session.close()
            details = (
                f"Date: {transaction.date.strftime('%Y-%m-%d')}\n"
                f"Party: {party.name if party else 'N/A'}\n"
                f"Material: {material.name if material else 'N/A'}\n"
                f"Quantity: {transaction.quantity:.2f}\n"
                f"Total: {transaction.total_afg:,.2f} AFG"
            )
            title = "Delete Purchase"
        else:  # expense
            party = self.party_manager.get_party_by_id(transaction.party_id) if transaction.party_id else None
            details = (
                f"Date: {transaction.date.strftime('%Y-%m-%d')}\n"
                f"Category: {transaction.category}\n"
                f"Party: {party.name if party else 'N/A'}\n"
                f"Amount: {transaction.amount_afg:,.2f} AFG"
            )
            title = "Delete Expense"
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Confirm Delete")
        msg.setText(f"Are you sure you want to delete this {trans_type}?")
        msg.setInformativeText(f"{details}\n\nThis action cannot be undone.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        if msg.exec() == QMessageBox.Yes:
            try:
                self.loading_overlay.set_message("Deleting transaction...")
                self.loading_overlay.show()
                QTimer.singleShot(50, lambda: self._do_delete_transaction(transaction, trans_type))
            except Exception as e:
                self.loading_overlay.hide()
                QMessageBox.critical(self, "Delete Failed", f"Failed to delete transaction: {str(e)}")
    
    def _do_delete_transaction(self, transaction, trans_type):
        """Perform the actual delete"""
        try:
            session = DatabaseManager.get_session()
            try:
                if trans_type == 'sale':
                    obj = session.query(Sale).filter(Sale.id == transaction.id).first()
                elif trans_type == 'purchase':
                    obj = session.query(Purchase).filter(Purchase.id == transaction.id).first()
                else:
                    obj = session.query(Expense).filter(Expense.id == transaction.id).first()

                if obj:
                    session.delete(obj)
                    session.commit()
                    self.loading_overlay.hide()
                    self.refresh_data()
                    success_msg = SuccessMessage(self, f"{trans_type.title()} deleted successfully")
                    success_msg.show()
                else:
                    self.loading_overlay.hide()
                    QMessageBox.warning(self, "Not Found", "Transaction not found")
            finally:
                session.close()
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, "Error", f"Failed to delete transaction: {str(e)}")

    def edit_sale(self, sale):
        """Edit sale using advanced dialog"""
        dialog = AdvancedSalesDialog(self, sale, farm_id=self.farm_id)
        dialog.sale_saved.connect(self.refresh_data)
        dialog.exec()
    
    def edit_purchase(self, purchase):
        """Edit purchase"""
        dialog = PurchaseDialog(self, purchase, self.purchase_manager, self.party_manager, self.inventory_manager)
        if dialog.exec():
            self.refresh_data()
    
    def edit_expense(self, expense):
        """Edit expense"""
        dialog = ExpenseDialog(self, expense, self.expense_manager, self.party_manager, farm_id=self.farm_id)
        if dialog.exec():
            self.refresh_data()
    
    def set_farm_id(self, farm_id):
        """Set current farm id and refresh data"""
        self.farm_id = farm_id
        try:
            self.refresh_data()
        except Exception:
            pass


class SalesDialog(QDialog):
    """Sales dialog"""
    
    def __init__(self, parent, sale, sales_manager, party_manager):
        super().__init__(parent)
        self.sale = sale
        self.sales_manager = sales_manager
        self.party_manager = party_manager
        
        self.setWindowTitle("New Sale")
        self.setGeometry(100, 100, 400, 250)
        
        layout = QFormLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        
        self.party_combo = QComboBox()
        for party in party_manager.get_all_parties():
            self.party_combo.addItem(party.name, party.id)
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMaximum(10000)
        self.quantity_spin.setSuffix(" eggs")
        
        self.rate_afg_spin = QDoubleSpinBox()
        self.rate_afg_spin.setSuffix(" AFG")
        self.rate_usd_spin = QDoubleSpinBox()
        self.rate_usd_spin.setSuffix(" USD")
        
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Credit"])
        self.payment_method_combo.setCurrentText("Cash")
        
        layout.addRow("Date:", self.date_edit)
        layout.addRow("Party:", self.party_combo)
        layout.addRow("Quantity:", self.quantity_spin)
        layout.addRow("Rate (AFG):", self.rate_afg_spin)
        layout.addRow("Rate (USD):", self.rate_usd_spin)
        layout.addRow("Payment Method:", self.payment_method_combo)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(35)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        save_btn.clicked.connect(self.save_sale)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
    
    def save_sale(self):
        """Save sale"""
        try:
            self.sales_manager.record_sale(
                self.party_combo.currentData(),
                self.quantity_spin.value(),
                self.rate_afg_spin.value(),
                self.rate_usd_spin.value(),
                date=self.date_edit.dateTime().toPython(),
                payment_method=self.payment_method_combo.currentText()
            )
            QMessageBox.information(self, "Success", "Sale recorded successfully")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to record sale: {e}")


class PurchaseDialog(QDialog):
    """Purchase dialog"""
    
    def __init__(self, parent, purchase, purchase_manager, party_manager, inventory_manager):
        super().__init__(parent)
        self.purchase = purchase
        self.purchase_manager = purchase_manager
        self.party_manager = party_manager
        self.inventory_manager = inventory_manager
        
        self.setWindowTitle("New Purchase")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QFormLayout()
        
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        
        self.party_combo = QComboBox()
        for party in party_manager.get_all_parties():
            self.party_combo.addItem(party.name, party.id)
        
        self.material_combo = QComboBox()
        materials = []
        try:
            # Use RawMaterialManager to get materials
            material_manager = RawMaterialManager()
            materials = material_manager.get_all_materials()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading materials: {e}")
            materials = []
        for material in materials:
            self.material_combo.addItem(material.name, material.id)
        
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMaximum(10000)
        self.quantity_spin.setSuffix(" units")
        
        self.rate_afg_spin = QDoubleSpinBox()
        self.rate_afg_spin.setSuffix(" AFG")
        self.rate_usd_spin = QDoubleSpinBox()
        self.rate_usd_spin.setSuffix(" USD")
        
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Credit"])
        self.payment_method_combo.setCurrentText("Cash")
        
        # Add tooltips and required field indicators
        self.date_edit.setToolTip("Select the purchase date (required)\nFormat: YYYY-MM-DD HH:MM")
        self.party_combo.setToolTip("Select the supplier/party (required)")
        self.material_combo.setToolTip("Select the raw material being purchased (required)")
        self.quantity_spin.setToolTip("Enter the quantity purchased (required, must be > 0)")
        self.quantity_spin.setValue(0.00)
        self.rate_afg_spin.setToolTip("Enter the rate per unit in AFG (required, must be >= 0)")
        self.rate_afg_spin.setValue(0.00)
        self.rate_usd_spin.setToolTip("Enter the rate per unit in USD (optional)")
        self.rate_usd_spin.setValue(0.00)
        self.payment_method_combo.setToolTip("Select payment method (required)")
        
        date_label = QLabel("Date: <span style='color: red;'>*</span>")
        date_label.setTextFormat(Qt.RichText)
        party_label = QLabel("Party: <span style='color: red;'>*</span>")
        party_label.setTextFormat(Qt.RichText)
        material_label = QLabel("Material: <span style='color: red;'>*</span>")
        material_label.setTextFormat(Qt.RichText)
        quantity_label = QLabel("Quantity: <span style='color: red;'>*</span>")
        quantity_label.setTextFormat(Qt.RichText)
        rate_afg_label = QLabel("Rate (AFG): <span style='color: red;'>*</span>")
        rate_afg_label.setTextFormat(Qt.RichText)
        rate_usd_label = QLabel("Rate (USD):")
        payment_label = QLabel("Payment Method: <span style='color: red;'>*</span>")
        payment_label.setTextFormat(Qt.RichText)
        
        layout.addRow(date_label, self.date_edit)
        layout.addRow(party_label, self.party_combo)
        layout.addRow(material_label, self.material_combo)
        layout.addRow(quantity_label, self.quantity_spin)
        layout.addRow(rate_afg_label, self.rate_afg_spin)
        layout.addRow(rate_usd_label, self.rate_usd_spin)
        layout.addRow(payment_label, self.payment_method_combo)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(35)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        save_btn.clicked.connect(self.save_purchase)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.SAVE, self.save_purchase)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.CLOSE, self.reject)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.ESCAPE, self.reject)
        
        # Load existing purchase data if editing
        if self.purchase:
            self.load_purchase_data()
    
    def load_purchase_data(self):
        """Load existing purchase data"""
        if not self.purchase:
            return
        
        try:
            self.date_edit.setDateTime(QDateTime.fromString(
                self.purchase.date.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss"
            ))
            
            # Find party index
            for i in range(self.party_combo.count()):
                if self.party_combo.itemData(i) == self.purchase.party_id:
                    self.party_combo.setCurrentIndex(i)
                    break
            
            # Find material index
            for i in range(self.material_combo.count()):
                if self.material_combo.itemData(i) == self.purchase.material_id:
                    self.material_combo.setCurrentIndex(i)
                    break
            
            self.quantity_spin.setValue(self.purchase.quantity)
            self.rate_afg_spin.setValue(self.purchase.rate_afg)
            self.rate_usd_spin.setValue(self.purchase.rate_usd)
            
            # Load payment method
            if hasattr(self.purchase, 'payment_method') and self.purchase.payment_method:
                index = self.payment_method_combo.findText(self.purchase.payment_method)
                if index >= 0:
                    self.payment_method_combo.setCurrentIndex(index)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading purchase data: {e}")
    
    def save_purchase(self):
        """Save purchase with loading indicator and success feedback"""
        # Validation
        if self.party_combo.currentData() is None:
            QMessageBox.warning(self, "Validation Error", "Please select a party. Party is required.")
            return
        
        if self.material_combo.currentData() is None:
            QMessageBox.warning(self, "Validation Error", "Please select a material. Material is required.")
            return
        
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0.")
            return
        
        if self.rate_afg_spin.value() < 0:
            QMessageBox.warning(self, "Validation Error", "Rate (AFG) cannot be negative.")
            return
        
        # Show loading overlay
        loading = LoadingOverlay(self, "Saving purchase...")
        loading.show()
        QTimer.singleShot(50, lambda: self._do_save_purchase(loading))
    
    def _do_save_purchase(self, loading):
        """Perform the actual save"""
        try:
            if self.purchase:
                # Update existing purchase
                from egg_farm_system.database.db import DatabaseManager
                session = DatabaseManager.get_session()
                try:
                    purchase = session.query(Purchase).filter_by(id=self.purchase.id).first()
                    if purchase:
                        purchase.party_id = self.party_combo.currentData()
                        purchase.material_id = self.material_combo.currentData()
                        purchase.date = self.date_edit.dateTime().toPython()
                        purchase.quantity = self.quantity_spin.value()
                        purchase.rate_afg = self.rate_afg_spin.value()
                        purchase.rate_usd = self.rate_usd_spin.value()
                        purchase.total_afg = purchase.quantity * purchase.rate_afg
                        purchase.total_usd = purchase.quantity * purchase.rate_usd
                        purchase.payment_method = self.payment_method_combo.currentText()
                        session.commit()
                        message = "Purchase updated successfully."
                finally:
                    session.close()
            else:
                # Create new purchase
                self.purchase_manager.record_purchase(
                    self.party_combo.currentData(),
                    self.material_combo.currentData(),
                    self.quantity_spin.value(),
                    self.rate_afg_spin.value(),
                    self.rate_usd_spin.value(),
                    date=self.date_edit.dateTime().toPython(),
                    payment_method=self.payment_method_combo.currentText()
                )
                message = "Purchase recorded successfully."
            
            loading.hide()
            loading.deleteLater()
            
            # Show success message
            success_msg = SuccessMessage(self, message)
            success_msg.show()
            QTimer.singleShot(100, lambda: self.accept())
        except ValueError as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.warning(self, "Validation Error", f"Invalid input: {str(e)}")
        except Exception as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.critical(
                self, 
                "Save Failed", 
                f"Failed to save purchase.\n\nError: {str(e)}\n\nPlease check your input and try again."
            )


class ExpenseDialog(QDialog):
    """Expense dialog"""
    
    def __init__(self, parent, expense, expense_manager, party_manager, farm_id=None):
        super().__init__(parent)
        self.expense = expense
        self.expense_manager = expense_manager
        self.party_manager = party_manager
        self.farm_id = farm_id
        
        self.setWindowTitle("Edit Expense" if expense else "New Expense")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QFormLayout()
        
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        
        self.category_combo = QComboBox()
        for category in EXPENSE_CATEGORIES:
            self.category_combo.addItem(category)
        
        self.amount_afg_spin = QDoubleSpinBox()
        self.amount_afg_spin.setSuffix(" AFG")
        self.amount_usd_spin = QDoubleSpinBox()
        self.amount_usd_spin.setSuffix(" USD")
        
        self.party_combo = QComboBox()
        self.party_combo.addItem("No Party", None)
        for party in party_manager.get_all_parties():
            self.party_combo.addItem(party.name, party.id)
        
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Credit"])
        self.payment_method_combo.setCurrentText("Cash")
        
        # Add tooltips and required field indicators
        self.date_edit.setToolTip("Select the expense date (required)\nFormat: YYYY-MM-DD HH:MM")
        self.category_combo.setToolTip("Select the expense category (required)")
        self.amount_afg_spin.setToolTip("Enter the amount in AFG (required, must be >= 0)")
        self.amount_afg_spin.setValue(0.00)
        self.amount_usd_spin.setToolTip("Enter the amount in USD (optional)")
        self.amount_usd_spin.setValue(0.00)
        self.party_combo.setToolTip("Select the party if this expense is related to a specific party (optional)")
        self.payment_method_combo.setToolTip("Select payment method (required)")
        
        date_label = QLabel("Date: <span style='color: red;'>*</span>")
        date_label.setTextFormat(Qt.RichText)
        category_label = QLabel("Category: <span style='color: red;'>*</span>")
        category_label.setTextFormat(Qt.RichText)
        amount_afg_label = QLabel("Amount (AFG): <span style='color: red;'>*</span>")
        amount_afg_label.setTextFormat(Qt.RichText)
        amount_usd_label = QLabel("Amount (USD):")
        party_label = QLabel("Party:")
        payment_label = QLabel("Payment Method: <span style='color: red;'>*</span>")
        payment_label.setTextFormat(Qt.RichText)
        
        layout.addRow(date_label, self.date_edit)
        layout.addRow(category_label, self.category_combo)
        layout.addRow(amount_afg_label, self.amount_afg_spin)
        layout.addRow(amount_usd_label, self.amount_usd_spin)
        layout.addRow(party_label, self.party_combo)
        layout.addRow(payment_label, self.payment_method_combo)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(35)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        save_btn.clicked.connect(self.save_expense)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.SAVE, self.save_expense)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.CLOSE, self.reject)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.ESCAPE, self.reject)
        
        # Load existing expense data if editing
        if self.expense:
            self.load_expense_data()
    
    def load_expense_data(self):
        """Load existing expense data"""
        if not self.expense:
            return
        
        try:
            self.date_edit.setDateTime(QDateTime.fromString(
                self.expense.date.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss"
            ))
            
            # Find category index
            index = self.category_combo.findText(self.expense.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            
            self.amount_afg_spin.setValue(self.expense.amount_afg)
            self.amount_usd_spin.setValue(self.expense.amount_usd)
            
            # Find party index
            if self.expense.party_id:
                for i in range(self.party_combo.count()):
                    if self.party_combo.itemData(i) == self.expense.party_id:
                        self.party_combo.setCurrentIndex(i)
                        break
            
            # Load payment method
            if hasattr(self.expense, 'payment_method') and self.expense.payment_method:
                index = self.payment_method_combo.findText(self.expense.payment_method)
                if index >= 0:
                    self.payment_method_combo.setCurrentIndex(index)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error loading expense data: {e}")
    
    def save_expense(self):
        """Save expense with loading indicator and success feedback"""
        farm_id = self.farm_id or (self.parent().farm_id if hasattr(self.parent(), 'farm_id') else None)
        if not farm_id:
            QMessageBox.warning(self, "Validation Error", "Farm ID is required. Please select a farm.")
            return
        
        if self.amount_afg_spin.value() < 0:
            QMessageBox.warning(self, "Validation Error", "Amount (AFG) cannot be negative.")
            return
        
        # Show loading overlay
        loading = LoadingOverlay(self, "Saving expense...")
        loading.show()
        QTimer.singleShot(50, lambda: self._do_save_expense(loading, farm_id))
    
    def _do_save_expense(self, loading, farm_id):
        """Perform the actual save"""
        try:
            if self.expense:
                # Update existing expense
                from egg_farm_system.database.db import DatabaseManager
                session = DatabaseManager.get_session()
                try:
                    expense = session.query(Expense).filter_by(id=self.expense.id).first()
                    if expense:
                        expense.farm_id = farm_id
                        expense.category = self.category_combo.currentText()
                        expense.amount_afg = self.amount_afg_spin.value()
                        expense.amount_usd = self.amount_usd_spin.value()
                        expense.party_id = self.party_combo.currentData()
                        expense.date = self.date_edit.dateTime().toPython()
                        expense.payment_method = self.payment_method_combo.currentText()
                        session.commit()
                        message = "Expense updated successfully."
                finally:
                    session.close()
            else:
                # Create new expense
                self.expense_manager.record_expense(
                    farm_id,
                    self.category_combo.currentText(),
                    self.amount_afg_spin.value(),
                    self.amount_usd_spin.value(),
                    party_id=self.party_combo.currentData(),
                    date=self.date_edit.dateTime().toPython(),
                    payment_method=self.payment_method_combo.currentText()
                )
                message = "Expense recorded successfully."
            
            loading.hide()
            loading.deleteLater()
            
            # Show success message
            success_msg = SuccessMessage(self, message)
            success_msg.show()
            QTimer.singleShot(100, lambda: self.accept())
        except ValueError as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.warning(self, "Validation Error", f"Invalid input: {str(e)}")
        except Exception as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.critical(
                self, 
                "Save Failed", 
                f"Failed to save expense.\n\nError: {str(e)}\n\nPlease check your input and try again."
            )
