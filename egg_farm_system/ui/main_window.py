"""
Main application window
"""

# pylint: disable=too-many-lines,too-many-public-methods

import sys
import logging
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Slot, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import traceback
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence, QShortcut

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
from egg_farm_system.database.models import User
from egg_farm_system.ui.themes import ThemeManager
from egg_farm_system.utils.keyboard_shortcuts import ShortcutManager
from egg_farm_system.utils.notification_manager import get_notification_manager, NotificationSeverity
from egg_farm_system.ui.widgets.notification_center import NotificationCenterWidget
from egg_farm_system.ui.widgets.backup_restore_widget import BackupRestoreWidget
from egg_farm_system.ui.widgets.global_search_widget import GlobalSearchWidget
from egg_farm_system.utils.i18n import tr, get_i18n
from egg_farm_system.ui.animation_helper import AnimationHelper
from egg_farm_system.ui.widgets.command_palette import CommandPalette
from egg_farm_system.ui.widgets.import_wizard import ImportWizard
from egg_farm_system.utils.alert_scheduler import AlertScheduler

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
        self.anim = None
        
        # Initialize Theme - Load from settings or use default
        from egg_farm_system.modules.settings import SettingsManager
        saved_theme = SettingsManager.get_setting('app_theme', ThemeManager.FARM)
        self.current_theme = saved_theme if saved_theme in [ThemeManager.LIGHT, ThemeManager.DARK, ThemeManager.FARM] else ThemeManager.FARM
        ThemeManager.set_current_theme(self.current_theme)
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
        
        # Initialize session timeout (30 minutes of inactivity)
        self.last_activity = datetime.now()
        self.session_timeout_minutes = 30
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._check_session_timeout)
        self.session_timer.start(60000)  # Check every minute
        
        # Install event filter to track user activity
        self.installEventFilter(self)
        
        # Initialize workflow automation and start task timer
        from egg_farm_system.utils.workflow_automation import get_workflow_automation
        self.workflow_automation = get_workflow_automation()
        self.workflow_timer = QTimer()
        self.workflow_timer.timeout.connect(self._run_workflow_tasks)
        self.workflow_timer.start(60000)  # Check every minute
        
        # Initialize alert scheduler
        self.alert_scheduler = AlertScheduler()
        self.alert_scheduler.start(interval_minutes=30)  # Check alerts every 30 minutes
        
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
        # Application menu for quick actions
        try:
            menubar = self.menuBar()
            actions_menu = menubar.addMenu(tr("Actions"))
            purchase_packaging_action = QAction(tr("Purchase Packaging"), self)
            purchase_packaging_action.triggered.connect(self.open_packaging_purchase_dialog)
            actions_menu.addAction(purchase_packaging_action)
        except Exception:
            # menu creation should not break startup
            logger.exception("Failed to create actions menu")
        
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
                    new_text = tr(key)
                    widget.setText(new_text)
                    if widget.property("full_text"):
                        widget.setProperty("full_text", new_text)
                        if not self.sidebar.property('collapsed'):
                            widget.setText(new_text)
                        else:
                            widget.setToolTip(new_text)
                elif isinstance(widget, QLabel):
                    widget.setText(tr(key))
                
        # Update CollapsibleGroup titles explicitly
        from egg_farm_system.ui.widgets.collapsible_group import CollapsibleGroup
        for group in self.sidebar.findChildren(CollapsibleGroup):
            key = group.property("i18n_key")
            if key:
                group.setTitle(tr(key))

        # Update specific buttons
        if hasattr(self, 'notification_btn'):
            self.notification_btn.setText(f"🔔 {tr('Notifications')}")
        
        if hasattr(self, 'theme_btn'):
            self.theme_btn.setText(f"🎨 {tr('Farm Theme')}")
            
        if hasattr(self, 'logout_button'):
            self.logout_button.setText(f"🚪 {tr('Logout')}")
            
        if hasattr(self, 'lang_btn'):
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
        sidebar.setFixedWidth(SIDEBAR_WIDTH) # Fix width to prevent squashing
        # No hardcoded styles - let theme handle it

        # Scroll area for navigation
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header layout (Collapse btn + Farm selector)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)
        
        # Collapse Button
        self.collapse_btn = QPushButton()
        self.collapse_btn.setObjectName("collapse_btn")
        self.collapse_btn.setFixedSize(35, 35)
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        # Remove hardcoded styles - global theme handles it
        # Load chevron icons
        from egg_farm_system.config import get_asset_path
        self._chev_left = Path(get_asset_path('icon_chevron_left.svg'))
        self._chev_right = Path(get_asset_path('icon_chevron_right.svg'))
        
        if self._chev_left.exists():
            self.collapse_btn.setIcon(QIcon(str(self._chev_left)))
            self.collapse_btn.setIconSize(QSize(20, 20))
        else:
            self.collapse_btn.setText("≡")
            
        self.collapse_btn.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.collapse_btn)

        # Farm selector
        self.farm_combo = QComboBox()
        self.farm_combo.setMinimumHeight(35)
        self.farm_combo.setProperty('class', 'sidebar-combo')
        # No hardcoded styles - global theme handles it
        self.farm_combo.currentIndexChanged.connect(self.on_farm_changed)
        self.refresh_farm_list()
        self.farm_combo_widget = self.farm_combo
        header_layout.addWidget(self.farm_combo)
        
        layout.addLayout(header_layout)

        # Import collapsible group
        from egg_farm_system.ui.widgets.collapsible_group import CollapsibleGroup

        # Dashboard (always visible, not in a group)
        dashboard_btn = QPushButton(tr("Dashboard"))
        dashboard_btn.setProperty("i18n_key", "Dashboard")
        dashboard_btn.setProperty("full_text", "Dashboard")
        dashboard_btn.setProperty('class', 'sidebar-dashboard')
        dashboard_btn.setMinimumHeight(40)
        # No hardcoded styles - global theme handles it
        dashboard_btn.clicked.connect(lambda: self._safe_load(self.load_dashboard))
        layout.addWidget(dashboard_btn)

        # Helper to set i18n key on buttons added to groups
        def add_btn_with_i18n(group, text, callback, icon):
            btn = group.add_button(tr(text), callback, icon)
            btn.setProperty("i18n_key", text)
            btn.setProperty("full_text", text)
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
        add_btn_with_i18n(system_group, "Import Data", self.show_import_wizard, 'icon_reports.svg')
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
        
        # Notification button
        notif_layout = QHBoxLayout()
        self.notification_btn = QPushButton(f"🔔 {tr('Notifications')}")
        self.notification_btn.setProperty("i18n_key", "Notifications")
        self.notification_btn.setProperty('class', 'sidebar-action')
        self.notification_btn.setMinimumHeight(42)
        self.notification_btn.clicked.connect(self.show_notifications)
        notif_layout.addWidget(self.notification_btn)
        
        # Notification badge
        self.notification_badge = QLabel("0")
        self.notification_badge.setObjectName('notification_badge')
        self.notification_badge.setProperty('class', 'badge-unread')
        self.notification_badge.setVisible(False)
        self.notification_badge.setAlignment(Qt.AlignCenter)
        notif_layout.addWidget(self.notification_badge)
        bottom_layout.addLayout(notif_layout)
        
        # Language Switcher
        self.lang_btn = QPushButton(tr("🌐 پښتو"))
        self.lang_btn.setProperty('class', 'sidebar-action')
        self.lang_btn.setMinimumHeight(42)
        self.lang_btn.clicked.connect(self.toggle_language)
        bottom_layout.addWidget(self.lang_btn)

        # Theme toggle
        self.theme_btn = QPushButton(f"🎨 {tr('Farm Theme')}")
        self.theme_btn.setProperty('class', 'sidebar-action')
        self.theme_btn.setMinimumHeight(42)
        self.theme_btn.clicked.connect(self.toggle_theme)
        bottom_layout.addWidget(self.theme_btn)
        
        # Logout button
        self.logout_btn = QPushButton(f"🚪 {tr('Logout')}")
        self.logout_btn.setProperty("i18n_key", "Logout")
        self.logout_btn.setProperty('class', 'sidebar-logout')
        self.logout_btn.setMinimumHeight(42)
        self.logout_btn.clicked.connect(self.logout)
        bottom_layout.addWidget(self.logout_btn)
        
        # Logout button
        logout_btn = QPushButton(f"🚪 {tr('Logout')}")
        logout_btn.setProperty('class', 'sidebar-logout')
        logout_btn.setMinimumHeight(42)
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
            try:
                QMessageBox.critical(self, tr("Error"), f"Failed to load page: {e}\nSee logs for details")
            except Exception:
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
            try:
                current_widget = None
                content_layout = getattr(self, 'content_layout', None)
                if content_layout and content_layout.count():
                    current_widget = content_layout.itemAt(0).widget()

                farm_id = self.get_current_farm_id()
                if current_widget is None:
                    return

                if hasattr(current_widget, 'set_farm_id') and callable(current_widget.set_farm_id):
                    current_widget.set_farm_id(farm_id)
                elif hasattr(current_widget, 'farm_id'):
                    try:
                        current_widget.farm_id = farm_id
                    except Exception:
                        pass

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

    def replace_content(self, new_widget):
        """Replace current content with new widget and animate."""
        self.clear_content()
        new_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_layout.addWidget(new_widget)
        AnimationHelper.fade_in(new_widget)
    
    def load_dashboard(self):
        """Load dashboard widget"""
        dashboard = DashboardWidget(self.get_current_farm_id())
        self.replace_content(dashboard)
        self._update_breadcrumbs("Dashboard", "dashboard")
        self._add_to_history("Dashboard", "dashboard", self.load_dashboard)
    
    def load_farm_management(self):
        """Load farm management widget"""
        farm_widget = FarmFormWidget()
        farm_widget.farm_changed.connect(self.refresh_farm_list)
        self.replace_content(farm_widget)
        self._update_breadcrumbs("Farm Management", "farm_management")
        self._add_to_history("Farm Management", "farm_management", self.load_farm_management)

    def load_flock_management(self):
        """Load flock management widget"""
        from egg_farm_system.ui.forms.flock_forms import FlockManagementWidget
        flock_widget = FlockManagementWidget()
        self.replace_content(flock_widget)
        self._update_breadcrumbs("Flock Management", "flock_management")
        self._add_to_history("Flock Management", "flock_management", self.load_flock_management)
    
    def load_production(self):
        """Load egg production widget"""
        prod_widget = ProductionFormWidget(self.get_current_farm_id())
        self.replace_content(prod_widget)
        self._update_breadcrumbs("Egg Production", "production")
        self._add_to_history("Egg Production", "production", self.load_production)
    
    def load_egg_stock(self):
        """Load egg stock management widget"""
        from egg_farm_system.ui.widgets.egg_stock_widget import EggStockWidget
        stock_widget = EggStockWidget()
        if self.get_current_farm_id():
            stock_widget.set_farm_id(self.get_current_farm_id())
        self.replace_content(stock_widget)
        self._update_breadcrumbs("Egg Stock", "egg_stock")
        self._add_to_history("Egg Stock", "egg_stock", self.load_egg_stock)
    
    def load_egg_expenses(self):
        """Load egg expense management widget"""
        from egg_farm_system.ui.widgets.egg_expense_widget import EggExpenseWidget
        expense_widget = EggExpenseWidget()
        self.replace_content(expense_widget)
        self._update_breadcrumbs("Egg Expenses", "egg_expenses")
        self._add_to_history("Egg Expenses", "egg_expenses", self.load_egg_expenses)
    
    def load_feed_management(self):
        """Load feed management widget"""
        from egg_farm_system.ui.forms.feed_forms import FeedFormWidget
        feed_widget = FeedFormWidget()
        self.replace_content(feed_widget)
        self._update_breadcrumbs("Feed Management", "feed")
        self._add_to_history("Feed Management", "feed", self.load_feed_management)
    
    def load_inventory(self):
        """Load inventory widget"""
        inventory_widget = InventoryFormWidget(self.get_current_farm_id())
        self.replace_content(inventory_widget)
        self._update_breadcrumbs("Inventory", "inventory")
        self._add_to_history("Inventory", "inventory", self.load_inventory)

    def load_equipment_management(self):
        """Load equipment management widget"""
        equipment_widget = EquipmentFormWidget(self.get_current_farm_id())
        self.replace_content(equipment_widget)
    
    def load_parties(self):
        """Load parties widget"""
        party_widget = PartyFormWidget()
        self.replace_content(party_widget)
        self._update_breadcrumbs("Parties", "parties")
        self._add_to_history("Parties", "parties", self.load_parties)
    
    def load_sales(self):
        """Load sales widget"""
        sales_widget = TransactionFormWidget("sales", self.get_current_farm_id(), current_user=self.current_user)
        self.replace_content(sales_widget)
        self._update_breadcrumbs("Sales", "sales")
        self._add_to_history("Sales", "sales", self.load_sales)
    
    def load_purchases(self):
        """Load purchases widget"""
        purchases_widget = TransactionFormWidget("purchases", self.get_current_farm_id(), current_user=self.current_user)
        self.replace_content(purchases_widget)
        self._update_breadcrumbs("Purchases", "purchases")
        self._add_to_history("Purchases", "purchases", self.load_purchases)
    
    def load_expenses(self):
        """Load expenses widget"""
        expenses_widget = TransactionFormWidget("expenses", self.get_current_farm_id(), current_user=self.current_user)
        self.replace_content(expenses_widget)
        self._update_breadcrumbs("Expenses", "expenses")
        self._add_to_history("Expenses", "expenses", self.load_expenses)
    
    def load_raw_material_sale(self):
        """Load raw material sale dialog"""
        from egg_farm_system.ui.forms.raw_material_sale_dialog import RawMaterialSaleDialog
        dialog = RawMaterialSaleDialog(self)
        dialog.sale_saved.connect(self._refresh_current_page)
        dialog.exec()
        self._update_breadcrumbs("Sell Raw Material", "raw_material_sale")
        self._add_to_history("Sell Raw Material", "raw_material_sale", self.load_raw_material_sale)

    def open_packaging_purchase_dialog(self):
        """Open Packaging Purchase dialog."""
        from egg_farm_system.ui.forms.packaging_purchase_dialog import PackagingPurchaseDialog
        dialog = PackagingPurchaseDialog(self)
        try:
            dialog.purchase_saved.connect(self._refresh_current_page)
        except Exception:
            pass
        dialog.exec()
        self._update_breadcrumbs("Purchase Packaging", "purchase_packaging")
        self._add_to_history("Purchase Packaging", "purchase_packaging", self.open_packaging_purchase_dialog)
    
    def load_employees_management(self):
        """Load employees management widget (Admin only)"""
        if not self._check_admin_permission("employee management"):
            return
        employees_widget = EmployeeManagementWidget()
        self.replace_content(employees_widget)
        
    def load_reports(self):
        """Load reports widget"""
        reports_widget = ReportViewerWidget(self.get_current_farm_id())
        self.replace_content(reports_widget)
        self._update_breadcrumbs("Reports", "reports")
        self._add_to_history("Reports", "reports", self.load_reports)

    def _check_admin_permission(self, operation_name="this operation"):
        """Check if current user has admin permission"""
        if not self.current_user or self.current_user.role != 'admin':
            QMessageBox.warning(
                self,
                tr("Access Denied"),
                tr(f"You need administrator privileges to access {operation_name}.")
            )
            return False
        return True

    def load_users_management(self):
        """Load user management UI (Admin only)"""
        if not self._check_admin_permission("user management"):
            return
        users_widget = UserManagementForm()
        self.replace_content(users_widget)

    def load_settings(self):
        """Load settings UI (Admin only)"""
        if not self._check_admin_permission("system settings"):
            return
        settings_widget = SettingsForm()
        self.replace_content(settings_widget)
    
    def load_backup_restore(self):
        """Load backup and restore widget (Admin only)"""
        if not self._check_admin_permission("backup and restore"):
            return
        backup_widget = BackupRestoreWidget()
        self.replace_content(backup_widget)
        self._update_breadcrumbs("Backup & Restore", "backup_restore")
        self._add_to_history("Backup & Restore", "backup_restore", self.load_backup_restore)
    
    def load_analytics(self):
        """Load advanced analytics dashboard with predictive analytics and forecasting"""
        # Create tabbed analytics dashboard
        from egg_farm_system.ui.advanced_dashboard import (
            ProductionForecastWidget,
            InventoryOptimizationWidget,
            FinancialDashboardWidget,
        )
        
        # Create main analytics container
        analytics_container = QWidget()
        layout = QVBoxLayout(analytics_container)
        
        # Create tab widget for different analytics
        tab_widget = QTabWidget()
        
        # Production Forecast Tab
        production_widget = ProductionForecastWidget(self.get_current_farm_id())
        tab_widget.addTab(production_widget, "Production Forecast")
        
        # Inventory Optimization Tab
        inventory_widget = InventoryOptimizationWidget(self.get_current_farm_id())
        tab_widget.addTab(inventory_widget, "Inventory Optimization")
        
        # Financial Dashboard Tab
        financial_widget = FinancialDashboardWidget(self.get_current_farm_id())
        tab_widget.addTab(financial_widget, "Financial Planning")
        
        layout.addWidget(tab_widget)
        
        self.replace_content(analytics_container)
        self._update_breadcrumbs("Advanced Analytics", "analytics")
        self._add_to_history("Advanced Analytics", "analytics", self.load_analytics)
    
    def load_cash_flow(self):
        """Load cash flow management widget"""
        from egg_farm_system.ui.widgets.cash_flow_widget import CashFlowWidget
        cash_flow_widget = CashFlowWidget(self.get_current_farm_id())
        self.replace_content(cash_flow_widget)
        self._update_breadcrumbs("Cash Flow", "cash_flow")
        self._add_to_history("Cash Flow", "cash_flow", self.load_cash_flow)
    
    def load_workflow_automation(self):
        """Load workflow automation widget"""
        from egg_farm_system.ui.widgets.workflow_automation_widget import WorkflowAutomationWidget
        workflow_widget = WorkflowAutomationWidget()
        self.replace_content(workflow_widget)
        self._update_breadcrumbs("Workflow Automation", "workflow")
        self._add_to_history("Workflow Automation", "workflow", self.load_workflow_automation)
    
    def load_audit_trail(self):
        """Load audit trail viewer"""
        from egg_farm_system.ui.widgets.audit_trail_viewer import AuditTrailViewerWidget
        audit_widget = AuditTrailViewerWidget()
        self.replace_content(audit_widget)
        self._update_breadcrumbs("Audit Trail", "audit_trail")
        self._add_to_history("Audit Trail", "audit_trail", self.load_audit_trail)
    
    def load_email_config(self):
        """Load email configuration widget"""
        from egg_farm_system.ui.widgets.email_config_widget import EmailConfigWidget
        email_widget = EmailConfigWidget()
        self.replace_content(email_widget)
        self._update_breadcrumbs("Email Configuration", "email_config")
        self._add_to_history("Email Configuration", "email_config", self.load_email_config)
    
    def show_notifications(self):
        """Show notification center"""
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("Notifications"))
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
    
    def _on_notification_changed(self, _notification=None):
        """Handle notification changes"""
        self._update_notification_badge()
    
    def _check_alerts_now(self):
        """Check alerts now"""
        self.alert_scheduler.check_now()

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
        
        # Add Ctrl+K for command palette
        self.cmd_palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.cmd_palette_shortcut.activated.connect(self.show_command_palette)
    
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
        """Toggle sidebar collapsed state with simple width animation"""
        try:
            collapsed = bool(self.sidebar.property('collapsed'))
            new_state = not collapsed
            
            # Target width
            target_width = 70 if new_state else SIDEBAR_WIDTH
            
            # Update collapse button icon
            if new_state:
                if hasattr(self, '_chev_right') and self._chev_right.exists():
                    self.collapse_btn.setIcon(QIcon(str(self._chev_right)))
                else:
                    self.collapse_btn.setText("»")
            else:
                if hasattr(self, '_chev_left') and self._chev_left.exists():
                    self.collapse_btn.setIcon(QIcon(str(self._chev_left)))
                else:
                    self.collapse_btn.setText("«")

            # Handle visibility of elements based on state
            # When collapsing: Hide text immediately, then shrink
            # When expanding: Expand, then show text (or just let layout handle it with clipping?)
            # Simplest approach: Hide/Show text labels on buttons.

            for btn in self.sidebar.findChildren(QPushButton):
                if btn.objectName() == 'collapse_btn':
                    continue

                full_text = btn.property('full_text')
                if not full_text:
                    continue

                if new_state:  # Collapsing
                    btn.setText("")  # Remove text
                    btn.setToolTip(full_text)  # Add tooltip
                else:  # Expanding
                    btn.setText(full_text)  # Restore text
                    btn.setToolTip("")  # Remove tooltip

            # Hide/Show Farm Combo and Labels
            if hasattr(self, 'farm_combo_widget'):
                self.farm_combo_widget.setVisible(not new_state)
            
            # Handle Collapsible Groups
            from egg_farm_system.ui.widgets.collapsible_group import CollapsibleGroup
            for group in self.sidebar.findChildren(CollapsibleGroup):
                # We can't easily "collapse" the group widget itself to icon-only mode
                # without significant changes to CollapsibleGroup.
                # For now, we rely on the button text hiding logic above (since group buttons are QPushButtons).
                # But the group HEADER button needs handling.
                if hasattr(group, 'header_btn'):
                    if new_state:
                        group.header_btn.setText("") # Hide header text
                        group.header_btn.setToolTip(group.title)
                        # Maybe force collapse content if sidebar is collapsed?
                        # group.is_expanded = False
                        # group.toggle() # This would close it.
                        # Actually keeping it open with just icons is fine if icons are distinct.
                    else:
                        # Restore header text (with arrow)
                        arrow = "▼" if group.is_expanded else "▶"
                        group.header_btn.setText(f"{arrow} {group.title}")
                        group.header_btn.setToolTip("")

            self.sidebar.setProperty('collapsed', new_state)
            
            # Animate width
            self.anim = QPropertyAnimation(self.sidebar, b"minimumWidth") # Animate min width (max width follows if setFixedWidth used previously but we need to unlock it)
            # Actually, standard way is to animate maximumWidth, but if we used setFixedWidth, we locked both.
            # Let's unlock:
            self.sidebar.setMinimumWidth(0) 
            self.sidebar.setMaximumWidth(self.sidebar.width()) # Start from current
            
            # We want to animate ONE property that controls width. 
            # If we use maximumWidth, minimumWidth should be 0 or small.
            # But we want to prevent squashing from layout.
            # So we animate minimumWidth? Layout will respect it.
            
            self.anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
            self.anim.setDuration(200)
            self.anim.setStartValue(self.sidebar.width())
            self.anim.setEndValue(target_width)
            self.anim.setEasingCurve(QEasingCurve.InOutQuad)
            
            # Also sync maximumWidth to match minimumWidth to keep it fixed-like during animation?
            # Or just set maximumWidth to target_width at end?
            
            def update_max_width(val):
                self.sidebar.setMaximumWidth(val)
                
            self.anim.valueChanged.connect(update_max_width)
            self.anim.start()
            
        except Exception as e:
            logger.exception(f"Failed to toggle sidebar: {e}")

    def toggle_theme(self):
        """Cycle through available themes: Farm -> Light -> Dark -> Farm"""
        from egg_farm_system.modules.settings import SettingsManager

        if self.current_theme == ThemeManager.FARM:
            self.current_theme = ThemeManager.LIGHT
            theme_name = "Light Theme"
        elif self.current_theme == ThemeManager.LIGHT:
            self.current_theme = ThemeManager.DARK
            theme_name = "Dark Theme"
        else:
            self.current_theme = ThemeManager.FARM
            theme_name = "Farm Theme"

        SettingsManager.set_setting('app_theme', self.current_theme, 'Application theme: farm/light/dark')
        ThemeManager.set_current_theme(self.current_theme)

        app = QApplication.instance()
        if app:
            ThemeManager.apply_theme(app, self.current_theme)
            if hasattr(self, 'theme_btn'):
                self.theme_btn.setText(f"🎨 {theme_name}")
            
    def _on_logout(self):
        """Log out current user and show login dialog; if cancelled, exit app."""
        from egg_farm_system.ui.forms.login_dialog import LoginDialog
        reply = QMessageBox.question(self, 'Confirm Logout', 'Are you sure you want to logout?', QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        dlg = LoginDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.current_user = getattr(dlg, 'user', None)
            for btn in self.sidebar.findChildren(QPushButton):
                full = btn.property('full_text')
                if full in ('Settings', 'Users'):
                    if not (self.current_user and getattr(self.current_user, 'role', '') == 'admin'):
                        btn.setEnabled(False)
                        btn.setToolTip(tr('Admin only'))
                    else:
                        btn.setEnabled(True)
                        btn.setToolTip('')
            try:
                if self.current_user:
                    pass 
                else:
                    pass
            except Exception:
                pass
        else:
            self.close_application()

    def _on_change_password(self):
        """Open password change dialog for current user."""
        from egg_farm_system.ui.forms.password_change_dialog import PasswordChangeDialog
        if not self.current_user:
            return
        dlg = PasswordChangeDialog(self, target_user_id=self.current_user.id, force=False)
        dlg.exec()
    
    def show_command_palette(self):
        """Show command palette dialog"""
        palette = CommandPalette(self)
        palette.command_executed.connect(self.execute_command)
        # Center on screen
        palette.move(
            self.geometry().center() - palette.rect().center()
        )
        palette.exec()
    
    def execute_command(self, command_id: str, _data: dict):
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
            'record_production': lambda: self._safe_load(self.load_production),
            'add_sale': lambda: self._safe_load(self.load_sales),
            'add_purchase': lambda: self._safe_load(self.load_purchases),
            'record_mortality': lambda: self._safe_load(self.load_production),
            'issue_feed': lambda: self._safe_load(self.load_feed_management),
            'add_expense': lambda: self._safe_load(self.load_expenses),
            'add_party': lambda: self._safe_load(self.load_parties),
            'add_payment': lambda: self._safe_load(self.load_parties),
            
            # Tools
            'refresh_dashboard': self._refresh_current_page,
            'import_data': self.show_import_wizard,
            'check_alerts': self._check_alerts_now,
            'backup_database': self.load_backup_restore,
        }
        
        handler = command_map.get(command_id)
        if handler:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error executing command {command_id}: {e}")
                QMessageBox.warning(self, "Error", f"Failed to execute command: {str(e)}")
    
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
    
    def eventFilter(self, obj, event):
        """Filter events to track user activity for session timeout"""
        from PySide6.QtCore import QEvent
        # Track mouse and keyboard events as user activity
        if event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress):
            self.last_activity = datetime.now()
        return super().eventFilter(obj, event)
    
    def _check_session_timeout(self):
        """Check if session has timed out due to inactivity"""
        from datetime import timedelta
        
        if not self.current_user:
            return
        
        inactive_minutes = (datetime.now() - self.last_activity).total_seconds() / 60
        
        if inactive_minutes >= self.session_timeout_minutes:
            logger.info(f"Session timeout after {inactive_minutes:.1f} minutes of inactivity")
            QMessageBox.warning(
                self,
                tr("Session Timeout"),
                tr(f"Your session has expired after {self.session_timeout_minutes} minutes of inactivity.\nPlease log in again.")
            )
            self.logout()
    
    def logout(self):
        """Logout current user and return to login screen"""
        try:
            # Stop all timers
            if hasattr(self, 'session_timer'):
                self.session_timer.stop()
            if hasattr(self, 'workflow_timer'):
                self.workflow_timer.stop()
            if hasattr(self, 'alert_scheduler'):
                self.alert_scheduler.stop()
            
            # Clear current user
            self.current_user = None
            
            # Close main window
            self.close()
            
            # Show login dialog
            from egg_farm_system.ui.forms.login_dialog import LoginDialog
            login = LoginDialog()
            if login.exec() == QDialog.Accepted:
                # Create new main window with logged-in user
                new_window = MainWindow(current_user=login.user, app_version=self.app_version)
                new_window.show()
            else:
                # User cancelled login, exit application
                QApplication.quit()
                
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            QApplication.quit()
