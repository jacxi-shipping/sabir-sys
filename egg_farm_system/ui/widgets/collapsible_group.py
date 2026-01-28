"""
Collapsible Group Widget for Navigation
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFrame, QLabel
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QFont, QIcon
from pathlib import Path


class CollapsibleGroup(QWidget):
    """Collapsible group widget for navigation"""
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_expanded = False  # Start collapsed by default
        self.content_widget = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header button
        arrow = "▶" if not self.is_expanded else "▼"
        self.header_btn = QPushButton(f"{arrow} {self.title}")
        self.header_btn.setCheckable(True)
        self.header_btn.setChecked(self.is_expanded)
        self.header_btn.setProperty('class', 'nav-group-header')
        self.header_btn.clicked.connect(self.toggle)
        layout.addWidget(self.header_btn)
        
        # Content frame
        self.content_frame = QFrame()
        self.content_frame.setFrameShape(QFrame.NoFrame)
        self.content_frame.setVisible(self.is_expanded)  # Set initial visibility
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setSpacing(2)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        
        layout.addWidget(self.content_frame)
    
    def add_button(self, text, callback, icon_path=None):
        """Add a button to the collapsible group"""
        btn = QPushButton(text)
        btn.setMinimumHeight(38)
        btn.setProperty('class', 'nav-group-item')
        
        if icon_path:
            from egg_farm_system.config import get_asset_path
            icon_file = get_asset_path(icon_path)
            if Path(icon_file).exists():
                icon = QIcon(icon_file)
                btn.setIcon(icon)
                btn.setIconSize(QSize(20, 20))  # Set proper icon size
        
        btn.clicked.connect(callback)
        self.content_layout.addWidget(btn)
        return btn
    
    def toggle(self):
        """Toggle expand/collapse"""
        self.is_expanded = self.header_btn.isChecked()
        self.content_frame.setVisible(self.is_expanded)
        
        # Update button text with arrow
        arrow = "▼" if self.is_expanded else "▶"
        self.header_btn.setText(f"{arrow} {self.title}")

    def setTitle(self, title):
        """Set the group's title and update header button text"""
        self.title = title
        arrow = "▼" if self.is_expanded else "▶"
        self.header_btn.setText(f"{arrow} {self.title}")
