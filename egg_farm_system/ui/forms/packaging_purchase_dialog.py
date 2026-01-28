from egg_farm_system.utils.i18n import tr
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QMessageBox, QTextEdit, QHBoxLayout
)
from PySide6.QtCore import Qt, QDateTime, Signal
from PySide6.QtGui import QFont

from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.purchases import PurchaseManager
from egg_farm_system.ui.ui_helpers import create_button

logger = logging.getLogger(__name__)


class PackagingPurchaseDialog(QDialog):
    """Dialog to purchase Carton or Tray packaging and increase RawMaterial stock."""

    purchase_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Purchase Packaging"))
        self.setModal(True)
        self.setMinimumWidth(480)
        self._build_ui()
        self._load_data()
        self._connect()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        title = QLabel(tr("Purchase Packaging"))
        title.setFont(QFont("Arial", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.party_combo = QComboBox()
        form.addRow(tr("Supplier:"), self.party_combo)

        self.material_combo = QComboBox()
        self.material_combo.addItems(["Carton", "Tray"])
        form.addRow(tr("Packaging Type:"), self.material_combo)

        # Current stock display
        self.current_stock_label = QLabel(tr("Current stock: N/A"))
        form.addRow(tr("Current Stock:"), self.current_stock_label)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(1_000_000)
        self.quantity_spin.valueChanged.connect(self._update_calculated_rate)
        form.addRow(tr("Quantity (pcs):"), self.quantity_spin)

        # Changed from rate per unit to total amount
        self.total_afg_spin = QDoubleSpinBox()
        self.total_afg_spin.setMinimum(0.0)
        self.total_afg_spin.setMaximum(10_000_000.0)
        self.total_afg_spin.setDecimals(2)
        self.total_afg_spin.valueChanged.connect(self._update_calculated_rate)
        form.addRow(tr("Total Amount (AFG):"), self.total_afg_spin)

        self.total_usd_spin = QDoubleSpinBox()
        self.total_usd_spin.setMinimum(0.0)
        self.total_usd_spin.setMaximum(10_000_000.0)
        self.total_usd_spin.setDecimals(2)
        self.total_usd_spin.valueChanged.connect(self._update_calculated_rate)
        form.addRow(tr("Total Amount (USD):"), self.total_usd_spin)
        
        # Display calculated rate per unit
        self.calc_rate_label = QLabel(tr("Rate/unit will be calculated"))
        form.addRow(tr("Calculated Rate:"), self.calc_rate_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        form.addRow(tr("Notes:"), self.notes_edit)

        main.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        self.cancel_btn = create_button(tr("Cancel"), style='ghost')
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn = create_button(tr("Purchase"), style='primary')
        self.save_btn.clicked.connect(self.save_purchase)
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_btn)
        main.addLayout(btns)

    def _load_data(self):
        self.party_combo.clear()
        with PartyManager() as pm:
            for p in pm.get_all_parties():
                self.party_combo.addItem(p.name, p.id)
        # Pre-select first supplier if available
        if self.party_combo.count() > 0:
            self.party_combo.setCurrentIndex(0)
        # Update stock display for default material
        self._update_stock_display()

    def _connect(self):
        self.material_combo.currentIndexChanged.connect(self._update_stock_display)

    def _update_stock_display(self):
        # Query current stock for selected packaging
        mat = self.material_combo.currentText()
        try:
            pm = PurchaseManager()
            try:
                session = pm.session
                from egg_farm_system.database.models import RawMaterial
                rm = session.query(RawMaterial).filter(RawMaterial.name == mat).first()
                if rm:
                    self.current_stock_label.setText(f"{rm.current_stock} pcs")
                else:
                    self.current_stock_label.setText(tr("Not found"))
            finally:
                pm.close_session()
        except Exception:
            self.current_stock_label.setText(tr("N/A"))

    def _connect(self):
        self.material_combo.currentIndexChanged.connect(self._update_stock_display)
        
    def _update_calculated_rate(self):
        """Calculate rate per unit from total amount and quantity"""
        qty = self.quantity_spin.value()
        if qty <= 0:
            self.calc_rate_label.setText(tr("Rate/unit will be calculated"))
            return
            
        total_afg = self.total_afg_spin.value()
        total_usd = self.total_usd_spin.value()
        
        rate_afg = total_afg / qty if qty > 0 else 0
        rate_usd = total_usd / qty if qty > 0 else 0
        
        self.calc_rate_label.setText(
            f"AFG: {rate_afg:.2f}/pc, USD: {rate_usd:.2f}/pc"
        )

    def _validate(self):
        if self.party_combo.currentIndex() < 0:
            QMessageBox.warning(self, tr("Validation Error"), tr("Please select a supplier."))
            return False
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, tr("Validation Error"), tr("Quantity must be greater than 0."))
            return False
        return True

    def save_purchase(self):
        if not self._validate():
            return

        party_id = self.party_combo.currentData()
        material_name = self.material_combo.currentText()
        qty = self.quantity_spin.value()
        total_afg = self.total_afg_spin.value()
        total_usd = self.total_usd_spin.value()
        notes = self.notes_edit.toPlainText().strip() or None
        
        # Calculate rate per unit from total
        rate_afg = total_afg / qty if qty > 0 else 0
        rate_usd = total_usd / qty if qty > 0 else 0

        try:
            pm = PurchaseManager()
            try:
                purchase = pm.record_packaging_purchase(
                    party_id=party_id,
                    material_name=material_name,
                    quantity=qty,
                    rate_afg=rate_afg,
                    rate_usd=rate_usd,
                    exchange_rate_used=rate_afg / rate_usd if rate_usd > 0 else 1.0,
                    notes=notes,
                    payment_method='Cash'
                )
            finally:
                pm.close_session()

            QMessageBox.information(self, tr("Success"), tr("Purchase recorded successfully."))
            self.purchase_saved.emit()
            self.accept()
        except Exception as e:
            logger.exception("Failed to record packaging purchase")
            QMessageBox.critical(self, tr("Error"), f"{tr('Failed to record purchase')}: {e}")
