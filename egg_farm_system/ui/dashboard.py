"""
Dashboard widget with interactive charts.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QGridLayout,
    QPushButton, QFrame, QScrollArea
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt
from datetime import datetime, timedelta

from egg_farm_system.modules.reports import ReportGenerator
from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.modules.inventory import InventoryManager
from egg_farm_system.ui.widgets.charts import TimeSeriesChart
from egg_farm_system.ui.widgets.forecasting import ForecastingWidget
import logging
from PySide6.QtWidgets import QSizePolicy

logger = logging.getLogger(__name__)

class DashboardWidget(QWidget):
    """Dashboard displaying key metrics and charts."""
    
    def __init__(self, farm_id):
        super().__init__()
        self.farm_id = farm_id
        self.report_generator = ReportGenerator()
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Ensure it expands
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title with refresh button
        title_layout = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName('titleLabel')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        title_layout.addWidget(refresh_btn)
        layout.addLayout(title_layout)
        
        # Today's Metrics Cards
        today_group = QGroupBox("Today's Metrics")
        today_layout = QGridLayout()
        
        self.today_eggs_card = self.create_metric_card("Eggs Today", "0", "#3498db")
        self.today_feed_card = self.create_metric_card("Feed Used (kg)", "0", "#27ae60")
        self.today_sales_card = self.create_metric_card("Sales (AFG)", "0", "#f39c12")
        self.today_revenue_card = self.create_metric_card("Revenue (USD)", "0", "#9b59b6")
        
        today_layout.addWidget(self.today_eggs_card, 0, 0)
        today_layout.addWidget(self.today_feed_card, 0, 1)
        today_layout.addWidget(self.today_sales_card, 0, 2)
        today_layout.addWidget(self.today_revenue_card, 0, 3)
        
        today_group.setLayout(today_layout)
        layout.addWidget(today_group)
        
        # Quick Actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout()
        
        quick_actions = [
            ("Record Production", self._navigate_to_production),
            ("New Sale", self._navigate_to_sales),
            ("New Purchase", self._navigate_to_purchases),
            ("View Reports", self._navigate_to_reports),
        ]
        
        for action_text, callback in quick_actions:
            btn = QPushButton(action_text)
            btn.setMinimumHeight(35)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Summary Metrics
        summary_group = QGroupBox("Last 30 Days Summary")
        summary_layout = QGridLayout()

        self.total_eggs_label = self.create_summary_label("Total Production: 0")
        self.avg_eggs_label = self.create_summary_label("Daily Average: 0")
        self.total_sales_label = self.create_summary_label("Total Sales: 0 AFG")
        self.avg_daily_sales_label = self.create_summary_label("Avg Daily Sales: 0 AFG")

        summary_layout.addWidget(self.total_eggs_label, 0, 0)
        summary_layout.addWidget(self.avg_eggs_label, 0, 1)
        summary_layout.addWidget(self.total_sales_label, 0, 2)
        summary_layout.addWidget(self.avg_daily_sales_label, 0, 3)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Charts Layout
        charts_layout = QHBoxLayout()
        
        # Production Chart
        self.production_chart = TimeSeriesChart(title="Daily Egg Production (Last 30 Days)")
        self.production_chart.set_labels(left_label="Total Eggs", bottom_label="Date")
        charts_layout.addWidget(self.production_chart)
        
        # Forecasting Widget
        self.forecasting_widget = ForecastingWidget(self.farm_id)
        charts_layout.addWidget(self.forecasting_widget)
        
        layout.addLayout(charts_layout)
        
        # Low Stock Alerts
        alerts_group = QGroupBox("Low Stock Alerts")
        alerts_layout = QVBoxLayout()
        self.alerts_label = QLabel("No low stock alerts")
        self.alerts_label.setWordWrap(True)
        alerts_layout.addWidget(self.alerts_label)
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def create_metric_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a metric card widget"""
        card = QFrame()
        card.setFrameShape(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
                min-height: 80px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 11pt; font-weight: bold;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 18pt; font-weight: bold;")
        layout.addWidget(value_label)
        
        layout.addStretch()
        return card
    
    def _navigate_to_production(self):
        """Navigate to production page"""
        if hasattr(self, 'parent') and hasattr(self.parent(), 'load_production'):
            self.parent().load_production()
    
    def _navigate_to_sales(self):
        """Navigate to sales page"""
        if hasattr(self, 'parent') and hasattr(self.parent(), 'load_sales'):
            self.parent().load_sales()
    
    def _navigate_to_purchases(self):
        """Navigate to purchases page"""
        if hasattr(self, 'parent') and hasattr(self.parent(), 'load_purchases'):
            self.parent().load_purchases()
    
    def _navigate_to_reports(self):
        """Navigate to reports page"""
        if hasattr(self, 'parent') and hasattr(self.parent(), 'load_reports'):
            self.parent().load_reports()

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
            
        # Refresh forecast
        if hasattr(self, 'forecasting_widget'):
            self.forecasting_widget.load_data()
        
        try:
            # Get today's date
            today = datetime.now().date()
            
            # Today's metrics
            self._update_today_metrics(today)
            
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
            
            # Update sales summary
            self._update_sales_summary()
            
            # Update low stock alerts
            self._update_low_stock_alerts()
            
        except Exception as e:
            logger.exception(f"Error refreshing dashboard data: {e}")
    
    def _update_today_metrics(self, today):
        """Update today's metrics"""
        try:
            # Today's eggs
            from egg_farm_system.database.models import EggProduction, Shed
            from egg_farm_system.database.db import DatabaseManager
            session = DatabaseManager.get_session()
            
            sheds = session.query(Shed).filter(Shed.farm_id == self.farm_id).all()
            shed_ids = [s.id for s in sheds]
            
            today_eggs = 0
            if shed_ids:
                productions = session.query(EggProduction).filter(
                    EggProduction.shed_id.in_(shed_ids),
                    EggProduction.date >= datetime.combine(today, datetime.min.time()),
                    EggProduction.date < datetime.combine(today + timedelta(days=1), datetime.min.time())
                ).all()
                
                for prod in productions:
                    today_eggs += prod.small_count + prod.medium_count + prod.large_count + prod.broken_count
            
            # Update eggs card - find the value label (second QLabel)
            labels = self.today_eggs_card.findChildren(QLabel)
            if len(labels) > 1:
                labels[1].setText(f"{today_eggs:,}")
            
            # Today's feed
            from egg_farm_system.database.models import FeedIssue
            today_feed = 0
            feed_issues = session.query(FeedIssue).filter(
                FeedIssue.shed_id.in_(shed_ids),
                FeedIssue.date >= datetime.combine(today, datetime.min.time()),
                FeedIssue.date < datetime.combine(today + timedelta(days=1), datetime.min.time())
            ).all()
            
            for issue in feed_issues:
                today_feed += issue.quantity_kg
            
            # Update feed card
            feed_labels = self.today_feed_card.findChildren(QLabel)
            if len(feed_labels) > 1:
                feed_labels[1].setText(f"{today_feed:.1f}")
            
            # Today's sales (sales are not farm-specific, so get all)
            sales_manager = SalesManager()
            today_sales = sales_manager.get_sales_summary(None, today, today)
            
            # Update sales cards
            sales_labels = self.today_sales_card.findChildren(QLabel)
            if len(sales_labels) > 1:
                sales_labels[1].setText(f"{today_sales.get('total_afg', 0):,.0f}")
            
            revenue_labels = self.today_revenue_card.findChildren(QLabel)
            if len(revenue_labels) > 1:
                revenue_labels[1].setText(f"{today_sales.get('total_usd', 0):,.2f}")
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error updating today's metrics: {e}")
    
    def _update_sales_summary(self):
        """Update sales summary for last 30 days"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            sales_manager = SalesManager()
            summary = sales_manager.get_sales_summary(None, start_date, end_date)
            
            total_sales = summary.get('total_afg', 0)
            avg_daily = total_sales / 30 if total_sales > 0 else 0
            
            self.total_sales_label.setText(f"Total Sales: {total_sales:,.0f} AFG")
            self.avg_daily_sales_label.setText(f"Avg Daily Sales: {avg_daily:,.0f} AFG")
            
        except Exception as e:
            logger.error(f"Error updating sales summary: {e}")
    
    def _update_low_stock_alerts(self):
        """Update low stock alerts"""
        try:
            inventory_manager = InventoryManager()
            alerts = inventory_manager.get_low_stock_alerts()
            
            if alerts:
                alert_text = "⚠️ Low Stock Items:\n"
                for alert in alerts[:5]:  # Show max 5
                    alert_text += f"• {alert['name']} ({alert['type']}): {alert['stock']} {alert['unit']}\n"
                if len(alerts) > 5:
                    alert_text += f"... and {len(alerts) - 5} more"
                self.alerts_label.setText(alert_text)
                self.alerts_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                self.alerts_label.setText("✓ No low stock alerts")
                self.alerts_label.setStyleSheet("color: #27ae60;")
                
        except Exception as e:
            logger.error(f"Error updating low stock alerts: {e}")

    def set_farm_id(self, farm_id):
        """Update the farm ID and refresh the data."""
        self.farm_id = farm_id
        if hasattr(self, 'forecasting_widget'):
            self.forecasting_widget.set_farm_id(farm_id)
        self.refresh_data()
