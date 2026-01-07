"""
Report viewer widget
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QMessageBox, QDateEdit, QFileDialog, QSizePolicy, QGroupBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from pathlib import Path

from egg_farm_system.modules.reports import ReportGenerator
from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.ui.reports.production_analytics_widget import ProductionAnalyticsWidget
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.utils.excel_export import ExcelExporter
from egg_farm_system.utils.print_manager import PrintManager
from egg_farm_system.ui.widgets.datatable import DataTableWidget

class ReportViewerWidget(QWidget):
    """Report viewing and export widget"""

    def __init__(self, farm_id=None):
        super().__init__()
        self.report_generator = ReportGenerator()
        self.farm_id = farm_id
        self.analytics_widget = None  # To hold the reference
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Header: title left, actions right
        header_hbox = QHBoxLayout()
        title = QLabel("Reports")
        title.setObjectName('titleLabel')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_hbox.addWidget(title)
        header_hbox.addStretch()
        
        # Report selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Report:"))
        
        self.report_combo = QComboBox()
        self.report_combo.addItem("Daily Egg Production", "daily_production")
        self.report_combo.addItem("Monthly Egg Production", "monthly_production")
        self.report_combo.addItem("Feed Usage Report", "feed_usage")
        self.report_combo.addItem("Party Statement", "party_statement")
        self.report_combo.currentIndexChanged.connect(self.on_report_changed)
        selector_layout.addWidget(self.report_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Date selectors / filters
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)

        # Range selectors for feed usage
        date_layout.addWidget(QLabel("From:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setVisible(False)
        date_layout.addWidget(self.start_date_edit)

        date_layout.addWidget(QLabel("To:"))
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
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_report)
        
        export_csv_btn = QPushButton("Export to CSV")
        export_csv_btn.clicked.connect(self.export_report_csv)
        
        export_excel_btn = QPushButton("Export to Excel")
        export_excel_btn.clicked.connect(self.export_report_excel)
        
        export_pdf_btn = QPushButton("Export to PDF")
        export_pdf_btn.clicked.connect(self.export_report_pdf)
        
        print_btn = QPushButton("Print")
        print_btn.clicked.connect(self.print_report)
        
        print_preview_btn = QPushButton("Print Preview")
        print_preview_btn.clicked.connect(self.print_preview_report)
        
        analytics_btn = QPushButton("Production Analytics")
        analytics_btn.clicked.connect(self.open_production_analytics)

        header_hbox.addWidget(generate_btn)
        header_hbox.addWidget(export_csv_btn)
        header_hbox.addWidget(export_excel_btn)
        header_hbox.addWidget(export_pdf_btn)
        header_hbox.addWidget(print_btn)
        header_hbox.addWidget(print_preview_btn)
        header_hbox.addWidget(analytics_btn)
        layout.addLayout(header_hbox)
        
        # Store current report data
        self.current_report_data = None
        self.current_report_type = None
        
        # Report info header
        self.info_group = QGroupBox("Report Information")
        info_layout = QVBoxLayout()
        self.info_label = QLabel("No report generated yet. Select a report type and click 'Generate Report'.")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # Report table for tabular data
        self.report_table = DataTableWidget(enable_pagination=True)
        self.report_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.report_table)
        
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
        self.info_label.setText("No report generated yet. Select a report type and click 'Generate Report'.")
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
            self.info_label.setText("No report generated yet. Select a report type and click 'Generate Report'.")
        except Exception:
            pass
    
    def generate_report(self):
        """Generate selected report"""
        report_type = self.report_combo.currentData()
        
        try:
            date = self.date_edit.date().toPython()
            
            if report_type == "daily_production":
                from datetime import datetime as _dt
                farm_id = self.farm_id or 1
                # ensure a datetime is passed
                if hasattr(date, 'year') and not hasattr(date, 'hour'):
                    date_dt = _dt.combine(date, _dt.min.time())
                else:
                    date_dt = date
                data = self.report_generator.daily_egg_production_report(farm_id, date_dt)
                if data:
                    # Update info
                    date_str = data['date'].strftime('%Y-%m-%d') if hasattr(data['date'], 'strftime') else str(data['date'])
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
                farm_id = self.farm_id or 1
                year = self.date_edit.date().year()
                month = self.date_edit.date().month()
                data = self.report_generator.monthly_egg_production_report(farm_id, year, month)
                if data:
                    # Update info
                    self.info_label.setText(f"<b>Farm:</b> {data['farm']}<br><b>Month:</b> {data['month']}/{data['year']}")
                    
                    # Create table data
                    headers = ["Date", "Total", "Usable", "Small", "Medium", "Large", "Broken"]
                    rows = []
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
                    
                    self.report_table.set_headers(headers)
                    self.report_table.set_rows(rows)
                    self.current_report_data = data
                    self.current_report_type = report_type

            elif report_type == 'feed_usage':
                farm_id = self.farm_id or 1
                start = self.start_date_edit.date().toPython()
                end = self.end_date_edit.date().toPython()
                data = self.report_generator.feed_usage_report(farm_id, start, end)
                if data:
                    # Update info
                    self.info_label.setText(f"<b>Farm:</b> {data['farm']}<br><b>Period:</b> {data['start_date']} to {data['end_date']}")
                    
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
                    QMessageBox.warning(self, 'Warning', 'Select a party')
                    return
                data = self.report_generator.party_statement(party_id)
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
                    for e in data['entries']:
                        rows.append([
                            str(e.get('date', '')),
                            e.get('description', ''),
                            f"{e.get('debit_afg', 0):,.2f}",
                            f"{e.get('credit_afg', 0):,.2f}",
                            f"{e.get('balance_afg', 0):,.2f}",
                            f"{e.get('debit_usd', 0):,.2f}",
                            f"{e.get('credit_usd', 0):,.2f}",
                            f"{e.get('balance_usd', 0):,.2f}"
                        ])
                    
                    self.report_table.set_headers(headers)
                    self.report_table.set_rows(rows)
                    self.current_report_data = data
                    self.current_report_type = report_type

            else:
                QMessageBox.information(self, "Info", f"Report generation for {report_type} is not supported yet")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")
    
    def export_report_csv(self):
        """Export report to CSV"""
        if not self.current_report_data:
            QMessageBox.warning(self, 'Warning', 'Please generate a report first')
            return
        
        report_type = self.current_report_type
        data = self.current_report_data
        
        try:
            csv_text = self.report_generator.export_to_csv(data, report_type)
            if not csv_text:
                QMessageBox.critical(self, 'Error', 'Failed to generate CSV')
                return

            path, _ = QFileDialog.getSaveFileName(self, 'Save CSV', f'{report_type}.csv', 'CSV Files (*.csv)')
            if path:
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    f.write(csv_text)
                QMessageBox.information(self, 'Success', f'Exported to {path}')

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")
    
    def export_report_excel(self):
        """Export report to Excel"""
        if not self.current_report_data:
            QMessageBox.warning(self, 'Warning', 'Please generate a report first')
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
                QMessageBox.information(self, 'Success', f'Exported to {path}')
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Excel export failed: {e}")
    
    def export_report_pdf(self):
        """Export report to PDF"""
        if not self.current_report_data:
            QMessageBox.warning(self, 'Warning', 'Please generate a report first')
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
                    self.report_table.export_pdf(path)
                    QMessageBox.information(self, 'Success', f'Exported to {path}')
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
                    QMessageBox.information(self, 'Success', f'Exported to {path}')
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"PDF export failed: {e}")
    
    def print_report(self):
        """Print current report"""
        if not self.current_report_data:
            QMessageBox.warning(self, 'Warning', 'Please generate a report first')
            return
        
        try:
            report_type = self.current_report_type
            data = self.current_report_data
            title = self.report_combo.currentText()
            
            html = PrintManager.format_report_html(data, report_type, title)
            PrintManager.print_text(html, title, self)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Print failed: {e}")
    
    def print_preview_report(self):
        """Show print preview for current report"""
        if not self.current_report_data:
            QMessageBox.warning(self, 'Warning', 'Please generate a report first')
            return
        
        try:
            report_type = self.current_report_type
            data = self.current_report_data
            title = self.report_combo.currentText()
            
            html = PrintManager.format_report_html(data, report_type, title)
            PrintManager.print_preview(html, title, self)
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Print preview failed: {e}")
