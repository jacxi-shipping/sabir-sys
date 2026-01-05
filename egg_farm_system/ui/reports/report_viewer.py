"""
Report viewer widget
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTextEdit, QMessageBox, QDateEdit, QFileDialog, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from modules.reports import ReportGenerator
from modules.parties import PartyManager
from ui.reports.production_analytics_widget import ProductionAnalyticsWidget
from egg_farm_system.database.db import DatabaseManager

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
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_report)
        
        analytics_btn = QPushButton("Production Analytics")
        analytics_btn.clicked.connect(self.open_production_analytics)

        header_hbox.addWidget(generate_btn)
        header_hbox.addWidget(export_btn)
        header_hbox.addWidget(analytics_btn)
        layout.addLayout(header_hbox)
        
        # Report content
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        layout.addWidget(self.report_text)
        
        self.setLayout(layout)

    def open_production_analytics(self):
        """Open the Production Analytics widget."""
        if not self.analytics_widget:
            session = DatabaseManager.get_session()
            self.analytics_widget = ProductionAnalyticsWidget(session)
        self.analytics_widget.show()
    
    def on_report_changed(self):
        """Handle report type change"""
        self.report_text.clear()
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
            self.report_text.clear()
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
                    text = f"Farm: {data['farm']}\nDate: {data['date']}\n\n"
                    for shed in data['sheds']:
                        text += f"{shed['name']}: {shed['total_eggs']} eggs\n"
                    text += f"\nTotal: {data['totals']['total']} eggs"
                    self.report_text.setText(text)

            elif report_type == 'monthly_production':
                farm_id = self.farm_id or 1
                year = self.date_edit.date().year()
                month = self.date_edit.date().month()
                data = self.report_generator.monthly_egg_production_report(farm_id, year, month)
                if data:
                    text = f"Farm: {data['farm']}\nMonth: {data['month']}/{data['year']}\n\n"
                    for d, vals in sorted(data['daily_summary'].items()):
                        text += f"{d}: {vals['total']} (usable {vals['usable']})\n"
                    self.report_text.setText(text)

            elif report_type == 'feed_usage':
                farm_id = self.farm_id or 1
                start = self.start_date_edit.date().toPython()
                end = self.end_date_edit.date().toPython()
                data = self.report_generator.feed_usage_report(farm_id, start, end)
                if data:
                    text = f"Farm: {data['farm']}\nPeriod: {data['start_date']} to {data['end_date']}\n\n"
                    for shed_name, shed_data in data['sheds'].items():
                        text += f"{shed_name}: {shed_data['total_kg']} kg\n"
                    self.report_text.setText(text)

            elif report_type == 'party_statement':
                party_id = self.party_combo.currentData()
                if not party_id:
                    QMessageBox.warning(self, 'Warning', 'Select a party')
                    return
                data = self.report_generator.party_statement(party_id)
                if data:
                    text = f"Party: {data['party']}\nFinal balance: Afs {data['final_balance_afg']}\n\n"
                    for e in data['entries']:
                        text += f"{e['date']}: {e['description']} D:{e['debit_afg']} C:{e['credit_afg']} Bal:{e['balance_afg']}\n"
                    self.report_text.setText(text)

            else:
                QMessageBox.information(self, "Info", f"Report generation for {report_type} is not supported yet")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {e}")
    
    def export_report(self):
        """Export report to CSV"""
        report_type = self.report_combo.currentData()
        try:
            # Generate same data used for display
            if report_type == 'daily_production':
                date = self.date_edit.date().toPython()
                farm_id = self.farm_id or 1
                data = self.report_generator.daily_egg_production_report(farm_id, date)
            elif report_type == 'monthly_production':
                year = self.date_edit.date().year()
                month = self.date_edit.date().month()
                data = self.report_generator.monthly_egg_production_report(self.farm_id or 1, year, month)
            elif report_type == 'feed_usage':
                start = self.start_date_edit.date().toPython()
                end = self.end_date_edit.date().toPython()
                data = self.report_generator.feed_usage_report(self.farm_id or 1, start, end)
            elif report_type == 'party_statement':
                party_id = self.party_combo.currentData()
                if not party_id:
                    QMessageBox.warning(self, 'Warning', 'Select a party')
                    return
                data = self.report_generator.party_statement(party_id)
            else:
                QMessageBox.information(self, 'Info', 'Export not supported for this report')
                return

            if not data:
                QMessageBox.warning(self, 'Warning', 'No data to export')
                return

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
