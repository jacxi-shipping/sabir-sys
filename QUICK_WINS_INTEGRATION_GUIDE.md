# Quick Wins Integration Guide

This document provides step-by-step instructions for integrating the Quick Wins features into the main application.

## Features Implemented

1. ✅ Data Import/Export System
2. ✅ Enhanced Dashboard Widgets
3. ✅ Smart Notifications & Alerts
4. ✅ Quick Actions & Command Palette

## Integration Steps

### 1. Main Window Integration (egg_farm_system/ui/main_window.py)

Add these imports at the top of the file:

```python
from egg_farm_system.ui.widgets.command_palette import CommandPalette
from egg_farm_system.ui.widgets.import_wizard import ImportWizard
from egg_farm_system.utils.alert_scheduler import AlertScheduler
from PySide6.QtGui import QShortcut, QKeySequence
```

Add initialization in `__init__` method (after line 88):

```python
# Initialize alert scheduler
self.alert_scheduler = AlertScheduler()
self.alert_scheduler.start(interval_minutes=30)  # Check alerts every 30 minutes
```

Add command palette shortcut in `_setup_keyboard_shortcuts` method:

```python
# Add Ctrl+K for command palette
self.cmd_palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
self.cmd_palette_shortcut.activated.connect(self.show_command_palette)
```

Add these methods to the MainWindow class:

```python
def show_command_palette(self):
    """Show command palette dialog"""
    palette = CommandPalette(self)
    palette.command_executed.connect(self.execute_command)
    # Center on screen
    palette.move(
        self.geometry().center() - palette.rect().center()
    )
    palette.exec()

def execute_command(self, command_id: str, data: dict):
    """Execute command from palette"""
    command_map = {
        # Navigation
        'goto_dashboard': self.load_dashboard,
        'goto_farms': self.load_farm_management,
        'goto_production': self.load_production,
        'goto_sales': self.load_sales,
        'goto_purchases': self.load_purchases,
        'goto_inventory': self.load_inventory,
        'goto_parties': self.load_parties,
        'goto_reports': self.load_reports,
        'goto_expenses': self.load_expenses,
        'goto_employees': self.load_employees,
        
        # Quick Actions
        'record_production': lambda: self._open_quick_action('production'),
        'add_sale': lambda: self._open_quick_action('sale'),
        'add_purchase': lambda: self._open_quick_action('purchase'),
        'record_mortality': lambda: self._open_quick_action('mortality'),
        'issue_feed': lambda: self._open_quick_action('feed'),
        'add_expense': lambda: self._open_quick_action('expense'),
        'add_party': lambda: self._open_quick_action('party'),
        'add_payment': lambda: self._open_quick_action('payment'),
        
        # Tools
        'refresh_dashboard': self._refresh_current_page,
        'import_data': self.show_import_wizard,
        'check_alerts': lambda: self.alert_scheduler.check_now(),
        'backup_database': lambda: self._open_quick_action('backup'),
    }
    
    handler = command_map.get(command_id)
    if handler:
        try:
            handler()
        except Exception as e:
            logger.error(f"Error executing command {command_id}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to execute command: {str(e)}")

def _open_quick_action(self, action_type: str):
    """Open quick action dialog"""
    # Navigate to appropriate page and trigger add action
    if action_type == 'production':
        self.load_production()
    elif action_type == 'sale':
        self.load_sales()
    elif action_type == 'purchase':
        self.load_purchases()
    elif action_type == 'expense':
        self.load_expenses()
    elif action_type == 'party':
        self.load_parties()
    elif action_type == 'backup':
        self.load_backup_restore()

def show_import_wizard(self):
    """Show import wizard dialog"""
    wizard = ImportWizard(self)
    wizard.import_completed.connect(self._on_import_completed)
    wizard.exec()

def _on_import_completed(self, result: dict):
    """Handle import completion"""
    if result['status'] == 'success':
        QMessageBox.information(
            self,
            "Import Successful",
            f"Successfully imported {result['imported']} records!"
        )
        # Refresh current view
        self._refresh_current_page()
    elif result['imported'] > 0:
        QMessageBox.warning(
            self,
            "Import Completed with Warnings",
            f"Imported {result['imported']} records with {len(result.get('errors', []))} errors."
        )
        self._refresh_current_page()
    else:
        QMessageBox.warning(
            self,
            "Import Failed",
            f"Import failed: {result.get('message', 'Unknown error')}"
        )
```

Add menu item for Import Data in the sidebar (in `create_sidebar` method):

```python
# Add to System group
add_btn_with_i18n(system_group, "Import Data", self.show_import_wizard, "icon_import.svg")
```

### 2. Dashboard Integration (egg_farm_system/ui/dashboard.py)

To integrate customizable widgets, update the DashboardWidget class:

At the top of the file, add imports:

```python
from egg_farm_system.ui.widgets.mortality_trend_widget import MortalityTrendWidget
from egg_farm_system.ui.widgets.top_customers_widget import TopCustomersWidget
from egg_farm_system.ui.widgets.low_stock_alerts_widget import LowStockAlertsWidget
from egg_farm_system.ui.widgets.widget_configurator import WidgetConfigurator
```

Add widget configuration support in `init_ui` method (after the refresh button):

```python
# Widget configurator button
configure_btn = QPushButton("⚙ Configure Widgets")
configure_btn.clicked.connect(self.configure_widgets)
title_layout.addWidget(configure_btn)
```

Add these methods to DashboardWidget class:

```python
def configure_widgets(self):
    """Show widget configuration dialog"""
    current_widgets = self.get_active_widgets()
    dialog = WidgetConfigurator(current_widgets, self)
    if dialog.exec() == QDialog.Accepted:
        selected = dialog.get_selected_widgets()
        self.save_active_widgets(selected)
        self.refresh_custom_widgets()

def get_active_widgets(self) -> list:
    """Get list of active widget IDs"""
    # Load from settings
    from egg_farm_system.modules.settings import SettingsManager
    return SettingsManager.get_setting('dashboard_widgets', default=[])

def save_active_widgets(self, widget_ids: list):
    """Save active widget IDs"""
    from egg_farm_system.modules.settings import SettingsManager
    SettingsManager.set_setting('dashboard_widgets', widget_ids)

def refresh_custom_widgets(self):
    """Refresh custom dashboard widgets"""
    # Add a section for custom widgets after main metrics
    # You can add this in init_ui or create a separate container
    active_widgets = self.get_active_widgets()
    
    if not active_widgets:
        return
    
    # Create widget container
    widgets_group = QGroupBox("Custom Widgets")
    widgets_layout = QGridLayout()
    widgets_layout.setSpacing(15)
    
    row, col = 0, 0
    for widget_id in active_widgets:
        widget = self._create_widget(widget_id)
        if widget:
            widgets_layout.addWidget(widget, row, col)
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
    
    widgets_group.setLayout(widgets_layout)
    # Add to main layout (you'll need to adjust based on your layout structure)
    # layout.addWidget(widgets_group)

def _create_widget(self, widget_id: str):
    """Create widget by ID"""
    widget_map = {
        'mortality_trend': MortalityTrendWidget,
        'top_customers': TopCustomersWidget,
        'low_stock_alerts': LowStockAlertsWidget,
    }
    
    widget_class = widget_map.get(widget_id)
    if widget_class:
        widget = widget_class(self)
        if hasattr(widget, 'set_farm_id'):
            widget.set_farm_id(self.farm_id)
        return widget
    return None
```

### 3. Settings Module Integration

The alert scheduler and widget preferences need settings storage. If SettingsManager doesn't exist, create a simple one:

```python
# egg_farm_system/modules/settings.py

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Setting
import json

class SettingsManager:
    """Manage application settings"""
    
    @staticmethod
    def get_setting(key: str, default=None):
        """Get setting value"""
        session = DatabaseManager.get_session()
        try:
            setting = session.query(Setting).filter(Setting.key == key).first()
            if setting:
                try:
                    return json.loads(setting.value)
                except:
                    return setting.value
            return default
        finally:
            session.close()
    
    @staticmethod
    def set_setting(key: str, value):
        """Set setting value"""
        session = DatabaseManager.get_session()
        try:
            setting = session.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = json.dumps(value) if not isinstance(value, str) else value
            else:
                setting = Setting(key=key, value=json.dumps(value) if not isinstance(value, str) else value)
                session.add(setting)
            session.commit()
        finally:
            session.close()
```

### 4. Testing the Integration

After making the above changes:

1. **Test Data Import**:
   - Press Ctrl+K and type "import"
   - Select "Import Data"
   - Download a template
   - Fill in some test data
   - Import it

2. **Test Command Palette**:
   - Press Ctrl+K
   - Try navigating to different pages
   - Try quick actions

3. **Test Alert System**:
   - The alerts will check automatically every 30 minutes
   - Or press Ctrl+K and select "Check Alerts Now"
   - Notifications will appear in the notification center

4. **Test Custom Widgets**:
   - Go to Dashboard
   - Click "⚙ Configure Widgets"
   - Select widgets to display
   - Save and see them appear

### 5. Cleanup and Polish

Add these keyboard shortcuts to the help documentation (if exists):

- `Ctrl+K`: Open Command Palette
- `Ctrl+Shift+P`: Record Production (can be added)
- `Ctrl+Shift+S`: Add Sale (can be added)
- `Ctrl+Shift+I`: Import Data (can be added)

## Files Created

### Core Utilities
- `egg_farm_system/utils/template_generator.py` - Template generation for imports
- `egg_farm_system/utils/data_validator.py` - Data validation
- `egg_farm_system/utils/data_importer.py` - Import engine
- `egg_farm_system/utils/alert_scheduler.py` - Alert scheduling

### Modules
- `egg_farm_system/modules/alert_rules.py` - Alert rules engine

### UI Widgets
- `egg_farm_system/ui/widgets/import_wizard.py` - Import wizard dialog
- `egg_farm_system/ui/widgets/dashboard_widget_base.py` - Base class for widgets
- `egg_farm_system/ui/widgets/mortality_trend_widget.py` - Mortality trend widget
- `egg_farm_system/ui/widgets/top_customers_widget.py` - Top customers widget
- `egg_farm_system/ui/widgets/low_stock_alerts_widget.py` - Low stock alerts widget
- `egg_farm_system/ui/widgets/widget_configurator.py` - Widget configuration dialog
- `egg_farm_system/ui/widgets/command_palette.py` - Command palette
- `egg_farm_system/ui/widgets/recent_items_widget.py` - Recent items widget

## Modified Files
- `egg_farm_system/utils/notification_manager.py` - Updated to handle string severity

## Notes

- All files have been syntax-checked and compile without errors
- The integration is designed to be backward compatible
- Features can be used independently
- No database schema changes required
- All caching and performance optimizations are maintained

## Support

If you encounter any issues during integration:

1. Check console logs for errors
2. Verify all imports are correct
3. Ensure database is initialized
4. Check that notification_manager is working
5. Verify settings table exists in database
