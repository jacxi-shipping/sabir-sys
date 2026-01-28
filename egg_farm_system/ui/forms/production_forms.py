"""
Form widgets for egg production
"""
from egg_farm_system.utils.i18n import tr

from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDialog, QFormLayout, QSpinBox, QDateTimeEdit, QComboBox, QSizePolicy,
    QScrollArea
)
from PySide6.QtCore import Qt, QDateTime, QSize, QTimer
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from egg_farm_system.ui.widgets.datatable import DataTableWidget
from egg_farm_system.ui.widgets.loading_overlay import LoadingOverlay
from egg_farm_system.ui.widgets.success_message import SuccessMessage
from egg_farm_system.ui.widgets.keyboard_shortcuts import KeyboardShortcuts
from egg_farm_system.utils.error_handler import ErrorHandler
from PySide6.QtWidgets import QToolButton

from egg_farm_system.modules.farms import FarmManager
from egg_farm_system.modules.sheds import ShedManager
from egg_farm_system.modules.flocks import FlockManager
from egg_farm_system.modules.egg_production import EggProductionManager
from egg_farm_system.utils.egg_management import EggManagementSystem
from egg_farm_system.modules.inventory import InventoryManager
from PySide6.QtWidgets import QGroupBox, QGridLayout
from egg_farm_system.ui.widgets.jalali_date_edit import JalaliDateTimeEdit
from egg_farm_system.utils.jalali import format_value_for_ui
from egg_farm_system.ui.themes import ThemeManager
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import RawMaterial

class ProductionFormWidget(QWidget):
    """Egg production tracking widget"""
    
    def __init__(self, farm_id):
        super().__init__()
        self.farm_id = farm_id
        self.farm_manager = FarmManager()
        self.shed_manager = ShedManager()
        self.flock_manager = FlockManager()
        self.egg_manager = EggProductionManager()
        self.loading_overlay = LoadingOverlay(self)
        
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Header: title left, actions right
        header_hbox = QHBoxLayout()
        title = QLabel(tr("Egg Production Tracking"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_hbox.addWidget(title)
        header_hbox.addStretch()
        layout.addLayout(header_hbox)
        
        # Farm and shed selector
        selector_layout = QHBoxLayout()
        shed_label = QLabel(tr("Shed: <span style='color: red;'>*</span>"))
        shed_label.setTextFormat(Qt.RichText)
        selector_layout.addWidget(shed_label)
        self.shed_combo = QComboBox()
        self.shed_combo.setToolTip(tr("Select the shed for which to record production (required)"))
        self.shed_combo.currentIndexChanged.connect(self.on_shed_changed)
        selector_layout.addWidget(self.shed_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # New production button (aligned right in header)
        new_prod_btn = QPushButton(tr("Record Production"))
        new_prod_btn.clicked.connect(self.record_production)
        new_prod_btn.setToolTip(tr("Record new production (Ctrl+N)"))
        header_hbox.addWidget(new_prod_btn)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.add_standard_shortcuts(self, {
            'new': self.record_production,
            'refresh': self.refresh_productions
        })
        
        # Production table
        self.table = DataTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.set_headers(["Date", "Small", "Medium", "Large", "Broken", "Total", "Actions"])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh_data(self):
        """Refresh sheds and production data"""
        try:
            if not self.farm_id:
                return
            
            self.shed_combo.clear()
            farm = self.farm_manager.get_farm_by_id(self.farm_id)
            if farm:
                for shed in farm.sheds:
                    self.shed_combo.addItem(shed.name, shed.id)
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Failed to load data: {e}")
    
    def on_shed_changed(self):
        """Handle shed selection change"""
        self.refresh_productions()
    
    def refresh_productions(self):
        """Refresh production table"""
        shed_id = self.shed_combo.currentData()
        if not shed_id:
            self.table.set_rows([])
            return
        
        self.loading_overlay.set_message("Loading production data...")
        self.loading_overlay.show()
        QTimer.singleShot(50, lambda: self._do_refresh_productions(shed_id))
    
    def _do_refresh_productions(self, shed_id):
        """Perform the actual refresh"""
        try:
            # Default to showing last 30 days, but handle errors gracefully
            try:
                start_date = datetime.utcnow() - timedelta(days=30)
                end_date = datetime.utcnow()
                
                # Use a wider range for testing if needed, or make it user-configurable later
                # For now, let's just make sure we get data
                productions = self.egg_manager.get_daily_production(shed_id, start_date, end_date)
            except Exception as db_err:
                print(f"Database Error in get_daily_production: {db_err}")
                productions = []
            
            rows = []
            action_widgets = []
            for row, prod in enumerate(productions):
                try:
                    date_str = format_value_for_ui(prod.date)
                except Exception as fmt_err:
                    print(f"Formatting error for date {prod.date}: {fmt_err}")
                    date_str = str(prod.date)

                rows.append([
                    date_str, 
                    prod.small_count, 
                    prod.medium_count, 
                    prod.large_count, 
                    prod.broken_count, 
                    prod.total_eggs, 
                    ""
                ])
                action_widgets.append((row, prod))

            self.loading_overlay.hide()
            self.table.set_rows(rows)
            
            from egg_farm_system.config import get_asset_path
            edit_icon = Path(get_asset_path('icon_edit.svg'))
            delete_icon = Path(get_asset_path('icon_delete.svg'))
            
            for row_idx, prod in action_widgets:
                try:
                    edit_btn = QToolButton()
                    edit_btn.setAutoRaise(True)
                    edit_btn.setFixedSize(28, 28)
                    if edit_icon.exists():
                        edit_btn.setIcon(QIcon(str(edit_icon)))
                        edit_btn.setIconSize(QSize(20, 20))
                    edit_btn.setToolTip(tr('Edit'))
                    edit_btn.clicked.connect(lambda checked, p=prod: self.edit_production(p))

                    delete_btn = QToolButton()
                    delete_btn.setAutoRaise(True)
                    delete_btn.setFixedSize(28, 28)
                    if delete_icon.exists():
                        delete_btn.setIcon(QIcon(str(delete_icon)))
                        delete_btn.setIconSize(QSize(20, 20))
                    delete_btn.setToolTip(tr('Delete'))
                    delete_btn.clicked.connect(lambda checked, p=prod: self.delete_production(p))

                    container = QWidget()
                    container.setMinimumHeight(36)
                    container.setMaximumHeight(36)
                    l = QHBoxLayout(container)
                    l.setContentsMargins(4, 2, 4, 2)
                    l.setSpacing(4)
                    l.addWidget(edit_btn)
                    l.addWidget(delete_btn)
                    l.addStretch()
                    self.table.set_cell_widget(row_idx, 6, container)
                except Exception as widget_err:
                    print(f"Error creating action widgets for row {row_idx}: {widget_err}")

        except Exception as e:
            self.loading_overlay.hide()
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, tr("Error"), f"Failed to load productions: {e}")
    
    def record_production(self):
        """Record new production"""
        shed_id = self.shed_combo.currentData()
        if not shed_id:
            QMessageBox.warning(self, tr("Error"), "Please select a shed")
            return
        
        dialog = ProductionDialog(self, shed_id, None, self.egg_manager)
        if dialog.exec():
            self.refresh_productions()
    
    def edit_production(self, production):
        """Edit production"""
        dialog = ProductionDialog(self, production.shed_id, production, self.egg_manager)
        if dialog.exec():
            self.refresh_productions()
    
    def delete_production(self, production):
        """Delete production with detailed confirmation"""
        total_eggs = production.total_eggs if hasattr(production, 'total_eggs') else 0
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(tr("Confirm Delete"))
        msg.setText(f"Are you sure you want to delete the production record for {format_value_for_ui(production.date)}?")
        msg.setInformativeText(
            f"Total eggs: {total_eggs:,}\n"
            f"Small: {production.small_count}, Medium: {production.medium_count}, "
            f"Large: {production.large_count}, Broken: {production.broken_count}\n\n"
            "This action cannot be undone."
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        if msg.exec() == QMessageBox.Yes:
            try:
                self.loading_overlay.set_message("Deleting production record...")
                self.loading_overlay.show()
                QTimer.singleShot(50, lambda: self._do_delete_production(production))
            except Exception as e:
                self.loading_overlay.hide()
                QMessageBox.critical(self, tr("Delete Failed"), f"Failed to delete production: {str(e)}")
    
    def _do_delete_production(self, production):
        """Perform the actual delete"""
        try:
            self.egg_manager.delete_production(production.id)
            self.loading_overlay.hide()
            self.refresh_productions()
            success_msg = SuccessMessage(self, "Production record deleted successfully")
            success_msg.show()
        except Exception as e:
            self.loading_overlay.hide()
            QMessageBox.critical(self, tr("Delete Failed"), f"Failed to delete production: {str(e)}")


class ProductionDialog(QDialog):
    """Production recording dialog with tray/carton conversion"""
    
    def __init__(self, parent, shed_id, production, egg_manager):
        super().__init__(parent)
        self.shed_id = shed_id
        self.production = production
        self.egg_manager = egg_manager
        self.egg_management = EggManagementSystem()
        
        # Load packaging stock once
        self.carton_stock = 0
        self.tray_stock = 0
        self._load_stock()
        
        self.setWindowTitle("Egg Production" if production else "Record Production")
        self.setMinimumWidth(750)
        self.setMinimumHeight(650)
        
        # Main Dialog Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for form content
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Date Section
        date_group = QGroupBox(tr("General Information"))
        date_layout = QFormLayout()
        date_layout.setSpacing(15)
        self.date_edit = JalaliDateTimeEdit(self)
        self.date_edit.setMinimumHeight(45)
        self.date_edit.setToolTip(tr("Select the date and time for this production record (required)\nFormat: YYYY-MM-DD HH:MM (Jalali)"))
        date_layout.addRow(tr("Date & Time:"), self.date_edit)
        date_group.setLayout(date_layout)
        content_layout.addWidget(date_group)
        
        # Egg Counts Group
        counts_group = QGroupBox(tr("Egg Production (Counts by Grade)"))
        # Use a horizontal layout containing two form layouts for robust 2-column alignment
        counts_inner_layout = QHBoxLayout()
        counts_inner_layout.setSpacing(30)
        counts_inner_layout.setContentsMargins(20, 20, 20, 20)
        
        # Helper to create styled spinboxes
        def create_spinbox():
            sb = QSpinBox()
            sb.setMinimum(0)
            sb.setMaximum(100000)
            sb.setMinimumHeight(45)
            sb.setStyleSheet("font-size: 13pt; font-weight: 500;")
            return sb

        self.small_spin = create_spinbox()
        self.small_spin.valueChanged.connect(self.update_conversion)
        
        self.medium_spin = create_spinbox()
        self.medium_spin.valueChanged.connect(self.update_conversion)
        
        self.large_spin = create_spinbox()
        self.large_spin.valueChanged.connect(self.update_conversion)
        
        self.broken_spin = create_spinbox()
        self.broken_spin.valueChanged.connect(self.update_conversion)
        
        # Helper for labels
        def create_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold; font-size: 11pt; color: #555;")
            return lbl

        # Left Column
        left_form = QFormLayout()
        left_form.setSpacing(15)
        left_form.addRow(create_label("Small:"), self.small_spin)
        left_form.addRow(create_label("Large:"), self.large_spin)
        
        # Right Column
        right_form = QFormLayout()
        right_form.setSpacing(15)
        right_form.addRow(create_label("Medium:"), self.medium_spin)
        right_form.addRow(create_label("Broken:"), self.broken_spin)
        
        counts_inner_layout.addLayout(left_form)
        counts_inner_layout.addLayout(right_form)
        
        counts_group.setLayout(counts_inner_layout)
        content_layout.addWidget(counts_group)
        
        # Conversion Display Group
        conversion_group = QGroupBox(tr("Conversion Preview"))
        conversion_layout = QHBoxLayout()
        conversion_layout.setSpacing(30)
        conversion_layout.setContentsMargins(20, 20, 20, 20)
        
        self.total_eggs_label = QLabel(tr("Total: 0"))
        self.total_eggs_label.setStyleSheet(f"font-weight: 800; font-size: 16px; color: {ThemeManager.FARM_DEEP_BROWN};")
        
        self.tray_label = QLabel(tr("Trays: 0.00"))
        self.tray_label.setStyleSheet(f"font-weight: 700; font-size: 16px; color: {ThemeManager.FARM_PASTURE_GREEN};")
        
        self.carton_label = QLabel(tr("Cartons: 0.00"))
        self.carton_label.setStyleSheet(f"font-weight: 700; font-size: 16px; color: {ThemeManager.PRIMARY};")
        
        conversion_layout.addWidget(self.total_eggs_label)
        conversion_layout.addStretch()
        conversion_layout.addWidget(self.tray_label)
        conversion_layout.addWidget(self.carton_label)
        
        conversion_group.setLayout(conversion_layout)
        content_layout.addWidget(conversion_group)

        # Packaging usage inputs
        packaging_group = QGroupBox(tr("Packaging Consumed"))
        # Same split form pattern for packaging
        pkg_inner_layout = QHBoxLayout()
        pkg_inner_layout.setSpacing(30)
        pkg_inner_layout.setContentsMargins(20, 20, 20, 20)
        
        self.trays_used_spin = create_spinbox()
        self.cartons_used_spin = create_spinbox()

        self.carton_stock_label = QLabel(tr("Stock: {}").format(self.carton_stock))
        self.carton_stock_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-weight: bold; margin-left: 10px;")
        self.tray_stock_label = QLabel(tr("Stock: {}").format(self.tray_stock))
        self.tray_stock_label.setStyleSheet("color: #7f8c8d; font-style: italic; font-weight: bold; margin-left: 10px;")

        # Prepare stock layout widgets to put next to label
        def create_field_with_stock(spin, stock_lbl):
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0,0,0,0)
            l.addWidget(spin)
            l.addWidget(stock_lbl)
            return w

        pkg_left_form = QFormLayout()
        pkg_left_form.setSpacing(15)
        pkg_left_form.addRow(create_label("Trays Used:"), create_field_with_stock(self.trays_used_spin, self.tray_stock_label))
        
        pkg_right_form = QFormLayout()
        pkg_right_form.setSpacing(15)
        pkg_right_form.addRow(create_label("Cartons Used:"), create_field_with_stock(self.cartons_used_spin, self.carton_stock_label))
        
        pkg_inner_layout.addLayout(pkg_left_form)
        pkg_inner_layout.addLayout(pkg_right_form)
        
        packaging_group.setLayout(pkg_inner_layout)
        content_layout.addWidget(packaging_group)
        
        if production:
            if isinstance(production.date, str):
                # Try parsing if it's a string
                try:
                    dt = datetime.strptime(production.date, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        dt = datetime.strptime(production.date, "%Y-%m-%d")
                    except ValueError:
                        dt = datetime.now()
                self.date_edit.setDateTime(dt)
            else:
                # It's already a datetime/date object
                if isinstance(production.date, datetime):
                    self.date_edit.setDateTime(production.date)
                elif hasattr(production.date, 'year'): # date object
                    self.date_edit.setDate(production.date)
                else:
                    self.date_edit.setDateTime(datetime.now())

            self.small_spin.setValue(production.small_count)
            self.medium_spin.setValue(production.medium_count)
            self.large_spin.setValue(production.large_count)
            self.broken_spin.setValue(production.broken_count)
            # populate packaging usage if present
            if hasattr(production, 'trays_used'):
                self.trays_used_spin.setValue(getattr(production, 'trays_used') or 0)
            if hasattr(production, 'cartons_used'):
                self.cartons_used_spin.setValue(getattr(production, 'cartons_used') or 0)
        
        self.small_spin.setToolTip(tr("Enter the number of small eggs (optional)"))
        self.small_spin.setSuffix(" eggs")
        self.medium_spin.setToolTip(tr("Enter the number of medium eggs (optional)"))
        self.medium_spin.setSuffix(" eggs")
        self.large_spin.setToolTip(tr("Enter the number of large eggs (optional)"))
        self.large_spin.setSuffix(" eggs")
        self.broken_spin.setToolTip(tr("Enter the number of broken eggs (optional)"))
        self.broken_spin.setSuffix(" eggs")
        
        content_layout.addStretch()
        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Buttons (Outside Scroll Area)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.setContentsMargins(20, 10, 20, 10)
        
        save_btn = QPushButton(tr("Save Production Record"))
        save_btn.setMinimumHeight(50)
        save_btn.setProperty("class", "success")
        save_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setMinimumHeight(50)
        cancel_btn.setFont(QFont("Segoe UI", 11))
        
        save_btn.clicked.connect(self.save_production)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(cancel_btn, 1)
        btn_layout.addWidget(save_btn, 2)
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
        
        # Add keyboard shortcuts
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.SAVE, self.save_production)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.CLOSE, self.reject)
        KeyboardShortcuts.create_shortcut(self, KeyboardShortcuts.ESCAPE, self.reject)
        
        # Initial conversion update
        self.update_conversion()

    def _load_stock(self):
        """Load current stock levels for packaging"""
        try:
            session = DatabaseManager.get_session()
            try:
                carton = session.query(RawMaterial).filter(RawMaterial.name == 'Carton').first()
                tray = session.query(RawMaterial).filter(RawMaterial.name == 'Tray').first()
                self.carton_stock = carton.current_stock if carton else 0
                self.tray_stock = tray.current_stock if tray else 0
            finally:
                session.close()
        except Exception as e:
            # Silently fail or log error
            pass

    
    def update_conversion(self):
        """Update tray/carton conversion display"""
        try:
            total_eggs = (
                self.small_spin.value() +
                self.medium_spin.value() +
                self.large_spin.value() +
                self.broken_spin.value()
            )
            
            trays = self.egg_management.eggs_to_trays(total_eggs)
            cartons = self.egg_management.eggs_to_cartons(total_eggs)
            
            self.total_eggs_label.setText(f"Total: {total_eggs:,} eggs")
            self.tray_label.setText(f"= {trays:.2f} trays")
            self.carton_label.setText(f"= {cartons:.2f} cartons")
            
            # Set defaults for packaging usage (only if we haven't manually changed them? 
            # Actually the original code reset them every time calculation changed, so we keep that behavior
            # but maybe we should check if the user has manually edited it? 
            # The original code just overwrote it. I'll stick to original behavior but simpler.)
            
            try:
                self.trays_used_spin.blockSignals(True)
                self.cartons_used_spin.blockSignals(True)
                
                # Default logic: auto-fill based on calculation
                # Users can still change it manually, but next egg count change will reset it.
                # This might be annoying if user adjusted it and then changed egg count.
                # But that was the original behavior.
                self.trays_used_spin.setValue(int(trays) if trays == int(trays) else int(trays) + 1)
                self.cartons_used_spin.setValue(int(cartons) if cartons == int(cartons) else int(cartons) + 1)
            finally:
                self.trays_used_spin.blockSignals(False)
                self.cartons_used_spin.blockSignals(False)
                
        except Exception as e:
            pass
    
    def save_production(self):
        """Save production with loading indicator and success feedback"""
        # Validate that at least some eggs are recorded
        total = (self.small_spin.value() + self.medium_spin.value() + 
                 self.large_spin.value() + self.broken_spin.value())
        if total == 0:
            QMessageBox.warning(
                self, 
                tr("Validation Error"), 
                "Please enter at least one egg count. Total eggs cannot be zero."
            )
            return
        
        # Show loading overlay
        loading = LoadingOverlay(self, "Saving production record...")
        loading.show()
        QTimer.singleShot(50, lambda: self._do_save_production(loading))
    
    def _do_save_production(self, loading):
        """Perform the actual save"""
        try:
            if self.production:
                self.egg_manager.update_production(
                    self.production.id,
                    self.small_spin.value(),
                    self.medium_spin.value(),
                    self.large_spin.value(),
                    self.broken_spin.value(),
                    cartons_used=self.cartons_used_spin.value(),
                    trays_used=self.trays_used_spin.value()
                )
                message = "Production record updated successfully."
            else:
                self.egg_manager.record_production(
                    self.shed_id,
                    self.date_edit.dateTime(),
                    self.small_spin.value(),
                    self.medium_spin.value(),
                    self.large_spin.value(),
                    self.broken_spin.value(),
                    cartons_used=self.cartons_used_spin.value(),
                    trays_used=self.trays_used_spin.value()
                )
                message = "Production record saved successfully."
            
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
                f"Failed to save production record.\n\nError: {str(e)}\n\nPlease check your input and try again."
            )
