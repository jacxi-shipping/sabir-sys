"""
Dashboard widget with interactive charts - Redesigned for better UI/UX
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QGridLayout,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QSize
from datetime import datetime, timedelta
from pathlib import Path

from egg_farm_system.modules.reports import ReportGenerator
from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.modules.inventory import InventoryManager
from egg_farm_system.ui.widgets.charts import TimeSeriesChart
from egg_farm_system.ui.widgets.forecasting import ForecastingWidget
from egg_farm_system.utils.advanced_caching import dashboard_cache, CacheInvalidationManager
from egg_farm_system.utils.performance_monitoring import measure_time
from egg_farm_system.utils.i18n import tr, get_i18n
from egg_farm_system.ui.animation_helper import AnimationHelper
from egg_farm_system.config import get_asset_path
from egg_farm_system.utils.audit_trail import get_audit_trail
import logging

logger = logging.getLogger(__name__)


class DashboardWidget(QWidget):
    """Dashboard displaying key metrics and charts."""
    
    def __init__(self, farm_id):
        super().__init__()
        self.farm_id = farm_id
        self.report_generator = ReportGenerator()
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Connect to language change signal
        get_i18n().language_changed.connect(self._update_texts)
        
        self.init_ui()
        self.refresh_data()
        
    def _update_texts(self, lang_code):
        """Update UI texts when language changes"""
        # Refresh dynamic data to update format strings
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
        title = QLabel(tr("Dashboard"))
        title.setProperty("i18n_key", "Dashboard")
        title.setObjectName('titleLabel')
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        refresh_btn = QPushButton(f" {tr('Refresh')}")
        refresh_btn.setIcon(QIcon(get_asset_path("icon_view.svg"))) # Fallback icon
        refresh_btn.setMinimumWidth(120)
        refresh_btn.setMinimumHeight(40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                font-weight: 600;
                font-size: 11pt;
                letter-spacing: 0.2px;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        title_layout.addWidget(refresh_btn)
        layout.addLayout(title_layout)
        
        # Today's Metrics Cards - Premium layout
        today_group = QGroupBox(tr("Today's Overview"))
        today_group.setProperty("i18n_key", "Today's Overview")
        today_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14pt;
                padding-top: 25px;
                margin-top: 15px;
                border: none;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 5px;
                color: #2c3e50;
            }
        """)
        today_layout = QGridLayout()
        today_layout.setSpacing(20)
        today_layout.setContentsMargins(0, 10, 0, 10)
        
        # Farm-themed colors: Barn Red, Pasture Green, Golden Wheat, Rust Orange
        self.today_eggs_card = self.create_metric_card("Eggs Today", "0", "#8B4513", "icon_egg.svg")  # Barn Red
        self.today_feed_card = self.create_metric_card("Feed Used (kg)", "0", "#558B2F", "icon_feed.svg")  # Darker Green
        self.today_sales_card = self.create_metric_card("Sales (AFG)", "0", "#E67E22", "icon_sales.svg")  # Carrot Orange
        self.today_revenue_card = self.create_metric_card("Revenue (USD)", "0", "#D35400", "icon_sales.svg")  # Pumpkin
        
        today_layout.addWidget(self.today_eggs_card, 0, 0)
        today_layout.addWidget(self.today_feed_card, 0, 1)
        today_layout.addWidget(self.today_sales_card, 0, 2)
        today_layout.addWidget(self.today_revenue_card, 0, 3)
        
        today_group.setLayout(today_layout)
        layout.addWidget(today_group)
        
        # Quick Actions - Premium styling
        actions_group = QGroupBox(tr("Quick Actions"))
        actions_group.setProperty("i18n_key", "Quick Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14pt;
                padding-top: 25px;
                margin-top: 15px;
                border: none;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 5px;
                color: #2c3e50;
            }
        """)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15)
        actions_layout.setContentsMargins(0, 10, 0, 10)
        
        quick_actions = [
            ("Add Production", self._navigate_to_production, "icon_egg.svg", "#8B4513"),
            ("Record Sale", self._navigate_to_sales, "icon_sales.svg", "#27AE60"),
            ("Record Purchase", self._navigate_to_purchases, "icon_purchases.svg", "#2980B9"),
            ("View Reports", self._navigate_to_reports, "icon_reports.svg", "#7F8C8D"),
        ]
        
        for action_text, callback, icon_name, color in quick_actions:
            btn = QPushButton(tr(action_text))
            btn.setProperty("i18n_key", action_text)
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(180)
            
            icon_path = get_asset_path(icon_name)
            if Path(icon_path).exists():
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(24, 24))
                
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11pt;
                    font-weight: 600;
                    letter-spacing: 0.3px;
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    color: #2c3e50;
                    text-align: left;
                    padding-left: 20px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    color: white;
                    border: 1px solid {color};
                }}
            """)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Main Content Grid (Charts + Activity)
        content_grid = QGridLayout()
        content_grid.setSpacing(20)
        content_grid.setContentsMargins(0, 10, 0, 10)

        # Charts Section (Left Side, spanning 2 columns)
        charts_group = QGroupBox(tr("Analytics & Forecasting"))
        charts_group.setProperty("i18n_key", "Analytics & Forecasting")
        charts_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14pt;
                padding-top: 25px;
                margin-top: 15px;
                border: none;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                padding: 0 5px;
                color: #2c3e50;
            }
        """)
        charts_layout = QVBoxLayout()
        charts_layout.setSpacing(20)
        charts_layout.setContentsMargins(0, 10, 0, 0)
        
        # Production Chart
        self.production_chart = TimeSeriesChart(title=tr("Daily Egg Production (Last 30 Days)"))
        self.production_chart.set_labels(left_label=tr("Total Eggs"), bottom_label=tr("Date"))
        self.production_chart.setMinimumHeight(350)
        # Add shadow effect to chart container if possible, or just style borders
        self.production_chart.setStyleSheet("border: 1px solid #e0e0e0; border-radius: 12px; background: white;")
        charts_layout.addWidget(self.production_chart)
        
        charts_group.setLayout(charts_layout)
        content_grid.addWidget(charts_group, 0, 0, 1, 2) # Row 0, Col 0, RowSpan 1, ColSpan 2

        # Right Side Column (Summary + Activity)
        right_column = QVBoxLayout()
        right_column.setSpacing(20)

        # Summary Metrics
        summary_group = QGroupBox(tr("Monthly Summary"))
        summary_group.setProperty("i18n_key", "Monthly Summary")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 12pt;
                border: none;
                padding-top: 10px;
            }
            QGroupBox::title { color: #555; }
        """)
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(10)
        summary_layout.setContentsMargins(0, 10, 0, 0)

        self.total_eggs_label = self.create_summary_label("Total Production", "0", "#E8F5E9", "#2E7D32")
        self.avg_eggs_label = self.create_summary_label("Daily Average", "0", "#E3F2FD", "#1565C0")
        self.total_sales_label = self.create_summary_label("Total Sales", "0 AFG", "#FFF3E0", "#E65100")
        
        summary_layout.addWidget(self.total_eggs_label)
        summary_layout.addWidget(self.avg_eggs_label)
        summary_layout.addWidget(self.total_sales_label)
        
        summary_group.setLayout(summary_layout)
        right_column.addWidget(summary_group)

        # Recent Activity Feed
        activity_group = QGroupBox(tr("Recent Activity"))
        activity_group.setProperty("i18n_key", "Recent Activity")
        activity_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 12pt;
                border: none;
                padding-top: 10px;
            }
            QGroupBox::title { color: #555; }
        """)
        self.activity_layout = QVBoxLayout()
        self.activity_layout.setSpacing(8)
        self.activity_layout.setContentsMargins(0, 10, 0, 0)
        self.activity_layout.setAlignment(Qt.AlignTop)
        
        # Placeholder for activity items
        self.activity_placeholder = QLabel("Loading activity...")
        self.activity_layout.addWidget(self.activity_placeholder)
        
        activity_group.setLayout(self.activity_layout)
        right_column.addWidget(activity_group)
        
        right_column.addStretch()
        content_grid.addLayout(right_column, 0, 2, 1, 1) # Row 0, Col 2, RowSpan 1, ColSpan 1

        layout.addLayout(content_grid)
        
        # Forecasting Widget (Full Width)
        forecast_group = QGroupBox(tr("Forecasting"))
        forecast_layout = QVBoxLayout()
        self.forecasting_widget = ForecastingWidget(self.farm_id)
        self.forecasting_widget.setMinimumHeight(300)
        self.forecasting_widget.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e0e0e0;")
        forecast_layout.addWidget(self.forecasting_widget)
        forecast_group.setLayout(forecast_layout)
        layout.addWidget(forecast_group)
        
        # Low Stock Alerts (Bottom)
        self.alerts_frame = QFrame()
        self.alerts_frame.setStyleSheet("""
            QFrame {
                background-color: #FFF3E0;
                border-left: 5px solid #FF9800;
                border-radius: 4px;
            }
        """)
        alerts_layout = QHBoxLayout(self.alerts_frame)
        alerts_layout.setContentsMargins(15, 10, 15, 10)
        self.alerts_label = QLabel(tr("Checking stock..."))
        self.alerts_label.setStyleSheet("color: #E65100; font-weight: 600;")
        alerts_layout.addWidget(self.alerts_label)
        layout.addWidget(self.alerts_frame)
        
        layout.addStretch()
        
        # Set container as scroll widget
        scroll.setWidget(container)
        
        # Main layout for this widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
    
    def _navigate_to_production(self):
        """Navigate to production page"""
        main_window = self.window()
        if hasattr(main_window, 'load_production'):
            main_window.load_production()
    
    def _navigate_to_sales(self):
        """Navigate to sales page"""
        main_window = self.window()
        if hasattr(main_window, 'load_sales'):
            main_window.load_sales()
    
    def _navigate_to_purchases(self):
        """Navigate to purchases page"""
        main_window = self.window()
        if hasattr(main_window, 'load_purchases'):
            main_window.load_purchases()
    
    def _navigate_to_reports(self):
        """Navigate to reports page"""
        main_window = self.window()
        if hasattr(main_window, 'load_reports'):
            main_window.load_reports()
    
    def create_metric_card(self, title: str, value: str, color: str, icon_name: str = None) -> QFrame:
        """Create a premium metric card widget with modern design and icon"""
        card = QFrame()
        card.setFrameShape(QFrame.NoFrame)
        card.setFixedHeight(120)
        card.setMinimumWidth(220)
        
        # Create gradient color
        card.setStyleSheet(f"""
            QFrame {{
                background: {color};
                border-radius: 15px;
                border: none;
            }}
        """)
        # Add subtle shadow via graphics effect or just rely on flat design with gradient
        
        layout = QHBoxLayout(card)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Left side: Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(tr(title))
        title_label.setProperty("i18n_key", title)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 11pt;
            font-weight: 600;
        """)
        text_layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            color: white;
            font-size: 22pt;
            font-weight: 800;
        """)
        text_layout.addWidget(value_label)
        text_layout.addStretch()
        
        layout.addLayout(text_layout)
        
        # Right side: Icon
        if icon_name:
            icon_path = get_asset_path(icon_name)
            if Path(icon_path).exists():
                icon_label = QLabel()
                pixmap = QPixmap(icon_path)
                # Recolor icon to white/transparent
                mask = pixmap.createMaskFromColor(Qt.transparent, Qt.MaskInColor)
                pixmap.fill(Qt.white)
                pixmap.setMask(mask)
                
                icon_label.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                icon_label.setGraphicsEffect(None) # Clear effects
                icon_label.setStyleSheet("background: transparent; opacity: 0.3;")
                # Opacity via styling on QLabel doesn't work well for pixmap usually, 
                # but we can set semi-transparent color if we draw it manually. 
                # For now, just show white icon.
                layout.addWidget(icon_label, 0, Qt.AlignRight | Qt.AlignTop)
        
        return card
    
    def create_summary_label(self, title, value, bg_color, text_color):
        """Create a summary row widget"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 8px;
            }}
        """)
        widget.setFixedHeight(60)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 5, 15, 5)
        
        title_lbl = QLabel(tr(title))
        title_lbl.setStyleSheet(f"color: #555; font-weight: 600; font-size: 10pt;")
        
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"color: {text_color}; font-weight: 800; font-size: 14pt;")
        
        layout.addWidget(title_lbl)
        layout.addStretch()
        layout.addWidget(val_lbl)
        
        return widget

    def refresh_data(self):
        """Refresh all dashboard data with caching."""
        logger.info(f"Refreshing dashboard for farm_id: {self.farm_id}")
        
        # 1. Update Forecasting
        if hasattr(self, 'forecasting_widget'):
            self.forecasting_widget.load_data()
        
        try:
            today = datetime.now().date()
            
            # 2. Update Metrics
            self._update_today_metrics(today)
            
            # 3. Update Chart
            self._update_chart(today)
            
            # 4. Update Summaries
            self._update_sales_summary()
            
            # 5. Update Low Stock
            self._update_low_stock_alerts()
            
            # 6. Update Activity Feed
            self._update_activity_feed()
            
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
            
            # Update eggs card (find value label)
            labels = self.today_eggs_card.findChildren(QLabel)
            if len(labels) > 1:
                AnimationHelper.count_up(labels[1], 0, today_eggs, is_int=True)
            
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
            
            feed_labels = self.today_feed_card.findChildren(QLabel)
            if len(feed_labels) > 1:
                AnimationHelper.count_up(feed_labels[1], 0, today_feed, is_int=False)
            
            # Today's sales
            sales_manager = SalesManager()
            today_sales = sales_manager.get_sales_summary(None, today, today)
            
            sales_labels = self.today_sales_card.findChildren(QLabel)
            if len(sales_labels) > 1:
                AnimationHelper.count_up(sales_labels[1], 0, today_sales.get('total_afg', 0), is_int=True)
            
            rev_labels = self.today_revenue_card.findChildren(QLabel)
            if len(rev_labels) > 1:
                AnimationHelper.count_up(rev_labels[1], 0, today_sales.get('total_usd', 0), is_int=False)
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def _update_chart(self, today):
        """Update production chart"""
        try:
            today_str = today.isoformat()
            # Try cache
            data = dashboard_cache.get_production_summary(self.farm_id, today_str)
            if data is None:
                data = self.report_generator.get_daily_production_summary(self.farm_id, days=30)
                dashboard_cache.set_production_summary(self.farm_id, today_str, data)
            
            dates = data.get('dates', [])
            egg_counts = data.get('egg_counts', [])
            
            if dates:
                self.production_chart.plot(dates, egg_counts, pen='b', name="Total Eggs")
                total_prod = sum(egg_counts)
                avg_prod = total_prod / len(egg_counts)
                
                # Update labels in summary section
                # Note: labels[2] is value due to layout
                lbls = self.total_eggs_label.findChildren(QLabel)
                if len(lbls) > 1: lbls[1].setText(f"{total_prod:,}")
                
                lbls = self.avg_eggs_label.findChildren(QLabel)
                if len(lbls) > 1: lbls[1].setText(f"{avg_prod:,.1f}")
            else:
                self.production_chart.plot([], [])
        except Exception as e:
            logger.error(f"Error updating chart: {e}")

    def _update_sales_summary(self):
        """Update sales summary labels"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            sales_manager = SalesManager()
            summary = sales_manager.get_sales_summary(None, start_date, end_date)
            total = summary.get('total_afg', 0)
            
            lbls = self.total_sales_label.findChildren(QLabel)
            if len(lbls) > 1: lbls[1].setText(f"{total:,.0f} AFG")
        except Exception as e:
            logger.error(f"Error updating sales summary: {e}")

    def _update_low_stock_alerts(self):
        """Update alerts section"""
        try:
            inventory_manager = InventoryManager()
            alerts = inventory_manager.get_low_stock_alerts()
            
            if alerts:
                self.alerts_frame.setVisible(True)
                count = len(alerts)
                first = alerts[0]
                text = f"⚠️ <b>{count} Low Stock Alert(s):</b> {first['name']} ({first['stock']} {first['unit']})"
                if count > 1:
                    text += " ..."
                self.alerts_label.setText(text)
            else:
                self.alerts_frame.setVisible(False)
        except Exception as e:
            logger.error(f"Error updating alerts: {e}")

    def _update_activity_feed(self):
        """Populate recent activity feed"""
        try:
            # Clear existing items
            while self.activity_layout.count():
                child = self.activity_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Fetch logs
            logs = get_audit_trail().get_logs(limit=5)
            
            if not logs:
                lbl = QLabel("No recent activity.")
                lbl.setStyleSheet("color: #7f8c8d; font-style: italic;")
                self.activity_layout.addWidget(lbl)
                return

            for log in logs:
                item = QFrame()
                item.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border-radius: 6px;
                        border: 1px solid #eee;
                    }
                """)
                item_layout = QHBoxLayout(item)
                item_layout.setContentsMargins(10, 8, 10, 8)
                item_layout.setSpacing(10)
                
                # Action Icon/Color dot
                dot = QLabel()
                dot.setFixedSize(8, 8)
                # Determine color based on action
                color = "#3498db" # Default blue
                if "delete" in log.action_type.value: color = "#e74c3c"
                elif "create" in log.action_type.value: color = "#2ecc71"
                elif "update" in log.action_type.value: color = "#f39c12"
                
                dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
                item_layout.addWidget(dot)
                
                # Description
                desc_text = log.description or f"{log.action_type.value} {log.entity_type}"
                desc = QLabel(desc_text)
                desc.setStyleSheet("font-weight: 500; color: #333;")
                item_layout.addWidget(desc, 1)
                
                # Time
                time_diff = datetime.utcnow() - log.timestamp
                if time_diff.total_seconds() < 60:
                    time_str = "Just now"
                elif time_diff.total_seconds() < 3600:
                    time_str = f"{int(time_diff.total_seconds() / 60)}m ago"
                elif time_diff.total_seconds() < 86400:
                    time_str = f"{int(time_diff.total_seconds() / 3600)}h ago"
                else:
                    time_str = f"{int(time_diff.days)}d ago"
                
                time_lbl = QLabel(time_str)
                time_lbl.setStyleSheet("color: #999; font-size: 9pt;")
                item_layout.addWidget(time_lbl)
                
                self.activity_layout.addWidget(item)
                
        except Exception as e:
            logger.error(f"Error updating activity feed: {e}")
            err_lbl = QLabel("Could not load activity.")
            self.activity_layout.addWidget(err_lbl)

    def set_farm_id(self, farm_id):
        """Update the farm ID and refresh the data."""
        self.farm_id = farm_id
        if hasattr(self, 'forecasting_widget'):
            self.forecasting_widget.set_farm_id(farm_id)
        self.refresh_data()