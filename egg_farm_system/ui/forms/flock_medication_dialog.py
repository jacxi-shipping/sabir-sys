from egg_farm_system.utils.i18n import tr
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QDateEdit, QLineEdit, QDoubleSpinBox, QComboBox, QPushButton, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont

from egg_farm_system.modules.flocks import FlockManager

logger = logging.getLogger(__name__)


class MedicationDialog(QDialog):
    """Dialog to record medication administration for a flock"""

    medication_saved = Signal()

    def __init__(self, flock_id, parent=None):
        super().__init__(parent)
        self.flock_id = flock_id
        self.setWindowTitle(tr("Record Medication"))
        self.setModal(True)
        self.setMinimumWidth(480)
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)

        title = QLabel(tr("Record Medication"))
        title.setFont(QFont("Arial", 12))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        form = QFormLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow(tr("Date:"), self.date_edit)

        self.med_name = QLineEdit()
        form.addRow(tr("Medication Name:"), self.med_name)

        self.dose = QDoubleSpinBox()
        self.dose.setRange(0.0, 100000.0)
        self.dose.setDecimals(3)
        form.addRow(tr("Dose:"), self.dose)

        self.dose_unit = QComboBox()
        self.dose_unit.addItems(["ml", "mg", "g", "kg"])
        form.addRow(tr("Dose Unit:"), self.dose_unit)

        self.administered_by = QLineEdit()
        form.addRow(tr("Administered By:"), self.administered_by)

        self.notes = QLineEdit()
        form.addRow(tr("Notes:"), self.notes)

        main.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        save_btn = QPushButton(tr("Save"))
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        main.addLayout(btns)

    def save(self):
        date = self.date_edit.date().toPython()
        med_name = self.med_name.text().strip()
        dose = self.dose.value()
        unit = self.dose_unit.currentText()
        admin = self.administered_by.text().strip() or None
        notes = self.notes.text().strip() or None

        if not med_name:
            QMessageBox.warning(self, tr("Validation Error"), tr("Please enter medication name."))
            return
        if dose <= 0:
            QMessageBox.warning(self, tr("Validation Error"), tr("Dose must be greater than zero."))
            return

        try:
            fm = FlockManager()
            fm.add_medication(self.flock_id, date, med_name, dose, dose_unit=unit, administered_by=admin, notes=notes)
            QMessageBox.information(self, tr("Success"), tr("Medication recorded."))
            self.medication_saved.emit()
            self.accept()
        except Exception as e:
            logger.exception("Failed to record medication")
            QMessageBox.critical(self, tr("Error"), f"{tr('Failed to record medication')}: {e}")
