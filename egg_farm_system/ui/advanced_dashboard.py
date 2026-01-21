"""
Advanced Dashboard Widgets for v2.0
Interactive charts, analytics, and KPI displays
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QScrollArea, QGroupBox,
    QTextEdit, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QDate
from PySide6.QtGui import QFont, QPalette, QBrush, QColor, QPixmap
import pyqtgraph as pg
from pyqtgraph import PlotWidget, BarGraphItem
import numpy as np
from datetime import datetime, timedelta
import logging

from egg_farm_system.modules.advanced_analytics import AdvancedAnalytics
from egg_farm_system.modules.inventory_optimizer import InventoryOptimizer
from egg_farm_system.modules.financial_planner import FinancialPlanner

logger = logging.getLogger(__name__)

class KPIWidget(QWidget):
    """Key Performance Indicator display widget"""
    
    def __init__(self, title="", value=0, unit="", trend="neutral", parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setup_ui(title, value, unit, trend)
    
    def setup_ui(self, title, value, unit, trend):
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(f"{value:,.0f} {unit}" if unit else f"{value:,.0f}")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(value_label)
        
        # Trend indicator
        trend_colors = {
            "up": "#28a745",
            "down": "#dc3545", 
            "neutral": "#6c757d"
        }
        trend_indicators = {
            "up": "↗",
            "down": "↘",
            "neutral": "→"
        }
        
        trend_label = QLabel(f"{trend_indicators[trend]} Trend")
        trend_label.setAlignment(Qt.AlignCenter)
        trend_label.setStyleSheet(f"font-size: 12px; color: {trend_colors[trend]};")
        layout.addWidget(trend_label)

class ProductionForecastWidget(QWidget):
    """Production forecasting visualization widget"""
    
    forecast_updated = Signal(dict)
    
    def __init__(self, farm_id=1, parent=None):
        super().__init__(parent)
        self.farm_id = farm_id
        self.forecast_thread = None
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Production Forecast")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        # Controls
        self.days_spinbox = QSpinBox()
        self.days_spinbox.setMinimum(7)
        self.days_spinbox.setMaximum(90)
        self.days_spinbox.setValue(30)
        self.days_spinbox.setSuffix(" days")
        header_layout.addWidget(QLabel("Forecast Period:"))
        header_layout.addWidget(self.days_spinbox)
        
        self.refresh_button = QPushButton("Refresh Forecast")
        self.refresh_button.clicked.connect(self.update_forecast)
        header_layout.addWidget(self.refresh_button)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Chart area
        self.plot_widget = PlotWidget()
        self.plot_widget.setLabel('left', 'Eggs')
        self.plot_widget.setLabel('bottom', 'Date')
        self.plot_widget.setTitle('Production Forecast vs Historical Data')
        
        layout.addWidget(self.plot_widget)
        
        # Statistics panel
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.StyledPanel)
        stats_layout = QGridLayout(stats_frame)
        
        self.kpi_widgets = {
            'predicted_avg': KPIWidget("Avg Daily Production", 0, "eggs"),
            'confidence': KPIWidget("Forecast Confidence", 0, "%"),
            'trend': KPIWidget("Trend Direction", 0, ""),
            'range': KPIWidget("Prediction Range", 0, "eggs")
        }
        
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for i, (key, widget) in enumerate(self.kpi_widgets.items()):
            stats_layout.addWidget(widget, *positions[i])
        
        layout.addWidget(stats_frame)
        
        # Initial load
        self.update_forecast()
    
    def setup_timer(self):
        """Setup auto-refresh timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_forecast)
        self.timer.start(300000)  # Refresh every 5 minutes
    
    def update_forecast(self):
        """Update production forecast"""
        try:
            days_ahead = self.days_spinbox.value()
            
            # Run forecast in background thread
            self.forecast_thread = ForecastThread(self.farm_id, days_ahead)
            self.forecast_thread.result_ready.connect(self.update_forecast_display)
            self.forecast_thread.error_occurred.connect(self.handle_forecast_error)
            self.forecast_thread.start()
            
        except Exception as e:
            logger.error(f"Error updating forecast: {e}")
            self.handle_forecast_error(str(e))
    
    def update_forecast_display(self, forecast_data):
        """Update the display with forecast data"""
        try:
            if 'error' in forecast_data:
                self.plot_widget.clear()
                self.plot_widget.addLabel(text=f"Forecast Error: {forecast_data['error']}", 
                                        color='red', anchor=(0.5, 0.5))
                return
            
            # Update title with farm info
            farm_id = forecast_data.get('farm_id', 'Unknown')
            period = forecast_data.get('forecast_period', 'Unknown Period')
            self.title_label.setText(f"Production Forecast - Farm {farm_id}")
            
            # Clear previous plots
            self.plot_widget.clear()
            
            # Plot historical data (if available)
            if 'historical_data' in forecast_data:
                historical = forecast_data['historical_data']
                if historical:
                    dates = [datetime.strptime(d, '%Y-%m-%d') for d in historical['dates']]
                    values = historical['egg_counts']
                    
                    self.plot_widget.plot(dates, values, 
                                         pen=pg.mkPen('blue', width=2), 
                                         name='Historical Data')
            
            # Plot forecast
            forecasts = forecast_data.get('forecasts', [])
            if forecasts:
                forecast_dates = [datetime.strptime(f['date'], '%Y-%m-%d') for f in forecasts]
                predicted_values = [f['predicted_total_eggs'] for f in forecasts]
                
                # Main forecast line
                self.plot_widget.plot(forecast_dates, predicted_values,
                                    pen=pg.mkPen('red', width=3),
                                    name='Forecast')
                
                # Confidence intervals
                if 'confidence_intervals' in forecast_data:
                    confidence = forecast_data['confidence_intervals']
                    if 'prediction_range' in forecasts[0]:
                        lower_bounds = [f['prediction_range']['low'] for f in forecasts]
                        upper_bounds = [f['prediction_range']['high'] for f in forecasts]
                        
                        # Fill between upper and lower bounds
                        self.plot_widget.plot(forecast_dates, upper_bounds, 
                                            pen=pg.mkPen('red', width=1, style=Qt.DashLine))
                        self.plot_widget.plot(forecast_dates, lower_bounds,
                                            pen=pg.mkPen('red', width=1, style=Qt.DashLine))
                        
                        # Add fill between lines
                        self.plot_widget.addItem(pg.FillBetweenItem(
                            self.plot_widget.listDataItems()[-2],  # upper
                            self.plot_widget.listDataItems()[-1],  # lower
                            brush=pg.mkBrush('red', alpha=0.2)
                        ))
            
            # Update KPIs
            self.update_kpis(forecast_data)
            
            self.forecast_updated.emit(forecast_data)
            
        except Exception as e:
            logger.error(f"Error updating forecast display: {e}")
            self.handle_forecast_error(str(e))
    
    def update_kpis(self, forecast_data):
        """Update KPI widgets with forecast statistics"""
        try:
            forecasts = forecast_data.get('forecasts', [])
            if forecasts:
                # Average daily production
                avg_production = np.mean([f['predicted_total_eggs'] for f in forecasts])
                self.kpi_widgets['predicted_avg'].update_value(avg_production, "eggs")
                
                # Confidence level
                confidence_data = forecast_data.get('confidence_intervals', {})
                confidence = 85 if 'confidence_level' not in confidence_data else int(confidence_data['confidence_level'].rstrip('%'))
                self.kpi_widgets['confidence'].update_value(confidence, "%")
                
                # Trend direction
                first_week = np.mean([f['predicted_total_eggs'] for f in forecasts[:7]])
                last_week = np.mean([f['predicted_total_eggs'] for f in forecasts[-7:]])
                trend = "up" if last_week > first_week else "down" if last_week < first_week else "neutral"
                self.kpi_widgets['trend'].update_value(0, trend)
                
                # Prediction range
                ranges = [f['prediction_range']['high'] - f['prediction_range']['low'] for f in forecasts]
                avg_range = np.mean(ranges)
                self.kpi_widgets['range'].update_value(avg_range, "eggs")
                
                # Update trend colors
                trend_colors = {
                    "up": "#28a745",
                    "down": "#dc3545",
                    "neutral": "#6c757d"
                }
                self.kpi_widgets['trend'].update_trend_color(trend_colors[trend])
                
        except Exception as e:
            logger.error(f"Error updating KPIs: {e}")
    
    def handle_forecast_error(self, error_message):
        """Handle forecast errors"""
        self.plot_widget.clear()
        self.plot_widget.addLabel(text=f"Forecast Error:\n{error_message}", 
                                color='red', anchor=(0.5, 0.5))

class InventoryOptimizationWidget(QWidget):
    """Inventory optimization and ABC analysis widget"""
    
    def __init__(self, farm_id=1, parent=None):
        super().__init__(parent)
        self.farm_id = farm_id
        self.setup_ui()
        self.load_analysis()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Inventory Optimization")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh Analysis")
        self.refresh_button.clicked.connect(self.load_analysis)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Create tab widget for different analyses
        self.tab_widget = QTabWidget()
        
        # ABC Analysis tab
        self.abc_tab = QWidget()
        self.setup_abc_tab()
        self.tab_widget.addTab(self.abc_tab, "ABC Analysis")
        
        # Reorder Points tab
        self.reorder_tab = QWidget()
        self.setup_reorder_tab()
        self.tab_widget.addTab(self.reorder_tab, "Reorder Points")
        
        # Risk Assessment tab
        self.risk_tab = QWidget()
        self.setup_risk_tab()
        self.tab_widget.addTab(self.risk_tab, "Risk Assessment")
        
        # Optimization Recommendations tab
        self.recommendations_tab = QWidget()
        self.setup_recommendations_tab()
        self.tab_widget.addTab(self.recommendations_tab, "Recommendations")
        
        layout.addWidget(self.tab_widget)
    
    def setup_abc_tab(self):
        """Setup ABC Analysis tab"""
        layout = QVBoxLayout(self.abc_tab)
        
        # Summary KPIs
        kpi_layout = QHBoxLayout()
        
        self.abc_kpis = {
            'category_a': KPIWidget("Category A Items", 0, ""),
            'category_b': KPIWidget("Category B Items", 0, ""),
            'category_c': KPIWidget("Category C Items", 0, ""),
            'total_value': KPIWidget("Total Inventory Value", 0, "AFG")
        }
        
        for kpi in self.abc_kpis.values():
            kpi_layout.addWidget(kpi)
        
        layout.addLayout(kpi_layout)
        
        # ABC Chart
        self.abc_chart = PlotWidget()
        self.abc_chart.setLabel('left', 'Number of Items')
        self.abc_chart.setLabel('bottom', 'ABC Category')
        self.abc_chart.setTitle('ABC Analysis - Item Distribution')
        
        layout.addWidget(self.abc_chart)
        
        # ABC Table
        self.abc_table = QTableWidget()
        self.abc_table.setColumnCount(5)
        self.abc_table.setHorizontalHeaderLabels([
            "Item Name", "Category", "Current Stock", "Total Value", "Usage Frequency"
        ])
        header = self.abc_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.abc_table)
    
    def setup_reorder_tab(self):
        """Setup Reorder Points tab"""
        layout = QVBoxLayout(self.reorder_tab)
        
        # Summary KPIs
        kpi_layout = QHBoxLayout()
        
        self.reorder_kpis = {
            'items_needing_reorder': KPIWidget("Items Needing Reorder", 0, ""),
            'high_urgency': KPIWidget("High Urgency Items", 0, ""),
            'reorder_percentage': KPIWidget("Reorder Percentage", 0, "%")
        }
        
        for kpi in self.reorder_kpis.values():
            kpi_layout.addWidget(kpi)
        
        layout.addLayout(kpi_layout)
        
        # Reorder Points Table
        self.reorder_table = QTableWidget()
        self.reorder_table.setColumnCount(7)
        self.reorder_table.setHorizontalHeaderLabels([
            "Item Name", "Current Stock", "Reorder Point", "Reorder Quantity", 
            "Action Needed", "Urgency", "Days of Stock"
        ])
        header = self.reorder_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.reorder_table)
    
    def setup_risk_tab(self):
        """Setup Risk Assessment tab"""
        layout = QVBoxLayout(self.risk_tab)
        
        # Risk Summary
        risk_layout = QHBoxLayout()
        
        self.risk_kpis = {
            'critical_items': KPIWidget("Critical Risk Items", 0, ""),
            'high_risk_items': KPIWidget("High Risk Items", 0, ""),
            'at_risk_value': KPIWidget("At-Risk Value", 0, "AFG")
        }
        
        for kpi in self.risk_kpis.values():
            risk_layout.addWidget(kpi)
        
        layout.addLayout(risk_layout)
        
        # Risk Chart
        self.risk_chart = PlotWidget()
        self.risk_chart.setLabel('left', 'Number of Items')
        self.risk_chart.setLabel('bottom', 'Risk Level')
        self.risk_chart.setTitle('Stockout Risk Assessment')
        
        layout.addWidget(self.risk_chart)
        
        # Risk Table
        self.risk_table = QTableWidget()
        self.risk_table.setColumnCount(6)
        self.risk_table.setHorizontalHeaderLabels([
            "Item Name", "Risk Level", "Days of Stock", "Current Stock", 
            "Financial Impact", "Action Required"
        ])
        header = self.risk_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.risk_table)
    
    def setup_recommendations_tab(self):
        """Setup Recommendations tab"""
        layout = QVBoxLayout(self.recommendations_tab)
        
        # Recommendations text area
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        
        layout.addWidget(QLabel("Optimization Recommendations:"))
        layout.addWidget(self.recommendations_text)
        
        # Implementation Plan
        self.implementation_table = QTableWidget()
        self.implementation_table.setColumnCount(6)
        self.implementation_table.setHorizontalHeaderLabels([
            "Priority", "Item", "Current Stock", "Optimal Stock", 
            "Action", "Timeline"
        ])
        header = self.implementation_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(QLabel("Implementation Plan:"))
        layout.addWidget(self.implementation_table)
    
    def load_analysis(self):
        """Load inventory optimization analysis"""
        try:
            # Run analysis in background thread
            self.analysis_thread = InventoryAnalysisThread(self.farm_id)
            self.analysis_thread.result_ready.connect(self.update_analysis_display)
            self.analysis_thread.error_occurred.connect(self.handle_analysis_error)
            self.analysis_thread.start()
            
        except Exception as e:
            logger.error(f"Error loading inventory analysis: {e}")
            self.handle_analysis_error(str(e))
    
    def update_analysis_display(self, analysis_data):
        """Update display with analysis results"""
        try:
            if 'error' in analysis_data:
                self.recommendations_text.setPlainText(f"Analysis Error: {analysis_data['error']}")
                return
            
            # Update ABC Analysis
            self.update_abc_analysis(analysis_data)
            
            # Update Reorder Points
            self.update_reorder_analysis(analysis_data)
            
            # Update Risk Assessment
            self.update_risk_analysis(analysis_data)
            
            # Update Recommendations
            self.update_recommendations(analysis_data)
            
        except Exception as e:
            logger.error(f"Error updating analysis display: {e}")
            self.handle_analysis_error(str(e))
    
    def update_abc_analysis(self, data):
        """Update ABC analysis display"""
        try:
            abc_data = data.get('abc_analysis', {})
            if 'summary' in abc_data:
                summary = abc_data['summary']
                
                # Update KPIs
                self.abc_kpis['category_a'].update_value(summary['category_A']['count'], "")
                self.abc_kpis['category_b'].update_value(summary['category_B']['count'], "")
                self.abc_kpis['category_c'].update_value(summary['category_C']['count'], "")
                self.abc_kpis['total_value'].update_value(summary['total_value'], "AFG")
                
                # Update chart
                self.abc_chart.clear()
                categories = ['A', 'B', 'C']
                counts = [summary['category_A']['count'], 
                         summary['category_B']['count'], 
                         summary['category_C']['count']]
                
                bars = BarGraphItem(x=[0, 1, 2], height=counts, width=0.6, 
                                  brushes=['red', 'orange', 'yellow'])
                self.abc_chart.addItem(bars)
                
                self.abc_chart.getAxis('bottom').setTicks([[(i, cat) for i, cat in enumerate(categories)]])
            
            # Update table
            items = abc_data.get('items', [])
            self.abc_table.setRowCount(len(items))
            
            for i, item in enumerate(items):
                self.abc_table.setItem(i, 0, QTableWidgetItem(item['name']))
                self.abc_table.setItem(i, 1, QTableWidgetItem(item['abc_category']))
                self.abc_table.setItem(i, 2, QTableWidgetItem(f"{item['current_stock']:.1f}"))
                self.abc_table.setItem(i, 3, QTableWidgetItem(f"{item['total_value']:.0f} AFG"))
                self.abc_table.setItem(i, 4, QTableWidgetItem(str(item['usage_frequency'])))
                
                # Color code by category
                color = {'A': QColor(255, 200, 200), 'B': QColor(255, 230, 200), 'C': QColor(255, 255, 200)}
                for col in range(5):
                    self.abc_table.item(i, col).setBackground(QBrush(color.get(item['abc_category'])))
                    
        except Exception as e:
            logger.error(f"Error updating ABC analysis: {e}")
    
    def update_reorder_analysis(self, data):
        """Update reorder points display"""
        try:
            reorder_data = data.get('reorder_analysis', {})
            if 'summary' in reorder_data:
                summary = reorder_data['summary']
                
                # Update KPIs
                self.reorder_kpis['items_needing_reorder'].update_value(summary['items_needing_reorder'], "")
                self.reorder_kpis['high_urgency'].update_value(summary['high_urgency_items'], "")
                self.reorder_kpis['reorder_percentage'].update_value(summary['reorder_percentage'], "%")
            
            # Update table
            reorder_points = reorder_data.get('reorder_points', [])
            self.reorder_table.setRowCount(len(reorder_points))
            
            for i, item in enumerate(reorder_points):
                self.reorder_table.setItem(i, 0, QTableWidgetItem(item['item_name']))
                self.reorder_table.setItem(i, 1, QTableWidgetItem(f"{item['current_stock']:.1f}"))
                self.reorder_table.setItem(i, 2, QTableWidgetItem(f"{item['reorder_point']:.0f}"))
                self.reorder_table.setItem(i, 3, QTableWidgetItem(f"{item['reorder_quantity']:.0f}"))
                self.reorder_table.setItem(i, 4, QTableWidgetItem("Yes" if item['action_needed'] else "No"))
                self.reorder_table.setItem(i, 5, QTableWidgetItem(item['urgency'].title()))
                self.reorder_table.setItem(i, 6, QTableWidgetItem(f"{item['current_stock'] / 10:.1f}"))
                
                # Color code by urgency
                urgency_colors = {
                    'high': QColor(255, 200, 200),
                    'medium': QColor(255, 230, 200),
                    'low': QColor(200, 255, 200)
                }
                for col in range(7):
                    self.reorder_table.item(i, col).setBackground(QBrush(urgency_colors.get(item['urgency'])))
                    
        except Exception as e:
            logger.error(f"Error updating reorder analysis: {e}")
    
    def update_risk_analysis(self, data):
        """Update risk assessment display"""
        try:
            risk_data = data.get('stockout_risk', {})
            if 'summary' in risk_data:
                summary = risk_data['summary']
                
                # Update KPIs
                self.risk_kpis['critical_items'].update_value(summary['critical_items'], "")
                self.risk_kpis['high_risk_items'].update_value(summary['high_risk_items'], "")
                self.risk_kpis['at_risk_value'].update_value(summary['total_at_risk_value'], "AFG")
                
                # Update chart
                self.risk_chart.clear()
                risk_levels = ['Critical', 'High', 'Medium', 'Low']
                risk_counts = [summary['critical_items'], summary['high_risk_items'],
                              summary['medium_risk_items'], summary['low_risk_items']]
                
                bars = BarGraphItem(x=[0, 1, 2, 3], height=risk_counts, width=0.6,
                                  brushes=['red', 'orange', 'yellow', 'green'])
                self.risk_chart.addItem(bars)
                
                self.risk_chart.getAxis('bottom').setTicks([[(i, level) for i, level in enumerate(risk_levels)]])
            
            # Update table
            risk_assessment = risk_data.get('risk_assessment', [])
            self.risk_table.setRowCount(len(risk_assessment))
            
            for i, item in enumerate(risk_assessment):
                self.risk_table.setItem(i, 0, QTableWidgetItem(item['item_name']))
                self.risk_table.setItem(i, 1, QTableWidgetItem(item['risk_level'].title()))
                self.risk_table.setItem(i, 2, QTableWidgetItem(f"{item['days_of_stock']:.1f}"))
                self.risk_table.setItem(i, 3, QTableWidgetItem(f"{item['current_stock']:.1f}"))
                self.risk_table.setItem(i, 4, QTableWidgetItem(f"{item['financial_impact']:.0f} AFG"))
                self.risk_table.setItem(i, 5, QTableWidgetItem("Immediate" if item['risk_level'] == 'critical' else 
                                                             "Within 1 week" if item['risk_level'] == 'high' else
                                                             "Monitor"))
                
                # Color code by risk level
                risk_colors = {
                    'critical': QColor(255, 100, 100),
                    'high': QColor(255, 150, 100),
                    'medium': QColor(255, 200, 100),
                    'low': QColor(100, 255, 100)
                }
                for col in range(6):
                    self.risk_table.item(i, col).setBackground(QBrush(risk_colors.get(item['risk_level'])))
                    
        except Exception as e:
            logger.error(f"Error updating risk analysis: {e}")
    
    def update_recommendations(self, data):
        """Update recommendations display"""
        try:
            # Update recommendations text
            recommendations = data.get('optimization_recommendations', [])
            if recommendations:
                recommendations_text = "\n".join([f"• {rec}" for rec in recommendations])
                self.recommendations_text.setPlainText(recommendations_text)
            
            # Update implementation plan
            implementation_plan = data.get('implementation_plan', {})
            steps = implementation_plan.get('all_steps', [])
            
            self.implementation_table.setRowCount(len(steps))
            
            for i, step in enumerate(steps):
                self.implementation_table.setItem(i, 0, QTableWidgetItem(step['priority'].title()))
                self.implementation_table.setItem(i, 1, QTableWidgetItem(step['item']))
                self.implementation_table.setItem(i, 2, QTableWidgetItem(f"{step['current_stock']:.1f}"))
                self.implementation_table.setItem(i, 3, QTableWidgetItem(f"{step['optimal_stock']:.1f}"))
                self.implementation_table.setItem(i, 4, QTableWidgetItem(step['action']))
                self.implementation_table.setItem(i, 5, QTableWidgetItem(step['timeline']))
                
                # Color code by priority
                priority_colors = {
                    'critical': QColor(255, 100, 100),
                    'high': QColor(255, 150, 100),
                    'medium': QColor(255, 200, 100),
                    'low': QColor(100, 255, 100)
                }
                for col in range(6):
                    self.implementation_table.item(i, col).setBackground(QBrush(priority_colors.get(step['priority'])))
                    
        except Exception as e:
            logger.error(f"Error updating recommendations: {e}")
    
    def handle_analysis_error(self, error_message):
        """Handle analysis errors"""
        self.recommendations_text.setPlainText(f"Analysis Error: {error_message}")

class FinancialDashboardWidget(QWidget):
    """Financial dashboard with budgeting and forecasting"""
    
    def __init__(self, farm_id=1, parent=None):
        super().__init__(parent)
        self.farm_id = farm_id
        self.setup_ui()
        self.load_financial_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Financial Dashboard")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        self.year_combo = QComboBox()
        current_year = datetime.utcnow().year
        self.year_combo.addItems([str(year) for year in range(current_year - 2, current_year + 3)])
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentTextChanged.connect(self.load_financial_data)
        header_layout.addWidget(QLabel("Budget Year:"))
        header_layout.addWidget(self.year_combo)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_financial_data)
        header_layout.addWidget(self.refresh_button)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # KPI Cards
        kpi_frame = QFrame()
        kpi_frame.setFrameStyle(QFrame.StyledPanel)
        kpi_layout = QHBoxLayout(kpi_frame)
        
        self.financial_kpis = {
            'budgeted_revenue': KPIWidget("Budgeted Revenue", 0, "AFG"),
            'budgeted_expenses': KPIWidget("Budgeted Expenses", 0, "AFG"),
            'budgeted_profit': KPIWidget("Budgeted Profit", 0, "AFG"),
            'profit_margin': KPIWidget("Profit Margin", 0, "%")
        }
        
        for kpi in self.financial_kpis.values():
            kpi_layout.addWidget(kpi)
        
        layout.addWidget(kpi_frame)
        
        # Charts area
        charts_splitter = QSplitter(Qt.Horizontal)
        
        # Revenue vs Expenses Chart
        self.revenue_chart = PlotWidget()
        self.revenue_chart.setLabel('left', 'Amount (AFG)')
        self.revenue_chart.setLabel('bottom', 'Month')
        self.revenue_chart.setTitle('Budget vs Actual - Revenue & Expenses')
        charts_splitter.addWidget(self.revenue_chart)
        
        # Cash Flow Chart
        self.cash_flow_chart = PlotWidget()
        self.cash_flow_chart.setLabel('left', 'Cash Flow (AFG)')
        self.cash_flow_chart.setLabel('bottom', 'Month')
        self.cash_flow_chart.setTitle('Cash Flow Projection')
        charts_splitter.addWidget(self.cash_flow_chart)
        
        layout.addWidget(charts_splitter)
        
        # Scenario Analysis
        scenario_frame = QGroupBox("Scenario Analysis")
        scenario_layout = QGridLayout(scenario_frame)
        
        self.scenario_labels = {
            'pessimistic': {'revenue': QLabel(), 'profit': QLabel()},
            'realistic': {'revenue': QLabel(), 'profit': QLabel()},
            'optimistic': {'revenue': QLabel(), 'profit': QLabel()}
        }
        
        # Headers
        scenario_layout.addWidget(QLabel("Scenario"), 0, 0)
        scenario_layout.addWidget(QLabel("Revenue"), 0, 1)
        scenario_layout.addWidget(QLabel("Profit"), 0, 2)
        
        # Data rows
        row = 1
        for scenario, labels in self.scenario_labels.items():
            scenario_layout.addWidget(QLabel(scenario.title()), row, 0)
            scenario_layout.addWidget(labels['revenue'], row, 1)
            scenario_layout.addWidget(labels['profit'], row, 2)
            row += 1
        
        layout.addWidget(scenario_frame)
    
    def load_financial_data(self):
        """Load financial data and budgets"""
        try:
            year = int(self.year_combo.currentText())
            
            # Load budget data
            self.budget_thread = BudgetThread(self.farm_id, year)
            self.budget_thread.result_ready.connect(self.update_budget_display)
            self.budget_thread.error_occurred.connect(self.handle_budget_error)
            self.budget_thread.start()
            
            # Load forecast data
            self.forecast_thread = ForecastThread(self.farm_id, 12)  # 12 months
            self.forecast_thread.result_ready.connect(self.update_forecast_display)
            self.forecast_thread.error_occurred.connect(self.handle_budget_error)
            self.forecast_thread.start()
            
        except Exception as e:
            logger.error(f"Error loading financial data: {e}")
            self.handle_budget_error(str(e))
    
    def update_budget_display(self, budget_data):
        """Update budget display"""
        try:
            if 'error' in budget_data:
                self.handle_budget_error(budget_data['error'])
                return
            
            # Update KPIs
            summary = budget_data.get('budget_summary', {})
            profit_loss = summary.get('profit_loss_projection', {})
            
            self.financial_kpis['budgeted_revenue'].update_value(
                profit_loss.get('total_revenue', 0), "AFG"
            )
            self.financial_kpis['budgeted_expenses'].update_value(
                profit_loss.get('total_expenses', 0), "AFG"
            )
            self.financial_kpis['budgeted_profit'].update_value(
                profit_loss.get('gross_profit', 0), "AFG"
            )
            self.financial_kpis['profit_margin'].update_value(
                profit_loss.get('gross_profit_margin', 0), "%"
            )
            
            # Update charts
            self.update_revenue_chart(budget_data)
            
            # Update scenarios
            self.update_scenarios(budget_data)
            
        except Exception as e:
            logger.error(f"Error updating budget display: {e}")
    
    def update_forecast_display(self, forecast_data):
        """Update forecast display"""
        try:
            if 'error' in forecast_data:
                return
            
            # Update cash flow chart
            cash_flow = forecast_data.get('forecasts', {}).get('cash_flow', {})
            monthly_data = cash_flow.get('monthly_forecasts', [])
            
            if monthly_data:
                months = list(range(1, len(monthly_data) + 1))
                cumulative_flows = [item['cumulative_cash_flow'] for item in monthly_data]
                
                self.cash_flow_chart.clear()
                self.cash_flow_chart.plot(months, cumulative_flows,
                                        pen=pg.mkPen('green', width=2),
                                        name='Cumulative Cash Flow')
                self.cash_flow_chart.addLegend()
                
        except Exception as e:
            logger.error(f"Error updating forecast display: {e}")
    
    def update_revenue_chart(self, budget_data):
        """Update revenue vs expenses chart"""
        try:
            monthly_dist = budget_data.get('revenue_budget', {}).get('monthly_distribution', {})
            if monthly_dist:
                months = []
                revenues = []
                expenses = []
                
                for month_key in sorted(monthly_dist.keys()):
                    month_num = int(month_key.split('_')[1])
                    months.append(month_num)
                    revenues.append(monthly_dist[month_key].get('total_afg', 0))
                    
                    # Get corresponding expense data
                    expense_month = budget_data.get('expense_budget', {}).get('monthly_distribution', {}).get(month_key, {})
                    expenses.append(expense_month.get('total_afg', 0))
                
                self.revenue_chart.clear()
                self.revenue_chart.plot(months, revenues, pen=pg.mkPen('blue', width=2), name='Revenue')
                self.revenue_chart.plot(months, expenses, pen=pg.mkPen('red', width=2), name='Expenses')
                self.revenue_chart.addLegend()
                
        except Exception as e:
            logger.error(f"Error updating revenue chart: {e}")
    
    def update_scenarios(self, budget_data):
        """Update scenario analysis"""
        try:
            scenarios = budget_data.get('budget_scenarios', {})
            
            for scenario_name, scenario_data in scenarios.items():
                if scenario_name in self.scenario_labels:
                    revenue = scenario_data.get('total_revenue', 0)
                    profit = scenario_data.get('net_profit', 0)
                    
                    self.scenario_labels[scenario_name]['revenue'].setText(f"{revenue:,.0f} AFG")
                    self.scenario_labels[scenario_name]['profit'].setText(f"{profit:,.0f} AFG")
                    
                    # Color code by profitability
                    color = 'green' if profit > 0 else 'red'
                    self.scenario_labels[scenario_name]['revenue'].setStyleSheet(f"color: {color};")
                    self.scenario_labels[scenario_name]['profit'].setStyleSheet(f"color: {color};")
                    
        except Exception as e:
            logger.error(f"Error updating scenarios: {e}")
    
    def handle_budget_error(self, error_message):
        """Handle budget/forecast errors"""
        logger.error(f"Financial dashboard error: {error_message}")

# Background thread classes for async operations
class ForecastThread(QThread):
    result_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, farm_id, days_ahead):
        super().__init__()
        self.farm_id = farm_id
        self.days_ahead = days_ahead
    
    def run(self):
        try:
            analytics = AdvancedAnalytics()
            result = analytics.forecast_egg_production(self.farm_id, self.days_ahead)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

class InventoryAnalysisThread(QThread):
    result_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, farm_id):
        super().__init__()
        self.farm_id = farm_id
    
    def run(self):
        try:
            optimizer = InventoryOptimizer()
            result = optimizer.analyze_inventory_optimization(self.farm_id)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

class BudgetThread(QThread):
    result_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, farm_id, year):
        super().__init__()
        self.farm_id = farm_id
        self.year = year
    
    def run(self):
        try:
            planner = FinancialPlanner()
            result = planner.create_budget(self.farm_id, self.year)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
