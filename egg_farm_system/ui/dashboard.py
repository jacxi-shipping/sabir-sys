"""
Dashboard widget with interactive charts.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QGridLayout
)
from PySide6.QtGui import QFont

from modules.reports import ReportGenerator
from ui.widgets.charts import TimeSeriesChart
import logging

logger = logging.getLogger(__name__)

class DashboardWidget(QWidget):
    """Dashboard displaying key metrics and charts."""
    
    def __init__(self, farm_id):
        super().__init__()
        self.farm_id = farm_id
        self.report_generator = ReportGenerator()
        
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Dashboard")
        title.setObjectName('titleLabel')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Summary Metrics
        summary_group = QGroupBox("Last 30 Days Summary")
        summary_layout = QHBoxLayout()

        self.total_eggs_label = self.create_summary_label("Total Production: 0")
        self.avg_eggs_label = self.create_summary_label("Daily Average: 0")

        summary_layout.addWidget(self.total_eggs_label)
        summary_layout.addWidget(self.avg_eggs_label)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Production Chart
        self.production_chart = TimeSeriesChart(title="Daily Egg Production (Last 30 Days)")
        self.production_chart.set_labels(left_label="Total Eggs", bottom_label="Date")
        layout.addWidget(self.production_chart)
        
        self.setLayout(layout)

    def create_summary_label(self, text):
        """Helper to create a consistent label for summary stats."""
        label = QLabel(text)
        font = QFont()
        font.setPointSize(14)
        label.setFont(font)
        return label

    def refresh_data(self):
        """Refresh all dashboard data."""
        logger.info(f"Refreshing dashboard for farm_id: {self.farm_id}")
        if not self.farm_id:
            logger.warning("No farm_id set, cannot refresh dashboard.")
            return
        
        try:
            # Get data for the chart
            data = self.report_generator.get_daily_production_summary(self.farm_id, days=30)
            
            dates = data.get('dates', [])
            egg_counts = data.get('egg_counts', [])

            if dates and egg_counts:
                # Update the chart
                self.production_chart.plot(dates, egg_counts, pen='b', name="Total Eggs")
                
                # Update summary labels
                total_production = sum(egg_counts)
                average_production = total_production / len(egg_counts) if egg_counts else 0
                
                self.total_eggs_label.setText(f"Total Production: {total_production:,}")
                self.avg_eggs_label.setText(f"Daily Average: {average_production:,.1f}")
            else:
                # Handle case with no data
                self.production_chart.plot([], [], pen='b', name="Total Eggs")
                self.total_eggs_label.setText("Total Production: 0")
                self.avg_eggs_label.setText("Daily Average: 0")

        except Exception as e:
            logger.exception(f"Error refreshing dashboard data: {e}")

    def set_farm_id(self, farm_id):
        """Update the farm ID and refresh the data."""
        self.farm_id = farm_id
        self.refresh_data()
