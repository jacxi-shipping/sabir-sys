"""
Widget Configurator for customizable dashboard
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class WidgetConfigurator(QDialog):
    """Configure dashboard widgets"""
    
    AVAILABLE_WIDGETS = [
        ('mortality_trend', 'Mortality Trend (30 Days)'),
        ('top_customers', 'Top 5 Customers'),
        ('low_stock_alerts', 'Low Stock Alerts'),
        ('production_summary', 'Production Summary'),
        ('feed_usage', 'Feed Usage'),
        ('revenue_chart', 'Revenue Chart'),
    ]
    
    def __init__(self, current_widgets: list, parent=None):
        super().__init__(parent)
        self.current_widgets = current_widgets if current_widgets else []
        self.setWindowTitle("Configure Dashboard")
        self.resize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup configurator UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Configure Dashboard Widgets")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Select widgets to display on your dashboard:")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Widget list with checkboxes
        self.widget_list = QListWidget()
        self.widget_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        
        for widget_id, widget_name in self.AVAILABLE_WIDGETS:
            item = QListWidgetItem(widget_name)
            item.setData(Qt.UserRole, widget_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(
                Qt.Checked if widget_id in self.current_widgets else Qt.Unchecked
            )
            self.widget_list.addItem(item)
        
        layout.addWidget(self.widget_list)
        
        # Info
        info = QLabel("💡 Tip: You can rearrange widgets by dragging them on the dashboard")
        info.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self.select_all)
        
        self.btn_deselect_all = QPushButton("Deselect All")
        self.btn_deselect_all.clicked.connect(self.deselect_all)
        
        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addWidget(self.btn_deselect_all)
        btn_layout.addStretch()
        
        self.btn_save = QPushButton("Save")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def select_all(self):
        """Select all widgets"""
        for i in range(self.widget_list.count()):
            item = self.widget_list.item(i)
            item.setCheckState(Qt.Checked)
    
    def deselect_all(self):
        """Deselect all widgets"""
        for i in range(self.widget_list.count()):
            item = self.widget_list.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def get_selected_widgets(self) -> list:
        """Get list of selected widget IDs"""
        selected = []
        for i in range(self.widget_list.count()):
            item = self.widget_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected
