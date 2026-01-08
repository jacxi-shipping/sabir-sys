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
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 240);
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
        """)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # Set background
        self.setStyleSheet("""
            LoadingOverlay {
                background-color: rgba(0, 0, 0, 100);
            }
        """)
        
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

