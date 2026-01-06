"""
Notification Manager for Egg Farm Management System
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class NotificationSeverity(Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SUCCESS = "success"


@dataclass
class Notification:
    """Notification data class"""
    id: str
    title: str
    message: str
    severity: NotificationSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    read: bool = False
    action_url: Optional[str] = None  # URL or module name to navigate to
    action_label: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read,
            "action_url": self.action_url,
            "action_label": self.action_label
        }


class NotificationManager:
    """Manages application notifications"""
    
    def __init__(self):
        self._notifications: List[Notification] = []
        self._listeners: List[callable] = []
        self._max_notifications = 100
    
    def add_notification(self, title: str, message: str, severity: NotificationSeverity = NotificationSeverity.INFO,
                        action_url: Optional[str] = None, action_label: Optional[str] = None) -> Notification:
        """
        Add a new notification
        
        Args:
            title: Notification title
            message: Notification message
            severity: Severity level
            action_url: Optional action URL/module
            action_label: Optional action label
            
        Returns:
            Created notification
        """
        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            title=title,
            message=message,
            severity=severity,
            action_url=action_url,
            action_label=action_label
        )
        
        self._notifications.insert(0, notification)  # Add to beginning
        
        # Limit number of notifications
        if len(self._notifications) > self._max_notifications:
            self._notifications = self._notifications[:self._max_notifications]
        
        # Notify listeners
        self._notify_listeners(notification)
        
        logger.info(f"Notification added: {title} ({severity.value})")
        return notification
    
    def get_notifications(self, unread_only: bool = False) -> List[Notification]:
        """
        Get all notifications
        
        Args:
            unread_only: Return only unread notifications
            
        Returns:
            List of notifications
        """
        if unread_only:
            return [n for n in self._notifications if not n.read]
        return self._notifications.copy()
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        return len([n for n in self._notifications if not n.read])
    
    def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark notification as read
        
        Args:
            notification_id: ID of notification
            
        Returns:
            True if notification was found and marked
        """
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.read = True
                self._notify_listeners(notification)
                return True
        return False
    
    def mark_all_as_read(self):
        """Mark all notifications as read"""
        for notification in self._notifications:
            notification.read = True
        self._notify_listeners()
    
    def delete_notification(self, notification_id: str) -> bool:
        """
        Delete a notification
        
        Args:
            notification_id: ID of notification
            
        Returns:
            True if notification was found and deleted
        """
        for i, notification in enumerate(self._notifications):
            if notification.id == notification_id:
                del self._notifications[i]
                self._notify_listeners()
                return True
        return False
    
    def clear_all(self):
        """Clear all notifications"""
        self._notifications.clear()
        self._notify_listeners()
    
    def add_listener(self, callback: callable):
        """
        Add a listener for notification changes
        
        Args:
            callback: Function to call when notifications change
        """
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: callable):
        """Remove a listener"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, notification: Optional[Notification] = None):
        """Notify all listeners of changes"""
        for callback in self._listeners:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Error in notification listener: {e}")
    
    def check_low_stock(self, inventory_manager):
        """Check for low stock items and create notifications"""
        try:
            alerts = inventory_manager.get_low_stock_alerts()
            for alert in alerts:
                self.add_notification(
                    title="Low Stock Alert",
                    message=f"{alert['name']} ({alert['type']}) is below threshold. Current: {alert['stock']} {alert['unit']}",
                    severity=NotificationSeverity.WARNING,
                    action_url="inventory",
                    action_label="View Inventory"
                )
        except Exception as e:
            logger.error(f"Error checking low stock: {e}")
    
    def check_overdue_payments(self, ledger_manager):
        """Check for overdue payments and create notifications"""
        try:
            # This would need to be implemented in ledger manager
            # For now, just a placeholder
            pass
        except Exception as e:
            logger.error(f"Error checking overdue payments: {e}")


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get global notification manager instance"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager

