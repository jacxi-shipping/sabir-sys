"""
Forecasting widget for egg production.
"""
from datetime import datetime, timedelta, date
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox
from PySide6.QtCore import Qt
import pyqtgraph as pg

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import EggProduction
from egg_farm_system.utils.calculations import EggCalculations
from egg_farm_system.ui.widgets.charts import TimeSeriesChart

class ForecastingWidget(QWidget):
    """
    Widget to display egg production forecast.
    """
    def __init__(self, farm_id, parent=None):
        super().__init__(parent)
        self.farm_id = farm_id
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Egg Production Forecast (Next 7 Days)")
        title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.layout.addLayout(header_layout)
        
        # Chart
        self.chart = TimeSeriesChart("Forecast Analysis")
        self.chart.set_labels(left_label="Eggs", bottom_label="Date")
        self.layout.addWidget(self.chart)
        
        self.load_data()

    def set_farm_id(self, farm_id):
        self.farm_id = farm_id
        self.load_data()

    def load_data(self):
        if not self.farm_id:
            return

        session = DatabaseManager.get_session()
        try:
            # Get last 30 days of production for the farm (sum of all sheds)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Simple query to aggregate daily production
            # Note: We need to filter by shed -> farm relationship.
            # Doing it in python for simplicity as complex joins can be tricky without direct SQL
            # Get sheds for this farm
            from egg_farm_system.database.models import Shed
            sheds = session.query(Shed).filter_by(farm_id=self.farm_id).all()
            shed_ids = [s.id for s in sheds]
            
            if not shed_ids:
                return

            productions = session.query(EggProduction).filter(
                EggProduction.shed_id.in_(shed_ids),
                EggProduction.date >= start_date,
                EggProduction.date <= end_date
            ).all()
            
            # Group by date
            daily_data = {}
            for p in productions:
                d_key = p.date.date()
                if d_key not in daily_data:
                    daily_data[d_key] = 0
                daily_data[d_key] += p.total_eggs
            
            # Sort data
            sorted_dates = sorted(daily_data.keys())
            history_values = [daily_data[d] for d in sorted_dates]
            
            # Forecast
            forecast_days = 7
            predictions = EggCalculations.calculate_production_forecast(history_values, forecast_days)
            
            # Prepare plotting data
            plot_dates = sorted_dates.copy()
            plot_values = history_values.copy()
            
            # Append forecast
            last_date = sorted_dates[-1] if sorted_dates else datetime.now().date()
            
            # We plot actuals in one color
            self.chart.plot_item.clear()
            
            # Plot History
            if sorted_dates:
                # Convert dates to timestamps
                ts_history = [datetime(d.year, d.month, d.day).timestamp() for d in sorted_dates]
                self.chart.plot_item.plot(ts_history, history_values, pen=pg.mkPen('b', width=2), name="Actual")
            
            # Plot Forecast
            if predictions:
                forecast_dates = [last_date + timedelta(days=i) for i in range(1, forecast_days + 1)]
                ts_forecast = [datetime(d.year, d.month, d.day).timestamp() for d in forecast_dates]
                
                # Connect last actual to first forecast
                if sorted_dates:
                    ts_forecast.insert(0, ts_history[-1])
                    predictions.insert(0, history_values[-1])
                
                self.chart.plot_item.plot(ts_forecast, predictions, pen=pg.mkPen('r', width=2, style=Qt.DashLine), name="Forecast")
                
            self.chart.plot_item.addLegend()

        except Exception as e:
            print(f"Error forecasting: {e}")
        finally:
            session.close()
