from egg_farm_system.utils.i18n import tr
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QDoubleSpinBox, QComboBox, QDateTimeEdit, QMessageBox, QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QDateTime, Signal
from PySide6.QtGui import QFont

from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.feed_mill import RawMaterialManager
from egg_farm_system.modules.sales import RawMaterialSaleManager
from egg_farm_system.utils.currency import CurrencyConverter
from egg_farm_system.ui.ui_helpers import create_button

logger = logging.getLogger(__name__)


class RawMaterialSaleDialog(QDialog):
    """Clean, focused dialog for selling raw materials."""

    sale_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Sell Raw Material"))
        self.setModal(True)
        self.setMinimumWidth(560)

        self.converter = CurrencyConverter()
        self.exchange_rate = self.converter.get_exchange_rate() or 1.0

        self._build_ui()
        self._load_data()
        self._connect()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        title = QLabel(tr("Sell Raw Material"))
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(12)

        # Date
        self.date_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.date_edit.setCalendarPopup(True)
        form.addRow(tr("Date:"), self.date_edit)

        # Customer
        self.party_combo = QComboBox()
        self.party_combo.setEditable(False)
        form.addRow(tr("Customer:"), self.party_combo)

        # Material + unit/stock on same row
        self.raw_material_combo = QComboBox()
        self.raw_material_combo.setEditable(False)
        form.addRow(tr("Raw Material:"), self.raw_material_combo)

        # Available stock (read-only label)
        self.available_label = QLabel(tr("Available: N/A"))
        form.addRow(tr("Stock Info:"), self.available_label)

        # Quantity
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setMinimum(0.0)
        self.quantity_spin.setMaximum(1_000_000)
        self.quantity_spin.setDecimals(2)
        self.quantity_spin.setSingleStep(1.0)
        form.addRow(tr("Quantity:"), self.quantity_spin)

        # Rate AFG / USD
        self.rate_afg_spin = QDoubleSpinBox()
        self.rate_afg_spin.setMinimum(0.0)
        self.rate_afg_spin.setMaximum(1_000_000)
        self.rate_afg_spin.setDecimals(2)
        self.rate_afg_spin.setSuffix(" AFG")

        self.rate_usd_spin = QDoubleSpinBox()
        self.rate_usd_spin.setMinimum(0.0)
        self.rate_usd_spin.setMaximum(1_000_000)
        self.rate_usd_spin.setDecimals(2)
        self.rate_usd_spin.setSuffix(" USD")

        rate_row = QHBoxLayout()
        rate_row.addWidget(self.rate_afg_spin)
        rate_row.addWidget(self.rate_usd_spin)
        rate_container = QLabel()
        rate_container.setLayout(rate_row)
        form.addRow(tr("Rate:"), rate_container)

        # Payment method
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([tr("Cash"), tr("Credit")])
        form.addRow(tr("Payment Method:"), self.payment_method_combo)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(tr("Enter any additional notes (optional)"))
        self.notes_edit.setMaximumHeight(80)
        form.addRow(tr("Notes:"), self.notes_edit)

        main.addLayout(form)

        # Totals
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        self.total_afg_label = QLabel(tr("0.00 AFG"))
        self.total_afg_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.total_usd_label = QLabel(tr("0.00 USD"))
        self.total_usd_label.setFont(QFont("Arial", 11, QFont.Bold))
        totals_layout.addWidget(self.total_afg_label)
        totals_layout.addWidget(self.total_usd_label)
        main.addLayout(totals_layout)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        self.cancel_btn = create_button(tr("Cancel"), style='ghost')
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = create_button(tr("Save Sale"), style='primary')
        self.save_btn.clicked.connect(self.save_sale)
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_btn)
        main.addLayout(btns)

    def _load_data(self):
        # Parties
        self.party_combo.clear()
        with PartyManager() as pm:
            for p in pm.get_all_parties():
                self.party_combo.addItem(p.name, p.id)

        # Raw materials
        self.raw_material_combo.clear()
        with RawMaterialManager() as rmm:
            for m in rmm.get_all_materials():
                self.raw_material_combo.addItem(f"{m.name} ({m.unit})", m.id)

        # Initialize fields
        self.available_label.setText(tr("Available: N/A"))
        self.quantity_spin.setValue(0.0)
        self.rate_afg_spin.setValue(0.0)
        self.rate_usd_spin.setValue(0.0)
        self.update_totals()

    def _connect(self):
        self.raw_material_combo.currentIndexChanged.connect(self._on_material_changed)
        self.quantity_spin.valueChanged.connect(self.update_totals)
        self.rate_afg_spin.valueChanged.connect(self._on_rate_afg_changed)
        self.rate_usd_spin.valueChanged.connect(self._on_rate_usd_changed)

    def _on_material_changed(self):
        material_id = self.raw_material_combo.currentData()
        if not material_id:
            self.available_label.setText(tr("Available: N/A"))
            self.quantity_spin.setMaximum(0.0)
            return

        with RawMaterialManager() as rmm:
            m = rmm.get_material_by_id(material_id)
            if not m:
                self.available_label.setText(tr("Available: N/A"))
                self.quantity_spin.setMaximum(0.0)
                return

            avail_text = f"{m.current_stock:,.2f} {m.unit}"
            if m.current_stock <= 0:
                avail_text = tr("Out of stock") + f": {avail_text}"
            elif m.current_stock <= getattr(m, 'low_stock_alert', 0):
                avail_text = tr("Low stock") + f": {avail_text}"

            self.available_label.setText(f"{tr('Available')}: {avail_text}")
            self.quantity_spin.setMaximum(m.current_stock if m.current_stock > 0 else 0.0)
            # Pre-fill rate if average cost exists
            if getattr(m, 'cost_afg', None):
                self.rate_afg_spin.setValue(round(m.cost_afg, 2))
                if self.exchange_rate:
                    self.rate_usd_spin.setValue(round(m.cost_afg / self.exchange_rate, 2))

        self.update_totals()

    def _on_rate_afg_changed(self):
        if self.exchange_rate and self.rate_afg_spin.value() > 0:
            self.rate_usd_spin.blockSignals(True)
            self.rate_usd_spin.setValue(round(self.rate_afg_spin.value() / self.exchange_rate, 2))
            self.rate_usd_spin.blockSignals(False)
            self.update_totals()

    def _on_rate_usd_changed(self):
        if self.exchange_rate and self.rate_usd_spin.value() > 0:
            self.rate_afg_spin.blockSignals(True)
            self.rate_afg_spin.setValue(round(self.rate_usd_spin.value() * self.exchange_rate, 2))
            self.rate_afg_spin.blockSignals(False)
            self.update_totals()

    def update_totals(self):
        q = self.quantity_spin.value()
        afg = self.rate_afg_spin.value()
        usd = self.rate_usd_spin.value()
        total_afg = q * afg
        total_usd = q * usd
        self.total_afg_label.setText(f"{total_afg:,.2f} AFG")
        self.total_usd_label.setText(f"{total_usd:,.2f} USD")

    def _validate(self):
        if self.party_combo.currentIndex() < 0:
            QMessageBox.warning(self, tr("Validation Error"), tr("Please select a customer."))
            return False
        if self.raw_material_combo.currentIndex() < 0:
            QMessageBox.warning(self, tr("Validation Error"), tr("Please select a raw material."))
            return False
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, tr("Validation Error"), tr("Quantity must be greater than 0."))
            return False
        if self.rate_afg_spin.value() <= 0 and self.rate_usd_spin.value() <= 0:
            QMessageBox.warning(self, tr("Validation Error"), tr("At least one rate (AFG or USD) must be greater than 0."))
            return False
        # Stock check
        material_id = self.raw_material_combo.currentData()
        with RawMaterialManager() as rmm:
            m = rmm.get_material_by_id(material_id)
            if m and self.quantity_spin.value() > m.current_stock:
                QMessageBox.warning(self, tr("Insufficient Stock"), tr("Requested quantity exceeds available stock."))
                return False
        return True

    def save_sale(self):
        if not self._validate():
            return

        party_id = self.party_combo.currentData()
        material_id = self.raw_material_combo.currentData()
        qty = self.quantity_spin.value()
        rate_afg = self.rate_afg_spin.value()
        rate_usd = self.rate_usd_spin.value()
        payment_method = self.payment_method_combo.currentText()
        notes = self.notes_edit.toPlainText().strip() or None

        try:
            with RawMaterialSaleManager() as rmsm:
                rmsm.record_raw_material_sale(
                    party_id=party_id,
                    material_id=material_id,
                    quantity=qty,
                    rate_afg=rate_afg,
                    rate_usd=rate_usd,
                    exchange_rate_used=self.exchange_rate,
                    date=self.date_edit.dateTime().toPython(),
                    payment_method=payment_method,
                    notes=notes,
                )

            QMessageBox.information(self, tr("Success"), tr("Saved successfully"))
            self.sale_saved.emit()
            self.accept()

        except Exception as e:
            logger.exception("Failed to save raw material sale")
            QMessageBox.critical(self, tr("Error"), f"{tr('Failed to save')}: {str(e)}")
