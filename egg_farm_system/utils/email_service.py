"""
Email Service for Egg Farm Management System
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

from egg_farm_system.modules.settings import SettingsManager

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending reports and notifications"""
    
    def __init__(self):
        self.smtp_server = SettingsManager.get_setting('email_smtp_server', 'smtp.gmail.com')
        self.smtp_port = int(SettingsManager.get_setting('email_smtp_port', '587'))
        self.smtp_username = SettingsManager.get_setting('email_username', '')
        self.smtp_password = SettingsManager.get_setting('email_password', '')
        self.from_email = SettingsManager.get_setting('email_from', self.smtp_username)
        self.use_tls = SettingsManager.get_setting('email_use_tls', 'true').lower() == 'true'
    
    def is_configured(self) -> bool:
        """Check if email is configured"""
        return bool(self.smtp_username and self.smtp_password)
    
    def configure(self, smtp_server: str, smtp_port: int, username: str, password: str,
                 from_email: Optional[str] = None, use_tls: bool = True):
        """Configure email settings"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = username
        self.smtp_password = password
        self.from_email = from_email or username
        self.use_tls = use_tls
        
        # Save to settings
        SettingsManager.set_setting('email_smtp_server', smtp_server)
        SettingsManager.set_setting('email_smtp_port', str(smtp_port))
        SettingsManager.set_setting('email_username', username)
        SettingsManager.set_setting('email_password', password)  # Note: In production, encrypt this
        SettingsManager.set_setting('email_from', self.from_email)
        SettingsManager.set_setting('email_use_tls', 'true' if use_tls else 'false')
    
    def send_email(self, to_emails: List[str], subject: str, body: str,
                   html_body: Optional[str] = None, attachments: Optional[List[Path]] = None) -> bool:
        """
        Send an email
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            attachments: Optional list of file paths to attach
            
        Returns:
            True if sent successfully
        """
        if not self.is_configured():
            logger.warning("Email not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add body
            if html_body:
                part1 = MIMEText(body, 'plain')
                part2 = MIMEText(html_body, 'html')
                msg.attach(part1)
                msg.attach(part2)
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if file_path.exists():
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {file_path.name}'
                            )
                            msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {', '.join(to_emails)}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def send_report(self, report_data: Dict[str, Any], report_type: str, to_emails: List[str],
                   subject: Optional[str] = None, attachment_path: Optional[Path] = None) -> bool:
        """
        Send a report via email
        
        Args:
            report_data: Report data dictionary
            report_type: Type of report
            to_emails: Recipient emails
            subject: Optional custom subject
            attachment_path: Optional path to report file (PDF/Excel)
        """
        if not subject:
            subject = f"Egg Farm Report - {report_type.replace('_', ' ').title()}"
        
        # Generate email body
        body = self._format_report_body(report_data, report_type)
        html_body = self._format_report_html(report_data, report_type)
        
        attachments = []
        if attachment_path and attachment_path.exists():
            attachments.append(attachment_path)
        
        return self.send_email(to_emails, subject, body, html_body, attachments)
    
    def send_notification(self, to_emails: List[str], title: str, message: str,
                         severity: str = "info") -> bool:
        """
        Send a notification email
        
        Args:
            to_emails: Recipient emails
            title: Notification title
            message: Notification message
            severity: Severity level (info, warning, critical)
        """
        subject = f"[{severity.upper()}] {title}"
        body = f"{title}\n\n{message}"
        
        html_body = f"""
        <html>
        <body>
            <h2 style="color: {'#e74c3c' if severity == 'critical' else '#f39c12' if severity == 'warning' else '#3498db'};">
                {title}
            </h2>
            <p>{message}</p>
            <hr>
            <p style="color: #7f8c8d; font-size: 12px;">
                Egg Farm Management System - Automated Notification
            </p>
        </body>
        </html>
        """
        
        return self.send_email(to_emails, subject, body, html_body)
    
    def _format_report_body(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Format report as plain text"""
        body = f"Egg Farm Management System - {report_type.replace('_', ' ').title()} Report\n\n"
        
        if report_type == "daily_production":
            body += f"Farm: {report_data.get('farm', 'N/A')}\n"
            body += f"Date: {report_data.get('date', 'N/A')}\n\n"
            for shed in report_data.get('sheds', []):
                body += f"{shed.get('name', '')}: {shed.get('total_eggs', 0)} eggs\n"
            totals = report_data.get('totals', {})
            body += f"\nTotal: {totals.get('total', 0)} eggs\n"
        
        return body
    
    def _format_report_html(self, report_data: Dict[str, Any], report_type: str) -> str:
        """Format report as HTML"""
        from egg_farm_system.utils.print_manager import PrintManager
        return PrintManager.format_report_html(report_data, report_type, 
                                               f"{report_type.replace('_', ' ').title()} Report")
    
    def test_connection(self) -> bool:
        """Test email connection"""
        if not self.is_configured():
            return False
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
            return True
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False

