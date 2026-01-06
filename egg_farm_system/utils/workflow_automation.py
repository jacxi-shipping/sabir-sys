"""
Workflow Automation Module for Egg Farm Management System
"""
import logging
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import json

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.settings import SettingsManager

logger = logging.getLogger(__name__)


class TaskFrequency(Enum):
    """Task frequency options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ScheduledTask:
    """Represents a scheduled task"""
    
    def __init__(self, task_id: str, name: str, frequency: TaskFrequency,
                 callback: Callable, enabled: bool = True, **kwargs):
        self.task_id = task_id
        self.name = name
        self.frequency = frequency
        self.callback = callback
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.kwargs = kwargs
        self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate next run time"""
        if not self.enabled:
            return
        
        now = datetime.utcnow()
        
        if self.frequency == TaskFrequency.DAILY:
            self.next_run = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        elif self.frequency == TaskFrequency.WEEKLY:
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            self.next_run = now.replace(hour=0, minute=0, second=0) + timedelta(days=days_until_monday)
        elif self.frequency == TaskFrequency.MONTHLY:
            # First day of next month
            if now.month == 12:
                self.next_run = datetime(now.year + 1, 1, 1)
            else:
                self.next_run = datetime(now.year, now.month + 1, 1)
        else:
            # Custom - use interval from kwargs
            interval_hours = self.kwargs.get('interval_hours', 24)
            self.next_run = now + timedelta(hours=interval_hours)
    
    def should_run(self) -> bool:
        """Check if task should run now"""
        if not self.enabled:
            return False
        
        if self.next_run is None:
            return False
        
        return datetime.utcnow() >= self.next_run
    
    def run(self):
        """Execute the task"""
        try:
            logger.info(f"Running scheduled task: {self.name}")
            result = self.callback(**self.kwargs)
            self.last_run = datetime.utcnow()
            self._calculate_next_run()
            return result
        except Exception as e:
            logger.error(f"Error running task {self.name}: {e}")
            return None


class WorkflowAutomation:
    """Manages workflow automation and scheduled tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.business_rules: List[Dict[str, Any]] = []
        self._load_tasks()
    
    def register_task(self, task_id: str, name: str, frequency: TaskFrequency,
                     callback: Callable, enabled: bool = True, **kwargs):
        """Register a scheduled task"""
        task = ScheduledTask(task_id, name, frequency, callback, enabled, **kwargs)
        self.tasks[task_id] = task
        self._save_tasks()
        logger.info(f"Registered task: {name} ({frequency.value})")
    
    def unregister_task(self, task_id: str):
        """Unregister a scheduled task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
    
    def enable_task(self, task_id: str, enabled: bool = True):
        """Enable or disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = enabled
            self._save_tasks()
    
    def run_pending_tasks(self):
        """Run all pending tasks"""
        for task_id, task in self.tasks.items():
            if task.should_run():
                task.run()
    
    def get_task_status(self) -> List[Dict[str, Any]]:
        """Get status of all tasks"""
        status = []
        for task_id, task in self.tasks.items():
            status.append({
                'task_id': task_id,
                'name': task.name,
                'frequency': task.frequency.value,
                'enabled': task.enabled,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'next_run': task.next_run.isoformat() if task.next_run else None
            })
        return status
    
    def add_business_rule(self, rule_id: str, name: str, condition: Callable, action: Callable, enabled: bool = True):
        """Add a business rule"""
        rule = {
            'rule_id': rule_id,
            'name': name,
            'condition': condition,
            'action': action,
            'enabled': enabled
        }
        self.business_rules.append(rule)
        logger.info(f"Added business rule: {name}")
    
    def evaluate_rules(self, context: Dict[str, Any] = None):
        """Evaluate all enabled business rules"""
        if context is None:
            context = {}
        
        for rule in self.business_rules:
            if not rule['enabled']:
                continue
            
            try:
                if rule['condition'](context):
                    rule['action'](context)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule['name']}: {e}")
    
    def _save_tasks(self):
        """Save tasks to settings"""
        try:
            tasks_data = {}
            for task_id, task in self.tasks.items():
                tasks_data[task_id] = {
                    'name': task.name,
                    'frequency': task.frequency.value,
                    'enabled': task.enabled,
                    'kwargs': task.kwargs,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None
                }
            
            SettingsManager.set_setting('scheduled_tasks', json.dumps(tasks_data))
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
    
    def _load_tasks(self):
        """Load tasks from settings"""
        try:
            tasks_json = SettingsManager.get_setting('scheduled_tasks')
            if tasks_json:
                tasks_data = json.loads(tasks_json)
                # Note: Callbacks need to be re-registered as they can't be serialized
                # This is just for persistence of task metadata
        except Exception as e:
            logger.debug(f"No saved tasks or error loading: {e}")


# Predefined task callbacks
def create_daily_backup(**kwargs):
    """Create daily backup"""
    try:
        from egg_farm_system.utils.backup_manager import BackupManager
        backup_manager = BackupManager()
        backup_manager.create_backup(include_logs=kwargs.get('include_logs', False))
        logger.info("Daily backup created")
        return True
    except Exception as e:
        logger.error(f"Error creating daily backup: {e}")
        return False


def generate_daily_report(**kwargs):
    """Generate and email daily report"""
    try:
        from egg_farm_system.modules.reports import ReportGenerator
        from egg_farm_system.utils.email_service import EmailService
        
        farm_id = kwargs.get('farm_id', 1)
        report_generator = ReportGenerator()
        today = datetime.utcnow().date()
        
        # Generate report
        data = report_generator.daily_egg_production_report(farm_id, datetime.combine(today, datetime.min.time()))
        
        # Email report (if email service configured)
        email_service = EmailService()
        if email_service.is_configured():
            email_service.send_report(data, "daily_production", [kwargs.get('email', '')])
        
        logger.info("Daily report generated")
        return True
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return False


def check_low_stock_alerts(**kwargs):
    """Check and send low stock alerts"""
    try:
        from egg_farm_system.modules.inventory import InventoryManager
        from egg_farm_system.utils.notification_manager import get_notification_manager
        
        inventory_manager = InventoryManager()
        notification_manager = get_notification_manager()
        
        notification_manager.check_low_stock(inventory_manager)
        logger.info("Low stock alerts checked")
        return True
    except Exception as e:
        logger.error(f"Error checking low stock: {e}")
        return False


    def create_daily_backup(self, **kwargs):
        """Create daily backup"""
        return create_daily_backup(**kwargs)
    
    def generate_daily_report(self, **kwargs):
        """Generate and email daily report"""
        return generate_daily_report(**kwargs)
    
    def check_low_stock_alerts(self, **kwargs):
        """Check and send low stock alerts"""
        return check_low_stock_alerts(**kwargs)


# Global workflow automation instance
_workflow_automation: Optional[WorkflowAutomation] = None


def get_workflow_automation() -> WorkflowAutomation:
    """Get global workflow automation instance"""
    global _workflow_automation
    if _workflow_automation is None:
        _workflow_automation = WorkflowAutomation()
    return _workflow_automation

