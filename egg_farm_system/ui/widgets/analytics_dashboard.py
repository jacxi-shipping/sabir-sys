"""
Advanced Analytics Dashboard Widget
"""
from egg_farm_system.utils.i18n import tr

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QComboBox, QDateEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QTextEdit, QSizePolicy
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont

from egg_farm_system.utils.advanced_analytics import (
    ProductionAnalytics, FinancialAnalytics, InventoryAnalytics
)
from egg_farm_system.utils.jalali import format_value_for_ui

logger = logging.getLogger(__name__)


class AnalyticsDashboardWidget(QWidget):
    """Advanced analytics dashboard"""
    
    def __init__(self, farm_id=None, parent=None):
        super().__init__(parent)
        self.farm_id = farm_id
        self.production_analytics = ProductionAnalytics()
        self.financial_analytics = FinancialAnalytics()
        self.inventory_analytics = InventoryAnalytics()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(tr("Advanced Analytics"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Tabs for different analytics
        self.tabs = QTabWidget()
        
        # Production Analytics Tab
        production_tab = self.create_production_analytics_tab()
        self.tabs.addTab(production_tab, "Production Analytics")
        
        # Financial Analytics Tab
        financial_tab = self.create_financial_analytics_tab()
        self.tabs.addTab(financial_tab, "Financial Analytics")
        
        # Inventory Analytics Tab
        inventory_tab = self.create_inventory_analytics_tab()
        self.tabs.addTab(inventory_tab, "Inventory Analytics")
        
        layout.addWidget(self.tabs)
    
    def create_production_analytics_tab(self) -> QWidget:
        """Create production analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel(tr("Analysis Period:")))
        
        self.anomaly_days = QComboBox()
        self.anomaly_days.addItems(['7', '14', '30', '60', '90'])
        self.anomaly_days.setCurrentText('30')
        controls_layout.addWidget(QLabel(tr("Days:")))
        controls_layout.addWidget(self.anomaly_days)
        
        analyze_btn = QPushButton(tr("Analyze Anomalies"))
        analyze_btn.clicked.connect(self.analyze_anomalies)
        controls_layout.addWidget(analyze_btn)
        
        compare_btn = QPushButton(tr("Compare Sheds"))
        compare_btn.clicked.connect(self.compare_sheds)
        controls_layout.addWidget(compare_btn)
        
        seasonal_btn = QPushButton(tr("Seasonal Analysis"))
        seasonal_btn.clicked.connect(self.seasonal_analysis)
        controls_layout.addWidget(seasonal_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Results
        self.anomaly_table = QTableWidget()
        self.anomaly_table.setColumnCount(6)
        self.anomaly_table.setHorizontalHeaderLabels([
            "Date", "Value", "Expected", "Deviation", "Type", "Severity"
        ])
        self.anomaly_table.verticalHeader().setMinimumSectionSize(40)
        self.anomaly_table.verticalHeader().setDefaultSectionSize(40)
        layout.addWidget(self.anomaly_table)
        
        return widget
    
    def create_financial_analytics_tab(self) -> QWidget:
        """Create financial analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Date range
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel(tr("From:")))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel(tr("To:")))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)
        
        analyze_pnl_btn = QPushButton(tr("Profit & Loss Analysis"))
        analyze_pnl_btn.clicked.connect(self.analyze_pnl)
        date_layout.addWidget(analyze_pnl_btn)
        
        cost_breakdown_btn = QPushButton(tr("Cost Breakdown"))
        cost_breakdown_btn.clicked.connect(self.analyze_cost_breakdown)
        date_layout.addWidget(cost_breakdown_btn)
        
        roi_btn = QPushButton(tr("Calculate ROI"))
        roi_btn.clicked.connect(self.calculate_roi)
        date_layout.addWidget(roi_btn)
        
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # Results
        self.financial_results = QTextEdit()
        self.financial_results.setReadOnly(True)
        layout.addWidget(self.financial_results)
        
        return widget
    
    def create_inventory_analytics_tab(self) -> QWidget:
        """Create inventory analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        turnover_btn = QPushButton(tr("Inventory Turnover"))
        turnover_btn.clicked.connect(self.analyze_turnover)
        controls_layout.addWidget(turnover_btn)
        
        abc_btn = QPushButton(tr("ABC Analysis"))
        abc_btn.clicked.connect(self.abc_analysis)
        controls_layout.addWidget(abc_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Results
        self.inventory_results = QTextEdit()
        self.inventory_results.setReadOnly(True)
        layout.addWidget(self.inventory_results)
        
        return widget
    
    def analyze_anomalies(self):
        """Analyze production anomalies"""
        if not self.farm_id:
            return
        
        days = int(self.anomaly_days.currentText())
        anomalies = self.production_analytics.detect_anomalies(self.farm_id, days)
        
        self.anomaly_table.setRowCount(len(anomalies))
        for row, anomaly in enumerate(anomalies):
            self.anomaly_table.setItem(row, 0, QTableWidgetItem(format_value_for_ui(anomaly.get('date'))))
            self.anomaly_table.setItem(row, 1, QTableWidgetItem(str(anomaly['value'])))
            self.anomaly_table.setItem(row, 2, QTableWidgetItem(str(anomaly['expected'])))
            self.anomaly_table.setItem(row, 3, QTableWidgetItem(str(anomaly['deviation'])))
            self.anomaly_table.setItem(row, 4, QTableWidgetItem(anomaly['type']))
            self.anomaly_table.setItem(row, 5, QTableWidgetItem(anomaly['severity']))
    
    def compare_sheds(self):
        """Compare shed performance"""
        if not self.farm_id:
            return
        
        comparison = self.production_analytics.shed_performance_comparison(self.farm_id)
        
        # Update table
        self.anomaly_table.setColumnCount(8)
        self.anomaly_table.setHorizontalHeaderLabels([
            "Shed", "Total Eggs", "Usable Eggs", "Avg Daily", 
            "Total Birds", "Eggs/Bird", "Production Days", "Utilization %"
        ])
        
        self.anomaly_table.setRowCount(len(comparison))
        for row, data in enumerate(comparison):
            self.anomaly_table.setItem(row, 0, QTableWidgetItem(data['shed_name']))
            self.anomaly_table.setItem(row, 1, QTableWidgetItem(str(data['total_eggs'])))
            self.anomaly_table.setItem(row, 2, QTableWidgetItem(str(data['usable_eggs'])))
            self.anomaly_table.setItem(row, 3, QTableWidgetItem(str(data['avg_daily'])))
            self.anomaly_table.setItem(row, 4, QTableWidgetItem(str(data['total_birds'])))
            self.anomaly_table.setItem(row, 5, QTableWidgetItem(str(data['eggs_per_bird'])))
            self.anomaly_table.setItem(row, 6, QTableWidgetItem(str(data['production_days'])))
            self.anomaly_table.setItem(row, 7, QTableWidgetItem(f"{data['utilization']}%"))
    
    def seasonal_analysis(self):
        """Perform seasonal analysis"""
        if not self.farm_id:
            return
        
        trends = self.production_analytics.seasonal_trend_analysis(self.farm_id)
        
        text = "Seasonal Production Trends\n\n"
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month in range(1, 13):
            if month in trends:
                data = trends[month]
                text += f"{month_names[month-1]}: Avg {data['average']:.0f} eggs "
                text += f"(Range: {data['min']:.0f} - {data['max']:.0f}, "
                text += f"Based on {data['count']} months)\n"
        
        self.anomaly_table.clear()
        self.anomaly_table.setColumnCount(1)
        self.anomaly_table.setHorizontalHeaderLabels(["Analysis Results"])
        self.anomaly_table.setRowCount(1)
        self.anomaly_table.setItem(0, 0, QTableWidgetItem(text))
    
    def analyze_pnl(self):
        """Analyze profit and loss"""
        if not self.farm_id:
            return
        
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        
        pnl = self.financial_analytics.profit_loss_analysis(self.farm_id, start, end)
        
        text = f"Profit & Loss Analysis\n"
        text += f"Period: {format_value_for_ui(pnl.get('period', 'N/A'))}\n\n"
        text += f"Revenue:\n"
        text += f"  AFG: {pnl.get('revenue_afg', 0):,.0f}\n"
        text += f"  USD: {pnl.get('revenue_usd', 0):,.2f}\n\n"
        text += f"Costs:\n"
        text += f"  Feed Costs (AFG): {pnl.get('feed_costs_afg', 0):,.0f}\n"
        text += f"  Expenses (AFG): {pnl.get('expenses_afg', 0):,.0f}\n"
        text += f"  Total Costs (AFG): {pnl.get('total_costs_afg', 0):,.0f}\n\n"
        text += f"Profit/Loss:\n"
        text += f"  AFG: {pnl.get('profit_afg', 0):,.0f}\n"
        text += f"  USD: {pnl.get('profit_usd', 0):,.2f}\n"
        text += f"  Profit Margin: {pnl.get('profit_margin', 0):.2f}%\n"
        
        self.financial_results.setText(text)
    
    def analyze_cost_breakdown(self):
        """Analyze cost breakdown"""
        if not self.farm_id:
            return
        
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        
        breakdown = self.financial_analytics.cost_breakdown(self.farm_id, start, end)
        
        text = "Cost Breakdown by Category\n\n"
        total_afg = sum(cat['afg'] for cat in breakdown.values())
        
        for category, data in sorted(breakdown.items(), key=lambda x: x[1]['afg'], reverse=True):
            percentage = (data['afg'] / total_afg * 100) if total_afg > 0 else 0
            text += f"{category}:\n"
            text += f"  AFG: {data['afg']:,.0f} ({percentage:.1f}%)\n"
            text += f"  USD: {data['usd']:,.2f}\n"
            text += f"  Transactions: {data['count']}\n\n"
        
        text += f"Total: {total_afg:,.0f} AFG\n"
        
        self.financial_results.setText(text)
    
    def calculate_roi(self):
        """Calculate ROI"""
        if not self.farm_id:
            return
        
        roi_data = self.financial_analytics.calculate_roi(self.farm_id)
        
        text = "Return on Investment (ROI) Analysis\n\n"
        text += f"Investment (Inventory Value):\n"
        text += f"  AFG: {roi_data.get('investment_afg', 0):,.0f}\n\n"
        text += f"Profit (Last {roi_data.get('period_days', 365)} days):\n"
        text += f"  AFG: {roi_data.get('profit_afg', 0):,.0f}\n\n"
        text += f"ROI: {roi_data.get('roi_percentage', 0):.2f}%\n"
        
        self.financial_results.setText(text)
    
    def analyze_turnover(self):
        """Analyze inventory turnover"""
        turnover = self.inventory_analytics.inventory_turnover_ratio()
        
        text = "Inventory Turnover Analysis\n\n"
        text += f"Total Purchases (1 year):\n"
        text += f"  AFG: {turnover.get('total_purchases_afg', 0):,.0f}\n\n"
        text += f"Average Inventory Value:\n"
        text += f"  AFG: {turnover.get('avg_inventory_afg', 0):,.0f}\n\n"
        text += f"Turnover Ratio: {turnover.get('turnover_ratio', 0):.2f}\n"
        text += f"Days to Turnover: {turnover.get('days_to_turnover', 0):.1f} days\n"
        
        self.inventory_results.setText(text)
    
    def abc_analysis(self):
        """Perform ABC analysis"""
        abc = self.inventory_analytics.abc_analysis()
        
        text = "ABC Analysis (Inventory Value Classification)\n\n"
        text += f"Total Inventory Value: {abc.get('total_value', 0):,.0f} AFG\n\n"
        
        text += "Category A (High Value - 80% of total):\n"
        for item in abc.get('A', [])[:10]:  # Show top 10
            text += f"  {item['name']}: {item['value']:,.0f} AFG\n"
        
        text += "\nCategory B (Medium Value - 15% of total):\n"
        for item in abc.get('B', [])[:10]:
            text += f"  {item['name']}: {item['value']:,.0f} AFG\n"
        
        text += "\nCategory C (Low Value - 5% of total):\n"
        for item in abc.get('C', [])[:10]:
            text += f"  {item['name']}: {item['value']:,.0f} AFG\n"
        
        self.inventory_results.setText(text)
    
    def set_farm_id(self, farm_id):
        """Update farm ID"""
        self.farm_id = farm_id

