"""
Form widgets for parties
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout,
    QTextEdit, QSizePolicy, QHeaderView, QToolButton, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from egg_farm_system.ui.widgets.datatable import DataTableWidget
from egg_farm_system.ui.widgets.loading_overlay import LoadingOverlay
from egg_farm_system.ui.widgets.success_message import SuccessMessage
from egg_farm_system.ui.widgets.keyboard_shortcuts import KeyboardShortcuts
from egg_farm_system.utils.error_handler import ErrorHandler

from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.ledger import LedgerManager

class PartyFormWidget(QWidget):
    """Party management widget"""
    
    def __init__(self):
        super().__init__()
        self.party_manager = PartyManager()
        self.ledger_manager = LedgerManager()
        self.loading_overlay = LoadingOverlay(self)
        self.init_ui()
        self.refresh_parties()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Header: title left, actions right
        header_hbox = QHBoxLayout()
        title = QLabel("Party Management")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_hbox.addWidget(title)
        header_hbox.addStretch()
        new_party_btn = QPushButton("Add New Party")
        new_party_btn.clicked.connect(self.add_party)
        new_party_btn.setToolTip("Add a new party (Ctrl+N)")
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
            parties = self.party_manager.get_all_parties()
            rows = []
            action_widgets = []
            for row, party in enumerate(parties):
                balance_afg = self.ledger_manager.get_party_balance(party.id, "AFG")
                balance_usd = self.ledger_manager.get_party_balance(party.id, "USD")
                rows.append([party.name, party.phone or "", f"{balance_afg:,.2f}", f"{balance_usd:,.2f}", ""])
                action_widgets.append((row, party))
            self.loading_overlay.hide()
            self.table.set_rows(rows)
            asset_dir = Path(__file__).parent.parent.parent / 'assets'
            view_icon = asset_dir / 'icon_view.svg'
            edit_icon = asset_dir / 'icon_edit.svg'
            delete_icon = asset_dir / 'icon_delete.svg'
            for row_idx, party in action_widgets:
                view_btn = QToolButton()
                view_btn.setAutoRaise(True)
                view_btn.setFixedSize(28, 28)
                if view_icon.exists():
                    view_btn.setIcon(QIcon(str(view_icon)))
                    view_btn.setIconSize(QSize(20, 20))
                view_btn.setToolTip('View')
                view_btn.clicked.connect(lambda checked, p=party: self.view_party(p))

                edit_btn = QToolButton()
                edit_btn.setAutoRaise(True)
                edit_btn.setFixedSize(28, 28)
                if edit_icon.exists():
                    edit_btn.setIcon(QIcon(str(edit_icon)))
                    edit_btn.setIconSize(QSize(20, 20))
                edit_btn.setToolTip('Edit')
                edit_btn.clicked.connect(lambda checked, p=party: self.edit_party(p))

                delete_btn = QToolButton()
                delete_btn.setAutoRaise(True)
                delete_btn.setFixedSize(28, 28)
                if delete_icon.exists():
                    delete_btn.setIcon(QIcon(str(delete_icon)))
                    delete_btn.setIconSize(QSize(20, 20))
                delete_btn.setToolTip('Delete')
                delete_btn.clicked.connect(lambda checked, p=party: self.delete_party(p))

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
            
            # Data rows have been populated via `set_rows` above and action
            # widgets were attached using `set_cell_widget` already. No further
            # per-cell population is required for the DataTableWidget.
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, "Error", f"Failed to load parties: {str(e)}")
    
    def add_party(self):
        """Add new party dialog"""
        dialog = PartyDialog(self, None, self.party_manager)
        if dialog.exec():
            self.refresh_parties()
            success_msg = SuccessMessage(self, "Party added successfully")
            success_msg.show()
    
    def view_party(self, party):
        """View party ledger with premium dialog"""
        from egg_farm_system.ui.widgets.party_view_dialog import PartyViewDialog
        dialog = PartyViewDialog(self, party)
        dialog.exec()
    
    def edit_party(self, party):
        """Edit party dialog"""
        dialog = PartyDialog(self, party, self.party_manager)
        if dialog.exec():
            self.refresh_parties()
            success_msg = SuccessMessage(self, "Party updated successfully")
            success_msg.show()
    
    def delete_party(self, party):
        """Delete party with detailed confirmation"""
        # Get party balance info
        balance_afg = self.ledger_manager.get_party_balance(party.id, "AFG")
        balance_usd = self.ledger_manager.get_party_balance(party.id, "USD")
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Confirm Delete")
        msg.setText(f"Are you sure you want to delete the party '{party.name}'?")
        
        balance_info = ""
        if balance_afg != 0 or balance_usd != 0:
            balance_info = (
                f"\n\nCurrent Balance:\n"
                f"AFG: {balance_afg:,.2f}\n"
                f"USD: {balance_usd:,.2f}\n\n"
                "⚠️ Warning: This party has an outstanding balance. "
                "Deleting will remove all transaction history."
            )
        
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
                party_name = party.name
                self.loading_overlay.set_message("Deleting party...")
                self.loading_overlay.show()
                QTimer.singleShot(50, lambda: self._do_delete_party(party, party_name))
            except Exception as e:
                self.loading_overlay.hide()
                QMessageBox.critical(self, "Delete Failed", f"Failed to delete party: {str(e)}")
    
    def _do_delete_party(self, party, party_name):
        """Perform the actual delete"""
        try:
            self.party_manager.delete_party(party.id)
            self.loading_overlay.hide()
            self.refresh_parties()
            success_msg = SuccessMessage(self, f"Party '{party_name}' deleted successfully")
            success_msg.show()
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(
                self, 
                "Delete Failed", 
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
        self.name_edit.setPlaceholderText("e.g., ABC Company, John Doe")
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("e.g., +93 700 123 456")
        self.address_edit = QTextEdit()
        self.address_edit.setPlaceholderText("Enter full address...")
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Any additional notes...")
        
        if party:
            self.name_edit.setText(party.name)
            self.phone_edit.setText(party.phone or "")
            self.address_edit.setText(party.address or "")
            self.notes_edit.setText(party.notes or "")
        
        # Required field indicators and tooltips
        self.name_edit.setToolTip("Enter the party name (required)")
        self.phone_edit.setToolTip("Enter phone number (optional)")
        self.address_edit.setToolTip("Enter address (optional)")
        self.notes_edit.setToolTip("Enter any additional notes (optional)")
        
        name_label = QLabel("Name: <span style='color: red;'>*</span>")
        name_label.setTextFormat(Qt.RichText)
        phone_label = QLabel("Phone:")
        address_label = QLabel("Address:")
        notes_label = QLabel("Notes:")
        
        layout.addRow(name_label, self.name_edit)
        layout.addRow(phone_label, self.phone_edit)
        layout.addRow(address_label, self.address_edit)
        layout.addRow(notes_label, self.notes_edit)
        
        # Buttons
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
                "Validation Error", 
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
            QMessageBox.warning(self, "Validation Error", f"Invalid input: {str(e)}")
        except Exception as e:
            loading.hide()
            loading.deleteLater()
            QMessageBox.critical(
                self, 
                "Save Failed", 
                f"Failed to save party.\n\nError: {str(e)}\n\nPlease check your input and try again."
            )
