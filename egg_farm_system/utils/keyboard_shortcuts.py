"""
Keyboard Shortcuts Manager for Egg Farm Management System
"""
import logging
from typing import Dict, Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

logger = logging.getLogger(__name__)


class ShortcutManager:
    """Manages keyboard shortcuts for the application"""
    
    # Standard shortcuts
    SHORTCUTS = {
        # File operations
        "new": ("Ctrl+N", "Create new item"),
        "save": ("Ctrl+S", "Save"),
        "delete": ("Delete", "Delete selected item"),
        "refresh": ("F5", "Refresh data"),
        
        # Navigation
        "dashboard": ("Ctrl+1", "Go to Dashboard"),
        "farm_management": ("Ctrl+2", "Go to Farm Management"),
        "production": ("Ctrl+3", "Go to Egg Production"),
        "feed": ("Ctrl+4", "Go to Feed Management"),
        "inventory": ("Ctrl+5", "Go to Inventory"),
        "parties": ("Ctrl+6", "Go to Parties"),
        "sales": ("Ctrl+7", "Go to Sales"),
        "purchases": ("Ctrl+8", "Go to Purchases"),
        "expenses": ("Ctrl+9", "Go to Expenses"),
        "reports": ("Ctrl+0", "Go to Reports"),
        
        # Common actions
        "search": ("Ctrl+F", "Search"),
        "close": ("Esc", "Close/Cancel"),
        "help": ("F1", "Show help"),
        "settings": ("Ctrl+,", "Open settings"),
        
        # Edit operations
        "copy": ("Ctrl+C", "Copy"),
        "paste": ("Ctrl+V", "Paste"),
        "cut": ("Ctrl+X", "Cut"),
        "undo": ("Ctrl+Z", "Undo"),
        "redo": ("Ctrl+Y", "Redo"),
        
        # Print/Export
        "print": ("Ctrl+P", "Print"),
        "export": ("Ctrl+E", "Export"),
        
        # Backup
        "backup": ("Ctrl+B", "Create backup"),
    }
    
    def __init__(self, parent_widget):
        """
        Initialize shortcut manager
        
        Args:
            parent_widget: Parent widget to attach shortcuts to
        """
        self.parent = parent_widget
        self.shortcuts: Dict[str, QShortcut] = {}
        self.actions: Dict[str, Callable] = {}
    
    def register_shortcut(self, key: str, callback: Callable, description: Optional[str] = None):
        """
        Register a keyboard shortcut
        
        Args:
            key: Shortcut key (e.g., "Ctrl+N")
            callback: Function to call when shortcut is triggered
            description: Optional description
        """
        try:
            shortcut = QShortcut(QKeySequence(key), self.parent)
            shortcut.activated.connect(callback)
            self.shortcuts[key] = shortcut
            self.actions[key] = callback
            logger.debug(f"Registered shortcut: {key}")
        except Exception as e:
            logger.error(f"Failed to register shortcut {key}: {e}")
    
    def register_standard_shortcut(self, name: str, callback: Callable):
        """
        Register a standard shortcut by name
        
        Args:
            name: Name of standard shortcut (from SHORTCUTS dict)
            callback: Function to call
        """
        if name in self.SHORTCUTS:
            key, description = self.SHORTCUTS[name]
            self.register_shortcut(key, callback, description)
        else:
            logger.warning(f"Unknown standard shortcut: {name}")
    
    def unregister_shortcut(self, key: str):
        """Unregister a shortcut"""
        if key in self.shortcuts:
            self.shortcuts[key].setEnabled(False)
            del self.shortcuts[key]
            if key in self.actions:
                del self.actions[key]
    
    def get_shortcut_help(self) -> Dict[str, str]:
        """
        Get help text for all registered shortcuts
        
        Returns:
            Dictionary mapping shortcut keys to descriptions
        """
        help_text = {}
        for name, (key, description) in self.SHORTCUTS.items():
            if key in self.shortcuts:
                help_text[key] = description
        return help_text
    
    def setup_default_shortcuts(self, callbacks: Dict[str, Callable]):
        """
        Setup default shortcuts with callbacks
        
        Args:
            callbacks: Dictionary mapping shortcut names to callback functions
        """
        for name, callback in callbacks.items():
            if name in self.SHORTCUTS:
                self.register_standard_shortcut(name, callback)
    
    def enable_shortcut(self, key: str, enabled: bool = True):
        """Enable or disable a shortcut"""
        if key in self.shortcuts:
            self.shortcuts[key].setEnabled(enabled)
    
    def disable_all(self):
        """Disable all shortcuts"""
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(False)
    
    def enable_all(self):
        """Enable all shortcuts"""
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(True)

