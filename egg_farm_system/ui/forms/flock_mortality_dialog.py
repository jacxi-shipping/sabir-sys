from egg_farm_system.utils.i18n import tr
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QDateEdit, QSpinBox, QPushButton, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont

from egg_farm_system.modules.flocks import FlockManager

logger = logging.getLogger(__name__)


class MortalityDialog(QDialog):
    """Dialog to record mortalities for a flock"""

    mortality_saved = Signal()

    def __init__(self, flock_id, parent=None):
        super().__init__(parent)
        self.flock_id = flock_id
        self.setWindowTitle(tr("Record Mortality"))
        self.setModal(True)
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)

        title = QLabel(tr("Record Mortality"))
        title.setFont(QFont("Arial", 12))
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        form = QFormLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow(tr("Date:"), self.date_edit)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100000)
        self.count_spin.setValue(1)
        form.addRow(tr("Count:"), self.count_spin)

        self.notes = QLabel("")
        # use QLineEdit or QTextEdit for notes if desired, but keep simple
        form.addRow(tr("Notes:"), QLabel(tr("(optional)")))

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
        count = self.count_spin.value()
        try:
            fm = FlockManager()
            fm.add_mortality(self.flock_id, date, count)
            QMessageBox.information(self, tr("Success"), tr("Mortality recorded."))
            self.mortality_saved.emit()
            self.accept()
        except Exception as e:
            logger.exception("Failed to record mortality")
            QMessageBox.critical(self, tr("Error"), f"{tr('Failed to record mortality')}: {e}")
