"""
Main application window
"""
import sys
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLayout,
    QPushButton, QLabel, QComboBox, QMessageBox, QTabWidget, QStyle, QSizePolicy,
    QGraphicsOpacityEffect, QDialog
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
from pathlib import Path
from PySide6.QtGui import QIcon
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
from egg_farm_system.ui.widgets.global_search_widget import GlobalSearchWidget, SearchBarWidget

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, current_user=None, app_version="1.0.0"):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("Egg Farm Management System")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.app_version = app_version
        
        # Initialize Theme
        self.current_theme = ThemeManager.LIGHT
        ThemeManager.apply_theme(sys.modules['__main__'].app if hasattr(sys.modules['__main__'], 'app') else self, self.current_theme)

        DatabaseManager.initialize()
        # Re-fetch the user to bind it to a new session for MainWindow's lifetime
        if current_user:
            session = DatabaseManager.get_session()
            try:
                self.current_user = session.query(User).filter_by(id=current_user.id).first()
            finally:
                session.close()

        self.farm_manager = FarmManager()
        
        # Initialize notification manager and check for alerts
        self.notification_manager = get_notification_manager()
        self._check_notifications()
        
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
        
        # Load dashboard initially
        self.load_dashboard()
    
    def create_sidebar(self):
        """Create left sidebar navigation"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMaximumWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header
        header = QFrame()
        header.setObjectName("sidebar_header")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title row
        title_row = QHBoxLayout()
        title = QLabel(f"Egg Farm v{self.app_version}")
        title.setObjectName("app_title")
        title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.title_widget = title
        title_row.addWidget(title)
        title_row.addStretch()
        header_layout.addLayout(title_row)
        
        # Global search bar
        self.search_bar = SearchBarWidget()
        header_layout.addWidget(self.search_bar)
        
        header.setLayout(header_layout)

        # Notification bell button
        self.notification_btn = QPushButton()
        self.notification_btn.setObjectName('notification_btn')
        self.notification_btn.setMaximumSize(32, 32)
        self.notification_btn.setToolTip("Notifications")
        # Try to set bell icon
        bell_icon = asset_dir / 'icon_view.svg'  # Using existing icon as placeholder
        if bell_icon.exists():
            self.notification_btn.setIcon(QIcon(str(bell_icon)))
            self.notification_btn.setIconSize(QSize(20, 20))
        self.notification_btn.clicked.connect(self.show_notifications)
        self.notification_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)
        header_layout.addWidget(self.notification_btn)
        
        # Notification badge
        self.notification_badge = QLabel("0")
        self.notification_badge.setObjectName('notification_badge')
        self.notification_badge.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                color: white;
                border-radius: 10px;
                padding: 2px 6px;
                font-weight: bold;
                font-size: 9pt;
            }
        """)
        self.notification_badge.setVisible(False)
        header_layout.addWidget(self.notification_badge)
        
        # Current user label
        self.user_label = QLabel()
        self.user_label.setObjectName('user_label')
        self.user_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        # show current user if available
        try:
            if hasattr(self, 'current_user') and self.current_user:
                self.user_label.setText(f"User: {getattr(self.current_user, 'username', '')}")
            else:
                self.user_label.setText("Not logged in")
        except Exception:
            self.user_label.setText("Not logged in")
        header_layout.addWidget(self.user_label)

        layout.addWidget(header)

        # Farm selector
        self.farm_label = QLabel("Select Farm:")
        layout.addWidget(self.farm_label)
        self.farm_combo = QComboBox()
        self.farm_combo.currentIndexChanged.connect(self.on_farm_changed)
        self.refresh_farm_list()
        layout.addWidget(self.farm_combo)
        self.farm_combo_widget = self.farm_combo

        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.load_dashboard, 'icon_dashboard.svg'),
            ("Farm Management", self.load_farm_management, 'icon_farm.svg'),
            ("Egg Production", self.load_production, 'icon_egg.svg'),
            ("Egg Stock", self.load_egg_stock, 'icon_egg.svg'),
            ("Egg Expenses", self.load_egg_expenses, 'icon_expenses.svg'),
            ("Feed Management", self.load_feed_management, 'icon_feed.svg'),
            ("Inventory", self.load_inventory, 'icon_inventory.svg'),
            ("Equipment", self.load_equipment_management, 'icon_inventory.svg'),
            ("Parties", self.load_parties, 'icon_parties.svg'),
            ("Sales", self.load_sales, 'icon_sales.svg'),
            ("Purchases", self.load_purchases, 'icon_purchases.svg'),
            ("Expenses", self.load_expenses, 'icon_expenses.svg'),
            ("Employees", self.load_employees_management, 'icon_parties.svg'),
            ("Users", self.load_users_management, 'icon_parties.svg'),
            ("Settings", self.load_settings, 'icon_reports.svg'),
            ("Backup & Restore", self.load_backup_restore, 'icon_reports.svg'),
            ("Analytics", self.load_analytics, 'icon_reports.svg'),
            ("Workflow Automation", self.load_workflow_automation, 'icon_reports.svg'),
            ("Audit Trail", self.load_audit_trail, 'icon_reports.svg'),
            ("Email Config", self.load_email_config, 'icon_reports.svg'),
            ("Reports", self.load_reports, 'icon_reports.svg'),
        ]

        asset_dir = Path(__file__).parent.parent / 'assets'
        for button_text, callback, icon_file in nav_buttons:
            btn = QPushButton(button_text)
            btn.setProperty('full_text', button_text)
            svg_path = asset_dir / icon_file
            try:
                if svg_path.exists():
                    btn.setIcon(QIcon(str(svg_path)))
                    btn.setIconSize(QSize(20, 20))
            except Exception:
                pass
            btn.setMinimumHeight(36)
            # wrap callback to catch and report exceptions during page load
            btn.clicked.connect(lambda checked=False, cb=callback: self._safe_load(cb))
            # role-based availability: disable Settings (and Users) for non-admins
            try:
                if button_text in ('Settings', 'Users', 'Employees', 'Equipment'):
                    if not (hasattr(self, 'current_user') and self.current_user and getattr(self.current_user, 'role', '') == 'admin'):
                        btn.setEnabled(False)
                        btn.setToolTip('Admin only')
            except Exception:
                pass
            layout.addWidget(btn)

        layout.addStretch()

        # Theme Toggle Button
        theme_btn = QPushButton("Toggle Theme")
        theme_btn.setObjectName('theme_btn')
        theme_icon = asset_dir / 'icon_view.svg'
        if theme_icon.exists():
            theme_btn.setIcon(QIcon(str(theme_icon)))
            theme_btn.setIconSize(QSize(18, 18))
        theme_btn.clicked.connect(self.toggle_theme)
        theme_btn.setProperty('full_text', 'Toggle Theme')
        layout.addWidget(theme_btn)

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName('logout_btn')
        exit_icon = asset_dir / 'icon_exit.svg'
        if exit_icon.exists():
            logout_btn.setIcon(QIcon(str(exit_icon)))
            logout_btn.setIconSize(QSize(18, 18))
        logout_btn.clicked.connect(self._on_logout)
        logout_btn.setProperty('full_text', 'Logout')
        layout.addWidget(logout_btn)
        self.logout_button = logout_btn

        sidebar.setLayout(layout)
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
        from ui.forms.feed_forms import FeedFormWidget
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
        sales_widget = TransactionFormWidget("sales", self.get_current_farm_id())
        sales_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(sales_widget)
        self._update_breadcrumbs("Sales", "sales")
        self._add_to_history("Sales", "sales", self.load_sales)
    
    def load_purchases(self):
        """Load purchases widget"""
        self.clear_content()
        purchases_widget = TransactionFormWidget("purchases", self.get_current_farm_id())
        purchases_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(purchases_widget)
        self._update_breadcrumbs("Purchases", "purchases")
        self._add_to_history("Purchases", "purchases", self.load_purchases)
    
    def load_expenses(self):
        """Load expenses widget"""
        self.clear_content()
        expenses_widget = TransactionFormWidget("expenses", self.get_current_farm_id())
        expenses_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout.addWidget(expenses_widget)
        self._update_breadcrumbs("Expenses", "expenses")
        self._add_to_history("Expenses", "expenses", self.load_expenses)
    
    def load_employees_management(self):
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
        """Switch between Light and Dark themes"""
        from PySide6.QtWidgets import QApplication
        if self.current_theme == ThemeManager.LIGHT:
            self.current_theme = ThemeManager.DARK
        else:
            self.current_theme = ThemeManager.LIGHT
            
        app = QApplication.instance()
        if app:
            ThemeManager.apply_theme(app, self.current_theme)
            
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
