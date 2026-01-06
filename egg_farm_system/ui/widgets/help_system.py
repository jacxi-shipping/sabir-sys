"""
In-App Help System
"""
import logging
from typing import Dict, Optional
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QTreeWidget, QTreeWidgetItem, QSplitter, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)


class HelpSystem:
    """Help system manager"""
    
    HELP_CONTENT = {
        "Getting Started": {
            "Introduction": """
            <h2>Welcome to Egg Farm Management System</h2>
            <p>This application helps you manage your egg farm operations efficiently.</p>
            <h3>Key Features:</h3>
            <ul>
                <li>Farm and Shed Management</li>
                <li>Egg Production Tracking</li>
                <li>Feed Manufacturing and Inventory</li>
                <li>Sales and Purchase Management</li>
                <li>Financial Reports and Analytics</li>
            </ul>
            """,
            "First Steps": """
            <h2>First Steps</h2>
            <ol>
                <li><strong>Create Farms:</strong> Go to Farm Management and add your farms (up to 4)</li>
                <li><strong>Set Up Sheds:</strong> Create sheds for each farm</li>
                <li><strong>Add Flocks:</strong> Create flocks in your sheds</li>
                <li><strong>Add Parties:</strong> Add customers and suppliers in Parties section</li>
                <li><strong>Configure Feed:</strong> Set up raw materials and feed formulas</li>
            </ol>
            """,
            "Daily Operations": """
            <h2>Daily Operations</h2>
            <p>Your daily workflow:</p>
            <ol>
                <li>Record egg production for each shed</li>
                <li>Issue feed to sheds</li>
                <li>Record sales and purchases</li>
                <li>Track expenses</li>
                <li>Review dashboard for key metrics</li>
            </ol>
            """
        },
        "Farm Management": {
            "Overview": """
            <h2>Farm Management</h2>
            <p>Manage up to 4 farms in the system.</p>
            <h3>Creating a Farm:</h3>
            <ol>
                <li>Click "Farm Management" in the sidebar</li>
                <li>Click "New Farm" button</li>
                <li>Enter farm name and location</li>
                <li>Click "Save"</li>
            </ol>
            """,
            "Sheds": """
            <h2>Shed Management</h2>
            <p>Each farm can have multiple sheds.</p>
            <ul>
                <li>Define shed capacity (maximum birds)</li>
                <li>Track utilization</li>
                <li>View shed statistics</li>
            </ul>
            """,
            "Flocks": """
            <h2>Flock Management</h2>
            <p>Manage bird flocks in sheds.</p>
            <ul>
                <li>Track initial bird count</li>
                <li>Record daily mortality</li>
                <li>Monitor live bird count</li>
                <li>Calculate mortality percentage</li>
            </ul>
            """
        },
        "Production": {
            "Recording Production": """
            <h2>Recording Egg Production</h2>
            <p>Record daily egg production for each shed.</p>
            <h3>Steps:</h3>
            <ol>
                <li>Go to "Egg Production"</li>
                <li>Select the shed</li>
                <li>Enter counts for each grade:
                    <ul>
                        <li>Small</li>
                        <li>Medium</li>
                        <li>Large</li>
                        <li>Broken</li>
                    </ul>
                </li>
                <li>Save the record</li>
            </ol>
            """,
            "Production Reports": """
            <h2>Production Reports</h2>
            <p>View production reports:</p>
            <ul>
                <li>Daily production report</li>
                <li>Monthly production summary</li>
                <li>Production trends and charts</li>
            </ul>
            """
        },
        "Feed Management": {
            "Raw Materials": """
            <h2>Raw Materials</h2>
            <p>Manage raw materials for feed production.</p>
            <ul>
                <li>Add raw materials with stock levels</li>
                <li>Set low stock alerts</li>
                <li>Track costs in AFG and USD</li>
            </ul>
            """,
            "Feed Formulas": """
            <h2>Feed Formulas</h2>
            <p>Create feed formulas (Starter, Grower, Layer).</p>
            <ul>
                <li>Define ingredient percentages</li>
                <li>Must total 100%</li>
                <li>Automatic cost calculation</li>
            </ul>
            """,
            "Batch Production": """
            <h2>Feed Batch Production</h2>
            <p>Produce feed batches:</p>
            <ol>
                <li>Select feed formula</li>
                <li>Enter batch quantity</li>
                <li>System deducts raw materials</li>
                <li>Creates finished feed inventory</li>
            </ol>
            """
        },
        "Accounting": {
            "Ledger System": """
            <h2>Ledger System</h2>
            <p>The system maintains a ledger for each party.</p>
            <ul>
                <li><strong>Positive Balance:</strong> Party owes you</li>
                <li><strong>Negative Balance:</strong> You owe the party</li>
                <li>All transactions auto-post to ledger</li>
            </ul>
            """,
            "Dual Currency": """
            <h2>Dual Currency Support</h2>
            <p>All transactions support both AFG and USD:</p>
            <ul>
                <li>Base currency: AFG</li>
                <li>Secondary currency: USD</li>
                <li>Exchange rate stored per transaction</li>
                <li>Historical accuracy maintained</li>
            </ul>
            """
        },
        "Reports": {
            "Generating Reports": """
            <h2>Generating Reports</h2>
            <p>Access reports from the Reports section:</p>
            <ol>
                <li>Select report type</li>
                <li>Choose date or date range</li>
                <li>Click "Generate Report"</li>
                <li>Export to CSV, Excel, or Print</li>
            </ol>
            """,
            "Report Types": """
            <h2>Available Reports</h2>
            <ul>
                <li><strong>Daily Production:</strong> Production by shed for a specific date</li>
                <li><strong>Monthly Production:</strong> Daily summary for a month</li>
                <li><strong>Feed Usage:</strong> Feed consumption over a period</li>
                <li><strong>Party Statement:</strong> Ledger statement for a party</li>
            </ul>
            """
        },
        "Keyboard Shortcuts": {
            "Navigation": """
            <h2>Navigation Shortcuts</h2>
            <ul>
                <li><strong>Ctrl+1:</strong> Dashboard</li>
                <li><strong>Ctrl+2:</strong> Farm Management</li>
                <li><strong>Ctrl+3:</strong> Egg Production</li>
                <li><strong>Ctrl+4:</strong> Feed Management</li>
                <li><strong>Ctrl+5:</strong> Inventory</li>
                <li><strong>Ctrl+6:</strong> Parties</li>
                <li><strong>Ctrl+7:</strong> Sales</li>
                <li><strong>Ctrl+8:</strong> Purchases</li>
                <li><strong>Ctrl+9:</strong> Expenses</li>
                <li><strong>Ctrl+0:</strong> Reports</li>
            </ul>
            """,
            "Actions": """
            <h2>Action Shortcuts</h2>
            <ul>
                <li><strong>F5:</strong> Refresh current page</li>
                <li><strong>Ctrl+F:</strong> Global search</li>
                <li><strong>Ctrl+P:</strong> Print</li>
                <li><strong>Ctrl+E:</strong> Export</li>
                <li><strong>Ctrl+S:</strong> Save</li>
                <li><strong>Ctrl+B:</strong> Create backup</li>
                <li><strong>F1:</strong> Show help</li>
                <li><strong>Esc:</strong> Close/Cancel</li>
            </ul>
            """
        }
    }
    
    @classmethod
    def get_help_content(cls, category: str, topic: str) -> str:
        """Get help content for a category and topic"""
        if category in cls.HELP_CONTENT:
            if topic in cls.HELP_CONTENT[category]:
                return cls.HELP_CONTENT[category][topic]
        return "<p>Help content not found.</p>"
    
    @classmethod
    def get_categories(cls) -> list:
        """Get all help categories"""
        return list(cls.HELP_CONTENT.keys())
    
    @classmethod
    def get_topics(cls, category: str) -> list:
        """Get all topics in a category"""
        if category in cls.HELP_CONTENT:
            return list(cls.HELP_CONTENT[category].keys())
        return []


class HelpDialog(QDialog):
    """Help dialog widget"""
    
    def __init__(self, parent=None, category: Optional[str] = None, topic: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("Help - Egg Farm Management System")
        self.setMinimumSize(800, 600)
        self.init_ui()
        
        if category and topic:
            self.show_topic(category, topic)
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Splitter for sidebar and content
        splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar with topics
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        
        self.topic_tree = QTreeWidget()
        self.topic_tree.setHeaderLabel("Help Topics")
        self.topic_tree.itemClicked.connect(self._on_topic_selected)
        sidebar_layout.addWidget(self.topic_tree)
        
        splitter.addWidget(sidebar)
        
        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        content_layout.addWidget(self.content_text)
        
        splitter.addWidget(content_widget)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        # Populate topics
        self._populate_topics()
    
    def _populate_topics(self):
        """Populate topic tree"""
        help_system = HelpSystem()
        
        for category in help_system.get_categories():
            category_item = QTreeWidgetItem(self.topic_tree)
            category_item.setText(0, category)
            category_item.setData(0, Qt.UserRole, {'type': 'category', 'name': category})
            
            for topic in help_system.get_topics(category):
                topic_item = QTreeWidgetItem(category_item)
                topic_item.setText(0, topic)
                topic_item.setData(0, Qt.UserRole, {'type': 'topic', 'category': category, 'name': topic})
            
            category_item.setExpanded(True)
    
    def _on_topic_selected(self, item: QTreeWidgetItem, column: int):
        """Handle topic selection"""
        data = item.data(0, Qt.UserRole)
        if data and data.get('type') == 'topic':
            category = data['category']
            topic = data['name']
            self.show_topic(category, topic)
    
    def show_topic(self, category: str, topic: str):
        """Show help content for a topic"""
        content = HelpSystem.get_help_content(category, topic)
        self.content_text.setHtml(content)
        
        # Expand and select the topic in tree
        for i in range(self.topic_tree.topLevelItemCount()):
            category_item = self.topic_tree.topLevelItem(i)
            if category_item.text(0) == category:
                for j in range(category_item.childCount()):
                    topic_item = category_item.child(j)
                    if topic_item.text(0) == topic:
                        self.topic_tree.setCurrentItem(topic_item)
                        break
                break


def show_context_help(parent, category: str, topic: str):
    """Show context-sensitive help"""
    dialog = HelpDialog(parent, category, topic)
    dialog.exec()

