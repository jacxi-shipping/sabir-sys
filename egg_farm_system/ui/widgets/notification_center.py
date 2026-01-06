"""
Notification Center Widget
"""
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget,
    QListWidgetItem, QFrame, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPalette

from egg_farm_system.utils.notification_manager import (
    NotificationManager, NotificationSeverity, get_notification_manager
)

logger = logging.getLogger(__name__)


class NotificationItemWidget(QFrame):
    """Widget for individual notification item"""
    
    def __init__(self, notification, parent=None):
        super().__init__(parent)
        self.notification = notification
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setFrameShape(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
                background-color: white;
            }
            QFrame:hover {
                background-color: #f5f5f5;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        
        # Header with title and severity
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.notification.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Severity indicator
        severity_label = QLabel(self.notification.severity.value.upper())
        severity_color = self._get_severity_color(self.notification.severity)
        severity_label.setStyleSheet(f"color: {severity_color}; font-weight: bold;")
        header_layout.addWidget(severity_label)
        
        layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(self.notification.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #666;")
        layout.addWidget(message_label)
        
        # Footer with timestamp and action
        footer_layout = QHBoxLayout()
        
        timestamp = self.notification.timestamp.strftime("%Y-%m-%d %H:%M")
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("color: #999; font-size: 9pt;")
        footer_layout.addWidget(time_label)
        
        footer_layout.addStretch()
        
        if self.notification.action_label:
            action_btn = QPushButton(self.notification.action_label)
            action_btn.setMaximumHeight(20)
            action_btn.setStyleSheet("font-size: 9pt; padding: 2px 8px;")
            action_btn.clicked.connect(lambda: self._on_action_clicked())
            footer_layout.addWidget(action_btn)
        
        layout.addLayout(footer_layout)
        
        # Mark as read/unread
        if not self.notification.read:
            self.setStyleSheet(self.styleSheet() + """
                QFrame {
                    border-left: 4px solid #3498db;
                }
            """)
    
    def _get_severity_color(self, severity: NotificationSeverity) -> str:
        """Get color for severity"""
        colors = {
            NotificationSeverity.INFO: "#3498db",
            NotificationSeverity.WARNING: "#f39c12",
            NotificationSeverity.CRITICAL: "#e74c3c",
            NotificationSeverity.SUCCESS: "#27ae60"
        }
        return colors.get(severity, "#95a5a6")
    
    def _on_action_clicked(self):
        """Handle action button click"""
        # Emit signal or call callback
        pass


class NotificationCenterWidget(QWidget):
    """Notification center widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notification_manager = get_notification_manager()
        self.notification_manager.add_listener(self._on_notification_changed)
        self.init_ui()
        self.refresh_notifications()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Notifications")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Unread count badge
        self.unread_badge = QLabel("0")
        self.unread_badge.setStyleSheet("""
            QLabel {
                background-color: #e74c3c;
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
                font-weight: bold;
            }
        """)
        self.unread_badge.setVisible(False)
        header_layout.addWidget(self.unread_badge)
        
        # Action buttons
        mark_all_read_btn = QPushButton("Mark All Read")
        mark_all_read_btn.clicked.connect(self.mark_all_read)
        header_layout.addWidget(mark_all_read_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(clear_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_notifications)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Notification list
        self.notification_list = QListWidget()
        self.notification_list.setSpacing(4)
        self.notification_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.notification_list)
        
        # Empty state
        self.empty_label = QLabel("No notifications")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #999; padding: 20px;")
        layout.addWidget(self.empty_label)
    
    def refresh_notifications(self):
        """Refresh notification list"""
        self.notification_list.clear()
        
        notifications = self.notification_manager.get_notifications()
        
        if not notifications:
            self.empty_label.setVisible(True)
            self.notification_list.setVisible(False)
        else:
            self.empty_label.setVisible(False)
            self.notification_list.setVisible(True)
            
            for notification in notifications:
                item = QListWidgetItem()
                item.setData(Qt.UserRole, notification.id)
                
                # Create custom widget for notification
                widget = NotificationItemWidget(notification)
                item.setSizeHint(widget.sizeHint())
                
                self.notification_list.addItem(item)
                self.notification_list.setItemWidget(item, widget)
        
        # Update unread count
        unread_count = self.notification_manager.get_unread_count()
        if unread_count > 0:
            self.unread_badge.setText(str(unread_count))
            self.unread_badge.setVisible(True)
        else:
            self.unread_badge.setVisible(False)
    
    def mark_all_read(self):
        """Mark all notifications as read"""
        self.notification_manager.mark_all_as_read()
        self.refresh_notifications()
    
    def clear_all(self):
        """Clear all notifications"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Clear All Notifications",
            "Are you sure you want to clear all notifications?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.notification_manager.clear_all()
            self.refresh_notifications()
    
    def on_item_double_clicked(self, item: QListWidgetItem):
        """Handle item double click"""
        notification_id = item.data(Qt.UserRole)
        self.notification_manager.mark_as_read(notification_id)
        self.refresh_notifications()
    
    def _on_notification_changed(self, notification=None):
        """Handle notification changes"""
        self.refresh_notifications()

