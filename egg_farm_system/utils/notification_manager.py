"""
Notification Manager for Egg Farm Management System
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def build_low_stock_dedup_key(item_type: str, item_name: str, farm_id: Optional[int] = None) -> str:
    """Build a stable dedup key for low-stock notifications across emitters."""
    normalized_type = item_type.strip().lower().replace(" ", "_")
    normalized_name = item_name.strip().lower()
    key = f"low_stock:{normalized_type}:{normalized_name}"
    if farm_id is not None:
        key = f"{key}:farm:{farm_id}"
    return key


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
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    dedup_key: Optional[str] = None

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
            "action_label": self.action_label,
            "dedup_key": self.dedup_key,
        }


class NotificationManager:
    """Manages application notifications"""

    def __init__(self):
        self._notifications: List[Notification] = []
        self._listeners: List[callable] = []
        self._max_notifications = 100

    def _find_recent_duplicate(
        self,
        title: str,
        message: str,
        severity: NotificationSeverity,
        dedup_key: Optional[str] = None,
        dedup_window_minutes: int = 30,
    ) -> Optional[Notification]:
        """Return a matching unread notification in the dedup time window."""
        cutoff = datetime.now() - timedelta(minutes=max(dedup_window_minutes, 1))
        for note in self._notifications:
            if note.read or note.timestamp < cutoff:
                continue

            if dedup_key and note.dedup_key == dedup_key:
                return note

            if (
                not dedup_key
                and note.title == title
                and note.message == message
                and note.severity == severity
            ):
                return note
        return None

    def add_notification(
        self,
        title: str,
        message: str,
        severity=None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        data: Optional[dict] = None,
        dedup_key: Optional[str] = None,
        dedup_window_minutes: int = 30,
    ) -> Notification:
        """Add a new notification."""
        if isinstance(severity, str):
            severity_map = {
                "info": NotificationSeverity.INFO,
                "warning": NotificationSeverity.WARNING,
                "critical": NotificationSeverity.CRITICAL,
                "success": NotificationSeverity.SUCCESS,
            }
            severity = severity_map.get(severity.lower(), NotificationSeverity.INFO)
        elif severity is None:
            severity = NotificationSeverity.INFO

        existing = self._find_recent_duplicate(
            title=title,
            message=message,
            severity=severity,
            dedup_key=dedup_key,
            dedup_window_minutes=dedup_window_minutes,
        )
        if existing:
            return existing

        notification = Notification(
            id=f"notif_{datetime.now().timestamp()}",
            title=title,
            message=message,
            severity=severity,
            action_url=action_url,
            action_label=action_label,
            dedup_key=dedup_key,
        )

        self._notifications.insert(0, notification)

        if len(self._notifications) > self._max_notifications:
            self._notifications = self._notifications[: self._max_notifications]

        self._notify_listeners(notification)
        logger.info("Notification added: %s (%s)", title, severity.value)
        return notification

    def get_notifications(self, unread_only: bool = False) -> List[Notification]:
        """Get all notifications."""
        if unread_only:
            return [n for n in self._notifications if not n.read]
        return self._notifications.copy()

    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        return len([n for n in self._notifications if not n.read])

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.read = True
                self._notify_listeners(notification)
                return True
        return False

    def mark_all_as_read(self):
        """Mark all notifications as read."""
        for notification in self._notifications:
            notification.read = True
        self._notify_listeners()

    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification."""
        for i, notification in enumerate(self._notifications):
            if notification.id == notification_id:
                del self._notifications[i]
                self._notify_listeners()
                return True
        return False

    def clear_all(self):
        """Clear all notifications."""
        self._notifications.clear()
        self._notify_listeners()

    def add_listener(self, callback: callable):
        """Add a listener for notification changes."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: callable):
        """Remove a listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self, notification: Optional[Notification] = None):
        """Notify all listeners of changes."""
        for callback in self._listeners:
            try:
                callback(notification)
            except Exception as exc:
                logger.error("Error in notification listener: %s", exc)

    def check_low_stock(self, inventory_manager):
        """Check for low stock items and create notifications."""
        try:
            alerts = inventory_manager.get_low_stock_alerts()
            for alert in alerts:
                self.add_notification(
                    title="Low Stock Alert",
                    message=(
                        f"{alert['name']} ({alert['type']}) is below threshold. "
                        f"Current: {alert['stock']} {alert['unit']}"
                    ),
                    severity=NotificationSeverity.WARNING,
                    action_url="inventory",
                    action_label="View Inventory",
                    dedup_key=build_low_stock_dedup_key(
                        alert['type'],
                        alert['name'],
                        alert.get('farm_id'),
                    ),
                )
        except Exception as exc:
            logger.error("Error checking low stock: %s", exc)

    def check_overdue_payments(self, ledger_manager):
        """Check for outstanding balances and create notifications."""
        try:
            outstanding = ledger_manager.get_all_parties_outstanding()

            for item in outstanding:
                if item["status"] == "Owes us":
                    party_name = item["party"].name
                    balance_afg = item["balance_afg"]
                    balance_usd = item["balance_usd"]

                    if balance_afg > 100 or balance_usd > 10:
                        title = f"Outstanding Balance: {party_name}"

                        amounts = []
                        if balance_afg > 0:
                            amounts.append(f"{balance_afg:,.0f} AFG")
                        if balance_usd > 0:
                            amounts.append(f"{balance_usd:,.2f} USD")

                        message = f"{party_name} owes {', '.join(amounts)}"

                        existing = False
                        for note in self.get_notifications(unread_only=True):
                            if note.title == title and note.message == message:
                                existing = True
                                break

                        if not existing:
                            self.add_notification(
                                title=title,
                                message=message,
                                severity=NotificationSeverity.WARNING,
                                action_url="parties",
                                action_label="View Ledger",
                            )
        except Exception as exc:
            logger.error("Error checking overdue payments: %s", exc)


_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get global notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
