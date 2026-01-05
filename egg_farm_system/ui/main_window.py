"""
Main application window
"""
import sys
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QLabel, QComboBox, QMessageBox, QTabWidget, QStyle, QSizePolicy,
    QGraphicsOpacityEffect, QDialog
)
import traceback
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Slot
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

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, current_user=None, app_version="1.0.0"):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle("Egg Farm Management System")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.app_version = app_version
        
        DatabaseManager.initialize()
        self.farm_manager = FarmManager()
        
        # Create main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Create sidebar
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar) # Remove stretch factor for sidebar

        # Create content area
        self.content_area = QFrame()
        self.content_area.setFrameShape(QFrame.NoFrame) # No border for content area
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0) # Remove margins
        self.content_area.setLayout(self.content_layout)
        main_layout.addWidget(self.content_area, 1) # Content area takes remaining space
        
        main_layout.setStretch(0, 0) # Sidebar does not stretch
        main_layout.setStretch(1, 1) # Content area stretches

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
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header.setLayout(header_layout)

        title = QLabel(f"Egg Farm v{self.app_version}")
        title.setObjectName("app_title")
        title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.title_widget = title

        header_layout.addWidget(title)
        header_layout.addStretch()

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
        self.content_layout.addWidget(dashboard)
    
    def load_farm_management(self):
        """Load farm management widget"""
        self.clear_content()
        farm_widget = FarmFormWidget()
        farm_widget.farm_changed.connect(self.refresh_farm_list)
        self.content_layout.addWidget(farm_widget)
    
    def load_production(self):
        """Load egg production widget"""
        self.clear_content()
        prod_widget = ProductionFormWidget(self.get_current_farm_id())
        self.content_layout.addWidget(prod_widget)
    
    def load_feed_management(self):
        """Load feed management widget"""
        self.clear_content()
        from ui.forms.feed_forms import FeedFormWidget
        feed_widget = FeedFormWidget()
        self.content_layout.addWidget(feed_widget)
    
    def load_inventory(self):
        """Load inventory widget"""
        self.clear_content()
        inventory_widget = InventoryFormWidget()
        self.content_layout.addWidget(inventory_widget)

    def load_equipment_management(self):
        """Load equipment management widget"""
        self.clear_content()
        equipment_widget = EquipmentFormWidget(self.get_current_farm_id())
        self.content_layout.addWidget(equipment_widget)
    
    def load_parties(self):
        """Load parties widget"""
        self.clear_content()
        party_widget = PartyFormWidget()
        self.content_layout.addWidget(party_widget)
    
    def load_sales(self):
        """Load sales widget"""
        self.clear_content()
        sales_widget = TransactionFormWidget("sales", self.get_current_farm_id())
        self.content_layout.addWidget(sales_widget)
    
    def load_purchases(self):
        """Load purchases widget"""
        self.clear_content()
        purchases_widget = TransactionFormWidget("purchases", self.get_current_farm_id())
        self.content_layout.addWidget(purchases_widget)
    
    def load_expenses(self):
        """Load expenses widget"""
        self.clear_content()
        expenses_widget = TransactionFormWidget("expenses", self.get_current_farm_id())
        self.content_layout.addWidget(expenses_widget)
    
    def load_employees_management(self):
        """Load employees management widget"""
        self.clear_content()
        employees_widget = EmployeeManagementWidget()
        self.content_layout.addWidget(employees_widget)
        
    def load_reports(self):
        """Load reports widget"""
        self.clear_content()
        reports_widget = ReportViewerWidget(self.get_current_farm_id())
        self.content_layout.addWidget(reports_widget)

    def load_users_management(self):
        """Load user management UI"""
        self.clear_content()
        users_widget = UserManagementForm()
        self.content_layout.addWidget(users_widget)

    def load_settings(self):
        """Load settings UI"""
        self.clear_content()
        settings_widget = SettingsForm()
        self.content_layout.addWidget(settings_widget)
    
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
