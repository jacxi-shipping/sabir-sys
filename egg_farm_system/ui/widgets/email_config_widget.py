"""
Email Configuration Widget
"""
from egg_farm_system.utils.i18n import tr

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QLineEdit, QSpinBox, QCheckBox, QMessageBox, QFormLayout, QTextEdit
)
from PySide6.QtGui import QFont

from egg_farm_system.utils.email_service import EmailService

logger = logging.getLogger(__name__)


class EmailConfigWidget(QWidget):
    """Email configuration widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.email_service = EmailService()
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(tr("Email Configuration"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Configuration form
        config_group = QGroupBox("SMTP Settings")
        config_layout = QFormLayout()
        
        self.smtp_server_edit = QLineEdit()
        self.smtp_server_edit.setPlaceholderText(tr("smtp.gmail.com"))
        config_layout.addRow("SMTP Server:", self.smtp_server_edit)
        
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setRange(1, 65535)
        self.smtp_port_spin.setValue(587)
        config_layout.addRow("SMTP Port:", self.smtp_port_spin)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText(tr("your-email@gmail.com"))
        config_layout.addRow("Username/Email:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText(tr("Your email password or app password"))
        config_layout.addRow("Password:", self.password_edit)
        
        self.from_email_edit = QLineEdit()
        self.from_email_edit.setPlaceholderText(tr("Optional - defaults to username"))
        config_layout.addRow("From Email:", self.from_email_edit)
        
        self.use_tls_check = QCheckBox("Use TLS/STARTTLS")
        self.use_tls_check.setChecked(True)
        config_layout.addRow("", self.use_tls_check)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr("Save Configuration"))
        save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(save_btn)
        
        test_btn = QPushButton(tr("Test Connection"))
        test_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(test_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Status
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px;")
        layout.addWidget(self.status_label)
        
        # Help text
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(150)
        help_text.setPlainText(
            "Email Configuration Help:\n\n"
            "For Gmail:\n"
            "- SMTP Server: smtp.gmail.com\n"
            "- Port: 587 (TLS) or 465 (SSL)\n"
            "- Use an App Password (not your regular password)\n"
            "- Enable 2-factor authentication first\n\n"
            "For Outlook:\n"
            "- SMTP Server: smtp-mail.outlook.com\n"
            "- Port: 587\n\n"
            "Note: Passwords are stored in settings. Consider encrypting in production."
        )
        layout.addWidget(help_text)
        
        layout.addStretch()
    
    def load_config(self):
        """Load current email configuration"""
        if self.email_service.is_configured():
            self.smtp_server_edit.setText(self.email_service.smtp_server)
            self.smtp_port_spin.setValue(self.email_service.smtp_port)
            self.username_edit.setText(self.email_service.smtp_username)
            self.from_email_edit.setText(self.email_service.from_email)
            self.use_tls_check.setChecked(self.email_service.use_tls)
            self.status_label.setText(tr("✓ Email is configured"))
            self.status_label.setStyleSheet("color: green; padding: 10px;")
        else:
            self.status_label.setText(tr("Email is not configured. Please enter your SMTP settings."))
            self.status_label.setStyleSheet("color: orange; padding: 10px;")
    
    def save_config(self):
        """Save email configuration"""
        smtp_server = self.smtp_server_edit.text().strip()
        smtp_port = self.smtp_port_spin.value()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        from_email = self.from_email_edit.text().strip() or username
        use_tls = self.use_tls_check.isChecked()
        
        if not smtp_server or not username or not password:
            QMessageBox.warning(self, tr("Validation"), "Please fill in all required fields")
            return
        
        try:
            self.email_service.configure(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                username=username,
                password=password,
                from_email=from_email,
                use_tls=use_tls
            )
            
            QMessageBox.information(self, tr("Success"), "Email configuration saved successfully")
            self.status_label.setText(tr("✓ Email configuration saved"))
            self.status_label.setStyleSheet("color: green; padding: 10px;")
        
        except Exception as e:
            logger.error(f"Error saving email config: {e}")
            QMessageBox.critical(self, tr("Error"), f"Failed to save configuration:\n{str(e)}")
    
    def test_connection(self):
        """Test email connection"""
        # Save config first
        self.save_config()
        
        if not self.email_service.is_configured():
            QMessageBox.warning(self, tr("Not Configured"), "Please configure email settings first")
            return
        
        QMessageBox.information(self, tr("Testing"), "Testing email connection...")
        
        if self.email_service.test_connection():
            QMessageBox.information(self, tr("Success"), "Email connection test successful!")
            self.status_label.setText(tr("✓ Email connection test successful"))
            self.status_label.setStyleSheet("color: green; padding: 10px;")
        else:
            QMessageBox.critical(self, tr("Failed"), "Email connection test failed. Please check your settings.")
            self.status_label.setText(tr("✗ Email connection test failed"))
            self.status_label.setStyleSheet("color: red; padding: 10px;")

