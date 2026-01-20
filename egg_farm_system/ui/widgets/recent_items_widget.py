"""
Recent Items Widget for Quick Access
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RecentItemsWidget(QWidget):
    """Show recently edited items"""
    
    item_clicked = Signal(str, int)  # entity_type, entity_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_recent_items()
    
    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Recent Items")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Items list
        self.items_list = QListWidget()
        self.items_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f5f5f5;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            QListWidget::item:selected {
                background-color: #e8f5e9;
                color: #1b5e20;
            }
        """)
        self.items_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.items_list)
        
        self.setLayout(layout)
    
    def load_recent_items(self):
        """Load recent items from audit trail"""
        try:
            from egg_farm_system.utils.audit_trail import get_audit_trail
            
            audit_trail = get_audit_trail()
            recent = audit_trail.get_recent_actions(limit=10)
            
            self.items_list.clear()
            
            for action in recent:
                # Format timestamp
                time_str = action.timestamp.strftime("%Y-%m-%d %H:%M")
                
                # Create item text
                icon = self._get_icon_for_action(action.action_type)
                item_text = f"{icon} {action.action_type}: {action.description}\n   {time_str}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, action)
                self.items_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Error loading recent items: {e}")
    
    def _get_icon_for_action(self, action_type: str) -> str:
        """Get icon for action type"""
        icons = {
            'CREATE': '➕',
            'UPDATE': '✏️',
            'DELETE': '🗑️',
            'VIEW': '👁️',
        }
        for key, icon in icons.items():
            if key in action_type.upper():
                return icon
        return '•'
    
    def on_item_clicked(self, item):
        """Handle item click"""
        try:
            action = item.data(Qt.UserRole)
            
            # Try to extract entity type and ID from description
            # This is a simplified implementation
            # You might want to store entity_type and entity_id in the audit trail
            
            logger.info(f"Recent item clicked: {action.description}")
            
            # Could emit signal to navigate to the item
            # For now, just log
            
        except Exception as e:
            logger.error(f"Error handling item click: {e}")
    
    def refresh(self):
        """Refresh the recent items list"""
        self.load_recent_items()
