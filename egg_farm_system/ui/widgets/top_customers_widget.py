"""
Top Customers Widget for Dashboard
"""
from datetime import datetime, timedelta
import logging

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PySide6.QtCore import Qt
from sqlalchemy import func

from egg_farm_system.ui.widgets.dashboard_widget_base import DashboardWidgetBase
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Party, Sale

logger = logging.getLogger(__name__)


class TopCustomersWidget(DashboardWidgetBase):
    """Show top 5 customers by revenue"""
    
    def __init__(self, parent=None):
        self.period = 'month'  # month, week, year
        self.limit = 5
        super().__init__("Top 5 Customers (This Month)", "top_customers", parent)
        self.refresh()
    
    def refresh(self):
        """Fetch and display top customers"""
        try:
            session = DatabaseManager.get_session()
            
            # Calculate start date based on period
            now = datetime.now()
            if self.period == 'month':
                start_date = now.replace(day=1)
                self.title_label.setText("Top 5 Customers (This Month)")
            elif self.period == 'week':
                start_date = now - timedelta(days=now.weekday())
                self.title_label.setText("Top 5 Customers (This Week)")
            elif self.period == 'year':
                start_date = now.replace(month=1, day=1)
                self.title_label.setText("Top 5 Customers (This Year)")
            else:
                start_date = now.replace(day=1)
            
            # Query top customers
            top_customers = session.query(
                Party.name,
                func.sum(Sale.total_afg).label('revenue_afg'),
                func.sum(Sale.total_usd).label('revenue_usd'),
                func.count(Sale.id).label('transaction_count')
            ).join(Sale).filter(
                Sale.date >= start_date
            ).group_by(Party.id).order_by(
                func.sum(Sale.total_afg).desc()
            ).limit(self.limit).all()
            
            session.close()
            
            if top_customers:
                self.display_table(top_customers)
            else:
                self.display_no_data()
                
        except Exception as e:
            logger.error(f"Error refreshing top customers: {e}")
            self.display_error(str(e))
    
    def display_table(self, customers):
        """Display customers in table"""
        self.clear_content()
        
        try:
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(['Rank', 'Customer', 'Revenue (AFG)', 'Transactions'])
            table.setRowCount(len(customers))
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionMode(QTableWidget.NoSelection)
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
            
            # Populate table
            for row, (name, revenue_afg, revenue_usd, count) in enumerate(customers):
                # Rank
                rank_item = QTableWidgetItem(f"#{row + 1}")
                rank_item.setTextAlignment(Qt.AlignCenter)
                if row == 0:
                    rank_item.setBackground(Qt.GlobalColor.yellow)
                table.setItem(row, 0, rank_item)
                
                # Customer name
                name_item = QTableWidgetItem(name)
                table.setItem(row, 1, name_item)
                
                # Revenue
                revenue_item = QTableWidgetItem(f"{revenue_afg:,.0f}")
                revenue_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 2, revenue_item)
                
                # Transaction count
                count_item = QTableWidgetItem(str(count))
                count_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 3, count_item)
            
            # Adjust column widths
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            
            self.content_layout.addWidget(table)
            
        except Exception as e:
            logger.error(f"Error creating table: {e}")
            self.display_error(str(e))
    
    def show_settings(self):
        """Show settings for this widget"""
        # Could add dialog to change period (week/month/year) and limit
        logger.info("Top customers widget settings")
