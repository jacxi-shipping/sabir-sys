"""
Form widgets for parties
"""
from egg_farm_system.utils.i18n import tr

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout,
    QTextEdit, QSizePolicy, QHeaderView, QToolButton, QAbstractItemView,
    QComboBox, QDateTimeEdit, QDoubleSpinBox, QGroupBox
)
from PySide6.QtCore import Qt, QSize, QTimer, QDateTime
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from egg_farm_system.ui.widgets.datatable import DataTableWidget
from egg_farm_system.ui.widgets.loading_overlay import LoadingOverlay
from egg_farm_system.ui.widgets.success_message import SuccessMessage
from egg_farm_system.ui.widgets.keyboard_shortcuts import KeyboardShortcuts
from egg_farm_system.utils.error_handler import ErrorHandler

from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.ledger import LedgerManager
from egg_farm_system.utils.currency import CurrencyConverter
from egg_farm_system.database.db import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class PartyFormWidget(QWidget):
    """Party management widget"""
    
    def __init__(self):
        super().__init__()
        # self.party_manager removed - using context manager
        self.ledger_manager = LedgerManager()
        self.converter = CurrencyConverter()
        self.loading_overlay = LoadingOverlay(self)
        self.init_ui()
        self.refresh_parties()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Header: title left, actions right
        header_hbox = QHBoxLayout()
        title = QLabel(tr("Party Management"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_hbox.addWidget(title)
        header_hbox.addStretch()
        transaction_btn = QPushButton(tr("Add Transaction"))
        transaction_btn.clicked.connect(self.add_transaction)
        transaction_btn.setToolTip(tr("Add credit/debit transaction to a party"))
        header_hbox.addWidget(transaction_btn)
        new_party_btn = QPushButton(tr("Add New Party"))
        new_party_btn.clicked.connect(self.add_party)
        new_party_btn.setToolTip(tr("Add a new party (Ctrl+N)"))
        header_hbox.addWidget(new_party_btn)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.add_standard_shortcuts(self, {
            'new': self.add_party,
            'refresh': self.refresh_parties
        })
        layout.addLayout(header_hbox)
        
        # Parties table
        self.table = DataTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.set_headers(["Name", "Phone", "Balance AFG", "Balance USD", "Actions"])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh_parties(self):
        """Refresh parties table"""
        self.loading_overlay.set_message("Loading parties...")
        self.loading_overlay.show()
        QTimer.singleShot(50, self._do_refresh_parties)
    
    def _do_refresh_parties(self):
        """Perform the actual refresh"""
        try:
            with PartyManager() as pm:
                parties = pm.get_all_parties()
                rows = []
                action_widgets = []
                for row, party in enumerate(parties):
                    balance_afg = self.ledger_manager.get_party_balance(party.id, "AFG")
                    balance_usd = self.ledger_manager.get_party_balance(party.id, "USD")
                    rows.append([party.name, party.phone or "", f"{balance_afg:,.2f}", f"{balance_usd:,.2f}", ""])
                    action_widgets.append((row, party.id, party.name, balance_afg, balance_usd)) # Store minimal data
                
            self.loading_overlay.hide()
            self.table.set_rows(rows)
            
            # Apply color formatting to balance columns
            from PySide6.QtGui import QColor
            for row_idx, party_id, party_name, balance_afg, balance_usd in action_widgets:
                # Balance AFG column (column 2)
                afg_item = self.table.model.item(row_idx, 2)
                if afg_item:
                    if balance_afg < 0:
                        afg_item.setForeground(QColor("#C62828"))  # Red for negative
                    elif balance_afg > 0:
                        afg_item.setForeground(QColor("#2E7D32"))  # Green for positive
                    else:
                        afg_item.setForeground(QColor("#000000"))  # Black for zero
                
                # Balance USD column (column 3)
                usd_item = self.table.model.item(row_idx, 3)
                if usd_item:
                    if balance_usd < 0:
                        usd_item.setForeground(QColor("#C62828"))  # Red for negative
                    elif balance_usd > 0:
                        usd_item.setForeground(QColor("#2E7D32"))  # Green for positive
                    else:
                        usd_item.setForeground(QColor("#000000"))  # Black for zero
            from egg_farm_system.config import get_asset_path
            view_icon = Path(get_asset_path('icon_view.svg'))
            edit_icon = Path(get_asset_path('icon_edit.svg'))
            delete_icon = Path(get_asset_path('icon_delete.svg'))
            
            # Re-fetch party for actions if needed, or pass data struct.
            # Lambda capture needs to be careful.
            # Using Party object from closed session is risky. We should fetch fresh in action or pass ID.
            # Here I'll just pass IDs to helper methods which will fetch fresh.
            
            for row_idx, party_id, party_name, balance_afg, balance_usd in action_widgets:
                view_btn = QToolButton()
                view_btn.setAutoRaise(True)
                view_btn.setFixedSize(28, 28)
                if view_icon.exists():
                    view_btn.setIcon(QIcon(str(view_icon)))
                    view_btn.setIconSize(QSize(20, 20))
                view_btn.setToolTip(tr('View'))
                view_btn.clicked.connect(lambda checked, pid=party_id: self.view_party(pid))

                edit_btn = QToolButton()
                edit_btn.setAutoRaise(True)
                edit_btn.setFixedSize(28, 28)
                if edit_icon.exists():
                    edit_btn.setIcon(QIcon(str(edit_icon)))
                    edit_btn.setIconSize(QSize(20, 20))
                edit_btn.setToolTip(tr('Edit'))
                edit_btn.clicked.connect(lambda checked, pid=party_id: self.edit_party(pid))

                delete_btn = QToolButton()
                delete_btn.setAutoRaise(True)
                delete_btn.setFixedSize(28, 28)
                if delete_icon.exists():
                    delete_btn.setIcon(QIcon(str(delete_icon)))
                    delete_btn.setIconSize(QSize(20, 20))
                delete_btn.setToolTip(tr('Delete'))
                delete_btn.clicked.connect(lambda checked, pid=party_id, pname=party_name: self.delete_party(pid, pname))

                container = QWidget()
                container.setMinimumHeight(36)
                container.setMaximumHeight(36)
                l = QHBoxLayout(container)
                l.setContentsMargins(4, 2, 4, 2)
                l.setSpacing(4)
                l.addWidget(view_btn)
                l.addWidget(edit_btn)
                l.addWidget(delete_btn)
                l.addStretch()
                self.table.set_cell_widget(row_idx, 4, container)
            
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, tr("Error"), f"Failed to load parties: {str(e)}")
    
    def add_transaction(self):
        """Add credit/debit transaction dialog"""
        from egg_farm_system.ui.forms.add_transaction_dialog import AddTransactionDialog
        # We pass PartyManager class or create new one inside. 
        # AddTransactionDialog seems to take party_manager instance.
        with PartyManager() as pm:
            dialog = AddTransactionDialog(self, party=None, transaction_type="Debit", ledger_manager=self.ledger_manager, converter=self.converter, party_manager=pm)
            if dialog.exec():
                self.refresh_parties()
                success_msg = SuccessMessage(self, "Transaction recorded successfully")
                success_msg.show()
    
    def add_party(self):
        """Add new party dialog"""
        with PartyManager() as pm:
            dialog = PartyDialog(self, None, pm)
            if dialog.exec():
                self.refresh_parties()
                # success message handled in dialog
    
    def view_party(self, party_id):
        """View party ledger with premium dialog"""
        from egg_farm_system.ui.widgets.party_view_dialog import PartyViewDialog
        with PartyManager() as pm:
            party = pm.get_party_by_id(party_id)
            if party:
                dialog = PartyViewDialog(self, party)
                dialog.exec()
    
    def edit_party(self, party_id):
        """Edit party dialog"""
        with PartyManager() as pm:
            party = pm.get_party_by_id(party_id)
            if party:
                dialog = PartyDialog(self, party, pm)
                if dialog.exec():
                    self.refresh_parties()
                    # success message handled in dialog
    
    def delete_party(self, party_id, party_name):
        """Delete party with detailed confirmation"""
        # Get party balance info
        balance_afg = self.ledger_manager.get_party_balance(party_id, "AFG")
        balance_usd = self.ledger_manager.get_party_balance(party_id, "USD")
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(tr("Confirm Delete"))
        msg.setText(f"Are you sure you want to delete the party '{party_name}'?")
        
        balance_info = ""
        if balance_afg != 0 or balance_usd != 0:
            balance_info = (
                f"\n\nCurrent Balance:\n"
                f"AFG: {balance_afg:,.2f}\n"
                f"USD: {balance_usd:,.2f}\n\n"
                "⚠️ Warning: This party has an outstanding balance. "
                "Deleting will remove all transaction history."
            )
        
        # Can't get other details like phone/address easily without querying again, skipping for now or query
        with PartyManager() as pm:
            party = pm.get_party_by_id(party_id)
            if not party: return

            msg.setInformativeText(
                f"Phone: {party.phone or 'N/A'}\n"
                f"Address: {party.address or 'N/A'}\n"
                f"{balance_info}\n"
                "This action cannot be undone."
            )
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            
            if msg.exec() == QMessageBox.Yes:
                try:
                    self.loading_overlay.set_message("Deleting party...")
                    self.loading_overlay.show()
                    # Need to perform deletion in a way that doesn't block UI but here we are in same thread
                    # For safety, doing it directly
                    pm.delete_party(party.id)
                    self.loading_overlay.hide()
                    self.refresh_parties()
                    success_msg = SuccessMessage(self, f"Party '{party_name}' deleted successfully")
                    success_msg.show()
                except Exception as e:
                    self.loading_overlay.hide()
                    QMessageBox.critical(
                        self, 
                        tr("Delete Failed"), 
                        f"Failed to delete party.\n\nError: {str(e)}\n\nPlease try again."
                    )


class PartyDialog(QDialog):
    """Party creation/edit dialog"""
    
    def __init__(self, parent, party, party_manager):
        super().__init__(parent)
        self.party = party
        self.party_manager = party_manager
        
        self.setWindowTitle("Party Details" if party else "New Party")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("e.g., ABC Company, John Doe"))
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText(tr("e.g., +93 700 123 456"))
        self.address_edit = QTextEdit()
        self.address_edit.setPlaceholderText(tr("Enter full address..."))
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(tr("Any additional notes..."))
        
        if party:
            self.name_edit.setText(party.name)
            self.phone_edit.setText(party.phone or "")
            self.address_edit.setText(party.address or "")
            self.notes_edit.setText(party.notes or "")
        
        # Required field indicators and tooltips
        self.name_edit.setToolTip(tr("Enter the party name (required)"))
        self.phone_edit.setToolTip(tr("Enter phone number (optional)"))
        self.address_edit.setToolTip(tr("Enter address (optional)"))
        self.notes_edit.setToolTip(tr("Enter any additional notes (optional)"))
        
        name_label = QLabel(tr("Name: <span style='color: red;'>*</span>"))
        name_label.setTextFormat(Qt.RichText)
        phone_label = QLabel(tr("Phone:"))
        address_label = QLabel(tr("Address:"))
        notes_label = QLabel(tr("Notes:"))
        
        layout.addRow(name_label, self.name_edit)
        layout.addRow(phone_label, self.phone_edit)
        layout.addRow(address_label, self.address_edit)
        layout.addRow(notes_label, self.notes_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.addStretch()
        
        save_btn = QPushButton(tr("Save"))
        save_btn.setMinimumWidth(100)
        save_btn.setMinimumHeight(35)
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setMinimumHeight(35)
        
        save_btn.clicked.connect(self.save_party)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.SAVE, self.save_party)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.CLOSE, self.reject)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.ESCAPE, self.reject)
    
    def save_party(self):
        """Save party with loading indicator and success feedback"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self, 
                tr("Validation Error"), 
                "Party name is required. Please enter a name for the party."
            )
            return
        
        # Show loading overlay
        loading = LoadingOverlay(self, "Saving party...")
        loading.show()
        QTimer.singleShot(50, lambda: self._do_save_party(loading))
    
    def _do_save_party(self, loading):
        """Perform the actual save"""
        try:
            name = self.name_edit.text().strip()
            phone = self.phone_edit.text().strip()
            address = self.address_edit.toPlainText().strip()
            notes = self.notes_edit.toPlainText().strip()
            
            if self.party:
                self.party_manager.update_party(self.party.id, name, phone, address, notes)
                message = f"Party '{name}' updated successfully."
            else:
                self.party_manager.create_party(name, phone, address, notes)
                message = f"Party '{name}' created successfully."
            
            loading.hide()
            loading.deleteLater()
            
            # Show success message
            success_msg = SuccessMessage(self, message)
            success_msg.show()
            QTimer.singleShot(100, lambda: self.accept())
        except ValueError as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.warning(self, tr("Validation Error"), f"Invalid input: {str(e)}")
        except Exception as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.critical(
                self, 
                tr("Save Failed"), 
                f"Failed to save party.\n\nError: {str(e)}\n\nPlease check your input and try again."
            )


class PartyTransactionDialog(QDialog):
    """Dialog for adding credit/debit transactions to parties"""
    
    def __init__(self, parent, party_manager, ledger_manager):
        super().__init__(parent)
        self.party_manager = party_manager
        self.ledger_manager = ledger_manager
        self.converter = CurrencyConverter()
        self.exchange_rate = self.converter.get_exchange_rate()
        
        self.setWindowTitle(tr("Add Party Transaction"))
        self.setMinimumSize(550, 500)
        self.setModal(True)
        
        self.init_ui()
        self.load_parties()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize UI elements"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel(tr("Party Transaction"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Transaction Details Group
        transaction_group = QGroupBox("Transaction Details")
        transaction_layout = QFormLayout()
        transaction_layout.setSpacing(10)
        transaction_layout.setLabelAlignment(Qt.AlignRight)
        
        # Party Selection
        self.party_combo = QComboBox()
        self.party_combo.setMinimumWidth(250)
        transaction_layout.addRow("Party:", self.party_combo)
        
        # Current Balance Display
        self.balance_label = QLabel(tr("Current Balance: N/A"))
        self.balance_label.setFont(QFont("Arial", 10))
        self.balance_label.setStyleSheet("color: #2c3e50; font-weight: bold; padding: 5px;")
        transaction_layout.addRow("Balance:", self.balance_label)
        
        # Transaction Type
        self.transaction_type_combo = QComboBox()
        self.transaction_type_combo.addItems(["Debit", "Credit"])
        self.transaction_type_combo.setMinimumWidth(250)
        self.transaction_type_combo.setToolTip(
            "Debit: Party owes us (money coming in)\n"
            "Credit: We owe party (money going out)"
        )
        transaction_layout.addRow("Transaction Type:", self.transaction_type_combo)
        
        # Date
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDateTime(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_edit.setMinimumWidth(250)
        transaction_layout.addRow("Date:", self.date_edit)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText(tr("e.g., Manual adjustment, Payment received, etc."))
        self.description_edit.setMinimumWidth(250)
        transaction_layout.addRow("Description:", self.description_edit)
        
        transaction_group.setLayout(transaction_layout)
        main_layout.addWidget(transaction_group)
        
        # Amount Details Group
        amount_group = QGroupBox("Amount Details")
        amount_layout = QFormLayout()
        amount_layout.setSpacing(10)
        amount_layout.setLabelAlignment(Qt.AlignRight)
        
        # Amount AFG
        self.amount_afg_spin = QDoubleSpinBox()
        self.amount_afg_spin.setMinimum(0.00)
        self.amount_afg_spin.setMaximum(100000000.00)
        self.amount_afg_spin.setDecimals(2)
        self.amount_afg_spin.setSingleStep(100.0)
        self.amount_afg_spin.setSuffix(" AFG")
        self.amount_afg_spin.setMinimumWidth(250)
        amount_layout.addRow("Amount (AFG):", self.amount_afg_spin)
        
        # Amount USD
        self.amount_usd_spin = QDoubleSpinBox()
        self.amount_usd_spin.setMinimum(0.00)
        self.amount_usd_spin.setMaximum(1000000.00)
        self.amount_usd_spin.setDecimals(2)
        self.amount_usd_spin.setSingleStep(1.0)
        self.amount_usd_spin.setSuffix(" USD")
        self.amount_usd_spin.setMinimumWidth(250)
        amount_layout.addRow("Amount (USD):", self.amount_usd_spin)
        
        # Exchange Rate Info
        exchange_info = QLabel(f"Exchange Rate: {self.exchange_rate:.2f} AFG = 1 USD")
        exchange_info.setFont(QFont("Arial", 9))
        exchange_info.setStyleSheet("color: #7f8c8d;")
        amount_layout.addRow("", exchange_info)
        
        amount_group.setLayout(amount_layout)
        main_layout.addWidget(amount_group)
        
        # Effect Preview Group
        preview_group = QGroupBox("Balance After Transaction")
        preview_layout = QFormLayout()
        preview_layout.setSpacing(10)
        preview_layout.setLabelAlignment(Qt.AlignRight)
        
        self.new_balance_afg_label = QLabel(tr("0.00 AFG"))
        self.new_balance_afg_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.new_balance_afg_label.setStyleSheet("color: #27ae60; padding: 5px;")
        preview_layout.addRow("New Balance (AFG):", self.new_balance_afg_label)
        
        self.new_balance_usd_label = QLabel(tr("0.00 USD"))
        self.new_balance_usd_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.new_balance_usd_label.setStyleSheet("color: #2980b9; padding: 5px;")
        preview_layout.addRow("New Balance (USD):", self.new_balance_usd_label)
        
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton(tr("Cancel"))
        self.cancel_btn.setMinimumSize(120, 40)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton(tr("Save Transaction"))
        self.save_btn.setMinimumSize(150, 40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.save_btn.clicked.connect(self.save_transaction)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def load_parties(self):
        """Load parties into combo box"""
        parties = self.party_manager.get_all_parties()
        for party in parties:
            self.party_combo.addItem(party.name, party.id)
        if parties:
            self.update_balance_display()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.party_combo.currentIndexChanged.connect(self.update_balance_display)
        self.transaction_type_combo.currentIndexChanged.connect(self.update_preview)
        self.amount_afg_spin.valueChanged.connect(self.on_amount_afg_changed)
        self.amount_usd_spin.valueChanged.connect(self.on_amount_usd_changed)
        self.amount_afg_spin.valueChanged.connect(self.update_preview)
        self.amount_usd_spin.valueChanged.connect(self.update_preview)
    
    def update_balance_display(self):
        """Update current balance display"""
        party_id = self.party_combo.currentData()
        if party_id:
            balance_afg = self.ledger_manager.get_party_balance(party_id, "AFG")
            balance_usd = self.ledger_manager.get_party_balance(party_id, "USD")
            
            balance_text = f"AFG: {balance_afg:,.2f} | USD: {balance_usd:,.2f}"
            if balance_afg > 0:
                balance_text += " (Party owes us)"
                self.balance_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 5px;")
            elif balance_afg < 0:
                balance_text += " (We owe party)"
                self.balance_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px;")
            else:
                balance_text += " (Balanced)"
                self.balance_label.setStyleSheet("color: #7f8c8d; font-weight: bold; padding: 5px;")
            
            self.balance_label.setText(balance_text)
            self.update_preview()
        else:
            self.balance_label.setText(tr("Current Balance: N/A"))
            self.balance_label.setStyleSheet("color: #7f8c8d;")
    
    def on_amount_afg_changed(self):
        """Auto-calculate USD from AFG"""
        if self.amount_afg_spin.value() > 0 and self.exchange_rate > 0:
            self.amount_usd_spin.blockSignals(True)
            calculated_usd = self.amount_afg_spin.value() / self.exchange_rate
            self.amount_usd_spin.setValue(round(calculated_usd, 2))
            self.amount_usd_spin.blockSignals(False)
    
    def on_amount_usd_changed(self):
        """Auto-calculate AFG from USD"""
        if self.amount_usd_spin.value() > 0 and self.exchange_rate > 0:
            self.amount_afg_spin.blockSignals(True)
            calculated_afg = self.amount_usd_spin.value() * self.exchange_rate
            self.amount_afg_spin.setValue(round(calculated_afg, 2))
            self.amount_afg_spin.blockSignals(False)
    
    def update_preview(self):
        """Update balance preview after transaction"""
        party_id = self.party_combo.currentData()
        if not party_id:
            self.new_balance_afg_label.setText(tr("0.00 AFG"))
            self.new_balance_usd_label.setText(tr("0.00 USD"))
            return
        
        current_balance_afg = self.ledger_manager.get_party_balance(party_id, "AFG")
        current_balance_usd = self.ledger_manager.get_party_balance(party_id, "USD")
        
        amount_afg = self.amount_afg_spin.value()
        amount_usd = self.amount_usd_spin.value()
        transaction_type = self.transaction_type_combo.currentText()
        
        # Calculate new balance
        if transaction_type == "Debit":
            # Debit increases what party owes us (positive balance)
            new_balance_afg = current_balance_afg + amount_afg
            new_balance_usd = current_balance_usd + amount_usd
        else:  # Credit
            # Credit decreases what party owes us (or increases what we owe)
            new_balance_afg = current_balance_afg - amount_afg
            new_balance_usd = current_balance_usd - amount_usd
        
        self.new_balance_afg_label.setText(f"{new_balance_afg:,.2f} AFG")
        self.new_balance_usd_label.setText(f"{new_balance_usd:,.2f} USD")
        
        # Color code based on new balance
        if new_balance_afg > 0:
            self.new_balance_afg_label.setStyleSheet("color: #27ae60; padding: 5px; font-weight: bold;")
        elif new_balance_afg < 0:
            self.new_balance_afg_label.setStyleSheet("color: #e74c3c; padding: 5px; font-weight: bold;")
        else:
            self.new_balance_afg_label.setStyleSheet("color: #7f8c8d; padding: 5px; font-weight: bold;")
    
    def save_transaction(self):
        """Save the transaction"""
        try:
            # Validation
            party_id = self.party_combo.currentData()
            if not party_id:
                QMessageBox.warning(self, tr("Validation Error"), "Please select a party.")
                return
            
            description = self.description_edit.text().strip()
            if not description:
                QMessageBox.warning(self, tr("Validation Error"), "Please enter a description for the transaction.")
                return
            
            amount_afg = self.amount_afg_spin.value()
            amount_usd = self.amount_usd_spin.value()
            
            if amount_afg <= 0 and amount_usd <= 0:
                QMessageBox.warning(self, tr("Validation Error"), "At least one amount (AFG or USD) must be greater than 0.")
                return
            
            transaction_type = self.transaction_type_combo.currentText()
            date = self.date_edit.dateTime().toPython()
            
            # Post to ledger
            session = DatabaseManager.get_session()
            try:
                if transaction_type == "Debit":
                    # Debit: Party owes us (money coming in)
                    self.ledger_manager.post_entry(
                        party_id=party_id,
                        date=date,
                        description=description,
                        debit_afg=amount_afg,
                        debit_usd=amount_usd,
                        credit_afg=0,
                        credit_usd=0,
                        exchange_rate_used=self.exchange_rate,
                        reference_type="Manual",
                        reference_id=None,
                        session=session
                    )
                else:  # Credit
                    # Credit: We owe party (money going out)
                    self.ledger_manager.post_entry(
                        party_id=party_id,
                        date=date,
                        description=description,
                        debit_afg=0,
                        debit_usd=0,
                        credit_afg=amount_afg,
                        credit_usd=amount_usd,
                        exchange_rate_used=self.exchange_rate,
                        reference_type="Manual",
                        reference_id=None,
                        session=session
                    )
                
                session.commit()
                QMessageBox.information(self, tr("Success"), f"{transaction_type} transaction recorded successfully!")
                self.accept()
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
        
        except ValueError as ve:
            QMessageBox.warning(self, tr("Validation Error"), str(ve))
        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to save transaction: {str(e)}")
