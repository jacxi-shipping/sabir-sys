"""
Audit Trail Viewer Widget
"""
import logging
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit, QTextEdit,
    QDialog, QFormLayout, QSizePolicy
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont

from egg_farm_system.utils.audit_trail import get_audit_trail, ActionType

logger = logging.getLogger(__name__)


class AuditTrailViewerWidget(QWidget):
    """Audit trail viewer widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audit_trail = get_audit_trail()
        self.init_ui()
        self.refresh_logs()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Audit Trail")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Filters
        filters_group = QGroupBox("Filters")
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Entity Type:"))
        self.entity_type_combo = QComboBox()
        self.entity_type_combo.addItem("All", None)
        self.entity_type_combo.addItems(["Farm", "Shed", "Flock", "Party", "Sale", "Purchase", "Expense"])
        filters_layout.addWidget(self.entity_type_combo)
        
        filters_layout.addWidget(QLabel("Action Type:"))
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItem("All", None)
        for action in ActionType:
            self.action_type_combo.addItem(action.value.title(), action)
        filters_layout.addWidget(self.action_type_combo)
        
        filters_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        filters_layout.addWidget(self.start_date)
        
        filters_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        filters_layout.addWidget(self.end_date)
        
        filter_btn = QPushButton("Filter")
        filter_btn.clicked.connect(self.refresh_logs)
        filters_layout.addWidget(filter_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_logs)
        filters_layout.addWidget(refresh_btn)
        
        filters_layout.addStretch()
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Entity Type", "Entity", "Description", "Details"
        ])
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.doubleClicked.connect(self.show_details)
        layout.addWidget(self.logs_table)
    
    def refresh_logs(self):
        """Refresh audit logs"""
        entity_type = self.entity_type_combo.currentData()
        action_type = self.action_type_combo.currentData()
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        
        logs = self.audit_trail.get_logs(
            entity_type=entity_type,
            action_type=action_type,
            start_date=datetime.combine(start, datetime.min.time()),
            end_date=datetime.combine(end, datetime.max.time())
        )
        
        self.logs_table.setRowCount(len(logs))
        for row, log in enumerate(logs):
            self.logs_table.setItem(row, 0, QTableWidgetItem(
                log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else ""
            ))
            self.logs_table.setItem(row, 1, QTableWidgetItem(log.username or "System"))
            self.logs_table.setItem(row, 2, QTableWidgetItem(log.action_type.value))
            self.logs_table.setItem(row, 3, QTableWidgetItem(log.entity_type))
            entity_name = log.entity_name or (str(log.entity_id) if log.entity_id else "N/A")
            self.logs_table.setItem(row, 4, QTableWidgetItem(entity_name))
            self.logs_table.setItem(row, 5, QTableWidgetItem(log.description or ""))
            self.logs_table.setItem(row, 6, QTableWidgetItem("Click to view"))
            self.logs_table.item(row, 6).setData(Qt.UserRole, log)
        
        self.logs_table.resizeColumnsToContents()
    
    def show_details(self, index):
        """Show audit log details"""
        if index.column() != 6:
            return
        
        log = self.logs_table.item(index.row(), 6).data(Qt.UserRole)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Audit Log Details")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        details = QTextEdit()
        details.setReadOnly(True)
        
        text = f"Audit Log Details\n"
        text += f"{'='*50}\n\n"
        text += f"Timestamp: {log.timestamp}\n"
        text += f"User: {log.username or 'System'}\n"
        text += f"Action: {log.action_type.value}\n"
        text += f"Entity Type: {log.entity_type}\n"
        text += f"Entity ID: {log.entity_id or 'N/A'}\n"
        text += f"Entity Name: {log.entity_name or 'N/A'}\n"
        text += f"Description: {log.description or 'N/A'}\n\n"
        
        if log.old_values:
            import json
            try:
                old_vals = json.loads(log.old_values)
                text += f"Old Values:\n{json.dumps(old_vals, indent=2)}\n\n"
            except:
                text += f"Old Values: {log.old_values}\n\n"
        
        if log.new_values:
            import json
            try:
                new_vals = json.loads(log.new_values)
                text += f"New Values:\n{json.dumps(new_vals, indent=2)}\n"
            except:
                text += f"New Values: {log.new_values}\n"
        
        details.setText(text)
        layout.addWidget(details)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()

