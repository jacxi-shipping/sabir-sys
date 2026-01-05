"""
Reusable charting components using pyqtgraph.
"""
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QDateTime
from datetime import datetime, timedelta, date

class TimeAxisItem(pg.AxisItem):
    """A custom axis item for displaying time-series data."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        # Convert timestamp values to readable date strings
        return [QDateTime.fromSecsSinceEpoch(int(v)).toString('yyyy-MM-dd') for v in values]

class TimeSeriesChart(QWidget):
    """A widget for displaying a time-series chart."""
    def __init__(self, title="Time Series Chart", parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.plot_widget = pg.PlotWidget(
            title=title,
            axisItems={'bottom': TimeAxisItem(orientation='bottom')}
        )
        self.layout.addWidget(self.plot_widget)

        # Set chart properties
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getAxis('left').setPen('k')
        self.plot_widget.getAxis('bottom').setPen('k')
        self.plot_widget.getAxis('left').setTextPen('k')
        self.plot_widget.getAxis('bottom').setTextPen('k')

        self.plot_item = self.plot_widget.getPlotItem()

    def plot(self, x_data, y_data, pen='b', name=None):
        """
        Plots data on the chart.
        x_data: List of datetime objects.
        y_data: List of numerical values.
        """
        # Convert datetime objects to timestamps for plotting
        timestamps = [(datetime(dt.year, dt.month, dt.day).timestamp() if isinstance(dt, date) else dt.timestamp()) for dt in x_data]
        
        # Clear previous plots
        self.plot_item.clear()

        # Create a new plot
        curve = self.plot_item.plot(timestamps, y_data, pen=pen, symbol='o', symbolBrush=pen, name=name)
        
        # Add a legend if a name is provided
        if name and not self.plot_item.legend:
            self.plot_item.addLegend()
        
    def set_labels(self, left_label=None, bottom_label=None):
        """Set labels for the axes."""
        if left_label:
            self.plot_widget.setLabel('left', left_label)
        if bottom_label:
            self.plot_widget.setLabel('bottom', bottom_label)
