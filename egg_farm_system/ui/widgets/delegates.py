"""
Custom Item Delegates for improved UI rendering
"""
from PySide6.QtWidgets import QStyledItemDelegate, QStyle
from PySide6.QtCore import Qt, QRect, QRectF
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QPainterPath

class StatusDelegate(QStyledItemDelegate):
    """
    Renders status text as a colored 'chip' or 'badge'.
    
    Mappings map text (lowercase) to (background_color, text_color).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.default_color = ("#E0E0E0", "#333333") # Grey
        
        # Define color mappings (Background, Text)
        self.colors = {
            # General Positive
            "active": ("#E8F5E9", "#2E7D32"),      # Green
            "completed": ("#E8F5E9", "#2E7D32"),
            "paid": ("#E8F5E9", "#2E7D32"),
            "working": ("#E8F5E9", "#2E7D32"),
            "available": ("#E8F5E9", "#2E7D32"),
            
            # General Negative/Danger
            "inactive": ("#FFEBEE", "#C62828"),    # Red
            "broken": ("#FFEBEE", "#C62828"),
            "expired": ("#FFEBEE", "#C62828"),
            "deleted": ("#FFEBEE", "#C62828"),
            
            # Warning/Pending
            "pending": ("#FFF3E0", "#EF6C00"),     # Orange
            "maintenance": ("#FFF3E0", "#EF6C00"),
            "repair": ("#FFF3E0", "#EF6C00"),
            "low stock": ("#FFF3E0", "#EF6C00"),
            
            # Info/Neutral
            "draft": ("#E3F2FD", "#1565C0"),       # Blue
            "new": ("#E3F2FD", "#1565C0"),
        }

    def paint(self, painter, option, index):
        """Paint the status chip"""
        # Save painter state
        painter.save()
        
        # Setup antialiasing
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get data
        text = index.data(Qt.DisplayRole)
        if not text:
            painter.restore()
            super().paint(painter, option, index)
            return
            
        status_key = str(text).lower().strip()
        
        # Determine colors
        bg_hex, text_hex = self.colors.get(status_key, self.default_color)
        
        # Handle selection state (keep system highlight or override?)
        # Usually for chips, we keep the chip color even if row is selected, 
        # but maybe darken the background slightly? 
        # Let's just draw the chip over the selection background (which QTableWidget draws first).
        
        # Define chip rect (centered with padding)
        rect = option.rect
        chip_height = rect.height() - 14
        chip_width = min(rect.width() - 10, len(text) * 8 + 20) # Approximate width
        if chip_width < 60: chip_width = 60
        
        # Center the chip
        x = rect.x() + (rect.width() - chip_width) / 2
        y = rect.y() + (rect.height() - chip_height) / 2
        
        chip_rect = QRectF(x, y, chip_width, chip_height)
        
        # Draw Background
        path = QPainterPath()
        path.addRoundedRect(chip_rect, 6, 6) # 6px radius
        
        painter.fillPath(path, QColor(bg_hex))
        
        # Draw Text
        painter.setPen(QColor(text_hex))
        painter.setFont(option.font)
        painter.drawText(chip_rect, Qt.AlignCenter, text)
        
        painter.restore()
        
    def sizeHint(self, option, index):
        """Adjust size hint if needed"""
        return super().sizeHint(option, index)
