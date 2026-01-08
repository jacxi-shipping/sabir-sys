"""
Cash Flow Management Widget
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QFrame, QDateEdit, QComboBox, QHeaderView,
    QMessageBox, QDoubleSpinBox, QTextEdit, QDialog, QFormLayout
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Ledger, Sale, Purchase, Expense, Payment
from egg_farm_system.utils.currency import CurrencyConverter
import logging

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
        title = QLabel("Cash Flow Management")
        title.setObjectName('titleLabel')
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Date range selector
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)
        
        filter_btn = QPushButton("🔍 Filter")
        filter_btn.clicked.connect(self.load_data)
        date_layout.addWidget(filter_btn)
        
        header_layout.addLayout(date_layout)
        layout.addLayout(header_layout)
        
        # Summary cards
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)
        
        self.cash_inflow_card = self.create_summary_card("Cash Inflow", "0.00", "#6B8E23")
        self.cash_outflow_card = self.create_summary_card("Cash Outflow", "0.00", "#C62828")
        self.net_cash_flow_card = self.create_summary_card("Net Cash Flow", "0.00", "#8B4513")
        self.cash_balance_card = self.create_summary_card("Cash Balance", "0.00", "#CD853F")
        
        summary_layout.addWidget(self.cash_inflow_card)
        summary_layout.addWidget(self.cash_outflow_card)
        summary_layout.addWidget(self.net_cash_flow_card)
        summary_layout.addWidget(self.cash_balance_card)
        layout.addLayout(summary_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        add_inflow_btn = QPushButton("➕ Add Cash Inflow")
        add_inflow_btn.clicked.connect(self.add_cash_inflow)
        action_layout.addWidget(add_inflow_btn)
        
        add_outflow_btn = QPushButton("➖ Add Cash Outflow")
        add_outflow_btn.clicked.connect(self.add_cash_outflow)
        action_layout.addWidget(add_outflow_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_data)
        action_layout.addWidget(refresh_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Cash flow table
        table_group = QGroupBox("Cash Flow Transactions")
        table_layout = QVBoxLayout(table_group)
        
        self.cash_flow_table = QTableWidget()
        self.cash_flow_table.setColumnCount(6)
        self.cash_flow_table.setHorizontalHeaderLabels([
            "Date", "Type", "Description", "Amount (AFG)", "Amount (USD)", "Balance"
        ])
        self.cash_flow_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cash_flow_table.setAlternatingRowColors(True)
        self.cash_flow_table.setSelectionBehavior(QTableWidget.SelectRows)
        table_layout.addWidget(self.cash_flow_table)
        
        layout.addWidget(table_group)
        
        self.setLayout(layout)
    
    def create_summary_card(self, title, value, color):
        """Create summary card"""
        card = QFrame()
        card.setFixedHeight(100)
        darker = self._darken_color(color, 0.15)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color},
                    stop:1 {darker});
                border-radius: 12px;
                padding: 14px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 10pt;
            font-weight: 600;
        """)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("card_value")
        value_label.setStyleSheet("""
            color: white;
            font-size: 24pt;
            font-weight: 700;
        """)
        layout.addWidget(value_label)
        
        return card
    
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
                transactions = []
                
                # Sales (cash inflow) - ONLY if payment_method is Cash
                sales = session.query(Sale).filter(
                    Sale.date >= start_date,
                    Sale.date <= end_date,
                    Sale.payment_method == "Cash"
                ).all()
                for sale in sales:
                    transactions.append({
                        'date': sale.date,
                        'type': 'Sale',
                        'description': f"Sale to {sale.party.name if sale.party else 'Cash'}: {sale.cartons or sale.quantity} {'cartons' if sale.cartons else 'eggs'}",
                        'amount_afg': sale.total_afg,
                        'amount_usd': sale.total_usd,
                        'is_inflow': True
                    })
                
                # Purchases (cash outflow) - ONLY if payment_method is Cash
                purchases = session.query(Purchase).filter(
                    Purchase.date >= start_date,
                    Purchase.date <= end_date,
                    Purchase.payment_method == "Cash"
                ).all()
                for purchase in purchases:
                    transactions.append({
                        'date': purchase.date,
                        'type': 'Purchase',
                        'description': f"Purchase from {purchase.party.name if purchase.party else 'Cash'}: {purchase.material.name if purchase.material else 'Material'}",
                        'amount_afg': purchase.total_afg,
                        'amount_usd': purchase.total_usd,
                        'is_inflow': False
                    })
                
                # Expenses (cash outflow) - ONLY if payment_method is Cash
                expenses = session.query(Expense).filter(
                    Expense.date >= start_date,
                    Expense.date <= end_date,
                    Expense.payment_method == "Cash"
                ).all()
                for expense in expenses:
                    transactions.append({
                        'date': expense.date,
                        'type': 'Expense',
                        'description': f"{expense.category}: {expense.description or ''}",
                        'amount_afg': expense.amount_afg,
                        'amount_usd': expense.amount_usd,
                        'is_inflow': False
                    })
                
                # Payments (can be inflow or outflow) - ONLY if payment_method is Cash
                payments = session.query(Payment).filter(
                    Payment.date >= start_date,
                    Payment.date <= end_date,
                    Payment.payment_method == "Cash"
                ).all()
                for payment in payments:
                    transactions.append({
                        'date': payment.date,
                        'type': 'Payment',
                        'description': f"Payment {payment.payment_type.lower()}: {payment.reference or 'Cash'}",
                        'amount_afg': payment.amount_afg,
                        'amount_usd': payment.amount_usd,
                        'is_inflow': payment.payment_type == "Received"
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
                
                # Update cards
                self.cash_inflow_card.findChild(QLabel, "card_value").setText(f"Afs {total_inflow_afg:,.2f}")
                self.cash_outflow_card.findChild(QLabel, "card_value").setText(f"Afs {total_outflow_afg:,.2f}")
                self.net_cash_flow_card.findChild(QLabel, "card_value").setText(f"Afs {net_flow_afg:,.2f}")
                
                # Color code net flow
                if net_flow_afg < 0:
                    self.net_cash_flow_card.setStyleSheet("""
                        QFrame {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #C62828,
                                stop:1 #A02020);
                            border-radius: 12px;
                            padding: 14px;
                        }
                    """)
                else:
                    self.net_cash_flow_card.setStyleSheet("""
                        QFrame {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #6B8E23,
                                stop:1 #5A7A1F);
                            border-radius: 12px;
                            padding: 14px;
                        }
                    """)
                
                closing_balance_afg = opening_balance_afg + net_flow_afg
                self.cash_balance_card.findChild(QLabel, "card_value").setText(f"Afs {closing_balance_afg:,.2f}")
                
                # Populate table
                self.cash_flow_table.setRowCount(len(transactions))
                running_balance_afg = opening_balance_afg
                
                for row, trans in enumerate(transactions):
                    running_balance_afg += (trans['amount_afg'] if trans['is_inflow'] else -trans['amount_afg'])
                    
                    self.cash_flow_table.setItem(row, 0, QTableWidgetItem(trans['date'].strftime("%Y-%m-%d %H:%M")))
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
                
                # Sort by date descending
                self.cash_flow_table.sortItems(0, Qt.DescendingOrder)
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error loading cash flow data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load cash flow data: {e}")
    
    def _get_opening_balance(self, start_date, session):
        """Calculate opening cash balance before start date"""
        try:
            # Get all transactions before start date
            total_inflow = 0
            total_outflow = 0
            
            # Sales - ONLY Cash transactions
            sales = session.query(Sale).filter(
                Sale.date < start_date,
                Sale.payment_method == "Cash"
            ).all()
            total_inflow += sum(s.total_afg for s in sales)
            
            # Purchases - ONLY Cash transactions
            purchases = session.query(Purchase).filter(
                Purchase.date < start_date,
                Purchase.payment_method == "Cash"
            ).all()
            total_outflow += sum(p.total_afg for p in purchases)
            
            # Expenses - ONLY Cash transactions
            expenses = session.query(Expense).filter(
                Expense.date < start_date,
                Expense.payment_method == "Cash"
            ).all()
            total_outflow += sum(e.amount_afg for e in expenses)
            
            # Payments - ONLY Cash transactions
            payments = session.query(Payment).filter(
                Payment.date < start_date,
                Payment.payment_method == "Cash"
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
        
        cancel_btn = QPushButton("Cancel")
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
                QMessageBox.warning(self, "Validation", "Please enter an amount")
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
                QMessageBox.information(self, "Success", f"Cash {self.transaction_type.lower()} saved successfully")
                self.accept()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error saving cash transaction: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save transaction: {e}")

