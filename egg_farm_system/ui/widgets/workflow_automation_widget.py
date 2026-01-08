"""
Workflow Automation Management Widget
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from egg_farm_system.utils.workflow_automation import (
    WorkflowAutomation, TaskFrequency, get_workflow_automation
)

logger = logging.getLogger(__name__)


class TaskDialog(QDialog):
    """Dialog for creating/editing scheduled tasks"""
    
    def __init__(self, parent=None, task_id=None):
        super().__init__(parent)
        self.task_id = task_id
        self.setWindowTitle("Scheduled Task" if task_id else "New Scheduled Task")
        self.setMinimumSize(400, 300)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        form.addRow("Task Name:", self.name_edit)
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems([f.value for f in TaskFrequency])
        form.addRow("Frequency:", self.frequency_combo)
        
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        form.addRow("", self.enabled_check)
        
        layout.addLayout(form)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def get_task_data(self):
        """Get task data from form"""
        return {
            'name': self.name_edit.text(),
            'frequency': TaskFrequency(self.frequency_combo.currentText()),
            'enabled': self.enabled_check.isChecked()
        }


class WorkflowAutomationWidget(QWidget):
    """Workflow automation management widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workflow = get_workflow_automation()
        self.init_ui()
        self.refresh_tasks()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Workflow Automation")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Tasks section
        tasks_group = QGroupBox("Scheduled Tasks")
        tasks_layout = QVBoxLayout()
        
        # Buttons
        btn_layout = QHBoxLayout()
        new_task_btn = QPushButton("New Task")
        new_task_btn.clicked.connect(self.create_task)
        btn_layout.addWidget(new_task_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_tasks)
        btn_layout.addWidget(refresh_btn)
        
        run_now_btn = QPushButton("Run Pending Tasks")
        run_now_btn.clicked.connect(self.run_pending_tasks)
        btn_layout.addWidget(run_now_btn)
        
        btn_layout.addStretch()
        tasks_layout.addLayout(btn_layout)
        
        # Tasks table
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "Task ID", "Name", "Frequency", "Enabled", "Last Run", "Next Run"
        ])
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.verticalHeader().setMinimumSectionSize(40)
        self.tasks_table.verticalHeader().setDefaultSectionSize(40)
        tasks_layout.addWidget(self.tasks_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        enable_btn = QPushButton("Enable/Disable")
        enable_btn.clicked.connect(self.toggle_task)
        action_layout.addWidget(enable_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_task)
        action_layout.addWidget(delete_btn)
        
        action_layout.addStretch()
        tasks_layout.addLayout(action_layout)
        
        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)
        
        layout.addStretch()
    
    def refresh_tasks(self):
        """Refresh tasks table"""
        status = self.workflow.get_task_status()
        
        self.tasks_table.setRowCount(len(status))
        for row, task in enumerate(status):
            self.tasks_table.setItem(row, 0, QTableWidgetItem(task['task_id']))
            self.tasks_table.setItem(row, 1, QTableWidgetItem(task['name']))
            self.tasks_table.setItem(row, 2, QTableWidgetItem(task['frequency']))
            self.tasks_table.setItem(row, 3, QTableWidgetItem("Yes" if task['enabled'] else "No"))
            self.tasks_table.setItem(row, 4, QTableWidgetItem(task['last_run'] or "Never"))
            self.tasks_table.setItem(row, 5, QTableWidgetItem(task['next_run'] or "N/A"))
    
    def create_task(self):
        """Create new scheduled task"""
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_task_data()
            
            # Map task name to callback
            from egg_farm_system.utils.workflow_automation import (
                create_daily_backup, generate_daily_report, check_low_stock_alerts
            )
            
            task_callbacks = {
                'Daily Backup': create_daily_backup,
                'Daily Report': generate_daily_report,
                'Low Stock Check': check_low_stock_alerts
            }
            
            callback = task_callbacks.get(data['name'], lambda **kwargs: None)
            task_id = data['name'].lower().replace(' ', '_')
            
            self.workflow.register_task(
                task_id=task_id,
                name=data['name'],
                frequency=data['frequency'],
                callback=callback,
                enabled=data['enabled']
            )
            
            QMessageBox.information(self, "Success", "Task created successfully")
            self.refresh_tasks()
    
    def toggle_task(self):
        """Toggle task enabled/disabled"""
        current_row = self.tasks_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a task")
            return
        
        task_id = self.tasks_table.item(current_row, 0).text()
        current_enabled = self.tasks_table.item(current_row, 3).text() == "Yes"
        
        self.workflow.enable_task(task_id, not current_enabled)
        self.refresh_tasks()
    
    def delete_task(self):
        """Delete a task"""
        current_row = self.tasks_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a task")
            return
        
        task_id = self.tasks_table.item(current_row, 0).text()
        task_name = self.tasks_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete task '{task_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.workflow.unregister_task(task_id)
            QMessageBox.information(self, "Deleted", "Task deleted successfully")
            self.refresh_tasks()
    
    def run_pending_tasks(self):
        """Run all pending tasks"""
        self.workflow.run_pending_tasks()
        QMessageBox.information(self, "Complete", "Pending tasks executed")
        self.refresh_tasks()

