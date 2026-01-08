"""
Keyboard shortcuts manager for the application
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut


class KeyboardShortcuts:
    """Manages keyboard shortcuts for the application"""
    
    # Standard shortcuts
    NEW = QKeySequence(Qt.CTRL | Qt.Key_N)
    SAVE = QKeySequence(Qt.CTRL | Qt.Key_S)
    EDIT = QKeySequence(Qt.CTRL | Qt.Key_E)
    DELETE = QKeySequence(Qt.Key_Delete)
    REFRESH = QKeySequence(Qt.CTRL | Qt.Key_R)
    SEARCH = QKeySequence(Qt.CTRL | Qt.Key_F)
    CLOSE = QKeySequence(Qt.CTRL | Qt.Key_W)
    ESCAPE = QKeySequence(Qt.Key_Escape)
    
    @staticmethod
    def create_shortcut(widget, sequence, callback, context=Qt.WidgetShortcut):
        """Create a keyboard shortcut for a widget"""
        shortcut = QShortcut(sequence, widget)
        shortcut.setContext(context)
        shortcut.activated.connect(callback)
        return shortcut
    
    @staticmethod
    def add_standard_shortcuts(widget, shortcuts_dict):
        """
        Add standard shortcuts to a widget
        
        Args:
            widget: The widget to add shortcuts to
            shortcuts_dict: Dictionary mapping action names to callbacks
                e.g., {'new': lambda: self.add_item(), 'save': lambda: self.save()}
        """
        shortcuts = []
        
        if 'new' in shortcuts_dict:
            shortcuts.append(KeyboardShortcuts.create_shortcut(
                widget, KeyboardShortcuts.NEW, shortcuts_dict['new']
            ))
        
        if 'save' in shortcuts_dict:
            shortcuts.append(KeyboardShortcuts.create_shortcut(
                widget, KeyboardShortcuts.SAVE, shortcuts_dict['save']
            ))
        
        if 'edit' in shortcuts_dict:
            shortcuts.append(KeyboardShortcuts.create_shortcut(
                widget, KeyboardShortcuts.EDIT, shortcuts_dict['edit']
            ))
        
        if 'delete' in shortcuts_dict:
            shortcuts.append(KeyboardShortcuts.create_shortcut(
                widget, KeyboardShortcuts.DELETE, shortcuts_dict['delete']
            ))
        
        if 'refresh' in shortcuts_dict:
            shortcuts.append(KeyboardShortcuts.create_shortcut(
                widget, KeyboardShortcuts.REFRESH, shortcuts_dict['refresh']
            ))
        
        if 'search' in shortcuts_dict:
            shortcuts.append(KeyboardShortcuts.create_shortcut(
                widget, KeyboardShortcuts.SEARCH, shortcuts_dict['search']
            ))
        
        if 'close' in shortcuts_dict:
            shortcuts.append(KeyboardShortcuts.create_shortcut(
                widget, KeyboardShortcuts.CLOSE, shortcuts_dict['close']
            ))
        
        return shortcuts

