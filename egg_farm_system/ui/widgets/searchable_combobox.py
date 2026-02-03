"""
Searchable/Filterable ComboBox widget.

Provides SearchableComboBox - a combobox where users can type to filter options.
This is essential for usability when there are many items (parties, materials, etc.).
"""
from PySide6.QtWidgets import QComboBox, QCompleter
from PySide6.QtCore import Qt, Signal


class SearchableComboBox(QComboBox):
    """ComboBox with search/filter functionality.
    
    Features:
    - Users can type to filter items in the dropdown
    - Auto-complete as you type
    - Case-insensitive matching
    - Works with existing QComboBox API
    
    Usage:
        combo = SearchableComboBox()
        combo.addItem("Item 1", data1)
        combo.addItem("Item 2", data2)
        # Users can now type to filter items
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Make it editable so users can type
        self.setEditable(True)
        
        # Set up completer for auto-complete
        self.completer = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.completer)
        
        # Filter popup to show only matching items
        self.setInsertPolicy(QComboBox.NoInsert)
        
        # Update completer model when items change
        self.model().rowsInserted.connect(self._update_completer)
        self.model().rowsRemoved.connect(self._update_completer)
        
        # Handle text changes to filter items
        self.lineEdit().textEdited.connect(self._on_text_changed)
        
        # When an item is selected, update the text
        self.activated.connect(self._on_item_selected)
        
        self._current_data = None
    
    def _update_completer(self):
        """Update completer with current items"""
        items = [self.itemText(i) for i in range(self.count())]
        self.completer.model().setStringList(items)
    
    def _on_text_changed(self, text):
        """Handle text change - filter items"""
        # Show popup with filtered items
        if text:
            self.completer.setCompletionPrefix(text)
            if self.completer.completionCount() > 0:
                self.completer.complete()
    
    def _on_item_selected(self, index):
        """Handle item selection"""
        if index >= 0:
            self._current_data = self.itemData(index)
    
    def currentData(self, role=Qt.UserRole):
        """Get data for current item - override to handle filtered state"""
        # If user typed text, find matching item
        current_text = self.currentText()
        for i in range(self.count()):
            if self.itemText(i) == current_text:
                return self.itemData(i, role)
        return None
    
    def setCurrentData(self, data):
        """Set current item by data"""
        for i in range(self.count()):
            if self.itemData(i) == data:
                self.setCurrentIndex(i)
                return
    
    def addItem(self, text, userData=None):
        """Add item - override to update completer"""
        super().addItem(text, userData)
        self._update_completer()
    
    def addItems(self, texts):
        """Add multiple items - override to update completer"""
        super().addItems(texts)
        self._update_completer()
    
    def clear(self):
        """Clear all items - override to update completer"""
        super().clear()
        self._update_completer()


class SearchableComboBoxWithAddNew(SearchableComboBox):
    """Searchable ComboBox with "Add New" functionality.
    
    Features:
    - All SearchableComboBox features
    - Special "➕ Add New..." item at the top
    - Emits addNewRequested signal when selected
    
    Usage:
        combo = SearchableComboBoxWithAddNew()
        combo.addNewRequested.connect(self.handle_add_new)
        combo.addItem("Item 1", data1)
    """
    
    addNewRequested = Signal()
    
    def __init__(self, parent=None, add_new_text="➕ Add New..."):
        super().__init__(parent)
        self.add_new_text = add_new_text
        self._add_new_item()
        
        # Connect to detect when "Add New" is selected
        self.activated.connect(self._check_add_new)
    
    def _add_new_item(self):
        """Add the 'Add New' item at the top"""
        super().insertItem(0, self.add_new_text, "__ADD_NEW__")
        # Make it visually distinct
        self.setItemData(0, Qt.lightGray, Qt.BackgroundRole)
    
    def _check_add_new(self, index):
        """Check if 'Add New' was selected"""
        if index == 0:
            self.addNewRequested.emit()
            # Reset to previous selection or empty
            self.setCurrentIndex(-1)
    
    def addItem(self, text, userData=None):
        """Add item - ensures 'Add New' stays at top"""
        super(SearchableComboBox, self).addItem(text, userData)
        self._update_completer()
    
    def clear(self):
        """Clear all items - but keep 'Add New'"""
        super(SearchableComboBox, self).clear()
        self._add_new_item()
        self._update_completer()
