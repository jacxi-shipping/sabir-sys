"""
Flock management forms
"""
from egg_farm_system.utils.i18n import tr

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QMessageBox, QDialog, QFormLayout, QSpinBox, QLineEdit, QToolButton,
    QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QStandardItem

from egg_farm_system.ui.widgets.jalali_date_edit import JalaliDateEdit
from datetime import date

from egg_farm_system.modules.farms import FarmManager
from egg_farm_system.modules.sheds import ShedManager
from egg_farm_system.modules.flocks import FlockManager
from egg_farm_system.ui.widgets.datatable import DataTableWidget
from egg_farm_system.config import get_asset_path

class FlockDialog(QDialog):
    def __init__(self, shed_id, flock=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{'Edit' if flock else 'Add'} Flock")
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit(flock.name if flock else "")
        self.date_edit = JalaliDateEdit(initial=flock.start_date if flock else date.today())
            
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 100000)
        self.count_spin.setValue(flock.initial_count if flock else 1000)
        
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Start Date:", self.date_edit)
        layout.addRow("Initial Count:", self.count_spin)
        
        buttons = QHBoxLayout()
        save_btn = QPushButton(tr("Save"))
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)
        
    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "start_date": self.date_edit.date(),
            "initial_count": self.count_spin.value()
        }

class FlockManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.refresh_farms()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(tr("Flock Management"))
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        header.addWidget(title)
        header.addStretch()
        
        refresh_btn = QPushButton(tr("Refresh"))
        refresh_btn.clicked.connect(self.refresh_flocks)
        header.addWidget(refresh_btn)
        layout.addLayout(header)
        
        # Filters
        filter_layout = QHBoxLayout()
        self.farm_combo = QComboBox()
        self.farm_combo.currentIndexChanged.connect(self.refresh_sheds)
        self.shed_combo = QComboBox()
        self.shed_combo.currentIndexChanged.connect(self.refresh_flocks)
        
        filter_layout.addWidget(QLabel(tr("Farm:")))
        filter_layout.addWidget(self.farm_combo)
        filter_layout.addWidget(QLabel(tr("Shed:")))
        filter_layout.addWidget(self.shed_combo)
        filter_layout.addStretch()
        
        self.add_btn = QPushButton(tr("Add Flock"))
        self.add_btn.clicked.connect(self.add_flock)
        self.add_btn.setEnabled(False)
        filter_layout.addWidget(self.add_btn)
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = DataTableWidget()
        self.table.set_headers(["ID", "Name", "Start Date", "Initial", "Live", "Age (Days)", "Actions"])
        self.table.view.setColumnHidden(0, True)
        layout.addWidget(self.table)

        # Details tabs (Medications / Mortalities)
        self.details_tabs = QTabWidget()
        # Medications table
        self.meds_table = DataTableWidget(enable_pagination=False)
        self.meds_table.set_headers(["ID", "Date", "Medication", "Dose", "Unit", "Administered By", "Notes"])
        self.details_tabs.addTab(self.meds_table, tr("Medications"))
        # Mortalities table
        self.morts_table = DataTableWidget(enable_pagination=False)
        self.morts_table.set_headers(["ID", "Date", "Count", "Notes"])
        self.details_tabs.addTab(self.morts_table, tr("Mortalities"))

        layout.addWidget(self.details_tabs)

        # Wire selection to load details
        self.table.row_selected.connect(self._on_flock_selected)

    def refresh_farms(self):
        self.farm_combo.blockSignals(True)
        self.farm_combo.clear()
        try:
            with FarmManager() as fm:
                for farm in fm.get_all_farms():
                    self.farm_combo.addItem(farm.name, farm.id)
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Failed to load farms: {e}")
        self.farm_combo.blockSignals(False)
        self.refresh_sheds()

    def refresh_sheds(self):
        self.shed_combo.blockSignals(True)
        self.shed_combo.clear()
        farm_id = self.farm_combo.currentData()
        if farm_id:
            try:
                with ShedManager() as sm:
                    for shed in sm.get_sheds_by_farm(farm_id):
                        self.shed_combo.addItem(shed.name, shed.id)
            except Exception as e:
                QMessageBox.critical(self, tr("Error"), f"Failed to load sheds: {e}")
        self.shed_combo.blockSignals(False)
        self.refresh_flocks()

    def refresh_flocks(self):
        self.table.model.setRowCount(0)
        shed_id = self.shed_combo.currentData()
        if not shed_id:
            self.add_btn.setEnabled(False)
            return
            
        self.add_btn.setEnabled(True)
        fm = FlockManager()
        try:
            flocks = fm.get_flocks_by_shed(shed_id)
            
            for row, flock in enumerate(flocks):
                stats = fm.get_flock_stats(flock.id)
                live = stats['live_count'] if stats else flock.initial_count
                age = stats['age_days'] if stats else 0
                
                self.table.model.insertRow(row)
                self.table.model.setItem(row, 0, QStandardItem(str(flock.id)))
                self.table.model.setItem(row, 1, QStandardItem(flock.name))
                self.table.model.setItem(row, 2, QStandardItem(str(flock.start_date.date())))
                self.table.model.setItem(row, 3, QStandardItem(str(flock.initial_count)))
                self.table.model.setItem(row, 4, QStandardItem(str(live)))
                self.table.model.setItem(row, 5, QStandardItem(str(age)))
                
                # Actions
                edit_btn = QToolButton(); edit_btn.setIcon(QIcon(get_asset_path('icon_edit.svg')))
                edit_btn.clicked.connect(lambda checked=False, f=flock: self.edit_flock(f))
                delete_btn = QToolButton(); delete_btn.setIcon(QIcon(get_asset_path('icon_delete.svg')))
                delete_btn.clicked.connect(lambda checked=False, f=flock: self.delete_flock(f))
                # Mortality and Medication actions
                mort_btn = QToolButton(); mort_btn.setIcon(QIcon(get_asset_path('icon_alert.svg')))
                mort_btn.setToolTip(tr('Record Mortality'))
                mort_btn.clicked.connect(lambda checked=False, f=flock: self.record_mortality(f))
                med_btn = QToolButton(); med_btn.setIcon(QIcon(get_asset_path('icon_medical.svg')))
                med_btn.setToolTip(tr('Record Medication'))
                med_btn.clicked.connect(lambda checked=False, f=flock: self.record_medication(f))
                
                container = QWidget()
                h = QHBoxLayout(container)
                h.setContentsMargins(0, 0, 0, 0)
                h.addWidget(edit_btn)
                h.addWidget(delete_btn)
                h.addWidget(mort_btn)
                h.addWidget(med_btn)
                h.addStretch()
                
                proxy_idx = self.table.proxy.mapFromSource(self.table.model.index(row, 6))
                self.table.view.setIndexWidget(proxy_idx, container)
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Failed to load flocks: {e}")

    def _on_flock_selected(self, source_row_index: int):
        """Load medications and mortalities for selected flock row (source model index)."""
        try:
            # flock id is stored in column 0 as string
            item = self.table.model.item(source_row_index, 0)
            if not item:
                # clear tables
                self.meds_table.clear()
                self.morts_table.clear()
                return
            flock_id = int(item.text())
            fm = FlockManager()
            meds = fm.get_medications(flock_id)
            morts = fm.get_mortalities(flock_id)

            med_rows = []
            for m in meds:
                med_rows.append([
                    m.id,
                    getattr(m.date, 'date', lambda: m.date)() if hasattr(m.date, 'date') else str(m.date),
                    m.medication_name,
                    m.dose,
                    m.dose_unit,
                    m.administered_by or '',
                    m.notes or ''
                ])
            self.meds_table.set_rows(med_rows)

            mort_rows = []
            for mt in morts:
                mort_rows.append([
                    mt.id,
                    getattr(mt.date, 'date', lambda: mt.date)() if hasattr(mt.date, 'date') else str(mt.date),
                    mt.count,
                    mt.notes or ''
                ])
            self.morts_table.set_rows(mort_rows)
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Failed to load flock details: {e}")

    def add_flock(self):
        shed_id = self.shed_combo.currentData()
        if not shed_id: return
        dialog = FlockDialog(shed_id, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                fm = FlockManager()
                fm.create_flock(shed_id, **data)
                self.refresh_flocks()
                QMessageBox.information(self, tr("Success"), "Flock created successfully")
            except Exception as e:
                QMessageBox.critical(self, tr("Error"), str(e))

    def edit_flock(self, flock):
        dialog = FlockDialog(flock.shed_id, flock, self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                fm = FlockManager()
                fm.update_flock(flock.id, **data)
                self.refresh_flocks()
                QMessageBox.information(self, tr("Success"), "Flock updated successfully")
            except Exception as e:
                QMessageBox.critical(self, tr("Error"), str(e))

    def delete_flock(self, flock):
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete flock '{flock.name}'? This cannot be undone.")
        if reply == QMessageBox.Yes:
            try:
                fm = FlockManager()
                fm.delete_flock(flock.id)
                self.refresh_flocks()
                QMessageBox.information(self, tr("Success"), "Flock deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, tr("Error"), str(e))

    def record_mortality(self, flock):
        from egg_farm_system.ui.forms.flock_mortality_dialog import MortalityDialog
        dialog = MortalityDialog(flock.id, parent=self)
        dialog.mortality_saved.connect(self.refresh_flocks)
        dialog.exec()

    def record_medication(self, flock):
        from egg_farm_system.ui.forms.flock_medication_dialog import MedicationDialog
        dialog = MedicationDialog(flock.id, parent=self)
        dialog.medication_saved.connect(self.refresh_flocks)
        dialog.exec()
