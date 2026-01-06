"""
Print Manager for Egg Farm Management System
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from PySide6.QtWidgets import QPrinter, QPrintDialog, QPrintPreviewDialog
from PySide6.QtGui import QTextDocument, QPainter, QPageSize
from PySide6.QtCore import QMarginsF, Qt

logger = logging.getLogger(__name__)


class PrintManager:
    """Manages printing functionality"""
    
    @staticmethod
    def print_text(text: str, title: str = "Document", parent=None):
        """
        Print text content
        
        Args:
            text: Text content to print
            title: Document title
            parent: Parent widget
        """
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize.A4)
        printer.setPageMargins(QMarginsF(20, 20, 20, 20), QPageSize.Millimeter)
        
        dialog = QPrintDialog(printer, parent)
        if dialog.exec() == QPrintDialog.Accepted:
            document = QTextDocument()
            document.setHtml(text)
            document.print(printer)
            logger.info(f"Printed document: {title}")
    
    @staticmethod
    def print_preview(text: str, title: str = "Document", parent=None):
        """
        Show print preview
        
        Args:
            text: Text content to preview
            title: Document title
            parent: Parent widget
        """
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize.A4)
        printer.setPageMargins(QMarginsF(20, 20, 20, 20), QPageSize.Millimeter)
        
        def print_preview_func(printer):
            document = QTextDocument()
            document.setHtml(text)
            document.print(printer)
        
        preview = QPrintPreviewDialog(printer, parent)
        preview.paintRequested.connect(print_preview_func)
        preview.exec()
    
    @staticmethod
    def print_to_pdf(text: str, file_path: Path, title: str = "Document"):
        """
        Print text to PDF file
        
        Args:
            text: Text content
            file_path: Path to save PDF
            title: Document title
        """
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(file_path))
        printer.setPageSize(QPageSize.A4)
        printer.setPageMargins(QMarginsF(20, 20, 20, 20), QPageSize.Millimeter)
        
        document = QTextDocument()
        document.setHtml(text)
        document.print(printer)
        logger.info(f"PDF saved: {file_path}")
    
    @staticmethod
    def format_report_html(report_data: Dict[str, Any], report_type: str, title: str = "Report") -> str:
        """
        Format report data as HTML for printing
        
        Args:
            report_data: Report data dictionary
            report_type: Type of report
            title: Report title
            
        Returns:
            HTML formatted string
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    color: #333;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 20px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #3498db;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    border: 1px solid #2980b9;
                }}
                td {{
                    padding: 10px;
                    border: 1px solid #ddd;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
                .total-row {{
                    font-weight: bold;
                    background-color: #ecf0f1;
                }}
                .header-info {{
                    margin-bottom: 20px;
                    color: #7f8c8d;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: right;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="header-info">
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        if report_type == "daily_production":
            html += f"""
                <p><strong>Farm:</strong> {report_data.get('farm', 'N/A')}</p>
                <p><strong>Date:</strong> {report_data.get('date', 'N/A')}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Shed</th>
                        <th>Small</th>
                        <th>Medium</th>
                        <th>Large</th>
                        <th>Broken</th>
                        <th>Total</th>
                        <th>Usable</th>
                    </tr>
                </thead>
                <tbody>
            """
            for shed in report_data.get('sheds', []):
                html += f"""
                    <tr>
                        <td>{shed.get('name', '')}</td>
                        <td>{shed.get('small', 0)}</td>
                        <td>{shed.get('medium', 0)}</td>
                        <td>{shed.get('large', 0)}</td>
                        <td>{shed.get('broken', 0)}</td>
                        <td>{shed.get('total', 0)}</td>
                        <td>{shed.get('usable', 0)}</td>
                    </tr>
                """
            
            totals = report_data.get('totals', {})
            html += f"""
                    <tr class="total-row">
                        <td>TOTAL</td>
                        <td>{totals.get('small', 0)}</td>
                        <td>{totals.get('medium', 0)}</td>
                        <td>{totals.get('large', 0)}</td>
                        <td>{totals.get('broken', 0)}</td>
                        <td>{totals.get('total', 0)}</td>
                        <td>{totals.get('usable', 0)}</td>
                    </tr>
                </tbody>
            </table>
            """
        
        elif report_type == "monthly_production":
            html += f"""
                <p><strong>Farm:</strong> {report_data.get('farm', 'N/A')}</p>
                <p><strong>Month:</strong> {report_data.get('month', 'N/A')}/{report_data.get('year', 'N/A')}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Total</th>
                        <th>Usable</th>
                        <th>Small</th>
                        <th>Medium</th>
                        <th>Large</th>
                        <th>Broken</th>
                    </tr>
                </thead>
                <tbody>
            """
            for date_str, values in sorted(report_data.get('daily_summary', {}).items()):
                html += f"""
                    <tr>
                        <td>{date_str}</td>
                        <td>{values.get('total', 0)}</td>
                        <td>{values.get('usable', 0)}</td>
                        <td>{values.get('small', 0)}</td>
                        <td>{values.get('medium', 0)}</td>
                        <td>{values.get('large', 0)}</td>
                        <td>{values.get('broken', 0)}</td>
                    </tr>
                """
            html += "</tbody></table>"
        
        elif report_type == "party_statement":
            html += f"""
                <p><strong>Party:</strong> {report_data.get('party', 'N/A')}</p>
                <p><strong>Final Balance (AFG):</strong> {report_data.get('final_balance_afg', 0)}</p>
                <p><strong>Final Balance (USD):</strong> {report_data.get('final_balance_usd', 0)}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Debit (AFG)</th>
                        <th>Credit (AFG)</th>
                        <th>Balance (AFG)</th>
                    </tr>
                </thead>
                <tbody>
            """
            for entry in report_data.get('entries', []):
                html += f"""
                    <tr>
                        <td>{entry.get('date', '')}</td>
                        <td>{entry.get('description', '')}</td>
                        <td>{entry.get('debit_afg', 0)}</td>
                        <td>{entry.get('credit_afg', 0)}</td>
                        <td>{entry.get('balance_afg', 0)}</td>
                    </tr>
                """
            html += "</tbody></table>"
        
        html += """
            <div class="footer">
                <p>Egg Farm Management System - Generated Report</p>
            </div>
        </body>
        </html>
        """
        
        return html

