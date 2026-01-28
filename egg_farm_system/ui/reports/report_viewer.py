"""
Report viewer widget
"""
from egg_farm_system.utils.i18n import tr

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QMessageBox, QDateEdit, QFileDialog, QSizePolicy, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from pathlib import Path

from egg_farm_system.modules.reports import ReportGenerator
from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.farms import FarmManager
from egg_farm_system.ui.reports.production_analytics_widget import ProductionAnalyticsWidget
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.utils.excel_export import ExcelExporter
from egg_farm_system.utils.print_manager import PrintManager
from egg_farm_system.ui.widgets.datatable import DataTableWidget
from egg_farm_system.utils.jalali import format_value_for_ui
from egg_farm_system.ui.widgets.charts import TimeSeriesChart
from datetime import datetime, date

class ReportViewerWidget(QWidget):
    """Report viewing and export widget"""

    def __init__(self, farm_id=None):
        super().__init__()
        self.farm_id = farm_id
        self.analytics_widget = None  # To hold the reference
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Header: title left, actions right
        header_hbox = QHBoxLayout()
        title = QLabel(tr("Reports"))
        title.setObjectName('titleLabel')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_hbox.addWidget(title)
        header_hbox.addStretch()
        
        # Report selector and farm filter
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(tr("Report:")))
        
        self.report_combo = QComboBox()
        self.report_combo.addItem("Daily Egg Production", "daily_production")
        self.report_combo.addItem("Monthly Egg Production", "monthly_production")
        self.report_combo.addItem("Feed Usage Report", "feed_usage")
        self.report_combo.addItem("Party Statement", "party_statement")
        self.report_combo.currentIndexChanged.connect(self.on_report_changed)
        selector_layout.addWidget(self.report_combo)
        
        # Farm filter
        selector_layout.addWidget(QLabel(tr("Farm:")))
        self.farm_combo = QComboBox()
        self.farm_combo.setMinimumWidth(150)
        self.farm_combo.setToolTip(tr("Select a farm to filter reports, or 'All Farms' to show all"))
        self.farm_combo.addItem(tr("All Farms"), None)
        try:
            fm = FarmManager()
            farms = fm.get_all_farms()
            for farm in farms:
                self.farm_combo.addItem(farm.name, farm.id)
        except Exception as e:
            print(f"Error loading farms: {e}")
        selector_layout.addWidget(self.farm_combo)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Date selectors / filters
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel(tr("Date:")))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)

        # Range selectors for feed usage
        date_layout.addWidget(QLabel(tr("From:")))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setVisible(False)
        date_layout.addWidget(self.start_date_edit)

        date_layout.addWidget(QLabel(tr("To:")))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setVisible(False)
        date_layout.addWidget(self.end_date_edit)

        # Party selector for party statement
        self.party_combo = QComboBox()
        try:
            pm = PartyManager()
            for party in pm.get_all_parties():
                self.party_combo.addItem(party.name, party.id)
        except Exception:
            pass
        self.party_combo.setVisible(False)
        date_layout.addWidget(self.party_combo)

        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # Generate and Export buttons
        generate_btn = QPushButton(tr("Generate Report"))
        generate_btn.clicked.connect(self.generate_report)
        
        export_csv_btn = QPushButton(tr("Export to CSV"))
        export_csv_btn.clicked.connect(self.export_report_csv)
        
        export_excel_btn = QPushButton(tr("Export to Excel"))
        export_excel_btn.clicked.connect(self.export_report_excel)
        
        export_pdf_btn = QPushButton(tr("Export to PDF"))
        export_pdf_btn.clicked.connect(self.export_report_pdf)
        
        print_btn = QPushButton(tr("Print"))
        print_btn.clicked.connect(self.print_report)
        
        analytics_btn = QPushButton(tr("Production Analytics"))
        analytics_btn.clicked.connect(self.open_production_analytics)

        header_hbox.addWidget(generate_btn)
        header_hbox.addWidget(export_csv_btn)
        header_hbox.addWidget(export_excel_btn)
        header_hbox.addWidget(export_pdf_btn)
        header_hbox.addWidget(print_btn)
        header_hbox.addWidget(analytics_btn)
        layout.addLayout(header_hbox)
        
        # Store current report data
        self.current_report_data = None
        self.current_report_type = None
        
        # Report info header
        self.info_group = QGroupBox("Report Information")
        info_layout = QVBoxLayout()
        self.info_label = QLabel(tr("No report generated yet. Select a report type and click 'Generate Report'."))
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # Splitter for Table and Chart
        from PySide6.QtWidgets import QSplitter
        splitter = QSplitter(Qt.Vertical)
        
        # Report table for tabular data
        self.report_table = DataTableWidget(enable_pagination=True)
        self.report_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(self.report_table)
        
        # Chart widget
        self.chart = TimeSeriesChart("Trend Analysis")
        self.chart.setVisible(False) # Hidden by default
        self.chart.setMinimumHeight(300)
        splitter.addWidget(self.chart)
        
        # Set splitter sizes to give more space to table initially, or 50/50 when chart is shown
        splitter.setSizes([400, 300])
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)

    def open_production_analytics(self):
        """Open the Production Analytics widget."""
        if not self.analytics_widget:
            session = DatabaseManager.get_session()
            self.analytics_widget = ProductionAnalyticsWidget(session)
        self.analytics_widget.show()
    
    def on_report_changed(self):
        """Handle report type change"""
        self.report_table.clear()
        self.chart.setVisible(False)
        self.info_label.setText(tr("No report generated yet. Select a report type and click 'Generate Report'."))
        # Show/hide relevant filters
        report_type = self.report_combo.currentData()
        if report_type == 'feed_usage':
            self.date_edit.setVisible(False)
            self.start_date_edit.setVisible(True)
            self.end_date_edit.setVisible(True)
            self.party_combo.setVisible(False)
        elif report_type == 'monthly_production':
            self.date_edit.setVisible(True)
            self.start_date_edit.setVisible(False)
            self.end_date_edit.setVisible(False)
            self.party_combo.setVisible(False)
        elif report_type == 'party_statement':
            self.date_edit.setVisible(False)
            self.start_date_edit.setVisible(False)
            self.end_date_edit.setVisible(False)
            self.party_combo.setVisible(True)
        else:
            self.date_edit.setVisible(True)
            self.start_date_edit.setVisible(False)
            self.end_date_edit.setVisible(False)
            self.party_combo.setVisible(False)

    def set_farm_id(self, farm_id):
        self.farm_id = farm_id
        try:
            self.report_table.clear()
            self.chart.setVisible(False)
            self.info_label.setText(tr("No report generated yet. Select a report type and click 'Generate Report'."))
        except Exception:
            pass
    
    def generate_report(self):
        """Generate selected report"""
        report_type = self.report_combo.currentData()
        self.chart.setVisible(False) # Hide previous chart
        
        # Get selected farm ID from combo box (None means "All Farms")
        selected_farm_id = self.farm_combo.currentData()
        # If a specific farm is selected, use it; otherwise use self.farm_id or 1 as fallback
        farm_id_to_use = selected_farm_id if selected_farm_id is not None else (self.farm_id or 1)
        
        try:
            date_val = self.date_edit.date().toPython()
            
            with ReportGenerator() as rg:
                if report_type == "daily_production":
                    # ... existing logic ...
                    # For daily, a chart isn't very useful unless it's comparative (Shed vs Shed)
                    # We can bar chart sheds?
                    # Let's keep it simple for now or implement Bar Chart in future
                    from datetime import datetime as _dt
                    # ensure a datetime is passed
                    if hasattr(date_val, 'year') and not hasattr(date_val, 'hour'):
                        date_dt = _dt.combine(date_val, _dt.min.time())
                    else:
                        date_dt = date_val
                    data = rg.daily_egg_production_report(farm_id_to_use, date_dt)
                    if data:
                        # Update info
                        date_str = format_value_for_ui(data.get('date'))
                        self.info_label.setText(f"<b>Farm:</b> {data['farm']}<br><b>Date:</b> {date_str}")
                        
                        # Create table data
                        headers = ["Shed", "Small", "Medium", "Large", "Broken", "Total", "Usable"]
                        rows = []
                        for shed in data['sheds']:
                            rows.append([
                                shed['name'],
                                str(shed.get('small', 0)),
                                str(shed.get('medium', 0)),
                                str(shed.get('large', 0)),
                                str(shed.get('broken', 0)),
                                str(shed.get('total', 0)),
                                str(shed.get('usable', 0))
                            ])
                        # Add totals row
                        totals = data.get('totals', {})
                        rows.append([
                            "<b>TOTAL</b>",
                            str(totals.get('small', 0)),
                            str(totals.get('medium', 0)),
                            str(totals.get('large', 0)),
                            str(totals.get('broken', 0)),
                            f"<b>{totals.get('total', 0)}</b>",
                            f"<b>{totals.get('usable', 0)}</b>"
                        ])
                        
                        self.report_table.set_headers(headers)
                        self.report_table.set_rows(rows)
                        self.current_report_data = data
                        self.current_report_type = report_type

                elif report_type == 'monthly_production':
                    year = self.date_edit.date().year()
                    month = self.date_edit.date().month()
                    data = rg.monthly_egg_production_report(farm_id_to_use, year, month)
                    if data:
                        # Update info
                        self.info_label.setText(f"<b>Farm:</b> {data['farm']}<br><b>Month:</b> {data['month']}/{data['year']}")
                        
                        # Create table data
                        headers = ["Date", "Total", "Usable", "Small", "Medium", "Large", "Broken"]
                        rows = []
                        chart_dates = []
                        chart_totals = []
                        
                        for d, vals in sorted(data['daily_summary'].items()):
                            rows.append([
                                str(d),
                                str(vals.get('total', 0)),
                                str(vals.get('usable', 0)),
                                str(vals.get('small', 0)),
                                str(vals.get('medium', 0)),
                                str(vals.get('large', 0)),
                                str(vals.get('broken', 0))
                            ])
                            # Prepare chart data
                            try:
                                dt = date(year, month, int(d))
                                chart_dates.append(dt)
                                chart_totals.append(vals.get('total', 0))
                            except ValueError:
                                pass
                        
                        self.report_table.set_headers(headers)
                        self.report_table.set_rows(rows)
                        
                        # Show chart
                        if chart_dates:
                            self.chart.setVisible(True)
                            self.chart.set_labels(left_label="Total Eggs", bottom_label="Date")
                            self.chart.plot(chart_dates, chart_totals, name="Total Production")
                        
                        self.current_report_data = data
                        self.current_report_type = report_type

                elif report_type == 'feed_usage':
                    start = self.start_date_edit.date().toPython()
                    end = self.end_date_edit.date().toPython()
                    data = rg.feed_usage_report(farm_id_to_use, start, end)
                    if data:
                        # Update info
                        start_str = format_value_for_ui(data.get('start_date'))
                        end_str = format_value_for_ui(data.get('end_date'))
                        self.info_label.setText(f"<b>Farm:</b> {data['farm']}<br><b>Period:</b> {start_str} to {end_str}")
                        
                        # Create table data
                        headers = ["Shed", "Feed Type", "Total (kg)", "Issues", "Avg per Issue (kg)", "Cost (AFG)", "Cost (USD)"]
                        rows = []
                        for shed_name, shed_data in data['sheds'].items():
                            rows.append([
                                shed_name,
                                shed_data.get('feed_type', 'N/A'),
                                f"{shed_data.get('total_kg', 0):.2f}",
                                str(shed_data.get('issue_count', 0)),
                                f"{shed_data.get('avg_per_issue', 0):.2f}",
                                f"{shed_data.get('total_cost_afg', 0):.2f}",
                                f"{shed_data.get('total_cost_usd', 0):.2f}"
                            ])
                        
                        self.report_table.set_headers(headers)
                        self.report_table.set_rows(rows)
                        self.current_report_data = data
                        self.current_report_type = report_type

                elif report_type == 'party_statement':
                    party_id = self.party_combo.currentData()
                    if not party_id:
                        QMessageBox.warning(self, tr('Warning'), 'Select a party')
                        return
                    data = rg.party_statement(party_id)
                    if data:
                        # Update info
                        self.info_label.setText(
                            f"<b>Party:</b> {data['party']}<br>"
                            f"<b>Final Balance (AFG):</b> {data.get('final_balance_afg', 0):,.2f}<br>"
                            f"<b>Final Balance (USD):</b> {data.get('final_balance_usd', 0):,.2f}"
                        )
                        
                        # Create table data
                        headers = ["Date", "Description", "Debit (AFG)", "Credit (AFG)", "Balance (AFG)", 
                                  "Debit (USD)", "Credit (USD)", "Balance (USD)"]
                        rows = []
                        chart_dates = []
                        chart_balances = []
                        
                        for e in data['entries']:
                            rows.append([
                                format_value_for_ui(e.get('date', '')),
                                e.get('description', ''),
                                f"{e.get('debit_afg', 0):,.2f}",
                                f"{e.get('credit_afg', 0):,.2f}",
                                f"{e.get('balance_afg', 0):,.2f}",
                                f"{e.get('debit_usd', 0):,.2f}",
                                f"{e.get('credit_usd', 0):,.2f}",
                                f"{e.get('balance_usd', 0):,.2f}"
                            ])
                            # Extract chart data if date is valid
                            if e.get('date'):
                                try:
                                    if isinstance(e['date'], (datetime, date)):
                                        chart_dates.append(e['date'])
                                    else:
                                        # parsing handled by format_value_for_ui usually, but here we need object
                                        pass 
                                    chart_balances.append(e.get('balance_afg', 0))
                                except: pass
                        
                        self.report_table.set_headers(headers)
                        self.report_table.set_rows(rows)
                        
                        # Show balance trend chart if data exists
                        if chart_dates and len(chart_dates) == len(chart_balances):
                            self.chart.setVisible(True)
                            self.chart.set_labels(left_label="Balance (AFG)", bottom_label="Date")
                            self.chart.plot(chart_dates, chart_balances, name="Balance (AFG)", pen='g')

                        self.current_report_data = data
                        self.current_report_type = report_type

                else:
                    QMessageBox.information(self, tr("Info"), f"Report generation for {report_type} is not supported yet")
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Failed to generate report: {e}")
    
    def export_report_csv(self):
        """Export report to CSV"""
        if not self.current_report_data:
            QMessageBox.warning(self, tr('Warning'), 'Please generate a report first')
            return
        
        report_type = self.current_report_type
        data = self.current_report_data
        
        try:
            with ReportGenerator() as rg:
                csv_text = rg.export_to_csv(data, report_type)
            
            if not csv_text:
                QMessageBox.critical(self, tr('Error'), 'Failed to generate CSV')
                return

            path, _ = QFileDialog.getSaveFileName(self, 'Save CSV', f'{report_type}.csv', 'CSV Files (*.csv)')
            if path:
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    f.write(csv_text)
                QMessageBox.information(self, tr('Success'), f'Exported to {path}')

        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Export failed: {e}")
    
    def export_report_excel(self):
        """Export report to Excel"""
        if not self.current_report_data:
            QMessageBox.warning(self, tr('Warning'), 'Please generate a report first')
            return
        
        report_type = self.current_report_type
        data = self.current_report_data
        
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, 
                'Save Excel', 
                f'{report_type}.xlsx', 
                'Excel Files (*.xlsx);;All Files (*.*)'
            )
            
            if path:
                exporter = ExcelExporter()
                exporter.export_report_data(data, report_type, Path(path))
                QMessageBox.information(self, tr('Success'), f'Exported to {path}')
        
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Excel export failed: {e}")
    
    def export_report_pdf(self):
        """Export report to PDF"""
        if not self.current_report_data:
            QMessageBox.warning(self, tr('Warning'), 'Please generate a report first')
            return
        
        try:
            report_type = self.current_report_type
            data = self.current_report_data
            title = self.report_combo.currentText()
            
            # Use the table's PDF export if available, otherwise use HTML
            if hasattr(self.report_table, 'export_pdf') and self.report_table.model.rowCount() > 0:
                # Export table directly to PDF
                result = QFileDialog.getSaveFileName(
                    self, 
                    'Save PDF', 
                    f'{report_type}.pdf', 
                    'PDF Files (*.pdf)'
                )
                if isinstance(result, tuple):
                    path, _ = result
                else:
                    path = result
                
                if path:
                    # Get report title and subtitle
                    report_title = self.current_report_type.replace('_', ' ').title() if self.current_report_type else "Report"
                    subtitle = None
                    if self.current_report_data:
                        if 'farm' in self.current_report_data:
                            subtitle = f"Farm: {self.current_report_data.get('farm', '')}"
                        if 'start_date' in self.current_report_data and 'end_date' in self.current_report_data:
                            s = format_value_for_ui(self.current_report_data.get('start_date'))
                            e = format_value_for_ui(self.current_report_data.get('end_date'))
                            subtitle = f"Period: {s} to {e}"
                        elif 'month' in self.current_report_data and 'year' in self.current_report_data:
                            subtitle = f"Month: {self.current_report_data.get('month', '')}/{self.current_report_data.get('year', '')}"
                    
                    self.report_table.export_pdf(path, title=report_title, subtitle=subtitle)
                    QMessageBox.information(self, tr('Success'), f'Exported to {path}')
            else:
                # Fallback to HTML-based PDF
                html = PrintManager.format_report_html(data, report_type, title)
                result = QFileDialog.getSaveFileName(
                    self, 
                    'Save PDF', 
                    f'{report_type}.pdf', 
                    'PDF Files (*.pdf)'
                )
                if isinstance(result, tuple):
                    path, _ = result
                else:
                    path = result
                
                if path:
                    PrintManager.print_to_pdf(html, Path(path), title)
                    QMessageBox.information(self, tr('Success'), f'Exported to {path}')
        
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"PDF export failed: {e}")
    
    def print_report(self):
        """Print current report"""
        if not self.current_report_data:
            QMessageBox.warning(self, tr('Warning'), 'Please generate a report first')
            return
        
        try:
            report_type = self.current_report_type
            data = self.current_report_data
            title = self.report_combo.currentText()
            
            html = PrintManager.format_report_html(data, report_type, title)
            PrintManager.print_text(html, title, self)
        
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Print failed: {e}")

