from egg_farm_system.utils.i18n import tr
from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QMessageBox, QHBoxLayout, QToolButton
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from egg_farm_system.modules.users import UserManager
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """Simple username/password login dialog with rate limiting"""

    # Class-level dictionary to track failed login attempts per username
    failed_attempts = {}
    lockout_time = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('Login'))
        self.user = None

        layout = QFormLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText(tr("Enter your username"))
        
        # Password field with visibility toggle
        password_layout = QHBoxLayout()
        password_layout.setSpacing(5)
        password_layout.setContentsMargins(0, 0, 0, 0)
        
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText(tr("Enter your password"))
        password_layout.addWidget(self.password)
        
        # Password visibility toggle button
        self.toggle_password_btn = QToolButton()
        self.toggle_password_btn.setText("👁")
        self.toggle_password_btn.setToolTip(tr("Show/hide password"))
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.clicked.connect(self._toggle_password_visibility)
        self.toggle_password_btn.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 2px;
                font-size: 16px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
                border-radius: 3px;
            }
        """)
        password_layout.addWidget(self.toggle_password_btn)

        layout.addRow('Username:', self.username)
        layout.addRow('Password:', password_layout)

        btn = QPushButton(tr('Login'))
        btn.clicked.connect(self.attempt_login)
        btn.setDefault(True)  # Allow Enter key to login
        layout.addRow(btn)

        self.setLayout(layout)
        
        # Set focus to username
        self.username.setFocus()
    
    def _toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.toggle_password_btn.isChecked():
            self.password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setToolTip(tr("Hide password"))
        else:
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setToolTip(tr("Show password"))

    def attempt_login(self):
        uname = self.username.text().strip()
        pwd = self.password.text()
        if not uname or not pwd:
            QMessageBox.warning(self, tr('Validation'), 'Enter username and password')
            return

        # Check if account is locked out
        if uname in self.lockout_time:
            lockout_until = self.lockout_time[uname]
            if datetime.now() < lockout_until:
                remaining = int((lockout_until - datetime.now()).total_seconds() / 60)
                QMessageBox.warning(
                    self,
                    tr('Account Locked'),
                    tr(f'Too many failed login attempts. Please try again in {remaining} minutes.')
                )
                return
            else:
                # Lockout expired, remove it
                del self.lockout_time[uname]
                if uname in self.failed_attempts:
                    del self.failed_attempts[uname]

        ok = UserManager.verify_credentials(uname, pwd)
        if ok:
            # Successful login - clear failed attempts
            if uname in self.failed_attempts:
                del self.failed_attempts[uname]
            if uname in self.lockout_time:
                del self.lockout_time[uname]
            
            self.user = UserManager.get_user_by_username(uname)
            logger.info(f"User {uname} logged in successfully")
            self.accept()
        else:
            # Failed login - track attempts
            if uname not in self.failed_attempts:
                self.failed_attempts[uname] = 0
            
            self.failed_attempts[uname] += 1
            attempts = self.failed_attempts[uname]
            
            logger.warning(f"Failed login attempt {attempts} for user {uname}")
            
            # Lock out after 5 failed attempts
            if attempts >= 5:
                self.lockout_time[uname] = datetime.now() + timedelta(minutes=15)
                logger.warning(f"User {uname} locked out for 15 minutes after {attempts} failed attempts")
                QMessageBox.warning(
                    self,
                    tr('Account Locked'),
                    tr('Too many failed login attempts. Account locked for 15 minutes.')
                )
            else:
                remaining = 5 - attempts
                QMessageBox.warning(
                    self,
                    tr('Login Failed'),
                    tr(f'Invalid username or password. {remaining} attempts remaining before lockout.')
                )
