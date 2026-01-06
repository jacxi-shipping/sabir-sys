"""
Global Search Widget
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QFrame, QDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut

from egg_farm_system.utils.global_search import GlobalSearchManager

logger = logging.getLogger(__name__)


class GlobalSearchWidget(QDialog):
    """Global search dialog"""
    
    item_selected = Signal(dict)  # Emitted when user selects a result
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_manager = GlobalSearchManager()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._perform_search)
        
        self.setWindowTitle("Global Search")
        self.setMinimumSize(600, 500)
        self.init_ui()
        
        # Close on Escape
        QShortcut(QKeySequence("Escape"), self, self.close)
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Search input
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search farms, parties, sales, purchases, expenses...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._perform_search)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._perform_search)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Results
        results_label = QLabel("Results:")
        results_label.setFont(QFont("", 10, QFont.Bold))
        layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_item_selected)
        self.results_list.itemActivated.connect(self._on_item_selected)
        layout.addWidget(self.results_list)
        
        # Status
        self.status_label = QLabel("Enter search query...")
        self.status_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(self.status_label)
        
        # Focus on search input
        self.search_input.setFocus()
    
    def _on_search_text_changed(self, text: str):
        """Handle search text change with debounce"""
        if len(text.strip()) >= 2:
            self.search_timer.stop()
            self.search_timer.start(300)  # Wait 300ms before searching
        else:
            self.results_list.clear()
            self.status_label.setText("Enter at least 2 characters to search...")
    
    def _perform_search(self):
        """Perform the search"""
        query = self.search_input.text().strip()
        
        if len(query) < 2:
            self.status_label.setText("Enter at least 2 characters to search...")
            return
        
        self.status_label.setText("Searching...")
        self.results_list.clear()
        
        try:
            results = self.search_manager.search(query)
            
            total_results = sum(len(r) for r in results.values())
            
            if total_results == 0:
                self.status_label.setText("No results found")
                return
            
            # Group results by module
            for module_name, items in results.items():
                if not items:
                    continue
                
                # Add section header
                header_item = QListWidgetItem(f"--- {module_name.upper()} ({len(items)}) ---")
                header_item.setFlags(Qt.NoItemFlags)
                header_item.setForeground(Qt.gray)
                font = QFont()
                font.setBold(True)
                header_item.setFont(font)
                self.results_list.addItem(header_item)
                
                # Add results
                for item_data in items:
                    result_item = QListWidgetItem()
                    result_item.setText(f"{item_data['title']}\n{item_data['subtitle']}")
                    result_item.setData(Qt.UserRole, item_data)
                    self.results_list.addItem(result_item)
            
            self.status_label.setText(f"Found {total_results} result(s)")
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def _on_item_selected(self, item: QListWidgetItem):
        """Handle item selection"""
        item_data = item.data(Qt.UserRole)
        if item_data:
            self.item_selected.emit(item_data)
            self.accept()
    
    def closeEvent(self, event):
        """Clean up on close"""
        self.search_manager.close()
        super().closeEvent(event)


class SearchBarWidget(QWidget):
    """Compact search bar widget for main window"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Global Search (Ctrl+F)...")
        self.search_input.setMaximumWidth(300)
        self.search_input.returnPressed.connect(self._open_search_dialog)
        layout.addWidget(self.search_input)
        
        search_btn = QPushButton("🔍")
        search_btn.setMaximumWidth(30)
        search_btn.clicked.connect(self._open_search_dialog)
        layout.addWidget(search_btn)
    
    def _open_search_dialog(self):
        """Open global search dialog"""
        dialog = GlobalSearchWidget(self)
        dialog.item_selected.connect(self._on_search_result_selected)
        dialog.exec()
    
    def _on_search_result_selected(self, item_data: dict):
        """Handle search result selection"""
        # Navigate to appropriate page based on result type
        result_type = item_data.get('type', '')
        main_window = self.window()
        
        if not hasattr(main_window, 'load_'):
            return
        
        navigation_map = {
            'farm': 'load_farm_management',
            'shed': 'load_farm_management',
            'flock': 'load_farm_management',
            'party': 'load_parties',
            'sale': 'load_sales',
            'purchase': 'load_purchases',
            'expense': 'load_expenses',
            'production': 'load_production',
            'material': 'load_inventory',
            'feed': 'load_feed_management'
        }
        
        method_name = navigation_map.get(result_type)
        if method_name and hasattr(main_window, method_name):
            getattr(main_window, method_name)()

