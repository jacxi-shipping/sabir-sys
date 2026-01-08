"""
Professional PDF exporter for tables and reports
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Qt, QMarginsF
from PySide6.QtGui import QPainter, QFont, QColor, QFontMetrics
from PySide6.QtPrintSupport import QPrinter, QPageSize

logger = logging.getLogger(__name__)


class ProfessionalPDFExporter:
    """Professional PDF exporter with headers, footers, and styling"""
    
    def __init__(self):
        self.header_height = 120
        self.footer_height = 60
        self.margin = 40
        self.table_margin = 20
        
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
        Export table data to professional PDF
        
        Args:
            headers: Column headers
            rows: Table rows (list of lists)
            path: Output file path (if None, shows save dialog)
            title: Document title
            subtitle: Document subtitle
            company_name: Company/farm name for header
            company_address: Company address
            company_phone: Company phone
            show_totals: Whether to show totals row
            totals_row: Totals row data
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            if path is None:
                result = QFileDialog.getSaveFileName(
                    parent, "Export PDF", 
                    str(Path.cwd() / f"{title.lower().replace(' ', '_')}.pdf"), 
                    "PDF Files (*.pdf)"
                )
                if isinstance(result, tuple):
                    path, _ = result
                else:
                    path = result
                
                if not path or not isinstance(path, str) or path == '':
                    return False
            
            # Create printer
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(str(path))
            printer.setPageSize(QPageSize.A4)
            printer.setPageMargins(QMarginsF(20, 20, 20, 20), QPageSize.Millimeter)
            
            painter = QPainter(printer)
            
            # Get page dimensions
            page_rect = printer.pageRect(QPrinter.DevicePixel)
            page_width = page_rect.width()
            page_height = page_rect.height()
            
            # Calculate content area
            content_y = self.header_height
            content_height = page_height - self.header_height - self.footer_height
            
            # Draw pages
            row_start = 0
            page_num = 1
            total_pages = self._calculate_total_pages(len(rows), content_height)
            
            while row_start < len(rows):
                # Draw header
                self._draw_header(painter, page_rect, title, subtitle, 
                                company_name, company_address, company_phone, 
                                page_num, total_pages)
                
                # Draw table
                row_start = self._draw_table(painter, page_rect, headers, rows, 
                                           row_start, content_y, content_height,
                                           show_totals and row_start + self._rows_per_page(len(rows), content_height) >= len(rows),
                                           totals_row if row_start + self._rows_per_page(len(rows), content_height) >= len(rows) else None)
                
                # Draw footer
                self._draw_footer(painter, page_rect, page_num, total_pages,
                                company_name, company_phone)
                
                page_num += 1
                if row_start < len(rows):
                    printer.newPage()
            
            painter.end()
            
            if parent:
                QMessageBox.information(parent, "Success", f"PDF exported successfully to:\n{path}")
            return True
            
        except Exception as e:
            logger.exception(f"Error exporting PDF: {e}")
            if parent:
                QMessageBox.critical(parent, "Export Error", f"Failed to export PDF:\n{str(e)}")
            return False
    
    def _draw_header(self, painter: QPainter, page_rect, title: str, 
                    subtitle: Optional[str], company_name: Optional[str],
                    company_address: Optional[str], company_phone: Optional[str],
                    page_num: int, total_pages: int):
        """Draw professional header"""
        painter.save()
        
        # Header background
        header_color = QColor(41, 128, 185)  # Professional blue
        painter.fillRect(0, 0, page_rect.width(), self.header_height, header_color)
        
        # Company/Farm name (large, white, bold)
        if company_name:
            company_font = QFont("Arial", 18, QFont.Bold)
            painter.setFont(company_font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(40, 30, company_name)
        
        # Company details (smaller, white)
        if company_address or company_phone:
            detail_font = QFont("Arial", 9)
            painter.setFont(detail_font)
            y_offset = 55
            if company_address:
                painter.drawText(40, y_offset, company_address)
                y_offset += 20
            if company_phone:
                painter.drawText(40, y_offset, f"Phone: {company_phone}")
        
        # Title (right side, large, white)
        title_font = QFont("Arial", 16, QFont.Bold)
        painter.setFont(title_font)
        fm = QFontMetrics(title_font)
        title_width = fm.horizontalAdvance(title)
        painter.drawText(page_rect.width() - title_width - 40, 35, title)
        
        # Subtitle (right side, smaller, light)
        if subtitle:
            subtitle_font = QFont("Arial", 10)
            painter.setFont(subtitle_font)
            fm = QFontMetrics(subtitle_font)
            subtitle_width = fm.horizontalAdvance(subtitle)
            painter.drawText(page_rect.width() - subtitle_width - 40, 60, subtitle)
        
        # Date (right side, bottom of header)
        date_str = datetime.now().strftime("%B %d, %Y")
        date_font = QFont("Arial", 9)
        painter.setFont(date_font)
        fm = QFontMetrics(date_font)
        date_width = fm.horizontalAdvance(date_str)
        painter.drawText(page_rect.width() - date_width - 40, self.header_height - 15, date_str)
        
        # Page number in header
        page_str = f"Page {page_num} of {total_pages}"
        page_width = fm.horizontalAdvance(page_str)
        painter.drawText(page_rect.width() - page_width - 40, 20, page_str)
        
        painter.restore()
    
    def _draw_table(self, painter: QPainter, page_rect, headers: List[str], 
                   rows: List[List[Any]], row_start: int, content_y: int,
                   content_height: int, show_totals: bool, 
                   totals_row: Optional[List[Any]]) -> int:
        """Draw table and return next row to start"""
        painter.save()
        painter.translate(0, content_y)
        
        # Calculate column widths
        col_widths = self._calculate_column_widths(painter, headers, rows, 
                                                   page_rect.width() - 2 * self.margin)
        
        # Table dimensions
        table_x = self.margin
        table_width = sum(col_widths)
        row_height = 25
        header_height = 30
        
        # Draw table header
        header_color = QColor(52, 152, 219)  # Lighter blue
        painter.fillRect(table_x, 0, table_width, header_height, header_color)
        
        # Header text
        header_font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(header_font)
        painter.setPen(QColor(255, 255, 255))
        
        x_offset = table_x + 8
        for i, header in enumerate(headers):
            painter.drawText(x_offset, 20, col_widths[i] - 16, header_height,
                           Qt.AlignLeft | Qt.AlignVCenter, str(header))
            # Draw border
            painter.setPen(QColor(255, 255, 255))
            painter.drawRect(x_offset, 0, col_widths[i], header_height)
            x_offset += col_widths[i]
        
        # Draw rows
        painter.setPen(QColor(0, 0, 0))
        row_font = QFont("Arial", 9)
        painter.setFont(row_font)
        
        y_offset = header_height
        rows_to_draw = min(self._rows_per_page(len(rows), content_height), 
                          len(rows) - row_start)
        
        for i in range(rows_to_draw):
            row_idx = row_start + i
            if row_idx >= len(rows):
                break
            
            row = rows[row_idx]
            
            # Alternate row colors
            if i % 2 == 0:
                painter.fillRect(table_x, y_offset, table_width, row_height, 
                               QColor(245, 245, 245))
            else:
                painter.fillRect(table_x, y_offset, table_width, row_height, 
                               QColor(255, 255, 255))
            
            # Draw row data
            x_offset = table_x + 8
            for j, cell_value in enumerate(row):
                if j < len(col_widths):
                    painter.drawText(x_offset, y_offset, col_widths[j] - 16, row_height,
                                   Qt.AlignLeft | Qt.AlignVCenter, str(cell_value))
                    # Draw border
                    painter.setPen(QColor(200, 200, 200))
                    painter.drawRect(x_offset, y_offset, col_widths[j], row_height)
                    painter.setPen(QColor(0, 0, 0))
                    x_offset += col_widths[j]
            
            y_offset += row_height
        
        # Draw totals row if needed
        if show_totals and totals_row:
            totals_y = y_offset + 5
            totals_height = row_height + 5
            
            # Totals background
            painter.fillRect(table_x, totals_y, table_width, totals_height,
                           QColor(220, 220, 220))
            
            # Totals text (bold)
            totals_font = QFont("Arial", 9, QFont.Bold)
            painter.setFont(totals_font)
            
            x_offset = table_x + 8
            for j, cell_value in enumerate(totals_row):
                if j < len(col_widths):
                    painter.drawText(x_offset, totals_y, col_widths[j] - 16, totals_height,
                                   Qt.AlignLeft | Qt.AlignVCenter, str(cell_value))
                    painter.setPen(QColor(100, 100, 100))
                    painter.drawRect(x_offset, totals_y, col_widths[j], totals_height)
                    painter.setPen(QColor(0, 0, 0))
                    x_offset += col_widths[j]
        
        painter.restore()
        return row_start + rows_to_draw
    
    def _draw_footer(self, painter: QPainter, page_rect, page_num: int, 
                    total_pages: int, company_name: Optional[str],
                    company_phone: Optional[str]):
        """Draw professional footer"""
        painter.save()
        
        footer_y = page_rect.height() - self.footer_height
        
        # Footer background
        footer_color = QColor(236, 240, 241)  # Light gray
        painter.fillRect(0, footer_y, page_rect.width(), self.footer_height, footer_color)
        
        # Footer line
        painter.setPen(QColor(189, 195, 199))
        painter.drawLine(40, footer_y, page_rect.width() - 40, footer_y)
        
        # Footer text
        footer_font = QFont("Arial", 8)
        painter.setFont(footer_font)
        painter.setPen(QColor(127, 140, 141))
        
        # Left side - Company info
        if company_name:
            painter.drawText(40, footer_y + 20, company_name)
        if company_phone:
            painter.drawText(40, footer_y + 35, f"Phone: {company_phone}")
        
        # Center - Generated info
        generated_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        fm = QFontMetrics(footer_font)
        text_width = fm.horizontalAdvance(generated_text)
        painter.drawText((page_rect.width() - text_width) // 2, footer_y + 25, generated_text)
        
        # Right side - Page info
        page_text = f"Page {page_num} of {total_pages}"
        page_width = fm.horizontalAdvance(page_text)
        painter.drawText(page_rect.width() - page_width - 40, footer_y + 25, page_text)
        
        painter.restore()
    
    def _calculate_column_widths(self, painter: QPainter, headers: List[str], 
                                 rows: List[List[Any]], available_width: int) -> List[int]:
        """Calculate optimal column widths"""
        # Sample some rows to determine content width
        sample_rows = rows[:min(10, len(rows))]
        
        col_widths = []
        for i, header in enumerate(headers):
            # Start with header width
            header_font = QFont("Arial", 10, QFont.Bold)
            painter.setFont(header_font)
            fm = QFontMetrics(header_font)
            max_width = fm.horizontalAdvance(str(header))
            
            # Check sample row data
            row_font = QFont("Arial", 9)
            painter.setFont(row_font)
            fm = QFontMetrics(row_font)
            for row in sample_rows:
                if i < len(row):
                    cell_width = fm.horizontalAdvance(str(row[i]))
                    max_width = max(max_width, cell_width)
            
            col_widths.append(max_width + 20)  # Add padding
        
        # Scale to fit available width
        total_width = sum(col_widths)
        if total_width > available_width:
            scale = available_width / total_width
            col_widths = [int(w * scale) for w in col_widths]
        
        return col_widths
    
    def _rows_per_page(self, total_rows: int, content_height: int) -> int:
        """Calculate how many rows fit per page"""
        row_height = 25
        header_height = 30
        available_height = content_height - header_height - 10
        return max(1, int(available_height / row_height))
    
    def _calculate_total_pages(self, total_rows: int, content_height: int) -> int:
        """Calculate total number of pages needed"""
        rows_per_page = self._rows_per_page(total_rows, content_height)
        return max(1, (total_rows + rows_per_page - 1) // rows_per_page)

