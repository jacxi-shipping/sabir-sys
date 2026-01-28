"""
Success message widget for showing operation success feedback
"""
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton
from egg_farm_system.ui.ui_helpers import create_button
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QPainter


class SuccessMessage(QWidget):
    """Temporary success message that auto-dismisses"""
    
    def __init__(self, parent=None, message="Operation completed successfully"):
        super().__init__(parent)
        self.message = message
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        self.label = QLabel(message)
        self.label.setProperty('class', 'success-message')
        layout.addWidget(self.label)
        close_btn = create_button("×", style='ghost')
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        self.adjustSize()
        
        # Auto-hide after 3 seconds
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
    
    def show(self):
        """Show message and start auto-hide timer"""
        super().show()
        self.timer.start(3000)
    
    def show_message(self, message, duration=3000):
        """Show message with custom duration"""
        self.message = message
        self.label.setText(message)
        self.adjustSize()
        self.show()
        self.timer.start(duration)

