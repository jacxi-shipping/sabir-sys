"""
Breadcrumb Navigation Widget
"""
import logging
from typing import List, Dict, Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class BreadcrumbWidget(QWidget):
    """Breadcrumb navigation widget"""
    
    # Signal emitted when a breadcrumb is clicked
    path_clicked = Signal(str)  # Emits the path that was clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.paths: List[Dict[str, str]] = []  # List of {name, path} dictionaries
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #3498db;
                text-align: left;
                padding: 2px 5px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
            QLabel {
                color: #7f8c8d;
            }
        """)
    
    def set_paths(self, paths: List[Dict[str, str]]):
        """
        Set breadcrumb paths
        
        Args:
            paths: List of dictionaries with 'name' and 'path' keys
        """
        self.paths = paths
        self._update_display()
    
    def add_path(self, name: str, path: str):
        """Add a path to breadcrumbs"""
        self.paths.append({'name': name, 'path': path})
        self._update_display()
    
    def clear(self):
        """Clear all breadcrumbs"""
        self.paths = []
        self._update_display()
    
    def _update_display(self):
        """Update breadcrumb display"""
        # Clear existing widgets
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.paths:
            return
        
        # Add breadcrumbs
        for i, path_info in enumerate(self.paths):
            if i > 0:
                # Add separator
                separator = QLabel(">")
                separator.setStyleSheet("color: #95a5a6; padding: 0 5px;")
                self.layout.addWidget(separator)
            
            # Add breadcrumb button
            btn = QPushButton(path_info['name'])
            btn.setCursor(Qt.PointingHandCursor)
            
            # Make last item non-clickable (current page)
            if i == len(self.paths) - 1:
                btn.setEnabled(False)
                btn.setStyleSheet("""
                    QPushButton {
                        border: none;
                        background-color: transparent;
                        color: #2c3e50;
                        font-weight: bold;
                        text-align: left;
                        padding: 2px 5px;
                    }
                """)
            else:
                btn.clicked.connect(lambda checked, p=path_info['path']: self.path_clicked.emit(p))
            
            self.layout.addWidget(btn)
        
        self.layout.addStretch()


class NavigationHistory:
    """Manages navigation history"""
    
    def __init__(self, max_history: int = 20):
        self.history: List[Dict[str, str]] = []
        self.current_index = -1
        self.max_history = max_history
    
    def add(self, name: str, path: str, callback: callable):
        """
        Add a page to history
        
        Args:
            name: Page name
            path: Page path/identifier
            callback: Function to call to navigate to this page
        """
        # Remove any forward history if we're not at the end
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Add new entry
        self.history.append({
            'name': name,
            'path': path,
            'callback': callback
        })
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.current_index = len(self.history) - 1
    
    def can_go_back(self) -> bool:
        """Check if can go back"""
        return self.current_index > 0
    
    def can_go_forward(self) -> bool:
        """Check if can go forward"""
        return self.current_index < len(self.history) - 1
    
    def go_back(self):
        """Go back in history"""
        if self.can_go_back():
            self.current_index -= 1
            entry = self.history[self.current_index]
            if entry['callback']:
                entry['callback']()
            return True
        return False
    
    def go_forward(self):
        """Go forward in history"""
        if self.can_go_forward():
            self.current_index += 1
            entry = self.history[self.current_index]
            if entry['callback']:
                entry['callback']()
            return True
        return False
    
    def get_current(self) -> Optional[Dict[str, str]]:
        """Get current page"""
        if 0 <= self.current_index < len(self.history):
            return self.history[self.current_index]
        return None
    
    def get_recent(self, count: int = 5) -> List[Dict[str, str]]:
        """Get recent pages"""
        start = max(0, len(self.history) - count)
        return self.history[start:]

