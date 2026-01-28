"""Add / Edit Transaction dialog used by Party views."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QTextEdit, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from egg_farm_system.ui.widgets.jalali_date_edit import JalaliDateEdit
from datetime import date
from egg_farm_system.utils.i18n import tr
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.ui.ui_helpers import create_button

from typing import Optional
from PySide6.QtWidgets import QComboBox
from egg_farm_system.modules.parties import PartyManager


class AddTransactionDialog(QDialog):
    """Dialog to add a credit or debit transaction for a party.

    Usage: dialog = AddTransactionDialog(parent, party=None, transaction_type='Debit', ledger_manager=..., converter=..., party_manager=...)
    If `party` is None the dialog shows a party selector.
    """

    def __init__(self, parent, party: Optional[object] = None, transaction_type: str = "Debit",
                 ledger_manager=None, converter=None, party_manager: Optional[PartyManager] = None):
        super().__init__(parent)
        self.party = party
        self.transaction_type = transaction_type  # "Credit" or "Debit"
        self.ledger_manager = ledger_manager
        self.converter = converter
        self.party_manager = party_manager or PartyManager()

        title = f"{transaction_type} Account"
        if party:
            title = f"{transaction_type} Account - {getattr(party, 'name', '')}"
        self.setWindowTitle(tr(title))
        self.setMinimumWidth(520)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(tr(f"{self.transaction_type} Account"))
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        # Transaction type selector (always present so user can choose)
        self.transaction_type_combo = QComboBox()
        self.transaction_type_combo.addItems(["Debit", "Credit"])
        # default to provided transaction_type if available
        try:
            if self.transaction_type:
                idx = self.transaction_type_combo.findText(self.transaction_type)
                if idx >= 0:
                    self.transaction_type_combo.setCurrentIndex(idx)
        except Exception:
            pass
        form.addRow(tr("Transaction Type:"), self.transaction_type_combo)

        # Party selector when no party provided
        if self.party is None:
            self.party_combo = QComboBox()
            self.party_combo.setMinimumWidth(300)
            form.addRow(tr("Party:"), self.party_combo)
            # load parties
            try:
                for p in self.party_manager.get_all_parties():
                    self.party_combo.addItem(p.name, p.id)
            except Exception:
                pass

        self.date_edit = JalaliDateEdit(initial=date.today())
        form.addRow(tr("Date:"), self.date_edit)

        self.amount_afg_spin = QDoubleSpinBox()
        self.amount_afg_spin.setMinimum(0.01)
        self.amount_afg_spin.setMaximum(9_999_999_999)
        self.amount_afg_spin.setDecimals(2)
        self.amount_afg_spin.setPrefix("Afs ")
        form.addRow(tr("Amount (AFG):"), self.amount_afg_spin)

        self.amount_usd_spin = QDoubleSpinBox()
        self.amount_usd_spin.setMinimum(0.01)
        self.amount_usd_spin.setMaximum(9_999_999_999)
        self.amount_usd_spin.setDecimals(2)
        self.amount_usd_spin.setPrefix("$ ")
        form.addRow(tr("Amount (USD):"), self.amount_usd_spin)

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems(["Cash", "Credit"])
        self.payment_method_combo.setCurrentText("Cash")
        form.addRow(tr("Payment Method:"), self.payment_method_combo)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText(tr("Description (optional)"))
        form.addRow(tr("Description:"), self.description_edit)

        layout.addLayout(form)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        self.cancel_btn = create_button(tr("Cancel"), style='ghost')
        self.cancel_btn.clicked.connect(self.reject)
        btns.addWidget(self.cancel_btn)

        self.save_btn = create_button(tr("Save"), style='primary')
        self.save_btn.clicked.connect(self.save_entry)
        btns.addWidget(self.save_btn)

        layout.addLayout(btns)

    def _on_afg_changed(self, value: float):
        if value > 0 and getattr(self.converter, 'exchange_rate', None):
            usd = self.converter.afg_to_usd(value)
            self.amount_usd_spin.blockSignals(True)
            self.amount_usd_spin.setValue(round(usd, 2))
            self.amount_usd_spin.blockSignals(False)

    def _on_usd_changed(self, value: float):
        if value > 0 and getattr(self.converter, 'exchange_rate', None):
            afg = self.converter.usd_to_afg(value)
            self.amount_afg_spin.blockSignals(True)
            self.amount_afg_spin.setValue(round(afg, 2))
            self.amount_afg_spin.blockSignals(False)

    def _validate(self) -> bool:
        if self.amount_afg_spin.value() <= 0 and self.amount_usd_spin.value() <= 0:
            QMessageBox.warning(self, tr("Validation Error"), tr("Please enter an amount"))
            return False
        return True

    def save_entry(self):
        if not self._validate():
            return

        amount_afg = self.amount_afg_spin.value()
        amount_usd = self.amount_usd_spin.value()
        description = self.description_edit.toPlainText().strip() or f"Direct {self.transaction_type.lower()} entry"
        date = self.date_edit.date()
        payment_method = self.payment_method_combo.currentText()

        session = DatabaseManager.get_session()
        try:
            exchange_rate = getattr(self.converter, 'exchange_rate', None)

            # resolve transaction type from UI (if present) otherwise use passed value
            try:
                transaction_type = self.transaction_type_combo.currentText()
            except Exception:
                transaction_type = self.transaction_type

            # resolve party id
            if self.party is not None:
                party_id = getattr(self.party, 'id', None)
            else:
                try:
                    party_id = self.party_combo.currentData()
                except Exception:
                    party_id = None

            if not party_id:
                QMessageBox.warning(self, tr("Validation Error"), tr("Please select a party."))
                return

            if transaction_type == "Debit":
                self.ledger_manager.post_entry(
                    party_id=party_id,
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
            else:
                self.ledger_manager.post_entry(
                    party_id=party_id,
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
            
            # If payment method is Cash, create a payment record for cash flow tracking
            if payment_method == "Cash":
                from egg_farm_system.database.models import Payment
                cash_payment = Payment(
                    party_id=party_id,
                    date=date,
                    amount_afg=amount_afg,
                    amount_usd=amount_usd,
                    payment_type="Received" if transaction_type == "Debit" else "Paid",
                    payment_method="Cash",
                    reference=description,
                    exchange_rate_used=exchange_rate
                )
                session.add(cash_payment)

            session.commit()
            QMessageBox.information(self, tr("Success"), tr("Saved successfully"))
            self.accept()

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, tr("Error"), f"{tr('Failed to save')}: {str(e)}")
        finally:
            session.close()
