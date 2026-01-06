"""
Enhanced Form Widget with auto-save, validation, and smart defaults
"""
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QLabel, QPushButton, QMessageBox,
    QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox, QTextEdit, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor

from egg_farm_system.modules.settings import SettingsManager

logger = logging.getLogger(__name__)


class EnhancedFormWidget(QWidget):
    """Enhanced form widget with auto-save, validation, and smart defaults"""
    
    # Signals
    form_validated = Signal(bool)  # Emitted when validation state changes
    form_saved = Signal()  # Emitted when form is saved
    
    def __init__(self, parent=None, form_id: str = "default"):
        super().__init__(parent)
        self.form_id = form_id
        self.form_layout = QFormLayout()
        self.fields: Dict[str, Any] = {}
        self.validators: Dict[str, Callable] = {}
        self.required_fields: set = set()
        self.error_labels: Dict[str, QLabel] = {}
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_enabled = True
        
        self.setLayout(self.form_layout)
    
    def add_field(self, name: str, label: str, widget: QWidget, required: bool = False,
                  validator: Optional[Callable] = None, help_text: str = "", 
                  default_value: Any = None):
        """
        Add a field to the form
        
        Args:
            name: Field name (internal identifier)
            label: Field label (display text)
            widget: Input widget
            required: Whether field is required
            validator: Optional validation function
            help_text: Help text to show as tooltip
            default_value: Default value for the field
        """
        self.fields[name] = widget
        
        # Add required indicator
        if required:
            label = f"{label} *"
            self.required_fields.add(name)
        
        # Set help text as tooltip
        if help_text:
            widget.setToolTip(help_text)
        
        # Add validator
        if validator:
            self.validators[name] = validator
        
        # Add to layout
        self.form_layout.addRow(label, widget)
        
        # Add error label (initially hidden)
        error_label = QLabel()
        error_label.setStyleSheet("color: red; font-size: 9pt;")
        error_label.setVisible(False)
        error_label.setWordWrap(True)
        self.error_labels[name] = error_label
        self.form_layout.addRow("", error_label)
        
        # Set default value
        if default_value is not None:
            self._set_widget_value(widget, default_value)
        
        # Connect change signals for auto-save and validation
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(lambda: self._on_field_changed(name))
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(lambda: self._on_field_changed(name))
        elif isinstance(widget, (QDateEdit, QDoubleSpinBox, QSpinBox)):
            widget.valueChanged.connect(lambda: self._on_field_changed(name))
        elif isinstance(widget, QTextEdit):
            widget.textChanged.connect(lambda: self._on_field_changed(name))
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(lambda: self._on_field_changed(name))
        
        # Load saved draft
        self._load_draft(name, widget)
    
    def _set_widget_value(self, widget: QWidget, value: Any):
        """Set value to widget based on type"""
        if isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, QComboBox):
            index = widget.findText(str(value))
            if index >= 0:
                widget.setCurrentIndex(index)
        elif isinstance(widget, QDateEdit):
            if isinstance(value, str):
                from PySide6.QtCore import QDate
                widget.setDate(QDate.fromString(value, Qt.ISODate))
        elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            widget.setValue(float(value))
        elif isinstance(widget, QTextEdit):
            widget.setPlainText(str(value))
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
    
    def _get_widget_value(self, widget: QWidget) -> Any:
        """Get value from widget based on type"""
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, QDateEdit):
            return widget.date().toString(Qt.ISODate)
        elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            return widget.value()
        elif isinstance(widget, QTextEdit):
            return widget.toPlainText()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        return None
    
    def _on_field_changed(self, field_name: str):
        """Handle field change"""
        # Validate field
        self._validate_field(field_name)
        
        # Trigger auto-save
        if self.auto_save_enabled:
            self.auto_save_timer.stop()
            self.auto_save_timer.start(2000)  # Auto-save after 2 seconds of inactivity
    
    def _validate_field(self, field_name: str) -> bool:
        """Validate a single field"""
        if field_name not in self.fields:
            return True
        
        widget = self.fields[field_name]
        value = self._get_widget_value(widget)
        error_label = self.error_labels[field_name]
        
        # Check required
        if field_name in self.required_fields:
            if not value or (isinstance(value, str) and not value.strip()):
                error_label.setText("This field is required")
                error_label.setVisible(True)
                return False
        
        # Run custom validator
        if field_name in self.validators:
            try:
                result = self.validators[field_name](value)
                if isinstance(result, tuple):
                    is_valid, error_msg = result
                    if not is_valid:
                        error_label.setText(error_msg)
                        error_label.setVisible(True)
                        return False
                elif not result:
                    error_label.setText("Invalid value")
                    error_label.setVisible(True)
                    return False
            except Exception as e:
                logger.error(f"Validator error for {field_name}: {e}")
                error_label.setText(f"Validation error: {str(e)}")
                error_label.setVisible(True)
                return False
        
        # Clear error
        error_label.setVisible(False)
        return True
    
    def validate_all(self) -> bool:
        """Validate all fields"""
        is_valid = True
        for field_name in self.fields:
            if not self._validate_field(field_name):
                is_valid = False
        
        self.form_validated.emit(is_valid)
        return is_valid
    
    def get_field_value(self, field_name: str) -> Any:
        """Get value of a field"""
        if field_name in self.fields:
            return self._get_widget_value(self.fields[field_name])
        return None
    
    def set_field_value(self, field_name: str, value: Any):
        """Set value of a field"""
        if field_name in self.fields:
            self._set_widget_value(self.fields[field_name], value)
    
    def get_all_values(self) -> Dict[str, Any]:
        """Get all field values as dictionary"""
        return {name: self._get_widget_value(widget) for name, widget in self.fields.items()}
    
    def set_all_values(self, values: Dict[str, Any]):
        """Set all field values from dictionary"""
        for name, value in values.items():
            if name in self.fields:
                self._set_widget_value(self.fields[name], value)
    
    def _auto_save(self):
        """Auto-save form data as draft"""
        try:
            values = self.get_all_values()
            draft_key = f"form_draft_{self.form_id}"
            import json
            SettingsManager.set_setting(draft_key, json.dumps(values))
            logger.debug(f"Auto-saved draft for form {self.form_id}")
        except Exception as e:
            logger.error(f"Error auto-saving draft: {e}")
    
    def _load_draft(self, field_name: str, widget: QWidget):
        """Load saved draft for a field"""
        try:
            draft_key = f"form_draft_{self.form_id}"
            draft_json = SettingsManager.get_setting(draft_key)
            if draft_json:
                import json
                values = json.loads(draft_json)
                if field_name in values:
                    self._set_widget_value(widget, values[field_name])
        except Exception as e:
            logger.debug(f"No draft found or error loading draft: {e}")
    
    def clear_draft(self):
        """Clear saved draft"""
        try:
            draft_key = f"form_draft_{self.form_id}"
            SettingsManager.set_setting(draft_key, "")
        except Exception as e:
            logger.error(f"Error clearing draft: {e}")
    
    def save(self) -> bool:
        """Save form (validate and clear draft)"""
        if not self.validate_all():
            QMessageBox.warning(self, "Validation Error", 
                              "Please fix the errors before saving.")
            return False
        
        self.clear_draft()
        self.form_saved.emit()
        return True
    
    def reset(self):
        """Reset form to defaults"""
        for name, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QDateEdit):
                from PySide6.QtCore import QDate
                widget.setDate(QDate.currentDate())
            elif isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                widget.setValue(0)
            elif isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)
            
            # Clear errors
            if name in self.error_labels:
                self.error_labels[name].setVisible(False)
        
        self.clear_draft()

