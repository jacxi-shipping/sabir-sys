"""
Progress dialog for long-running operations
"""
from PySide6.QtWidgets import QProgressDialog
from PySide6.QtCore import Qt, QTimer


class ProgressDialog(QProgressDialog):
    """Progress dialog for long-running operations"""
    
    def __init__(self, parent=None, label_text="Processing...", minimum=0, maximum=100):
        super().__init__(parent)
        self.setWindowTitle("Progress")
        self.setLabelText(label_text)
        self.setMinimum(minimum)
        self.setMaximum(maximum)
        self.setWindowModality(Qt.WindowModal)
        self.setAutoClose(True)
        self.setAutoReset(True)
        self.setCancelButton(None)  # No cancel button by default
    
    def set_cancellable(self, cancellable=True, on_cancel=None):
        """Set whether the dialog can be cancelled"""
        if cancellable:
            self.setCancelButtonText("Cancel")
            if on_cancel:
                self.canceled.connect(on_cancel)
        else:
            self.setCancelButton(None)
    
    def update_progress(self, value, text=None):
        """Update progress value and optionally text"""
        self.setValue(value)
        if text:
            self.setLabelText(text)
        QTimer.singleShot(0, lambda: None)  # Process events
    
    def finish(self, message="Completed"):
        """Finish the progress dialog"""
        self.setLabelText(message)
        self.setValue(self.maximum())
        QTimer.singleShot(500, self.close)

