"""
Base class for customizable dashboard widgets
"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class DashboardWidgetBase(QFrame):
    """Base class for dashboard widgets"""
    
    refresh_requested = Signal()
    settings_requested = Signal()
    
    def __init__(self, title: str, widget_id: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.widget_id = widget_id
        self.setup_ui()
    
    def setup_ui(self):
        """Setup widget UI"""
        self.setObjectName("dashboard-widget")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame#dashboard-widget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            QFrame#dashboard-widget:hover {
                border: 1px solid #b0b0b0;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(5)
        
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("widget-title")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setFixedSize(28, 28)
        self.refresh_btn.setToolTip("Refresh")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
                color: #666;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-radius: 14px;
            }
        """)
        self.refresh_btn.clicked.connect(self.on_refresh)
        
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 16px;
                color: #666;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-radius: 14px;
            }
        """)
        self.settings_btn.clicked.connect(self.on_settings)
        
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.refresh_btn)
        header.addWidget(self.settings_btn)
        
        layout.addLayout(header)
        
        # Content area (override in subclasses)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_widget.setLayout(self.content_layout)
        layout.addWidget(self.content_widget)
        
        self.setLayout(layout)
        self.setMinimumHeight(250)
    
    def on_refresh(self):
        """Handle refresh button click"""
        self.refresh()
        self.refresh_requested.emit()
    
    def on_settings(self):
        """Handle settings button click"""
        self.show_settings()
        self.settings_requested.emit()
    
    def refresh(self):
        """Refresh widget data - override in subclasses"""
        logger.info(f"Refreshing widget: {self.widget_id}")
    
    def show_settings(self):
        """Show widget settings - override in subclasses"""
        logger.info(f"Showing settings for widget: {self.widget_id}")
    
    def clear_content(self):
        """Clear all content widgets"""
        for i in reversed(range(self.content_layout.count())): 
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
    
    def display_no_data(self):
        """Display 'no data' message"""
        self.clear_content()
        no_data_label = QLabel("No data available")
        no_data_label.setAlignment(Qt.AlignCenter)
        no_data_label.setStyleSheet("color: #999; font-size: 12pt; padding: 40px;")
        self.content_layout.addWidget(no_data_label)
    
    def display_error(self, message: str):
        """Display error message"""
        self.clear_content()
        error_label = QLabel(f"Error: {message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setWordWrap(True)
        error_label.setStyleSheet("color: #e74c3c; font-size: 11pt; padding: 20px;")
        self.content_layout.addWidget(error_label)
