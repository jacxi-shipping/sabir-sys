"""
Loading overlay widget for showing progress during operations
"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor


class LoadingOverlay(QWidget):
    """Overlay widget that shows a loading indicator"""
    
    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        self.message = message
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_NoSystemBackground, False)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Loading label
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setProperty('class', 'loading-label')
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # Set background
        self.setProperty('class', 'loading-overlay')
        
        self.hide()
    
    def showEvent(self, event):
        """Resize to parent when shown"""
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().showEvent(event)
    
    def paintEvent(self, event):
        """Paint semi-transparent background"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        super().paintEvent(event)
    
    def set_message(self, message):
        """Update loading message"""
        self.message = message
        self.label.setText(message)

