"""
Success message widget for showing operation success feedback
"""
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton
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
        self.label.setStyleSheet("""
            QLabel {
                color: #155724;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.label)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #155724;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 10px;
            }
        """)
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

