from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from egg_farm_system.modules.settings import SettingsManager
from egg_farm_system.utils.egg_management import EggManagementSystem
from egg_farm_system.utils.i18n import tr


class SettingsForm(QWidget):
    """Enhanced settings editor with categories"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tabs = None
        self.tray_expense_spin = None
        self.carton_expense_spin = None
        self.exchange_rate_spin = None
        self.settings_list = None
        self.key_edit = None
        self.value_edit = None
        self.description_edit = None

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel(tr("Settings"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Create tab widget for categories
        self.tabs = QTabWidget()
        
        # Egg Management Settings Tab
        egg_tab = self.create_egg_settings_tab()
        self.tabs.addTab(egg_tab, "Egg Management")
        
        # General Settings Tab
        general_tab = self.create_general_settings_tab()
        self.tabs.addTab(general_tab, "General")
        
        # Advanced Settings Tab (raw key-value editor)
        advanced_tab = self.create_advanced_settings_tab()
        self.tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(self.tabs)
        
        # Save All button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_all_btn = QPushButton(tr("Save All Settings"))
        save_all_btn.setMinimumWidth(150)
        save_all_btn.clicked.connect(self.save_all_settings)
        btn_layout.addWidget(save_all_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def create_egg_settings_tab(self):
        """Create egg management settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Info label
        info_label = QLabel(
            tr("Configure egg packaging expenses. These values are used when calculating " + "total costs for carton-based egg sales.")
        )
        info_label.setWordWrap(True)
        info_label.setProperty('class', 'info-banner')
        layout.addWidget(info_label)
        
        # Egg Expense Settings Group
        expense_group = QGroupBox("Egg Packaging Expenses")
        expense_layout = QFormLayout()
        expense_layout.setSpacing(12)
        expense_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.tray_expense_spin = QDoubleSpinBox()
        self.tray_expense_spin.setMinimum(0)
        self.tray_expense_spin.setMaximum(10000)
        self.tray_expense_spin.setDecimals(2)
        self.tray_expense_spin.setSuffix(" AFG per tray")
        self.tray_expense_spin.setSingleStep(1.0)
        self.tray_expense_spin.setMinimumWidth(250)
        self.tray_expense_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        expense_layout.addRow("Tray Expense:", self.tray_expense_spin)
        
        self.carton_expense_spin = QDoubleSpinBox()
        self.carton_expense_spin.setMinimum(0)
        self.carton_expense_spin.setMaximum(10000)
        self.carton_expense_spin.setDecimals(2)
        self.carton_expense_spin.setSuffix(" AFG per carton")
        self.carton_expense_spin.setSingleStep(1.0)
        self.carton_expense_spin.setMinimumWidth(250)
        self.carton_expense_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        expense_layout.addRow("Carton Expense:", self.carton_expense_spin)
        
        expense_group.setLayout(expense_layout)
        layout.addWidget(expense_group)
        
        # Conversion Info Group
        info_group = QGroupBox("Conversion Information")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        conversion_info = QLabel(
            "<b>Egg Conversion:</b><br>"
            "• 30 eggs = 1 tray<br>"
            "• 180 eggs = 1 carton (6 trays)<br>"
            "• 1 carton uses 7 trays for packaging<br><br>"
            "<b>Expense Calculation:</b><br>"
            "• Tray expense = (Cartons × 7) × Tray Expense<br>"
            "• Carton expense = Cartons × Carton Expense<br>"
            "• Total expense = Tray expense + Carton expense"
        )
        conversion_info.setWordWrap(True)
        conversion_info.setProperty('class', 'info-banner-secondary')
        info_layout.addWidget(conversion_info)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_general_settings_tab(self):
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Exchange Rate Group
        exchange_group = QGroupBox("Currency Settings")
        exchange_layout = QFormLayout()
        exchange_layout.setSpacing(12)
        
        self.exchange_rate_spin = QDoubleSpinBox()
        self.exchange_rate_spin.setMinimum(0.01)
        self.exchange_rate_spin.setMaximum(1000)
        self.exchange_rate_spin.setDecimals(2)
        self.exchange_rate_spin.setSuffix(" AFG per USD")
        exchange_layout.addRow("Exchange Rate (AFG/USD):", self.exchange_rate_spin)
        
        exchange_group.setLayout(exchange_layout)
        layout.addWidget(exchange_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_settings_tab(self):
        """Create advanced settings tab with raw key-value editor"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        info_label = QLabel(
            tr("Advanced settings editor. Use this to view and edit all application settings " + "using key-value pairs. Changes are saved immediately.")
        )
        info_label.setWordWrap(True)
        info_label.setProperty('class', 'warning-banner')
        layout.addWidget(info_label)
        
        # Settings list
        list_label = QLabel(tr("All Settings:"))
        layout.addWidget(list_label)
        
        self.settings_list = QListWidget()
        self.settings_list.itemDoubleClicked.connect(self.on_setting_double_clicked)
        layout.addWidget(self.settings_list)
        
        # Edit form
        form_group = QGroupBox("Edit Setting")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText(tr("Setting key"))
        form_layout.addRow("Key:", self.key_edit)
        
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText(tr("Setting value"))
        form_layout.addRow("Value:", self.value_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.description_edit.setPlaceholderText(tr("Optional description"))
        form_layout.addRow("Description:", self.description_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr("Save Setting"))
        save_btn.clicked.connect(self.save_setting)
        delete_btn = QPushButton(tr("Delete Setting"))
        delete_btn.clicked.connect(self.delete_setting)
        refresh_btn = QPushButton(tr("Refresh List"))
        refresh_btn.clicked.connect(self.load_advanced_settings)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def load_settings(self):
        """Load all settings"""
        try:
            # Load egg expense settings
            egg_manager = EggManagementSystem()
            tray_expense = egg_manager.get_tray_expense()
            carton_expense = egg_manager.get_carton_expense()
            
            self.tray_expense_spin.setValue(tray_expense)
            self.carton_expense_spin.setValue(carton_expense)
            
            # Load exchange rate
            from egg_farm_system.utils.currency import CurrencyConverter
            converter = CurrencyConverter()
            exchange_rate = converter.get_exchange_rate()
            self.exchange_rate_spin.setValue(exchange_rate)
            
            # Load advanced settings
            self.load_advanced_settings()
        except Exception as e:
            QMessageBox.warning(self, tr("Error"), f"Failed to load settings: {e}")
    
    def load_advanced_settings(self):
        """Load advanced settings list"""
        self.settings_list.clear()
        try:
            for s in SettingsManager.get_all_settings():
                desc = f" - {s.description}" if s.description else ""
                self.settings_list.addItem(f"{s.key} = {s.value}{desc}")
        except Exception as e:
            QMessageBox.warning(self, tr("Error"), f"Failed to load settings list: {e}")
    
    def on_setting_double_clicked(self, item):
        """Handle double-click on setting item"""
        text = item.text()
        if " = " in text:
            key = text.split(" = ")[0]
            self.key_edit.setText(key)
            
            # Get full setting details
            try:
                settings = SettingsManager.get_all_settings()
                for s in settings:
                    if s.key == key:
                        self.value_edit.setText(s.value)
                        self.description_edit.setPlainText(s.description or "")
                        break
            except Exception:
                pass
    
    def save_setting(self):
        """Save a setting from advanced tab"""
        key = self.key_edit.text().strip()
        value = self.value_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        
        if not key:
            QMessageBox.warning(self, tr('Validation'), 'Key is required')
            return
        
        try:
            SettingsManager.set_setting(key, value, description if description else None)
            QMessageBox.information(self, tr('Saved'), 'Setting saved successfully')
            self.load_advanced_settings()
            # Clear form
            self.key_edit.clear()
            self.value_edit.clear()
            self.description_edit.clear()
        except Exception as e:
            QMessageBox.critical(self, tr('Error'), f'Failed to save setting: {e}')
    
    def delete_setting(self):
        """Delete a setting"""
        key = self.key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, tr('Validation'), 'Please enter a key to delete')
            return
        
        reply = QMessageBox.question(
            self, 'Confirm Delete',
            f'Are you sure you want to delete setting "{key}"?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from egg_farm_system.database.db import DatabaseManager
                from egg_farm_system.database.models import Setting
                
                session = DatabaseManager.get_session()
                try:
                    setting = session.query(Setting).filter(Setting.key == key).first()
                    if setting:
                        session.delete(setting)
                        session.commit()
                        QMessageBox.information(self, tr('Deleted'), 'Setting deleted successfully')
                        self.load_advanced_settings()
                        self.key_edit.clear()
                        self.value_edit.clear()
                        self.description_edit.clear()
                    else:
                        QMessageBox.warning(self, tr('Not Found'), f'Setting "{key}" not found')
                finally:
                    session.close()
            except Exception as e:
                QMessageBox.critical(self, tr('Error'), f'Failed to delete setting: {e}')
    
    def save_all_settings(self):
        """Save all settings from all tabs"""
        try:
            # Save egg expense settings
            egg_manager = EggManagementSystem()
            egg_manager.set_tray_expense(self.tray_expense_spin.value())
            egg_manager.set_carton_expense(self.carton_expense_spin.value())
            
            # Save exchange rate
            from egg_farm_system.utils.currency import CurrencyConverter
            converter = CurrencyConverter()
            converter.set_exchange_rate(self.exchange_rate_spin.value())
            
            QMessageBox.information(
                self, 
                tr("Success"), 
                "All settings saved successfully!\n\n"
                f"Tray Expense: {self.tray_expense_spin.value():.2f} AFG\n"
                f"Carton Expense: {self.carton_expense_spin.value():.2f} AFG\n"
                f"Exchange Rate: {self.exchange_rate_spin.value():.2f} AFG/USD"
            )
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Failed to save settings: {e}")
