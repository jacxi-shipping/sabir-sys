"""
Command Palette for quick actions (Ctrl+K)
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
import logging

logger = logging.getLogger(__name__)


class CommandPalette(QDialog):
    """Quick command palette (Ctrl+K)"""
    
    command_executed = Signal(str, dict)  # command_id, data
    
    COMMANDS = [
        # Navigation
        ('goto_dashboard', 'Go to Dashboard', 'navigation', {}),
        ('goto_farms', 'Go to Farms', 'navigation', {}),
        ('goto_production', 'Go to Production', 'navigation', {}),
        ('goto_sales', 'Go to Sales', 'navigation', {}),
        ('goto_purchases', 'Go to Purchases', 'navigation', {}),
        ('goto_inventory', 'Go to Inventory', 'navigation', {}),
        ('goto_parties', 'Go to Parties', 'navigation', {}),
        ('goto_reports', 'Go to Reports', 'navigation', {}),
        ('goto_expenses', 'Go to Expenses', 'navigation', {}),
        ('goto_employees', 'Go to Employees', 'navigation', {}),
        
        # Quick Actions
        ('record_production', 'Record Today\'s Production', 'action', {}),
        ('add_sale', 'Add Sale', 'action', {}),
        ('add_purchase', 'Add Purchase', 'action', {}),
        ('record_mortality', 'Record Mortality', 'action', {}),
        ('issue_feed', 'Issue Feed', 'action', {}),
        ('add_expense', 'Add Expense', 'action', {}),
        ('add_party', 'Add Party / Customer', 'action', {}),
        ('add_payment', 'Record Payment', 'action', {}),
        
        # Tools
        ('refresh_dashboard', 'Refresh Dashboard', 'tool', {}),
        ('import_data', 'Import Data', 'tool', {}),
        ('export_report', 'Export Report', 'tool', {}),
        ('check_alerts', 'Check Alerts Now', 'tool', {}),
        ('backup_database', 'Backup Database', 'tool', {}),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setMinimumWidth(500)
        self.setMaximumWidth(600)
        self.setup_ui()
        self.filter_commands("")
    
    def setup_ui(self):
        """Setup palette UI"""
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel(" Quick Actions (Ctrl+K)")
        header.setProperty('class', 'command-palette-header')
        layout.addWidget(header)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type to search commands...")
        self.search_box.setProperty('class', 'command-palette-search')
        self.search_box.textChanged.connect(self.filter_commands)
        layout.addWidget(self.search_box)
        
        # Command list
        self.command_list = QListWidget()
        self.command_list.setProperty('class', 'command-palette-list')
        self.command_list.itemActivated.connect(self.execute_command)
        self.command_list.setMinimumHeight(300)
        self.command_list.setMaximumHeight(400)
        layout.addWidget(self.command_list)
        
        # Footer with hint
        footer = QLabel("↵ Enter to execute • Esc to close")
        footer.setProperty('class', 'command-palette-footer')
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
        
        self.setLayout(layout)
        
        # Setup keyboard shortcuts
        self.enter_shortcut = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.enter_shortcut.activated.connect(self.execute_selected)
        
        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.esc_shortcut.activated.connect(self.reject)
        
        # Arrow keys
        self.down_shortcut = QShortcut(QKeySequence(Qt.Key_Down), self.search_box)
        self.down_shortcut.activated.connect(self.select_next)
        
        self.up_shortcut = QShortcut(QKeySequence(Qt.Key_Up), self.search_box)
        self.up_shortcut.activated.connect(self.select_previous)
    
    def filter_commands(self, text: str):
        """Filter commands by search text"""
        self.command_list.clear()
        
        search_text = text.lower()
        
        for cmd_id, cmd_name, category, data in self.COMMANDS:
            if not search_text or search_text in cmd_name.lower() or search_text in category.lower():
                # Create item with icon/category indicator
                category_icon = {
                    'navigation': '🧭',
                    'action': '⚡',
                    'tool': '🔧'
                }.get(category, '•')
                
                item_text = f"{category_icon} {cmd_name}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, cmd_id)
                item.setData(Qt.UserRole + 1, data)
                
                self.command_list.addItem(item)
        
        # Select first item
        if self.command_list.count() > 0:
            self.command_list.setCurrentRow(0)
    
    def select_next(self):
        """Select next item in list"""
        current = self.command_list.currentRow()
        if current < self.command_list.count() - 1:
            self.command_list.setCurrentRow(current + 1)
    
    def select_previous(self):
        """Select previous item in list"""
        current = self.command_list.currentRow()
        if current > 0:
            self.command_list.setCurrentRow(current - 1)
    
    def execute_selected(self):
        """Execute the currently selected command"""
        current_item = self.command_list.currentItem()
        if current_item:
            self.execute_command(current_item)
    
    def execute_command(self, item):
        """Execute selected command"""
        cmd_id = item.data(Qt.UserRole)
        data = item.data(Qt.UserRole + 1)
        
        logger.info(f"Executing command: {cmd_id}")
        
        # Emit signal with command
        self.command_executed.emit(cmd_id, data)
        
        # Close palette
        self.accept()
    
    def showEvent(self, event):
        """Focus search box when shown"""
        super().showEvent(event)
        self.search_box.setFocus()
        self.search_box.selectAll()
