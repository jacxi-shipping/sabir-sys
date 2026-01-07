"""
Dashboard widget with interactive charts - Redesigned for better UI/UX
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QGridLayout,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from datetime import datetime, timedelta

from egg_farm_system.modules.reports import ReportGenerator
from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.modules.inventory import InventoryManager
from egg_farm_system.ui.widgets.charts import TimeSeriesChart
from egg_farm_system.ui.widgets.forecasting import ForecastingWidget
import logging

logger = logging.getLogger(__name__)


class DashboardWidget(QWidget):
    """Dashboard displaying key metrics and charts."""
    
    def __init__(self, farm_id):
        super().__init__()
        self.farm_id = farm_id
        self.report_generator = ReportGenerator()
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        """Initialize UI with proper spacing and scrollable content"""
        # Main scroll area for the entire dashboard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container widget for scrollable content
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title with refresh button
        title_layout = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName('titleLabel')
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setMinimumWidth(120)
        refresh_btn.setMinimumHeight(40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                font-weight: 600;
                font-size: 11pt;
                letter-spacing: 0.2px;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        title_layout.addWidget(refresh_btn)
        layout.addLayout(title_layout)
        
        # Today's Metrics Cards - Premium layout
        today_group = QGroupBox("Today's Metrics")
        today_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14pt;
                padding-top: 20px;
                margin-top: 12px;
                letter-spacing: 0.3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        today_layout = QGridLayout()
        today_layout.setSpacing(15)
        today_layout.setContentsMargins(15, 25, 15, 15)
        
        # Farm-themed colors: Barn Red, Pasture Green, Golden Wheat, Rust Orange
        self.today_eggs_card = self.create_metric_card("Eggs Today", "0", "#8B4513")  # Barn Red
        self.today_feed_card = self.create_metric_card("Feed Used (kg)", "0", "#6B8E23")  # Pasture Green
        self.today_sales_card = self.create_metric_card("Sales (AFG)", "0", "#F4A460")  # Golden Wheat
        self.today_revenue_card = self.create_metric_card("Revenue (USD)", "0", "#CD853F")  # Rust Orange
        
        today_layout.addWidget(self.today_eggs_card, 0, 0)
        today_layout.addWidget(self.today_feed_card, 0, 1)
        today_layout.addWidget(self.today_sales_card, 0, 2)
        today_layout.addWidget(self.today_revenue_card, 0, 3)
        
        today_group.setLayout(today_layout)
        layout.addWidget(today_group)
        
        # Quick Actions - Premium styling
        actions_group = QGroupBox("Quick Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14pt;
                padding-top: 20px;
                margin-top: 12px;
                letter-spacing: 0.3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        actions_layout.setContentsMargins(15, 25, 15, 15)
        
        quick_actions = [
            ("📊 Record Production", self._navigate_to_production),
            ("💰 New Sale", self._navigate_to_sales),
            ("🛒 New Purchase", self._navigate_to_purchases),
            ("📈 View Reports", self._navigate_to_reports),
        ]
        
        for action_text, callback in quick_actions:
            btn = QPushButton(action_text)
            btn.setMinimumHeight(48)
            btn.setMinimumWidth(180)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 11pt;
                    font-weight: 600;
                    letter-spacing: 0.2px;
                }
            """)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Summary Metrics - Premium layout
        summary_group = QGroupBox("Last 30 Days Summary")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14pt;
                padding-top: 20px;
                margin-top: 12px;
                letter-spacing: 0.3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        summary_layout = QGridLayout()
        summary_layout.setSpacing(15)
        summary_layout.setContentsMargins(15, 25, 15, 15)

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

        # Charts Layout - Side by side with proper sizing
        charts_group = QGroupBox("Analytics & Forecasting")
        charts_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12pt;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)
        charts_layout.setContentsMargins(15, 25, 15, 15)
        
        # Production Chart
        self.production_chart = TimeSeriesChart(title="Daily Egg Production (Last 30 Days)")
        self.production_chart.set_labels(left_label="Total Eggs", bottom_label="Date")
        self.production_chart.setMinimumHeight(300)
        charts_layout.addWidget(self.production_chart, 1)
        
        # Forecasting Widget
        self.forecasting_widget = ForecastingWidget(self.farm_id)
        self.forecasting_widget.setMinimumHeight(300)
        charts_layout.addWidget(self.forecasting_widget, 1)
        
        charts_group.setLayout(charts_layout)
        layout.addWidget(charts_group)
        
        # Low Stock Alerts - Premium styling
        alerts_group = QGroupBox("Low Stock Alerts")
        alerts_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14pt;
                padding-top: 20px;
                margin-top: 12px;
                letter-spacing: 0.3px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        alerts_layout = QVBoxLayout()
        alerts_layout.setContentsMargins(15, 25, 15, 15)
        self.alerts_label = QLabel("No low stock alerts")
        self.alerts_label.setWordWrap(True)
        self.alerts_label.setMinimumHeight(60)
        self.alerts_label.setStyleSheet("""
            padding: 14px 16px;
            border-radius: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #F5DEB3,
                stop:1 #F8E8D5);
            border: none;
            color: #2C1810;
            font-weight: 500;
        """)
        alerts_layout.addWidget(self.alerts_label)
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)
        
        layout.addStretch()
        
        # Set container as scroll widget
        scroll.setWidget(container)
        
        # Main layout for this widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def create_metric_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a premium metric card widget with modern design"""
        card = QFrame()
        card.setFrameShape(QFrame.NoFrame)
        card.setFixedHeight(100)
        # Create gradient color
        darker_color = self._darken_color(color, 0.15)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color},
                    stop:1 {darker_color});
                border-radius: 12px;
                padding: 14px;
                border: none;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(14, 12, 14, 12)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.95);
            font-size: 10pt;
            font-weight: 600;
            letter-spacing: 0.2px;
        """)
        title_label.setWordWrap(False)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            color: white;
            font-size: 22pt;
            font-weight: 700;
            letter-spacing: -0.3px;
        """)
        value_label.setWordWrap(False)
        layout.addWidget(value_label)
        
        return card
    
    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken a hex color by a factor (0-1)"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f"#{r:02x}{g:02x}{b:02x}"
    
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
        """Helper to create a premium label for summary stats."""
        label = QLabel(text)
        font = QFont()
        font.setPointSize(13)
        font.setWeight(QFont.Weight.DemiBold)
        label.setFont(font)
        label.setStyleSheet("""
            padding: 14px 16px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #F5DEB3,
                stop:1 #F8E8D5);
            border-radius: 8px;
            border: none;
            color: #2C1810;
            font-weight: 600;
        """)
        label.setWordWrap(True)
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
                self.alerts_label.setStyleSheet("padding: 10px; border-radius: 4px; background-color: #fff3cd; color: #856404; font-weight: bold;")
            else:
                self.alerts_label.setText("✓ No low stock alerts")
                self.alerts_label.setStyleSheet("padding: 10px; border-radius: 4px; background-color: #d4edda; color: #155724;")
                
        except Exception as e:
            logger.error(f"Error updating low stock alerts: {e}")

    def set_farm_id(self, farm_id):
        """Update the farm ID and refresh the data."""
        self.farm_id = farm_id
        if hasattr(self, 'forecasting_widget'):
            self.forecasting_widget.set_farm_id(farm_id)
        self.refresh_data()
