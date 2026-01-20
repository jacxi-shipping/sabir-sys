"""
Low Stock Alerts Widget for Dashboard
"""
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import logging

from egg_farm_system.ui.widgets.dashboard_widget_base import DashboardWidgetBase
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import RawMaterial, FinishedFeed

logger = logging.getLogger(__name__)


class LowStockAlertsWidget(DashboardWidgetBase):
    """Show items with low stock"""
    
    def __init__(self, parent=None):
        super().__init__("Low Stock Alerts", "low_stock_alerts", parent)
        self.refresh()
    
    def refresh(self):
        """Fetch and display low stock items"""
        try:
            session = DatabaseManager.get_session()
            
            # Get raw materials with low stock
            low_materials = session.query(RawMaterial).filter(
                RawMaterial.current_stock <= RawMaterial.low_stock_alert
            ).all()
            
            # Get finished feed with low stock
            low_feed = session.query(FinishedFeed).filter(
                FinishedFeed.current_stock <= FinishedFeed.low_stock_alert
            ).all()
            
            session.close()
            
            if low_materials or low_feed:
                self.display_table(low_materials, low_feed)
            else:
                self.display_no_alerts()
                
        except Exception as e:
            logger.error(f"Error refreshing low stock alerts: {e}")
            self.display_error(str(e))
    
    def display_table(self, materials, feeds):
        """Display low stock items in table"""
        self.clear_content()
        
        try:
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(['Type', 'Item', 'Current Stock', 'Alert Level'])
            table.setRowCount(len(materials) + len(feeds))
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionMode(QTableWidget.SingleSelection)
            table.verticalHeader().setVisible(False)
            
            # Style
            table.setStyleSheet("""
                QTableWidget {
                    border: none;
                    gridline-color: #f0f0f0;
                }
                QHeaderView::section {
                    background-color: #f8f9fa;
                    padding: 8px;
                    border: none;
                    border-bottom: 2px solid #dee2e6;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QTableWidget::item {
                    padding: 8px;
                    font-size: 10pt;
                }
            """)
            
            row = 0
            
            # Add raw materials
            for material in materials:
                # Type
                type_item = QTableWidgetItem("Raw Material")
                table.setItem(row, 0, type_item)
                
                # Name
                name_item = QTableWidgetItem(material.name)
                table.setItem(row, 1, name_item)
                
                # Current stock
                stock_item = QTableWidgetItem(f"{material.current_stock:.1f} {material.unit}")
                stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if material.current_stock == 0:
                    stock_item.setBackground(QColor("#ffebee"))  # Light red
                    stock_item.setForeground(QColor("#c62828"))  # Dark red
                else:
                    stock_item.setBackground(QColor("#fff3e0"))  # Light orange
                table.setItem(row, 2, stock_item)
                
                # Alert level
                alert_item = QTableWidgetItem(f"{material.low_stock_alert:.1f} {material.unit}")
                alert_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 3, alert_item)
                
                row += 1
            
            # Add finished feed
            for feed in feeds:
                # Type
                type_item = QTableWidgetItem("Finished Feed")
                table.setItem(row, 0, type_item)
                
                # Name
                name_item = QTableWidgetItem(feed.feed_type.value)
                table.setItem(row, 1, name_item)
                
                # Current stock
                stock_item = QTableWidgetItem(f"{feed.current_stock:.1f} kg")
                stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if feed.current_stock == 0:
                    stock_item.setBackground(QColor("#ffebee"))
                    stock_item.setForeground(QColor("#c62828"))
                else:
                    stock_item.setBackground(QColor("#fff3e0"))
                table.setItem(row, 2, stock_item)
                
                # Alert level
                alert_item = QTableWidgetItem(f"{feed.low_stock_alert:.1f} kg")
                alert_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 3, alert_item)
                
                row += 1
            
            # Adjust column widths
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            
            self.content_layout.addWidget(table)
            
        except Exception as e:
            logger.error(f"Error creating table: {e}")
            self.display_error(str(e))
    
    def display_no_alerts(self):
        """Display 'no alerts' message"""
        from PySide6.QtWidgets import QLabel
        self.clear_content()
        no_alerts_label = QLabel("✅ All stock levels are healthy!")
        no_alerts_label.setAlignment(Qt.AlignCenter)
        no_alerts_label.setStyleSheet("color: #27ae60; font-size: 12pt; padding: 40px;")
        self.content_layout.addWidget(no_alerts_label)
