"""
Main application window
"""
import sys
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLayout,
    QPushButton, QLabel, QComboBox, QMessageBox, QTabWidget, QStyle, QSizePolicy,
    QGraphicsOpacityEffect, QDialog, QScrollArea
)
import traceback
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Slot, QTimer
from PySide6.QtGui import QIcon, QFont

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.farms import FarmManager
from egg_farm_system.config import WINDOW_WIDTH, WINDOW_HEIGHT, SIDEBAR_WIDTH
from egg_farm_system.ui.dashboard import DashboardWidget
from egg_farm_system.ui.forms.farm_forms import FarmFormWidget
from egg_farm_system.ui.forms.production_forms import ProductionFormWidget
from egg_farm_system.ui.forms.inventory_forms import InventoryFormWidget
from egg_farm_system.ui.forms.party_forms import PartyFormWidget
from egg_farm_system.ui.forms.transaction_forms import TransactionFormWidget
from egg_farm_system.ui.reports.report_viewer import ReportViewerWidget
from egg_farm_system.ui.forms.settings_form import SettingsForm
from egg_farm_system.ui.forms.user_forms import UserManagementForm
from egg_farm_system.ui.forms.employee_forms import EmployeeManagementWidget
from egg_farm_system.ui.forms.equipment_forms import EquipmentFormWidget
from egg_farm_system.database.models import User # Added import
from egg_farm_system.ui.themes import ThemeManager # Added import
from egg_farm_system.utils.keyboard_shortcuts import ShortcutManager
from egg_farm_system.utils.notification_manager import get_notification_manager, NotificationSeverity
from egg_farm_system.ui.widgets.notification_center import NotificationCenterWidget
from egg_farm_system.ui.widgets.backup_restore_widget import BackupRestoreWidget
from egg_farm_system.ui.widgets.global_search_widget import GlobalSearchWidget
from egg_farm_system.utils.i18n import tr, get_i18n

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, current_user=None, app_version="1.0.0"):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle(tr("Egg Farm Management System"))
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.app_version = app_version
        
        # Initialize Theme - Default to Farm theme
        self.current_theme = ThemeManager.FARM
        ThemeManager.apply_theme(sys.modules['__main__'].app if hasattr(sys.modules['__main__'], 'app') else self, self.current_theme)

        # Initialize I18n
        get_i18n().language_changed.connect(self._update_texts)

        DatabaseManager.initialize()
        # Re-fetch the user to bind it to a new session for MainWindow's lifetime
        if current_user:
            session = DatabaseManager.get_session()
            try:
                self.current_user = session.query(User).filter_by(id=current_user.id).first()
            finally:
                session.close()

        self.farm_manager = FarmManager()
        
        # Initialize notification manager (don't check yet - badge not created)
        self.notification_manager = get_notification_manager()
        
        # Initialize keyboard shortcuts
        self.shortcut_manager = ShortcutManager(self)
        self._setup_keyboard_shortcuts()
        
        # Initialize navigation history
        from egg_farm_system.ui.widgets.breadcrumbs import NavigationHistory
        self.nav_history = NavigationHistory()
        
        # Initialize workflow automation and start task timer
        from egg_farm_system.utils.workflow_automation import get_workflow_automation
        self.workflow_automation = get_workflow_automation()
        self.workflow_timer = QTimer()
        self.workflow_timer.timeout.connect(self._run_workflow_tasks)
        self.workflow_timer.start(60000)  # Check every minute
        
        # Create main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Breadcrumbs
        from egg_farm_system.ui.widgets.breadcrumbs import BreadcrumbWidget
        self.breadcrumbs = BreadcrumbWidget()
        self.breadcrumbs.path_clicked.connect(self._on_breadcrumb_clicked)
        main_layout.addWidget(self.breadcrumbs)
        
        # Content area with sidebar
        content_layout = QHBoxLayout()
        
        # Create sidebar
        self.sidebar = self.create_sidebar()
        content_layout.addWidget(self.sidebar) # Remove stretch factor for sidebar

        # Create content area
        self.content_area = QFrame()
        self.content_area.setFrameShape(QFrame.NoFrame) # No border for content area
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0) # Remove margins
        self.content_area.setLayout(self.content_layout)
        content_layout.addWidget(self.content_area, 1) # Content area takes remaining space
        
        content_layout.setStretch(0, 0) # Sidebar does not stretch
        content_layout.setStretch(1, 1) # Content area stretches
        content_layout.setSizeConstraint(QLayout.SetNoConstraint) # Ignore size hints of children
        
        main_layout.addLayout(content_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Now that UI is created, check notifications and update badge
        self._check_notifications()
        
        # Load dashboard initially
        self.load_dashboard()
    
    def _update_texts(self, lang_code):
        """Update UI texts when language changes"""
        self.setWindowTitle(tr("Egg Farm Management System"))
        
        # Update sidebar buttons and labels
        for widget in self.sidebar.findChildren(QWidget):
            key = widget.property("i18n_key")
            if key:
                if isinstance(widget, QPushButton):
                    # For sidebar buttons, we might need to update full_text property too
                    # if it's used for tooltip/expansion
                    new_text = tr(key)
                    # If it has an icon (most do), we often prepend text. 
                    # But here buttons are " Icon  Text".
                    # The text set in create_sidebar was just text.
                    # Wait, create_sidebar sets text directly.
                    # CollapsibleGroup adds buttons.
                    
                    # Update displayed text
                    widget.setText(new_text)
                    
                    # Update full_text property if it exists (used by sidebar collapse logic)
                    if widget.property("full_text"):
                        widget.setProperty("full_text", new_text)
                        if not self.sidebar.property('collapsed'):
                             widget.setText(new_text)
                        else:
                             widget.setToolTip(new_text)
                
                elif isinstance(widget, QLabel):
                    widget.setText(tr(key))
                
                # Collapsible Group Titles
                # CollapsibleGroup is a QWidget but holds a button and label?
                # Actually CollapsibleGroup title is usually a button or label.
                # If CollapsibleGroup is custom widget, we might need to iterate it specifically.
                
        # Update CollapsibleGroup titles explicitly if they aren't caught above
        from egg_farm_system.ui.widgets.collapsible_group import CollapsibleGroup
        for group in self.sidebar.findChildren(CollapsibleGroup):
            key = group.property("i18n_key")
            if key:
                group.setTitle(tr(key))

        # Update specific buttons that might not be caught
        if hasattr(self, 'notification_btn'):
            self.notification_btn.setText(f"🔔 {tr('Notifications')}")
        
        if hasattr(self, 'theme_btn'):
            self.theme_btn.setText(f"🎨 {tr('Farm Theme')}")
            
        if hasattr(self, 'logout_button'):
            self.logout_button.setText(f"🚪 {tr('Logout')}")
            
        if hasattr(self, 'lang_btn'):
            # Update label based on current language
            label = "English" if lang_code == 'ps' else "پښتو"
            self.lang_btn.setText(f"🌐 {label}")

        # Refresh current page to apply translations to the active view
        self._refresh_current_page()

    def toggle_language(self):
        """Switch between English and Pashto"""
        current = get_i18n().current_lang
        new_lang = 'ps' if current == 'en' else 'en'
        get_i18n().set_language(new_lang)

    def create_sidebar(self):
        """Create left sidebar navigation with grouped collapsible sections"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMaximumWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #2c3e50;
            }
        """)

        # Scroll area for navigation
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Farm selector at top
        farm_layout = QHBoxLayout()
        farm_layout.setSpacing(5)
        self.farm_combo = QComboBox()
        self.farm_combo.setMinimumHeight(35)
        self.farm_combo.setStyleSheet("""
            QComboBox {
                background-color: #34495e;
                color: white;
                border: 1px solid #4a5f7f;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:hover {
                background-color: #3d566e;
            }
        """)
        self.farm_combo.currentIndexChanged.connect(self.on_farm_changed)
        self.refresh_farm_list()
        self.farm_combo_widget = self.farm_combo
        farm_layout.addWidget(self.farm_combo)
        layout.addLayout(farm_layout)

        # Import collapsible group
        from egg_farm_system.ui.widgets.collapsible_group import CollapsibleGroup

        # Dashboard (always visible, not in a group)
        dashboard_btn = QPushButton(tr("Dashboard"))
        dashboard_btn.setProperty("i18n_key", "Dashboard")
        dashboard_btn.setProperty("full_text", "Dashboard") # Ensure consistent property
        dashboard_btn.setMinimumHeight(40)
        dashboard_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                border: none;
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        dashboard_btn.clicked.connect(lambda: self._safe_load(self.load_dashboard))
        layout.addWidget(dashboard_btn)

        # Helper to set i18n key on buttons added to groups
        def add_btn_with_i18n(group, text, callback, icon):
            btn = group.add_button(tr(text), callback, icon)
            btn.setProperty("i18n_key", text)
            btn.setProperty("full_text", text) # CollapsibleGroup might set this, but ensure it matches key
            return btn

        # Egg Management Group
        egg_group = CollapsibleGroup(tr("Egg Management"))
        egg_group.setProperty("i18n_key", "Egg Management")
        add_btn_with_i18n(egg_group, "Production", lambda: self._safe_load(self.load_production), 'icon_egg.svg')
        add_btn_with_i18n(egg_group, "Stock", lambda: self._safe_load(self.load_egg_stock), 'icon_egg.svg')
        add_btn_with_i18n(egg_group, "Expenses", lambda: self._safe_load(self.load_egg_expenses), 'icon_expenses.svg')
        layout.addWidget(egg_group)

        # Farm Operations Group
        farm_group = CollapsibleGroup(tr("Farm Operations"))
        farm_group.setProperty("i18n_key", "Farm Operations")
        add_btn_with_i18n(farm_group, "Farm Management", lambda: self._safe_load(self.load_farm_management), 'icon_farm.svg')
        add_btn_with_i18n(farm_group, "Flock Management", lambda: self._safe_load(self.load_flock_management), 'icon_farm.svg')
        add_btn_with_i18n(farm_group, "Feed Management", lambda: self._safe_load(self.load_feed_management), 'icon_feed.svg')
        add_btn_with_i18n(farm_group, "Inventory", lambda: self._safe_load(self.load_inventory), 'icon_inventory.svg')
        add_btn_with_i18n(farm_group, "Equipment", lambda: self._safe_load(self.load_equipment_management), 'icon_inventory.svg')
        layout.addWidget(farm_group)

        # Transactions Group
        trans_group = CollapsibleGroup(tr("Transactions"))
        trans_group.setProperty("i18n_key", "Transactions")
        add_btn_with_i18n(trans_group, "Sales", lambda: self._safe_load(self.load_sales), 'icon_sales.svg')
        add_btn_with_i18n(trans_group, "Purchases", lambda: self._safe_load(self.load_purchases), 'icon_purchases.svg')
        add_btn_with_i18n(trans_group, "Sell Raw Material", lambda: self._safe_load(self.load_raw_material_sale), 'icon_sales.svg') 
        add_btn_with_i18n(trans_group, "Expenses", lambda: self._safe_load(self.load_expenses), 'icon_expenses.svg')
        add_btn_with_i18n(trans_group, "Parties", lambda: self._safe_load(self.load_parties), 'icon_parties.svg')
        layout.addWidget(trans_group)

        # Reports & Analytics Group
        reports_group = CollapsibleGroup(tr("Reports & Analytics"))
        reports_group.setProperty("i18n_key", "Reports & Analytics")
        add_btn_with_i18n(reports_group, "Reports", lambda: self._safe_load(self.load_reports), 'icon_reports.svg')
        add_btn_with_i18n(reports_group, "Analytics", lambda: self._safe_load(self.load_analytics), 'icon_reports.svg')
        add_btn_with_i18n(reports_group, "Cash Flow", lambda: self._safe_load(self.load_cash_flow), 'icon_reports.svg')
        layout.addWidget(reports_group)

        # System Group
        system_group = CollapsibleGroup(tr("System"))
        system_group.setProperty("i18n_key", "System")
        add_btn_with_i18n(system_group, "Settings", lambda: self._safe_load(self.load_settings), 'icon_reports.svg')
        add_btn_with_i18n(system_group, "Backup & Restore", lambda: self._safe_load(self.load_backup_restore), 'icon_reports.svg')
        add_btn_with_i18n(system_group, "Workflow Automation", lambda: self._safe_load(self.load_workflow_automation), 'icon_reports.svg')
        add_btn_with_i18n(system_group, "Audit Trail", lambda: self._safe_load(self.load_audit_trail), 'icon_reports.svg')
        add_btn_with_i18n(system_group, "Email Config", lambda: self._safe_load(self.load_email_config), 'icon_reports.svg')
        layout.addWidget(system_group)

        # Admin Group (only for admins)
        try:
            if hasattr(self, 'current_user') and self.current_user and getattr(self.current_user, 'role', '') == 'admin':
                admin_group = CollapsibleGroup(tr("Administration"))
                admin_group.setProperty("i18n_key", "Administration")
                add_btn_with_i18n(admin_group, "Users", lambda: self._safe_load(self.load_users_management), 'icon_parties.svg')
                add_btn_with_i18n(admin_group, "Employees", lambda: self._safe_load(self.load_employees_management), 'icon_parties.svg')
                layout.addWidget(admin_group)
        except Exception:
            pass

        layout.addStretch()

        # Bottom buttons
        bottom_layout = QVBoxLayout()
        bottom_layout.setSpacing(5)
        
        # Premium Notification button
        notif_layout = QHBoxLayout()
        self.notification_btn = QPushButton(f"🔔 {tr('Notifications')}")
        self.notification_btn.setProperty("i18n_key", "Notifications") # Special handling needed for icon prefix
        self.notification_btn.setMinimumHeight(42)
        self.notification_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 18px;
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e,
                    stop:1 #2c3e50);
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d566e,
                    stop:1 #34495e);
            }
        """)
        self.notification_btn.clicked.connect(self.show_notifications)
        notif_layout.addWidget(self.notification_btn)
        
        # Premium Notification badge
        self.notification_badge = QLabel("0")
        self.notification_badge.setObjectName('notification_badge')
        self.notification_badge.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c,
                    stop:1 #c0392b);
                color: white;
                border-radius: 12px;
                padding: 3px 8px;
                font-weight: 700;
                font-size: 9pt;
                min-width: 22px;
                min-height: 22px;
            }
        """)
        self.notification_badge.setVisible(False)
        self.notification_badge.setAlignment(Qt.AlignCenter)
        notif_layout.addWidget(self.notification_badge)
        bottom_layout.addLayout(notif_layout)
        
        # Language Switcher
        self.lang_btn = QPushButton("🌐 پښتو")
        self.lang_btn.setMinimumHeight(42)
        self.lang_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 18px;
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e,
                    stop:1 #2c3e50);
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d566e,
                    stop:1 #34495e);
            }
        """)
        self.lang_btn.clicked.connect(self.toggle_language)
        bottom_layout.addWidget(self.lang_btn)

        # Premium Theme toggle
        self.theme_btn = QPushButton(f"🎨 {tr('Farm Theme')}")
        self.theme_btn.setMinimumHeight(42)
        self.theme_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 18px;
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e,
                    stop:1 #2c3e50);
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d566e,
                    stop:1 #34495e);
            }
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        bottom_layout.addWidget(self.theme_btn)
        
        # Premium Logout button
        logout_btn = QPushButton(f"🚪 {tr('Logout')}")
        logout_btn.setMinimumHeight(42)
        logout_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 18px;
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c,
                    stop:1 #c0392b);
                color: white;
                border-radius: 8px;
                font-weight: 600;
                font-size: 11pt;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063,
                    stop:1 #e74c3c);
            }
        """)
        logout_btn.clicked.connect(self._on_logout)
        self.logout_button = logout_btn
        bottom_layout.addWidget(logout_btn)
        
        layout.addLayout(bottom_layout)
        
        scroll.setWidget(container)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll)
        
        return sidebar

    def _safe_load(self, callback):
        """Call a page-load callback and handle exceptions with logging and UI alert."""
        try:
            callback()
        except Exception as e:
            logger.exception(f"Error loading page via {getattr(callback, '__name__', repr(callback))}: {e}")
            # show brief message to user
            try:
                QMessageBox.critical(self, "Error", f"Failed to load page: {e}\nSee logs for details")
            except Exception:
                # If UI alert fails, print traceback
                print("Failed to show error message")
                traceback.print_exc()
    
    def refresh_farm_list(self):
        """Refresh farm combo box"""
        try:
            self.farm_combo.clear()
            farms = self.farm_manager.get_all_farms()
            for farm in farms:
                self.farm_combo.addItem(farm.name, farm.id)
        except Exception as e:
            logger.error(f"Error refreshing farm list: {e}")
    
    def get_current_farm_id(self):
        """Get selected farm ID"""
        return self.farm_combo.currentData()
    
    def on_farm_changed(self):
        """Handle farm selection change"""
        if self.farm_combo.count() > 0:
            # Propagate new farm id to the active content widget when possible
            try:
                current_widget = None
                content_layout = getattr(self, 'content_layout', None)
                if content_layout and content_layout.count():
                    current_widget = content_layout.itemAt(0).widget()

                farm_id = self.get_current_farm_id()
                if current_widget is None:
                    return

                # If widget exposes a setter or attribute for farm id, update it
                if hasattr(current_widget, 'set_farm_id') and callable(current_widget.set_farm_id):
                    current_widget.set_farm_id(farm_id)
                elif hasattr(current_widget, 'farm_id'):
                    try:
                        current_widget.farm_id = farm_id
                    except Exception:
                        pass

                # If widget implements a refresh method, call it to reload data
                if hasattr(current_widget, 'refresh_data') and callable(current_widget.refresh_data):
                    current_widget.refresh_data()
                elif hasattr(current_widget, 'refresh_stock') and callable(current_widget.refresh_stock):
                    current_widget.refresh_stock()
            except Exception as e:
                logger.exception(f"Error handling farm change: {e}")
    
    def clear_content(self):
        """Clear content area"""
        while self.content_layout.count():
            self.content_layout.takeAt(0).widget().deleteLater()
    
    def load_dashboard(self):
        """Load dashboard widget"""
        self.clear_content()
        dashboard = DashboardWidget(self.get_current_farm_id())
        dashboard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(dashboard)
        self._update_breadcrumbs("Dashboard", "dashboard")
        self._add_to_history("Dashboard", "dashboard", self.load_dashboard)
    
    def load_farm_management(self):
        """Load farm management widget"""
        self.clear_content()
        farm_widget = FarmFormWidget()
        farm_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        farm_widget.farm_changed.connect(self.refresh_farm_list)
        self.content_layout.addWidget(farm_widget)
        self._update_breadcrumbs("Farm Management", "farm_management")
        self._add_to_history("Farm Management", "farm_management", self.load_farm_management)

    def load_flock_management(self):
        """Load flock management widget"""
        self.clear_content()
        from egg_farm_system.ui.forms.flock_forms import FlockManagementWidget
        flock_widget = FlockManagementWidget()
        flock_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(flock_widget)
        self._update_breadcrumbs("Flock Management", "flock_management")
        self._add_to_history("Flock Management", "flock_management", self.load_flock_management)
    
    def load_production(self):
        """Load egg production widget"""
        self.clear_content()
        prod_widget = ProductionFormWidget(self.get_current_farm_id())
        prod_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(prod_widget)
        self._update_breadcrumbs("Egg Production", "production")
        self._add_to_history("Egg Production", "production", self.load_production)
    
    def load_egg_stock(self):
        """Load egg stock management widget"""
        self.clear_content()
        from egg_farm_system.ui.widgets.egg_stock_widget import EggStockWidget
        stock_widget = EggStockWidget()
        stock_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if self.get_current_farm_id():
            stock_widget.set_farm_id(self.get_current_farm_id())
        self.content_layout.addWidget(stock_widget)
        self._update_breadcrumbs("Egg Stock", "egg_stock")
        self._add_to_history("Egg Stock", "egg_stock", self.load_egg_stock)
    
    def load_egg_expenses(self):
        """Load egg expense management widget"""
        self.clear_content()
        from egg_farm_system.ui.widgets.egg_expense_widget import EggExpenseWidget
        expense_widget = EggExpenseWidget()
        expense_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(expense_widget)
        self._update_breadcrumbs("Egg Expenses", "egg_expenses")
        self._add_to_history("Egg Expenses", "egg_expenses", self.load_egg_expenses)
    
    def load_feed_management(self):
        """Load feed management widget"""
        self.clear_content()
        from egg_farm_system.ui.forms.feed_forms import FeedFormWidget
        feed_widget = FeedFormWidget()
        feed_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(feed_widget)
        self._update_breadcrumbs("Feed Management", "feed")
        self._add_to_history("Feed Management", "feed", self.load_feed_management)
    
    def load_inventory(self):
        """Load inventory widget"""
        self.clear_content()
        inventory_widget = InventoryFormWidget()
        inventory_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(inventory_widget)
        self._update_breadcrumbs("Inventory", "inventory")
        self._add_to_history("Inventory", "inventory", self.load_inventory)

    def load_equipment_management(self):
        """Load equipment management widget"""
        self.clear_content()
        equipment_widget = EquipmentFormWidget(self.get_current_farm_id())
        equipment_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(equipment_widget)
    
    def load_parties(self):
        """Load parties widget"""
        self.clear_content()
        party_widget = PartyFormWidget()
        party_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(party_widget)
        self._update_breadcrumbs("Parties", "parties")
        self._add_to_history("Parties", "parties", self.load_parties)
    
    def load_sales(self):
        """Load sales widget"""
        self.clear_content()
        sales_widget = TransactionFormWidget("sales", self.get_current_farm_id(), current_user=self.current_user)
        sales_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(sales_widget)
        self._update_breadcrumbs("Sales", "sales")
        self._add_to_history("Sales", "sales", self.load_sales)
    
    def load_purchases(self):
        """Load purchases widget"""
        self.clear_content()
        purchases_widget = TransactionFormWidget("purchases", self.get_current_farm_id(), current_user=self.current_user)
        purchases_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(purchases_widget)
        self._update_breadcrumbs("Purchases", "purchases")
        self._add_to_history("Purchases", "purchases", self.load_purchases)
    
    def load_expenses(self):
        """Load expenses widget"""
        self.clear_content()
        expenses_widget = TransactionFormWidget("expenses", self.get_current_farm_id(), current_user=self.current_user)
        expenses_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(expenses_widget)
        self._update_breadcrumbs("Expenses", "expenses")
        self._add_to_history("Expenses", "expenses", self.load_expenses)
    
    def load_raw_material_sale(self):
        """Load raw material sale dialog"""
        from egg_farm_system.ui.forms.raw_material_sale_dialog import RawMaterialSaleDialog
        dialog = RawMaterialSaleDialog(self)
        dialog.sale_saved.connect(self._refresh_current_page) # Refresh current view if sale is saved
        dialog.exec()
        self._update_breadcrumbs("Sell Raw Material", "raw_material_sale")
        self._add_to_history("Sell Raw Material", "raw_material_sale", self.load_raw_material_sale)
    
    def load_employees_management():
        """Load employees management widget"""
        self.clear_content()
        employees_widget = EmployeeManagementWidget()
        employees_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(employees_widget)
        
    def load_reports(self):
        """Load reports widget"""
        self.clear_content()
        reports_widget = ReportViewerWidget(self.get_current_farm_id())
        reports_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(reports_widget)
        self._update_breadcrumbs("Reports", "reports")
        self._add_to_history("Reports", "reports", self.load_reports)

    def load_users_management(self):
        """Load user management UI"""
        self.clear_content()
        users_widget = UserManagementForm()
        users_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(users_widget)

    def load_settings(self):
        """Load settings UI"""
        self.clear_content()
        settings_widget = SettingsForm()
        settings_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(settings_widget)
    
    def load_backup_restore(self):
        """Load backup and restore widget"""
        self.clear_content()
        backup_widget = BackupRestoreWidget()
        backup_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(backup_widget)
        self._update_breadcrumbs("Backup & Restore", "backup_restore")
        self._add_to_history("Backup & Restore", "backup_restore", self.load_backup_restore)
    
    def load_analytics(self):
        """Load analytics dashboard"""
        self.clear_content()
        from egg_farm_system.ui.widgets.analytics_dashboard import AnalyticsDashboardWidget
        analytics_widget = AnalyticsDashboardWidget(self.get_current_farm_id())
        analytics_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(analytics_widget)
        self._update_breadcrumbs("Analytics", "analytics")
        self._add_to_history("Analytics", "analytics", self.load_analytics)
    
    def load_cash_flow(self):
        """Load cash flow management widget"""
        self.clear_content()
        from egg_farm_system.ui.widgets.cash_flow_widget import CashFlowWidget
        cash_flow_widget = CashFlowWidget(self.get_current_farm_id())
        cash_flow_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(cash_flow_widget)
        self._update_breadcrumbs("Cash Flow", "cash_flow")
        self._add_to_history("Cash Flow", "cash_flow", self.load_cash_flow)
    
    def load_workflow_automation(self):
        """Load workflow automation widget"""
        self.clear_content()
        from egg_farm_system.ui.widgets.workflow_automation_widget import WorkflowAutomationWidget
        workflow_widget = WorkflowAutomationWidget()
        workflow_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(workflow_widget)
        self._update_breadcrumbs("Workflow Automation", "workflow")
        self._add_to_history("Workflow Automation", "workflow", self.load_workflow_automation)
    
    def load_audit_trail(self):
        """Load audit trail viewer"""
        self.clear_content()
        from egg_farm_system.ui.widgets.audit_trail_viewer import AuditTrailViewerWidget
        audit_widget = AuditTrailViewerWidget()
        audit_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(audit_widget)
        self._update_breadcrumbs("Audit Trail", "audit_trail")
        self._add_to_history("Audit Trail", "audit_trail", self.load_audit_trail)
    
    def load_email_config(self):
        """Load email configuration widget"""
        self.clear_content()
        from egg_farm_system.ui.widgets.email_config_widget import EmailConfigWidget
        email_widget = EmailConfigWidget()
        email_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(email_widget)
        self._update_breadcrumbs("Email Configuration", "email_config")
        self._add_to_history("Email Configuration", "email_config", self.load_email_config)
    
    def show_notifications(self):
        """Show notification center"""
        from PySide6.QtWidgets import QDialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Notifications")
        dialog.setMinimumSize(500, 600)
        layout = QVBoxLayout(dialog)
        notification_widget = NotificationCenterWidget()
        layout.addWidget(notification_widget)
        dialog.exec()
        self._update_notification_badge()
    
    def _check_notifications(self):
        """Check for notifications and update badge"""
        try:
            from egg_farm_system.modules.inventory import InventoryManager
            inventory_manager = InventoryManager()
            self.notification_manager.check_low_stock(inventory_manager)
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
        
        self._update_notification_badge()
        # Listen for notification changes
        self.notification_manager.add_listener(self._on_notification_changed)
    
    def _update_notification_badge(self):
        """Update notification badge count"""
        if not hasattr(self, 'notification_badge') or self.notification_badge is None:
            return  # Badge not created yet
        
        unread_count = self.notification_manager.get_unread_count()
        if unread_count > 0:
            self.notification_badge.setText(str(unread_count))
            self.notification_badge.setVisible(True)
        else:
            self.notification_badge.setVisible(False)
    
    def _on_notification_changed(self, notification=None):
        """Handle notification changes"""
        self._update_notification_badge()
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            "dashboard": self.load_dashboard,
            "farm_management": self.load_farm_management,
            "production": self.load_production,
            "feed": self.load_feed_management,
            "inventory": self.load_inventory,
            "parties": self.load_parties,
            "sales": self.load_sales,
            "purchases": self.load_purchases,
            "expenses": self.load_expenses,
            "reports": self.load_reports,
            "settings": self.load_settings,
            "refresh": self._refresh_current_page,
            "help": self._show_help,
            "search": self._open_global_search,
        }
        self.shortcut_manager.setup_default_shortcuts(shortcuts)
    
    def _open_global_search(self):
        """Open global search dialog"""
        dialog = GlobalSearchWidget(self)
        dialog.item_selected.connect(self._on_search_result_selected)
        dialog.exec()
    
    def _on_search_result_selected(self, item_data: dict):
        """Handle search result selection"""
        result_type = item_data.get('type', '')
        
        navigation_map = {
            'farm': self.load_farm_management,
            'shed': self.load_farm_management,
            'flock': self.load_farm_management,
            'party': self.load_parties,
            'sale': self.load_sales,
            'purchase': self.load_purchases,
            'expense': self.load_expenses,
            'production': self.load_production,
            'material': self.load_inventory,
            'feed': self.load_feed_management
        }
        
        handler = navigation_map.get(result_type)
        if handler:
            handler()
    
    def _run_workflow_tasks(self):
        """Run pending workflow tasks (called by timer)"""
        try:
            self.workflow_automation.run_pending_tasks()
        except Exception as e:
            logger.error(f"Error running workflow tasks: {e}")
    
    def _refresh_current_page(self):
        """Refresh current page"""
        try:
            current_widget = None
            if self.content_layout.count():
                current_widget = self.content_layout.itemAt(0).widget()
            
            if current_widget and hasattr(current_widget, 'refresh_data'):
                current_widget.refresh_data()
        except Exception as e:
            logger.error(f"Error refreshing page: {e}")
    
    def _show_help(self):
        """Show help dialog"""
        from egg_farm_system.ui.widgets.help_system import HelpDialog
        dialog = HelpDialog(self)
        dialog.exec()
    
    def _update_breadcrumbs(self, page_name: str, page_path: str):
        """Update breadcrumb navigation"""
        paths = [
            {'name': 'Home', 'path': 'dashboard'},
            {'name': page_name, 'path': page_path}
        ]
        self.breadcrumbs.set_paths(paths)
    
    def _add_to_history(self, name: str, path: str, callback: callable):
        """Add page to navigation history"""
        self.nav_history.add(name, path, callback)
    
    def _on_breadcrumb_clicked(self, path: str):
        """Handle breadcrumb click"""
        navigation_map = {
            'dashboard': self.load_dashboard,
            'farm_management': self.load_farm_management,
            'production': self.load_production,
            'feed': self.load_feed_management,
            'inventory': self.load_inventory,
            'parties': self.load_parties,
            'sales': self.load_sales,
            'purchases': self.load_purchases,
            'expenses': self.load_expenses,
            'reports': self.load_reports,
        }
        
        handler = navigation_map.get(path)
        if handler:
            handler()
    
    def close_application(self):
        """Close application"""
        DatabaseManager.close()
        self.close()
    
    def closeEvent(self, event):
        """Handle window close"""
        DatabaseManager.close()
        event.accept()

    def toggle_sidebar(self):
        """Toggle sidebar collapsed state"""
        try:
            collapsed = bool(self.sidebar.property('collapsed'))
            new_state = not collapsed

            # animate width
            start_w = self.sidebar.width()
            end_w = 56 if new_state else SIDEBAR_WIDTH
            anim = QPropertyAnimation(self.sidebar, b"maximumWidth")
            anim.setDuration(220)
            anim.setStartValue(start_w)
            anim.setEndValue(end_w)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            self._sidebar_anim = anim
            anim.start()

            # toggle labels/tooltips immediately
            for btn in self.sidebar.findChildren(QPushButton):
                # keep the collapse button visible and unchanged
                if btn.objectName() == 'collapse_btn':
                    continue
                full = btn.property('full_text')
                if full:
                    # animate button opacity when switching text for smoother transition
                    effect = btn.graphicsEffect()
                    if not isinstance(effect, QGraphicsOpacityEffect):
                        effect = QGraphicsOpacityEffect(btn)
                        btn.setGraphicsEffect(effect)

                    if new_state:
                        # fade out, then clear text and set tooltip
                        fade_out = QPropertyAnimation(effect, b"opacity", self)
                        fade_out.setDuration(140)
                        fade_out.setStartValue(1.0)
                        fade_out.setEndValue(0.0)
                        fade_out.setEasingCurve(QEasingCurve.InOutQuad)
                        fade_out.finished.connect(lambda b=btn, f=full: (b.setProperty('cached_text', f), b.setText(""), b.setToolTip(f), b.graphicsEffect().setOpacity(1.0)))
                        fade_out.start()
                        if not hasattr(self, '_ui_anims'):
                            self._ui_anims = []
                        self._ui_anims.append(fade_out)
                    else:
                        # restore text, then fade in
                        cached = btn.property('cached_text') or full
                        btn.setText(cached)
                        btn.setToolTip("")
                        effect.setOpacity(0.0)
                        fade_in = QPropertyAnimation(effect, b"opacity", self)
                        fade_in.setDuration(160)
                        fade_in.setStartValue(0.0)
                        fade_in.setEndValue(1.0)
                        fade_in.setEasingCurve(QEasingCurve.InOutQuad)
                        fade_in.start()
                        if not hasattr(self, '_ui_anims'):
                            self._ui_anims = []
                        self._ui_anims.append(fade_in)

            # fade title and farm label for smooth effect
            def animate_opacity(w, start_val, end_val, duration=200, hide_after=False):
                if w is None:
                    return None
                effect = w.graphicsEffect()
                if not isinstance(effect, QGraphicsOpacityEffect):
                    effect = QGraphicsOpacityEffect(w)
                    w.setGraphicsEffect(effect)
                anim = QPropertyAnimation(effect, b"opacity", self)
                anim.setDuration(duration)
                anim.setStartValue(start_val)
                anim.setEndValue(end_val)
                anim.setEasingCurve(QEasingCurve.InOutQuad)

                if hide_after:
                    @Slot()
                    def _on_finished():
                        w.setVisible(False)
                        if end_val > 0:
                            effect.setOpacity(1.0)
                    anim.finished.connect(_on_finished)
                else:
                    anim.finished.connect(lambda: None)

                # store reference to avoid GC
                if not hasattr(self, '_ui_anims'):
                    self._ui_anims = []
                self._ui_anims.append(anim)
                anim.start()
                return anim

            title = getattr(self, 'title_widget', None) or self.sidebar.findChild(QLabel, 'app_title')
            logo = getattr(self, 'logo_widget', None)
            farm_combo = getattr(self, 'farm_combo_widget', None)
            farm_label = getattr(self, 'farm_label', None)

            if new_state:
                # collapsing: fade out
                animate_opacity(title, 1.0, 0.0, 200, hide_after=True)
                animate_opacity(farm_label, 1.0, 0.0, 180, hide_after=True)
                if logo:
                    animate_opacity(logo, 1.0, 0.0, 160, hide_after=True)
            else:
                # expanding: show then fade in
                if title:
                    title.setVisible(True)
                    animate_opacity(title, 0.0, 1.0, 220, hide_after=False)
                if farm_label:
                    farm_label.setVisible(True)
                    animate_opacity(farm_label, 0.0, 1.0, 200, hide_after=False)
                if logo:
                    logo.setVisible(True)
                    animate_opacity(logo, 0.0, 1.0, 200, hide_after=False)

            # swap chevron icon to indicate action
            try:
                if new_state and getattr(self, '_chev_right', None) and self._chev_right.exists():
                    self.collapse_btn.setIcon(QIcon(str(self._chev_right)))
                elif (not new_state) and getattr(self, '_chev_left', None) and self._chev_left.exists():
                    self.collapse_btn.setIcon(QIcon(str(self._chev_left)))
            except Exception:
                pass

            self.sidebar.setProperty('collapsed', new_state)
            # refresh style
            self.sidebar.style().unpolish(self.sidebar)
            self.sidebar.style().polish(self.sidebar)
            self.sidebar.update()
        except Exception as e:
            logger.exception(f"Failed to toggle sidebar: {e}")

    def toggle_theme(self):
        """Cycle through available themes: Farm -> Light -> Dark -> Farm"""
        from PySide6.QtWidgets import QApplication
        if self.current_theme == ThemeManager.FARM:
            self.current_theme = ThemeManager.LIGHT
            theme_name = "Light Theme"
        elif self.current_theme == ThemeManager.LIGHT:
            self.current_theme = ThemeManager.DARK
            theme_name = "Dark Theme"
        else:
            self.current_theme = ThemeManager.FARM
            theme_name = "Farm Theme"
            
        app = QApplication.instance()
        if app:
            ThemeManager.apply_theme(app, self.current_theme)
            # Update button text
            if hasattr(self, 'theme_btn'):
                self.theme_btn.setText(f"🎨 {theme_name}")
            
    def _on_logout(self):
        """Log out current user and show login dialog; if cancelled, exit app."""
        from ui.forms.login_dialog import LoginDialog
        # confirm logout
        reply = QMessageBox.question(self, 'Confirm Logout', 'Are you sure you want to logout?', QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        dlg = LoginDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.current_user = getattr(dlg, 'user', None)
            # refresh nav button availability and update user label
            for btn in self.sidebar.findChildren(QPushButton):
                full = btn.property('full_text')
                if full in ('Settings', 'Users'):
                    if not (self.current_user and getattr(self.current_user, 'role', '') == 'admin'):
                        btn.setEnabled(False)
                        btn.setToolTip('Admin only')
                    else:
                        btn.setEnabled(True)
                        btn.setToolTip('')
            try:
                if self.current_user:
                    self.user_label.setText(f"User: {getattr(self.current_user, 'username', '')}")
                else:
                    self.user_label.setText('Not logged in')
            except Exception:
                pass
        else:
            # user cancelled login -> exit application
            self.close_application()

    def _on_change_password(self):
        """Open password change dialog for current user."""
        from ui.forms.password_change_dialog import PasswordChangeDialog
        if not self.current_user:
            return
        dlg = PasswordChangeDialog(self, target_user_id=self.current_user.id, force=False)
        dlg.exec()
