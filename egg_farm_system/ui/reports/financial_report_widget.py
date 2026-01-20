"""
Widget for viewing financial reports like P&L and Cash Flow.
"""
from egg_farm_system.utils.i18n import tr

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QDateEdit, 
    QPushButton, QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import QDate
from PySide6.QtGui import QFont
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.financial_reports import FinancialReportGenerator

class FinancialReportWidget(QWidget):
    def __init__(self, farm_id=None):
        super().__init__()
        self.session = DatabaseManager.get_session()
        self.farm_id = farm_id
        self.setWindowTitle(tr("Financial Reports"))
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Filters ---
        filters_group = QGroupBox("Report Period")
        filters_layout = QFormLayout()
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_edit.setDate(QDate.currentDate())
        filters_layout.addRow("Start Date:", self.start_date_edit)
        filters_layout.addRow("End Date:", self.end_date_edit)
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)

        self.generate_button = QPushButton(tr("Generate Reports"))
        self.generate_button.clicked.connect(self.generate_reports)
        layout.addWidget(self.generate_button)

        # --- P&L Display ---
        pnl_group = QGroupBox("Profit & Loss Statement")
        pnl_layout = QFormLayout()
        self.revenue_label = QLabel(tr("Total Revenue: Not calculated"))
        self.cogs_label = QLabel(tr("Cost of Goods Sold (Feed): Not calculated"))
        self.gross_profit_label = QLabel(tr("Gross Profit: Not calculated"))
        self.expenses_label = QLabel(tr("Operating Expenses: Not calculated"))
        self.net_profit_label = QLabel(tr("Net Profit: Not calculated"))
        pnl_layout.addRow(self.revenue_label)
        pnl_layout.addRow(self.cogs_label)
        pnl_layout.addRow(self.gross_profit_label)
        pnl_layout.addRow(self.expenses_label)
        pnl_layout.addRow(self.net_profit_label)
        pnl_group.setLayout(pnl_layout)
        layout.addWidget(pnl_group)

        # --- Cash Flow Display ---
        cash_flow_group = QGroupBox("Cash Flow Statement")
        cash_flow_layout = QFormLayout()
        self.inflows_label = QLabel(tr("Total Cash Inflows: Not calculated"))
        self.outflows_label = QLabel(tr("Total Cash Outflows: Not calculated"))
        self.net_cash_flow_label = QLabel(tr("Net Cash Flow: Not calculated"))
        cash_flow_layout.addRow(self.inflows_label)
        cash_flow_layout.addRow(self.outflows_label)
        cash_flow_layout.addRow(self.net_cash_flow_label)
        cash_flow_group.setLayout(cash_flow_layout)
        layout.addWidget(cash_flow_group)

        # Style bold labels
        for label in [self.net_profit_label, self.net_cash_flow_label]:
            font = label.font()
            font.setBold(True)
            label.setFont(font)

        self.setLayout(layout)

    def generate_reports(self):
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()

        try:
            generator = FinancialReportGenerator(self.session)
            
            # P&L Calculation
            pnl_data = generator.generate_pnl_statement(start_date, end_date, self.farm_id)
            self.update_pnl_labels(pnl_data)

            # Cash Flow Calculation
            cash_flow_data = generator.generate_cash_flow_statement(start_date, end_date, self.farm_id)
            self.update_cash_flow_labels(cash_flow_data)

        except Exception as e:
            QMessageBox.critical(self, tr("Error"), f"Failed to generate reports: {e}")

    def update_pnl_labels(self, pnl_data):
        self.revenue_label.setText(f"Total Revenue: {pnl_data['total_revenue']:,.2f} AFN")
        self.cogs_label.setText(f"Cost of Goods Sold (Feed): {pnl_data['total_cogs']:,.2f} AFN")
        self.gross_profit_label.setText(f"Gross Profit: {pnl_data['gross_profit']:,.2f} AFN")
        self.expenses_label.setText(f"Operating Expenses: {pnl_data['total_expenses']:,.2f} AFN")
        
        net_profit = pnl_data['net_profit']
        self.net_profit_label.setText(f"Net Profit: {net_profit:,.2f} AFN")
        
        self.net_profit_label.setStyleSheet("color: green;" if net_profit >= 0 else "color: red;")

    def update_cash_flow_labels(self, cash_data):
        self.inflows_label.setText(f"Total Cash Inflows: {cash_data['total_inflows']:,.2f} AFN")
        self.outflows_label.setText(f"Total Cash Outflows: {cash_data['total_outflows']:,.2f} AFN")
        
        net_cash_flow = cash_data['net_cash_flow']
        self.net_cash_flow_label.setText(f"Net Cash Flow: {net_cash_flow:,.2f} AFN")
        
        self.net_cash_flow_label.setStyleSheet("color: green;" if net_cash_flow >= 0 else "color: red;")

    def set_farm_id(self, farm_id):
        self.farm_id = farm_id
        self.clear_labels()

    def clear_labels(self):
        # Clear P&L
        self.revenue_label.setText(tr("Total Revenue: Not calculated"))
        self.cogs_label.setText(tr("Cost of Goods Sold (Feed): Not calculated"))
        self.gross_profit_label.setText(tr("Gross Profit: Not calculated"))
        self.expenses_label.setText(tr("Operating Expenses: Not calculated"))
        self.net_profit_label.setText(tr("Net Profit: Not calculated"))
        self.net_profit_label.setStyleSheet("")
        # Clear Cash Flow
        self.inflows_label.setText(tr("Total Cash Inflows: Not calculated"))
        self.outflows_label.setText(tr("Total Cash Outflows: Not calculated"))
        self.net_cash_flow_label.setText(tr("Net Cash Flow: Not calculated"))
        self.net_cash_flow_label.setStyleSheet("")

    def closeEvent(self, event):
        self.session.close()
        super().closeEvent(event)
