"""
Premium Party View Dialog with Ledger Management and Direct Credit/Debit
"""
from egg_farm_system.utils.i18n import tr

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QFrame, QTabWidget, QWidget,
    QFormLayout, QDoubleSpinBox, QDateEdit, QTextEdit, QComboBox, QHeaderView,
    QLineEdit, QToolButton
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from datetime import datetime
from egg_farm_system.modules.ledger import LedgerManager
from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.utils.currency import CurrencyConverter
import logging
from egg_farm_system.ui.ui_helpers import create_button
from egg_farm_system.ui.forms.add_transaction_dialog import AddTransactionDialog
from egg_farm_system.utils.jalali import format_value_for_ui

logger = logging.getLogger(__name__)


class PartyViewDialog(QDialog):
    """Premium party view dialog with ledger management"""
    
    def __init__(self, parent, party):
        super().__init__(parent)
        self.party = party
        self.ledger_manager = LedgerManager()
        self.party_manager = PartyManager()
        self.converter = CurrencyConverter()
        
        self.setWindowTitle(f"Party Account: {party.name}")
        self.setMinimumSize(1000, 700)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize premium UI"""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with party info
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B4513,
                    stop:1 #A0522D);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(8)
        
        name_label = QLabel(self.party.name)
        name_label.setStyleSheet("""
            color: white;
            font-size: 20pt;
            font-weight: 700;
        """)
        header_layout.addWidget(name_label)
        
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        
        phone_label = QLabel(f"📞 {self.party.phone or 'N/A'}")
        phone_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 11pt;")
        info_layout.addWidget(phone_label)
        
        address_label = QLabel(f"📍 {self.party.address or 'N/A'}")
        address_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 11pt;")
        info_layout.addWidget(address_label)
        
        info_layout.addStretch()
        header_layout.addLayout(info_layout)
        layout.addWidget(header_frame)
        
        # Balance cards
        balance_layout = QHBoxLayout()
        balance_layout.setSpacing(12)
        
        self.balance_afg_card, self.balance_afg_value = self.create_balance_card("Balance (AFG)", "0.00", "#8B4513")
        self.balance_usd_card, self.balance_usd_value = self.create_balance_card("Balance (USD)", "0.00", "#CD853F")
        self.total_debit_card, self.total_debit_value = self.create_balance_card("Total Debit", "0.00", "#6B8E23")
        self.total_credit_card, self.total_credit_value = self.create_balance_card("Total Credit", "0.00", "#9ACD32")
        
        balance_layout.addWidget(self.balance_afg_card)
        balance_layout.addWidget(self.balance_usd_card)
        balance_layout.addWidget(self.total_debit_card)
        balance_layout.addWidget(self.total_credit_card)
        layout.addLayout(balance_layout)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        debit_btn = create_button(tr("💰 Debit Account"), style='danger')
        debit_btn.clicked.connect(self.show_debit_dialog)
        action_layout.addWidget(debit_btn)
        
        credit_btn = create_button(tr("💵 Credit Account"), style='success')
        credit_btn.clicked.connect(self.show_credit_dialog)
        action_layout.addWidget(credit_btn)
        
        refresh_btn = create_button(tr("🔄 Refresh"), style='ghost')
        refresh_btn.clicked.connect(self.load_data)
        action_layout.addWidget(refresh_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Tabs for ledger and details
        tabs = QTabWidget()
        
        # Ledger tab
        ledger_tab = QWidget()
        ledger_layout = QVBoxLayout(ledger_tab)
        
        self.ledger_table = QTableWidget()
        self.ledger_table.setColumnCount(8)
        self.ledger_table.setHorizontalHeaderLabels([
            "Date", "Description", "Debit AFG", "Credit AFG", 
            "Debit USD", "Credit USD", "Balance", "Actions"
        ])
        self.ledger_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ledger_table.setAlternatingRowColors(True)
        self.ledger_table.verticalHeader().setMinimumSectionSize(40)
        self.ledger_table.verticalHeader().setDefaultSectionSize(40)
        self.ledger_table.setSelectionBehavior(QTableWidget.SelectRows)
        ledger_layout.addWidget(self.ledger_table)
        
        tabs.addTab(ledger_tab, "📊 Ledger Entries")
        
        # Details tab
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        details_layout.setSpacing(12)
        
        notes_group = QGroupBox("Notes")
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setPlainText(self.party.notes or "No notes available.")
        notes_group_layout = QVBoxLayout(notes_group)
        notes_group_layout.addWidget(self.notes_text)
        details_layout.addWidget(notes_group)
        
        details_layout.addStretch()
        tabs.addTab(details_tab, "📝 Details")
        
        layout.addWidget(tabs)
        
        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        close_btn = create_button(tr("Close"), style='ghost')
        close_btn.setMinimumWidth(100)
        close_btn.setMinimumHeight(35)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def create_balance_card(self, title, value, color):
        """Create a balance card matching dashboard design - returns (card_widget, value_label)"""
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
    
    def _apply_balance_color(self, label, balance):
        """Apply color to balance label based on value: red if negative, green if positive, black if zero"""
        if balance < 0:
            label.setStyleSheet("""
                color: #C62828;
                font-size: 24pt;
                font-weight: 700;
                letter-spacing: -0.3px;
            """)
        elif balance > 0:
            label.setStyleSheet("""
                color: #2E7D32;
                font-size: 24pt;
                font-weight: 700;
                letter-spacing: -0.3px;
            """)
        else:
            label.setStyleSheet("""
                color: #000000;
                font-size: 24pt;
                font-weight: 700;
                letter-spacing: -0.3px;
            """)
    
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
        """Load party ledger data"""
        try:
            # Get ledger entries with running balance
            entries_afg = self.ledger_manager.get_balance_with_running(self.party.id, "AFG")
            entries_usd = self.ledger_manager.get_balance_with_running(self.party.id, "USD")
            summary = self.ledger_manager.get_ledger_summary(self.party.id)
            
            # Update balance cards with direct label references
            if summary:
                balance_afg = summary['balance_afg']
                balance_usd = summary['balance_usd']
                total_debit_afg = summary['total_debit_afg']
                total_credit_afg = summary['total_credit_afg']
                
                # Update values directly with color coding
                self.balance_afg_value.setText(f"{balance_afg:,.2f}")
                self._apply_balance_color(self.balance_afg_value, balance_afg)
                
                self.balance_usd_value.setText(f"{balance_usd:,.2f}")
                self._apply_balance_color(self.balance_usd_value, balance_usd)
                
                self.total_debit_value.setText(f"{total_debit_afg:,.2f}")
                self.total_credit_value.setText(f"{total_credit_afg:,.2f}")
            
            # Load ledger entries
            all_entries = self.ledger_manager.get_party_ledger(self.party.id)
            self.ledger_table.setRowCount(len(all_entries))
            
            running_balance_afg = 0
            running_balance_usd = 0
            
            # Store entries for later reference in edit/delete
            self.ledger_entries = all_entries
            
            for row, entry in enumerate(all_entries):
                running_balance_afg += (entry.debit_afg - entry.credit_afg)
                running_balance_usd += (entry.debit_usd - entry.credit_usd)
                
                self.ledger_table.setItem(row, 0, QTableWidgetItem(format_value_for_ui(entry.date)))
                self.ledger_table.setItem(row, 1, QTableWidgetItem(entry.description))
                self.ledger_table.setItem(row, 2, QTableWidgetItem(f"{entry.debit_afg:,.2f}" if entry.debit_afg > 0 else ""))
                self.ledger_table.setItem(row, 3, QTableWidgetItem(f"{entry.credit_afg:,.2f}" if entry.credit_afg > 0 else ""))
                self.ledger_table.setItem(row, 4, QTableWidgetItem(f"{entry.debit_usd:,.2f}" if entry.debit_usd > 0 else ""))
                self.ledger_table.setItem(row, 5, QTableWidgetItem(f"{entry.credit_usd:,.2f}" if entry.credit_usd > 0 else ""))
                
                balance_item = QTableWidgetItem(f"AFG: {running_balance_afg:,.2f} | USD: {running_balance_usd:,.2f}")
                if running_balance_afg < 0 or running_balance_usd < 0:
                    balance_item.setForeground(QColor("#C62828"))
                elif running_balance_afg > 0 or running_balance_usd > 0:
                    balance_item.setForeground(QColor("#6B8E23"))
                self.ledger_table.setItem(row, 6, balance_item)
                
                # Add action buttons (Edit and Delete)
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(4, 2, 4, 2)
                action_layout.setSpacing(4)
                
                edit_btn = QToolButton()
                edit_btn.setText("Edit")
                edit_btn.setAutoRaise(True)
                edit_btn.clicked.connect(lambda checked, e=entry, r=row: self.edit_transaction(e, r))
                action_layout.addWidget(edit_btn)
                
                delete_btn = QToolButton()
                delete_btn.setText("Delete")
                delete_btn.setAutoRaise(True)
                delete_btn.setStyleSheet("color: #C62828;")
                delete_btn.clicked.connect(lambda checked, e=entry, r=row: self.delete_transaction(e, r))
                action_layout.addWidget(delete_btn)
                
                action_layout.addStretch()
                self.ledger_table.setCellWidget(row, 7, action_widget)
            
            # Sort by date descending (newest first)
            self.ledger_table.sortItems(0, Qt.DescendingOrder)
            
        except Exception as e:
            logger.error(f"Error loading party data: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to load party data: {e}")
    
    def edit_transaction(self, entry, row):
        """Edit transaction entry"""
        try:
            # Create edit dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Edit Transaction - {format_value_for_ui(entry.date)}")
            dialog.setMinimumWidth(500)
            
            layout = QFormLayout()
            
            date_edit = QDateEdit()
            date_edit.setDateTime(entry.date)
            layout.addRow("Date & Time:", date_edit)
            
            desc_edit = QLineEdit()
            desc_edit.setText(entry.description)
            layout.addRow("Description:", desc_edit)
            
            debit_afg_spin = QDoubleSpinBox()
            debit_afg_spin.setValue(entry.debit_afg)
            debit_afg_spin.setMinimum(0)
            layout.addRow("Debit AFG:", debit_afg_spin)
            
            credit_afg_spin = QDoubleSpinBox()
            credit_afg_spin.setValue(entry.credit_afg)
            credit_afg_spin.setMinimum(0)
            layout.addRow("Credit AFG:", credit_afg_spin)
            
            debit_usd_spin = QDoubleSpinBox()
            debit_usd_spin.setValue(entry.debit_usd)
            debit_usd_spin.setMinimum(0)
            layout.addRow("Debit USD:", debit_usd_spin)
            
            credit_usd_spin = QDoubleSpinBox()
            credit_usd_spin.setValue(entry.credit_usd)
            credit_usd_spin.setMinimum(0)
            layout.addRow("Credit USD:", credit_usd_spin)
            
            btn_layout = QHBoxLayout()
            save_btn = QPushButton("Save")
            cancel_btn = QPushButton("Cancel")
            btn_layout.addStretch()
            btn_layout.addWidget(save_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addRow(btn_layout)
            
            dialog.setLayout(layout)
            
            def save_changes():
                try:
                    entry.date = date_edit.dateTime().toPython()
                    entry.description = desc_edit.text()
                    entry.debit_afg = debit_afg_spin.value()
                    entry.credit_afg = credit_afg_spin.value()
                    entry.debit_usd = debit_usd_spin.value()
                    entry.credit_usd = credit_usd_spin.value()
                    
                    from egg_farm_system.database.db import DatabaseManager
                    db = DatabaseManager()
                    db.session.commit()
                    
                    dialog.accept()
                    self.load_data()
                    QMessageBox.information(self, tr("Success"), "Transaction updated successfully")
                except Exception as e:
                    logger.error(f"Error saving transaction: {e}")
                    QMessageBox.critical(self, tr("Error"), f"Failed to save transaction: {e}")
            
            save_btn.clicked.connect(save_changes)
            cancel_btn.clicked.connect(dialog.reject)
            
            dialog.exec()
        except Exception as e:
            logger.error(f"Error editing transaction: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to edit transaction: {e}")
    
    def delete_transaction(self, entry, row):
        """Delete transaction entry"""
        try:
            reply = QMessageBox.question(
                self, 
                tr("Confirm Delete"),
                f"Are you sure you want to delete this transaction?\n\n"
                f"Date: {format_value_for_ui(entry.date)}\n"
                f"Description: {entry.description}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                from egg_farm_system.database.db import DatabaseManager
                db = DatabaseManager()
                db.session.delete(entry)
                db.session.commit()
                
                self.load_data()
                QMessageBox.information(self, tr("Success"), "Transaction deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to delete transaction: {e}")
    
    def show_debit_dialog(self):
        """Show dialog to debit party account"""
        dialog = AddTransactionDialog(self, self.party, "Debit", self.ledger_manager, self.converter)
        if dialog.exec():
            self.load_data()
    
    def show_credit_dialog(self):
        """Show dialog to credit party account"""
        dialog = AddTransactionDialog(self, self.party, "Credit", self.ledger_manager, self.converter)
        if dialog.exec():
            self.load_data()


class CreditDebitDialog(QDialog):
    """Dialog for direct credit/debit entry"""
    
    def __init__(self, parent, party, transaction_type, ledger_manager, converter):
        super().__init__(parent)
        self.party = party
        self.transaction_type = transaction_type  # "Credit" or "Debit"
        self.ledger_manager = ledger_manager
        self.converter = converter
        
        self.setWindowTitle(f"{transaction_type} Account - {party.name}")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel(f"{self.transaction_type} Account")
        title.setStyleSheet("""
            font-size: 18pt;
            font-weight: 700;
            color: #8B4513;
        """)
        layout.addWidget(title)
        
        # Form
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
        self.amount_afg_spin.valueChanged.connect(self._on_afg_changed)
        form.addRow("Amount (AFG):", self.amount_afg_spin)
        
        self.amount_usd_spin = QDoubleSpinBox()
        self.amount_usd_spin.setMinimum(0.01)
        self.amount_usd_spin.setMaximum(999999999)
        self.amount_usd_spin.setDecimals(2)
        self.amount_usd_spin.setPrefix("$ ")
        self.amount_usd_spin.valueChanged.connect(self._on_usd_changed)
        form.addRow("Amount (USD):", self.amount_usd_spin)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText(f"Description for {self.transaction_type.lower()} entry...")
        form.addRow("Description:", self.description_edit)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        
        cancel_btn = create_button(tr("Cancel"), style='ghost')
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = create_button(f"Save {self.transaction_type}", style='primary')
        save_btn.setMinimumWidth(120)
        save_btn.setMinimumHeight(35)
        save_btn.clicked.connect(self.save_entry)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def _on_afg_changed(self, value):
        """Update USD when AFG changes"""
        if value > 0:
            usd_value = self.converter.afg_to_usd(value)
            self.amount_usd_spin.blockSignals(True)
            self.amount_usd_spin.setValue(usd_value)
            self.amount_usd_spin.blockSignals(False)
    
    def _on_usd_changed(self, value):
        """Update AFG when USD changes"""
        if value > 0:
            afg_value = self.converter.usd_to_afg(value)
            self.amount_afg_spin.blockSignals(True)
            self.amount_afg_spin.setValue(afg_value)
            self.amount_afg_spin.blockSignals(False)
    
    def save_entry(self):
        """Save credit/debit entry"""
        try:
            amount_afg = self.amount_afg_spin.value()
            amount_usd = self.amount_usd_spin.value()
            description = self.description_edit.toPlainText().strip()
            date = self.date_edit.date().toPython()
            
            if amount_afg <= 0 and amount_usd <= 0:
                QMessageBox.warning(self, tr("Validation"), "Please enter an amount")
                return
            
            if not description:
                description = f"Direct {self.transaction_type.lower()} entry"
            
            session = DatabaseManager.get_session()
            try:
                exchange_rate = self.converter.exchange_rate
                
                if self.transaction_type == "Debit":
                    # Debit party (party owes us)
                    self.ledger_manager.post_entry(
                        party_id=self.party.id,
                        date=date,
                        description=description,
                        debit_afg=amount_afg,
                        debit_usd=amount_usd,
                        credit_afg=0,
                        credit_usd=0,
                        exchange_rate_used=exchange_rate,
                        reference_type="Manual Entry",
                        reference_id=None,
                        session=session
                    )
                else:  # Credit
                    # Credit party (we owe party)
                    self.ledger_manager.post_entry(
                        party_id=self.party.id,
                        date=date,
                        description=description,
                        debit_afg=0,
                        debit_usd=0,
                        credit_afg=amount_afg,
                        credit_usd=amount_usd,
                        exchange_rate_used=exchange_rate,
                        reference_type="Manual Entry",
                        reference_id=None,
                        session=session
                    )
                
                session.commit()
                QMessageBox.information(self, tr("Success"), f"{self.transaction_type} entry saved successfully")
                self.accept()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error saving entry: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to save entry: {e}")

