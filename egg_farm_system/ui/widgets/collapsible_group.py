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
        self.header_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 11pt;
                border: none;
                background-color: #34495e;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
            QPushButton:checked {
                background-color: #2c3e50;
            }
        """)
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
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 20px 10px 30px;
                border: none;
                background-color: transparent;
                color: #654321;
                border-radius: 6px;
                font-weight: 500;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: rgba(139, 69, 19, 0.15);
                color: #8B4513;
                border-left: 3px solid #8B4513;
                padding-left: 27px;
            }
        """)
        
        if icon_path:
            asset_dir = Path(__file__).parent.parent.parent / 'assets'
            icon_file = asset_dir / icon_path
            if icon_file.exists():
                icon = QIcon(str(icon_file))
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

