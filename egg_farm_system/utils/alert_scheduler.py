"""
Alert Scheduler for periodic alert checking
"""
from PySide6.QtCore import QTimer
import logging

from egg_farm_system.modules.alert_rules import AlertEngine

logger = logging.getLogger(__name__)


class AlertScheduler:
    """Schedule periodic alert checking"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AlertScheduler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_alerts)
        self.engine = AlertEngine()
        self.interval_minutes = 30
        self._initialized = True
        logger.info("Alert scheduler initialized")
    
    def start(self, interval_minutes: int = 30):
        """Start checking alerts periodically"""
        self.interval_minutes = interval_minutes
        self.timer.start(interval_minutes * 60 * 1000)  # Convert to milliseconds
        logger.info(f"Alert scheduler started (interval: {interval_minutes} minutes)")
        # Check immediately on start
        self.check_alerts()
    
    def stop(self):
        """Stop checking alerts"""
        self.timer.stop()
        logger.info("Alert scheduler stopped")
    
    def check_alerts(self):
        """Check all alert rules"""
        try:
            logger.info("Checking alert rules...")
            alerts = self.engine.trigger_alerts()
            logger.info(f"Alert check complete: {len(alerts)} alerts triggered")
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def check_now(self):
        """Manually trigger alert check"""
        self.check_alerts()
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.timer.isActive()
