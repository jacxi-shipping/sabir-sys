"""
Professional PDF exporter for tables and reports using ReportLab
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Any, Tuple

from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import QStandardPaths

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


class ProfessionalPDFExporter:
    """Professional PDF exporter using ReportLab"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.header_color = colors.HexColor("#2980b9")  # Professional blue
        self.table_header_color = colors.HexColor("#3498db")  # Lighter blue
        self.row_even_color = colors.white
        self.row_odd_color = colors.HexColor("#f5f5f5")
        
        # Custom styles
        self.styles.add(ParagraphStyle(
            name='HeaderTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.white,
            alignment=TA_RIGHT,
            spaceAfter=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='HeaderSubtitle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=TA_RIGHT
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=2
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyDetail',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            alignment=TA_LEFT,
            leading=11
        ))

        self.styles.add(ParagraphStyle(
            name='CellText',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            leading=11
        ))
        
        self.styles.add(ParagraphStyle(
            name='CellHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.white,
            alignment=TA_LEFT
        ))

    def export_table(self, headers: List[str], rows: List[List[Any]], 
                    path: Optional[str] = None, title: str = "Report",
                    subtitle: Optional[str] = None,
                    company_name: Optional[str] = None,
                    company_address: Optional[str] = None,
                    company_phone: Optional[str] = None,
                    show_totals: bool = False,
                    totals_row: Optional[List[Any]] = None,
                    parent=None) -> bool:
        """
        Export table data to professional PDF using ReportLab
        """
        # Defensive check for invalid path types (e.g. boolean from Qt signals)
        if isinstance(path, bool) or (isinstance(path, str) and not path.strip()):
            path = None

        try:
            # 1. Handle File Path
            if path is None:
                default_name = f"{title.lower().replace(' ', '_')}.pdf"
                documents_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
                default_path = os.path.join(documents_path, default_name)
                
                result = QFileDialog.getSaveFileName(
                    parent, "Export PDF", 
                    default_path, 
                    "PDF Files (*.pdf)"
                )
                if isinstance(result, tuple):
                    path, _ = result
                else:
                    path = result
                
                if not path or not isinstance(path, str) or path == '':
                    return False

            # Ensure .pdf extension
            if not path.lower().endswith('.pdf'):
                path += '.pdf'

            # 2. Prepare Data for Table
            # Convert all data to Paragraphs for wrapping
            table_data = []
            
            # Header Row
            header_row = [Paragraph(str(h), self.styles['CellHeader']) for h in headers]
            table_data.append(header_row)
            
            # Data Rows
            for row in rows:
                processed_row = []
                for cell in row:
                    # Handle None values
                    text = str(cell) if cell is not None else ""
                    processed_row.append(Paragraph(text, self.styles['CellText']))
                table_data.append(processed_row)
            
            # Totals Row
            if show_totals and totals_row:
                total_processed = []
                for cell in totals_row:
                    text = str(cell) if cell is not None else ""
                    # Use bold for totals
                    p = Paragraph(f"<b>{text}</b>", self.styles['CellText'])
                    total_processed.append(p)
                table_data.append(total_processed)

            # 3. Setup Document
            # Determine orientation based on column count/width
            # Simple heuristic: > 6 columns -> Landscape
            page_size = landscape(A4) if len(headers) > 6 else A4
            
            doc = SimpleDocTemplate(
                path,
                pagesize=page_size,
                leftMargin=15*mm,
                rightMargin=15*mm,
                topMargin=35*mm,  # Space for header
                bottomMargin=20*mm
            )

            # 4. Create Table
            # Calculate available width
            avail_width = doc.width
            col_widths = [avail_width / len(headers)] * len(headers)
            
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Table Styling
            style_cmds = [
                ('BACKGROUND', (0, 0), (-1, 0), self.table_header_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]
            
            # Alternating row colors
            for i in range(1, len(table_data)):
                bg_color = self.row_odd_color if i % 2 == 1 else self.row_even_color
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg_color))
            
            # Style for totals row if present
            if show_totals and totals_row:
                style_cmds.append(('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey))
                style_cmds.append(('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'))

            table.setStyle(TableStyle(style_cmds))
            
            elements = [table]

            # 5. Define Header and Footer Callback
            def draw_header_footer(canvas, doc):
                canvas.saveState()
                
                # --- Header ---
                header_height = 25 * mm
                page_width, page_height = doc.pagesize
                
                # Blue background for header
                canvas.setFillColor(self.header_color)
                canvas.rect(0, page_height - header_height, page_width, header_height, fill=1, stroke=0)
                
                # Company Info (Left)
                text_x = 15 * mm
                text_y = page_height - 10 * mm
                
                # We use Paragraphs drawn on canvas for rich text
                p = Paragraph(company_name or "Company Name", self.styles['CompanyName'])
                w, h = p.wrap(page_width/2, header_height)
                p.drawOn(canvas, text_x, text_y - h)
                
                current_y = text_y - h - 2*mm
                if company_address:
                    p = Paragraph(company_address, self.styles['CompanyDetail'])
                    w, h = p.wrap(page_width/2, header_height)
                    p.drawOn(canvas, text_x, current_y - h)
                    current_y -= (h + 1*mm)
                    
                if company_phone:
                    p = Paragraph(f"Phone: {company_phone}", self.styles['CompanyDetail'])
                    w, h = p.wrap(page_width/2, header_height)
                    p.drawOn(canvas, text_x, current_y - h)

                # Report Title (Right)
                right_margin = 15 * mm
                title_width = page_width/2
                
                p = Paragraph(title, self.styles['HeaderTitle'])
                w, h = p.wrap(title_width, header_height)
                p.drawOn(canvas, page_width - right_margin - w, page_height - 12 * mm - h)
                
                if subtitle:
                    p = Paragraph(subtitle, self.styles['HeaderSubtitle'])
                    w, h = p.wrap(title_width, header_height)
                    p.drawOn(canvas, page_width - right_margin - w, page_height - 12 * mm - h - 6*mm)

                # Date (Bottom Right of Header)
                date_str = datetime.now().strftime("%B %d, %Y")
                canvas.setFont("Helvetica", 9)
                canvas.setFillColor(colors.white)
                canvas.drawRightString(page_width - right_margin, page_height - header_height + 3*mm, date_str)

                # --- Footer ---
                footer_height = 10 * mm
                canvas.setFillColor(colors.HexColor("#ecf0f1")) # Light gray footer bg
                canvas.rect(0, 0, page_width, footer_height, fill=1, stroke=0)
                
                canvas.setStrokeColor(colors.lightgrey)
                canvas.line(15*mm, footer_height, page_width - 15*mm, footer_height)
                
                canvas.setFont("Helvetica", 8)
                canvas.setFillColor(colors.grey)
                
                # Left Footer
                if company_name:
                    canvas.drawString(15*mm, 4*mm, company_name)
                
                # Center Footer
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                canvas.drawCentredString(page_width/2, 4*mm, f"Generated: {timestamp}")
                
                # Right Footer (Page Number)
                page_num = f"Page {doc.page}"
                canvas.drawRightString(page_width - 15*mm, 4*mm, page_num)
                
                canvas.restoreState()

            # 6. Build
            doc.build(elements, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
            
            if parent:
                QMessageBox.information(parent, "Success", f"PDF exported successfully to:\n{path}")
            return True

        except Exception as e:
            logger.exception(f"Error exporting PDF: {e}")
            if parent:
                QMessageBox.critical(parent, "Export Error", f"Failed to export PDF:\n{str(e)}")
            return False

