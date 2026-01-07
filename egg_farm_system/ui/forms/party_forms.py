"""
Form widgets for parties
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog, QFormLayout,
    QTextEdit, QSizePolicy, QHeaderView, QToolButton, QAbstractItemView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from ui.widgets.datatable import DataTableWidget

from modules.parties import PartyManager
from modules.ledger import LedgerManager

class PartyFormWidget(QWidget):
    """Party management widget"""
    
    def __init__(self):
        super().__init__()
        self.party_manager = PartyManager()
        self.ledger_manager = LedgerManager()
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
        header_hbox.addWidget(new_party_btn)
        layout.addLayout(header_hbox)
        
        # Parties table
        self.table = DataTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.set_headers(["Name", "Phone", "Balance AFG", "Balance USD", "Actions"])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh_parties(self):
        """Refresh parties table"""
        try:
            parties = self.party_manager.get_all_parties()
            rows = []
            action_widgets = []
            for row, party in enumerate(parties):
                balance_afg = self.ledger_manager.get_party_balance(party.id, "AFG")
                balance_usd = self.ledger_manager.get_party_balance(party.id, "USD")
                rows.append([party.name, party.phone or "", f"{balance_afg:,.2f}", f"{balance_usd:,.2f}", ""])
                action_widgets.append((row, party))
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
            QMessageBox.critical(self, "Error", f"Failed to load parties: {e}")
    
    def add_party(self):
        """Add new party dialog"""
        dialog = PartyDialog(self, None, self.party_manager)
        if dialog.exec():
            self.refresh_parties()
    
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
    
    def delete_party(self, party):
        """Delete party"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{party.name}'?"
        )
        if reply == QMessageBox.Yes:
            try:
                self.party_manager.delete_party(party.id)
                self.refresh_parties()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")


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
        self.phone_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.notes_edit = QTextEdit()
        
        if party:
            self.name_edit.setText(party.name)
            self.phone_edit.setText(party.phone or "")
            self.address_edit.setText(party.address or "")
            self.notes_edit.setText(party.notes or "")
        
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Phone:", self.phone_edit)
        layout.addRow("Address:", self.address_edit)
        layout.addRow("Notes:", self.notes_edit)
        
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
    
    def save_party(self):
        """Save party"""
        try:
            name = self.name_edit.text().strip()
            phone = self.phone_edit.text().strip()
            address = self.address_edit.toPlainText().strip()
            notes = self.notes_edit.toPlainText().strip()
            
            if not name:
                QMessageBox.warning(self, "Validation", "Party name is required")
                return
            
            if self.party:
                self.party_manager.update_party(self.party.id, name, phone, address, notes)
            else:
                self.party_manager.create_party(name, phone, address, notes)
            
            QMessageBox.information(self, "Success", "Party saved successfully")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")
