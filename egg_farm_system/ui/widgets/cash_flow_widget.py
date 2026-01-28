"""
Cash Flow Management Widget
"""
from egg_farm_system.utils.i18n import tr

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QFrame, QDateEdit, QComboBox, QHeaderView,
    QMessageBox, QDoubleSpinBox, QTextEdit, QDialog, QFormLayout, QToolButton
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Ledger, Sale, Purchase, Expense, Payment
from egg_farm_system.utils.currency import CurrencyConverter
import logging
from egg_farm_system.ui.ui_helpers import create_button
from egg_farm_system.utils.jalali import format_value_for_ui

logger = logging.getLogger(__name__)


class CashFlowWidget(QWidget):
    """Cash flow management widget"""
    
    def __init__(self, farm_id=None):
        super().__init__()
        self.farm_id = farm_id
        self.converter = CurrencyConverter()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel(tr("Cash Flow Management"))
        title.setObjectName('titleLabel')
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Date range selector
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel(tr("From:")))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel(tr("To:")))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        
        filter_btn = create_button(tr("🔍 Filter"), style='primary')
        filter_btn.clicked.connect(self.load_data)
        date_layout.addWidget(filter_btn)
        
        header_layout.addLayout(date_layout)
        layout.addLayout(header_layout)
        
        # Summary cards - NEW SIMPLIFIED DESIGN
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)
        
        # Create cards with direct label references
        self.cash_inflow_card, self.cash_inflow_value = self.create_simple_card("Cash Inflow", "0.00", "#6B8E23")
        self.cash_outflow_card, self.cash_outflow_value = self.create_simple_card("Cash Outflow", "0.00", "#C62828")
        self.net_cash_flow_card, self.net_cash_flow_value = self.create_simple_card("Net Cash Flow", "0.00", "#8B4513")
        self.cash_balance_card, self.cash_balance_value = self.create_simple_card("Cash Balance", "0.00", "#CD853F")
        
        summary_layout.addWidget(self.cash_inflow_card)
        summary_layout.addWidget(self.cash_outflow_card)
        summary_layout.addWidget(self.net_cash_flow_card)
        summary_layout.addWidget(self.cash_balance_card)
        layout.addLayout(summary_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        add_inflow_btn = create_button(tr("➕ Add Cash Inflow"), style='success')
        add_inflow_btn.clicked.connect(self.add_cash_inflow)
        action_layout.addWidget(add_inflow_btn)

        add_outflow_btn = create_button(tr("➖ Add Cash Outflow"), style='danger')
        add_outflow_btn.clicked.connect(self.add_cash_outflow)
        action_layout.addWidget(add_outflow_btn)

        refresh_btn = create_button(tr("🔄 Refresh"), style='ghost')
        refresh_btn.clicked.connect(self.load_data)
        action_layout.addWidget(refresh_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Cash flow table
        table_group = QGroupBox("Cash Flow Transactions")
        table_layout = QVBoxLayout(table_group)
        
        self.cash_flow_table = QTableWidget()
        self.cash_flow_table.setColumnCount(7)
        self.cash_flow_table.setHorizontalHeaderLabels([
            "Date", "Type", "Description", "Amount (AFG)", "Amount (USD)", "Balance", "Actions"
        ])
        self.cash_flow_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cash_flow_table.setAlternatingRowColors(True)
        self.cash_flow_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cash_flow_table.verticalHeader().setMinimumSectionSize(40)
        self.cash_flow_table.verticalHeader().setDefaultSectionSize(40)
        table_layout.addWidget(self.cash_flow_table)
        
        layout.addWidget(table_group)
        
        self.setLayout(layout)
    
    def create_simple_card(self, title, value, color):
        """Create a metric card matching dashboard design - returns (card_widget, value_label)"""
        card = QFrame()
        card.setFrameShape(QFrame.NoFrame)
        card.setFixedHeight(110)
        card.setMinimumWidth(200)
        
        darker_color = self._darken_color(color, 0.15)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color},
                    stop:1 {darker_color});
                border-radius: 12px;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 14, 16, 14)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.95);
            font-size: 10pt;
            font-weight: 600;
            letter-spacing: 0.2px;
        """)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            color: white;
            font-size: 24pt;
            font-weight: 700;
            letter-spacing: -0.3px;
        """)
        value_label.setWordWrap(False)
        value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        value_label.setMinimumHeight(35)
        layout.addWidget(value_label)
        
        return card, value_label
    
    def _darken_color(self, hex_color, factor):
        """Darken a hex color"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def load_data(self):
        """Load cash flow data"""
        try:
            session = DatabaseManager.get_session()
            try:
                start_date = self.start_date.date().toPython()
                end_date = self.end_date.date().toPython()
                # end_date is already a date object, combine with max time
                if isinstance(end_date, datetime):
                    end_date = datetime.combine(end_date.date(), datetime.max.time())
                else:
                    end_date = datetime.combine(end_date, datetime.max.time())
                
                # Get all cash transactions
                # Note: Sales and Purchases are Accrual (Ledger) events. 
                # Cash flow is tracked via Payments and Direct Expenses only.
                transactions = []
                
                # Direct Expenses (cash outflow) - Direct expenses with no party linked and cash payment method
                direct_expenses = session.query(Expense).filter(
                    Expense.date >= start_date,
                    Expense.date <= end_date,
                    Expense.party_id == None,
                    Expense.payment_method == "Cash"
                ).all()
                for expense in direct_expenses:
                    transactions.append({
                        'date': expense.date,
                        'type': 'Expense',
                        'description': f"{expense.category}: {expense.description or ''}",
                        'amount_afg': expense.amount_afg,
                        'amount_usd': expense.amount_usd,
                        'is_inflow': False,
                        'expense_id': expense.id,
                        'payment_id': None
                    })
                
                # Payments (can be inflow or outflow) - All payments represent cash movement
                # This includes: Sales (Received), Purchases (Paid), and Expenses with cash payment method
                payments = session.query(Payment).filter(
                    Payment.date >= start_date,
                    Payment.date <= end_date
                ).all()
                for payment in payments:
                    transactions.append({
                        'date': payment.date,
                        'type': 'Payment',
                        'description': f"Payment {payment.payment_type.lower()}: {payment.reference or 'Cash'}",
                        'amount_afg': payment.amount_afg,
                        'amount_usd': payment.amount_usd,
                        'is_inflow': payment.payment_type == "Received",
                        'expense_id': None,
                        'payment_id': payment.id,
                        'payment_reference': payment.reference
                    })
                
                # Sort by date
                transactions.sort(key=lambda x: x['date'])
                
                # Calculate totals
                total_inflow_afg = sum(t['amount_afg'] for t in transactions if t['is_inflow'])
                total_inflow_usd = sum(t['amount_usd'] for t in transactions if t['is_inflow'])
                total_outflow_afg = sum(t['amount_afg'] for t in transactions if not t['is_inflow'])
                total_outflow_usd = sum(t['amount_usd'] for t in transactions if not t['is_inflow'])
                
                net_flow_afg = total_inflow_afg - total_outflow_afg
                net_flow_usd = total_inflow_usd - total_outflow_usd
                
                # Get opening balance (all transactions before start date)
                opening_balance_afg = self._get_opening_balance(start_date, session)
                
                # Update cards with direct label references - NO FINDCHILD NEEDED
                logger.info(f"Updating card values - inflow: {total_inflow_afg}, outflow: {total_outflow_afg}, net: {net_flow_afg}")
                
                self.cash_inflow_value.setText(f"Afs {total_inflow_afg:,.2f}")
                self.cash_outflow_value.setText(f"Afs {total_outflow_afg:,.2f}")
                self.net_cash_flow_value.setText(f"Afs {net_flow_afg:,.2f}")
                
                logger.info(f"Card values updated successfully")
                
                closing_balance_afg = opening_balance_afg + net_flow_afg
                self.cash_balance_value.setText(f"Afs {closing_balance_afg:,.2f}")
                
                # Populate table
                self.cash_flow_table.setRowCount(len(transactions))
                running_balance_afg = opening_balance_afg
                
                for row, trans in enumerate(transactions):
                    running_balance_afg += (trans['amount_afg'] if trans['is_inflow'] else -trans['amount_afg'])
                    
                    self.cash_flow_table.setItem(row, 0, QTableWidgetItem(format_value_for_ui(trans.get('date'))))
                    self.cash_flow_table.setItem(row, 1, QTableWidgetItem(trans['type']))
                    self.cash_flow_table.setItem(row, 2, QTableWidgetItem(trans['description']))
                    
                    amount_item = QTableWidgetItem(f"{trans['amount_afg']:,.2f}")
                    if trans['is_inflow']:
                        amount_item.setForeground(QColor("#6B8E23"))
                    else:
                        amount_item.setForeground(QColor("#C62828"))
                    self.cash_flow_table.setItem(row, 3, amount_item)
                    
                    self.cash_flow_table.setItem(row, 4, QTableWidgetItem(f"{trans['amount_usd']:,.2f}"))
                    
                    balance_item = QTableWidgetItem(f"{running_balance_afg:,.2f}")
                    if running_balance_afg < 0:
                        balance_item.setForeground(QColor("#C62828"))
                    self.cash_flow_table.setItem(row, 5, balance_item)
                    
                    # Add action button (Delete)
                    delete_btn = QToolButton()
                    delete_btn.setText("Delete")
                    delete_btn.setAutoRaise(True)
                    delete_btn.setStyleSheet("color: #C62828;")
                    delete_btn.clicked.connect(lambda checked, t=trans: self.delete_cash_transaction(t))
                    self.cash_flow_table.setCellWidget(row, 6, delete_btn)
                
                # Sort by date descending
                self.cash_flow_table.sortItems(0, Qt.DescendingOrder)
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error loading cash flow data: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to load cash flow data: {e}")
    
    def _get_opening_balance(self, start_date, session):
        """Calculate opening cash balance before start date"""
        try:
            # Get all transactions before start date
            total_inflow = 0
            total_outflow = 0
            
            # Expenses - Direct only (no party)
            expenses = session.query(Expense).filter(
                Expense.date < start_date,
                Expense.party_id == None
            ).all()
            total_outflow += sum(e.amount_afg for e in expenses)
            
            # Payments - All
            payments = session.query(Payment).filter(
                Payment.date < start_date
            ).all()
            for payment in payments:
                if payment.payment_type == "Received":
                    total_inflow += payment.amount_afg
                else:
                    total_outflow += payment.amount_afg
            
            return total_inflow - total_outflow
        except Exception as e:
            logger.error(f"Error calculating opening balance: {e}")
            return 0
    
    def add_cash_inflow(self):
        """Add manual cash inflow"""
        dialog = CashTransactionDialog(self, "Inflow")
        if dialog.exec():
            self.load_data()
    
    def add_cash_outflow(self):
        """Add manual cash outflow"""
        dialog = CashTransactionDialog(self, "Outflow")
        if dialog.exec():
            self.load_data()
    
    def delete_cash_transaction(self, transaction):
        """Delete a cash flow transaction and its associated source transaction"""
        try:
            # Confirmation dialog
            reply = QMessageBox.question(
                self,
                tr("Confirm Delete"),
                f"Are you sure you want to delete this {transaction.get('type', 'Transaction')} transaction?\n\n"
                f"Description: {transaction.get('description', 'N/A')}\n"
                f"Amount: Afs {transaction.get('amount_afg', 0):,.2f}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            session = DatabaseManager.get_session()
            try:
                # Delete the Payment record if it exists
                if transaction.get('payment_id'):
                    payment = session.query(Payment).filter(Payment.id == transaction['payment_id']).first()
                    if payment:
                        # Parse the reference to find and delete the source transaction
                        reference = payment.reference or ""
                        
                        # Handle different transaction types
                        if "Sale #" in reference:
                            # Extract sale ID and delete the sale
                            sale_id = int(reference.split("#")[1])
                            from egg_farm_system.database.models import Sale
                            sale = session.query(Sale).filter(Sale.id == sale_id).first()
                            if sale:
                                session.delete(sale)
                                # Also delete associated ledger entries
                                from egg_farm_system.database.models import Ledger
                                session.query(Ledger).filter(
                                    Ledger.reference_type == "Sale",
                                    Ledger.reference_id == sale_id
                                ).delete()
                        
                        elif "Raw Material Sale #" in reference:
                            # Extract raw material sale ID and delete
                            from egg_farm_system.database.models import RawMaterialSale
                            sale_id = int(reference.split("#")[1])
                            raw_sale = session.query(RawMaterialSale).filter(RawMaterialSale.id == sale_id).first()
                            if raw_sale:
                                # Restore material stock
                                from egg_farm_system.database.models import RawMaterial
                                material = session.query(RawMaterial).filter(RawMaterial.id == raw_sale.material_id).first()
                                if material:
                                    material.current_stock += raw_sale.quantity
                                session.delete(raw_sale)
                                # Also delete associated ledger entries
                                from egg_farm_system.database.models import Ledger
                                session.query(Ledger).filter(
                                    Ledger.reference_type == "RawMaterialSale",
                                    Ledger.reference_id == sale_id
                                ).delete()
                        
                        elif "Purchase #" in reference:
                            # Extract purchase ID and delete
                            from egg_farm_system.database.models import Purchase
                            purchase_id = int(reference.split("#")[1])
                            purchase = session.query(Purchase).filter(Purchase.id == purchase_id).first()
                            if purchase:
                                # Restore material stock
                                from egg_farm_system.database.models import RawMaterial
                                material = session.query(RawMaterial).filter(RawMaterial.id == purchase.material_id).first()
                                if material:
                                    material.current_stock -= purchase.quantity
                                session.delete(purchase)
                                # Also delete associated ledger entries
                                from egg_farm_system.database.models import Ledger
                                session.query(Ledger).filter(
                                    Ledger.reference_type == "Purchase",
                                    Ledger.reference_id == purchase_id
                                ).delete()
                        
                        elif "Expense:" in reference:
                            # Extract expense category and delete related expense
                            from egg_farm_system.database.models import Expense
                            category = reference.split(":")[1].strip() if ":" in reference else ""
                            if category:
                                expense = session.query(Expense).filter(
                                    Expense.category == category,
                                    Expense.party_id == payment.party_id,
                                    Expense.date == payment.date
                                ).first()
                                if expense:
                                    session.delete(expense)
                        
                        # Delete the payment record
                        session.delete(payment)
                
                # Delete direct expense if it exists
                elif transaction.get('expense_id'):
                    from egg_farm_system.database.models import Expense
                    expense = session.query(Expense).filter(Expense.id == transaction['expense_id']).first()
                    if expense:
                        session.delete(expense)
                
                session.commit()
                QMessageBox.information(self, tr("Success"), "Transaction deleted successfully")
                self.load_data()
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error deleting transaction: {e}")
                QMessageBox.critical(self, tr("Error"), f"Failed to delete transaction: {str(e)}")
            finally:
                session.close()
        
        except Exception as e:
            logger.error(f"Error in delete_cash_transaction: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to delete transaction: {str(e)}")


class CashTransactionDialog(QDialog):
    """Dialog for manual cash transaction entry"""
    
    def __init__(self, parent, transaction_type):
        super().__init__(parent)
        self.transaction_type = transaction_type
        self.converter = CurrencyConverter()
        
        self.setWindowTitle(f"Add Cash {transaction_type}")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Date:", self.date_edit)
        
        self.amount_afg_spin = QDoubleSpinBox()
        self.amount_afg_spin.setMinimum(0.01)
        self.amount_afg_spin.setMaximum(999999999)
        self.amount_afg_spin.setDecimals(2)
        self.amount_afg_spin.setPrefix("Afs ")
        form.addRow("Amount (AFG):", self.amount_afg_spin)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText(f"Description for cash {self.transaction_type.lower()}...")
        form.addRow("Description:", self.description_edit)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton(f"Save {self.transaction_type}")
        save_btn.setMinimumWidth(120)
        save_btn.setMinimumHeight(35)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8B4513,
                    stop:1 #7A3A0F);
                color: white;
                font-weight: 600;
                padding: 8px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #A0522D,
                    stop:1 #8B4513);
            }
        """)
        save_btn.clicked.connect(self.save_transaction)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def save_transaction(self):
        """Save cash transaction"""
        try:
            amount_afg = self.amount_afg_spin.value()
            description = self.description_edit.toPlainText().strip()
            date = self.date_edit.date().toPython()
            
            if amount_afg <= 0:
                QMessageBox.warning(self, tr("Validation"), "Please enter an amount")
                return
            
            if not description:
                description = f"Manual cash {self.transaction_type.lower()}"
            
            # Create a manual expense or payment entry
            session = DatabaseManager.get_session()
            try:
                from egg_farm_system.database.models import Expense
                
                amount_usd = self.converter.afg_to_usd(amount_afg)
                
                if self.transaction_type == "Inflow":
                    # Record as negative expense (income)
                    expense = Expense(
                        farm_id=self.parent().farm_id if hasattr(self.parent(), 'farm_id') else None,
                        date=date,
                        category="Cash Income",
                        description=description,
                        amount_afg=-amount_afg,  # Negative for inflow
                        amount_usd=-amount_usd,
                        exchange_rate_used=self.converter.exchange_rate,
                        party_id=None
                    )
                else:
                    # Record as expense (outflow)
                    expense = Expense(
                        farm_id=self.parent().farm_id if hasattr(self.parent(), 'farm_id') else None,
                        date=date,
                        category="Cash Outflow",
                        description=description,
                        amount_afg=amount_afg,
                        amount_usd=amount_usd,
                        exchange_rate_used=self.converter.exchange_rate,
                        party_id=None
                    )
                
                session.add(expense)
                session.commit()
                QMessageBox.information(self, tr("Success"), f"Cash {self.transaction_type.lower()} saved successfully")
                self.accept()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error saving cash transaction: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to save transaction: {e}")

