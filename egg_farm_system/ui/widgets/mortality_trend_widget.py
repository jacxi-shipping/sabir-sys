"""
Mortality Trend Widget for Dashboard
"""
from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from datetime import datetime, timedelta
import logging

from egg_farm_system.ui.widgets.dashboard_widget_base import DashboardWidgetBase
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Mortality, Flock
from sqlalchemy import func

logger = logging.getLogger(__name__)

try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available for MortalityTrendWidget")


class MortalityTrendWidget(DashboardWidgetBase):
    """Show mortality trend for last 30 days"""
    
    def __init__(self, parent=None):
        self.days = 30
        self.farm_id = None
        super().__init__("Mortality Trend (30 Days)", "mortality_trend", parent)
        self.refresh()
    
    def set_farm_id(self, farm_id):
        """Set farm ID and refresh"""
        self.farm_id = farm_id
        self.refresh()
    
    def refresh(self):
        """Fetch and display mortality trend"""
        try:
            session = DatabaseManager.get_session()
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=self.days - 1)
            
            # Get mortality data
            query = session.query(
                func.date(Mortality.date).label('date'),
                func.sum(Mortality.count).label('total')
            )
            
            # Filter by farm if specified
            if self.farm_id:
                query = query.join(Flock).filter(
                    Mortality.date >= start_date,
                    Mortality.date <= end_date
                )
            else:
                query = query.filter(
                    Mortality.date >= start_date,
                    Mortality.date <= end_date
                )
            
            mortalities = query.group_by(func.date(Mortality.date)).all()
            
            session.close()
            
            if mortalities:
                avg = sum(m.total for m in mortalities) / len(mortalities)
                self.display_chart(mortalities, avg, start_date, end_date)
            else:
                self.display_no_data()
                
        except Exception as e:
            logger.error(f"Error refreshing mortality trend: {e}")
            self.display_error(str(e))
    
    def display_chart(self, data, average, start_date, end_date):
        """Display mortality chart"""
        self.clear_content()
        
        if not MATPLOTLIB_AVAILABLE:
            # Fallback to text display
            summary = QLabel(f"Average daily mortality: {average:.1f} birds")
            summary.setAlignment(Qt.AlignCenter)
            summary.setStyleSheet("font-size: 12pt; padding: 10px;")
            self.content_layout.addWidget(summary)
            return
        
        try:
            # Create matplotlib figure
            fig = Figure(figsize=(6, 3), facecolor='white')
            ax = fig.add_subplot(111)
            
            # Create date map
            date_map = {m.date: m.total for m in data}
            
            # Fill in all dates
            all_dates = []
            counts = []
            current = start_date
            while current <= end_date:
                all_dates.append(current)
                counts.append(date_map.get(current, 0))
                current += timedelta(days=1)
            
            # Plot
            ax.bar(all_dates, counts, color='#e74c3c', alpha=0.7, label='Daily Mortality')
            ax.axhline(y=average, color='#3498db', linestyle='--', linewidth=2, label=f'Avg: {average:.1f}')
            
            ax.set_xlabel('Date', fontsize=9)
            ax.set_ylabel('Mortalities', fontsize=9)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(fontsize=8)
            ax.tick_params(axis='both', labelsize=8)
            
            # Rotate x-axis labels
            fig.autofmt_xdate()
            fig.tight_layout()
            
            # Add to widget
            canvas = FigureCanvasQTAgg(fig)
            self.content_layout.addWidget(canvas)
            
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            self.display_error(str(e))
    
    def show_settings(self):
        """Show settings for this widget"""
        # Could add dialog to change number of days
        logger.info("Mortality trend widget settings")
